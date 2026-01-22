# 🗺️ Development Roadmap

> "Xây dựng hệ thống Chatbot tư vấn tâm lý an toàn, tin cậy và hiệu quả."

---

## 📅 Overview Timeline

| Phase | Name | Duration | Status |
| :--- | :--- | :--- | :--- |
| **Phase 1** | Foundation & Core | Weeks 1-4 | ✅ **COMPLETED** |
| **Phase 2** | RAG Engine & Features | Weeks 5-8 | ✅ **COMPLETED** |
| **Phase 3** | Admin & Optimization | Weeks 9-10 | ✅ **COMPLETED** |
| **Phase 4** | Deploy & Monitor | Weeks 11-12 | ✅ **READY** (Chatbot Working) |

---

## 🔥 Phase Details

### Phase 1: Foundation (Weeks 1-4) ✅

**Objective**: Basic Chatbot functional with hardcoded responses & DB setup.

- [x] Project Setup (FastAPI, Docker).
- [x] Database Schema Design (PostgreSQL).
- [x] Authentication (JWT, Register/Login).
- [x] Basic Chat API (Echo bot).
- [x] Mood Tracker API (CRUD).
- [x] Frontend POC (Simple HTML/JS Chat UI).

### Phase 2: RAG Engine & Advanced Features (Weeks 5-8) ✅

**Objective**: Integrate Knowledge Base & Crisis Detection.

- [x] Vector Database Setup (ChromaDB).
- [x] Document Ingestion Pipeline (PDF -> Text -> Chunks -> Embeddings).
- [x] Semantic Search Implementation.
- [x] LLM Integration (Google Gemini / OpenAI).
- [x] Crisis Detection Logic (Keyword Spotting).
- [x] Admin Dashboard (Base Stats).

### Phase 3: Admin & Optimization (Weeks 9-10) ✅

**Objective**: Production Readiness, Security & User Management.

## Sprint 3 - Production Readiness ✅ **COMPLETED 2025-12-17**

**Status:** ✅ 100% Complete

### Implemented Features

#### 1. HTTPS/SSL Configuration ✅

- **nginx.conf**: Production-ready SSL/TLS 1.2+ configuration.
- **ssl_setup.sh**: Automated Let's Encrypt setup script.
- **docker-compose.yml**: SSL port 443 & volumes configured.
- **Security**: HSTS header, HTTP->HTTPS redirect.

#### 2. Privacy UI - Clear History ✅

- **UI**: Clear History button in chat header & confirmation modal.
- **Privacy**: Soft delete (archive) + Session reset.
- **UX**: Hidden button when empty history.

#### 3. Admin User Management ✅

- **API**: List users (pagination, search), Ban/Unban.
- **Security**: Admin protection, Session invalidation on ban.
- **Audit**: Comprehensive logging with metadata.

### Technical Debt Addressed

- ✅ **Trailing Slash Compliance**: Fixed all API endpoints for FastAPI compatibility.
- ✅ **Audit Metadata**: Added JSONB column for detailed logs.
- ✅ **Doc Sync**: Archived 13 outdated files, created Master Index.

## Sprint 4 - System Finalization ✅ **COMPLETED 2025-12-17**

**Status:** ✅ 100% Complete - All Core Features Implemented

### Implemented Features

#### 1. Database Migration ✅

- **Script**: `src/scripts/migrate_audit_metadata.py` - Automated migration.
- **Change**: Added `metadata` JSONB column to `audit_logs` table.
- **Purpose**: Store structured context for admin actions (ban reasons, config changes).
- **Execution**: Docker-compatible, idempotent (checks before adding).

#### 2. Admin User Management UI ✅

- **Frontend**: Full User Management interface in `admin.html`.
- **Features**:
  - Paginated user list with search/filter
  - Ban/Unban with real-time updates
  - Role-based badge styling
  - Protection against admin self-bans
- **Backend**: Existing API `/api/v1/admin/users/` fully utilized.
- **Fix**: Corrected syntax error (`async function` → `async def` in `users.py`).

#### 3. Data Export (GDPR Compliance) ✅

- **Endpoint**: `GET /api/v1/conversations/export`.
- **Format**: JSON file with all conversations and messages.
- **Privacy**: Works for authenticated users and guests.
- **Frontend**: "Xuất dữ liệu" button in sidebar (`index.html`).
- **Download**: Automatic file download with proper Content-Disposition header.
- **Filename**: `chat_history_{user_id}.json`.

### Code Quality

- ✅ **Comprehensive Review**: Line-by-line verification completed.
- ✅ **Bug Fixes**: Fixed 2 issues (missing datetime import, incorrect export_date).
- ✅ **No Conflicts**: Verified no duplicate IDs, functions, or routes.
- ✅ **Documentation**: All docs updated (API_DESIGN.md, FEATURE_LIST.md, DATABASE_SCHEMA.md).

---

### Phase 4: Deploy & Monitor (Weeks 11-12) 🟡

**Objective**: Go Live & Maintenance.

- [ ] Staging Deployment.
- [ ] Load Testing (Locust).
- [ ] Monitoring Setup (Prometheus/Grafana - Optional).
- [ ] User Acceptance Testing (UAT).
- [ ] **GO LIVE**.

---

## 🛠️ Critical Checkpoints

1. **Security Audit**:
   - [x] Check SQL Injection (ORM used).
   - [x] Check XSS (Frontend sanitization).
   - [x] Check Rate Limiting (Nginx).
   - [x] SSL Configuration (Sprint 3).

2. **Performance Goals**:
   - Chat Response < 2s.
   - Vector Search < 200ms.
   - Support 100 concurrent users.

3. **Backup Strategy**:
   - Daily DB Dump (Cronjob).
   - Weekly Vector DB snapshot.
