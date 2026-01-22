# 🧠 Phase 2 Detailed Plan: RAG Engine & Core Logic

**Status**: ✅ **COMPLETED** (December 15, 2024)

**Mục tiêu**: Xây dựng "Bộ não" cho chatbot. Sau giai đoạn này, bot có thể hiểu câu hỏi, tìm kiếm kiến thức trong PDF và trả lời thấu cảm.

**Achievements**:

- ✅ ChromaDB integration với v2 API
- ✅ RAG pipeline với source citations
- ✅ Session management (Redis + PostgreSQL)
- ✅ Crisis detection system
- ✅ Guest conversation support
- ✅ Database timing optimization (pg_isready)
- ✅ System settings seeding via migration

---

## 1. RAG Core Services

### Step 1.1: ChromaDB Setup

*Mục đích*: Nơi lưu trữ vector kiến thức.

1. **Cập nhật `docker-compose.yml`** (Nếu chưa):
    - Image: `chromadb/chroma:0.5.5` (0.5.4+ fixes NumPy 2.0 compatibility, backward compatible with 0.4.22 client).
    - Volume: `./chroma_data:/chroma/chroma`.
    - Port: `8000` (Map ra 8001 để tránh đụng backend).

2. **`src/core/vector_store.py`** (Code Snippet):

    ```python
    import chromadb
    from src.config import settings

    def get_chroma_client():
        # Kết nối tới Chroma container qua Docker Network
        return chromadb.HttpClient(
            host=settings.CHROMA_HOST,  # "chroma"
            port=settings.CHROMA_PORT   # 8000
        )

    def get_collection():
        client = get_chroma_client()
        return client.get_or_create_collection("psychology_knowledge")
    ```

### Step 1.2: RAG Pipeline Implementation

*File*: `src/services/rag_service.py`

1. **Chức năng Chunking & Embedding**:
    - Sử dụng `RecursiveCharacterTextSplitter` (chunk_size=1000, overlap=200).
    - Sử dụng `google-generativeai` để embedding (`text-embedding-004`).

2. **Chức năng Hybrid Search** (Key feature):
    - Query ChromaDB lấy Top-10 semantic results.
    - Sử dụng `rank_bm25` (in-memory) hoặc Chroma metadata filtering để tăng độ chính xác từ khóa.

3. **Chức năng Reranking**:
    - Sử dụng `CrossEncoder` (nhẹ) hoặc gọi lại Gemini Flash chấm điểm Top-10 -> Lấy Top-3.

### Step 1.3: Ingestion Script

*File*: `src/scripts/ingest.py`

### Step 1.3: Ingestion Script (Snippet)

*File*: `src/scripts/ingest.py`

```python
import os
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.core.vector_store import get_collection
from src.config import settings
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=settings.GOOGLE_API_KEY)

def ingest_docs():
    collection = get_collection()
    data_dir = "./data"
    
    for filename in os.listdir(data_dir):
        if not filename.endswith(".pdf"): continue
        
        # 1. Read PDF
        print(f"Processing {filename}...")
        reader = PdfReader(os.path.join(data_dir, filename))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
        # 2. Chunking
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = splitter.split_text(text)
        
        # 3. Embedding & Upsert
        # Note: Thực tế nên batching để tiết kiệm API
        ids = [f"{filename}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": filename, "page": 0} for _ in chunks]
        
        # Gọi Gemini Embeddings (giả lập function wrapper)
        embeddings = [
            genai.embed_content(
                model="models/text-embedding-004",
                content=chunk,
                task_type="retrieval_document"
            )['embedding'] 
            for chunk in chunks
        ]
        
        collection.upsert(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas
        )
        print(f"Upserted {len(chunks)} chunks.")

if __name__ == "__main__":
    ingest_docs()
```

1. **Chạy thử**:

    ```bash
    docker-compose exec backend python -m src.scripts.ingest
    ```

---

## 2. API Implementation (Business Logic)

### Step 2.1: Chat API

*File*: `src/api/v1/chat.py`

