# 📚 MASTER DOCUMENTATION - Chatbot RAG Tư Vấn Tâm Lý

**Version:** 1.2  
**Last Updated:** 2025-12-25  
**Status:** ✅ **PRODUCTION READY - CHATBOT WORKING**

---

## 📋 Mục Lục

1. [Tổng Quan Hệ Thống](#1-tổng-quan-hệ-thống)
2. [Kiến Trúc](#2-kiến-trúc)
3. [API Endpoints](#3-api-endpoints)
4. [Phân Quyền (RBAC)](#4-phân-quyền-rbac)
5. [Database Schema](#5-database-schema)
6. [RAG Pipeline](#6-rag-pipeline)
7. [Triển Khai](#7-triển-khai)
8. [Tài Liệu Chi Tiết](#8-tài-liệu-chi-tiết)

---

## 1. Tổng Quan Hệ Thống

### 1.1 Mô Tả

Hệ thống Chatbot tư vấn tâm lý sử dụng công nghệ RAG (Retrieval-Augmented Generation) để cung cấp lời khuyên dựa trên kiến thức chuyên môn tâm lý học.

### 1.2 Trạng Thái Hoàn Thiện

| Component | Status |
|-----------|--------|
| Backend API | ✅ 100% (35/35 endpoints) |
| RAG Pipeline | ✅ Working (Model Fallback) |
| Frontend UI | ✅ 100% |
| Admin Dashboard | ✅ 100% |
| Database | ✅ 100% |
| Documentation | ✅ Updated |

### 1.3 Công Nghệ Sử Dụng

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy |
| **Database** | PostgreSQL 15 |
| **Vector Store** | ChromaDB 0.5.0 |
| **Cache** | Redis |
| **LLM** | Google Gemini (gemini-2.0-flash-exp với fallback) |
| **Frontend** | HTML5, JavaScript (ES6+), TailwindCSS |
| **Web Server** | Nginx |
| **Container** | Docker, Docker Compose |

---

## 2. Kiến Trúc

### 2.1 Architecture Diagram

```text
┌─────────────────────────────────────────────────────────────┐
│                     DOCKER COMPOSE NETWORK                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────────┐   │
│  │  Nginx   │───▶│   FastAPI    │───▶│   PostgreSQL    │   │
│  │  :8080   │    │   :8000      │    │    :5432        │   │
│  └──────────┘    └──────────────┘    └─────────────────┘   │
│       │              │     │                                 │
│       │              │     └─────────▶┌─────────────────┐   │
│       │              │                │   ChromaDB      │   │
│       ▼              │                │   :8001         │   │
│  ┌──────────┐        │                └─────────────────┘   │
│  │  Static  │        │                                       │
│  │  HTML/JS │        └────────────────▶┌─────────────────┐   │
│  └──────────┘                          │     Redis       │   │
│                                        │    :6379        │   │
│                                        └─────────────────┘   │
│                                                              │
│                 ┌───────────────────────────────────┐       │
│                 │       Google Gemini API           │       │
│                 │  (gemini-2.0-flash-exp + fallback)│       │
│                 └───────────────────────────────────┘       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Directory Structure

```text
chatbot_rag_tu_van_tam_ly/
├── src/                      # Backend source code
│   ├── api/v1/              # API endpoints
│   │   ├── admin/           # Admin endpoints (stats, users, config, knowledge)
│   │   ├── auth.py          # Authentication
│   │   ├── chat.py          # Chat API
│   │   ├── moods.py         # Mood tracking
│   │   └── sessions.py      # Session management
│   ├── services/            # Business logic
│   │   └── rag_service.py   # RAG pipeline (với model fallback)
│   └── models/              # SQLAlchemy models
├── static/                   # Frontend files
│   ├── index.html           # Main app
│   ├── admin.html           # Admin dashboard
│   └── js/                  # JavaScript modules
├── docs/                     # Documentation
├── data/                     # PDF knowledge base
├── nginx/                    # Nginx config
└── docker-compose.yml        # Container orchestration
```

---

## 3. API Endpoints

### 3.1 Public (No Auth)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check |
| ~~GET~~ | ~~`/metrics`~~ | ~~Prometheus metrics~~ (Removed - ASGI conflict) |

### 3.2 Guest (Session ID Only)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/sessions/init` | Create session (lazy conversation) |
| GET | `/api/v1/sessions/info` | Get session info |
| DELETE | `/api/v1/sessions/` | End session |
| POST | `/api/v1/chat` | Send message |
| POST | `/api/v1/chat/stream` | Send message (SSE streaming) |
| GET | `/api/v1/chat/history` | View history (requires session) |

### 3.3 User (JWT Required)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/auth/register/` | Register |
| POST | `/api/v1/auth/login/` | Login |
| GET | `/api/v1/auth/me/` | Get profile |
| POST | `/api/v1/moods/` | Log mood |
| GET | `/api/v1/moods/history/` | Mood history |
| GET | `/api/v1/conversations/` | List conversations |
| GET | `/api/v1/conversations/export` | Export data (auth required) |
| DELETE | `/api/v1/conversations/{id}` | Archive |

### 3.4 Admin (JWT + Admin Role)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/admin/stats/overview` | Statistics |
| GET | `/api/v1/admin/stats/word-cloud` | Word cloud |
| GET | `/api/v1/admin/stats/mood-trends` | Mood trends |
| GET | `/api/v1/admin/users/` | List users |
| POST | `/api/v1/admin/users/{id}/ban` | Ban user |
| POST | `/api/v1/admin/users/{id}/unban` | Unban user |
| GET | `/api/v1/admin/config/` | List configs |
| PUT | `/api/v1/admin/config/{key}` | Update config |
| POST | `/api/v1/admin/knowledge/upload` | Upload PDF |
| GET | `/api/v1/admin/knowledge/list` | List PDFs |
| DELETE | `/api/v1/admin/knowledge/{file}` | Delete PDF |
| DELETE | `/api/v1/admin/knowledge/reset-all` | Reset KB |
| DELETE | `/api/v1/admin/knowledge/purge-orphans` | Purge orphans |

### 3.5 Super Admin (JWT + Super Admin Role)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/admin/users/{id}/promote` | Promote to admin |
| POST | `/api/v1/admin/users/{id}/demote` | Demote to user |
| GET | `/api/v1/exercises/` | List exercises |
| GET | `/api/v1/exercises/categories` | List categories |
| GET | `/api/v1/exercises/{id}` | Get exercise |

**Total:** 35 endpoints

---

## 4. Phân Quyền (RBAC)

### 4.1 User Roles

| Role | Description | Auth |
|------|-------------|------|
| 👥 **Guest** | Khách vãng lai | Session ID |
| 👤 **User** | Thành viên | JWT Token |
| 👨‍💼 **Admin** | Quản trị viên | JWT Token + role |
| 👑 **Super Admin** | Quản trị cấp cao | JWT Token + role |

### 4.2 Permission Matrix

| Feature | Guest | User | Admin | Super Admin |
|---------|:-----:|:----:|:-----:|:-----------:|
| Chat with AI | ✅ | ✅ | ✅ | ✅ |
| Crisis Support | ✅ | ✅ | ✅ | ✅ |
| Save chat history | ❌ | ✅ | ✅ | ✅ |
| Mood Tracking | ❌ | ✅ | ✅ | ✅ |
| Export Data | ❌ | ✅ | ✅ | ✅ |
| Admin Dashboard | ❌ | ❌ | ✅ | ✅ |
| Manage Users | ❌ | ❌ | ✅ | ✅ |
| System Config | ❌ | ❌ | ✅ | ✅ |

---

## 5. Database Schema

### 5.1 Tables

| Table | Purpose |
|-------|---------|
| `users` | User accounts + RBAC roles |
| `conversations` | Chat sessions |
| `messages` | Chat messages + RAG sources |
| `mood_entries` | Mood tracking data |
| `feedbacks` | Message ratings |
| `audit_logs` | Admin action logs |
| `system_settings` | System configuration |

### 5.2 Key Fields

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),  -- Argon2id
    role VARCHAR(20) DEFAULT 'user',  -- guest, user, admin, super_admin
    is_active BOOLEAN DEFAULT TRUE,
    is_anonymous BOOLEAN DEFAULT FALSE
);

-- Messages table with RAG support  
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    role VARCHAR(20),  -- user, assistant, system
    content TEXT,
    is_sos BOOLEAN DEFAULT FALSE,
    rag_sources JSONB  -- RAG citations
);
```

---

## 6. RAG Pipeline

### 6.1 Pipeline Flow

```text
User Query → Crisis Detection → Hybrid Search (BM25 + Vector)
           → Reranking → Context Building → LLM Generation
           → Response with Citations
```

### 6.2 Model Configuration

```python
# src/services/rag_service.py
embedding_model = "models/text-embedding-004"
generation_model = "gemini-2.0-flash"

# Fallback mechanism (line 306-311)
candidate_models = [
    "gemini-2.0-flash-exp",   # Primary
    "gemini-flash-latest",    # Fallback 1
    "gemini-1.5-flash",       # Fallback 2
    "gemini-pro"              # Legacy fallback
]
```

### 6.3 Key Parameters

| Parameter | Value |
|-----------|-------|
| Chunk Size | 1000 characters |
| Chunk Overlap | 200 characters |
| Hybrid Alpha | 0.5 (50% BM25 + 50% Vector) |
| Top-K Results | 3 |
| Temperature | 0.7 |

### 6.4 Performance Optimizations ✅ (2025-12-22)

| Optimization | Location | Improvement |
|--------------|----------|-------------|
| BM25 Index Cache | `rag_service.py` | ~200-500ms |
| Query Embedding Reuse | `rag_query()`, `chat_stream.py` | ~100-300ms |
| Semantic Cache | `semantic_cache.py` | Skip RAG on hit |
| ChromaDB Pool | `vector_store.py` | ~50-100ms |
| SOS Keywords Cache | `safety.py` | ~10-30ms |

---

## 7. Triển Khai

### 7.1 Quick Start

```bash
# Clone & setup
git clone <repo-url>
cd chatbot_rag_tu_van_tam_ly
copy .env.example .env
# Edit .env: GOOGLE_API_KEY, SECRET_KEY, POSTGRES_PASSWORD

# Start services
docker-compose up -d --build
docker-compose exec backend alembic upgrade head

# Access
# Frontend: http://localhost:8080
# API Docs: http://localhost:8080/api/v1/docs
```

### 7.2 Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Gemini API key |
| `SECRET_KEY` | JWT signing key |
| `POSTGRES_PASSWORD` | DB password |
| `DEBUG` | Set to `False` for production |

### 7.3 Production SSL

```bash
# Run SSL setup
sudo bash scripts/ssl_setup.sh

# Edit nginx/nginx.conf - uncomment HTTPS block
# Edit docker-compose.yml - uncomment port 443
docker-compose up -d
```

---

## 8. Tài Liệu Chi Tiết

| Topic | Document |
|-------|----------|
| Architecture | [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) |
| API Design | [API_DESIGN.md](API_DESIGN.md) |
| Database | [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) |
| Permissions | [AUTHORIZATION_GUIDE.md](AUTHORIZATION_GUIDE.md) |
| RAG Details | [RAG_WORKFLOW.md](RAG_WORKFLOW.md) |
| User Flow | [USER_FLOW.md](USER_FLOW.md) |
| Features | [FEATURE_LIST.md](FEATURE_LIST.md) |
| Deployment | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) |
| Backup | [BACKUP_AUTOMATION.md](BACKUP_AUTOMATION.md) |
| Errors | [ERROR_RESPONSE_FORMAT.md](ERROR_RESPONSE_FORMAT.md) |
| Status | [SYSTEM_IMPLEMENTATION_STATUS.md](SYSTEM_IMPLEMENTATION_STATUS.md) |

---

## 📊 Changelog

| Date | Change |
|------|--------|
| 2025-12-25 | ✅ Complete documentation audit: endpoint count fix (35), ChromaDB 0.5.0, lazy conversation, exercises/streaming endpoints |
| 2025-12-23 | ✅ Documentation synchronized: trailing slashes, export auth required, RAG chars |
| 2025-12-22 | ✅ Performance optimization: caching, pooling, embedding reuse |
| 2025-12-19 | ✅ Chatbot working with model fallback mechanism |
| 2025-12-19 | ✅ Documentation consolidated and updated |
| 2025-12-18 | ✅ Sprint 4 completed (Admin UI, Export) |
| 2025-12-17 | ✅ Sprint 3 completed (SSL, User Management) |

---

**Document Created:** 2025-12-19  
**Status:** ✅ **PRODUCTION READY**
