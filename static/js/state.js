/**
 * State Management Module for Chatbot Tâm Lý
 * Handles session persistence, disclaimer acceptance, and app state
 */

/**
 * Application State Object
 * Centralized state management for the chatbot
 */
const AppState = {
    // Session data
    sessionId: null,
    conversationId: null,

    // User preferences
    disclaimerAccepted: false,

    // Connection status
    isConnected: true,

    // UI state
    isChatDisabled: false,
    isTyping: false,

    // Storage keys
    STORAGE_KEYS: {
        SESSION_ID: 'chatbot_session_id',
        CONVERSATION_ID: 'chatbot_conversation_id',
        DISCLAIMER: 'chatbot_disclaimer_accepted'
    }
};

/**
 * Initialize state from storage
 * Loads session data and disclaimer status
 */
function initializeState() {
    // Load disclaimer status from localStorage (persists across tabs)
    const disclaimerStatus = localStorage.getItem(AppState.STORAGE_KEYS.DISCLAIMER);
    AppState.disclaimerAccepted = disclaimerStatus === 'true';

    // Load session data from sessionStorage (unique per tab)
    const sessionId = sessionStorage.getItem(AppState.STORAGE_KEYS.SESSION_ID);
    const conversationId = sessionStorage.getItem(AppState.STORAGE_KEYS.CONVERSATION_ID);

    if (sessionId) {
        AppState.sessionId = sessionId;
        console.log('✅ Session restored:', sessionId);
    }

    if (conversationId) {
        AppState.conversationId = conversationId;
        console.log('✅ Conversation restored:', conversationId);
    }

    return {
        hasSession: !!(sessionId && conversationId),
        disclaimerAccepted: AppState.disclaimerAccepted
    };
}

/**
 * Save session data to sessionStorage
 * @param {string} sessionId - UUID of the session (required)
 * @param {string|null} conversationId - UUID of the conversation (can be null for lazy creation)
 */
function saveSession(sessionId, conversationId) {
    // Only sessionId is required; conversationId can be null (lazy creation)
    if (!sessionId) {
        console.error('❌ Cannot save session: session_id is required');
        return false;
    }

    AppState.sessionId = sessionId;
    sessionStorage.setItem(AppState.STORAGE_KEYS.SESSION_ID, sessionId);

    // Handle conversation_id (can be null for lazy creation)
    if (conversationId) {
        AppState.conversationId = conversationId;
        sessionStorage.setItem(AppState.STORAGE_KEYS.CONVERSATION_ID, conversationId);
        console.log('💾 Session saved:', { sessionId, conversationId });
    } else {
        // Lazy creation: no conversation yet
        AppState.conversationId = null;
        sessionStorage.removeItem(AppState.STORAGE_KEYS.CONVERSATION_ID);
        console.log('💾 Session saved (conversation pending):', { sessionId, conversationId: 'pending' });
    }

    return true;
}

/**
 * Load session data from sessionStorage
 * @returns {Object|null} Session data or null if session_id not found
 */
function loadSession() {
    const sessionId = sessionStorage.getItem(AppState.STORAGE_KEYS.SESSION_ID);
    const conversationId = sessionStorage.getItem(AppState.STORAGE_KEYS.CONVERSATION_ID);

    // Only sessionId is required; conversationId can be null (lazy creation)
    if (sessionId) {
        AppState.sessionId = sessionId;
        AppState.conversationId = conversationId || null;

        return {
            sessionId,
            conversationId: conversationId || null  // Can be null for lazy creation
        };
    }

    return null;
}

/**
 * Clear session data (logout or session end)
 */
function clearSession() {
    AppState.sessionId = null;
    AppState.conversationId = null;

    sessionStorage.removeItem(AppState.STORAGE_KEYS.SESSION_ID);
    sessionStorage.removeItem(AppState.STORAGE_KEYS.CONVERSATION_ID);

    console.log('🗑️ Session cleared');
}