1. **Endpoint**: `POST /chat`.
2. **Tasks**:
    - Verify Session ID (from Redis).
    - **Safety Check**: Regex keyword "tự tử", "chết", "tự hại". Nếu có -> Trả về Crisis Response (403).
    - **Context Retrieval**: Gọi RAG Service lấy Top-3 chunks.
    - **Generate**: Gọi Gemini API với System Prompt + Context.
    - **Save DB**: Lưu User Message & Bot Response vào DB (async).

3. **System Prompt Mẫu** (Quan trọng!):

    ```text
    Bạn là một chuyên gia tư vấn tâm lý AI nhân ái, thấu cảm và chuyên nghiệp.
    Nhiệm vụ: Sử dụng thông tin trong [CONTEXT] để trả lời câu hỏi của người dùng.

    Quy tắc bắt buộc:
    1. Luôn lắng nghe và xác nhận cảm xúc trước khi đưa lời khuyên.
    2. Chỉ trả lời dựa trên kiến thức tâm lý học và context được cung cấp.
    3. KHÔNG phán xét, đổ lỗi hoặc bịa đặt thông tin.
    4. Trích dẫn nguồn nếu có (VD: "Theo sách X, trang Y...").
    5. Trả lời bằng tiếng Việt tự nhiên, ấm áp.
    ```

### Step 2.2: Mood API

*File*: `src/api/v1/mood.py`

1. **Endpoint**: `POST /moods`.
    - Insert vào bảng `mood_entries`.
2. **Endpoint**: `GET /moods/history`.
    - Query Aggregate: `SELECT AVG(mood_value), DATE(created_at) GROUP BY DATE(created_at)`.

---

## ✅ Verification Checklist (Phase 2)

**Automated Scripts** (Recommended):

1. **Quick Start**:

   ```bash
   scripts\phase2\quick_start_phase2.bat
   ```

   Xây dựng, khởi động, và verify toàn bộ hệ thống.

2. **Verification**:

   ```bash
   scripts\phase2\verify_phase2.bat
   ```

   Kiểm tra: Docker containers, Database health, ChromaDB, System Settings.

3. **API Testing**:

   ```bash
   scripts\phase2\test_phase2_apis.bat
   ```

   Test: Session init, Crisis detection, Normal chat, Chat history.

**Manual Tests** (Optional):

1. **Test ChromaDB v2 API**:

    ```bash
    curl http://localhost:8001/api/v2/heartbeat
    # Expected: Timestamp (e.g., 1734234567890123456)
    ```

2. **Test Session Init**:

    ```bash
    curl -X POST http://localhost:8080/api/v1/sessions/init \
      -H "Content-Type: application/json" \
      -d '{}'
    # Expected: {session_id, conversation_id, greeting, created_at}
    ```

3. **Test Crisis Detection**:

    ```bash
    curl -X POST http://localhost:8080/api/v1/chat \
      -H "Content-Type: application/json" \
      -H "X-Session-ID: <your_session_id>" \
      -d '{"content": "tôi muốn chết"}'
    # Expected: {is_crisis: true, message: ..., hotlines: [...]}
    ```

4. **Test RAG Chat**:

    ```bash
    curl -X POST http://localhost:8080/api/v1/chat \
      -H "Content-Type: application/json" \
      -H "X-Session-ID: <your_session_id>" \
      -d '{"content": "làm sao để bớt lo âu?"}'
    # Expected: {message_id, role: "assistant", content: ..., sources: [], is_crisis: false}
    ```

5. **Verify Database**:

    ```bash
    # Check system_settings seeded
    docker-compose exec db psql -U chatbot_user -d chatbot_db -c "SELECT key FROM system_settings;"
    
    # Check guest conversation (user_id nullable)
    docker-compose exec db psql -U chatbot_user -d chatbot_db -c "SELECT id, user_id FROM conversations LIMIT 5;"
    ```

👉 **Phase 2 COMPLETED khi tất cả tests trên PASS.**
