// DOM Elements
const modeButtons = document.querySelectorAll('.mode-btn');
const modeInput = document.getElementById('modeInput');
const qualitySelect = document.getElementById('quality');
const downloadForm = document.getElementById('downloadForm');
const dropdownSelected = document.getElementById('dropdownSelected');
const dropdownList = document.getElementById('dropdownList');
const messagesDiv = document.getElementById('messages');

// Quality options mapping
const qualityOptions = {
    'a': 'A — 4K (2160p)',
    'b': 'B — 2K (1440p)',
    'c': 'C — 1080p',
    'd': 'D — 720p',
    'e': 'E — 480p',
    'audio': 'Audio only (best)'
};

// Initialize quality select with default value
qualitySelect.value = 'c';

// Mode button handling
modeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        // Remove active class from all buttons
        modeButtons.forEach(b => b.classList.remove('active'));

        // Add active class to clicked button
        btn.classList.add('active');

        // Get mode value
        const mode = btn.dataset.mode;
        modeInput.value = mode;

        // Adjust quality based on mode
        if (mode === 'mp3') {
            // Force quality to audio option for MP3 mode
            qualitySelect.value = 'audio';
            dropdownSelected.textContent = qualityOptions['audio'];
        } else {
            // Default to 1080p for video/playlist if currently on audio
            if (qualitySelect.value === 'audio') {
                qualitySelect.value = 'c';
                dropdownSelected.textContent = qualityOptions['c'];
            }
        }
    });
});

// Dropdown toggle
dropdownSelected.addEventListener('click', (e) => {
    e.stopPropagation();
    const isVisible = dropdownList.style.display === 'block';
    dropdownList.style.display = isVisible ? 'none' : 'block';
});

// Dropdown option selection
document.querySelectorAll('.dropdown-list div').forEach(item => {
    item.addEventListener('click', (e) => {
        e.stopPropagation();

        // Update selected text
        dropdownSelected.textContent = item.textContent;

        // Update hidden input value
        const value = item.getAttribute('data-value');
        qualitySelect.value = value;

        // Close dropdown
        dropdownList.style.display = 'none';

        // If audio is selected, switch to MP3 mode
        if (value === 'audio') {
            const mp3Button = document.querySelector('.mode-btn[data-mode="mp3"]');
            if (mp3Button) {
                modeButtons.forEach(b => b.classList.remove('active'));
                mp3Button.classList.add('active');
                modeInput.value = 'mp3';
            }
        }
    });
});

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.dropdown')) {
        dropdownList.style.display = 'none';
    }
});

// Form submission handling
downloadForm.addEventListener('submit', (e) => {
    // Show loading message
    messagesDiv.textContent = 'Request submitted — preparing your download. This may take a moment.';
    messagesDiv.style.display = 'block';

    // Disable submit button to prevent double submission
    const submitBtn = downloadForm.querySelector('.download-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Processing...';

    // Re-enable after a delay (in case of redirect issues)
    setTimeout(() => {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Download';
    }, 3000);
});

// Handle flash messages if present (from Flask redirects)
window.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const flashMessage = urlParams.get('message');

    if (flashMessage) {
        messagesDiv.textContent = decodeURIComponent(flashMessage);
        messagesDiv.style.display = 'block';
    }
});

// Keyboard accessibility for dropdown
dropdownSelected.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        dropdownSelected.click();
    }
});

// Add keyboard navigation for dropdown items
document.querySelectorAll('.dropdown-list div').forEach((item, index, items) => {
    item.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            item.click();
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            const next = items[index + 1] || items[0];
            next.focus();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            const prev = items[index - 1] || items[items.length - 1];
            prev.focus();
        } else if (e.key === 'Escape') {
            dropdownList.style.display = 'none';
            dropdownSelected.focus();
        }
    });
});