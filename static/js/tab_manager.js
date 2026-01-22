/**
 * Tab Manager - Hybrid localStorage + Tab ID approach
 * Manages tab-specific tokens while supporting cross-page navigation
 * 
 * Architecture:
 * - Each tab has a unique TAB_ID (stored in sessionStorage)
 * - Tokens are stored in localStorage, indexed by TAB_ID
 * - Supports multi-account multi-tab AND admin redirect
 */

class TabManager {
    constructor() {
        this.TAB_ID = this.initializeTabId();
        this.STORAGE_KEY = 'tab_tokens';
        this.MAX_TOKEN_AGE = 24 * 60 * 60 * 1000; // 24 hours

        // Cleanup old tokens on initialization
        this.cleanupOldTokens();

        // Migrate old tokens if exist
        this.migrateOldTokens();

        console.log('✅ TabManager initialized with TAB_ID:', this.TAB_ID);
    }

    /**
     * Initialize or retrieve Tab ID
     * Tab ID is stored in sessionStorage (unique per tab, persists across navigation)
     */
    initializeTabId() {
        let tabId = sessionStorage.getItem('tab_id');

        if (!tabId) {
            tabId = 'tab-' + Date.now() + '-' + Math.random().toString(36).substring(2, 9);
            sessionStorage.setItem('tab_id', tabId);
            console.log('🆕 Created new TAB_ID:', tabId);
        } else {
            console.log('♻️ Reusing existing TAB_ID:', tabId);
        }

        return tabId;
    }

    /**
     * Get all tab tokens from localStorage
     */
    getAllTabTokens() {
        try {
            const data = localStorage.getItem(this.STORAGE_KEY);
            return data ? JSON.parse(data) : {};
        } catch (error) {
            console.error('Error reading tab tokens:', error);
            return {};
        }
    }

