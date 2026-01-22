// ============================================
// Clear History Functionality (Sprint 3)
// ============================================

// Get elements
const clearHistoryButton = document.getElementById('clear-history-button');
const clearHistoryModal = document.getElementById('clear-history-modal');
const cancelClearHistory = document.getElementById('cancel-clear-history');
const confirmClearHistory = document.getElementById('confirm-clear-history');

// Show confirmation modal when clear button clicked
if (clearHistoryButton) {
    clearHistoryButton.addEventListener('click', function () {
        if (clearHistoryModal) {
            clearHistoryModal.classList.remove('hidden');
            clearHistoryModal.classList.add('flex');
        }
    });
}

// Cancel clear history
if (cancelClearHistory) {
    cancelClearHistory.addEventListener('click', function () {
        if (clearHistoryModal) {
            clearHistoryModal.classList.add('hidden');
            clearHistoryModal.classList.remove('flex');
        }
    });
}

// Confirm clear history
if (confirmClearHistory) {
    confirmClearHistory.addEventListener('click', async function () {
        // Hide modal
        if (clearHistoryModal) {
            clearHistoryModal.classList.add('hidden');
            clearHistoryModal.classList.remove('flex');
        }

        // Call clear history function
        await clearHistory();
    });
}

/**
 * Clear chat history (archive current conversation)
 * Sprint 3 Feature
 */
async function clearHistory() {
    const conversationId = window.StateManager.getConversationId();

    if (!conversationId) {
        if (window.Toast) {
            window.Toast.warning('Không có lịch sử để xóa');
        }
        return;
    }

    try {
        // Show loading toast
        if (window.Toast) {
            window.Toast.info('Đang xóa lịch sử...');
        }

        // Call DELETE API
        const response = await fetch(`/api/v1/conversations/${conversationId}`, {
            method: 'DELETE',
            headers: {
                'X-Session-ID': window.StateManager.getSessionId(),
                'Authorization': window.AuthManager.getAuthHeader() || ''
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to clear history');
        }

        // Clear UI
        const chatContainer = document.getElementById('chat-container');
        if (chatContainer) {
            chatContainer.innerHTML = '';
        }

        // Clear session state
        window.StateManager.clearSession();

        // Hide clear history button
        if (clearHistoryButton) {
            clearHistoryButton.classList.add('hidden');
        }

        // Initialize new session
        await createNewSession();

        // Success message
        if (window.Toast) {
            window.Toast.success('Đã xóa lịch sử thành công');
        }

        console.log('✅ History cleared successfully');

    } catch (error) {
        console.error('❌ Error clearing history:', error);
        if (window.Toast) {
            window.Toast.error(`Lỗi khi xóa lịch sử: ${error.message}`);
        }
    }
}

/**
 * Show/hide clear history button based on conversation state
 * Call this after sending first message
 */
function updateClearHistoryButtonVisibility() {
    if (!clearHistoryButton) return;

    const conversationId = window.StateManager.getConversationId();
    const chatContainer = document.getElementById('chat-container');

    // Show button if we have a conversation with messages
    if (conversationId && chatContainer && chatContainer.children.length > 1) {
        clearHistoryButton.classList.remove('hidden');
    } else {
        clearHistoryButton.classList.add('hidden');
    }
}

// Add this file to the list of scripts loaded in index.html
// Or append to existing app.js after the existing event listeners

console.log('✅ Clear History functionality loaded');
