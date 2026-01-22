/**
 * YouTube to MP3 Converter - Frontend JavaScript
 */

// ==============================================================================
// State Management
// ==============================================================================

const state = {
    currentConversionId: null,
    isConverting: false,
    history: [],
    maxHistoryItems: 5,
    statusCheckInterval: null,
};

// ==============================================================================
// DOM Elements
// ==============================================================================

const elements = {
    urlInput: document.getElementById('urlInput'),
    convertBtn: document.getElementById('convertBtn'),
    clearBtn: document.getElementById('clearBtn'),
    statusCard: document.getElementById('statusCard'),
    videoInfo: document.getElementById('videoInfo'),
    videoThumbnail: document.getElementById('videoThumbnail'),
    videoTitle: document.getElementById('videoTitle'),
    videoChannel: document.getElementById('videoChannel'),
    videoDuration: document.getElementById('videoDuration'),
    progressContainer: document.getElementById('progressContainer'),
    progressBar: document.getElementById('progressBar'),
    progressPercent: document.getElementById('progressPercent'),
    statusText: document.getElementById('statusText'),
    statusIcon: document.getElementById('statusIcon'),
    statusMessage: document.getElementById('statusMessage'),
    downloadSection: document.getElementById('downloadSection'),
    downloadBtn: document.getElementById('downloadBtn'),
    downloadFilename: document.getElementById('downloadFilename'),
    downloadFilesize: document.getElementById('downloadFilesize'),
    errorSection: document.getElementById('errorSection'),
    errorMessage: document.getElementById('errorMessage'),
    historySection: document.getElementById('historySection'),
    historyList: document.getElementById('historyList'),
    clearHistoryBtn: document.getElementById('clearHistoryBtn'),
    themeToggle: document.getElementById('themeToggle'),
    toastContainer: document.getElementById('toastContainer'),
};

// ==============================================================================
// Theme Management
// ==============================================================================

function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
}

