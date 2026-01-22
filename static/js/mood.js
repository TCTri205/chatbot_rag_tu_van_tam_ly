/**
 * Mood Tracker Module
 * Handles mood logging and history visualization
 */

class MoodTracker {
    constructor() {
        this.moodLevels = [
            { value: 1, label: 'angry', emoji: '😠', color: '#ef4444', text: 'Tức giận' },
            { value: 2, label: 'sad', emoji: '😢', color: '#f59e0b', text: 'Buồn bã' },
            { value: 3, label: 'neutral', emoji: '😐', color: '#6b7280', text: 'Bình thường' },
            { value: 4, label: 'happy', emoji: '😊', color: '#10b981', text: 'Vui vẻ' },
            { value: 5, label: 'excited', emoji: '🤩', color: '#8b5cf6', text: 'Phấn khích' }
        ];
        this.selectedMood = null;
        this.chartInstance = null; // Chart.js instance
    }

    /**
     * Log mood entry
     * @param {number} moodValue - Mood value 1-5
     * @param {string} moodLabel - Mood label
     * @param {string} note - Optional note
     * @returns {Promise<Object>} Mood entry response
     */
    async logMood(moodValue, moodLabel, note = '') {
        if (!window.AuthManager || !window.AuthManager.isAuthenticated()) {
            throw new Error('Vui lòng đăng nhập để sử dụng tính năng này');
        }

        const response = await window.API.logMood(moodValue, moodLabel, note);
        return response;
    }

    /**
     * Get mood history
     * @param {number} days - Number of days to fetch
     * @returns {Promise<Array>} Array of mood entries
     */
    async getMoodHistory(days = 7) {
        if (!window.AuthManager || !window.AuthManager.isAuthenticated()) {
            throw new Error('Vui lòng đăng nhập để xem lịch sử');
        }

        const data = await window.API.getMoodHistory(days);
        return data;
    }

    /**
     * Render mood history chart using Chart.js
     * @param {HTMLElement} container - Container element (now unused, we use canvas)
     * @param {Array} data - Mood history data
     */
    renderChart(container, data) {
        const chartContainer = document.getElementById('mood-chart-container');
        const listContainer = document.getElementById('mood-history-container');
        const canvas = document.getElementById('moodHistoryChart');

        // Destroy existing chart if any
        if (this.chartInstance) {
            this.chartInstance.destroy();
            this.chartInstance = null;
        }

        if (!data || data.length === 0) {
            // Hide chart, show empty message in list container
            if (chartContainer) chartContainer.classList.add('hidden');
            if (listContainer) {
                listContainer.classList.remove('hidden');
                listContainer.innerHTML = '<p class="text-center text-gray-400 py-4">Chưa có dữ liệu tâm trạng</p>';
            }
            return;
        }

        // Show chart container
        if (chartContainer) chartContainer.classList.remove('hidden');
        if (listContainer) listContainer.classList.add('hidden');

        // Prepare data for chart (reverse to show oldest first)
        const sortedData = [...data].reverse();

        const labels = sortedData.map(entry => {
            // Backend returns UTC timestamps without 'Z' suffix
            let timestamp = entry.created_at;
            if (!timestamp.endsWith('Z') && !timestamp.includes('+') && !timestamp.includes('-', 10)) {
                timestamp = timestamp + 'Z';
            }
            const date = new Date(timestamp);
            return date.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
        });


        const values = sortedData.map(entry => entry.mood_value);

        const ctx = canvas.getContext('2d');

        this.chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Tâm trạng',
                    data: values,
                    borderColor: 'rgb(168, 85, 247)', // Purple
                    backgroundColor: 'rgba(168, 85, 247, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.3,
                    pointBackgroundColor: values.map(v => this.getMoodInfo(v).color),
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const moodInfo = this.getMoodInfo(context.raw);
                                return `${moodInfo.emoji} ${moodInfo.text}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        min: 0.5,
                        max: 5.5,
                        ticks: {
                            stepSize: 1,
                            callback: (value) => {
                                const moodInfo = this.getMoodInfo(value);
                                return moodInfo ? moodInfo.emoji : '';
                            }
                        },
                        grid: {
                            color: 'rgba(0,0,0,0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    /**
     * Get mood info by value
     * @param {number} value - Mood value
     * @returns {Object} Mood info
     */
    getMoodInfo(value) {
        return this.moodLevels.find(m => m.value === value) || this.moodLevels[2];
    }

    /**
     * Get emoji by value
     * @param {number} value - Mood value
     * @returns {string} Emoji
     */
    getEmoji(value) {
        const mood = this.getMoodInfo(value);
        return mood.emoji;
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

    /**
     * Set selected mood
     * @param {number} value - Mood value
     */
    setSelectedMood(value) {
        this.selectedMood = value;
    }

    /**
     * Get selected mood
     * @returns {number|null} Selected mood value
     */
    getSelectedMood() {
        return this.selectedMood;
    }

    /**
     * Clear selected mood
     */
    clearSelectedMood() {
        this.selectedMood = null;
    }
}

// Export as global singleton
if (typeof window !== 'undefined') {
    window.MoodTracker = new MoodTracker();
}

console.log('✅ MoodTracker module loaded');
