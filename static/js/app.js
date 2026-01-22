/**
 * Main Application Logic for Chatbot Tâm Lý
 * Handles UI interactions, chat flow, and user events
 */

/**
 * Application initialization
 * Runs when DOM is fully loaded
 */
document.addEventListener('DOMContentLoaded', async function () {
    console.log('🚀 Initializing Chatbot Application...');

    try {
        // Initialize state manager
        const state = window.StateManager.initializeState();

        // Setup event listeners
        setupEventListeners();

        // Check disclaimer
        if (!state.disclaimerAccepted) {
            showDisclaimerModal();
        } else {
            // Initialize session
            await initializeApp();
        }

        // Check connection health
        checkConnectionHealth();

    } catch (error) {
        console.error('❌ App initialization error:', error);
        showError('Không thể khởi tạo ứng dụng. Vui lòng tải lại trang.');
    }
});

/**
 * Initialize application after disclaimer accepted
 */
async function initializeApp() {
    try {
        // Check if we have existing session
        const existingSession = window.StateManager.loadSession();

        if (existingSession) {
            console.log('✅ Existing session found, loading history...');
            await loadChatHistory();
        } else {
            console.log('🆕 No existing session, creating new...');
            await createNewSession();
        }

        // Load conversations list (for authenticated users or guest with current conversation)
        await loadConversationsList();

        // Enable chat input
        window.StateManager.enableChat();

        // Focus input
        const input = document.getElementById('user-input');
        if (input) input.focus();

    } catch (error) {
        console.error('❌ App initialization failed:', error);
        showError('Không thể khởi tạo phiên chat. Vui lòng tải lại trang.');
    }
}

/**
 * Create new chat session
 */
async function createNewSession() {
    try {
        const response = await window.API.initSession();

        // Save session to state
        // Note: conversation_id may be null initially (lazy creation on first message)
        window.StateManager.saveSession(
            response.session_id,
            response.conversation_id || null  // Handle null/undefined
        );

        // Display greeting message
        if (response.greeting) {
            appendMessage('assistant', response.greeting, [], false);
        }

        console.log('✅ New session created (conversation will be created on first message)');

    } catch (error) {
        console.error('❌ Failed to create session:', error);
        throw error;
    }
}

/**
 * Load chat history from backend
 */
async function loadChatHistory() {
    try {
        const history = await window.API.getChatHistory(50, 0);

        if (history.messages && history.messages.length > 0) {
            // Clear chat container
            const container = document.getElementById('chat-container');
            if (container) {
                container.innerHTML = '';
            }

            // Render messages
            history.messages.forEach(msg => {
                const sources = msg.rag_sources || [];
                appendMessage(msg.role, msg.content, sources, msg.is_sos, false);
            });

            // Scroll to bottom
            scrollToBottom();

            console.log(`✅ Loaded ${history.messages.length} messages from history`);
        }

    } catch (error) {
        console.error('❌ Failed to load history:', error);

        // Handle 403 Forbidden - conversation doesn't belong to current user
        // This happens when user was guest, started conversation, then logged in
        if (error.status === 403) {
            console.log('⚠️ Conversation access denied - creating new session for authenticated user');
            try {
                // Clear stale session and create new one
                window.StateManager.clearSession();
                await createNewSession();
                console.log('✅ New session created for authenticated user');
            } catch (sessionError) {
                console.error('❌ Failed to create new session:', sessionError);
            }
        }
        // Non-critical error for other cases, continue anyway
    }
}

/**
 * Load conversations list from backend and render in sidebar
 */
async function loadConversationsList() {
    try {
        console.log('📋 Loading conversations list...');
        const response = await window.API.getConversations(20, 0);

        if (response && response.conversations) {
            renderConversations(response.conversations);
            console.log(`✅ Rendered ${response.conversations.length} conversations`);
        } else {
            renderConversations([]);
        }
    } catch (error) {
        console.error('❌ Failed to load conversations list:', error);
        // Show error state in sidebar
        const historyList = document.getElementById('history-list');
        if (historyList) {
            historyList.innerHTML = `
                <div class="text-xs text-red-400 dark:text-red-500 text-center py-4">
                    <i class="fas fa-exclamation-triangle text-lg mb-2 block"></i>
                    <p>Không thể tải lịch sử chat</p>
                </div>
            `;
        }
    }
}

/**
 * Render conversations list in sidebar
 * @param {Array} conversations - Array of conversation objects
 */
