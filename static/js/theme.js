/**
 * Theme Manager Module
 * Handles light/dark mode toggle with localStorage persistence
 * Last Updated: 2025-12-20
 */

(function () {
    'use strict';

    const ThemeManager = {
        STORAGE_KEY: 'tamly-theme-preference',
        DARK_CLASS: 'dark',

        /**
         * Initialize theme on page load
         */
        init() {
            // Load saved theme or detect system preference
            const savedTheme = this.getSavedTheme();
            const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

            // Apply theme: saved preference > system preference > default light
            const theme = savedTheme || (systemPrefersDark ? 'dark' : 'light');
            this.apply(theme);

            // Listen for system theme changes
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                // Only auto-switch if user hasn't set a preference
                if (!this.getSavedTheme()) {
                    this.apply(e.matches ? 'dark' : 'light');
                }
            });

            // Setup toggle buttons
            this.setupToggleButtons();

            console.log('🎨 ThemeManager initialized:', theme);
        },

        /**
         * Get saved theme from localStorage
         * @returns {string|null} 'light', 'dark', or null
         */
        getSavedTheme() {
            try {
                return localStorage.getItem(this.STORAGE_KEY);
            } catch (e) {
                console.warn('Could not access localStorage for theme:', e);
                return null;
            }
        },

        /**
         * Save theme preference to localStorage
         * @param {string} theme - 'light' or 'dark'
         */
        saveTheme(theme) {
            try {
                localStorage.setItem(this.STORAGE_KEY, theme);
            } catch (e) {
                console.warn('Could not save theme to localStorage:', e);
            }
        },

        /**
         * Apply theme to document
         * @param {string} theme - 'light' or 'dark'
         */
        apply(theme) {
            const root = document.documentElement;

            if (theme === 'dark') {
                root.classList.add(this.DARK_CLASS);
            } else {
                root.classList.remove(this.DARK_CLASS);
            }

            // Update toggle button icons
            this.updateToggleIcons(theme);

            // Update Chart.js colors if charts exist
            this.updateChartColors(theme);
        },

        /**
         * Toggle between light and dark themes
         */
        toggle() {
            const currentTheme = this.getCurrentTheme();
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

            this.apply(newTheme);
            this.saveTheme(newTheme);

            console.log('🎨 Theme toggled to:', newTheme);
        },

        /**
         * Get current theme
         * @returns {string} 'light' or 'dark'
         */
        getCurrentTheme() {
            return document.documentElement.classList.contains(this.DARK_CLASS) ? 'dark' : 'light';
        },

        /**
         * Setup click handlers for all theme toggle buttons
         */
        setupToggleButtons() {
            // Find all theme toggle buttons
            const toggleButtons = document.querySelectorAll('[data-theme-toggle]');

            toggleButtons.forEach(button => {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.toggle();

                    // Add animation class to icon
                    const icon = button.querySelector('i');
                    if (icon) {
                        icon.classList.add('theme-icon-animate');
                        setTimeout(() => icon.classList.remove('theme-icon-animate'), 300);
                    }
                });
            });
        },

        /**
         * Update toggle button icons based on current theme
         * @param {string} theme - 'light' or 'dark'
         */
        updateToggleIcons(theme) {
            const toggleButtons = document.querySelectorAll('[data-theme-toggle]');

            toggleButtons.forEach(button => {
                const icon = button.querySelector('i');
                if (icon) {
                    // Sun icon for dark mode (click to switch to light)
                    // Moon icon for light mode (click to switch to dark)
                    icon.className = theme === 'dark'
                        ? 'fas fa-sun text-yellow-400'
                        : 'fas fa-moon text-slate-600';
                }

                // Update title/tooltip
                button.title = theme === 'dark'
                    ? 'Chuyển sang chế độ sáng'
                    : 'Chuyển sang chế độ tối';
            });
        },

        /**
         * Update Chart.js chart colors for theme
         * @param {string} theme - 'light' or 'dark'
         */
        updateChartColors(theme) {
            // Check if Chart.js is loaded
            if (typeof Chart === 'undefined') return;

            const textColor = theme === 'dark' ? '#f1f5f9' : '#1e293b';
            const gridColor = theme === 'dark' ? '#334155' : '#e2e8f0';

            // Update Chart.js defaults
            Chart.defaults.color = textColor;
            Chart.defaults.borderColor = gridColor;

            // Update existing charts if any
            Object.values(Chart.instances).forEach(chart => {
                if (chart.options.scales) {
                    // Update scale colors
                    Object.values(chart.options.scales).forEach(scale => {
                        if (scale.ticks) scale.ticks.color = textColor;
                        if (scale.grid) scale.grid.color = gridColor;
                    });
                }
                if (chart.options.plugins?.legend?.labels) {
                    chart.options.plugins.legend.labels.color = textColor;
                }
                chart.update('none'); // Update without animation
            });
        }
    };

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => ThemeManager.init());
    } else {
        ThemeManager.init();
    }

    // Expose globally for manual control if needed
    window.ThemeManager = ThemeManager;

})();
