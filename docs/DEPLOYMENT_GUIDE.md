# 🚀 Deployment Guide

Hướng dẫn triển khai hệ thống Chatbot lên môi trường Server (Linux/Docker).

## 1. Prerequisites (Yêu cầu)

- **OS**: Ubuntu 22.04 LTS (Recommended).
- **RAM**: Min 4GB.
- **Disk**: Min 20GB.
- **Software**:
  - Docker & Docker Compose plugin.
  - Git.
- **Network**: Open ports 80, 443 (Production) or 8080 (Dev).

## 2. Quick Start (Development)

Chạy nhanh trên máy local hoặc Dev server (HTTP only).

```bash
# 1. Clone repo
git clone https://github.com/your-repo/chatbot.git
cd chatbot

# 2. Setup Env
cp .env.example .env
# Edit .env (GEMINI_API_KEY, POSTGRES_PASSWORD...)

# 3. Start Services
docker-compose up -d --build

# 4. Access
# Frontend: http://localhost:8080
# API Docs: http://localhost:8080/docs
```

---

## 3. Production Deployment (SSL/HTTPS)

**⚠️ Important:** These steps are for production deployment only.

### Prerequisites for SSL

- ✅ Domain name pointing to server IP (e.g., `chat.example.com`).
- ✅ Ports 80 and 443 open.
- ✅ Root/sudo access.

### Step 1: Obtain SSL Certificate

**Using Automated Script (Recommended):**

```bash
# Run the SSL setup script provided in Sprint 3
sudo bash scripts/ssl_setup.sh
```

**What the script does:**

1. Installs certbot.
2. Obtains Let's Encrypt certificate for your domain.
3. Sets up auto-renewal.

### Step 2: Configure Nginx

**Edit `nginx/nginx.conf`:**

1. **Uncomment HTTPS server block** (lines ~32-112).
2. **Update domain name**: Replace `your-domain.com` with actual domain.
3. **Uncomment HTTP redirect block** (lines ~21-28).
4. **Disable Development server block** (lines 117-192).

**Example Config (Snippet):**

```nginx
server {
    listen 443 ssl http2;
    server_name chat.example.com;

    ssl_certificate /etc/letsencrypt/live/chat.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/chat.example.com/privkey.pem;
    
    # ... security headers ...
}
```

### Step 3: Update Docker Compose

**Edit `docker-compose.yml`:**

Uncomment SSL ports and volumes in `nginx` service:

```yaml
services:
  nginx:
    ports:
      - "8080:80"
      - "443:443"        # ← UNCOMMENT
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./static:/usr/share/nginx/html:ro
      - ./ssl:/etc/letsencrypt:ro  # ← UNCOMMENT
```

### Step 4: Copy Certificates

Ensure certificates are accessible to Docker:

```bash
mkdir -p ./ssl
sudo cp -r /etc/letsencrypt/* ./ssl/
```

### Step 5: Restart

```bash
docker-compose down
docker-compose up -d
```

### Verification

- Access `https://chat.example.com` -> Should load securely 🔒.
- Access `http://chat.example.com` -> Should redirect to HTTPS.

---

## 4. Maintenance

### Backup Database

```bash
# Manual Backup
docker-compose exec db pg_dump -U chatbot_user chatbot_db > backup_$(date +%F).sql

# Restore
cat backup.sql | docker-compose exec -T db psql -U chatbot_user chatbot_db
```

### Logs & Monitoring

```bash
# View backend logs
docker-compose logs -f backend

# View access logs
docker-compose logs -f nginx
```

### Troubleshooting SSL

**Issue: "Certificate not found"**

- Check `./ssl` folder permissions.
- Ensure volume mount in `docker-compose.yml` matches.

**Issue: "Connection Refused on 443"**

- Check firewall (`ufw status`).
- Check if another service uses port 443 (`sudo lsof -i :443`).
