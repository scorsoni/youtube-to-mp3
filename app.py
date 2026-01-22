"""
YouTube to MP3 Converter
A simple, ad-free YouTube to MP3 converter for personal use.
"""

import os
import re
import json
import uuid
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, abort

import yt_dlp

# ==============================================================================
# Configuration
# ==============================================================================

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Paths
BASE_DIR = Path(__file__).resolve().parent
BIN_DIR = BASE_DIR / 'bin'
DOWNLOADS_DIR = BASE_DIR / 'downloads'
FFMPEG_PATH = BIN_DIR / 'ffmpeg.exe'
FFPROBE_PATH = BIN_DIR / 'ffprobe.exe'

# Ensure downloads directory exists
DOWNLOADS_DIR.mkdir(exist_ok=True)

# Store conversion progress and status
conversions = {}

# ==============================================================================
# Utility Functions
# ==============================================================================

def is_valid_youtube_url(url: str) -> bool:
    """Validate if the URL is a valid YouTube link."""
    if not url or not isinstance(url, str):
        return False

    youtube_patterns = [
        r'^https?://(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'^https?://(www\.)?youtube\.com/shorts/[\w-]+',
        r'^https?://youtu\.be/[\w-]+',
        r'^https?://(www\.)?youtube\.com/embed/[\w-]+',
        r'^https?://m\.youtube\.com/watch\?v=[\w-]+',
    ]

    for pattern in youtube_patterns:
        if re.match(pattern, url.strip()):
            return True
    return False


def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """
    Sanitize filename for Windows compatibility.
    Removes invalid characters and limits length.
    """
    # Remove invalid Windows filename characters
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(invalid_chars, '', filename)

    # Replace multiple spaces/dots with single ones
    sanitized = re.sub(r'\s+', ' ', sanitized)
    sanitized = re.sub(r'\.+', '.', sanitized)

    # Trim whitespace and dots from ends
    sanitized = sanitized.strip(' .')

    # Limit length (accounting for extension)
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].strip(' .')

    # Fallback if empty
    if not sanitized:
        sanitized = 'audio'

    return sanitized


def get_unique_filepath(filepath: Path) -> Path:
    """
    Get a unique filepath by adding a suffix if the file already exists.
    Example: 'song.mp3' -> 'song (1).mp3' -> 'song (2).mp3'
    """
    if not filepath.exists():
        return filepath

    stem = filepath.stem
    suffix = filepath.suffix
    parent = filepath.parent

    counter = 1
    while True:
        new_name = f"{stem} ({counter}){suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1
        if counter > 1000:  # Safety limit
            new_path = parent / f"{stem}_{uuid.uuid4().hex[:8]}{suffix}"
            return new_path


def format_duration(seconds: int) -> str:
    """Format duration in seconds to MM:SS or HH:MM:SS."""
    if not seconds:
        return "00:00"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_filesize(size_bytes: int) -> str:
    """Format file size in bytes to human readable format."""
    if not size_bytes:
        return "0 B"

    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# ==============================================================================
# YouTube Download Functions
# ==============================================================================

