# Phase 2 Verification Checklist

Sử dụng checklist này để verify từng bước Phase 2 implementation.

## ✅ Pre-Deployment Checklist

- [ ] **Check `.env` file exists** với tất cả required variables:

  ```bash
  GOOGLE_API_KEY=...
  POSTGRES_USER=chatbot_user
  POSTGRES_PASSWORD=...
  POSTGRES_DB=chatbot_db
  SECRET_KEY=...
  ```

- [ ] **Verify Docker is running**:

  ```bash
  docker --version
  docker-compose --version
  ```

- [ ] **Check project structure**:
  - [ ] `src/core/vector_store.py` exists
  - [ ] `src/core/safety.py` exists
  - [ ] `src/services/rag_service.py` exists
  - [ ] `src/api/v1/chat.py` exists
  - [ ] `src/api/v1/sessions.py` exists
  - [ ] `src/api/v1/moods.py` exists
  - [ ] `migrations/versions/2025_12_15_1030-seed_system_settings_phase2.py` exists
  - [ ] `migrations/versions/2025_12_15_1035-allow_guest_conversations.py` exists

---

## 🚀 Deployment Steps

### Step 1: Build and Start Services

```bash
# Build backend with new dependencies
docker-compose build backend

# Start all services
docker-compose up -d

# Check all containers are running
docker-compose ps
```

**Expected Output**: 5 containers running (nginx, backend, db, redis, chroma)

**Status**: [ ] PASS / [ ] FAIL

**Notes**: _____________________

---

### Step 2: Run Database Migrations

```bash
# Run migrations
docker-compose exec backend alembic upgrade head
```

**Expected Output**:

```text
INFO  [alembic.runtime.migration] Running upgrade ... -> seed_system_settings
INFO  [alembic.runtime.migration] Running upgrade ... -> allow_guest_conversations
```

**Status**: [ ] PASS / [ ] FAIL

**Notes**: _____________________

---

### Step 3: Verify System Settings

```bash
# Connect to PostgreSQL and check system_settings
docker-compose exec db psql -U chatbot_user -d chatbot_db

# In psql:
SELECT * FROM system_settings;
```

**Expected Output**: 3 rows với keys: `sys_prompt`, `sos_keywords`, `crisis_hotlines`

**Status**: [ ] PASS / [ ] FAIL

**Notes**: _____________________

---

### Step 4: Verify ChromaDB

```bash
# Check ChromaDB heartbeat
curl http://localhost:8001/api/v2/heartbeat
```

**Expected Output**: Nanosecond timestamp (e.g., `1734234567890123456`)

**Status**: [ ] PASS / [ ] FAIL

**Notes**: _____________________

---

### Step 5: Check Backend Logs

```bash
docker-compose logs backend --tail=50
```

**Look for**:

- [x] No errors during startup
- [x] "Connected to ChromaDB" message (if vector_store was used)
- [x] Uvicorn started successfully

**Status**: [ ] PASS / [ ] FAIL

**Notes**: _____________________

---

## 🧪 API Testing

### Test 1: API Documentation

```bash
# Open in browser
http://localhost:8080/api/v1/docs
```

**Verify**:

- [ ] 6 endpoint groups visible: Health, Authentication, Chat, Sessions, Mood Tracking
- [ ] Chat endpoints: POST /chat, GET /chat/history
- [ ] Sessions endpoints: POST /sessions/init, GET /sessions/info, DELETE /sessions
- [ ] Moods endpoints: POST /moods, GET /moods/history

**Status**: [ ] PASS / [ ] FAIL

---

### Test 2: Session Initialization

**Request**:

```bash
curl -X POST http://localhost:8080/api/v1/sessions/init \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected Response**:

```json
{
  "session_id": "<uuid>",
  "conversation_id": "<uuid>",
  "greeting": "Chào bạn! Tôi là trợ lý tâm lý AI...",
  "created_at": "..."
}
```

**Save session_id**: `_____________________`

**Status**: [ ] PASS / [ ] FAIL

---

### Test 3: Crisis Detection

**Request** (use session_id from Test 2):

```bash
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: <your_session_id>" \
  -d '{"content": "tôi muốn chết"}'
```

**Expected Response**:

```json
{
  "is_crisis": true,
  "message": "Chúng tôi rất lo lắng cho bạn...",
  "hotlines": [...]
}
```

**Verify**:

- [ ] `is_crisis` = true
- [ ] Hotlines array contains at least 2 entries
- [ ] Message has crisis intervention text

**Status**: [ ] PASS / [ ] FAIL

---

### Test 4: Normal Chat

**Request**:

```bash
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: <your_session_id>" \
  -d '{"content": "xin chào, bạn là ai?"}'
