# 📋 Feature List & Requirements

Danh sách tính năng chi tiết (Functional Requirements) cho Chatbot Tư vấn Tâm lý.

## 1. Core Chat Features (Trò chuyện cốt lõi)

### 1.1 Hội thoại AI (AI Conversation)

- **Context-Aware Chat**: Bot nhớ ngữ cảnh trong phiên làm việc hiện tại (Memory).
- **RAG Integration**: Bot trả lời dựa trên *Kiến thức chuyên gia* (Sách, tài liệu tâm lý đã vector hóa).
- **Fallback**: Khi không tìm thấy thông tin trong knowledge base, bot trả lời chung chung nhưng an toàn (General empathetic response).
- **Stream Response**: ✅ **[IMPLEMENTED]** Hiển thị chữ chạy qua SSE (Server-Sent Events) để tăng trải nghiệm.

### 1.2 Nhận diện Khủng hoảng (Crisis Detection)

- **Keyword Spotting**: Phát hiện từ khóa nguy hiểm (tự tử, giết người, làm hại bản thân).
- **Crisis Response Protocol**:
  - Dừng ngay mạch chat bình thường.
  - Đưa ra thông điệp trấn an, đồng cảm.
  - **Cung cấp Hotline**: Hiển thị số điện thoại khẩn cấp (111, 113, 115, các tổ chức hỗ trợ tâm lý).
  - Gắn cờ (flag) đoạn hội thoại để Admin xem xét (Audit).

---

## 2. Mental Health Tools (Công cụ hỗ trợ)

### 2.1 Mood Tracker (Nhật ký cảm xúc)

- Người dùng ghi lại cảm xúc hiện tại (Thang 1-5: Tệ -> Rất tốt).
- Note ngắn (Tùy chọn): "Hôm nay bị điểm kém".
- **Biểu đồ (Chart)**: Xem lại lịch sử cảm xúc 7 ngày qua (Simple Line Chart).

### 2.2 Thư viện bài tập (Exercises Library)

- Bot đề xuất bài tập dựa trên cảm xúc (VD: Đang lo âu -> Bài tập hít thở 4-7-8).
- Hiển thị hướng dẫn từng bước (Text/Image).
- Các bài tập:
  - Hít thở sâu (Breathing).
  - Thiền chánh niệm (Mindfulness).
  - Viết nhật ký biết ơn (Gratitude Journaling).
  - Kỹ thuật tiếp đất (Grounding).

---

## 3. User & Privacy (Người dùng & Quyền riêng tư)

### 3.1 Quản lý tài khoản (User Management)

- **Guest Mode**: Sử dụng ngay không cần đăng ký (Dữ liệu lưu local/session, mất khi đóng tab).
- **Register/Login**: Email/Password.
- **Profile**: Đổi tên hiển thị, Avatar (Preset).

### 3.2 Phân quyền (RBAC - Role-Based Access Control)

> [!NOTE]
> **Chi tiết đầy đủ**: Xem [AUTHORIZATION_GUIDE.md](./AUTHORIZATION_GUIDE.md) - Hướng dẫn toàn diện về phân quyền, luồng xác thực, và ma trận permissions.

**Tổng quan 4 cấp độ:**

- **👥 Guest**: Chat cơ bản + Session tạm thời
  - Không cần đăng ký/đăng nhập
  - Dữ liệu lưu trong Redis (TTL 24h)
  - Hạn chế: Không có Mood Tracking, không export data
  
- **👤 User (Member)**: Lưu lịch sử chat + Mood History vĩnh viễn
  - Đăng ký bằng email/password
  - JWT authentication
  - Database: PostgreSQL (persistent storage)
  - Quyền: Chat, Mood Tracking, Export Data, Manage Conversations
  
- **👨‍💼 Admin**: Quản trị hệ thống + Xem Dashboard
  - Promoted từ User
  - Access Admin Dashboard
  - Quyền: Statistics, User Management (Ban/Unban), Knowledge Base Upload, System Config
  
- **👑 Super Admin**: Quản lý toàn bộ (Highest privileges)
  - Tạo thủ công hoặc qua script
  - Full system control
  - Quyền: Tất cả quyền Admin + (Future) Role Management, Audit Logs Viewer

### 3.3 Quyền riêng tư (Privacy Control)

- **Anonymous Mode**: ✅ Chat không cần login (lưu sessionStorage)
- **Clear Data**: ✅ **[Sprint 3 IMPLEMENTED]** Nút "Xóa lịch sử" giúp người dùng an tâm
  - **UI**: Button in chat header + confirmation modal
  - **Behavior**: Soft delete (archives conversation to preserve audit trail)
  - **Effect**: Clears UI, resets session, creates new conversation
  - **Frontend**: `static/js/clear_history.js`
  - **Backend**: `DELETE /api/v1/conversations/{id}` (soft delete)
- **Export Data**: ✅ **[Sprint 4 IMPLEMENTED]** Download complete chat history as JSON
  - **UI**: "Xuất dữ liệu" button in sidebar
  - **Format**: JSON file with all conversations and messages
  - **Privacy**: Authenticated users only (guests must register)
  - **Frontend**: `static/js/api.js` (exportData method)
  - **Backend**: `GET /api/v1/conversations/export`

