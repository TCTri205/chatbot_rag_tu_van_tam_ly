/**
 * Profile Module
 * Handles user profile viewing and editing
 */

/**
 * Show Profile Modal
 */
function showProfileModal() {
    const modal = document.getElementById('profile-modal');
    if (!modal) return;

    // Get current user data
    const user = window.AuthManager.getUser();
    if (!user) {
        console.error('No user data available');
        return;
    }

    // Populate form fields
    document.getElementById('profile-email').value = user.email || '';
    document.getElementById('profile-username').value = user.username || '';
    document.getElementById('profile-role').value = formatRole(user.role);

    // Show modal
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

/**
 * Hide Profile Modal
 */
function hideProfileModal() {
    const modal = document.getElementById('profile-modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

/**
 * Format role for display
 */
function formatRole(role) {
    const roleLabels = {
        'user': 'Người dùng',
        'admin': 'Quản trị viên',
        'super_admin': 'Siêu quản trị'
    };
    return roleLabels[role] || role;
}

/**
 * Handle Profile Form Submit
 */
async function handleProfileSubmit(event) {
    event.preventDefault();

    const username = document.getElementById('profile-username').value.trim();
    const saveBtn = document.getElementById('profile-save-btn');

    if (!username || username.length < 2) {
        if (window.Toast) {
            window.Toast.error('Tên hiển thị phải có ít nhất 2 ký tự');
        }
        return;
    }

    // Disable button
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Đang lưu...';

    try {
        const response = await fetch('/api/v1/auth/me/', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': window.AuthManager.getAuthHeader()
            },
            body: JSON.stringify({ username: username })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Update failed');
        }

        const updatedUser = await response.json();

        // Update local storage via TabManager
        const currentUser = window.AuthManager.getUser();
        currentUser.username = updatedUser.username;

        if (window.TabManager && window.AuthManager.token) {
            window.TabManager.saveToken(window.AuthManager.token, currentUser);
        }
        window.AuthManager.user = currentUser;

        // Update UI
        updateAuthUI();

        // Show success message
        if (window.Toast) {
            window.Toast.success('Đã cập nhật thông tin thành công!');
        }

        // Close modal after short delay
        setTimeout(() => {
            hideProfileModal();
        }, 1000);

    } catch (error) {
        console.error('Profile update error:', error);
        if (window.Toast) {
            window.Toast.error('Lỗi: ' + error.message);
        }
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-save mr-2"></i>Lưu thay đổi';
    }
}

/**
 * Initialize Profile Event Listeners
 */
document.addEventListener('DOMContentLoaded', () => {
    // Close profile modal button
    const closeProfileBtn = document.getElementById('close-profile-modal');
    if (closeProfileBtn) {
        closeProfileBtn.addEventListener('click', hideProfileModal);
    }

    // Profile form submit
    const profileForm = document.getElementById('profile-form');
    if (profileForm) {
        profileForm.addEventListener('submit', handleProfileSubmit);
    }

    // Logout button in profile modal
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            if (confirm('Đăng xuất khỏi tài khoản?')) {
                hideProfileModal();
                window.AuthManager.logout();
            }
        });
    }

    // Close on backdrop click
    const profileModal = document.getElementById('profile-modal');
    if (profileModal) {
        profileModal.addEventListener('click', (e) => {
            if (e.target === profileModal) {
                hideProfileModal();
            }
        });
    }
});

console.log('✅ Profile module loaded');
