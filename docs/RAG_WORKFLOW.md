# 🧠 Advanced RAG Methodology

Tài liệu này mô tả chi tiết quy trình Retrieval-Augmented Generation (RAG) chuyên sâu dành cho Chatbot Tâm lý, tập trung vào độ chính xác và an toàn.

---

## 1. Overview Architecture

### Diagram (PlantUML Style)

```mermaid
graph TD
    subgraph "1. Offline: Indexing Pipeline"
        RawData[PDF/Text/Json] -->|Cleanup & Regex| CleanData[Clean Text]
        CleanData -->|Recursive Splitter| Chunks[Chunks (500-1000 tokens)]
        Chunks -->|Text Embedding 004| Vectors[Embedding Vectors]
        Vectors -->|Upsert| VectorDB[(ChromaDB)]
    end

    subgraph "2. Online: Retrieval Pipeline"
        UserQuery[User Query] -->|Rewrite| RefinedQuery[Refined Query]
        RefinedQuery -->|Hybrid Search| Candidates[Top-10 Candidates]
        
        VectorDB -->|Semantic Search| Candidates
        Keywords[BM25/Keyword] -->|Lexical Search| Candidates
        
        Candidates -->|Cross-Encoder| Reranker[Reranking Model]
        Reranker -->|Top-3 Best| Context
        
        Context -->|Prompt Engineering| Gemini[Gemini 2.0 Generator]
        Gemini -->|Response| FinalAnswer
    end
```

---

## 2. Chi tiết 5 Bước Xử lý (The RAG Pipeline)

### Bước 1: Ingestion & Cleaning (Nạp và Làm sạch)

* **Mục tiêu**: "Garbage In, Garbage Out". Dữ liệu sạch quyết định IQ của Bot.
* **Quy trình**:
    1. **Extract**: Dùng `pypdf` (PyPDF2) để lấy text từ PDF.
    2. **Clean**:
        * Loại bỏ Header/Footer (VD: "Trang 1/100", "NXB Kim Đồng").
        * Chuẩn hóa Unicode tiếng Việt (NFC).
        * Xóa ký tự nhiễu (Regex).

### Bước 2: Chunking (Cắt nhỏ dữ liệu)

* **Chiến thuật**:
  * **Chunk Size**: 1000 characters (không phải tokens).
  * **Chunk Overlap**: 200 characters (để giữ liên kết câu).
  * **Method**: `RecursiveCharacterTextSplitter` (LangChain).
* **Metadata Enrichment**: Gắn nhãn cho mỗi chunk.

    ```json
    {
      "source": "hat_giong_tam_hon.pdf",
      "page": 15,
      "category": "Depression",
      "author": "BS. Nguyen Van A"
    }
    ```

### Bước 3: Embedding (Vector hóa)

* **Model**: Google `text-embedding-004`.
* **Dimension**: 768.
* **Database**: ChromaDB (Persistent Disk).
* **Collection Name**: `psychology_knowledge` (Phase 2 implementation)
* **Health Check**: `/api/v2/heartbeat` (ChromaDB v2 API)
* **Embedding Model**: `text-embedding-004` (Gemini)

### Bước 4.0: Index Warmup (Khởi động nóng)

* **Vấn đề**: Cold Start - Request đầu tiên bị chậm do load model/index.
* **Giải pháp hiện tại (MVP)**:
  * Chỉ init Redis connection khi service start.
  * BM25 index được build lazy (khi có query đầu tiên) với cache 5 phút.

Đây là "bộ lọc kép" để đảm bảo kết quả chính xác nhất.

1. **Hybrid Search (Tìm kiếm lai)**:
    * **Vector Search**: Tìm ý nghĩa (VD: "trống rỗng" ~ "trầm cảm").
    * **Keyword Search**: Tìm từ khóa chính xác (VD: tên thuốc "Fluoxetine").
    * *Kết quả*: Lấy Top-10 candidates.

2. **Reranking (Sắp xếp lại)**:
    * **Hiện tại**: Sử dụng **distance-based filtering** (MVP) - sắp xếp theo khoảng cách vector.
    * **Kế hoạch**: Cross-Encoder hoặc Gemini Flash làm reranker.
    * *Kết quả*: Chọn ra **Top-3** đoạn tốt nhất để đưa vào Prompt.

### Bước 5: Generation (Tạo câu trả lời)

* **System Prompt** (configurable via `PUT /admin/config/sys_prompt`):
  * Role: Chuyên gia tâm lý.
  * Constraint: KHÔNG hallucination, Phải trích dẫn nguồn.
  * Tone: Thấu cảm, nhẹ nhàng.
  * Admin có thể tuỳ chỉnh sys_prompt qua Admin Dashboard.
  * Cache 5 phút để tránh query DB liên tục.
* **Context Injection**:

    ```text
    Dựa vào thông tin sau (kèm nguồn):
    [1] ... (Nguồn: Sách A)
    [2] ... (Nguồn: Sách B)
    
    Hãy trả lời user: "..."
    ```

---

## 3. Technology Stack & Configuration

| Component | Tech / Library | Lý do |
| :--- | :--- | :--- |
| **Pipeline Framework** | **LangChain** | Quản lý Node, Metadata và Indexing pipeline tốt hơn code tay. |
| **Vector DB** | **ChromaDB 0.5.0** | Đơn giản, chạy local, tích hợp tốt với Docker. |
| **Embedding** | **Google Gemini Embeddings** | `text-embedding-004`, 768 dimensions. |
| **LLM** | **Google Gemini 2.0 Flash** | Context window lớn, giá rẻ, performance tốt. |
| **Reranker** | Distance-based (MVP) | Tăng độ chính xác retrieval. Cross-Encoder planned. |

### Model Fallback Mechanism ✅ (Enhanced 2025-12-22)

Để đảm bảo chatbot luôn hoạt động, hệ thống sử dụng model fallback với **memory optimization**:

```python
# src/services/rag_service.py
candidate_models = [
    "gemini-2.0-flash-exp",   # Primary - free tier
    "gemini-flash-latest",    # Fallback 1
    "gemini-1.5-flash",       # Fallback 2
    "gemini-pro"              # Legacy fallback
]

# [P2.2] Prioritize last working model to avoid failed attempts
if _last_working_model and _last_working_model in candidate_models:
    candidate_models.remove(_last_working_model)
    candidate_models.insert(0, _last_working_model)
```

---

## 4. Performance Optimizations ✅ (2025-12-22)

Các cải tiến hiệu suất đã được triển khai:

| Optimization | Location | Improvement |
|--------------|----------|-------------|
| **BM25 Index Caching** | `rag_service.py` | ~200-500ms/query |
| **Query Embedding Reuse** | `rag_query()`, `chat_stream.py` | ~100-300ms/query |
| **Semantic Cache** | `semantic_cache.py` | Skip RAG on cache hit |
| **ChromaDB Connection Pool** | `vector_store.py` | ~50-100ms/query |
| **SOS Keywords Cache** | `safety.py` | ~10-30ms/query |
| **Model Fallback Memory** | `rag_service.py` | 0-30s on failures |
| **Sys Prompt Cache** | `rag_service.py` | 5 min TTL |

### Cache Invalidation

Khi upload/delete document, cần gọi:

```python
rag_service.invalidate_bm25_cache()  # Refresh BM25 index
semantic_cache.clear_all()           # Clear stale responses
```

Điều này được thực hiện tự động trong `knowledge.py` (Admin API).

---

**Last Updated:** 2025-12-25
