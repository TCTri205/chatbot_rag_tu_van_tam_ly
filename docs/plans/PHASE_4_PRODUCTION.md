# 🛡️ Phase 4 Detailed Plan: Production Readiness

**Mục tiêu**: Biến ứng dụng thành "Pháo đài". An toàn, Giám sát được và Chịu tải tốt.

---

## 1. Security Hardening

### Step 1.1: Backend Security

*File*: `src/main.py` & `src/middleware/`

1. **CORS Strict Mode**:
    * Chỉ allow domains cụ thể (VD: `https://tamly.vn`).
    * `allow_credentials=True`.

2. **Rate Limiting**:
    * Sử dụng `slowapi` hoặc Nginx zone.
    * Limit: 5 req/s cho Chat Endpoint.

3. **Prompt Injection Shield**:
    * **Implementation**: Dependency injection in chat endpoint (not middleware to avoid ASGI conflicts).
    * **Validation**: Check input patterns like "Ignore previous instructions", "System Prompt" -> Return HTTP 400.

### Step 1.2: Nginx Hardening

*File*: `nginx/nginx.conf`

1. **Headers**:
    * `X-Content-Type-Options: nosniff`
    * `X-Frame-Options: DENY` (Chống clickjacking)
    * `Strict-Transport-Security` (HSTS).

2. **Turn off Server Tokens**: `server_tokens off;` (Ẩn version Nginx).

---

## 2. Observability Stack

### Step 2.1: Monitoring Setup

*Mục đích*: Đo lường sức khỏe hệ thống.

1. **Cập nhật `docker-compose.yml`** (Nếu chưa):
    * Thêm `prometheus` (Port 9090).
    * Thêm `grafana` (Port 3000).

2. **Config `monitoring/prometheus.yml`**:

    ```yaml
    global:
      scrape_interval: 15s

    scrape_configs:
      - job_name: 'backend'
        metrics_path: '/metrics'
        static_configs:
          - targets: ['backend:8000']
    ```

3. **Backend Instrumentation**:
    * ⚠️ **Note**: `/metrics` endpoint removed due to ASGI compatibility issues (`RuntimeError` with Starlette).
    * **Alternative**: Use external monitoring or custom implementation not relying on `prometheus-fastapi-instrumentator`.

---

## 3. Deployment Checklist

### Step 3.1: Pre-flight Check

1. **Database Backup Automation**:
    * Tạo script `scripts/backup.sh`:

    ```bash
    #!/bin/bash
    TIMESTAMP=$(date +"%F")
    BACKUP_DIR="./backups"
    mkdir -p $BACKUP_DIR

    # Dump Database
    docker-compose exec -T db pg_dump -U chatbot_user chatbot_db > $BACKUP_DIR/db_$TIMESTAMP.sql

    # Compress
    gzip $BACKUP_DIR/db_$TIMESTAMP.sql

    echo "Backup created: $BACKUP_DIR/db_$TIMESTAMP.sql.gz"
    
    # Auto delete older than 30 days
    find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
    ```

    * Setup Cronjob chạy mỗi đêm lúc 2h sáng: `0 2 * * * /path/to/backup.sh`.

2. **Environment Variables**:
    * Đảm bảo `DEBUG=False` trên Prod.
    * Đảm bảo `SECRET_KEY` là chuỗi ngẫu nhiên dài (dùng `openssl rand -hex 32`).

### Step 3.2: Launch

1. **Build Production Image**:

    ```bash
    docker-compose -f docker-compose.yml build --no-cache
    ```

2. **Start Services**:

    ```bash
    docker-compose up -d
    ```

3. **Warmup**:
    * Gọi `/health` vài lần.
    * Chạy script load Index vào RAM.

---

## ✅ Verification Checklist (Phase 4)

1. **Security Scan**:
    * Dùng **OWASP ZAP** (hoặc tool online) scan thử endpoint.
    * Không thấy lộ version Server.

2. **Load Test (Cơ bản)**:
    * Dùng `locust` giả lập 50 user chat cùng lúc.
    * Kiểm tra Grafana: CPU/RAM tăng nhưng không crash; Latency chấp nhận được.

3. **Monitor Alert**:
    * Tắt container DB -> Grafana phải báo đỏ/thiếu data ngay.

👉 **Hoàn thành Phase 4, dự án của bạn đã sẵn sàng Public!**
