# Chatbot RAG Tư Vấn Tâm Lý

Hệ thống chatbot tư vấn tâm lý sử dụng RAG (Retrieval-Augmented Generation) với FastAPI, PostgreSQL, Redis, và ChromaDB.

## 🎯 Status: ✅ PRODUCTION READY - CHATBOT WORKING

**Last Updated:** 2025-12-19

## 🚀 Phase 1: Foundation & Infrastructure - COMPLETED ✅

- ✅ Docker infrastructure (Nginx, FastAPI, PostgreSQL, Redis, ChromaDB)
- ✅ Backend core structure với FastAPI
- ✅ Database models và migrations (Alembic)
- ✅ Authentication system (JWT)
- ✅ API endpoints (Health check, Auth)
- ✅ Pydantic schemas cho validation

## 🧠 Phase 2: RAG Engine & Core Logic - COMPLETED ✅

- ✅ RAG Service với Gemini embeddings & generation
- ✅ ChromaDB vector store integration
- ✅ Safety layer (crisis detection với SOS keywords)
- ✅ Chat API với context-aware responses + source citations
- ✅ Session management (guest + authenticated users)
- ✅ Mood tracking API
- ✅ PDF knowledge ingestion script

## 👨‍💼 Phase 3: Admin & Optimization - COMPLETED ✅

- ✅ Admin Dashboard (Statistics, Word Cloud, Mood Trends)
- ✅ User Management (List, Ban/Unban với audit logs)
- ✅ Knowledge Base Management (Upload/Delete PDFs)
- ✅ System Configuration Editor
- ✅ HTTPS/SSL Configuration
- ✅ Privacy UI (Clear History, Export Data)

## 🚀 Phase 4: Production Ready - COMPLETED ✅

- ✅ **Model Fallback Mechanism** - Chatbot luôn hoạt động với fallback models
- ✅ Backup Automation (PowerShell/Bash scripts)
- ✅ Complete Documentation

## 📋 Requirements

- Docker Desktop
- Python 3.10+ (cho local development)
- Google Gemini API Key với quota cho:
  - Embeddings API (text-embedding-004)
  - Generation API (gemini-2.0-flash-exp hoặc fallback models)

## 🛠️ Quick Start

### 1. Clone và Setup Environment

```bash
# Tạo file .env từ template
copy .env.example .env

# Sửa file .env và điền:
# - GOOGLE_API_KEY=your_actual_api_key
# - SECRET_KEY=random_32_character_string
# - POSTGRES_PASSWORD=strong_password
```

### 2. Khởi động hệ thống (Phase 2)

```bash
# Option 1: Quick start script (recommended)
scripts\phase2\quick_start_phase2.bat

# Option 2: Manual
docker-compose up -d --build
docker-compose exec backend alembic upgrade head

# Kiểm tra status
docker-compose ps

# Xem logs
docker-compose logs -f backend
```

### 3. Truy cập hệ thống

- **Frontend**: <http://localhost:8080>
- **API Docs**: <http://localhost:8080/api/v1/docs>
- **Health Check**: <http://localhost:8080/api/health>
- **ChromaDB**: <http://localhost:8001> (internal)

### 4. Verify Installation

```bash
# Windows
scripts\phase2\verify_phase2.bat

# Linux/Mac
./scripts/phase2/verify_phase2.sh
```

### 5. Quick Start (All-in-One)

```bash
scripts\phase2\quick_start_phase2.bat
```

### 6. Testing Phase 2

```bash
# Test APIs
scripts\phase2\test_phase2_apis.bat

# Or follow manual checklist
# See: PHASE2_VERIFICATION_CHECKLIST.md
```

## 📁 Project Structure

```text
chatbot_rag_tu_van_tam_ly/
├── src/                      # Source code
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── api/                 # API routes
│   │   └── v1/              # API v1 endpoints
│   │       ├── auth.py      # Authentication
│   │       ├── chat.py      # Chat (NEW Phase 2)
│   │       ├── sessions.py  # Session management (NEW)
│   │       └── moods.py     # Mood tracking (NEW)
│   ├── core/                # Core utilities
│   │   ├── security.py      # JWT, password hashing
│   │   ├── safety.py        # Crisis detection (NEW)
│   │   ├── vector_store.py  # ChromaDB client (NEW)
│   │   └── redis.py         # Redis connection
│   ├── services/            # Business logic (NEW)
│   │   └── rag_service.py   # RAG pipeline
│   ├── scripts/             # Utility scripts (NEW)
│   │   └── ingest.py        # PDF ingestion
│   └── utils/               # Helper functions
├── migrations/              # Alembic migrations
├── nginx/                   # Nginx configuration
├── static/                  # Frontend static files
├── data/                    # PDF knowledge base (NEW)
├── docs/                    # Documentation
│   ├── plans/               # Phase plans
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── DATABASE_SCHEMA.md
│   └── API_DESIGN.md
├── PHASE2_DEPLOYMENT.md     # Phase 2 deployment guide (NEW)
├── PHASE2_SCRIPTS_README.md # Testing tools guide (NEW)
├── PHASE2_VERIFICATION_CHECKLIST.md  # Manual checklist (NEW)
├── quick_start_phase2.bat   # Quick deployment script (NEW)
├── verify_phase2.bat        # Verification script (NEW)
├── test_phase2_apis.bat     # API testing script (NEW)
├── docker-compose.yml       # Container orchestration
├── Dockerfile              # Backend container build
├── requirements.txt        # Python dependencies
└── .env.example           # Environment template
```

