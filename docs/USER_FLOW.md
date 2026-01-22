# 🔄 User Flow Diagram

Mô tả luồng trải nghiệm người dùng (User Journey) chuẩn cho Chatbot Tâm lý.

> [!NOTE]
> **Hệ thống Phân quyền (RBAC)**: Hỗ trợ 4 cấp độ - 👥 Guest, 👤 User, 👨‍💼 Admin, 👑 Super Admin
>
> **Chi tiết đầy đủ**: [AUTHORIZATION_GUIDE.md](./AUTHORIZATION_GUIDE.md) - Ma trận phân quyền và luồng xác thực

```mermaid
flowchart TD
    Start((Start)) --> AuthCheck{Logged In?}
    
    AuthCheck -- No --> Disclaimer{Disclaimer}
    AuthCheck -- Yes --> RoleCheck{Role?}
    
    RoleCheck -- 👤 User --> Disclaimer
    RoleCheck -- 👨‍💼 Admin/Super Admin --> AdminDash[Admin Dashboard]
    
    subgraph "Admin Management"
        AdminDash --> ViewStats[View Statistics]
        AdminDash --> ManageUsers[Manage Users - Ban/Unban]
        AdminDash --> ViewLogs[Audit Logs]
        AdminDash --> SystemConfig[System Configuration]
    end

    Disclaimer -- "Không đồng ý" --> Exit[Thoát ứng dụng]
    Disclaimer -- "Đồng ý" --> MoodCheck[Mood Check-in]
    
    MoodCheck -->|User chọn Mood| SaveMood[Lưu Mood vào DB]
    SaveMood --> MainChat[Giao diện Chat Chính]
    
    subgraph Conversation Loop
        MainChat -->|User nhập liệu| InputCheck{Kiểm tra nội dung}
        
        InputCheck -- "SOS Keywords" --> CrisisAlert[🚨 CẢNH BÁO SOS]
        CrisisAlert --> ShowHotlines[Hiện Hotline & Bệnh viện]
        ShowHotlines --> StopChat((Dừng Chat))
        
        InputCheck -- "Từ khóa cấm" --> BlockMsg[Chặn tin nhắn & Cảnh báo]
        BlockMsg --> MainChat
        
        InputCheck -- "Hợp lệ" --> RAGProcess[RAG Processing]
        RAGProcess -->|Success| BotResponse[Bot trả lời]
        RAGProcess -->|API Error| ErrorHandler[Hiện thông báo lỗi]
        ErrorHandler --> MainChat
        
        BotResponse --> Feedback{User Feedback?}
        Feedback -->|Like/Dislike| LogFeedback[Lưu Feedback]
        LogFeedback --> MainChat
    end

    subgraph Tools & Utilities
        MainChat -- "Chọn chức năng" --> ToolSelection
        ToolSelection -- "Thư giãn" --> RelaxEx[Bài tập thở/Thiền]
        ToolSelection -- "Nhật ký" --> MoodHistory[Xem biểu đồ Mood]
        RelaxEx --> MainChat
        MoodHistory --> MainChat
    end
```

## Giải thích chi tiết các bước

1. **Onboarding (Start -> MainChat)**:
    * Người dùng mở app.
    * **Bắt buộc**: Phải xem và đồng ý với Tuyên bố miễn trách nhiệm (Disclaimer).
    * **Start**: Vào giao diện Chat chính, nhận lời chào từ Bot (Mood Check-in được tích hợp tùy chọn).

2. **Safety Loop (SOS Check)**:
    * Mọi tin nhắn user gửi (`InputCheck`) đều phải đi qua bộ lọc An toàn trước tiên.
    * Nếu phát hiện từ khóa nguy hiểm -> **Ngắt ngay lập tức**, chuyển sang màn hình Cấp cứu (CrisisAlert).

3. **Conversation RAG Loop**:
    * Nếu an toàn, tin nhắn đi qua RAG Pipeline.
    * Bot trả lời kèm empathy (thấu cảm) và citation (trích dẫn).
    * User có thể đánh giá câu trả lời.

4. **Utility Navigation**:
    * Từ màn hình chính, user có thể rẽ nhánh sang các công cụ hỗ trợ (Bài tập, Lịch sử) mà không cần chat liên tục.
