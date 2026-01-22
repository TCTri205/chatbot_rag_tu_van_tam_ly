# Kế Hoạch Hoàn Thiện Hệ Thống (Execution Plan)

Dựa trên **Master System Status v3.0**, đây là kế hoạch chi tiết để hoàn thiện toàn bộ các phần còn lại ("Remaining Parts") của hệ thống Chatbot tư vấn tâm lý.

## 🎯 Mục Tiêu

1. **Ngắn hạn (24h)**: Hoàn tất 100% Sprint 3 (Migration & Testing), đảm bảo Code & Database hoàn chỉnh.
2. **Trung hạn (2 Tuần - Sprint 4)**: Hoàn thiện UI Admin, tính năng Data Export.
3. **Ghi chú**: *Bước Deploy Production sẽ được thực hiện sau cùng khi hệ thống hoàn hảo (On Request).*

---

## 📅 Phần A: Hoàn Tất Sprint 3 (Code & Database)

**Mục tiêu:** Giải quyết các vấn đề kỹ thuật để hệ thống chạy đúng Logic 100% trên môi trường Dev/Docker hiện tại.

### 1. Database Migration (Critical)

- **Tình trạng:** Script đã có, chưa chạy.
- **Hành động:**
  - Chạy lệnh SQL thêm cột `metadata` vào bảng `audit_logs`.
  - Verify schema sau khi chạy.
- **Command:**

  ```sql
  ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS metadata JSONB NULL;
  ```

### 2. Manual Testing (Chất lượng)

- **Tình trạng:** Code xong nhưng chưa test tay hoàn chỉnh.
- **Hành động:** Thực hiện quy trình test theo Checklist:
  - [ ] **Admin User Management**: Test API Ban/Unban (dùng Postman/cURL) và kiểm tra database/redis.
  - [ ] **Clear History**: Test nút xóa trên UI, kiểm tra network request và trạng thái UI sau khi xóa.
  - [ ] **Security**: Thử login với user bị ban (Mong đợi: 403 Forbidden).

---

## 📅 Phần B: Sprint 4 - Admin UI & Features (Kế hoạch tiếp theo)

**Mục tiêu:** Xây dựng các tính năng còn thiếu ("Future Work") để tăng trải nghiệm UX.

### Phase 1: Admin Dashboard Frontend (Ưu tiên cao)

Hiện tại Admin chỉ có API, chưa có giao diện quản lý user thuận tiện.

- **Task 1.1: User List Table**
  - Tạo bảng hiển thị danh sách người dùng trong `admin.html`.
  - Các cột: Avatar, Username, Email, Role, Status (Active/Banned), Actions.
  - Tích hợp Pagination API.

- **Task 1.2: User Actions UI**
  - Thêm nút "Ban" (biểu tượng cấm) và "Unban" (biểu tượng check).
  - Thêm Modal xác nhận khi Ban (yêu cầu nhập lý do -> lưu vào metadata).
  - Thêm bộ lọc (Filter): Show Active/Banned, Search by Email.

### Phase 2: Privacy Features (Data Export)

Đáp ứng quyền riêng tư của người dùng.

- **Task 2.1: Chat History Export API**
  - Endpoint `GET /api/v1/conversations/{id}/export`.
  - Format: JSON hoặc PDF đơn giản.
  
- **Task 2.2: Export UI**
  - Thêm nút "Tải về" trong menu chat.

### Phase 3: Performance & Monitoring (Optional)

Chuẩn bị nền tảng tối ưu.

- **Task 3.1: Frontend Optimization**
  - Minify JS/CSS assets.

- **Task 3.2: Monitoring Setup**
  - Cấu hình Prometheus + Grafana dashboard (cơ bản) để theo dõi lỗi trong quá trình Dev.

---

## 📋 Lịch Trình Thực Hiện Dự Kiến

| Thời gian | Hạng mục | Chi tiết |
| :--- | :--- | :--- |
| **Ngày 17/12 (Hôm nay)** | **Phần A (Sprint 3 Closure)** | **1. DB Migration<br>2. Verify Manual Tests** |
| **Tuần 11** | **Phần B - Feature** | 1. Implement Admin User List UI<br>2. Implement Ban/Unban Actions UX |
| **Tuần 12** | **Phần B - Optimize** | 1. Data Export Feature<br>2. System Hardening |

---

## 🚦 Đề Xuất Hành Động Ngay (Next Step Action)

**Bạn có muốn tôi thực hiện các bước sau không?**

1. **Thực thi Database Migration** (thêm cột `metadata`).
2. **Verify nhanh** các API.
3. **Tạo ticket** cho Admin Frontend UI.
