# 🔌 API Design Specification

Tài liệu quy định chuẩn giao tiếp giữa Backend (FastAPI) và Frontend (Web Client).
Base URL: `/api/v1`

> **⚠️ Technical Note (Trailing Slashes)**:
> Với `redirect_slashes=False` (xem `src/main.py`), client **PHẢI** gọi đúng path như route định nghĩa.
>
> - **Không trailing slash**: `/chat`, `/sessions/init`, `/auth/login`, `/auth/register`
> - **Có trailing slash**: `/moods/`, `/moods/history/`, `/conversations/`, `/exercises/`

**Authentication Strategy**:

- `JWT (JSON Web Token)` cho xác thực User/Admin/Super Admin.
- Header: `Authorization: Bearer <token>`
- **Role-Based Access Control (RBAC)**: 4 cấp độ phân quyền (Guest, User, Admin, Super Admin)
- Chi tiết đầy đủ: Xem [AUTHORIZATION_GUIDE.md](./AUTHORIZATION_GUIDE.md)

**Session Management (Multi-tab)**:

- **Session Storage**: `session_id` lưu trong `sessionStorage` (mỗi tab riêng biệt).
- **JWT Storage**: Token lưu trong `localStorage` indexed by `tab_id` (TabManager).
  - Hỗ trợ multi-account multi-tab (mỗi tab có token riêng).
- Header: `X-Session-ID: <uuid>` bắt buộc cho mọi Chat endpoint.
- **Quy tắc Session**:
  - Guest: Session TTL = 24 giờ (Redis EXPIRE 86400).
  - Authenticated: Session không có TTL (đến khi logout).
  - `JWT` xác định *User là ai* (Who), `session_id` xác định *Ngữ cảnh chat nào* (Which context).

**Caching Strategy**:

- `Cache-Control: no-store` cho các endpoint chat, mood (dữ liệu động).
- `Cache-Control: public, max-age=3600` cho Static Resources (Images, Exercises).
- response kèm `ETag` để browser caching hiệu quả.

---

## Authorization Overview

### User Roles

| Role | Description | Authentication | Data Storage |
|------|-------------|----------------|-------------|
| **Guest** | Khách vãng lai | Session ID only | Redis (24h) |
| **User** | Thành viên đã đăng ký | JWT Token | PostgreSQL |
| **Admin** | Quản trị viên | JWT Token (role: admin) | PostgreSQL |
| **Super Admin** | Quản trị cấp cao | JWT Token (role: super_admin) | PostgreSQL |

### Authentication Headers

**For Guests:**

```http
X-Session-ID: <uuid>
```

**For Authenticated Users (User/Admin/Super Admin):**

```http
Authorization: Bearer <jwt_token>
X-Session-ID: <uuid>
```

**JWT Payload Structure:**

```json
{
  "sub": "user_id_uuid",
  "role": "user | admin | super_admin",
  "exp": 1234567890
}
```

**Xem chi tiết:** [AUTHORIZATION_GUIDE.md](./AUTHORIZATION_GUIDE.md) - Hướng dẫn đầy đủ về phân quyền, luồng xác thực, và ma trận permissions.

---

## 1. Authentication & Session

### 1.1 Login / Register (for Members)

- **Endpoint**: `POST /auth/login/` (with trailing slash)
- **Request Validation (Pydantic)**:
  - `email`: Valid Email format.
  - `password`: Min 8 chars.
- **Body**: `{ "email": "...", "password": "..." }`
- **Response**:

  ```json
  {
    "access_token": "eyJhbG...",
    "token_type": "bearer",
    "user": { "id": "uuid", "role": "user", "name": "Nam" }
  }
  ```

### 1.2 Session Init (Guest/Anonymous)

- **Endpoint**: `POST /sessions/init` (Full URL: `/api/v1/sessions/init`) - NO trailing slash
- **Description**: Tạo session mới (Guest hoặc Authenticated). Conversation được tạo **LAZY** (khi gửi tin nhắn đầu tiên).
- **Response**:

  ```json
  {
    "session_id": "uuid-v4",
    "conversation_id": null,
    "greeting": "Chào bạn! Tôi là trợ lý tâm lý AI...",
    "created_at": "timestamp"
  }
  ```

