// Theme Management
const ThemeManager = {
    init() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.setTheme(savedTheme);
    },

    toggle() {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        this.setTheme(next);
    },

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        this.updateUI(theme);
        this.updateHighlight(theme);
        // Sync icon if exists
        const icon = document.getElementById('themeIcon');
        if (icon) icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
    },

    updateUI(theme) {
        const toggle = document.getElementById('themeToggle');
        if (!toggle) return;
        toggle.setAttribute('data-value', theme === 'dark' ? 'left' : 'right');
        // Logic for L/R based on implementation. 
        // In existing code: dark=left, light=right? Or vice versa?
        // Let's standardize: Left=Dark, Right=Light based on text position in HTML
        // HTML: Left=Dark, Right=Light.

        const left = toggle.querySelector('.toggle-option[data-side="left"]');
        const right = toggle.querySelector('.toggle-option[data-side="right"]');

        if (left && right) {
            // If dark (left active)
            if (theme === 'dark') {
                left.classList.add('active');
                right.classList.remove('active');
                toggle.setAttribute('data-value', 'left');
            } else {
                left.classList.remove('active');
                right.classList.add('active');
                toggle.setAttribute('data-value', 'right');
            }
        }
    },

    updateHighlight(theme) {
        const highlightTheme = document.getElementById('highlightTheme');
        if (highlightTheme) {
            const cssUrl = theme === 'dark'
                ? 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/tokyo-night-dark.min.css'
                : 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css';
            highlightTheme.href = cssUrl;
        }
    }
};

// Font Size Management
const FontManager = {
    init() {
        const savedSize = localStorage.getItem('fontSize') || 'normal';
        this.setSize(savedSize);
    },

    toggle() {
        const current = localStorage.getItem('fontSize') || 'normal';
        const next = current === 'normal' ? 'large' : 'normal';
        this.setSize(next);
    },

    setSize(size) {
        document.documentElement.setAttribute('data-font-size', size);
        localStorage.setItem('fontSize', size);

        // CSS implementation for size:
        // We need to ensure CSS respects data-font-size.
        // Assuming root vars change. If not exists, we add simple scale logic.
        if (size === 'large') {
            document.documentElement.style.fontSize = '18px'; // 16px default
        } else {
            document.documentElement.style.fontSize = '';
        }

        this.updateUI(size);
    },

    updateUI(size) {
        const toggle = document.getElementById('fontToggle');
        if (!toggle) return;

        // Custom logic: Normal=Left (Aa), Large=Right (Aa+)
        const isNormal = size === 'normal';
        toggle.setAttribute('data-value', isNormal ? 'left' : 'right');

        const left = toggle.querySelector('.toggle-option[data-side="left"]');
        const right = toggle.querySelector('.toggle-option[data-side="right"]');

        if (left && right) {
            if (isNormal) {
                left.classList.add('active');
                right.classList.remove('active');
            } else {
                left.classList.remove('active');
                right.classList.add('active');
            }
        }
    }
};

// Layout (TOC) Management
const LayoutManager = {
    init() {
        const savedPos = localStorage.getItem('tocPosition') || 'right';
        this.setPosition(savedPos);
    },

    toggle() {
        const current = localStorage.getItem('tocPosition') || 'right';
        const next = current === 'right' ? 'left' : 'right';
        this.setPosition(next);
    },

    setPosition(pos) {
        // Class check: main-container or layout-container
        const containers = document.querySelectorAll('.main-container, .layout-container, .content-wrapper');
        containers.forEach(el => {
            if (pos === 'left') {
                el.classList.add('toc-left');
                el.classList.remove('toc-right');
            } else {
                el.classList.remove('toc-left');
                el.classList.add('toc-right');
            }
        });

        localStorage.setItem('tocPosition', pos);
        this.updateUI(pos);

        // Dispatch event for specialized handlers if needed
        window.dispatchEvent(new CustomEvent('layoutChanged', { detail: { toc: pos } }));
    },

    updateUI(pos) {
        const toggle = document.getElementById('tocToggle');
        if (!toggle) return;

        // Left=Left, Right=Right
        toggle.setAttribute('data-value', pos);

        const left = toggle.querySelector('.toggle-option[data-side="left"]'); // or class left
        const right = toggle.querySelector('.toggle-option[data-side="right"]');

        // Need to match the HTML structure (data-side or class)
        // Adjusting to support both for robustness if classes vary
        const leftEl = left || toggle.querySelector('.left');
        const rightEl = right || toggle.querySelector('.right');

        if (leftEl && rightEl) {
            if (pos === 'left') {
                leftEl.classList.add('active');
                rightEl.classList.remove('active');
            } else {
                leftEl.classList.remove('active');
                rightEl.classList.add('active');
            }
        }
    }
};

// Global Init & Delegation
document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.init();
    FontManager.init();
    LayoutManager.init();

    // Settings Menu Toggle
    document.addEventListener('click', (e) => {
        // Toggle Menu
        const trigger = e.target.closest('.settings-trigger');
        if (trigger) {
            const menu = trigger.nextElementSibling; // Assuming sibling structure
            if (menu && menu.classList.contains('settings-menu')) {
                menu.classList.toggle('show');
                e.stopPropagation();
            }
        }

        // Close on outside click
        if (!e.target.closest('.settings-dropdown')) {
            document.querySelectorAll('.settings-menu.show').forEach(m => m.classList.remove('show'));
        }

        // Toggles
        if (e.target.closest('#themeToggle')) ThemeManager.toggle();
        if (e.target.closest('#fontToggle')) FontManager.toggle();
        if (e.target.closest('#tocToggle')) LayoutManager.toggle();
    });
});

// Toast Notification
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position:fixed; bottom:20px; right:20px; z-index:99999; display:flex; flex-direction:column; gap:10px;';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const bgColor = type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6';
    const icon = type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle';

    toast.style.cssText = `
        background: ${bgColor};
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        gap: 12px;
        min-width: 300px;
        opacity: 0;
        transform: translateY(20px);
        transition: all 0.3s ease;
        font-family: 'Outfit', sans-serif;
    `;

    toast.innerHTML = `<i class="fas fa-${icon}"></i> <span>${message}</span>`;

    container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
    });

    // Remove after delay
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Immediate execution
(function () {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
})();
