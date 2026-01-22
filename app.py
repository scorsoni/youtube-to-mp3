"""
YouTube to MP3 Converter
Render-ready version (Linux + Gunicorn + FFmpeg system)
"""

import os
import re
import uuid
import threading
import shutil
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, abort
import yt_dlp

# ==============================================================================
# App
# ==============================================================================

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", os.urandom(24))

BASE_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)

# Detect ffmpeg in system (Render/Linux)
FFMPEG_PATH = shutil.which("ffmpeg")
FFPROBE_PATH = shutil.which("ffprobe")

conversions = {}

# ==============================================================================
# Utils
# ==============================================================================

def is_valid_youtube_url(url: str) -> bool:
    patterns = [
        r'^https?://(www\.)?youtube\.com/watch\?v=',
        r'^https?://youtu\.be/',
        r'^https?://(www\.)?youtube\.com/shorts/',
        r'^https?://m\.youtube\.com/watch\?v=',
    ]
    return any(re.match(p, url) for p in patterns)


def sanitize_filename(name: str, max_len: int = 100) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name)
    name = re.sub(r'\s+', ' ', name).strip(" .")
    return name[:max_len] or "audio"


def format_filesize(size):
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


# ==============================================================================
# yt-dlp
# ==============================================================================

def download_and_convert(url: str, cid: str):
    conversions[cid] = {
        "status": "processing",
        "progress": 0,
        "filename": None,
        "error": None,
    }

    def hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            if total:
                conversions[cid]["progress"] = int(d["downloaded_bytes"] / total * 90)
        elif d["status"] == "finished":
            conversions[cid]["progress"] = 95

    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(DOWNLOADS_DIR / "%(title)s.%(ext)s"),
            "progress_hooks": [hook],
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }

        if FFMPEG_PATH:
            ydl_opts["ffmpeg_location"] = os.path.dirname(FFMPEG_PATH)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        title = sanitize_filename(info.get("title", "audio"))
        mp3_file = next(DOWNLOADS_DIR.glob(f"{title}*.mp3"))

        conversions[cid].update({
            "status": "completed",
            "progress": 100,
            "filename": mp3_file.name,
            "filesize": format_filesize(mp3_file.stat().st_size),
        })

    except Exception as e:
        conversions[cid]["status"] = "error"
        conversions[cid]["error"] = str(e)


# ==============================================================================
# Routes
# ==============================================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert():
    data = request.get_json()
    url = data.get("url", "").strip()

    if not is_valid_youtube_url(url):
        return jsonify({"error": "URL inválida"}), 400

    cid = uuid.uuid4().hex
    threading.Thread(target=download_and_convert, args=(url, cid)).start()

    return jsonify({"conversion_id": cid})


@app.route("/status/<cid>")
def status(cid):
    return jsonify(conversions.get(cid, {"error": "Não encontrado"}))


@app.route("/download/<filename>")
def download(filename):
    if ".." in filename:
        abort(403)

    file = DOWNLOADS_DIR / filename
    if not file.exists():
        abort(404)

    return send_file(file, as_attachment=True, mimetype="audio/mpeg")


# ==============================================================================
# Entry
# ==============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
