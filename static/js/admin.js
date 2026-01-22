/**
 * Admin Dashboard JavaScript
 * Handles stats loading, user management, and system configuration editing.
 */

const API_BASE_URL = window.location.origin + '/api/v1';
let currentConfig = {}; // Store current config for editing

// ============================================
// Authentication Check
// ============================================
function checkAuth() {
    console.log('🔍 [Admin Auth] ========== STARTING AUTH CHECK ==========');
    console.log('🔍 [Admin Auth] Current URL:', window.location.href);
    console.log('🔍 [Admin Auth] window.TabManager exists:', !!window.TabManager);

    // Critical check: Ensure TabManager exists
    if (!window.TabManager) {
        console.error('❌ [Admin Auth] FATAL: window.TabManager is undefined!');
        console.error('❌ [Admin Auth] This means tab_manager.js did not load properly');
        alert('Lỗi hệ thống: TabManager không khả dụng. Vui lòng refresh trang (Ctrl+F5)');
        setTimeout(() => {
            window.location.href = '/index.html';
        }, 2000);
        return false;
    }

    // Log TabManager state
    const debugInfo = window.TabManager.getDebugInfo();
    console.log('🔍 [Admin Auth] TabManager Debug Info:', debugInfo);
    console.log('🔍 [Admin Auth] Tab ID:', debugInfo.currentTabId);
    console.log('🔍 [Admin Auth] Is Authenticated:', debugInfo.isAuthenticated);
    console.log('🔍 [Admin Auth] Total Tabs with Tokens:', debugInfo.totalTabs);

    // Try to get token
    const token = window.TabManager.getToken();
    console.log('🔍 [Admin Auth] Token from TabManager:', token ? `EXISTS (${token.length} chars)` : 'NOT FOUND');

    // If no token, dump full state for debugging
    if (!token) {
        console.error('❌ [Admin Auth] No access token found');
        console.error('❌ [Admin Auth] localStorage.tab_tokens:', localStorage.getItem('tab_tokens'));
        console.error('❌ [Admin Auth] sessionStorage.tab_id:', sessionStorage.getItem('tab_id'));

        // Check if there are ANY tokens in localStorage
        try {
            const allTokens = JSON.parse(localStorage.getItem('tab_tokens') || '{}');
            console.error('❌ [Admin Auth] All tokens in storage:', Object.keys(allTokens));
            console.error('❌ [Admin Auth] Detail:', allTokens);
        } catch (e) {
            console.error('❌ [Admin Auth] Error parsing tab_tokens:', e);
        }

        alert('Vui lòng đăng nhập để truy cập trang này');
        setTimeout(() => {
            window.location.href = '/index.html';
        }, 1000);
        return false;
    }

    try {
        console.log('🔍 [Admin Auth] Decoding JWT token...');
        // Decode JWT token to extract role
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(c => {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));

        const payload = JSON.parse(jsonPayload);

        console.log('🔍 [Admin Auth] JWT payload:', payload);

        // Check role
        if (!payload.role || (payload.role !== 'admin' && payload.role !== 'super_admin')) {
            console.error('❌ [Admin Auth] User role not admin:', payload.role);
            alert('Yêu cầu quyền Admin để truy cập trang này');
            setTimeout(() => {
                window.location.href = '/index.html';
            }, 1000);
            return false;
        }

        // Display admin info
        const displayName = payload.email || payload.username || 'Admin';
        const adminUsernameEl = document.getElementById('admin-username');
        if (adminUsernameEl) {
            adminUsernameEl.textContent = `Xin chào, ${displayName}`;
        }

        console.log('✅ [Admin Auth] Auth successful! Role:', payload.role);
        console.log('🔍 [Admin Auth] ========== AUTH CHECK COMPLETE ==========');

        return true;
    } catch (error) {
        console.error('❌ [Admin Auth] Token decode error:', error);
        console.error('❌ [Admin Auth] Stack trace:', error.stack);
        alert('Token không hợp lệ');
        setTimeout(() => {
            window.location.href = '/index.html';
        }, 1000);
        return false;
    }
}

// ============================================
// Load Statistics
// ============================================
async function loadStats() {
    try {
        const token = window.TabManager ? window.TabManager.getToken() : null;
        const response = await fetch(`${API_BASE_URL}/admin/stats/overview`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) throw new Error('Failed to load stats');

        const data = await response.json();

        // Update stat cards
        document.getElementById('total-users').textContent = data.users.total || 0;
        document.getElementById('total-conversations').textContent = data.conversations.total || 0;
        document.getElementById('total-messages').textContent = data.messages.total || 0;
        document.getElementById('total-moods').textContent = data.moods.total || 0;
    } catch (error) {
        console.error('Error loading stats:', error);
        // Stats error - silently fail or show console error
    }
}