---

## 4. Admin Dashboard (Quản trị)

### 4.1 Analytics (Thống kê)

- Tổng số cuộc hội thoại.
- Top chủ đề/từ khóa được hỏi nhiều (Word Cloud).
- Tỉ lệ phát hiện Crisis.
- Cảm xúc trung bình của người dùng theo thời gian.

### 4.2 Knowledge Base Management (Quản lý tri thức)

- Upload tài liệu mới (PDF/Docx). -> *Admin trigger script import (Phase 1)*.
- Xem danh sách tài liệu đang có trong vector DB.

### 4.3 System Config

- Cập nhật số Hotline.
- Cập nhật danh sách từ khóa Crisis.

---

## 5. Non-Functional Requirements (Phi chức năng)

- **Performance**: Phản hồi < 2s (với RAG).
  - ✅ **Optimized 2025-12-22**: BM25 caching, embedding reuse, connection pooling.
- **Security**:
  - HTTPS (TLS 1.2/1.3).
  - Sanitize input (chống XSS/Injection).
  - Rate Limiting (chống DDoS cơ bản).
- **Reliability**: Auto-restart khi crash (Docker Restart Policy).
- **Accessibility**: Màu sắc dịu nhẹ, font chữ dễ đọc (Psychology-friendly UI).

---

## RBAC Matrix (Ma trận phân quyền)

> [!TIP]
> **Xem chi tiết đầy đủ**: [AUTHORIZATION_GUIDE.md](./AUTHORIZATION_GUIDE.md#ma-trận-phân-quyền-đầy-đủ)

### Core Features

| Feature | Guest | User | Admin | Super Admin |
| :--- | :---: | :---: | :---: | :---: |
| Chat with AI | ✅ | ✅ | ✅ | ✅ |
| Crisis Support | ✅ | ✅ | ✅ | ✅ |
| View chat trong session | ✅ | ✅ | ✅ | ✅ |
| Save chat history (persistent) | ❌ | ✅ | ✅ | ✅ |
| Mood Tracker | ❌ | ✅ | ✅ | ✅ |
| Mood History/Chart | ❌ | ✅ | ✅ | ✅ |
| Export Chat History | ❌ | ✅ | ✅ | ✅ |
| Archive Conversation | ❌ | ✅ | ✅ | ✅ |

### Admin Features

| Feature | Guest | User | Admin | Super Admin |
| :--- | :---: | :---: | :---: | :---: |
| View Dashboard | ❌ | ❌ | ✅ | ✅ |
| View Statistics | ❌ | ❌ | ✅ | ✅ |
| Manage Users (Ban/Unban) | ❌ | ❌ | ✅ | ✅ |
| Manage Knowledge Base | ❌ | ❌ | ✅ | ✅ |
| Update System Config | ❌ | ❌ | ✅ | ✅ |
| Reset Knowledge Base | ❌ | ❌ | ✅ | ✅ |
| Manage Admin Roles (Promote/Demote) | ❌ | ❌ | ❌ | ✅ |
| View Audit Logs | ❌ | ❌ | ❌ | 🔜 (Planned) |

---

## 6. Sprint 3 Completion Status

**Implemented Features:**

### Security & Privacy (Production Readiness)

✅ **HTTPS/SSL Configuration**

- Nginx TLS 1.2/1.3 setup
- HTTP → HTTPS redirect
- HSTS header (1 year)
- Let's Encrypt automation (`scripts/ssl_setup.sh`)

✅ **Clear History UI**

- Privacy control button
- Confirmation modal
- Soft delete (preserves audit)
- Session reset

✅ **Admin User Management**

- List users (pagination + filters)
- Ban users (deactivate + session invalidation)
- Unban users (reactivate)
- Audit logging
- Protection against admin bans

**Deployment Status:** Ready for Production ✅
**Last Updated:** 2025-12-23 (Sprint 4)

---

## 7. Sprint 4 Completion Status

System Finalization - All Core Features Complete

### Database Migration

✅ **Audit Logs Metadata Column**

- Added `metadata` JSONB column to `audit_logs` table
- Supports structured context data for admin actions
- Migration script: `src/scripts/migrate_audit_metadata.py`

### Admin User Management UI

✅ **Admin Dashboard - User Management Tab**

- Full CRUD interface for user management
- Search and filter capabilities
- Ban/Unban with confirmation dialogs
- Real-time status updates
- Pagination support
- Frontend: `static/admin.html`
- Backend: `/api/v1/admin/users/`

### Data Export (Privacy Enhancement)

✅ **Chat History Export**

- Download complete conversation history
- JSON format with structured data
- Includes all messages with timestamps and metadata
- Works for authenticated users and guests
- Privacy compliance (GDPR-ready)
- Filename: `chat_history_{user_id}.json`

### System Status

**100% Feature Complete** ✅  
**Production Ready** - Full Stack Verified ✅  
**Last Updated:** 2025-12-25
