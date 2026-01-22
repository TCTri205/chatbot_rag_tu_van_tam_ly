# 🏗️ Phase 1 Detailed Plan: Foundation & Infrastructure

**Mục tiêu**: Xây dựng móng nhà vững chắc. Sau giai đoạn này, bạn sẽ có một hệ thống Backend chạy được, kết nối Database thành công và sẵn sàng để code tính năng.

---

## 1. Setup Environment (Môi trường)

### Step 1.1: Clean & Prepare

*Mục đích*: Dọn dẹp các file cũ không dùng tới (như `app.py` POC).

1. Backup file `app.py` cũ (nếu cần tham khảo):

    ```bash
    ren app.py app_old.py
    ```

2. Tạo cấu trúc thư mục chuẩn:

    ```bash
    mkdir src
    mkdir src\api src\core src\models src\services src\utils
    mkdir nginx
    mkdir migrations
    ```

### Step 1.2: Cấu hình Docker

*Mục đích*: Container hóa mọi thứ để môi trường Dev giống hệt Prod.

1. **Tạo `.env.example`** (Template):

    ```ini
    # API Keys
    GOOGLE_API_KEY=your_google_api_key_here
    SECRET_KEY=your_super_secret_key_32_chars

    # Database
    POSTGRES_USER=chatbot_user
    POSTGRES_PASSWORD=super_secure_password
    POSTGRES_DB=chatbot_db
    POSTGRES_HOST=db
    POSTGRES_PORT=5432

    # Redis
    REDIS_URL=redis://redis:6379/0

    # App
    DEBUG=True
    ```

2. **Tạo `docker-compose.yml`**:

    ```yaml
    version: '3.8'
    services:
      nginx:
        image: nginx:alpine
        ports:
          - "8080:80"
        volumes:
          - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
          - ./static:/usr/share/nginx/html:ro
        depends_on:
          - backend

      backend:
        build: .
        env_file: .env
        volumes:
          - ./src:/app/src
        depends_on:
          - db
          - redis

      db:
        image: postgres:15-alpine
        environment:
          POSTGRES_USER: ${POSTGRES_USER}
          POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
          POSTGRES_DB: ${POSTGRES_DB}
        volumes:
          - ./pg_data:/var/lib/postgresql/data

      redis:
        image: redis:7-alpine
        volumes:
          - ./redis_data:/data

      chroma:
        image: chromadb/chroma:0.5.5
        volumes:
          - ./chroma_data:/chroma/chroma
        ports:
          - "8001:8000"
    ```

3. **Tạo `nginx/nginx.conf`**:

    ```nginx
    events { worker_connections 1024; }

    http {
        include       mime.types;
        default_type  application/octet-stream;
        server_tokens off;

        # Rate Limiting Zone
        limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

        server {
            listen 80;

            # Static Files
            location / {
                root /usr/share/nginx/html;
                try_files $uri $uri/ /index.html;
            }

            # API Proxy
            location /api/ {
                limit_req zone=api_limit burst=20 nodelay;
                proxy_pass http://backend:8000/api/;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Request-ID $request_id;
            }

            # Security Headers
            add_header X-Frame-Options "DENY" always;
            add_header X-Content-Type-Options "nosniff" always;
        }
    }
    ```

4. **Tạo `Dockerfile`**:

    ```dockerfile
    FROM python:3.10-slim

    WORKDIR /app

    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    COPY ./src ./src
    COPY ./migrations ./migrations
    COPY alembic.ini .

    # Auto-run migrations on startup
    CMD alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000
    ```

---

## 2. Backend Base (FastAPI Skeleton)

### Step 2.1: Dependencies

1. **Tạo `Dockerfile`**:
    * Workdir: `/app`.
    * Install: `requirements.txt`.
    * CMD: `uvicorn src.main:app --host 0.0.0.0`.

2. **Cập nhật `requirements.txt`** (Production ready):

    ```text
    fastapi==0.109.0
    uvicorn[standard]==0.27.0
    sqlalchemy[asyncio]==2.0.25
    alembic==1.13.1
    asyncpg==0.29.0
    python-jose[cryptography]==3.3.0
    passlib[argon2]==1.7.4
    python-multipart==0.0.9
    pydantic-settings==2.1.0
    redis==5.0.1
    google-generativeai==0.3.2
    chromadb==0.4.22
    llama-index==0.9.45
    sentence-transformers==2.3.1
    ```