function renderConversations(conversations) {
    const historyList = document.getElementById('history-list');
    if (!historyList) return;

    // Empty state
    if (!conversations || conversations.length === 0) {
        historyList.innerHTML = `
            <div class="text-xs text-slate-400 dark:text-slate-500 text-center py-4">
                <i class="fas fa-clock text-lg mb-2 block"></i>
                <p>Lịch sử chat sẽ hiển thị ở đây</p>
            </div>
        `;
        return;
    }

    // Get current conversation ID
    const currentConversationId = window.StateManager.getConversationId();

    // Render conversation items
    historyList.innerHTML = conversations.map(conv => {
        const isActive = conv.id === currentConversationId;
        const timestamp = formatTimestamp(conv.updated_at || conv.created_at);
        const title = conv.title || 'Cuộc trò chuyện mới';

        return `
            <div class="conversation-item p-3 rounded-lg cursor-pointer transition-all duration-200
                ${isActive ? 'bg-primary/10 dark:bg-primary/20 border-l-4 border-primary' : 'hover:bg-slate-100 dark:hover:bg-slate-700'}
                group"
                data-conversation-id="${conv.id}"
                onclick="selectConversation('${conv.id}')">
                <div class="flex items-start justify-between mb-1">
                    <h4 class="font-medium text-sm text-slate-800 dark:text-slate-100 truncate flex-1 pr-2">
                        ${escapeHtml(title)}
                    </h4>
                    <button class="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-500 transition-opacity"
                        onclick="event.stopPropagation(); deleteConversation('${conv.id}')"
                        title="Xóa cuộc trò chuyện">
                        <i class="fas fa-trash-alt text-xs"></i>
                    </button>
                </div>
                <p class="text-xs text-slate-500 dark:text-slate-400">
                    <i class="fas fa-clock mr-1"></i>${timestamp}
                </p>
            </div>
        `;
    }).join('');
}

/**
 * Select and load a conversation
 * @param {string} conversationId - UUID of conversation to load
 */
async function selectConversation(conversationId) {
    try {
        console.log('🔄 Switching to conversation:', conversationId);

        // Update state with new conversation ID
        window.StateManager.saveSession(
            window.StateManager.getSessionId(),
            conversationId
        );

        // Clear chat container
        const container = document.getElementById('chat-container');
        if (container) {
            container.innerHTML = '';
        }

        // Load conversation messages
        await loadChatHistory();

        // Update sidebar highlighting
        await loadConversationsList();

        // Scroll to bottom
        scrollToBottom();

        console.log('✅ Conversation switched successfully');
    } catch (error) {
        console.error('❌ Failed to switch conversation:', error);
        showError('Không thể tải cuộc trò chuyện. Vui lòng thử lại.');
    }
}

/**
 * Delete a conversation (archive it)
 * @param {string} conversationId - UUID of conversation to delete
 */