    /**
     * Save all tab tokens to localStorage
     */
    saveAllTabTokens(tabTokens) {
        try {
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(tabTokens));
        } catch (error) {
            console.error('Error saving tab tokens:', error);
        }
    }

    /**
     * Save token for current tab
     */
    saveToken(accessToken, user) {
        console.log('💾 [TabManager] Saving token for tab:', this.TAB_ID);

        const tabTokens = this.getAllTabTokens();

        tabTokens[this.TAB_ID] = {
            access_token: accessToken,
            user: user,
            created_at: Date.now()
        };

        this.saveAllTabTokens(tabTokens);

        console.log('✅ [TabManager] Token saved successfully');
        console.log('✅ [TabManager] Total tabs with tokens:', Object.keys(tabTokens).length);
    }

    /**
     * Get token for current tab
     */
    getToken() {
        const tabTokens = this.getAllTabTokens();
        const tokenData = tabTokens[this.TAB_ID];

        if (!tokenData) {
            console.log('❌ [TabManager] No token found for tab:', this.TAB_ID);
            return null;
        }

        console.log('✅ [TabManager] Token found for tab:', this.TAB_ID);
        return tokenData.access_token;
    }

    /**
     * Get user data for current tab
     */
    getUser() {
        const tabTokens = this.getAllTabTokens();
        const tokenData = tabTokens[this.TAB_ID];

        if (!tokenData) {
            return null;
        }

        return tokenData.user;
    }

    /**
     * Check if current tab is authenticated
     */
    isAuthenticated() {
        return !!this.getToken();
    }

    /**
     * Remove token for current tab
     */
    removeToken() {
        console.log('🗑️ [TabManager] Removing token for tab:', this.TAB_ID);

        const tabTokens = this.getAllTabTokens();
        delete tabTokens[this.TAB_ID];
        this.saveAllTabTokens(tabTokens);

        console.log('✅ [TabManager] Token removed successfully');
    }

    /**
     * Cleanup tokens older than MAX_TOKEN_AGE
     */
    cleanupOldTokens() {
        const tabTokens = this.getAllTabTokens();
        const now = Date.now();
        let cleanedCount = 0;

        Object.keys(tabTokens).forEach(tabId => {
            const tokenData = tabTokens[tabId];
            if (now - tokenData.created_at > this.MAX_TOKEN_AGE) {
                delete tabTokens[tabId];
                cleanedCount++;
            }
        });

        if (cleanedCount > 0) {
            this.saveAllTabTokens(tabTokens);
            console.log(`🧹 [TabManager] Cleaned up ${cleanedCount} old token(s)`);
        }
    }

    /**
     * Migrate old sessionStorage/localStorage tokens to new structure
     */
    migrateOldTokens() {
        // Check for old sessionStorage token
        const oldSessionToken = sessionStorage.getItem('access_token');
        const oldSessionUser = sessionStorage.getItem('user');

        if (oldSessionToken) {
            console.log('🔄 [TabManager] Migrating old sessionStorage token...');
            try {
                const user = oldSessionUser ? JSON.parse(oldSessionUser) : null;
                this.saveToken(oldSessionToken, user);

                // Clean up old storage
                sessionStorage.removeItem('access_token');
                sessionStorage.removeItem('user');

                console.log('✅ [TabManager] Migration from sessionStorage complete');
            } catch (error) {
                console.error('Migration error:', error);
            }
        }

        // Check for old localStorage token (from before sessionStorage change)
        const oldLocalToken = localStorage.getItem('access_token');
        const oldLocalUser = localStorage.getItem('user');

        if (oldLocalToken) {
            console.log('🔄 [TabManager] Migrating old localStorage token...');
            try {
                const user = oldLocalUser ? JSON.parse(oldLocalUser) : null;
                this.saveToken(oldLocalToken, user);

                // Clean up old storage
                localStorage.removeItem('access_token');
                localStorage.removeItem('user');

                console.log('✅ [TabManager] Migration from localStorage complete');
            } catch (error) {
                console.error('Migration error:', error);
            }
        }
    }

    /**
     * Get auth header for API requests
     */
    getAuthHeader() {
        const token = this.getToken();
        return token ? `Bearer ${token}` : null;
    }

    /**
     * Debug: Get info about current tab and all tokens
     */
    getDebugInfo() {
        const tabTokens = this.getAllTabTokens();
        return {
            currentTabId: this.TAB_ID,
            isAuthenticated: this.isAuthenticated(),
            totalTabs: Object.keys(tabTokens).length,
            allTabIds: Object.keys(tabTokens),
            currentUser: this.getUser()
        };
    }
}

// Create global instance with error handling
(function () {
    'use strict';

    console.log('🔧 [TabManager] Script loaded, starting initialization...');

    try {
        // Create the instance
        window.TabManager = new TabManager();
        console.log('✅ [TabManager] Successfully created and assigned to window.TabManager');
        console.log('✅ [TabManager] Verification:', {
            exists: !!window.TabManager,
            type: typeof window.TabManager,
            hasGetToken: typeof window.TabManager.getToken === 'function'
        });
    } catch (error) {
        console.error('❌ [TabManager] CRITICAL ERROR during initialization:', error);
        console.error('❌ [TabManager] Stack trace:', error.stack);

        // Create a fallback dummy TabManager to prevent crashes
        window.TabManager = {
            getToken: () => {
                console.error('❌ Fallback TabManager - getToken called');
                return null;
            },
            getUser: () => {
                console.error('❌ Fallback TabManager - getUser called');
                return null;
            },
            saveToken: () => {
                console.error('❌ Fallback TabManager - saveToken called');
            },
            removeToken: () => {
                console.error('❌ Fallback TabManager - removeToken called');
            },
            isAuthenticated: () => {
                console.error('❌ Fallback TabManager - isAuthenticated called');
                return false;
            },
            getDebugInfo: () => ({
                error: 'TabManager failed to initialize',
                fallback: true
            })
        };
    }
})();