> **Note**: `conversation_id` là `null` ban đầu và sẽ được tạo tự động khi gửi tin nhắn đầu tiên. Điều này tránh spam conversation rỗng.

### 1.3 Session Info

- **Endpoint**: `GET /sessions/info`
- **Header**: `X-Session-ID: <uuid>`
- **Response**:

  ```json
  {
    "session_id": "uuid-v4",
    "user_id": "uuid" | null,
    "conversation_id": "uuid" | null,
    "is_active": true,
    "created_at": "timestamp",
    "expires_at": "timestamp"
  }
  ```

### 1.4 End Session

- **Endpoint**: `DELETE /sessions/`
- **Header**: `X-Session-ID: <uuid>`
- **Response**: `{ "message": "Session ended successfully" }`

---

## 2. Chat API (Conversational)

### 2.1 Send Message (Chat)

- **Endpoint**: `POST /chat` (NO trailing slash)
- **Header**: `X-Session-ID: <uuid>`
- **Body**:

  ```json
  {
    "content": "Tôi cảm thấy buồn quá"
  }
  ```

> **Note**: `conversation_id` được xác định bởi session, không gửi trong body.

- **Logic**:
  1. Kiểm tra `is_crisis` (từ khóa "tự tử", "chết",...).
  2. Nếu Crisis -> Trả về thông điệp ứng cứu khẩn cấp + Hotline.
  3. Nếu Normal -> Gọi RAG Pipeline -> Trả lời + trích dẫn source.
  4. Lưu xuống DB.

- **Response (Normal)**:

  ```json
  {
    "message_id": "uuid",
    "role": "assistant",
    "content": "Chào bạn, tôi lắng nghe đây...",
    "emotion_tag": "neutral",
    "sources": [
      { "title": "Sổ tay tâm lý", "page": 10, "content_snippet": "..."}
    ],
    "is_crisis": false,
    "created_at": "timestamp"
  }
  ```

- **Response (Crisis)**:

  ```json
  {
    "is_crisis": true,
    "message": "Chúng tôi rất lo lắng cho bạn...",
    "hotlines": [
      { "name": "Đường dây nóng tâm lý", "number": "1800 599 913", "available": "24/7" }
    ],
    "additional_resources": [
      "Hãy nói chuyện với người thân..."
    ]
  }
  ```

### 2.2 Conversation History

- **Endpoint**: `GET /chat/history`
- **Query Parameters**: `?conversation_id=uuid&limit=50&offset=0`
- **Authorization**:
  - Requires `X-Session-ID` header (session must own conversation) OR
  - `Authorization: Bearer <JWT>` (user must own conversation)
  - Returns 401 if neither provided
  - Returns 403 if session/user doesn't own conversation
- **Response**:

  ```json
  {
    "messages": [
      { "id": "...", "role": "user", "content": "...", "created_at": "..." },
      { "id": "...", "role": "assistant", "content": "...", "created_at": "..." }
    ],
    "total": 25,
    "has_more": false
  }
  ```

### 2.3 Streaming Chat (SSE)

- **Endpoint**: `POST /chat/stream`
- **Description**: Gửi tin nhắn và nhận phản hồi AI qua Server-Sent Events (SSE)
- **Header**: `X-Session-ID: <uuid>`
- **Body**: `{ "content": "..." }`
- **Response**: `text/event-stream`

**Event Types:**

| Type | Description |
|------|-------------|
| `sources` | RAG sources và metadata |
| `chunk` | Text chunk từ AI response |
| `done` | Completion event với message ID |
| `crisis` | Crisis detected response |
| `error` | Error occurred |

**Example SSE events:**

```text
data: {"type": "sources", "sources": [...], "emotion_tag": "neutral"}

data: {"type": "chunk", "content": "Chào "}

data: {"type": "chunk", "content": "bạn, "}

data: {"type": "done", "message_id": "uuid", "created_at": "..."}

data: [DONE]
```

### 2.4 Clear History (Archive)

