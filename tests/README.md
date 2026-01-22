# Manual Testing Scripts

This directory contains manual Python test scripts for API testing without pytest.

## ⚠️ Prerequisites (QUAN TRỌNG!)

**Backend PHẢI đang chạy trước khi chạy tests!**

### 1. Start Backend

```bash
# Khởi động tất cả services (backend, db, redis, chroma)
docker-compose up -d

# Đợi ~10 giây để backend khởi động hoàn toàn
```

### 2. Verify Backend is Running

```bash
# Check docker containers
docker ps

# Should see: nginx, backend, db, redis, chroma containers

# Check backend health
curl http://localhost:8080/api/health/
# Should return: {"status":"ok"}
```

### 3. Install Python Dependencies

```bash
pip install requests
```

## Test Structure

```
tests/
├── test_utils.py        # Test utilities (TestAPIClient, TestRunner)
├── test_auth.py         # Authentication API tests
├── test_chat.py         # Chat & Session API tests
└── run_all_tests.py     # Main test runner
```

## Prerequisites

1. **Backend must be running:**

   ```bash
   docker-compose up
   ```

2. **Install requests library:**

   ```bash
   pip install requests
   ```

## Running Tests

### Run All Tests

```bash
python tests/run_all_tests.py
```

### Run Individual Test Suites

```bash
# Auth tests
python tests/test_auth.py

# Chat tests
python tests/test_chat.py
```

## Test Coverage

### 1. Authentication (`test_auth.py`)

- ✅ User registration
- ✅ User login
- ✅ JWT token validation
- ✅ Get current user
- ✅ Invalid credentials handling
- ✅ Unauthorized access

### 2. Chat & Sessions (`test_chat.py`)

- ✅ Guest session initialization
- ✅ Send chat message
- ✅ Get chat history
- ✅ Session info retrieval
- ✅ Empty message validation

## Test Output

Tests provide detailed output with:

- ✅ Green checkmarks for passing tests
- ❌ Red X marks for failing tests
- Detailed error messages
- Response data for debugging
- Summary statistics

## Configuration

Base URL is set in `test_utils.py`:

```python
base_url = "http://localhost:8080/api/v1"  # Nginx proxy port
```

**Port Options:**

- `8080`: Nginx proxy (recommended, default in docker-compose)
- `8000`: Direct backend (if running without docker)

Change if your backend runs on different port.

## Troubleshooting

### Error: Connection Refused

```
ConnectionRefusedError: [WinError 10061] No connection could be made...
```

**Solution:** Backend chưa chạy. Khởi động backend:

```bash
docker-compose up -d
```

### Error: 404 Not Found

**Solution:** Sai trailing slash hoặc endpoint không tồn tại. Kiểm tra:

- Tất cả endpoints PHẢI có `/` ở cuối (ví dụ: `/auth/login/`)
- Kiểm tra `docs/API_DESIGN.md` để xem endpoint chính xác

### Tests chạy quá chậm

**Solution:** Backend có thể đang gặp vấn đề. Kiểm tra logs:

```bash
docker-compose logs backend
```

## Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed or error occurred
