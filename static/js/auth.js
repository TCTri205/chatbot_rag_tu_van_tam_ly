/**
 * Authentication Module
 * Handles login, register, logout flows for optional authentication
 * Guest mode remains the default - users can optionally log in for enhanced features
 */

class AuthManager {
    constructor() {
        this.baseURL = '/api/v1';

        // Use TabManager for token/user storage
        this.token = window.TabManager ? window.TabManager.getToken() : null;
        this.user = window.TabManager ? window.TabManager.getUser() : null;

        console.log('🔐 AuthManager initialized:', {
            hasToken: !!this.token,
            hasUser: !!this.user,
            username: this.user?.username
        });
    }

    /**
     * Register a new user account.
     * 
     * @param {string} email - User email
     * @param {string} password - User password (min 8 chars)
     * @param {string} username - Display username
     * @returns {Promise<Object>} User data and access token
     * @throws {Error} Registration error message
     */
    async register(email, username, password) {
        // Get current session ID
        const sessionId = window.StateManager?.getSessionId();

        const headers = { 'Content-Type': 'application/json' };

        // Add session ID if available (for updating guest session to authenticated)
        if (sessionId) {
            headers['X-Session-ID'] = sessionId;
        }

        const response = await fetch(`${this.baseURL}/auth/register/`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ email, username, password })
        });

        if (!response.ok) {
            let errorData;
            const contentType = response.headers.get("content-type");

            try {
                if (contentType && contentType.includes("application/json")) {
                    errorData = await response.json();
                } else {
                    const text = await response.text();
                    console.error('Non-JSON error response:', text);
                    throw new Error(`Server Error (${response.status})`);
                }
            } catch (e) {
                throw new Error(e.message || `Request failed with status ${response.status}`);
            }

            // Handle FastAPI validation errors (422)
            if (response.status === 422 && errorData.detail && Array.isArray(errorData.detail)) {
                const messages = errorData.detail.map(err => {
                    const field = err.loc ? err.loc[err.loc.length - 1] : 'field';
                    return `${field}: ${err.msg}`;
                }).join(', ');
                throw new Error(messages || 'Dữ liệu không hợp lệ');
            }

            // Handle other error formats
            throw new Error(errorData.detail || errorData.message || 'Đăng ký thất bại');
        }

        const data = await response.json();
        this.saveAuth(data);
        return data;
    }

    /**
     * Login with existing credentials.
     * 
     * @param {string} email - User email
     * @param {string} password - User password
     * @returns {Promise<Object>} User data and access token
     * @throws {Error} Login error message
     */
    async login(email, password) {
        console.log('AuthManager.login called with email:', email);
        // Get current session ID
        const sessionId = window.StateManager?.getSessionId();

        const headers = { 'Content-Type': 'application/json' };

        // Add session ID if available (for updating guest session to authenticated)
        if (sessionId) {
            headers['X-Session-ID'] = sessionId;
            console.log('Using session ID:', sessionId);
        }

        console.log('Sending login request to:', `${this.baseURL}/auth/login/`);

        const response = await fetch(`${this.baseURL}/auth/login/`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ email, password })
        });

        console.log('Login response status:', response.status);

        if (!response.ok) {
            let errorData;
            const contentType = response.headers.get("content-type");

            try {
                if (contentType && contentType.includes("application/json")) {
                    errorData = await response.json();
                } else {
                    // Handle non-JSON error (e.g., 500 HTML page)
                    const text = await response.text();
                    console.error('Non-JSON error response:', text);
                    throw new Error(`Server Error (${response.status})`);
                }
            } catch (e) {
                // Formatting error or other parsing issue
                throw new Error(e.message || `Request failed with status ${response.status}`);
            }

            // Handle FastAPI validation errors (422)
            if (response.status === 422 && errorData.detail && Array.isArray(errorData.detail)) {
                // Extract readable error messages from Pydantic validation errors
                const messages = errorData.detail.map(err => {
                    const field = err.loc ? err.loc[err.loc.length - 1] : 'field';
                    return `${field}: ${err.msg}`;
                }).join(', ');
                throw new Error(messages || 'Dữ liệu không hợp lệ');
            }

            // Handle other error formats (string detail)
            throw new Error(errorData.detail || errorData.message || 'Đăng nhập thất bại');
        }

        const data = await response.json();
        console.log('Login response data received');
        this.saveAuth(data);
        return data;
    }

    /**
     * Save authentication data using TabManager.
     * 
     * @param {Object} data - Response data containing access_token and user
     */
    saveAuth(data) {
        console.log('🔐 [saveAuth] Starting to save authentication data...');
        console.log('🔐 [saveAuth] Received data:', { hasToken: !!data.access_token, hasUser: !!data.user });

        // Save token and user
        this.token = data.access_token;
        this.user = data.user || null;

        // Use TabManager for storage
        if (window.TabManager) {
            window.TabManager.saveToken(data.access_token, data.user);
            console.log('✅ [saveAuth] Token saved via TabManager');
        } else {
            console.error('❌ [saveAuth] TabManager not available!');
        }

        // Fetch user profile if not included in response
        if (!data.user) {
            this.fetchUserProfile();
        }
    }

    /**
     * Fetch current user profile from API.
     */
    async fetchUserProfile() {
        try {
            const response = await fetch(`${this.baseURL}/auth/me/`, {
                headers: { 'Authorization': this.getAuthHeader() }
            });

            if (response.ok) {
                const userData = await response.json();
                this.user = userData;

                // Update user data in TabManager
                if (window.TabManager && this.token) {
                    window.TabManager.saveToken(this.token, userData);
                }
            }
        } catch (error) {
            console.error('Failed to fetch user profile:', error);
        }
    }

    /**
     * Logout and clear authentication data.
     */
    logout() {
        this.token = null;
        this.user = null;

        // Remove token via TabManager
        if (window.TabManager) {
            window.TabManager.removeToken();
        }

        // Reload page to reset to guest mode
        window.location.reload();
    }

    /**
     * Check if user is authenticated.
     * 
     * @returns {boolean} True if authenticated
     */
    isAuthenticated() {
        return !!this.token;
    }

    /**
     * Get Authorization header value.
     * 
     * @returns {string|null} Bearer token or null
     */
    getAuthHeader() {
        return this.token ? `Bearer ${this.token}` : null;
    }

    /**
     * Get current user data.
     * 
     * @returns {Object|null} User object or null
     */
    getUser() {
        return this.user;
    }
}

// Export as global singleton
if (typeof window !== 'undefined') {
    window.AuthManager = new AuthManager();

    /**
     * Debug helper: check auth status
     * Usage: Run `checkAuthStatus()` in browser console
     */
    window.checkAuthStatus = function () {
        console.log('=================================');
        console.log('🔐 Authentication Status Check');
        console.log('=================================');
        console.log('✅ Authenticated:', window.AuthManager.isAuthenticated());
        console.log('🔑 Token in memory:', window.AuthManager.token ? 'EXISTS (length: ' + window.AuthManager.token.length + ')' : 'NOT FOUND');
        console.log('👤 User:', window.AuthManager.getUser());

        if (window.TabManager) {
            const debugInfo = window.TabManager.getDebugInfo();
            console.log('📊 TabManager Info:', debugInfo);
        }

        console.log('=================================');

        return {
            hasToken: !!window.AuthManager.token,
            user: window.AuthManager.getUser(),
            tabManagerInfo: window.TabManager ? window.TabManager.getDebugInfo() : 'Not available'
        };
    };

    console.log('✅ Auth module loaded');
    console.log('💡 Debug tip: Run checkAuthStatus() in console to verify login state');
}
