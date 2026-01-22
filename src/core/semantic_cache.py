"""
Semantic cache layer for RAG queries.
Caches query embeddings and results to reduce Gemini API calls and latency.
"""
import hashlib
import json
import logging
from typing import Optional, Tuple, List, Dict
from src.core.redis import get_redis

logger = logging.getLogger(__name__)


class SemanticCache:
    """
    Semantic cache for RAG query results.
    
    Uses query embedding hash as cache key to find semantically similar queries.
    """
    
    def __init__(self, ttl: int = 3600):
        """
        Initialize semantic cache.
        
        Args:
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        self.ttl = ttl
        self.cache_prefix = "rag_cache:"
        
    def _generate_cache_key(self, query_embedding: List[float]) -> str:
        """
        Generate cache key from query embedding.
        
        Args:
            query_embedding: Embedding vector
            
        Returns:
            Cache key (hash of embedding)
        """
        # Convert embedding to bytes for hashing
        embedding_bytes = json.dumps(query_embedding, sort_keys=True).encode('utf-8')
        hash_digest = hashlib.sha256(embedding_bytes).hexdigest()[:16]  # First 16 chars
        return f"{self.cache_prefix}{hash_digest}"
    
    async def get(
        self,
        query_embedding: List[float]
    ) -> Optional[Tuple[str, List[Dict]]]:
        """
        Get cached RAG result.
        
        Args:
            query_embedding: Query embedding vector
            
        Returns:
            Tuple of (response_text, sources) if cache hit, None otherwise
        """
        try:
            redis = await get_redis()
            cache_key = self._generate_cache_key(query_embedding)
            
            # Get cached data
            cached_data = await redis.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.info(f"✅ Cache HIT: {cache_key}")
                return data['response'], data['sources']
            
            logger.info(f"❌ Cache MISS: {cache_key}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting from cache: {str(e)}")
            return None
    
    async def set(
        self,
        query_embedding: List[float],
        response: str,
        sources: List[Dict]
    ) -> bool:
        """
        Cache RAG result.
        
        Args:
            query_embedding: Query embedding vector
            response: Generated response text
            sources: RAG sources list
            
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            redis = await get_redis()
            cache_key = self._generate_cache_key(query_embedding)
            
            # Prepare cache data
            cache_data = {
                'response': response,
                'sources': sources
            }
            
            # Set with TTL
            await redis.setex(
                cache_key,
                self.ttl,
                json.dumps(cache_data, ensure_ascii=False)
            )
            
            logger.info(f"💾 Cached: {cache_key} (TTL: {self.ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
            return False
    
    async def clear_all(self) -> int:
        """
        Clear all RAG cache entries.
        
        Returns:
            Number of keys deleted
        """
        try:
            redis = await get_redis()
            pattern = f"{self.cache_prefix}*"
            
            # Find all cache keys
            keys = await redis.keys(pattern)
            
            if keys:
                deleted = await redis.delete(*keys)
                logger.info(f"🗑️ Cleared {deleted} cache entries")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return 0


# Global semantic cache instance
semantic_cache = SemanticCache(ttl=3600)  # 1 hour TTL