// ============================================
// Load Recent Users
// ============================================
async function loadRecentUsers() {
    try {
        const token = window.TabManager ? window.TabManager.getToken() : null;
        // Use the correct endpoint: /admin/users with pagination
        const response = await fetch(`${API_BASE_URL}/admin/users?page=1&page_size=20`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) throw new Error('Failed to load users');

        const data = await response.json();
        const tableBody = document.getElementById('users-table-body');

        if (data.users.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center py-8 text-gray-400">
                        Chưa có người dùng nào
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = data.users.map(user => {
            // Backend returns UTC timestamps without 'Z' suffix
            let timestamp = user.created_at;
            if (timestamp && !timestamp.endsWith('Z') && !timestamp.includes('+') && !timestamp.includes('-', 10)) {
                timestamp = timestamp + 'Z';
            }
            const createdDate = timestamp ? new Date(timestamp).toLocaleDateString('vi-VN') : 'N/A';

            return `
            <tr class="border-b hover:bg-gray-50 transition">
                <td class="py-3 px-4 text-sm">${user.email || '<em>N/A</em>'}</td>
                <td class="py-3 px-4 text-sm">${user.username}</td>
                <td class="py-3 px-4 text-sm">
                    <span class="px-2 py-1 rounded-full text-xs font-semibold ${user.role === 'admin' || user.role === 'super_admin'
                    ? 'bg-red-100 text-red-700'
                    : 'bg-blue-100 text-blue-700'
                }">
                        ${user.role}
                    </span>
                </td>
                <td class="py-3 px-4 text-sm">
                    <span class="px-2 py-1 rounded-full text-xs font-semibold ${user.is_active
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-100 text-gray-700'
                }">
                        ${user.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td class="py-3 px-4 text-sm text-gray-600">
                    ${createdDate}
                </td>
            </tr>
        `}).join('');

    } catch (error) {
        console.error('Error loading users:', error);
        // User list error - silently fail
    }
}

// ============================================
// Load System Configs
// ============================================
async function loadConfigs() {
    try {
        const token = window.TabManager ? window.TabManager.getToken() : null;
        const response = await fetch(`${API_BASE_URL}/admin/config/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) throw new Error('Failed to load configs');

        const configs = await response.json();
        const configList = document.getElementById('config-list');

        if (configs.length === 0) {
            configList.innerHTML = `
                <div class="text-center py-8 text-gray-400">
                    Chưa có cấu hình nào
                </div>
            `;
            return;
        }

        configList.innerHTML = configs.map(config => `
            <div class="border border-gray-200 rounded-lg p-4 hover:border-primary transition">
                <div class="flex justify-between items-start mb-2">
                    <div class="flex-1">
                        <h4 class="font-semibold text-gray-800">${config.key}</h4>
                        <p class="text-sm text-gray-600 mt-1">${config.description}</p>
                    </div>
                    <button onclick="openConfigEdit('${config.key}')" 
                        class="ml-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-secondary transition text-sm">
                        <i class="fas fa-edit mr-1"></i>Chỉnh sửa
                    </button>
                </div>
                <div class="bg-gray-50 p-3 rounded mt-3 font-mono text-xs text-gray-700 max-h-32 overflow-y-auto custom-scrollbar">
                    ${config.value.length > 200 ? config.value.substring(0, 200) + '...' : config.value}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading configs:', error);
        showToast('error', 'Không thể tải cấu hình');
    }
}

// ============================================
// Config Edit Modal
// ============================================
async function openConfigEdit(key) {
    try {
        const token = window.TabManager ? window.TabManager.getToken() : null;
        const response = await fetch(`${API_BASE_URL}/admin/config/${key}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) throw new Error('Failed to load config');

        const config = await response.json();
        currentConfig = config;

        // Populate modal
        document.getElementById('config-modal-key').textContent = `Key: ${config.key}`;
        document.getElementById('config-modal-description').textContent = config.description;
        document.getElementById('config-modal-value').value = config.value;

        // Show modal
        document.getElementById('config-modal').classList.remove('hidden');
        document.getElementById('config-modal').classList.add('flex');
    } catch (error) {
        console.error('Error opening config edit:', error);
        showToast('error', 'Không thể mở cấu hình');
    }
}

async function saveConfig() {
    try {
        const token = window.TabManager ? window.TabManager.getToken() : null;
        const newValue = document.getElementById('config-modal-value').value;

        const response = await fetch(`${API_BASE_URL}/admin/config/${currentConfig.key}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ value: newValue })
        });

        if (!response.ok) throw new Error('Failed to update config');

        showToast('success', 'Cập nhật cấu hình thành công');
        closeConfigModal();
        loadConfigs(); // Reload configs
    } catch (error) {
        console.error('Error saving config:', error);
        showToast('error', 'Không thể lưu cấu hình');
    }
}

function closeConfigModal() {
    document.getElementById('config-modal').classList.add('hidden');
    document.getElementById('config-modal').classList.remove('flex');
}

// ============================================
// Tab Switching
// ============================================
function switchTab(tabName) {
    // Hide all content
    document.querySelectorAll('.tab-content').forEach(section => {
        section.classList.add('hidden');
    });

    // Remove active state from all buttons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('border-primary', 'text-primary');
        button.classList.add('text-gray-500');
    });

    // Show selected content
    document.getElementById(`${tabName}-section`).classList.remove('hidden');

    // Set active button
    const activeButton = document.getElementById(`tab-${tabName}`);
    activeButton.classList.add('border-primary', 'text-primary');
    activeButton.classList.remove('text-gray-500');

    // Load data for selected tab
    if (tabName === 'users') {
        loadRecentUsers();
    } else if (tabName === 'config') {
        loadConfigs();
    }
}

// ============================================
// Initialization Note
// ============================================
// Dashboard initialization is handled by inline script in admin.html
// This file provides helper functions: checkAuth, loadStats, loadRecentUsers, etc.
// Do NOT add DOMContentLoaded here - it will conflict with admin.html inline initialization
