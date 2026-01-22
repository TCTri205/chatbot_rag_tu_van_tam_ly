"""
Admin knowledge base management API router.
Handles PDF upload, listing, and deletion.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Set
import os
import shutil
import logging
from pathlib import Path

from src.database import get_db
from src.models.user import User
from src.api.deps import require_admin
from src.scripts.ingest import ingest_pdf
# [Round 2 Fix #1] Use global singleton instead of creating new instance
from src.services.rag_service import rag_service
from src.core.vector_store import get_collection, reset_collection

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    category: str = "General",
    admin: User = Depends(require_admin)
):
    """
    Upload and ingest a PDF into knowledge base.
    
    Args:
        file: PDF file to upload
        category: Document category
        admin: Admin user (from dependency)
    
    Returns:
        Upload status with chunk count
    
    Raises:
        400: Invalid file type
        500: Ingestion error
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Ensure data directory exists
    data_dir = Path("./data")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = data_dir / file.filename
    
    try:
        logger.info(f"📄 Uploading PDF: {file.filename}")
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"✅ File saved to: {file_path}")
        
        # [Round 2 Fix #1] Use global RAG service singleton
        logger.info("🔧 Using global RAG service...")
        collection = get_collection()
        
        # Ingest PDF
        logger.info(f"📚 Starting ingestion for: {file.filename}")
        chunks_count = ingest_pdf(
            str(file_path),
            rag_service,
            collection,
            category
        )
        
        # [Round 2 Fix #2] Invalidate BM25 cache after adding new documents
        rag_service.invalidate_bm25_cache()
        logger.info(f"✅ Ingestion complete: {chunks_count} chunks created, BM25 cache invalidated")
        
        # CHANGED: Do NOT delete file even if chunks_count == 0
        # Keep file for debugging and potential retry
        if chunks_count == 0:
            logger.warning(f"⚠️ No chunks created for {file.filename}, but file kept for debugging")
            # Return success but with warning
            return {
                "message": "PDF uploaded but ingestion produced 0 chunks. File kept for debugging.",
                "filename": file.filename,
                "chunks": 0,
                "category": category,
                "warning": "No chunks created - file may be empty or incompatible"
            }
        
        return {
            "message": "PDF uploaded and ingested successfully",
            "filename": file.filename,
            "chunks": chunks_count,
            "category": category
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # CHANGED: Log error but do NOT delete file - keep for debugging
        logger.error(f"❌ Error processing PDF {file.filename}: {str(e)}", exc_info=True)
        
        # Return detailed error without deleting file
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process PDF: {str(e)}. File saved to {file_path} for debugging."
        )


@router.get("/list")
async def list_knowledge_files(
    admin: User = Depends(require_admin)
):
    """
    List all PDF files in knowledge base.
    
    Returns:
        List of PDF files with metadata
    """
    data_dir = Path("./data")
    logger.info(f"📂 Listing files from: {data_dir.absolute()}")
    
    if not data_dir.exists():
        logger.warning(f"⚠️ Data directory does not exist: {data_dir.absolute()}")
        return {"files": [], "total": 0}
    
    files = []
    for pdf_file in data_dir.glob("*.pdf"):
        stat = pdf_file.stat()
        files.append({
            "filename": pdf_file.name,
            "size_bytes": stat.st_size,
            "uploaded_at": stat.st_mtime,
            "size_mb": round(stat.st_size / (1024 * 1024), 2)
        })
    
    # Sort by upload time (newest first)
    files.sort(key=lambda x: x["uploaded_at"], reverse=True)
    
    logger.info(f"📚 Found {len(files)} PDF files")
    return {"files": files, "total": len(files)}


@router.delete("/reset-all")
async def reset_knowledge_base(
    admin: User = Depends(require_admin)
):
    """
    Reset entire knowledge base - delete ALL ChromaDB data and semantic cache.
    
    WARNING: This is a destructive operation that removes ALL knowledge data.
    Use this when you want to start fresh or fix orphaned data issues.
    
    Returns:
        Reset status with counts
    """
    try:
        logger.warning("⚠️ RESETTING ENTIRE KNOWLEDGE BASE")
        
        # 1. Reset ChromaDB collection (delete and recreate)
        reset_collection()
        logger.info("🗑️ ChromaDB collection reset")
        
        # 2. Clear all semantic cache
        from src.core.semantic_cache import semantic_cache
        cache_cleared = await semantic_cache.clear_all()
        logger.info(f"🗑️ Cleared {cache_cleared} semantic cache entries")
        
        # 3. Optionally delete all PDF files (commented out for safety)
        # data_dir = Path("./data")
        # for pdf in data_dir.glob("*.pdf"):
        #     pdf.unlink()
        
        return {
            "message": "Knowledge base reset successfully. All vector data and cache cleared.",
            "cache_cleared": cache_cleared,
            "warning": "PDF files in ./data/ are NOT deleted. Delete them manually if needed."
        }
        
    except Exception as e:
        logger.error(f"❌ Error resetting knowledge base: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reset failed: {str(e)}"
        )


