// Theme Management
const ThemeManager = {
    init() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.setTheme(savedTheme);

        // Attach click handlers (Event Delegation for robustness)
        document.addEventListener('click', (e) => {
            const toggle = e.target.closest('#themeToggle');
            if (toggle) {
                this.toggle();
            }
        });
    },

    toggle() {
        console.log('Theme toggle triggered');
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        this.setTheme(next);
    },

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);

        // Update Slider UI
        const toggle = document.getElementById('themeToggle');
        if (toggle) {
            toggle.setAttribute('data-value', theme);
            const left = toggle.querySelector('.toggle-option.left');
            const right = toggle.querySelector('.toggle-option.right');
            if (left && right) {
                if (theme === 'light') {
                    left.classList.add('active');
                    right.classList.remove('active');
                } else {
                    left.classList.remove('active');
                    right.classList.add('active');
                }
            }
        }

        // Update Syntax Highlight if present
        const highlightTheme = document.getElementById('highlightTheme');
        if (highlightTheme) {
            const cssUrl = theme === 'dark'
                ? 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/tokyo-night-dark.min.css'
                : 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css';
            highlightTheme.href = cssUrl;
        }
    }
};

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.init();
});

// Immediate apply to prevent flash (also call this inline in head if possible)
(function () {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
})();