def get_video_info(url: str) -> dict:
    """Get video information without downloading."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }

    # Add ffmpeg path if exists
    if FFMPEG_PATH.exists():
        ydl_opts['ffmpeg_location'] = str(BIN_DIR)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown Title'),
                'duration': info.get('duration', 0),
                'duration_formatted': format_duration(info.get('duration', 0)),
                'thumbnail': info.get('thumbnail', ''),
                'channel': info.get('channel', info.get('uploader', 'Unknown')),
                'view_count': info.get('view_count', 0),
            }
    except Exception as e:
        raise Exception(f"Failed to get video info: {str(e)}")


def download_and_convert(url: str, conversion_id: str) -> dict:
    """Download YouTube video and convert to MP3."""

    def progress_hook(d):
        """Update progress during download."""
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)

            if total > 0:
                percent = int((downloaded / total) * 100)
                conversions[conversion_id]['progress'] = min(percent, 95)
                conversions[conversion_id]['status_text'] = f"Baixando... {percent}%"
            else:
                conversions[conversion_id]['status_text'] = "Baixando..."

        elif d['status'] == 'finished':
            conversions[conversion_id]['progress'] = 95
            conversions[conversion_id]['status_text'] = "Convertendo para MP3..."

    # Initialize conversion status
    conversions[conversion_id] = {
        'status': 'processing',
        'status_text': 'Iniciando download...',
        'progress': 0,
        'filename': None,
        'error': None,
        'info': None,
    }

    try:
        # Get video info first
        conversions[conversion_id]['status_text'] = 'Obtendo informações do vídeo...'
        info = get_video_info(url)
        conversions[conversion_id]['info'] = info

        # Prepare filename
        safe_title = sanitize_filename(info['title'])
        output_template = str(DOWNLOADS_DIR / f"{safe_title}.%(ext)s")

        # yt-dlp options for MP3 extraction
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [progress_hook],
            'quiet': True,
            'no_warnings': True,
        }

        # Add ffmpeg path if exists
        if FFMPEG_PATH.exists():
            ydl_opts['ffmpeg_location'] = str(BIN_DIR)

        conversions[conversion_id]['status_text'] = 'Baixando áudio...'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find the created MP3 file
        expected_file = DOWNLOADS_DIR / f"{safe_title}.mp3"

        if not expected_file.exists():
            # Try to find the file with similar name
            mp3_files = list(DOWNLOADS_DIR.glob(f"{safe_title[:50]}*.mp3"))
            if mp3_files:
                expected_file = max(mp3_files, key=lambda f: f.stat().st_mtime)
            else:
                raise Exception("MP3 file was not created")

        # Get final file info
        file_size = expected_file.stat().st_size

        conversions[conversion_id].update({
            'status': 'completed',
            'status_text': 'Concluído!',
            'progress': 100,
            'filename': expected_file.name,
            'filesize': file_size,
            'filesize_formatted': format_filesize(file_size),
        })

        return conversions[conversion_id]

    except Exception as e:
        error_msg = str(e)

        # Clean up error message
        if 'Video unavailable' in error_msg:
            error_msg = 'Vídeo não disponível ou privado'
        elif 'Sign in' in error_msg:
            error_msg = 'Este vídeo requer autenticação'
        elif 'ffmpeg' in error_msg.lower():
            error_msg = 'FFmpeg não encontrado. Verifique se ffmpeg.exe está na pasta /bin'

        conversions[conversion_id].update({
            'status': 'error',
            'status_text': 'Erro ao converter',
            'error': error_msg,
            'progress': 0,
        })

        return conversions[conversion_id]


# ==============================================================================
# Routes
# ==============================================================================

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/convert', methods=['POST'])
def convert():
    """Start conversion of a YouTube video to MP3."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': 'URL não fornecida'}), 400

    if not is_valid_youtube_url(url):
        return jsonify({'error': 'URL do YouTube inválida'}), 400

    # Generate unique conversion ID
    conversion_id = uuid.uuid4().hex

    # Start conversion in background thread
    thread = threading.Thread(
        target=download_and_convert,
        args=(url, conversion_id)
    )
    thread.start()

    return jsonify({
        'conversion_id': conversion_id,
        'message': 'Conversão iniciada'
    })


@app.route('/status/<conversion_id>')
def status(conversion_id):
    """Get the status of a conversion."""
    if conversion_id not in conversions:
        return jsonify({'error': 'Conversão não encontrada'}), 404

    return jsonify(conversions[conversion_id])


@app.route('/info', methods=['POST'])
def info():
    """Get video information without converting."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': 'URL não fornecida'}), 400

    if not is_valid_youtube_url(url):
        return jsonify({'error': 'URL do YouTube inválida'}), 400

    try:
        info = get_video_info(url)
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download/<filename>')
def download(filename):
    """Download a converted MP3 file."""
    # Security: prevent path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        abort(403)

    # Only allow .mp3 files
    if not filename.lower().endswith('.mp3'):
        abort(403)

    # Sanitize filename
    safe_filename = sanitize_filename(Path(filename).stem) + '.mp3'
    filepath = DOWNLOADS_DIR / safe_filename

    # Also try the original filename in case sanitization differs
    if not filepath.exists():
        filepath = DOWNLOADS_DIR / filename

    if not filepath.exists():
        abort(404)

    # Ensure the file is within downloads directory (extra security)
    try:
        filepath.resolve().relative_to(DOWNLOADS_DIR.resolve())
    except ValueError:
        abort(403)

    return send_file(
        filepath,
        as_attachment=True,
        download_name=filepath.name,
        mimetype='audio/mpeg'
    )


@app.route('/clear/<conversion_id>', methods=['DELETE'])
def clear_conversion(conversion_id):
    """Clear a conversion from memory."""
    if conversion_id in conversions:
        del conversions[conversion_id]
    return jsonify({'message': 'Conversão removida'})


# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  YouTube to MP3 Converter")
    print("=" * 60)
    print(f"\n  Pasta de downloads: {DOWNLOADS_DIR}")
    print(f"  FFmpeg: {'Encontrado' if FFMPEG_PATH.exists() else 'NAO ENCONTRADO - coloque ffmpeg.exe em /bin'}")
    print(f"\n  Acesse: http://localhost:5000")
    print("=" * 60 + "\n")

    port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)