- **Endpoint**: `DELETE /conversations/{conversation_id}` (NO trailing slash)
- **Description**: Soft delete a conversation (set status='archived')
- **Authorization**: Authenticated users can archive their own conversations. Guests can archive their session's conversation via X-Session-ID.
- **Response**: `{ "message": "Conversation archived successfully" }`

---

## 3. Mood Tracking API

### 3.1 Log Mood

- **Endpoint**: `POST /moods/`
- **Body**:

  ```json
  {
    "mood_value": 4, // 1-5
    "note": "Hôm nay trời đẹp"
  }
  ```

- **Endpoint**: `GET /moods/history/`
- **Query**: `?days=7`
- **Response** (raw entries, not aggregated):

  ```json
  [
    {
      "id": "uuid",
      "mood_value": 4,
      "mood_label": "Happy",
      "note": "Hôm nay trời đẹp",
      "created_at": "2023-10-27T10:00:00Z"
    }
  ]
  ```

---

## 4. Admin API

**Base Path:** `/api/v1/admin/`

**Authentication:** Required - JWT Token with role `admin` or `super_admin`

**Authorization:** Uses `require_admin` dependency

```python
# All admin endpoints protected by:
from src.api.deps import require_admin

@router.get("/endpoint")
async def admin_endpoint(admin: User = Depends(require_admin)):
    # Only accessible by admin/super_admin
    pass
```

### 4.1 Statistics & Analytics

#### Overview Stats

- **Endpoint**: `GET /api/v1/admin/stats/overview`
- **Required Role**: `admin` or `super_admin`
- **Description**: Tổng hợp thống kê hệ thống
- **Response**:

  ```json
  {
    "total_users": 150,
    "total_conversations": 1250,
    "total_messages": 8500,
    "sos_alerts": 12,
    "active_users_7d": 85,
    "avg_messages_per_conversation": 6.8
  }
  ```

#### Word Cloud Data

- **Endpoint**: `GET /api/v1/admin/stats/word-cloud`
- **Query Parameters**: `?limit=100` (số từ khóa top)
- **Description**: Từ khóa được hỏi nhiều nhất
- **Response**:

  ```json
  {
    "words": [
      {"text": "lo_âu", "value": 45},
      {"text": "stress", "value": 38}
    ],
    "total_messages_analyzed": 1000
  }
  ```

#### Mood Trends

- **Endpoint**: `GET /api/v1/admin/stats/mood-trends`
- **Query Parameters**: `?days=30` (số ngày phân tích)
- **Description**: xu hướng cảm xúc người dùng
- **Response**:

  ```json
  {
    "mood_distribution": {
      "1": 15,
      "2": 25,
      "3": 45,
      "4": 60,
      "5": 30
    },
    "total_entries": 175,
    "average_mood": 3.2,
    "period_days": 30
  }
  ```

### 4.2 System Configuration

#### Get All Configs

- **Endpoint**: `GET /api/v1/admin/config/`
- **Description**: Danh sách tất cả system settings
- **Response**:

  ```json
  [
    {
      "key": "sys_prompt",
      "value": "Bạn là một chatbot tư vấn tâm lý...",
      "description": "System prompt for AI"
    },
    {
      "key": "sos_keywords",
      "value": "tự tử, chết, giết, ...",
      "description": "Crisis detection keywords"
    },
    {
      "key": "crisis_hotlines",
      "value": "[{\"name\": \"111\", \"number\": \"111\"}, ...]",
      "description": "Emergency hotline numbers"
    }
  ]
  ```

#### Get Config by Key

- **Endpoint**: `GET /api/v1/admin/config/{key}`
- **Path Parameter**: `key` (sys_prompt | sos_keywords | crisis_hotlines)
- **Response**: Single config object

#### Update Config

- **Endpoint**: `PUT /api/v1/admin/config/{key}`
- **Body**:

  ```json
  {
    "value": "<new_config_value>"
  }
  ```

- **Validation Rules**:
  - `sys_prompt`: 50-5000 characters
  - `sos_keywords`: Comma-separated, minimum 3 keywords
  - `crisis_hotlines`: Valid JSON array with `name` and `number` fields

