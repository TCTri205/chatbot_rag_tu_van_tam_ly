# 💻 Phase 3 Detailed Plan: Client Side & Integration

**Mục tiêu**: Xây dựng giao diện người dùng (UI) đẹp, mượt mà và kết nối với bộ não Backend.

---

## 1. Frontend Setup (HTML/CSS)

### Step 1.1: Project Structure

*Thư mục*: `static/`

1. **Structure**:

    ```bash
    static/
    ├── css/
    │   └── style.css
    ├── js/
    │   ├── api.js
    │   └── app.js
    └── index.html
    ```

### Step 1.2: Base UI (HTML + Tailwind) (Snippet)

*File*: `static/index.html`

```html
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chatbot Tâm Lý</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        .scrollbar-hide::-webkit-scrollbar { display: none; }
    </style>
</head>
<body class="bg-gray-50 h-screen flex overflow-hidden">
    <!-- Sidebar -->
    <aside class="w-64 bg-white border-r hidden md:flex flex-col">
        <div class="p-4 font-bold text-teal-600 text-xl"><i class="fas fa-brain mr-2"></i>TamLy Bot</div>
        <button onclick="newChat()" class="mx-4 mt-2 bg-teal-50 text-teal-700 p-2 rounded-lg hover:bg-teal-100 transition">
            <i class="fas fa-plus mr-2"></i>Cuộc trò chuyện mới
        </button>
        <div class="flex-1 overflow-y-auto p-4 space-y-2" id="history-list">
            <!-- History Items -->
        </div>
    </aside>

    <!-- Main Chat -->
    <main class="flex-1 flex flex-col relative">
        <header class="bg-white border-b p-4 flex justify-between items-center z-10">
            <h1 class="font-semibold text-gray-700">Tư vấn viên AI</h1>
            <div class="text-sm text-gray-500" id="connection-status">Online</div>
        </header>

        <div id="chat-container" class="flex-1 overflow-y-auto p-4 space-y-4 pb-24 scroll-smooth">
            <!-- Messages go here -->
            <div class="flex start">
                <div class="bg-white border p-3 rounded-2xl rounded-tl-none max-w-xl shadow-sm">
                    Xin chào! Mình có thể giúp gì cho bạn hôm nay?
                </div>
            </div>
        </div>

        <!-- Input Area -->
        <div class="absolute bottom-0 w-full bg-white border-t p-4">
            <div class="max-w-4xl mx-auto flex gap-2">
                <textarea id="user-input" rows="1" class="flex-1 border rounded-xl p-3 focus:outline-none focus:border-teal-500 resize-none" placeholder="Hãy chia sẻ câu chuyện của bạn..."></textarea>
                <button onclick="sendMessage()" class="bg-teal-600 text-white p-3 rounded-xl hover:bg-teal-700 w-12 flex items-center justify-center">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
            <div class="text-center text-xs text-gray-400 mt-2">AI có thể mắc lỗi. Hotline SOS: 111</div>
        </div>
    </main>

    <!-- Safety Modal (Hidden by default) -->
    <div id="safety-modal" class="fixed inset-0 bg-black/50 hidden items-center justify-center z-50">
        <div class="bg-white p-6 rounded-xl max-w-sm mx-4 border-l-4 border-red-500">
            <h3 class="text-xl font-bold text-red-600 mb-2"><i class="fas fa-exclamation-triangle"></i> Cảnh báo SOS</h3>
            <p class="text-gray-700 mb-4">Chúng tôi phát hiện tín hiệu nguy hiểm. Vui lòng liên hệ hỗ trợ ngay lập tức:</p>
            <ul class="space-y-2 mb-4 font-semibold">
                <li>📞 111 - Tổng đài BVTE Quốc gia</li>
                <li>📞 115 - Cấp cứu Y tế</li>
            </ul>
            <button onclick="closeSafetyModal()" class="w-full bg-gray-200 p-2 rounded hover:bg-gray-300">Đã hiểu</button>
        </div>
    </div>
</body>
</html>
```

---

## 2. JavaScript Logic (The Glue)

### Step 2.1: API Wrapper (Snippet)

*File*: `static/js/api.js`

```javascript
const API_BASE = '/api/v1';

class API {
    constructor() {
        this.sessionId = sessionStorage.getItem('session_id') || this.initSession();
    }

    initSession() {
        const id = crypto.randomUUID();
        sessionStorage.setItem('session_id', id);
        return id;
    }

    async chatStream(message, onChunk, onDone, onError) {
        try {
            const response = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Session-ID': this.sessionId
                },
                body: JSON.stringify({ content: message })
            });

            if (response.status === 403) {
                const data = await response.json();
                onError({ isCrisis: true, details: data });
                return;
            }

            if (!response.ok) throw new Error('Network error');

            // Handle SSE Streaming
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                // Clean SSE format "data: ... \n\n" if necessary
                onChunk(chunk); 
            }
            onDone();

        } catch (err) {
            onError(err);
        }
    }
}
```

### Step 2.2: App State & Events

*File*: `static/js/app.js`

1. **Init Flow**:
    * Check `localStorage` xem User đã đồng ý Disclaimer chưa? Nếu chưa -> Show Modal.
    * Gọi `/conversations/start` để lấy Welcome Message.

2. **Chat Logic**:
    * `form.onsubmit`:
        1. Hiển thị tin nhắn User ngay (Optimistic UI).
        2. Show "Typing...".
        3. Gọi API Chat.
        4. (Streaming) Append text dần dần vào tin nhắn AI.
        5. Scroll to bottom.

3. **Safety UI**:
    * Nếu API trả về `403 Crisis`:
        * Ẩn khung chat input.
        * Hiển thị danh sách Hotline to rõ.

---

## ✅ Verification Checklist (Phase 3)

1. **Check UI Responsiveness**:
    * Mở DevTools chuyển sang Mobile view (iPhone SE, Pro Max).
    * Layout không bị vỡ, Input box không bị keyboard che (trên Mobile thật).

2. **Integration Test**:
    * Nhập "Hello": Thấy tin nhắn hiện ngay -> Chờ 1-2s thấy Bot trả lời.
    * F5 lại trang: Lịch sử chat cũ không bị mất (do Backend đã lưu và Frontend load lại - *Cần implement logic load history*).

3. **Multi-tab Isolation**:
    * Mở Tab A: Chat "Tôi tên A".
    * Mở Tab B: Chat "Tôi tên B".
    * Quay lại Tab A: Không thấy tin nhắn của Tab B. (Đúng Session Isolation).

👉 **Hoàn thành các bước trên nghĩa là bạn đã XONG Phase 3.**
