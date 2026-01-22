/**
 * API Client for Chatbot Tâm Lý Backend
 * Handles all HTTP requests to FastAPI backend with error handling and retry logic
 */

/**
 * API Configuration
 */
const API_CONFIG = {
    BASE_URL: '/api/v1',
    TIMEOUT: 30000, // 30 seconds
    RETRY_ATTEMPTS: 3, // Number of retry attempts
    RETRY_DELAY: 1000  // Initial retry delay in ms (will be multiplied by attempt number)
};

/**
 * API Client for backend communication
 * Handles all HTTP requests with automatic retry and error handling
 */
class APIClient {
    constructor() {
        // IMPORTANT: Use relative URL to avoid CORS issues
        // When served from http://localhost:8080, relative /api/v1 will resolve to same origin
        // Avoiding http://localhost:8080 → http://localhost redirect which causes CORS
        this.baseURL = '/api/v1';
        this.maxRetries = 3;
        this.retryDelay = 1000; // 1 second
    }

    /**
     * Get session ID from state manager
     * @returns {string|null}
     */
    getSessionId() {
        return window.StateManager.getSessionId();
    }

    /**
     * Make HTTP request with error handling and retry logic
     * @param {string} url - Endpoint URL
     * @param {Object} options - Fetch options
     * @param {number} attempt - Current attempt number
     * @returns {Promise<Object>} Response data
     */
    async request(url, options = {}, attempt = 1) {
        try {
            // Add default headers
            const headers = {
                'Content-Type': 'application/json',
                ...options.headers
            };

            // Add session ID header if available
            const sessionId = this.getSessionId();
            if (sessionId && !url.includes('/sessions/init')) {
                headers['X-Session-ID'] = sessionId;
            }

            // Add Authorization header if user is authenticated
            if (window.AuthManager && window.AuthManager.isAuthenticated()) {
                const authHeader = window.AuthManager.getAuthHeader();
                if (authHeader) {
                    headers['Authorization'] = authHeader;
                    console.log('🔐 Auth header added to request:', url);
                }
            } else {
                console.log('⚠️  No auth - request sent as guest:', url);
            }

            const response = await fetch(url, {
                ...options,
                headers,
                signal: AbortSignal.timeout(API_CONFIG.TIMEOUT)
            });

            // Log response details for debugging
            console.log(`📡 Response from ${url}:`, {
                status: response.status,
                ok: response.ok,
                statusText: response.statusText,
                contentType: response.headers.get('Content-Type')
            });

            // Handle non-OK responses
            if (!response.ok) {
                let errorData;
                try {
                    const errorText = await response.text();
                    console.error('❌ Error response body:', errorText.substring(0, 500));
                    errorData = JSON.parse(errorText);
                } catch (parseError) {
                    console.error('❌ Failed to parse error response');
                    errorData = { detail: `HTTP ${response.status}` };
                }
                throw new APIError(
                    errorData.detail || `HTTP ${response.status}`,
                    response.status,
                    errorData
                );
            }

            // Parse success response with logging
            let data;
            try {
                const responseText = await response.text();
                console.log('📥 Response (first 500 chars):', responseText.substring(0, 500));
                data = JSON.parse(responseText);
                console.log('✅ JSON parsed successfully');
            } catch (parseError) {
                console.error('❌ JSON parse error:', parseError.message);
                throw new Error('Invalid JSON from server');
            }
            return data;

        } catch (error) {
            console.error(`❌ API Error (attempt ${attempt}/${API_CONFIG.RETRY_ATTEMPTS}):`, error);
            console.error('❌ Error type:', error.constructor.name);

            // Retry logic for network errors
            if (attempt < API_CONFIG.RETRY_ATTEMPTS && this.shouldRetry(error)) {
                const delay = API_CONFIG.RETRY_DELAY * attempt;
                console.log(`🔄 Retrying in ${delay}ms...`);
                await this.sleep(delay);
                return this.request(url, options, attempt + 1);
            }

            throw error;
        }
    }