- **Response**: Updated config object

### 4.3 Knowledge Base Management

#### Upload PDF

- **Endpoint**: `POST /api/v1/admin/knowledge/upload`
- **Content-Type**: `multipart/form-data`
- **Body**:
  - `file`: PDF file (binary)
  - `category`: String (optional, default: "General")

- **Process**:
  1. Validate file type (.pdf)
  2. Save to `./data/` directory
  3. Extract text và chunking
  4. Generate embeddings
  5. Store in ChromaDB

- **Response**:

  ```json
  {
    "message": "PDF uploaded and ingested successfully",
    "filename": "tam_ly_hoc.pdf",
    "chunks": 245,
    "category": "Psychology"
  }
  ```

#### List PDFs

- **Endpoint**: `GET /api/v1/admin/knowledge/list`
- **Response**:

  ```json
  {
    "files": [
      {
        "filename": "tam_ly_hoc.pdf",
        "size_bytes": 2458640,
        "size_mb": 2.34,
        "uploaded_at": 1702834800.0
      }
    ],
    "total": 1
  }
  ```

#### Delete PDF

- **Endpoint**: `DELETE /api/v1/admin/knowledge/{filename}`
- **Path Parameter**: `filename` (PDF filename)
- **Side Effects**:
  - Deletes chunks from ChromaDB
  - Clears semantic cache (ensures stale sources not returned)
  - Deletes file from `./data/`

- **Response**:

  ```json
  {
    "message": "File and associated knowledge data deleted successfully",
    "filename": "tam_ly_hoc.pdf",
    "chunks_deleted": 245,
    "cache_cleared": 15
  }
  ```

---

## 5. Admin User Management API

**Base Path:** `/api/v1/admin/users/`

**Authentication:** Required - Admin or Super Admin role only

**Authorization:** Uses `require_admin` dependency from `src/api/deps.py`

### List Users

**Endpoint:** `GET /api/v1/admin/users/`

**Description:** Retrieve paginated list of users with optional filtering

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number (min: 1) |
| `page_size` | integer | No | 20 | Items per page (min: 1, max: 100) |
| `search` | string | No | - | Search by username or email (case-insensitive) |
| `role` | enum | No | - | Filter by role: `guest`, `user`, `admin`, `super_admin` |
| `is_active` | boolean | No | - | Filter by account status |

**Success Response (200 OK):**

```json
{
  "users": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "john_doe",
      "email": "john@example.com",
      "role": "user",
      "is_active": true,
      "is_anonymous": false,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 156,
  "page": 1,
  "page_size": 20,
  "has_more": true
}
```

**Notes:**

- Anonymous users are excluded from results
- Results ordered by `created_at DESC`

### Ban User

**Endpoint:** `POST /api/v1/admin/users/{user_id}/ban`

**Description:** Ban a user account (deactivate) and invalidate sessions.

**Success Response (200 OK):**

```json
{
  "message": "User banned successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_active": false
}
```

**Side Effects:**

1. Sets `users.is_active = false`
2. Invalidates all user sessions in Redis (immediate logout)
3. Creates audit log entry (USER_BANNED)

### Unban User

**Endpoint:** `POST /api/v1/admin/users/{user_id}/unban`

**Description:** Unban a user account (reactivate).

**Success Response (200 OK):**

```json
{
  "message": "User unbanned successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_active": true
}
```

### Promote User (Super Admin Only)

**Endpoint:** `POST /api/v1/admin/users/{user_id}/promote`

**Description:** Promote a regular user to admin role.

**Authorization:** Requires `super_admin` role (uses `require_super_admin` dependency)

**Success Response (200 OK):**

```json
{
  "message": "User promoted to admin successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "admin"
}
```

**Error Responses:**

- `403 Forbidden`: User is already admin or super_admin
- `404 Not Found`: User not found

### Demote User (Super Admin Only)

**Endpoint:** `POST /api/v1/admin/users/{user_id}/demote`

**Description:** Demote an admin to regular user role.

**Authorization:** Requires `super_admin` role (uses `require_super_admin` dependency)

**Success Response (200 OK):**

