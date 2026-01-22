"""
RAG (Retrieval-Augmented Generation) Service.
Implements the complete RAG pipeline: chunking, embedding, hybrid search (BM25+Vector), reranking, and generation.

Performance optimizations applied:
- P0: BM25 index caching with TTL
- P1: Query embedding reuse (avoid duplicate API calls)
- P2: Model fallback memory (prioritize last working model)
"""
import logging
import time
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING

# Type checking import to avoid circular import
if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
from dataclasses import dataclass
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi

from src.config import settings
from src.core.vector_store import get_collection, VectorStoreError

logger = logging.getLogger(__name__)

# [P2] Module-level cache for last working model
_last_working_model: Optional[str] = None

# [P3] sys_prompt cache for runtime configuration loading
_sys_prompt_cache: Optional[str] = None
_sys_prompt_cache_time: Optional[float] = None
_SYS_PROMPT_CACHE_TTL: int = 300  # 5 minutes TTL

# Configure Gemini API
genai.configure(api_key=settings.GOOGLE_API_KEY)


async def load_sys_prompt(db) -> Optional[str]:
    """
    Load custom system prompt from database SystemSettings.
    Uses caching to avoid DB query on every request.
    
    Args:
        db: Database session (AsyncSession)
        
    Returns:
        Custom system prompt if configured, None otherwise (uses default)
    """
    global _sys_prompt_cache, _sys_prompt_cache_time
    
    current_time = time.time()
    
    # Check cache validity
    if (_sys_prompt_cache is not None and
        _sys_prompt_cache_time is not None and
        current_time - _sys_prompt_cache_time < _SYS_PROMPT_CACHE_TTL):
        return _sys_prompt_cache
    
    try:
        from sqlalchemy import select
        from src.models.audit import SystemSetting
        
        result = await db.execute(
            select(SystemSetting).where(SystemSetting.key == "sys_prompt")
        )
        setting = result.scalar_one_or_none()
        
        if setting and setting.value:
            _sys_prompt_cache = setting.value
            _sys_prompt_cache_time = current_time
            logging.info("Loaded custom sys_prompt from database")
            return setting.value
        
        # No custom prompt, return None (caller uses default)
        _sys_prompt_cache_time = current_time  # Cache the "not found" result too
        return None
        
    except Exception as e:
        logging.error(f"Failed to load sys_prompt from database: {str(e)}")
        return None


@dataclass
class SearchResult:
    """RAG search result container."""
    content: str
    source: str
    page: int
    distance: float
    score: Optional[float] = None  # Reranking score


