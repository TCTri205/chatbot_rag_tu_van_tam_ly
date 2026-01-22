/**
 * Toast Notification System
 * Provides beautiful, non-intrusive notifications for user feedback
 */

class ToastManager {
    constructor() {
        this.container = null;
        this.init();
    }

    /**
     * Initialize toast container
     */
    init() {
        // Create container if not exists
        if (!document.getElementById('toast-container')) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'fixed bottom-4 right-4 z-50 flex flex-col gap-2';
            document.body.appendChild(this.container);
        } else {
            this.container = document.getElementById('toast-container');
        }
    }

    /**
     * Show a toast notification
     * @param {string} message - Message to display
     * @param {string} type - Toast type: 'success', 'error', 'warning', 'info'
     * @param {number} duration - Duration in milliseconds (0 = permanent)
     */
    show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} min-w-[300px] max-w-md p-4 rounded-lg shadow-lg flex items-start gap-3 animate-slide-in`;

        // Icon mapping
        const icons = {
            success: { icon: 'fa-check-circle', color: 'text-green-500' },
            error: { icon: 'fa-times-circle', color: 'text-red-500' },
            warning: { icon: 'fa-exclamation-triangle', color: 'text-yellow-500' },
            info: { icon: 'fa-info-circle', color: 'text-blue-500' }
        };

        const iconInfo = icons[type] || icons.info;

        // Build toast HTML
        toast.innerHTML = `
            <div class="flex-shrink-0">
                <i class="fas ${iconInfo.icon} ${iconInfo.color} text-xl"></i>
            </div>
            <div class="flex-1 text-sm text-gray-700">
                ${this.escapeHtml(message)}
            </div>
            <button class="close-toast flex-shrink-0 text-gray-400 hover:text-gray-600 transition">
                <i class="fas fa-times text-sm"></i>
            </button>
        `;

        // Add background color based on type
        const bgColors = {
            success: 'bg-green-50 border-l-4 border-green-500',
            error: 'bg-red-50 border-l-4 border-red-500',
            warning: 'bg-yellow-50 border-l-4 border-yellow-500',
            info: 'bg-blue-50 border-l-4 border-blue-500'
        };
        toast.classList.add(...(bgColors[type] || bgColors.info).split(' '));

        // Add to container
        this.container.appendChild(toast);

        // Close button handler
        const closeBtn = toast.querySelector('.close-toast');
        closeBtn.addEventListener('click', () => this.remove(toast));

        // Auto-remove after duration (if not permanent)
        if (duration > 0) {
            setTimeout(() => this.remove(toast), duration);
        }

        return toast;
    }

    /**
     * Remove a toast with animation
     * @param {HTMLElement} toast - Toast element to remove
     */
    remove(toast) {
        toast.classList.add('animate-slide-out');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    /**
     * Show success toast
     * @param {string} message - Success message
     * @param {number} duration - Duration in ms
     */
    success(message, duration = 3000) {
        return this.show(message, 'success', duration);
    }

    /**
     * Show error toast
     * @param {string} message - Error message
     * @param {number} duration - Duration in ms (longer for errors)
     */
    error(message, duration = 5000) {
        return this.show(message, 'error', duration);
    }

    /**
     * Show warning toast
     * @param {string} message - Warning message
     * @param {number} duration - Duration in ms
     */
    warning(message, duration = 4000) {
        return this.show(message, 'warning', duration);
    }

    /**
     * Show info toast
     * @param {string} message - Info message
     * @param {number} duration - Duration in ms
     */
    info(message, duration = 3000) {
        return this.show(message, 'info', duration);
    }

    /**
     * Clear all toasts
     */
    clearAll() {
        const toasts = this.container.querySelectorAll('.toast');
        toasts.forEach(toast => this.remove(toast));
    }

    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export as global singleton
if (typeof window !== 'undefined') {
    window.Toast = new ToastManager();
}

console.log('✅ Toast notification system loaded');