@router.delete("/purge-orphans")
async def purge_orphan_data(
    admin: User = Depends(require_admin)
):
    """
    Purge orphaned ChromaDB data - remove chunks whose source files no longer exist.
    
    This is useful when PDF files were deleted manually but ChromaDB still has their chunks.
    Also clears semantic cache to ensure stale data is not returned.
    
    Returns:
        Purge status with list of orphaned sources removed
    """
    try:
        logger.info("🔍 Scanning for orphaned ChromaDB data...")
        
        # 1. Get list of existing PDF files
        data_dir = Path("./data")
        existing_files: Set[str] = set()
        if data_dir.exists():
            existing_files = {pdf.name for pdf in data_dir.glob("*.pdf")}
        
        logger.info(f"📂 Found {len(existing_files)} existing PDF files")
        
        # 2. Get all unique sources from ChromaDB
        collection = get_collection()
        all_data = collection.get(include=["metadatas"])
        
        if not all_data['metadatas']:
            return {
                "message": "No data in ChromaDB to purge",
                "orphans_found": [],
                "total_deleted": 0
            }
        
        # Find unique sources
        sources_in_db: Set[str] = set()
        for metadata in all_data['metadatas']:
            if metadata and 'source' in metadata:
                sources_in_db.add(metadata['source'])
        
        logger.info(f"📊 Found {len(sources_in_db)} unique sources in ChromaDB")
        
        # 3. Find orphans (in DB but no file)
        orphans = sources_in_db - existing_files
        
        if not orphans:
            return {
                "message": "No orphaned data found",
                "orphans_found": [],
                "total_deleted": 0
            }
        
        logger.info(f"🗑️ Found {len(orphans)} orphaned sources: {orphans}")
        
        # 4. Delete orphaned data
        from src.core.vector_store import delete_document
        total_deleted = 0
        for orphan_source in orphans:
            deleted = delete_document(orphan_source)
            total_deleted += deleted
            logger.info(f"   Deleted {deleted} chunks for orphan: {orphan_source}")
        
        # 5. Clear semantic cache
        from src.core.semantic_cache import semantic_cache
        cache_cleared = await semantic_cache.clear_all()
        logger.info(f"🗑️ Cleared {cache_cleared} semantic cache entries")
        
        return {
            "message": "Orphaned data purged successfully",
            "orphans_found": list(orphans),
            "total_chunks_deleted": total_deleted,
            "cache_cleared": cache_cleared
        }
        
    except Exception as e:
        logger.error(f"❌ Error purging orphans: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Purge failed: {str(e)}"
        )


@router.delete("/{filename}")
async def delete_knowledge_file(
    filename: str,
    admin: User = Depends(require_admin)
):
    """
    Delete a PDF from knowledge base.
    
    WARNING: This only deletes the file, not the chunks from ChromaDB.
    ChromaDB chunks remain until manual cleanup.
    
    Args:
        filename: Name of PDF file to delete
    
    Returns:
        Deletion status with warning
    
    Raises:
        404: File not found
    """
    # Security: prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )
    
    file_path = Path("./data") / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not a file"
        )
    
    # Delete file
    try:
        # First, delete chunks from ChromaDB
        from src.core.vector_store import delete_document
        chunks_deleted = delete_document(filename)
        logger.info(f"🗑️ Deleted {chunks_deleted} vector chunks for {filename}")
        
        # [Round 2 Fix #2] Invalidate BM25 cache after deleting documents
        rag_service.invalidate_bm25_cache()
        
        # Clear semantic cache to ensure stale sources are not returned
        from src.core.semantic_cache import semantic_cache
        cache_cleared = await semantic_cache.clear_all()
        logger.info(f"🗑️ Cleared {cache_cleared} semantic cache entries, BM25 cache invalidated")
        
        # Then delete physical file
        file_path.unlink()
        logger.info(f"🗑️ Deleted physical file: {file_path}")
        
        return {
            "message": "File and associated knowledge data deleted successfully",
            "filename": filename,
            "chunks_deleted": chunks_deleted,
            "cache_cleared": cache_cleared
        }
    except Exception as e:
        logger.error(f"❌ Error during file deletion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deletion failed: {str(e)}"
        )