    /**
     * Check if error should trigger retry
     * @param {Error} error
     * @returns {boolean}
     */
    shouldRetry(error) {
        // Retry on network errors but not on client errors (4xx)
        if (error instanceof APIError && error.status >= 400 && error.status < 500) {
            return false;
        }
        return true;
    }

    /**
     * Sleep helper for retry delay
     * @param {number} ms - Milliseconds to sleep
     * @returns {Promise}
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Helper method for GET requests
     * @param {string} endpoint - API endpoint path
     * @param {Object} params - Query parameters
     * @returns {Promise<any>}
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${this.baseURL}${endpoint}?${queryString}` : `${this.baseURL}${endpoint}`;

        return this.request(url, { method: 'GET' });
    }

    /**
     * Helper method for POST requests
     * @param {string} endpoint - API endpoint path
     * @param {Object} data - Request body data
     * @returns {Promise<any>}
     */
    async post(endpoint, data = {}) {
        return this.request(`${this.baseURL}${endpoint}`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }


    /**
     * Initialize a new session
     * POST /sessions/init/
     * @returns {Promise<Object>} Session data with session_id, conversation_id, greeting
     */
    async initSession() {
        console.log('🔄 Initializing new session...');

        const data = await this.request(`${this.baseURL}/sessions/init`, {
            method: 'POST',
            body: JSON.stringify({})
        });

        console.log('✅ Session initialized:', data);
        return data;
    }

    /**
     * Send chat message
     * POST /chat/
     * @param {string} content - User message content
     * @returns {Promise<Object>} Chat response or crisis response
     */
    async sendMessage(content) {
        if (!content || !content.trim()) {
            throw new Error('Message content cannot be empty');
        }

        const sessionId = this.getSessionId();
        if (!sessionId) {
            throw new Error('No active session. Please refresh the page.');
        }

        console.log('💬 Sending message:', content.substring(0, 50) + '...');

        const data = await this.post('/chat', { content: content.trim() });

        console.log('✅ Response received:', data);
        return data;
    }

    /**
     * Get chat history for current conversation
     * GET /chat/history/
     * @param {number} limit - Number of messages to fetch
     * @param {number} offset - Pagination offset
     * @returns {Promise<Object>} Chat history with messages array
     */
    async getChatHistory(limit = 50, offset = 0) {
        const conversationId = window.StateManager.getConversationId();
        if (!conversationId) {
            throw new Error('No active conversation');
        }

        console.log('📜 Fetching chat history...');

        const data = await this.get('/chat/history', {
            conversation_id: conversationId,
            limit: limit.toString(),
            offset: offset.toString()
        });

        console.log(`✅ Loaded ${data.messages.length} messages`);
        return data;
    }

    /**
     * Get list of conversations
     * GET /conversations/
     * @param {number} limit - Number of conversations to fetch
     * @param {number} offset - Pagination offset
     * @returns {Promise<Object>} Conversations list with metadata
     */
    async getConversations(limit = 20, offset = 0) {
        console.log('📋 Fetching conversations list...');

        const data = await this.get('/conversations/', {
            limit: limit.toString(),
            offset: offset.toString()
        });

        console.log(`✅ Loaded ${data.conversations?.length || 0} conversations`);
        return data;
    }

    /**
     * Log mood entry
     * POST /moods/
     * @param {number} moodValue - Mood value 1-5
     * @param {string} moodLabel - Mood label (happy, sad, etc.)
     * @param {string} note - Optional note
     * @returns {Promise<Object>} Mood entry response
     */
    async logMood(moodValue, moodLabel, note = '') {
        if (!moodValue || moodValue < 1 || moodValue > 5) {
            throw new Error('Mood value must be between 1 and 5');
        }

        console.log('😊 Logging mood:', { moodValue, moodLabel });

        const data = await this.post('/moods/', {
            mood_value: moodValue,
            mood_label: moodLabel,
            note: note
        });

        console.log('✅ Mood logged');
        return data;
    }

    /**
     * Get mood history
     * GET /moods/history/
     * @param {number} days - Number of days to fetch
     * @returns {Promise<Array>} Array of mood entries
     */
    async getMoodHistory(days = 7) {
        console.log(`📊 Fetching mood history (${days} days)...`);

        const data = await this.get('/moods/history/', { days: days.toString() });

        console.log(`✅ Loaded ${data.length} mood entries`);
        return data;
    }

    /**
     * Submit feedback for a message
     * POST /feedback/
     * @param {string} messageId - UUID of the message
     * @param {number} rating - 1 (like) or -1 (dislike)
     * @param {string} comment - Optional comment
     * @returns {Promise<Object>} Feedback response
     */
    async submitFeedback(messageId, rating, comment = '') {
        if (!messageId) {
            throw new Error('Message ID is required');
        }
        if (rating !== 1 && rating !== -1) {
            throw new Error('Rating must be 1 (like) or -1 (dislike)');
        }

        console.log('👍/👎 Submitting feedback:', { messageId, rating });

        const data = await this.post('/feedback', {
            message_id: messageId,
            rating: rating,
            comment: comment
        });

        console.log('✅ Feedback submitted');
        return data;
    }

    /**
     * Check API health
     * GET /api/health/
     * @returns {Promise<Object>} Health status
     */
    async checkHealth() {
        try {
            const data = await this.request('/api/health', {
                method: 'GET'
            });
            return data;
        } catch (error) {
            console.error('Health check failed:', error);
            return { status: 'error', error: error.message };
        }
    }

    /**
     * Export chat history
     * GET /conversations/export
     */
    async exportData() {
        console.log('📥 Exporting data...');
        const url = `${this.baseURL}/conversations/export`;
        const headers = {};

        // Add auth headers
        const sessionId = this.getSessionId();
        if (sessionId) headers['X-Session-ID'] = sessionId;
        if (window.AuthManager && window.AuthManager.isAuthenticated()) {
            const authHeader = window.AuthManager.getAuthHeader();
            if (authHeader) headers['Authorization'] = authHeader;
        }

        try {
            const response = await fetch(url, { headers });

            // Handle 403 (guest not authorized to export)
            if (response.status === 403) {
                console.warn('⚠️ Export requires authentication');
                if (window.Toast) {
                    window.Toast.show('Vui lòng đăng nhập để xuất dữ liệu', 'warning');
                } else {
                    alert('Vui lòng đăng nhập để xuất dữ liệu');
                }
                return false;
            }

            if (!response.ok) throw new Error('Export failed');

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;

            // Get filename from header or default
            const disposition = response.headers.get('Content-Disposition');
            let filename = 'chat_history.json';
            if (disposition && disposition.indexOf('attachment') !== -1) {
                const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                const matches = filenameRegex.exec(disposition);
                if (matches != null && matches[1]) {
                    filename = matches[1].replace(/['"]/g, '');
                }
            }

            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(downloadUrl);

            console.log('✅ Data exported successfully');
            return true;
        } catch (error) {
            console.error('Export error:', error);
            throw error;
        }
    }
}

/**
 * Custom API Error Class
 */
class APIError extends Error {
    constructor(message, status, data) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.data = data;
    }

    /**
     * Check if error is a crisis response
     * @returns {boolean}
     */
    isCrisisResponse() {
        return this.data && this.data.is_crisis === true;
    }

    /**
     * Get crisis data if available
     * @returns {Object|null}
     */
    getCrisisData() {
        if (this.isCrisisResponse()) {
            return {
                message: this.data.message,
                hotlines: this.data.hotlines || []
            };
        }
        return null;
    }
}

/**
 * Create singleton API client instance
 */
const api = new APIClient();

// Export for global access
window.API = api;
window.APIError = APIError;

console.log('✅ API Client initialized');
