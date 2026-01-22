# 🕵️ Phase 1 Verification Plan: Foundation & Security

Tài liệu này dùng để **kiểm tra nghiêm ngặt (Audit)** toàn bộ kết quả của Giai đoạn 1. Mục tiêu là đảm bảo "Móng nhà" không chỉ chạy được mà còn phải **An toàn** và **Chuẩn chỉ**.

---

## 1. Infrastructure Audit (Kiểm tra Hạ tầng)

### 1.1 Container Status

- [ ] **Lệnh**: `docker-compose ps`
- [ ] **Expected**:
  - `nginx`: Up (Ports 80->80)
  - `backend`: Up (Ports 8000)
  - `db`: Up (Ports 5432)
  - `redis`: Up (Ports 6379)
  - `chroma`: Up (Ports 8001->8000)
- [ ] **Check Logs**:
  - `docker-compose logs backend`: Không có Error/Traceback khi khởi động.
  - `docker-compose logs db`: "database system is ready to accept connections".

### 1.2 Network isolation

- [ ] **Test**: Từ máy host, thử kết nối trực tiếp vào `backend:8000` (nếu docker ko map port này ra ngoài thì tốt).
- [ ] **Check Config**: File `.env` chứa mật khẩu mạnh (không dùng default "password").

---

## 2. API & Security Tests (Kiểm tra Bảo mật)

### 2.1 Health Check

- [ ] **Request**: `GET http://localhost/api/health`
- [ ] **Response**: `200 OK`
- [ ] **Body**: `{"status": "ok", "db": "connected", ...}`

### 2.2 Input Validation (Quan trọng!)

- [ ] **Test Case 1: Email sai format**
  - Req: `POST /api/v1/auth/register` | Body: `{"email": "bad-email", "password": "123"}`
  - Resp: `422 Unprocessable Entity` (Do Pydantic chặn).
- [ ] **Test Case 2: Mật khẩu quá ngắn**
  - Req: Body `{"password": "123"}`
  - Resp: `422` (Msg: "ensure this value has at least 8 characters").
- [ ] **Test Case 3: SQL Injection Sim**
  - Req: Body `{"email": "' OR 1=1 --"}`
  - Resp: `422` hoặc Login Fail (Tuyệt đối không chạy được query).

### 2.3 Rate Limiting

- [ ] **Test**: Spam liên tục 20 request trong 1 giây vào `/api/health`.
- [ ] **Expected**: Các request sau đó bị Nginx trả về `503 Service Temporarily Unavailable` hoặc `429 Too Many Requests`.

---

## 3. Database Integrity

### 3.1 Migration Check

- [ ] **Lệnh**: Vào container `docker-compose exec backend alembic current`.
- [ ] **Expected**: Hiển thị ID của revision mới nhất (head).
- [ ] **Manual Check**: Dùng tool DB truy cập bảng `users`, `conversations` xem cột có đúng type không.

---

## 4. Conflict & Error Handling

- [ ] **Port Conflict**: Đảm bảo máy Host không chạy IIS/Apache chiếm port 80.
- [ ] **Environment**: Kiểm tra biến `DEBUG=True` đang bật (cho Dev) nhưng `SECRET_KEY` phải được load từ file `.env` chứ không phải hardcode.

👉 **Nếu tất cả các mục trên đều tích xanh (Pass), Phase 1 được coi là HOÀN HẢO.**
