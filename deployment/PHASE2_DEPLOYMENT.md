# Phase 2 Deployment Guide

## Prerequisites

Đảm bảo Phase 1 đã hoàn thành:

- ✅ Docker containers đang chạy (backend, db, redis, nginx, chroma)
- ✅ Database đã được migrate
- ✅ Google API Key đã được cấu hình trong `.env`

## Deployment Steps

### 1. Install New Dependencies

```bash
# Install mới các package cho Phase 2
pip install -r requirements.txt
```

Hoặc nếu dùng Docker:

```bash
docker-compose build backend
```

### 2. Run Database Migration

```bash
# Chạy migration để seed system settings
docker-compose exec backend alembic upgrade head
```

**Kết quả mong đợi**: Migration `seed_system_settings` sẽ thêm 3 records vào bảng `system_settings`:

- `sys_prompt`: System instruction cho Gemini
- `sos_keywords`: Danh sách keywords phát hiện crisis
- `crisis_hotlines`: Thông tin đường dây nóng

**Important**: Nếu gặp lỗi "database system is starting up", chờ thêm vài giây và chạy lại. Hoặc kiểm tra trước:

```bash
# Kiểm tra database đã sẵn sàng chưa
docker-compose exec db pg_isready -U postgres
# Output mong đợi: "accepting connections"
```

### 3. Verify ChromaDB Running

```bash
# Check ChromaDB health
curl http://localhost:8001/api/v2/heartbeat
```

**Expected Output**: `{"nanosecond heartbeat": ...}`

### 4. Add Knowledge Base (Optional for testing)

Thêm PDF files vào thư mục `data/` và chạy ingestion:

```bash
# Copy sample PDF vào data/ trước
docker-compose exec backend python -m src.scripts.ingest
```

**Note**: Có thể bỏ qua bước này để test mà không cần PDF. System sẽ trả lời "không tìm thấy thông tin phù hợp".

### 5. Restart Backend

```bash
docker-compose restart backend
```

### 6 Verify API Documentation

Truy cập: <http://localhost:8080/api/v1/docs>

**Kiểm tra có 6 groups**:

- Health
- Authentication  
- Chat (NEW)
- Sessions (NEW)
- Mood Tracking (NEW)

## Testing Phase 2 Features

### Test 1: Session Initialization

```bash
curl -X POST http://localhost:8080/api/v1/sessions/init \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected Response**:

```json
{
  "session_id": "uuid",
  "conversation_id": "uuid",
  "greeting": "Chào bạn! Tôi là trợ lý tâm lý AI...",
  "created_at": "2024-..."
}
```

**Lưu lại `session_id` để dùng cho các test tiếp theo**.

### Test 2: Safety Check (Crisis Detection)

```bash
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: <session_id_from_test1>" \
  -d '{"content": "Tôi muốn chết"}'
```

**Expected Response**:

```json
{
  "is_crisis": true,
  "message": "Chúng tôi rất lo lắng cho bạn...",
  "hotlines": [...]
}
```

### Test 3: Normal Chat (RAG-powered)

```bash
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: <session_id>" \
  -d '{"content": "Làm sao để bớt lo âu?"}'
```

**Expected Response**:

```json
{
  "message_id": "uuid",
  "role": "assistant",
  "content": "...",
  "sources": [],  # Empty nếu chưa ingest PDF
  "is_crisis": false
}
```

### Test 4: Mood Logging (Requires Authenticated User)

**Note**: Mood tracking chỉ cho registered users. Cần login trước:

```bash
# Login để lấy token
TOKEN=$(curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}' \
  | jq -r .access_token)

# Log mood
curl -X POST http://localhost:8080/api/v1/moods \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Session-ID: <session_id>" \
  -H "Content-Type: application/json" \
  -d '{"mood_value": 4, "mood_label": "happy", "note": "Ngày tốt"}'
```

### Test 5: Mood History

```bash
curl -X GET "http://localhost:8080/api/v1/moods/history?days=7" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Session-ID: <session_id>"
```

### Test 6: Chat History

```bash
curl -X GET "http://localhost:8080/api/v1/chat/history?conversation_id=<conversation_id>" \
  -H "Authorization: Bearer $TOKEN"
```

## Database Verification

Connect to PostgreSQL và check:

```sql
-- Check system settings
SELECT * FROM system_settings;

-- Check messages with RAG sources
SELECT id, role, content, rag_sources, is_sos 
FROM messages 
ORDER BY created_at DESC 
LIMIT 10;

-- Check conversations
SELECT * FROM conversations ORDER BY created_at DESC LIMIT 5;

-- Check mood entries
SELECT * FROM mood_entries ORDER BY created_at DESC LIMIT 10;
```

## Troubleshooting

### Issue: "Database system is starting up"

**Solution**:

```bash
# Wait for database to be ready
docker-compose exec db pg_isready -U postgres
# Retry migration when output shows "accepting connections"
docker-compose exec backend alembic upgrade head
```

**Note**: Automated scripts (`quick_start_phase2.bat`, `verify_phase2.bat`) now handle this automatically.

### Issue: "ChromaDB connection failed"

**Solution**:

```bash
docker-compose up -d chroma
docker-compose logs chroma
```

### Issue: "Google API Key error"

**Solution**: Verify `.env`:

```bash
GOOGLE_API_KEY=your_actual_api_key_here
```

### Issue: "Failed to generate embedding"

**Possible causes**:

- API quota exceeded
- Invalid API key
- Network connectivity

**Check logs**:

```bash
docker-compose logs backend | grep -i "error"
```

### Issue: "Session not found"

**Solution**: Sessions expire after 24h. Initialize new session.

## Success Criteria

✅ **Phase 2 thành công nếu**:

1. All 3 new router groups hiển thị trong API docs
2. Session init trả về session_id
3. Chat với crisis keyword trả về hotlines
4. Chat bình thường trả về response (có hoặc không có sources tùy vào đã ingest PDF chưa)
5. System settings table có 3 records
6. Messages được save với rag_sources và is_sos fields

## Next Steps

Phase 3 sẽ triển khai:

- Frontend UI
- Real-time streaming responses
- Emotion detection
- Advanced analytics