class RAGService:
    """RAG Service for knowledge retrieval and response generation."""
    
    def __init__(self):
        """Initialize RAG service with configuration."""
        self.embedding_model = "models/text-embedding-004"
        self.generation_model = "gemini-2.0-flash"
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # [P0] BM25 index caching attributes
        self._bm25_cache: Optional[BM25Okapi] = None
        self._bm25_cache_time: Optional[float] = None
        self._bm25_cache_ttl: int = 300  # 5 minutes TTL
        self._corpus_cache: Optional[List[str]] = None
        self._corpus_metadatas: Optional[List[Dict]] = None
        
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks for embedding.
        
        Args:
            text: Raw text to chunk
            
        Returns:
            List of text chunks
        """
        try:
            chunks = self.text_splitter.split_text(text)
            logger.info(f"Split text into {len(chunks)} chunks")
            return chunks
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            raise
    
    def generate_embedding(self, text: str, task_type: str = "retrieval_query") -> List[float]:
        """
        Generate embedding vector using Gemini.
        
        Args:
            text: Text to embed
            task_type: "retrieval_query" or "retrieval_document"
            
        Returns:
            Embedding vector (768 dimensions)
        """
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type=task_type
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def _get_bm25_index(
        self,
        collection,
        filter_metadata: Optional[Dict] = None
    ) -> Tuple[Optional[BM25Okapi], List[str], List[Dict]]:
        """
        [P0] Get or create cached BM25 index.
        
        Returns:
            Tuple of (bm25_index, documents, metadatas)
        """
        current_time = time.time()
        
        # Check cache validity
        if (self._bm25_cache is not None and
            self._bm25_cache_time is not None and
            current_time - self._bm25_cache_time < self._bm25_cache_ttl):
            logger.debug("[P0] Using cached BM25 index")
            return self._bm25_cache, self._corpus_cache or [], self._corpus_metadatas or []
        
        # Cache miss or expired - rebuild
        logger.info("[P0] Rebuilding BM25 index (cache miss or expired)")
        all_results = collection.get(
            where=filter_metadata,
            include=["documents", "metadatas"]
        )
        
        if not all_results['documents'] or len(all_results['documents']) == 0:
            return None, [], []
        
        documents = all_results['documents']
        metadatas = all_results['metadatas']
        
        # Build BM25 index
        tokenized_corpus = [doc.lower().split() for doc in documents]
        bm25 = BM25Okapi(tokenized_corpus)
        
        # Cache the result
        self._bm25_cache = bm25
        self._corpus_cache = documents
        self._corpus_metadatas = metadatas
        self._bm25_cache_time = current_time
        
        logger.info(f"[P0] BM25 index built with {len(documents)} documents")
        return bm25, documents, metadatas
    
    def invalidate_bm25_cache(self):
        """Invalidate BM25 cache (call when documents are added/removed)."""
        self._bm25_cache = None
        self._bm25_cache_time = None
        self._corpus_cache = None
        self._corpus_metadatas = None
        logger.info("[P0] BM25 cache invalidated")
    
    def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        filter_metadata: Optional[Dict] = None,
        alpha: float = 0.5,  # Weight: 0=pure BM25, 1=pure vector
        query_embedding: Optional[List[float]] = None  # [P1] Reuse embedding
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining BM25 (keyword) and vector (semantic) search.
        
        Args:
            query: User query
            top_k: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {"category": "Depression"})
            alpha: Weighting factor (0-1). Higher values favor vector search.
            
        Returns:
            List of SearchResult objects sorted by combined score
        """
        try:
            # Get collection
            collection = get_collection()
            
            # [P0] Get cached BM25 index instead of rebuilding every time
            bm25, documents, metadatas = self._get_bm25_index(collection, filter_metadata)
            
            if bm25 is None or not documents:
                logger.warning("No documents found in vector store")
                return []
            
            # 1. BM25 Keyword Search
            # Tokenize query
            tokenized_query = query.lower().split()
            
            # Get BM25 scores for all documents
            bm25_scores = bm25.get_scores(tokenized_query)
            
            # Normalize BM25 scores to 0-1 range
            max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1
            bm25_scores_norm = [score / max_bm25 for score in bm25_scores]
            
            # 2. Vector Semantic Search
            # [P1] Reuse query embedding if provided, otherwise generate
            if query_embedding is None:
                query_embedding = self.generate_embedding(query, task_type="retrieval_query")
            
            vector_results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k * 2, len(documents)),  # Get more candidates
                where=filter_metadata,
                include=["documents", "metadatas", "distances"]
            )
            
            # Create lookup dict for vector distances
            vector_distance_map = {}
            if vector_results['documents'] and len(vector_results['documents']) > 0:
                for i, doc in enumerate(vector_results['documents'][0]):
                    distance = vector_results['distances'][0][i]
                    # Convert distance to similarity (0=far, 1=close)
                    # Assuming cosine distance: 0=identical, 2=opposite
                    similarity = 1 - (distance / 2)
                    vector_distance_map[doc] = similarity
            
            # 3. Combine scores with alpha weighting
            combined_results = []
            for i, doc in enumerate(documents):
                metadata = metadatas[i] if metadatas else {}
                
                # Get scores
                bm25_score = bm25_scores_norm[i]
                vector_score = vector_distance_map.get(doc, 0)
                
                # Hybrid score: alpha * vector + (1-alpha) * BM25
                hybrid_score = alpha * vector_score + (1 - alpha) * bm25_score
                
                combined_results.append(SearchResult(
                    content=doc,
                    source=metadata.get('source', 'Unknown'),
                    page=metadata.get('page', 0),
                    distance=1 - hybrid_score,  # Convert back to distance for consistency
                    score=hybrid_score  # Store combined score
                ))
            
            # Sort by hybrid score (descending) and take top_k
            combined_results.sort(key=lambda x: x.score if x.score else 0, reverse=True)
            top_results = combined_results[:top_k]
            
            logger.info(f"Hybrid search (alpha={alpha}) returned {len(top_results)} results")
            return top_results
            
        except VectorStoreError as e:
            logger.error(f"Vector store error during hybrid search: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error during hybrid search: {str(e)}")
            return []
    
    def rerank_results(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int = 3
    ) -> List[SearchResult]:
        """
        Rerank search results using Gemini for better relevance.
        
        Args:
            query: Original user query
            results: Initial search results
            top_k: Number of top results to return
            
        Returns:
            Reranked and filtered results
        """
        try:
            if not results:
                return []
            
            # For MVP, use simple distance-based filtering
            # TODO: Implement CrossEncoder or Gemini-based reranking
            sorted_results = sorted(results, key=lambda x: x.distance)[:top_k]
            
            logger.info(f"Reranked to top {len(sorted_results)} results")
            return sorted_results
            
        except Exception as e:
            logger.error(f"Error during reranking: {str(e)}")
            return results[:top_k]  # Fallback to original order
    
    def build_context(self, results: List[SearchResult]) -> Tuple[str, List[Dict]]:
        """
        Build context string and sources list for prompt.
        
        Args:
            results: Search results
            
        Returns:
            Tuple of (context_string, sources_list)
        """
        if not results:
            return "", []
        
        context_parts = []
        sources = []
        
        for i, result in enumerate(results, 1):
            context_parts.append(f"[{i}] {result.content}\n(Nguồn: {result.source}, trang {result.page})")
            sources.append({
                "title": result.source,
                "page": result.page,
                "content_snippet": result.content[:200] + "..." if len(result.content) > 200 else result.content
            })
        
        context = "\n\n".join(context_parts)
        return context, sources
    
    async def generate_response(
        self,
        query: str,
        context: str,
        chat_history: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate response using Gemini with RAG context.
        
        Args:
            query: User query
            context: Retrieved knowledge context
            chat_history: Previous conversation messages
            system_prompt: Optional custom system prompt
            
        Returns:
            Generated response text
        """
        try:
            # Default system prompt with citation emphasis
            if system_prompt is None:
                system_prompt = """Bạn là một chuyên gia tư vấn tâm lý AI nhân ái, thấu cảm và chuyên nghiệp.

Nhiệm vụ của bạn:
1. Sử dụng thông tin trong [CONTEXT] để trả lời câu hỏi của người dùng.
2. Luôn lắng nghe và xác nhận cảm xúc trước khi đưa lời khuyên.
3. Chỉ trả lời dựa trên kiến thức tâm lý học và context được cung cấp.
4. KHÔNG bịa đặt thông tin không có trong context.

**QUAN TRỌNG - Cách trích dẫn nguồn:**
- Khi sử dụng thông tin từ context, BẮT BUỘC trích dẫn nguồn theo format: "Theo [Tên nguồn], trang X..."
- Ví dụ: "Theo Sổ tay Sơ cứu Tâm lý, trang 45, kỹ thuật thở sâu giúp giảm lo âu..."
- Nếu nguồn không có trang cụ thể, dùng: "Theo [Tên nguồn]..."
- LUÔN trích dẫn ít nhất 1 nguồn khi có thông tin từ context.

6. Trả lời bằng tiếng Việt tự nhiên, ấm áp và dễ hiểu.
7. Nếu không có đủ thông tin trong context, hãy thừa nhận và đề xuất người dùng tìm kiếm chuyên gia.
8. KHÔNG sử dụng HTML tags (như <blockquote>, <p>, <br>, v.v.). Chỉ dùng plain text.

Giọng điệu: Thấu cảm, nhẹ nhàng, không phán xét."""
            
            # Build prompt with context
            prompt = f"""{system_prompt}

[CONTEXT - Thông tin tham khảo]
{context}

[LỊCH SỬ HỘI THOẠI]
"""
            if chat_history:
                for msg in chat_history[-5:]:  # Last 5 messages for context
                    role = "Người dùng" if msg.get("role") == "user" else "Trợ lý"
                    prompt += f"{role}: {msg.get('content', '')}\n"
            
            prompt += f"\n[CÂU HỎI HIỆN TẠI]\nNgười dùng: {query}\n\nTrợ lý:"
            
            # [P2] Define model priority list for fallback
            global _last_working_model
            candidate_models = [
                "gemini-2.0-flash-exp",   # Try experimental first (often free/smart)
                "gemini-flash-latest",    # Stable fallback
                "gemini-1.5-flash",       # Old reliable
                "gemini-pro"              # Legacy
            ]
            
            # [P2] Prioritize last working model to avoid failed attempts
            if _last_working_model and _last_working_model in candidate_models:
                candidate_models.remove(_last_working_model)
                candidate_models.insert(0, _last_working_model)
                logger.debug(f"[P2] Prioritizing last working model: {_last_working_model}")

            last_error = None
            
            for model_name in candidate_models:
                try:
                    logger.info(f"Attempting to generate with model: {model_name}")
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(
                        prompt,
                        generation_config={
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "top_k": 40,
                            "max_output_tokens": 2048,
                        }
                    )
                    
                    generated_text = response.text
                    
                    # Sanitize: Remove ALL HTML-like tags that Gemini might add
                    import re
                    # Pattern 1: Match standard HTML tags (opening, closing, self-closing)
                    generated_text = re.sub(r'</?[a-zA-Z][a-zA-Z0-9]*[^>]*/?>', '', generated_text)
                    # Pattern 2: Catch malformed/incomplete tags like </blockquote> appearing separately
                    generated_text = re.sub(r'</?\s*\w+\s*>', '', generated_text)
                    generated_text = generated_text.strip()
                    
                    _last_working_model = model_name  # [P2] Remember successful model
                    logger.info(f"✅ Generated response with {model_name}: {len(generated_text)} characters")
                    return generated_text
                    
                except Exception as e:
                    logger.warning(f"⚠️ Model {model_name} failed: {str(e)}")
                    last_error = e
                    continue
            
            # If all models fail
            logger.error(f"❌ All models failed. Last error: {str(last_error)}", exc_info=True)
            return "Xin lỗi, tôi gặp sự cố khi xử lý câu hỏi của bạn. Vui lòng thử lại sau."
            
        except Exception as e:
            logger.error(f"Error in generate_response: {str(e)}", exc_info=True)
            return "Xin lỗi, tôi gặp sự cố khi xử lý câu hỏi của bạn. Vui lòng thử lại sau."
    
    async def generate_response_stream(
        self,
        query: str,
        context: str,
        chat_history: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None
    ):
        """
        Generate streaming response using Gemini with RAG context.
        Yields response chunks for Server-Sent Events.
        
        Args:
            query: User query
            context: Retrieved knowledge context
            chat_history: Previous conversation messages
            system_prompt: Optional custom system prompt
            
        Yields:
            Response text chunks as they are generated
        """
        try:
            # Default system prompt with citation emphasis (same as generate_response)
            if system_prompt is None:
                system_prompt = """Bạn là một chuyên gia tư vấn tâm lý AI nhân ái, thấu cảm và chuyên nghiệp.

Nhiệm vụ của bạn:
1. Sử dụng thông tin trong [CONTEXT] để trả lời câu hỏi của người dùng.
2. Luôn lắng nghe và xác nhận cảm xúc trước khi đưa lời khuyên.
3. Chỉ trả lời dựa trên kiến thức tâm lý học và context được cung cấp.
4. KHÔNG bịa đặt thông tin không có trong context.

**QUAN TRỌNG - Cách trích dẫn nguồn:**
- Khi sử dụng thông tin từ context, BẮT BUỘC trích dẫn nguồn theo format: "Theo [Tên nguồn], trang X..."
- Ví dụ: "Theo Sổ tay Sơ cứu Tâm lý, trang 45, kỹ thuật thở sâu giúp giảm lo âu..."
- Nếu nguồn không có trang cụ thể, dùng: "Theo [Tên nguồn]..."
- LUÔN trích dẫn ít nhất 1 nguồn khi có thông tin từ context.

6. Trả lời bằng tiếng Việt tự nhiên, ấm áp và dễ hiểu.
7. Nếu không có đủ thông tin trong context, hãy thừa nhận và đề xuất người dùng tìm kiếm chuyên gia.
8. KHÔNG sử dụng HTML tags (như <blockquote>, <p>, <br>, v.v.). Chỉ dùng plain text.

Giọng điệu: Thấu cảm, nhẹ nhàng, không phán xét."""
            
            # Build prompt with context
            prompt = f"""{system_prompt}

[CONTEXT - Thông tin tham khảo]
{context}

[LỊCH SỬ HỘI THOẠI]
"""
            if chat_history:
                for msg in chat_history[-5:]:  # Last 5 messages for context
                    role = "Người dùng" if msg.get("role") == "user" else "Trợ lý"
                    prompt += f"{role}: {msg.get('content', '')}\n"
            
            prompt += f"\n[CÂU HỎI HIỆN TẠI]\nNgười dùng: {query}\n\nTrợ lý:"
            
            # Define model priority list for fallback
            candidate_models = [
                "gemini-2.0-flash-exp",
                "gemini-flash-latest",
                "gemini-1.5-flash"
            ]

            last_error = None
            response_iterator = None
            
            # Try models until one works
            for model_name in candidate_models:
                try:
                    logger.info(f"Stream: Attempting model {model_name}")
                    model = genai.GenerativeModel(model_name)
                    response_iterator = model.generate_content(
                        prompt,
                        generation_config={
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "top_k": 40,
                            "max_output_tokens": 2048,
                        },
                        stream=True  # Enable streaming
                    )
                    # Check if iterator is valid by peeking or it will fail in loop
                    # Actually for stream=True, api call happens here. 
                    # If 404/429, it raises here.
                    logger.info(f"Stream: Connection established with {model_name}")
                    break
                except Exception as e:
                    logger.warning(f"Stream: Model {model_name} failed: {str(e)}")
                    last_error = e
                    continue

            if not response_iterator:
                logger.error(f"❌ Stream: All models failed. Last error: {str(last_error)}", exc_info=True)
                yield "Xin lỗi, tôi gặp sự cố khi xử lý câu hỏi của bạn. Vui lòng thử lại sau."
                return

            # Stream response chunks
            full_response = ""
            for chunk in response_iterator:
                if chunk.text:
                    full_response += chunk.text
                    yield chunk.text
            
            logger.info(f"Streamed response: {len(full_response)} characters total")
            
        except Exception as e:
            logger.error(f"Error generating streaming response: {str(e)}", exc_info=True)
            yield "Xin lỗi, tôi gặp sự cố khi xử lý câu hỏi của bạn. Vui lòng thử lại sau."
    
    async def rag_query(
        self,
        query: str,
        chat_history: Optional[List[Dict]] = None,
        top_k: int = 3,
        use_cache: bool = True,  # Enable cache by default
        db: Optional["AsyncSession"] = None  # [P3] Database session for loading sys_prompt
    ) -> Tuple[str, List[Dict]]:
        """
        Complete RAG pipeline: search -> rerank -> generate (with caching).
        
        Args:
            query: User question
            chat_history: Conversation history
            top_k: Number of context chunks to use
            use_cache: Whether to use semantic cache
            db: Optional database session for loading custom sys_prompt
            
        Returns:
            Tuple of (response_text, sources_list)
        """
        try:
            # Import semantic cache
            from src.core.semantic_cache import semantic_cache
            
            # Generate query embedding for both search and cache
            query_embedding = self.generate_embedding(query, task_type="retrieval_query")
            
            # 1. Check semantic cache first (if enabled)
            if use_cache:
                cached_result = await semantic_cache.get(query_embedding)
                if cached_result:
                    response_text, sources = cached_result
                    logger.info("✅ Semantic cache HIT - returning cached response")
                    return response_text, sources
            
            # 2. Cache miss - proceed with full RAG pipeline
            logger.info("❌ Semantic cache MISS - executing RAG pipeline")
            
            # 3. Hybrid search - [P1] Pass embedding to avoid duplicate generation
            search_results = self.hybrid_search(query, top_k=10, query_embedding=query_embedding)
            
            # 4. Rerank
            top_results = self.rerank_results(query, search_results, top_k=top_k)
            
            # 5. Build context
            context, sources = self.build_context(top_results)
            
            # [P3] Load custom sys_prompt from database if db session provided
            custom_sys_prompt = None
            if db is not None:
                custom_sys_prompt = await load_sys_prompt(db)
            
            # 6. Generate response
            if context:
                response = await self.generate_response(query, context, chat_history, system_prompt=custom_sys_prompt)
            else:
                # No relevant context found
                response = """Xin lỗi, tôi không tìm thấy thông tin phù hợp trong cơ sở kiến thức của mình để trả lời câu hỏi này.

Tôi khuyến khích bạn:
- Liên hệ với chuyên gia tâm lý để được tư vấn trực tiếp
- Đặt câu hỏi khác hoặc diễn đạt lại câu hỏi
- Chia sẻ thêm về tình huống của bạn để tôi có thể hỗ trợ tốt hơn"""
                sources = []
            
            # 7. Cache the result for future queries (if enabled and context was found)
            if use_cache and context:
                await semantic_cache.set(query_embedding, response, sources)
            
            return response, sources
            
        except Exception as e:
            logger.error(f"Error in RAG query pipeline: {str(e)}")
            return "Xin lỗi, có lỗi xảy ra. Vui lòng thử lại.", []


# Global RAG service instance
rag_service = RAGService()