```

**Expected Response**:

```json
{
  "message_id": "<uuid>",
  "role": "assistant",
  "content": "...",
  "sources": [],
  "is_crisis": false
}
```

**Verify**:

- [ ] `is_crisis` = false
- [ ] `content` has meaningful response
- [ ] `sources` is empty (if no PDFs ingested) or has items

**Status**: [ ] PASS / [ ] FAIL

---

### Test 5: Chat History

**Request** (use conversation_id from Test 2):

```bash
curl "http://localhost:8080/api/v1/chat/history?conversation_id=<conversation_id>&limit=10"
```

**Expected Response**:

```json
{
  "messages": [...],
  "total": 4,
  "has_more": false
}
```

**Verify**:

- [ ] Messages array contains at least 4 messages (2 from crisis test, 2 from normal test)
- [ ] Message with `is_sos: true` exists
- [ ] Messages are ordered chronologically

**Status**: [ ] PASS / [ ] FAIL

---

### Test 6: Session Info

**Request**:

```bash
curl http://localhost:8080/api/v1/sessions/info \
  -H "X-Session-ID: <your_session_id>"
```

**Expected Response**:

```json
{
  "session_id": "...",
  "user_id": null,
  "conversation_id": "...",
  "is_active": true
}
```

**Verify**:

- [ ] `user_id` is null (guest user)
- [ ] `is_active` = true
- [ ] `conversation_id` matches from Test 2

**Status**: [ ] PASS / [ ] FAIL

---

## 📊 Database Verification

### Check Conversations Table

```sql
-- Connect to DB
docker-compose exec db psql -U chatbot_user -d chatbot_db

-- Query
SELECT id, user_id, title, status, created_at 
FROM conversations 
ORDER BY created_at DESC 
LIMIT 5;
```

**Verify**:

- [ ] At least 1 conversation with `user_id = NULL` (guest)
- [ ] Status = 'ACTIVE'

**Status**: [ ] PASS / [ ] FAIL

---

### Check Messages Table

```sql
SELECT id, role, content, is_sos, rag_sources 
FROM messages 
ORDER BY created_at DESC 
LIMIT 10;
```

**Verify**:

- [ ] At least 1 message with `is_sos = true`
- [ ] Messages have both 'USER' and 'ASSISTANT' roles
- [ ] `rag_sources` column exists (may be NULL)

**Status**: [ ] PASS / [ ] FAIL

---

## 🔬 Optional: PDF Ingestion Test

### Step 1: Add Sample PDF

Create a simple text file and save as `data/test.txt`:

```text
Stress Management Tips

1. Practice deep breathing
2. Get regular exercise
3. Maintain healthy sleep schedule
```

### Step 2: Run Ingestion

```bash
docker-compose exec backend python -m src.scripts.ingest
```

**Expected Output**:

```text
Processing: test.txt
Created X chunks, generating embeddings...
Ingested batch 1: X chunks
✓ Completed test.txt: X chunks ingested
```

**Status**: [ ] PASS / [ ] FAIL / [ ] SKIPPED

---

### Step 3: Verify ChromaDB Collection

```bash
# Check collection count (via Python)
docker-compose exec backend python -c "from src.core.vector_store import get_collection; print(f'Collection count: {get_collection().count()}')"
```

**Expected**: Count > 0

**Status**: [ ] PASS / [ ] FAIL / [ ] SKIPPED

---

### Step 4: Test RAG with Knowledge

```bash
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: <session_id>" \
  -d '{"content": "làm sao để giảm stress?"}'
```

**Verify**:

- [ ] Response references content from PDF
- [ ] `sources` array is NOT empty
- [ ] Source has correct filename and page

**Status**: [ ] PASS / [ ] FAIL / [ ] SKIPPED

---

## 📝 Final Summary

### Implementation Status

**Core Components**:

- [ ] ChromaDB connection: PASS / FAIL
- [ ] Safety layer: PASS / FAIL
- [ ] RAG service: PASS / FAIL / PARTIAL (no PDFs)
- [ ] Chat API: PASS / FAIL
- [ ] Sessions API: PASS / FAIL
- [ ] Mood API: NOT TESTED (requires auth)

**Database**:

- [ ] Migrations executed: PASS / FAIL
- [ ] System settings populated: PASS / FAIL
- [ ] Guest conversations supported: PASS / FAIL

**APIs**:

- [ ] Crisis detection: PASS / FAIL
- [ ] Normal chat: PASS / FAIL
- [ ] Session management: PASS / FAIL

### Issues Found

1. Issue: ______________________________
   Status: RESOLVED / PENDING

2. Issue: ______________________________
   Status: RESOLVED / PENDING

### Overall Phase 2 Status

- [ ] ✅ FULLY OPERATIONAL
- [ ] ⚠️ PARTIALLY WORKING (specify what's broken)
- [ ] ❌ NOT WORKING (critical issues)

### Next Steps

- [ ] Fix any failing tests
- [ ] Ingest real psychology PDFs
- [ ] Test mood tracking with authenticated users
- [ ] Proceed to Phase 3 (Frontend)

---

**Completed by**: _____________  
**Date**: _____________  
**Sign-off**: _____________
