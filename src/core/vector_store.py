"""
ChromaDB vector store connection and utilities.

Performance optimizations:
- [P1.2] Connection pooling via singleton client
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import Optional
import logging
import time

from src.config import settings

logger = logging.getLogger(__name__)

# [P1.2] Module-level singleton for connection pooling
_chroma_client: Optional[chromadb.HttpClient] = None
_chroma_client_last_check: float = 0
_CHROMA_HEARTBEAT_INTERVAL: int = 60  # Check heartbeat every 60 seconds


class VectorStoreError(Exception):
    """Custom exception for vector store operations."""
    pass


def get_chroma_client() -> chromadb.HttpClient:
    """
    Get ChromaDB HTTP client connected to Docker container.
    [P1.2] Uses singleton pattern with periodic heartbeat check.
    
    Returns:
        chromadb.HttpClient: Connected ChromaDB client
        
    Raises:
        VectorStoreError: If connection fails
    """
    global _chroma_client, _chroma_client_last_check
    
    current_time = time.time()
    
    # [P1.2] Return cached client if valid and heartbeat is recent
    if _chroma_client is not None:
        # Skip heartbeat if checked recently
        if current_time - _chroma_client_last_check < _CHROMA_HEARTBEAT_INTERVAL:
            return _chroma_client
        
        # Periodic heartbeat check
        try:
            _chroma_client.heartbeat()
            _chroma_client_last_check = current_time
            logger.debug("[P1.2] ChromaDB heartbeat OK (cached client)")
            return _chroma_client
        except Exception as e:
            logger.warning(f"[P1.2] ChromaDB heartbeat failed, reconnecting: {e}")
            _chroma_client = None
    
    # Create new connection with retry logic
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            # ChromaDB open-source configuration
            _chroma_client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT,
                settings=ChromaSettings(
                    anonymized_telemetry=False
                )
            )
            
            # Test connection with heartbeat
            _chroma_client.heartbeat()
            _chroma_client_last_check = current_time
            logger.info(f"✓ [P1.2] Connected to ChromaDB at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
            
            return _chroma_client
            
        except Exception as e:
            error_msg = str(e)
            attempt_msg = f"(attempt {attempt + 1}/{max_retries})"
            
            if attempt < max_retries - 1:
                logger.warning(f"ChromaDB connection failed {attempt_msg}, retrying in {retry_delay}s: {error_msg}")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
            
            # Last attempt failed - log detailed diagnostics
            logger.error(f"Failed to connect to ChromaDB at {settings.CHROMA_HOST}:{settings.CHROMA_PORT} after {max_retries} attempts")
            logger.error(f"Error details: {error_msg}")
            
            # Provide helpful diagnostics
            if "tenant" in error_msg.lower() or "database" in error_msg.lower():
                logger.error("❌ ChromaDB tenant/database error detected")
                logger.error("   This may indicate version mismatch between client and server")
                logger.error(f"   Client version: chromadb==0.5.0 (from requirements.txt)")
                logger.error(f"   Server version: chromadb/chroma:0.5.0 (from docker-compose.yml)")
                logger.error("   Ensure ChromaDB container is running: docker-compose up -d chroma")
                logger.error("   Check container logs: docker-compose logs chroma")
            elif "connection" in error_msg.lower() or "refused" in error_msg.lower():
                logger.error("❌ ChromaDB connection refused")
                logger.error("   Ensure ChromaDB container is running: docker-compose ps chroma")
                logger.error("   Verify network connectivity in Docker")
                logger.error("   Check if service is healthy: docker-compose ps")
            elif "np.float_" in error_msg.lower() or "numpy" in error_msg.lower():
                logger.error("❌ NumPy compatibility error detected")
                logger.error("   This indicates ChromaDB server is using incompatible NumPy version")
                logger.error("   Ensure Docker image is updated: docker-compose pull chroma")
                logger.error("   Rebuild containers: docker-compose up -d --force-recreate chroma")
            else:
                logger.error("   Check ChromaDB service status and logs")
                logger.error("   Verify environment variables: CHROMA_HOST and CHROMA_PORT")
                
            raise VectorStoreError(f"ChromaDB connection failed after {max_retries} attempts: {error_msg}")


def get_collection(name: str = "psychology_knowledge"):
    """
    Get or create a collection in ChromaDB.
    
    Args:
        name: Collection name (default: "psychology_knowledge")
        
    Returns:
        chromadb.Collection: Collection instance
        
    Raises:
        VectorStoreError: If collection operations fail
    """
    try:
        client = get_chroma_client()
        collection = client.get_or_create_collection(
            name=name,
            metadata={
                "description": "Psychology knowledge base from PDF documents",
                "hnsw:space": "cosine"  # Use cosine similarity for semantic search
            }
        )
        logger.info(f"Retrieved collection '{name}' with {collection.count()} documents")
        return collection
    except Exception as e:
        logger.error(f"Failed to get collection '{name}': {str(e)}")
        raise VectorStoreError(f"Collection operation failed: {str(e)}")


def reset_collection(name: str = "psychology_knowledge") -> None:
    """
    Delete and recreate a collection (use with caution!).
    
    Args:
        name: Collection name to reset
    """
    try:
        client = get_chroma_client()
        try:
            client.delete_collection(name)
            logger.warning(f"Deleted collection '{name}'")
        except:
            pass
        get_collection(name)
        logger.info(f"Recreated collection '{name}'")
    except Exception as e:
        logger.error(f"Failed to reset collection '{name}': {str(e)}")
        raise VectorStoreError(f"Collection reset failed: {str(e)}")


def delete_document(filename: str, collection_name: str = "psychology_knowledge") -> int:
    """
    Delete all chunks associated with a specific document file from ChromaDB.
    
    Args:
        filename: Name of the file to delete (matches 'source' metadata)
        collection_name: Name of the collection
        
    Returns:
        int: Number of items deleted (estimate, as ChromaDB doesn't return count)
    """
    try:
        collection = get_collection(collection_name)
        # ChromaDB delete doesn't return count, so we query first to get count for logging
        try:
            # Query to see how many chunks we're about to delete
            # Note: This is optional and for logging purposes
            results = collection.get(where={"source": filename})
            count = len(results['ids']) if results and 'ids' in results else 0
        except:
            count = 0 # Fallback if get fails
            
        logger.info(f"Deleting {count} chunks for document: {filename}")
        
        # Perform deletion
        collection.delete(where={"source": filename})
        logger.info(f"Successfully deleted chunks for {filename}")
        
        return count
    except Exception as e:
        logger.error(f"Failed to delete document '{filename}': {str(e)}")
        raise VectorStoreError(f"Document deletion failed: {str(e)}")