async function deleteConversation(conversationId) {
    if (!confirm('Bạn có chắc muốn xóa cuộc trò chuyện này?')) {
        return;
    }

    try {
        console.log('🗑️ Deleting conversation:', conversationId);

        const response = await fetch(`/api/v1/conversations/${conversationId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                ...(window.AuthManager?.isAuthenticated() ?
                    { 'Authorization': window.AuthManager.getAuthHeader() } : {}),
                ...(window.StateManager.getSessionId() ?
                    { 'X-Session-ID': window.StateManager.getSessionId() } : {})
            }
        });

        if (!response.ok) {
            throw new Error('Failed to delete conversation');
        }

        // If deleted conversation is current, create new one
        if (conversationId === window.StateManager.getConversationId()) {
            await handleNewChat();
        } else {
            // Just refresh the list
            await loadConversationsList();
        }

        showSuccess('Đã xóa cuộc trò chuyện');
        console.log('✅ Conversation deleted');
    } catch (error) {
        console.error('❌ Failed to delete conversation:', error);
        showError('Không thể xóa cuộc trò chuyện');
    }
}

/**
 * Format timestamp to relative time
 * @param {string} timestamp - ISO timestamp from backend (UTC without timezone indicator)
 * @returns {string} Formatted relative time
 */
function formatTimestamp(timestamp) {
    if (!timestamp) return '';

    // Backend returns UTC timestamps without 'Z' suffix
    // We need to append 'Z' to ensure JavaScript interprets it as UTC
    let utcTimestamp = timestamp;
    if (!timestamp.endsWith('Z') && !timestamp.includes('+') && !timestamp.includes('-', 10)) {
        utcTimestamp = timestamp + 'Z';
    }

    const date = new Date(utcTimestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Vừa xong';
    if (diffMins < 60) return `${diffMins} phút trước`;
    if (diffHours < 24) return `${diffHours} giờ trước`;
    if (diffDays < 7) return `${diffDays} ngày trước`;

    // Format as date
    return date.toLocaleDateString('vi-VN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}


/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Setup all event listeners
 */
function setupEventListeners() {
    // Send button click
    const sendBtn = document.getElementById('send-button');
    if (sendBtn) {
        sendBtn.addEventListener('click', handleSendMessage);
    }

    // Input Enter key (without Shift)
    const input = document.getElementById('user-input');
    if (input) {
        input.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
            }
        });

        // Auto-resize textarea
        input.addEventListener('input', function () {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
    }

    // New chat button
    const newChatBtn = document.getElementById('new-chat-button');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', handleNewChat);
    }

    // Disclaimer modal buttons
    const disclaimerAcceptBtn = document.getElementById('disclaimer-accept');
    const disclaimerDeclineBtn = document.getElementById('disclaimer-decline');

    if (disclaimerAcceptBtn) {
        disclaimerAcceptBtn.addEventListener('click', handleDisclaimerAccept);
    }

    if (disclaimerDeclineBtn) {
        disclaimerDeclineBtn.addEventListener('click', handleDisclaimerDecline);
    }

    // Safety modal close button
    const safetyCloseBtn = document.getElementById('safety-modal-close');
    if (safetyCloseBtn) {
        safetyCloseBtn.addEventListener('click', closeSafetyModal);
    }

    // Auth modal buttons
    const authButton = document.getElementById('auth-button');
    const loginTab = document.getElementById('login-tab');
    const registerTab = document.getElementById('register-tab');
    const loginForm = document.getElementById('login-form-element');
    const registerForm = document.getElementById('register-form-element');
    const closeAuthModal = document.getElementById('close-auth-modal');

    if (authButton) {
        authButton.addEventListener('click', handleAuthButton);
    }

    if (loginTab) {
        loginTab.addEventListener('click', () => switchAuthTab('login'));
    }

    if (registerTab) {
        registerTab.addEventListener('click', () => switchAuthTab('register'));
    }

    if (loginForm) {
        console.log('Login form listener attached');
        loginForm.addEventListener('submit', handleLogin);
    }

    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }

    if (closeAuthModal) {
        closeAuthModal.addEventListener('click', hideAuthModal);
    }

    // Update auth UI on page load
    updateAuthUI();

    // Mood modal buttons
    const moodButton = document.getElementById('mood-button');
    const closeMoodModal = document.getElementById('close-mood-modal');
    const submitMoodBtn = document.getElementById('submit-mood');

    if (moodButton) {
        moodButton.addEventListener('click', handleMoodButtonClick);
    }

    if (closeMoodModal) {
        closeMoodModal.addEventListener('click', hideMoodModal);
    }

    if (submitMoodBtn) {
        submitMoodBtn.addEventListener('click', handleMoodSubmit);
    }

    // Mood emoji buttons (add listeners to all)
    document.querySelectorAll('.mood-btn').forEach(btn => {
        btn.addEventListener('click', handleMoodSelect);
    });

    // Exercises modal buttons
    const exercisesButton = document.getElementById('exercises-button');
    const closeExercisesModal = document.getElementById('close-exercises-modal');

    if (exercisesButton) {
        exercisesButton.addEventListener('click', handleExercisesButtonClick);
    }

    if (closeExercisesModal) {
        closeExercisesModal.addEventListener('click', hideExercisesModal);
    }
}

/**
 * Handle send message event
 */
async function handleSendMessage() {
    const input = document.getElementById('user-input');
    if (!input) return;

    const content = input.value.trim();

    // Validate input
    if (!content) {
        return;
    }

    // Check if chat is disabled
    if (window.AppState.isChatDisabled) {
        showError('Chat đang bị khóa. Vui lòng liên hệ đường dây nóng hỗ trợ.');
        return;
    }

    // Clear input immediately (optimistic UI)
    input.value = '';
    input.style.height = 'auto';

    // Display user message
    appendMessage('user', content, [], false);

    // Show typing indicator
    showTypingIndicator();

    // Disable input while processing
    input.disabled = true;
    const sendBtn = document.getElementById('send-button');
    if (sendBtn) sendBtn.disabled = true;


    try {
        // Send message to API
        const response = await window.API.sendMessage(content);
        console.log('📥 Raw API response:', response);  // Debug log

        // Hide typing indicator
        hideTypingIndicator();

        // Defensive: Check response validity
        if (!response) {
            throw new Error('Empty response from server');
        }

        // Check if crisis detected
        const isCrisis = response.is_crisis === true;

        if (isCrisis) {
            handleCrisisResponse(response);
        } else {
            // LAZY CONVERSATION: If response contains conversation_id, save it
            // This happens when conversation was created on first message
            if (response.conversation_id && !window.StateManager.getConversationId()) {
                console.log('📝 Saving conversation_id from lazy creation:', response.conversation_id);
                window.StateManager.saveSession(
                    window.StateManager.getSessionId(),
                    response.conversation_id
                );
                // Refresh conversations list to show the new conversation
                loadConversationsList();
            }

            // DEFENSIVE PARSING: Ensure sources is always an array
            let sources = [];
            if (response.sources) {
                if (Array.isArray(response.sources)) {
                    sources = response.sources;
                } else {
                    console.warn('⚠️ sources is not an array:', typeof response.sources, response.sources);
                    sources = [];
                }
            }

            // DEFENSIVE: Handle message ID (backend uses message_id, not id)
            const messageId = response.message_id || response.id || null;

            // DEFENSIVE: Ensure content exists
            const contentText = response.content || 'Xin lỗi, không nhận được phản hồi.';

            console.log(`✅ Parsed response: ${contentText.length} chars, ${sources.length} sources, msgId=${messageId ? messageId.substring(0, 8) + '...' : 'none'}`);

            // Display bot response with feedback buttons
            appendMessage('assistant', contentText, sources, false, true, messageId);

            // Update clear history button visibility
            if (typeof updateClearHistoryButtonVisibility === 'function') {
                updateClearHistoryButtonVisibility();
            }
        }

    } catch (error) {
        hideTypingIndicator();
        console.error('❌ Send message error:', error);
        console.error('❌ Error name:', error.name);
        console.error('❌ Error message:', error.message);
        if (error.stack) console.error('❌ Error stack:', error.stack);

        // Check if it's a crisis response disguised as error
        if (error instanceof window.APIError) {
            const crisisData = error.getCrisisData();
            if (crisisData) {
                handleCrisisResponse(crisisData);
                return;
            }
        }

        showError('Không thể gửi tin nhắn. Vui lòng thử lại.');
        appendMessage('assistant', 'Xin lỗi, có lỗi xảy ra. Vui lòng thử lại sau.', [], false);


    } finally {
        // Re-enable input
        input.disabled = false;
        if (sendBtn) sendBtn.disabled = false;
        input.focus();
    }
}

/**
 * Handle crisis response
 * @param {Object} crisisData - Crisis response data
 */
function handleCrisisResponse(crisisData) {
    console.warn('⚠️ Crisis detected:', crisisData);

    // Show safety modal with hotlines
    showSafetyModal(crisisData.hotlines || []);

    // Disable chat
    window.StateManager.disableChat('Vui lòng liên hệ đường dây nóng ngay');

    // Display crisis message in chat
    const message = crisisData.message || 'Chúng tôi rất lo lắng cho bạn. Vui lòng liên hệ ngay với đường dây nóng hỗ trợ tâm lý.';
    appendMessage('assistant', message, [], true);
}

/**
 * Handle new chat button
 */
async function handleNewChat() {
    if (!confirm('Bạn có chắc muốn bắt đầu cuộc trò chuyện mới?')) {
        return;
    }

    try {
        // Clear session
        window.StateManager.clearSession();

        // Clear chat UI
        const container = document.getElementById('chat-container');
        if (container) {
            container.innerHTML = '';
        }

        // Create new session
        await createNewSession();

        // Refresh conversation list
        await loadConversationsList();

        // Enable chat
        window.StateManager.enableChat();

    } catch (error) {
        console.error('❌ Failed to create new chat:', error);
        showError('Không thể tạo cuộc trò chuyện mới.');
    }
}

/**
 * Append a message to the chat container.
 * 
 * @param {string} role - 'user' or 'assistant'
 * @param {string} content - Message text content
 * @param {Array} sources - RAG sources (for assistant only)
 * @param {boolean} isSOS - Whether message triggered crisis mode
 * @param {boolean} animate - Whether to animate message appearance
 * @param {string|null} messageId - Message ID for feedback (assistant messages only)
 */
function appendMessage(role, content, sources = [], isSOS = false, animate = true, messageId = null) {
    const messagesContainer = document.getElementById('chat-container'); // Changed to chat-container to match existing HTML
    if (!messagesContainer) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'} mb-4 ${animate ? 'fade-in' : ''}`;

    // Create message bubble
    const bubble = document.createElement('div');
    bubble.className = `message-bubble ${role === 'user' ? 'message-user' : 'message-assistant'}`;

    // Add SOS styling if needed
    if (isSOS) {
        bubble.classList.add('border-red-500', 'border-2', 'bg-red-50', 'dark:bg-red-900/30');
    }

    // Add content (handle markdown if needed)
    const contentDiv = document.createElement('div');
    contentDiv.className = 'prose prose-sm max-w-none';

    // Simple markdown rendering (basic support)
    contentDiv.innerHTML = formatMessageContent(content);
    bubble.appendChild(contentDiv);

    // Add sources if available
    if (sources && sources.length > 0) {
        const sourcesDiv = createSourcesElement(sources);
        bubble.appendChild(sourcesDiv);
    }

    // Add feedback buttons for assistant messages (if messageId provided and not SOS)
    if (role === 'assistant' && messageId && !isSOS) {
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'flex gap-2 mt-3 pt-3 border-t border-slate-200 dark:border-slate-600';
        feedbackDiv.innerHTML = `
            <button class="feedback-btn text-slate-400 dark:text-slate-500 hover:text-emerald-500 dark:hover:text-emerald-400 transition p-1 rounded" 
                data-message-id="${messageId}" data-rating="1" title="Hữu ích">
                <i class="fas fa-thumbs-up"></i>
            </button>
            <button class="feedback-btn text-slate-400 dark:text-slate-500 hover:text-red-500 dark:hover:text-red-400 transition p-1 rounded" 
                data-message-id="${messageId}" data-rating="-1" title="Không hữu ích">
                <i class="fas fa-thumbs-down"></i>
            </button>
        `;
        bubble.appendChild(feedbackDiv);

        // Add event listeners to feedback buttons
        feedbackDiv.querySelectorAll('.feedback-btn').forEach(btn => {
            btn.addEventListener('click', handleFeedback);
        });
    }

    messageDiv.appendChild(bubble);
    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    scrollToBottom();
}

/**
 * Format message content (basic markdown support)
 * @param {string} content
 * @returns {string} Formatted HTML
 */
function formatMessageContent(content) {
    if (!content) return '';

    // First: Remove any stray HTML-like tags from AI response (backup sanitization)
    // This catches cases where backend sanitization missed some tags
    content = content.replace(/<\/?[a-zA-Z][a-zA-Z0-9]*[^>]*\/?>/g, '');
    content = content.replace(/<\/?\s*\w+\s*>/g, '');

    // Escape HTML
    let formatted = content
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Bold: **text**
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic: *text*
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Line breaks
    formatted = formatted.replace(/\n/g, '<br>');

    return formatted;
}

/**
 * Create sources display element
 * @param {Array} sources - Array of source objects
 * @returns {HTMLElement}
 */
function createSourcesElement(sources) {
    const sourcesDiv = document.createElement('div');
    sourcesDiv.className = 'mt-3 pt-3 border-t border-slate-200 dark:border-slate-600';

    const title = document.createElement('div');
    title.className = 'text-xs font-semibold text-slate-600 dark:text-slate-300 mb-2';
    title.textContent = '📚 Nguồn tham khảo:';
    sourcesDiv.appendChild(title);

    sources.forEach(source => {
        const sourceItem = document.createElement('div');
        sourceItem.className = 'text-xs text-slate-500 dark:text-slate-400 ml-2 source-item pl-2 py-1';
        sourceItem.textContent = `• ${source.title}${source.page ? `, trang ${source.page}` : ''}`;
        sourcesDiv.appendChild(sourceItem);
    });

    return sourcesDiv;
}

/**
 * Handle feedback button click
 * @param {Event} event - Click event
 */
async function handleFeedback(event) {
    const button = event.currentTarget;
    const messageId = button.dataset.messageId;
    const rating = parseInt(button.dataset.rating);

    // Disable all feedback buttons for this message
    const feedbackDiv = button.parentElement;
    const allButtons = feedbackDiv.querySelectorAll('.feedback-btn');
    allButtons.forEach(btn => btn.disabled = true);

    try {
        // Map rating to 1-5 scale (1=thumbs down, 5=thumbs up)
        const apiRating = rating > 0 ? 5 : 1;
        const sentiment = rating > 0 ? 'positive' : 'negative';

        await window.API.post('/feedback/', {
            message_id: messageId,
            rating: apiRating,
            comment: sentiment
        });

        // Visual confirmation
        button.classList.remove('text-gray-400');
        button.classList.add(rating > 0 ? 'text-green-500' : 'text-red-500');

        // Add checkmark or confirmation
        const confirmation = document.createElement('span');
        confirmation.className = 'text-xs text-gray-500 ml-2';
        confirmation.textContent = 'Cảm ơn phản hồi!';
        feedbackDiv.appendChild(confirmation);

        console.log('✅ Feedback submitted successfully');

    } catch (error) {
        console.error('❌ Feedback submission error:', error);

        // Re-enable buttons on error
        allButtons.forEach(btn => btn.disabled = false);

        // Show error message
        showError('Không thể gửi phản hồi. Vui lòng thử lại.');
    }
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    const container = document.getElementById('chat-container');
    if (!container) return;

    const indicator = document.createElement('div');
    indicator.id = 'typing-indicator';
    indicator.className = 'flex justify-start mb-4';

    indicator.innerHTML = `
        <div class="message-bubble message-assistant">
            <div class="flex items-center space-x-1">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        </div>
    `;

    container.appendChild(indicator);
    scrollToBottom();

    window.StateManager.setTypingState(true);
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }

    window.StateManager.setTypingState(false);
}

/**
 * Scroll chat container to bottom
 */
function scrollToBottom(smooth = true) {
    const container = document.getElementById('chat-container');
    if (!container) return;

    setTimeout(() => {
        container.scrollTo({
            top: container.scrollHeight,
            behavior: smooth ? 'smooth' : 'auto'
        });
    }, 100);
}

/**
 * Show disclaimer modal
 */
function showDisclaimerModal() {
    const modal = document.getElementById('disclaimer-modal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

/**
 * Hide disclaimer modal
 */
function hideDisclaimerModal() {
    const modal = document.getElementById('disclaimer-modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

/**
 * Handle disclaimer accept
 */
async function handleDisclaimerAccept() {
    window.StateManager.acceptDisclaimer();
    hideDisclaimerModal();
    await initializeApp();
}

/**
 * Handle disclaimer decline
 */
function handleDisclaimerDecline() {
    alert('Bạn cần đồng ý với điều khoản để sử dụng dịch vụ.');
}

/**
 * Show safety modal with hotlines
 * @param {Array} hotlines - Array of hotline objects
 */
function showSafetyModal(hotlines = []) {
    const modal = document.getElementById('safety-modal');
    if (!modal) return;

    // Update hotlines list
    const hotlinesList = document.getElementById('hotlines-list');
    if (hotlinesList && hotlines.length > 0) {
        hotlinesList.innerHTML = hotlines.map(h => `
            <li class="hotline-item p-3 bg-red-50 rounded-lg">
                <div class="font-bold text-red-700">📞 ${h.name || 'Đường dây nóng'}</div>
                <div class="text-2xl font-bold text-red-600">${h.number}</div>
                ${h.available ? `<div class="text-sm text-gray-600">${h.available}</div>` : ''}
            </li>
        `).join('');
    }

    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

/**
 * Close safety modal
 */
function closeSafetyModal() {
    const modal = document.getElementById('safety-modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }

    // Re-enable chat so user can continue conversation
    window.StateManager.enableChat();
    console.log('✅ Crisis modal closed, chat re-enabled');
}

/**
 * Show error message using toast notification
 * @param {string} message - Error message
 */
function showError(message) {
    console.error('❌ Error:', message);

    // Use toast notification if available
    if (window.Toast) {
        window.Toast.error(message);
    } else {
        // Fallback to console + inline message
        const container = document.getElementById('chat-container');
        if (container) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = message;
            container.prepend(errorDiv);
        }
    }
}

/**
 * Show success message using toast notification
 * @param {string} message - Success message
 */
function showSuccess(message) {
    console.log('✅ Success:', message);

    // Use toast notification if available
    if (window.Toast) {
        window.Toast.success(message);
    } else {
        // Fallback to console
        const container = document.getElementById('chat-container');
        if (container) {
            const successDiv = document.createElement('div');
            successDiv.className = 'success-message';
            successDiv.textContent = message;
            successDiv.style.color = 'green';
            successDiv.style.padding = '10px';
            successDiv.style.marginBottom = '10px';
            container.prepend(successDiv);
            setTimeout(() => successDiv.remove(), 3000);
        }
    }
}

/**
 * Check connection health periodically
 */
function checkConnectionHealth() {
    // Initial check
    performHealthCheck();

    // Check every 30 seconds
    setInterval(performHealthCheck, 30000);
}

/**
 * Perform health check
 */
async function performHealthCheck() {
    try {
        const health = await window.API.checkHealth();
        const isHealthy = health.status === 'ok';
        window.StateManager.setConnectionStatus(isHealthy);
    } catch (error) {
        console.error('Health check failed:', error);
        window.StateManager.setConnectionStatus(false);
    }
}

/**
 * Handle auth button click
 */
function handleAuthButton() {
    if (window.AuthManager && window.AuthManager.isAuthenticated()) {
        // Show profile modal (instead of logout confirm)
        if (typeof showProfileModal === 'function') {
            showProfileModal();
        } else {
            // Fallback to old behavior if profile module not loaded
            if (confirm('Đăng xuất khỏi tài khoản?')) {
                window.AuthManager.logout();
            }
        }
    } else {
        showAuthModal();
    }
}

/**
 * Show auth modal
 */
function showAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');

        // Focus on email input
        const emailInput = document.getElementById('login-email');
        if (emailInput) {
            setTimeout(() => emailInput.focus(), 100);
        }
    }
}

/**
 * Hide auth modal
 */
function hideAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');

        // Reset forms
        const loginForm = document.getElementById('login-form-element');
        const registerForm = document.getElementById('register-form-element');
        if (loginForm) loginForm.reset();
        if (registerForm) registerForm.reset();
    }
}

/**
 * Switch between login and register tabs
 * @param {string} tab - 'login' or 'register'
 */
function switchAuthTab(tab) {
    const loginTab = document.getElementById('login-tab');
    const registerTab = document.getElementById('register-tab');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    if (tab === 'login') {
        loginTab.classList.add('border-b-2', 'border-primary', 'text-primary');
        loginTab.classList.remove('text-gray-500');
        registerTab.classList.remove('border-b-2', 'border-primary', 'text-primary');
        registerTab.classList.add('text-gray-500');

        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
    } else {
        registerTab.classList.add('border-b-2', 'border-primary', 'text-primary');
        registerTab.classList.remove('text-gray-500');
        loginTab.classList.remove('border-b-2', 'border-primary', 'text-primary');
        loginTab.classList.add('text-gray-500');

        registerForm.classList.remove('hidden');
        loginForm.classList.add('hidden');
    }
}

/**
 * Handle login form submission
 * @param {Event} e - Form event
 */
async function handleLogin(e) {
    e.preventDefault();
    console.log('Login form submitted');

    const emailInput = document.getElementById('login-email');
    const passwordInput = document.getElementById('login-password');

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    console.log('Login credentials:', { email, passwordLength: password?.length });

    if (!email || !password) {
        console.error('Validation failed: missing email or password');
        showError('Vui lòng nhập email và mật khẩu');
        return;
    }

    try {
        console.log('Calling AuthManager.login...');
        const result = await window.AuthManager.login(email, password);
        console.log('✅ Login successful!', result);

        hideAuthModal();

        // Update UI immediately with user data from response
        updateAuthUI();

        // Check if user is admin/super_admin and redirect
        if (result.user && (result.user.role === 'admin' || result.user.role === 'super_admin')) {
            console.log('🔐 Admin detected, redirecting to dashboard...');

            // Verify token is saved before redirect
            const savedToken = window.TabManager ? window.TabManager.getToken() : null;
            console.log('✅ [Admin Redirect] Token verified:', savedToken ? 'YES' : 'NO');

            if (!savedToken) {
                console.error('❌ Token not saved! Cannot redirect.');
                showError('Lỗi lưu token. Vui lòng thử lại.');
                return;
            }

            showSuccess(`Chào mừng Admin ${result.user.username}! Đang chuyển đến dashboard...`);

            // Redirect to admin dashboard
            setTimeout(() => {
                console.log('🚀 [Admin Redirect] Redirecting to admin.html...');
                window.location.href = '/admin.html';
            }, 1500);
            return; // Don't continue with chat setup
        }

        // For regular users, load chat history and conversation list
        const container = document.getElementById('chat-container');
        if (container) {
            container.innerHTML = '';
        }
        await loadChatHistory();
        await loadConversationsList();

        showSuccess('Đăng nhập thành công!');
    } catch (error) {
        console.error('❌ Login error:', error);
        console.error('Error stack:', error.stack);
        showError(error.message || 'Đăng nhập thất bại. Vui lòng kiểm tra lại thông tin.');
    }
}

/**
 * Handle register form submission
 * @param {Event} e - Form event
 */
async function handleRegister(e) {
    e.preventDefault();

    const usernameInput = document.getElementById('register-username');
    const emailInput = document.getElementById('register-email');
    const passwordInput = document.getElementById('register-password');

    const username = usernameInput.value.trim();
    const email = emailInput.value.trim();
    const password = passwordInput.value;

    if (!username || !email || !password) {
        showError('Vui lòng điền đầy đủ thông tin');
        return;
    }

    if (password.length < 8) {
        showError('Mật khẩu phải có ít nhất 8 ký tự');
        return;
    }

    try {
        const result = await window.AuthManager.register(email, username, password);
        hideAuthModal();
        updateAuthUI();

        // Check if user is admin/super_admin and redirect
        if (result.user && (result.user.role === 'admin' || result.user.role === 'super_admin')) {
            console.log('🔐 Admin detected, redirecting to dashboard...');
            showSuccess(`Chào mừng Admin ${result.user.username}! Đang chuyển đến dashboard...`);
            setTimeout(() => {
                window.location.href = '/admin.html';
            }, 1000);
            return;
        }

        showSuccess('Đăng ký thành công! Chào mừng bạn đến với TamLy Bot.');

        // Reload page to ensure auth state is properly initialized
        setTimeout(() => {
            console.log('🔄 Reloading page to refresh auth state...');
            window.location.reload();
        }, 1500);
    } catch (error) {
        console.error('Register error:', error);
        showError(error.message || 'Đăng ký thất bại. Email có thể đã được sử dụng.');
    }
}

/**
 * Handle mood button click
 */
async function handleMoodButtonClick() {
    if (!window.AuthManager || !window.AuthManager.isAuthenticated()) {
        showError('Vui lòng đăng nhập để sử dụng tính năng theo dõi tâm trạng');
        showAuthModal();
        return;
    }

    showMoodModal();
}

/**
 * Show mood modal
 */
async function showMoodModal() {
    const modal = document.getElementById('mood-modal');
    if (!modal) return;

    modal.classList.remove('hidden');
    modal.classList.add('flex');

    // Reset selection
    window.MoodTracker.clearSelectedMood();
    document.getElementById('submit-mood').disabled = true;
    document.getElementById('mood-note').value = '';

    // Clear all mood button highlights
    document.querySelectorAll('.mood-btn').forEach(btn => {
        btn.classList.remove('ring-4', 'ring-purple-500');
    });

    // Load mood history
    try {
        const history = await window.MoodTracker.getMoodHistory(7);
        const container = document.getElementById('mood-history-container');
        window.MoodTracker.renderChart(container, history);
    } catch (error) {
        console.error('Failed to load mood history:', error);
        document.getElementById('mood-history-container').innerHTML =
            '<p class="text-center text-gray-400 py-4">Không thể tải lịch sử</p>';
    }
}

/**
 * Hide mood modal
 */
function hideMoodModal() {
    const modal = document.getElementById('mood-modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

/**
 * Handle mood emoji selection
 * @param {Event} e - Click event
 */
function handleMoodSelect(e) {
    const btn = e.currentTarget;
    const moodValue = parseInt(btn.dataset.mood);
    const moodLabel = btn.dataset.label;

    // Update selection in MoodTracker
    window.MoodTracker.setSelectedMood(moodValue);

    // Visual feedback
    document.querySelectorAll('.mood-btn').forEach(b => {
        b.classList.remove('ring-4', 'ring-purple-500');
    });
    btn.classList.add('ring-4', 'ring-purple-500');

    // Enable submit button
    document.getElementById('submit-mood').disabled = false;
}

/**
 * Handle mood submit
 */
async function handleMoodSubmit() {
    const selectedMood = window.MoodTracker.getSelectedMood();
    if (!selectedMood) {
        showError('Vui lòng chọn tâm trạng');
        return;
    }

    const moodLabels = ['', 'angry', 'sad', 'neutral', 'happy', 'excited'];
    const note = document.getElementById('mood-note').value.trim();

    try {
        await window.MoodTracker.logMood(selectedMood, moodLabels[selectedMood], note);
        hideMoodModal();
        showSuccess('Đã lưu tâm trạng của bạn!');
    } catch (error) {
        console.error('Mood submit error:', error);
        showError(error.message || 'Không thể lưu tâm trạng. Vui lòng thử lại.');
    }
}

/**
 * Handle feedback button click
 * @param {Event} e - Click event
 */
async function handleFeedback(e) {
    const btn = e.currentTarget;
    const messageId = btn.dataset.messageId;
    const rating = parseInt(btn.dataset.rating);

    if (!messageId) {
        console.error('No message ID for feedback');
        return;
    }

    try {
        await window.API.submitFeedback(messageId, rating);

        // Visual feedback
        btn.classList.remove('text-gray-400');
        btn.classList.add(rating === 1 ? 'text-green-500' : 'text-red-500');
        btn.disabled = true;

        // Disable sibling button
        btn.parentElement.querySelectorAll('.feedback-btn').forEach(b => {
            b.disabled = true;
            b.classList.add('opacity-50', 'cursor-not-allowed');
        });

    } catch (error) {
        console.error('Feedback error:', error);
        showError('Không thể gửi phản hồi');
    }
}

/**
 * Update auth UI (button text and user info)
 * Show/hide admin link based on user role from JWT token
 */
function updateAuthUI() {
    const authButtonText = document.getElementById('auth-button-text');
    const adminLink = document.getElementById('admin-link');

    if (!authButtonText) return;

    if (window.AuthManager && window.AuthManager.isAuthenticated()) {
        const user = window.AuthManager.getUser();
        if (user && user.username) {
            authButtonText.textContent = user.username;
        } else {
            authButtonText.textContent = 'User';
        }

        // Check if user is admin/super_admin from JWT token
        try {
            const token = window.TabManager ? window.TabManager.getToken() : null;
            if (token && adminLink) {
                // Decode JWT payload
                const base64Url = token.split('.')[1];
                const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
                const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => {
                    return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
                }).join(''));

                const payload = JSON.parse(jsonPayload);

                // Show admin link if role is admin or super_admin
                if (payload.role === 'admin' || payload.role === 'super_admin') {
                    adminLink.classList.remove('hidden');
                    console.log('✅ Admin link visible - role:', payload.role);
                } else {
                    adminLink.classList.add('hidden');
                }
            }
        } catch (error) {
            console.error('Error decoding JWT for admin check:', error);
            if (adminLink) adminLink.classList.add('hidden');
        }
    } else {
        authButtonText.textContent = 'Đăng nhập';
        // Hide admin link when not authenticated
        if (adminLink) adminLink.classList.add('hidden');
    }
}


/**
 * Handle exercises button click
 */
async function handleExercisesButtonClick() {
    showExercisesModal();
    await loadExercises();
}

/**
 * Show exercises modal
 */
function showExercisesModal() {
    const modal = document.getElementById('exercises-modal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

/**
 * Hide exercises modal
 */
function hideExercisesModal() {
    const modal = document.getElementById('exercises-modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

// Note: loadExercises, renderExercises, showExerciseDetail, closeExerciseDetail
// are defined in exercises.js which should be loaded before app.js
// The exercises modal uses those functions from exercises.js

/**
 * Debug: Expose useful functions to window for console testing
 */
window.ChatApp = {
    sendMessage: handleSendMessage,
    newChat: handleNewChat,
    showSafetyModal,
    closeSafetyModal,
    loadHistory: loadChatHistory,
    loadConversations: loadConversationsList,
    selectConversation: selectConversation,
    deleteConversation: deleteConversation,
    debugState: window.StateManager.debugState,
    // Auth functions
    showAuthModal,
    hideAuthModal,
    updateAuthUI
};

// Also expose conversation functions globally for onclick handlers
window.selectConversation = selectConversation;
window.deleteConversation = deleteConversation;

console.log('✅ Chat Application initialized');
console.log('💡 Debug: Use ChatApp.debugState() to inspect state');