function toggleTheme() {
    const isDark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

// ==============================================================================
// Toast Notifications
// ==============================================================================

function showToast(message, type = 'info', duration = 4000) {
    const toast = document.createElement('div');

    const bgColors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-blue-500',
        warning: 'bg-yellow-500',
    };

    const icons = {
        success: 'check-circle',
        error: 'x-circle',
        info: 'info',
        warning: 'alert-triangle',
    };

    toast.className = `
        ${bgColors[type]} text-white px-4 py-3 rounded-lg shadow-lg
        flex items-center gap-3 min-w-[300px] max-w-md
        transform translate-x-full opacity-0 transition-all duration-300
    `;

    toast.innerHTML = `
        <i data-lucide="${icons[type]}" class="w-5 h-5 flex-shrink-0"></i>
        <span class="flex-1">${message}</span>
        <button class="hover:opacity-80 transition-opacity" onclick="this.parentElement.remove()">
            <i data-lucide="x" class="w-4 h-4"></i>
        </button>
    `;

    elements.toastContainer.appendChild(toast);
    lucide.createIcons();

    // Animate in
    requestAnimationFrame(() => {
        toast.classList.remove('translate-x-full', 'opacity-0');
    });

    // Auto remove
    setTimeout(() => {
        toast.classList.add('translate-x-full', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ==============================================================================
// Validation
// ==============================================================================

function isValidYouTubeUrl(url) {
    if (!url || typeof url !== 'string') return false;

    const patterns = [
        /^https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+/,
        /^https?:\/\/(www\.)?youtube\.com\/shorts\/[\w-]+/,
        /^https?:\/\/youtu\.be\/[\w-]+/,
        /^https?:\/\/(www\.)?youtube\.com\/embed\/[\w-]+/,
        /^https?:\/\/m\.youtube\.com\/watch\?v=[\w-]+/,
    ];

    return patterns.some(pattern => pattern.test(url.trim()));
}

// ==============================================================================
// UI Updates
// ==============================================================================

function setButtonLoading(loading) {
    const btnText = elements.convertBtn.querySelector('.btn-text');
    const convertIcon = elements.convertBtn.querySelector('.convert-icon');
    const loadingIcon = elements.convertBtn.querySelector('.loading-icon');

    elements.convertBtn.disabled = loading;
    state.isConverting = loading;

    if (loading) {
        btnText.textContent = 'Convertendo...';
        convertIcon.classList.add('hidden');
        loadingIcon.classList.remove('hidden');
    } else {
        btnText.textContent = 'Converter';
        convertIcon.classList.remove('hidden');
        loadingIcon.classList.add('hidden');
    }
}

function showStatusCard() {
    elements.statusCard.classList.remove('hidden');
}

function hideStatusCard() {
    elements.statusCard.classList.add('hidden');
}

function resetStatusCard() {
    elements.videoInfo.classList.add('hidden');
    elements.progressContainer.classList.remove('hidden');
    elements.progressBar.style.width = '0%';
    elements.progressPercent.textContent = '0%';
    elements.statusText.textContent = 'Aguardando...';
    elements.statusIcon.classList.add('hidden');
    elements.downloadSection.classList.add('hidden');
    elements.errorSection.classList.add('hidden');
}

function updateProgress(percent, text) {
    elements.progressBar.style.width = `${percent}%`;
    elements.progressPercent.textContent = `${percent}%`;
    if (text) {
        elements.statusText.textContent = text;
    }
}

function showVideoInfo(info) {
    if (!info) return;

    elements.videoInfo.classList.remove('hidden');

    if (info.thumbnail) {
        elements.videoThumbnail.src = info.thumbnail;
    }

    elements.videoTitle.textContent = info.title || 'Carregando...';
    elements.videoChannel.textContent = info.channel || '';

    const durationSpan = elements.videoDuration.querySelector('span');
    if (durationSpan) {
        durationSpan.textContent = info.duration_formatted || '--:--';
    }
}

function showDownloadSection(filename, filesize) {
    elements.progressContainer.classList.add('hidden');
    elements.downloadSection.classList.remove('hidden');
    elements.downloadFilename.textContent = filename;
    elements.downloadFilesize.textContent = filesize || '';
    elements.downloadBtn.href = `/download/${encodeURIComponent(filename)}`;

    // Show success status
    elements.statusIcon.classList.remove('hidden');
    elements.statusIcon.querySelector('.success-icon').classList.remove('hidden');
    elements.statusIcon.querySelector('.error-icon').classList.add('hidden');
    elements.statusMessage.textContent = 'Conversão concluída!';
    elements.statusMessage.classList.remove('text-red-500');
    elements.statusMessage.classList.add('text-green-500');
}

function showError(message) {
    elements.progressContainer.classList.add('hidden');
    elements.errorSection.classList.remove('hidden');
    elements.errorMessage.textContent = message;

    // Show error status
    elements.statusIcon.classList.remove('hidden');
    elements.statusIcon.querySelector('.success-icon').classList.add('hidden');
    elements.statusIcon.querySelector('.error-icon').classList.remove('hidden');
    elements.statusMessage.textContent = 'Erro ao converter';
    elements.statusMessage.classList.add('text-red-500');
    elements.statusMessage.classList.remove('text-green-500');
}

// ==============================================================================
// History Management
// ==============================================================================

function loadHistory() {
    try {
        const saved = localStorage.getItem('ytmp3_history');
        state.history = saved ? JSON.parse(saved) : [];
    } catch {
        state.history = [];
    }
    renderHistory();
}

function saveHistory() {
    try {
        localStorage.setItem('ytmp3_history', JSON.stringify(state.history));
    } catch {
        // Ignore storage errors
    }
}

function addToHistory(item) {
    // Remove duplicates
    state.history = state.history.filter(h => h.filename !== item.filename);

    // Add to beginning
    state.history.unshift({
        filename: item.filename,
        title: item.title,
        filesize: item.filesize,
        timestamp: Date.now(),
    });

    // Limit history
    if (state.history.length > state.maxHistoryItems) {
        state.history = state.history.slice(0, state.maxHistoryItems);
    }

    saveHistory();
    renderHistory();
}

function clearHistory() {
    state.history = [];
    saveHistory();
    renderHistory();
}

function renderHistory() {
    if (state.history.length === 0) {
        elements.historySection.classList.add('hidden');
        return;
    }

    elements.historySection.classList.remove('hidden');
    elements.historyList.innerHTML = '';

    state.history.forEach(item => {
        const div = document.createElement('div');
        div.className = 'flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg';

        div.innerHTML = `
            <div class="flex items-center gap-3 min-w-0 flex-1">
                <div class="w-8 h-8 bg-red-100 dark:bg-red-900/30 rounded-lg flex items-center justify-center flex-shrink-0">
                    <i data-lucide="music" class="w-4 h-4 text-red-500"></i>
                </div>
                <div class="min-w-0 flex-1">
                    <p class="text-sm font-medium text-gray-900 dark:text-white truncate">${escapeHtml(item.title || item.filename)}</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400">${item.filesize || ''}</p>
                </div>
            </div>
            <a
                href="/download/${encodeURIComponent(item.filename)}"
                class="flex-shrink-0 p-2 text-gray-500 hover:text-red-500 transition-colors"
                title="Baixar novamente"
            >
                <i data-lucide="download" class="w-4 h-4"></i>
            </a>
        `;

        elements.historyList.appendChild(div);
    });

    lucide.createIcons();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==============================================================================
// Conversion Logic
// ==============================================================================

async function startConversion() {
    const url = elements.urlInput.value.trim();

    if (!url) {
        showToast('Por favor, cole um link do YouTube', 'warning');
        elements.urlInput.focus();
        return;
    }

    if (!isValidYouTubeUrl(url)) {
        showToast('Link do YouTube inválido', 'error');
        elements.urlInput.focus();
        return;
    }

    // Reset and show status
    resetStatusCard();
    showStatusCard();
    setButtonLoading(true);
    updateProgress(0, 'Iniciando conversão...');

    try {
        // Start conversion
        const response = await fetch('/convert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Erro ao iniciar conversão');
        }

        state.currentConversionId = data.conversion_id;

        // Start polling for status
        startStatusPolling();

    } catch (error) {
        setButtonLoading(false);
        showError(error.message);
        showToast(error.message, 'error');
    }
}

function startStatusPolling() {
    if (state.statusCheckInterval) {
        clearInterval(state.statusCheckInterval);
    }

    state.statusCheckInterval = setInterval(checkStatus, 500);
}

function stopStatusPolling() {
    if (state.statusCheckInterval) {
        clearInterval(state.statusCheckInterval);
        state.statusCheckInterval = null;
    }
}

async function checkStatus() {
    if (!state.currentConversionId) {
        stopStatusPolling();
        return;
    }

    try {
        const response = await fetch(`/status/${state.currentConversionId}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Erro ao verificar status');
        }

        // Update UI based on status
        updateProgress(data.progress || 0, data.status_text);

        // Show video info if available
        if (data.info) {
            showVideoInfo(data.info);
        }

        // Handle completion
        if (data.status === 'completed') {
            stopStatusPolling();
            setButtonLoading(false);
            showDownloadSection(data.filename, data.filesize_formatted);
            showToast('Conversão concluída!', 'success');

            // Add to history
            addToHistory({
                filename: data.filename,
                title: data.info?.title || data.filename,
                filesize: data.filesize_formatted,
            });
        }

        // Handle error
        if (data.status === 'error') {
            stopStatusPolling();
            setButtonLoading(false);
            showError(data.error || 'Erro desconhecido');
            showToast('Erro na conversão', 'error');
        }

    } catch (error) {
        console.error('Status check error:', error);
        // Don't stop polling on network errors, just log
    }
}

function clearInput() {
    elements.urlInput.value = '';
    hideStatusCard();
    stopStatusPolling();
    setButtonLoading(false);
    state.currentConversionId = null;
    elements.urlInput.focus();
}

// ==============================================================================
// Event Listeners
// ==============================================================================

function initEventListeners() {
    // Theme toggle
    elements.themeToggle.addEventListener('click', toggleTheme);

    // Convert button
    elements.convertBtn.addEventListener('click', startConversion);

    // Clear button
    elements.clearBtn.addEventListener('click', clearInput);

    // Clear history button
    elements.clearHistoryBtn.addEventListener('click', () => {
        clearHistory();
        showToast('Histórico limpo', 'info');
    });

    // Enter key on input
    elements.urlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !state.isConverting) {
            startConversion();
        }
    });

    // Paste detection - auto convert on paste
    elements.urlInput.addEventListener('paste', (e) => {
        // Small delay to let the paste complete
        setTimeout(() => {
            const url = elements.urlInput.value.trim();
            if (isValidYouTubeUrl(url) && !state.isConverting) {
                // Optionally auto-start conversion
                // startConversion();
            }
        }, 100);
    });

    // Handle visibility change (stop polling when tab is hidden)
    document.addEventListener('visibilitychange', () => {
        if (document.hidden && state.statusCheckInterval) {
            // Slow down polling when tab is hidden
            stopStatusPolling();
            state.statusCheckInterval = setInterval(checkStatus, 2000);
        } else if (!document.hidden && state.currentConversionId && state.isConverting) {
            // Speed up polling when tab is visible
            stopStatusPolling();
            state.statusCheckInterval = setInterval(checkStatus, 500);
        }
    });
}

// ==============================================================================
// Initialization
// ==============================================================================

function init() {
    initTheme();
    initEventListeners();
    loadHistory();

    // Initialize Lucide icons
    lucide.createIcons();

    // Focus on input
    elements.urlInput.focus();
}

// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