```json
{
  "message": "Admin demoted to user successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "user"
}
```

**Error Responses:**

- `403 Forbidden`: Cannot demote super_admin or regular user
- `404 Not Found`: User not found

---

## 5.5 Knowledge Base Maintenance (Admin)

### Reset Knowledge Base

**Endpoint:** `DELETE /api/v1/admin/knowledge/reset-all`

**Description:** Reset entire knowledge base - delete ALL ChromaDB data and semantic cache.

**WARNING:** This is a destructive operation that removes ALL knowledge data.

**Success Response (200 OK):**

```json
{
  "message": "Knowledge base reset successfully",
  "chunks_deleted": 1250,
  "cache_cleared": true
}
```

### Purge Orphaned Data

**Endpoint:** `DELETE /api/v1/admin/knowledge/purge-orphans`

**Description:** Remove ChromaDB chunks whose source PDF files no longer exist in the data directory.

**Use Case:** When PDF files were deleted manually but ChromaDB still has their chunks.

**Success Response (200 OK):**

```json
{
  "message": "Orphaned data purged successfully",
  "orphaned_sources": ["deleted_file.pdf", "old_document.pdf"],
  "chunks_removed": 150,
  "cache_cleared": true
}
```

---

## 5.6 Data Export (User Privacy)

**Endpoint:** `GET /api/v1/conversations/export`

**Description:** Export all user conversations and messages as JSON file.

**Authentication:** Required - JWT Token for authenticated users only.

> **Note**: Guest users cannot export data. Must register to access this feature.

**Headers:**

- `Authorization: Bearer <token>` (required)
- `X-Session-ID` (optional)

**Success Response (200 OK):**

Returns a downloadable JSON file with Content-Disposition header:

```json
{
  "export_date": "2025-12-17T23:00:00.000000",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "conversations": [
    {
      "id": "conversation-uuid",
      "title": "Chat về stress",
      "created_at": "2025-12-17T22:00:00.000000",
      "messages": [
        {
          "role": "user",
          "content": "Tôi cảm thấy căng thẳng",
          "created_at": "2025-12-17T22:00:00.000000",
          "detected_emotion": "stress"
        }
      ]
    }
  ]
}
```

**Notes:**

- Filename format: `chat_history_{user_id}.json`
- Only includes active conversations (excludes archived)

---

## 6. Data Structures

**RAGSource**:
*(Cấu trúc trong `rag_sources`)*

```json
{
  "title": "String (Tên file)",
  "page": "Integer (Số trang)",
  "content_snippet": "String (Đoạn trích dẫn ngắn)"
}
```

**Hotline**:
*(Cấu trúc trong Crisis Response)*

```json
{
  "name": "String (Tên tổ chức)",
  "number": "String (Số điện thoại)",
  "available": "String (Thời gian hoạt động, VD: 24/7)"
}
```

---

## 7. Exercises API (Relaxation)

### 7.1 List Exercises

- **Endpoint**: `GET /api/v1/exercises/`
- **Query Parameters**: `?category=breathing` (optional)
- **Response**:

  ```json
  [
    {
      "id": "breathing-1",
      "title": "Hít thở 4-7-8",
      "category": "breathing",
      "duration_minutes": 5,
      "description": "Kỹ thuật hít thở giúp thư giãn...",
      "steps": ["Hít vào 4 giây", "Giữ 7 giây", "Thở ra 8 giây"],
      "benefits": ["Giảm stress", "Cải thiện giấc ngủ"],
      "icon": "🧘"
    }
  ]
  ```

### 7.2 List Categories

- **Endpoint**: `GET /api/v1/exercises/categories`
- **Response**:

  ```json
  [
    {"id": "breathing", "label": "Hít thở", "count": 3},
    {"id": "mindfulness", "label": "Chánh niệm", "count": 2},
    {"id": "relaxation", "label": "Thư giãn", "count": 2}
  ]
  ```

### 7.3 Get Exercise

- **Endpoint**: `GET /api/v1/exercises/{exercise_id}`
- **Response**: Single exercise object (see 7.1)
- **Error**: `404 Not Found` if exercise_id not found