### Step 2.2: Core Application Code

1. **`src/config.py`** (Quản lý Config tập trung):

    ```python
    import os
    from pydantic_settings import BaseSettings

    class Settings(BaseSettings):
        # App
        PROJECT_NAME: str = "Chatbot TamLy"
        API_V1_STR: str = "/api/v1"
        SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_secret")
        DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

        # Database
        POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
        POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
        POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "db")
        POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
        POSTGRES_DB: str = os.getenv("POSTGRES_DB", "chatbot_db")
        
        @property
        def DATABASE_URL(self) -> str:
            return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

        # Redis
        REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
        
        # AI
        GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
        
        # Chroma (Internal Docker Network)
        CHROMA_HOST: str = "chroma"
        CHROMA_PORT: int = 8000

    settings = Settings()
    ```

2. **`src/database.py`**:
    * Setup `AsyncEngine` và `AsyncSessionLocal`.
    * Hàm `get_db()` dependency.

3. **`src/main.py`**:
    * Khởi tạo `FastAPI()`.
    * Setup CORS Middleware.
    * Endpoint `/health` check DB connection.

4. **`src/core/security.py`** (Implementation, Step 2.3):
    * Mục đích: Xử lý Hash mật khẩu và Tạo JWT Token.

    ```python
    from datetime import datetime, timedelta
    from passlib.context import CryptContext
    from jose import jwt
    from src.config import settings

    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

    def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(password):
        return pwd_context.hash(password)

    def create_access_token(data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        # Encode with RS256 or HS256 based on config (Using HS256 for MVP)
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
        return encoded_jwt
    ```

---

### Chú ý về Nginx Config (Refined)

Trong `nginx/nginx.conf`, để đảm bảo `proxy_pass` hoạt động đúng với FastAPI prefix `/api/v1`:

```nginx
            # API Proxy
            location /api/ {
                # Chuyển tiếp nguyên vẹn path: /api/v1/chat -> /api/v1/chat
                proxy_pass http://backend:8000; 
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Request-ID $request_id;
            }
```

---

## 3. Database Schema Migration

### Step 3.1: Define Models

1. **`src/models/base.py`**: Class `Base` (Declarative).
2. **`src/models/user.py`**: Bảng `users` (id, email, password, role).
3. **`src/models/chat.py`**: Bảng `conversations`, `messages`, `mood_entries`.

### Step 3.2: Define Schemas (Input Validation)

1. **`src/schemas/auth.py`** (Code Snippet):
    * Mục đích: Validate input đăng ký/đăng nhập ngay tại lớp API, trước khi vào Logic.

    ```python
    from pydantic import BaseModel, EmailStr, Field

    class UserCreate(BaseModel):
        email: EmailStr
        password: str = Field(..., min_length=8, description="Mật khẩu tối thiểu 8 ký tự")
        full_name: str | None = Field(None, max_length=100)
        
        # Validator tự động:
        # - EmailStr: check đúng format a@b.c
        # - min_length=8: chặn mật khẩu ngắn

    class Token(BaseModel):
        access_token: str
        token_type: str
    ```

### Step 3.3: Alembic Setup

1. Chạy `alembic init -t async migrations`.
2. Sửa `alembic.ini`: Trỏ `sqlalchemy.url` tới biến môi trường.
3. Sửa `migrations/env.py`: Import `Base` để autogenerate.

---

## ✅ Verification Checklist (Phase 1)

1. **Run Containers**:

    ```bash
    docker-compose up -d --build
    ```

    > Check: `docker ps` phải thấy 4 container (nginx, backend, db, redis) đều Up.

2. **Check API Health**:

    ```bash
    curl http://localhost:8080/api/health
    ```

    > Expected: `{"status": "ok", "db": "connected", "redis": "connected"}`.

3. **Auto Migration**:
    * Backend tự chạy migration khi start (cần script `prestart.sh`).
    * Kiểm tra DB: Dùng DBeaver/PgAdmin connect port 5432, thấy đủ bảng.

👉 **Hoàn thành các bước trên nghĩa là bạn đã XONG Phase 1.**
