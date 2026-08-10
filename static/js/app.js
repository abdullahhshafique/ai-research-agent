/**
 * Main application JavaScript with accessibility support.
 */

// Theme Management
const ThemeManager = {
    init() {
        const toggle = document.getElementById('theme-toggle');
        const icon = document.getElementById('theme-icon');
        const html = document.documentElement;

        const savedTheme = localStorage.getItem('theme') || 'dark';
        html.setAttribute('data-theme', savedTheme);
        this.updateIcon(icon, savedTheme);
        this.updateAriaLabel(toggle, savedTheme);

        if (toggle) {
            toggle.addEventListener('click', () => {
                const currentTheme = html.getAttribute('data-theme');
                const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                html.setAttribute('data-theme', newTheme);
                localStorage.setItem('theme', newTheme);
                this.updateIcon(icon, newTheme);
                this.updateAriaLabel(toggle, newTheme);

                // Announce theme change to screen readers
                this.announceChange(`Switched to ${newTheme} mode`);
            });
        }
    },

    updateIcon(icon, theme) {
        if (!icon) return;
        if (theme === 'dark') {
            icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"></path>';
        } else {
            icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path>';
        }
    },

    updateAriaLabel(button, theme) {
        if (button) {
            button.setAttribute('aria-label', `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`);
        }
    },

    announceChange(message) {
        const announcer = document.createElement('div');
        announcer.setAttribute('role', 'status');
        announcer.setAttribute('aria-live', 'polite');
        announcer.className = 'sr-only';
        announcer.textContent = message;
        document.body.appendChild(announcer);
        setTimeout(() => announcer.remove(), 1000);
    }
};

// Mobile Menu
const MobileMenu = {
    init() {
        const btn = document.getElementById('mobile-menu-btn');
        const menu = document.getElementById('mobile-menu');

        if (btn && menu) {
            btn.addEventListener('click', () => {
                const isHidden = menu.classList.contains('hidden');
                menu.classList.toggle('hidden');
                btn.setAttribute('aria-expanded', (!isHidden).toString());

                // Focus management
                if (!isHidden) {
                    const firstLink = menu.querySelector('a');
                    if (firstLink) firstLink.focus();
                }
            });

            // Close on escape
            menu.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    menu.classList.add('hidden');
                    btn.setAttribute('aria-expanded', 'false');
                    btn.focus();
                }
            });
        }
    }
};

// Auto-dismiss messages with screen reader announcement
//const MessageManager = {
    //init() {
        //const messages = document.querySelectorAll('.animate-fade-in');
        //messages.forEach(msg => {
            // Make messages assertive for screen readers
            //if (msg.classList.contains('bg-red-900') || msg.classList.contains('bg-green-900')) {
            //    msg.setAttribute('role', 'alert');
            //    msg.setAttribute('aria-live', 'assertive');
            //}

            //setTimeout(() => {
            //    msg.style.opacity = '0';
            //    msg.style.transition = 'opacity 0.5s';
            //    setTimeout(() => msg.remove(), 500);
            //}, 5000);
        //});
    //}
//};

// Keyboard navigation helpers
const KeyboardNavigation = {
    init() {
        // Trap focus in modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                this.handleTabNavigation(e);
            }
        });
    },

    handleTabNavigation(e) {
        const modal = document.querySelector('[role="dialog"]:not(.hidden)');
        if (!modal) return;

        const focusable = modal.querySelectorAll(
            'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );

        if (focusable.length === 0) return;

        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first.focus();
        }
    }
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.init();
    MobileMenu.init();
    //MessageManager.init();
    KeyboardNavigation.init();
});