## 🗄️ Database Models

Phase 1 & 2 includes:

- **Users**: Authentication và user roles (guest/user/admin/super_admin)
- **Conversations**: Chat sessions (supports NULL user_id for guests)
- **Messages**: Chat history với **RAG sources** (JSONB) và **SOS detection** (BOOLEAN)
- **MoodEntries**: Mood tracking
- **Feedbacks**: Message ratings
- **AuditLogs**: Security audit trail
- **SystemSettings**: Dynamic configuration (system prompts, SOS keywords, hotlines)

## 🔐 API Endpoints

### Health

- `GET /api/health` - System health check

### Authentication (Phase 1)

- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login (returns JWT)
- `GET /api/v1/auth/me` - Get current user info (requires auth)

### Chat (Phase 2) 🆕

- `POST /api/v1/chat` - Send message và receive AI response
  - Headers: `X-Session-ID` (required)
  - Returns: ChatResponse hoặc CrisisResponse
- `GET /api/v1/chat/history` - Get conversation history
  - Params: `conversation_id`, `limit`, `offset`

### Sessions (Phase 2) 🆕

- `POST /api/v1/sessions/init` - Initialize new session
  - Works for guests and authenticated users
- `GET /api/v1/sessions/info` - Get session information
- `DELETE /api/v1/sessions/` - End session

### Mood Tracking (Phase 2) 🆕

- `POST /api/v1/moods` - Log mood entry (authenticated only)
- `GET /api/v1/moods/history` - Get mood history
  - Params: `days` (1-90, default 7)

## 🧪 Testing

### Phase 1 Tests

```bash
# Health check
curl http://localhost:8080/api/health

# Register user
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@example.com\",\"password\":\"password123\"}"

# Login
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@example.com\",\"password\":\"password123\"}"
```

### Phase 2 Tests 🆕

```bash
# Initialize session
curl -X POST http://localhost:8080/api/v1/sessions/init \
  -H "Content-Type: application/json" \
  -d '{}'

# Test crisis detection (use session_id from above)
curl -X POST http://localhost:8080/api/v1/chat \
  -H "X-Session-ID: <your_session_id>" \
  -H "Content-Type: application/json" \
  -d '{"content": "tôi muốn chết"}'

# Normal chat
curl -X POST http://localhost:8080/api/v1/chat \
  -H "X-Session-ID: <your_session_id>" \
  -H "Content-Type: application/json" \
  -d '{"content": "xin chào"}'
```

**Or use automated scripts**:

```bash
test_phase2_apis.bat
```

## 🚦 Development Phases

- ✅ **Phase 1**: Foundation & Infrastructure
- ✅ **Phase 2**: RAG Engine & Core Logic  
- ✅ **Phase 3**: Admin Dashboard & Optimization
- ✅ **Phase 4**: Production Ready (Chatbot Working)

## 📝 Documentation

### Core Documentation (docs/)

- `MASTER_DOCUMENTATION.md` - **Tài liệu tổng hợp** 🆕
- `SYSTEM_ARCHITECTURE.md` - Kiến trúc hệ thống
- `DATABASE_SCHEMA.md` - Thiết kế database
- `API_DESIGN.md` - API specification
- `AUTHORIZATION_GUIDE.md` - Phân quyền RBAC
- `RAG_WORKFLOW.md` - RAG pipeline chi tiết

### Status & Plans (docs/)

- `SYSTEM_IMPLEMENTATION_STATUS.md` - Trạng thái hệ thống
- `DEVELOPMENT_ROADMAP.md` - Lộ trình phát triển
- `plans/BAO_CAO_RA_SOAT_HE_THONG.md` - Báo cáo rà soát

### Knowledge Base

- `data/README.md` - How to add PDFs 🆕

## 🛑 Troubleshooting

### Port already in use

```bash
# Kiểm tra process đang dùng port 80
netstat -ano | findstr :80

# Stop các container cũ
docker-compose down
```

### Database connection error

```bash
# Restart database container
docker-compose restart db

# Check logs
docker-compose logs db
```

### Migration errors

```bash
# Reset database (WARNING: Deletes all data)
docker-compose down -v
docker-compose up -d --build
```

## 🤝 Contributing

1. Tạo branch mới từ `main`
2. Implement changes
3. Test locally
4. Submit pull request

## 📄 License

Private project - All rights reserved
