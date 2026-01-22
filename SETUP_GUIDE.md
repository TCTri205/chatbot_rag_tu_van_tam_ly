# 🚀 Phase 1 Setup Guide - Hướng Dẫn Khởi Chạy

Hướng dẫn từng bước để khởi chạy hệ thống sau khi hoàn thành Phase 1.

## ✅ Yêu Cầu Trước Khi Bắt Đầu

Đảm bảo bạn đã cài đặt:

- ✅ **Docker Desktop** (đã bật và chạy)
- ✅ **Google Gemini API Key** (từ <https://aistudio.google.com/apikey>)

## 📝 Bước 1: Tạo File `.env`

**Quan trọng**: Tạo file `.env` từ template `.env.example`

```bash
# Windows
copy .env.example .env
```

## 🔑 Bước 2: Cấu Hình `.env`

Mở file `.env` và điền các giá trị sau:

### 2.1. Google API Key (BẮT BUỘC)

```ini
GOOGLE_API_KEY=AIzaSy...  # Thay bằng API key thật của bạn
```

### 2.2. Secret Key (BẮT BUỘC)

Tạo một chuỗi ngẫu nhiên 32+ ký tự cho JWT signing:

```python
# Chạy lệnh Python này để tạo secret key:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Sau đó điền vào `.env`:

```ini
SECRET_KEY=kết_quả_từ_lệnh_trên
```

### 2.3. Database Password (KHUYẾN NGHỊ)

```ini
POSTGRES_PASSWORD=mat_khau_manh_cua_ban_123
```

### 2.4. Kiểm Tra File `.env`

File `.env` hoàn chỉnh sẽ trông như thế này:

```ini
# API Keys
GOOGLE_API_KEY=AIzaSyA7L6ha5UJF...  # YOUR REAL KEY
SECRET_KEY=YyzX9rJ3Kw8N...  # YOUR GENERATED SECRET

# Database
POSTGRES_USER=chatbot_user
POSTGRES_PASSWORD=my_secure_pass_2024  # CHANGE THIS
POSTGRES_DB=chatbot_db
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# App
DEBUG=True
PROJECT_NAME=Chatbot TamLy
API_V1_STR=/api/v1

# Chroma
CHROMA_HOST=chroma
CHROMA_PORT=8000
```

## 🐳 Bước 3: Khởi Động Docker

### 3.1. Build và Start Containers

```bash
docker-compose up -d --build
```

**Quá trình này sẽ:**

- Download các Docker images (PostgreSQL, Redis, Nginx, ChromaDB)
- Build backend container với Python dependencies
- Tự động chạy database migrations
- Khởi động 5 containers

**Thời gian**: Lần đầu khoảng 3-5 phút

### 3.2. Kiểm Tra Trạng Thái Containers

```bash
docker-compose ps
```

**Kết quả mong muốn** - tất cả containers phải **Up**:

```text
NAME                    STATUS
chatbot-nginx-1         Up
chatbot-backend-1       Up
chatbot-db-1            Up
chatbot-redis-1         Up
chatbot-chroma-1        Up
```

### 3.3. Xem Logs (Nếu Có Lỗi)

```bash
# Logs của tất cả services
docker-compose logs

# Chỉ xem logs backend (quan trọng nhất)
docker-compose logs backend

# Theo dõi logs real-time
docker-compose logs -f backend
```

## ✅ Bước 4: Kiểm Tra Hệ Thống

### 4.1. Health Check via Browser

Mở trình duyệt và truy cập: **<http://localhost:8080>**

Bạn sẽ thấy trang landing page với status "✅ Hoạt động tốt"

### 4.2. Health Check via Command Line

```bash
curl http://localhost:8080/api/health
```

**Kết quả mong muốn**:

```json
{
  "status": "ok",
  "timestamp": "2024-12-14T...",
  "services": {
    "database": "connected",
    "redis": "connected"
  }
}
```

### 4.3. Kiểm Tra API Documentation

Mở Swagger UI: **<http://localhost:8080/api/v1/docs>**

Bạn sẽ thấy:

- `/api/health` - Health check
- `/api/v1/auth/register` - User registration
- `/api/v1/auth/login` - User login
- `/api/v1/auth/me` - Get current user

## 🧪 Bước 5: Test API Endpoints

### 5.1. Test Registration (via Swagger UI)

1. Mở <http://localhost:8080/api/v1/docs>
2. Click vào `POST /api/v1/auth/register`
3. Click "Try it out"
4. Nhập:

   ```json
   {
     "email": "test@example.com",
     "password": "password123",
     "username": "test_user"
   }
   ```

5. Click "Execute"
6. **Kết quả**: Trả về `access_token`

### 5.2. Test Login

1. Click vào `POST /api/v1/auth/login`
2. Click "Try it out"
3. Nhập:

   ```json
   {
     "email": "test@example.com",
     "password": "password123"
   }
   ```

4. Click "Execute"
5. **Kết quả**: Trả về `access_token`

### 5.3. Test Authorized Endpoint

1. Copy `access_token` từ bước trên
2. Click nút **Authorize** (ổ khóa) ở đầu trang Swagger
3. Nhập: `Bearer YOUR_TOKEN_HERE`
4. Click "Authorize"
5. Test endpoint `/api/v1/auth/me`
6. **Kết quả**: Trả về thông tin user

## 🔧 Bước 6: Kiểm Tra Database

### 6.1. Kết Nối Vào Database (Tùy Chọn)

Nếu bạn muốn xem database trực tiếp, sử dụng tool như **DBeaver** hoặc **pgAdmin**:

**Uncomment port mapping trong `docker-compose.yml`:**

```yaml
db:
  ports:
    - "5432:5432"  # Bỏ comment dòng này
```

Restart:

```bash
docker-compose down
docker-compose up -d
```

**Thông tin kết nối**:

- Host: `localhost`
- Port: `5432`
- Database: `chatbot_db`
- User: `chatbot_user`
- Password: `(giá trị trong .env)`

### 5. Verify Installation

Run the verification script to ensure everything is working:

```cmd
scripts\phase2\verify_phase2.bat
```

### 6.2. Kiểm Tra Tables

Sau khi kết nối, bạn sẽ thấy các bảng:

- `users`
- `conversations`
- `messages`
- `mood_entries`
- `feedbacks`
- `audit_logs`
- `system_settings`
- `alembic_version` (migration tracking)

## 🛑 Troubleshooting - Xử Lý Lỗi

### ❌ Lỗi: Port 80 Already in Use

**Nguyên nhân**: Một ứng dụng khác đang dùng port 80 (IIS, Apache, XAMPP, Skype)

**Giải pháp**:

```bash
# 1. Tìm process đang dùng port 80
netstat -ano | findstr :80

# 2. Dừng process đó hoặc thay đổi port trong docker-compose.yml
# Hệ thống đã được cấu hình mặc định chạy port 8080 để tránh xung đột này.
# Kiểm tra truy cập http://localhost:8080
```

### ❌ Lỗi: Backend Container Keeps Restarting

**Nguyên nhân**: Thường do thiếu `.env` hoặc API key không đúng

**Giải pháp**:

```bash
# Xem logs để biết lỗi cụ thể
docker-compose logs backend

# Kiểm tra .env file tồn tại
dir .env

# Restart lại
docker-compose restart backend
```

### ❌ Lỗi: Database Connection Failed

**Giải pháp**:

```bash
# Restart database
docker-compose restart db

# Chờ 10 giây rồi restart backend
timeout /t 10
docker-compose restart backend
```

### ❌ Lỗi: Cannot Create .env File

**Giải pháp**: Tạo thủ công

1. Mở Notepad
2. Copy nội dung từ `.env.example`
3. Điền các giá trị
4. Save As → `.env` (chọn "All Files" trong Save as type)

## 🧹 Dọn Dẹp / Reset Hệ Thống

### Reset Hoàn Toàn (Xóa Tất Cả Dữ Liệu)

```bash
# Stop và xóa tất cả containers + volumes
docker-compose down -v

# Xóa folders data
rmdir /s /q pg_data redis_data chroma_data

If you encounter issues, run the quick start script to rebuild:

```cmd
scripts\phase2\quick_start_phase2.bat
```

### Khởi động lại từ đầu

```bash
docker-compose up -d --build
```

### Chỉ Restart Containers

```bash
docker-compose restart
```

### Stop Hệ Thống

```bash
docker-compose down
```

### Start Lại

```bash
docker-compose up -d
```

## 📊 Kết Quả Phase 1

Nếu tất cả bước trên thành công, bạn đã có:

✅ **Infrastructure**

- [x] Nginx gateway (port 8080)
- [x] FastAPI backend (internal port 8000)
- [x] PostgreSQL database (với 7 tables)
- [x] Redis cache
- [x] ChromaDB vector database

✅ **Features**

- [x] User registration with email validation
- [x] JWT authentication
- [x] Password hashing with Argon2
- [x] Health check endpoint
- [x] Auto-run database migrations

✅ **Security**

- [x] Rate limiting (10 req/s)
- [x] CORS protection
- [x] Security headers
- [x] Input validation with Pydantic

## 🎯 Tiếp Theo

Phase 1 hoàn thành! Bạn đã sẵn sàng cho:

**Phase 2**: RAG Engine Implementation

- ChromaDB integration
- Google Gemini LLM service
- Document chunking & embedding
- Hybrid search (Vector + Keyword)

**Tham khảo**: `docs/plans/PHASE_2_RAG_ENGINE.md`

## 💡 Tips

1. **Luôn kiểm tra logs** khi có vấn đề: `docker-compose logs -f backend`
2. **Backup .env file** của bạn ở nơi an toàn
3. **Không commit .env** lên Git (đã được .gitignore bảo vệ)
4. **Test trên Swagger UI** trước khi code frontend

---

## Chúc mừng bạn đã hoàn thành Phase 1! 🎉