/**
 * Check if user has accepted disclaimer
 * @returns {boolean}
 */
function hasAcceptedDisclaimer() {
    const status = localStorage.getItem(AppState.STORAGE_KEYS.DISCLAIMER);
    return status === 'true';
}

/**
 * Mark disclaimer as accepted
 * Persists across all tabs and browser sessions
 */
function acceptDisclaimer() {
    AppState.disclaimerAccepted = true;
    localStorage.setItem(AppState.STORAGE_KEYS.DISCLAIMER, 'true');
    console.log('✅ Disclaimer accepted');
}

/**
 * Reset disclaimer (for testing)
 */
function resetDisclaimer() {
    AppState.disclaimerAccepted = false;
    localStorage.removeItem(AppState.STORAGE_KEYS.DISCLAIMER);
    console.log('🔄 Disclaimer reset');
}

/**
 * Update connection status
 * @param {boolean} isConnected
 */
function setConnectionStatus(isConnected) {
    AppState.isConnected = isConnected;
    updateConnectionUI(isConnected);
}

/**
 * Update connection status UI indicator
 * @param {boolean} isConnected
 */
function updateConnectionUI(isConnected) {
    const statusElement = document.getElementById('connection-status');
    if (statusElement) {
        if (isConnected) {
            statusElement.innerHTML = '<span class="text-green-600">● Online</span>';
            statusElement.title = 'Kết nối ổn định';
        } else {
            statusElement.innerHTML = '<span class="text-red-600">● Offline</span>';
            statusElement.title = 'Mất kết nối';
        }
    }
}

/**
 * Disable chat input and send button
 * Used when crisis detected or connection lost
 */
function disableChat(reason = '') {
    AppState.isChatDisabled = true;

    const input = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-button');

    if (input) {
        input.disabled = true;
        input.placeholder = reason || 'Chat đã bị tạm khóa';
    }

    if (sendBtn) {
        sendBtn.disabled = true;
    }

    console.log('🔒 Chat disabled:', reason);
}

/**
 * Enable chat input and send button
 */
function enableChat() {
    AppState.isChatDisabled = false;

    const input = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-button');

    if (input) {
        input.disabled = false;
        input.placeholder = 'Hãy chia sẻ câu chuyện của bạn...';
    }

    if (sendBtn) {
        sendBtn.disabled = false;
    }

    console.log('🔓 Chat enabled');
}

/**
 * Set typing indicator state
 * @param {boolean} isTyping
 */
function setTypingState(isTyping) {
    AppState.isTyping = isTyping;
}

/**
 * Get current session ID
 * @returns {string|null}
 */
function getSessionId() {
    return AppState.sessionId;
}

/**
 * Get current conversation ID
 * @returns {string|null}
 */
function getConversationId() {
    return AppState.conversationId;
}

/**
 * Check if app has active session
 * @returns {boolean}
 */
function hasActiveSession() {
    return !!(AppState.sessionId && AppState.conversationId);
}

/**
 * Debug: Log current state
 */
function debugState() {
    console.log('📊 Current App State:', {
        sessionId: AppState.sessionId,
        conversationId: AppState.conversationId,
        disclaimerAccepted: AppState.disclaimerAccepted,
        isConnected: AppState.isConnected,
        isChatDisabled: AppState.isChatDisabled,
        isTyping: AppState.isTyping
    });
}

// Export for use in other modules
// Note: Using global scope for simplicity (no module bundler)
window.AppState = AppState;
window.StateManager = {
    initializeState,
    saveSession,
    loadSession,
    clearSession,
    hasAcceptedDisclaimer,
    acceptDisclaimer,
    resetDisclaimer,
    setConnectionStatus,
    updateConnectionUI,
    disableChat,
    enableChat,
    setTypingState,
    getSessionId,
    getConversationId,
    hasActiveSession,
    debugState
};

console.log('✅ State Manager initialized');
