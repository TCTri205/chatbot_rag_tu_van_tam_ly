"""
PDF Ingestion Script for RAG Knowledge Base.
Processes PDF files from data directory and stores them in ChromaDB.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict
import re
import unicodedata

from pypdf import PdfReader

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.vector_store import get_collection, VectorStoreError
from src.services.rag_service import RAGService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """
    Clean and normalize extracted PDF text.
    
    Args:
        text: Raw text from PDF
        
    Returns:
        Cleaned text
    """
    # Normalize Unicode (NFC for Vietnamese)
    text = unicodedata.normalize('NFC', text)
    
    # Remove common PDF artifacts
    text = re.sub(r'\.{3,}', '', text)  # Remove excessive dots
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Clean up line breaks
    
    # Remove page numbers and headers (simple heuristic)
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
    text = re.sub(r'\n\s*Trang\s+\d+\s*/\s*\d+\s*\n', '\n', text)
    
    return text.strip()


def extract_text_from_pdf(pdf_path: str) -> tuple[str, int]:
    """
    Extract text from PDF file.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Tuple of (extracted_text, num_pages)
    """
    try:
        reader = PdfReader(pdf_path)
        num_pages = len(reader.pages)
        
        text_parts = []
        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        
        full_text = "\n".join(text_parts)
        cleaned_text = clean_text(full_text)
        
        logger.info(f"Extracted {len(cleaned_text)} characters from {num_pages} pages")
        return cleaned_text, num_pages
        
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
        raise


def ingest_pdf(
    pdf_path: str,
    rag_service: RAGService,
    collection,
    category: str = "General"
) -> int:
    """
    Process and ingest a single PDF file.
    
    Args:
        pdf_path: Path to PDF file
        rag_service: RAG service instance
        collection: ChromaDB collection
        category: Document category
        
    Returns:
        Number of chunks ingested
    """
    try:
        filename = os.path.basename(pdf_path)
        logger.info(f"Processing: {filename}")
        
        # Extract text
        text, num_pages = extract_text_from_pdf(pdf_path)
        
        if not text or len(text) < 100:
            logger.warning(f"Insufficient text extracted from {filename}, skipping")
            return 0
        
        # Chunk text
        chunks = rag_service.chunk_text(text)
        
        if not chunks:
            logger.warning(f"No chunks created from {filename}")
            return 0
        
        logger.info(f"Created {len(chunks)} chunks, generating embeddings...")
        
        # Batch processing to avoid rate limits
        batch_size = 10
        total_ingested = 0
        
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_ids = []
            batch_embeddings = []
            batch_metadatas = []
            
            for j, chunk in enumerate(batch_chunks):
                chunk_id = f"{filename}_{i+j}"
                
                try:
                    # Generate embedding
                    embedding = rag_service.generate_embedding(
                        chunk,
                        task_type="retrieval_document"
                    )
                    
                    # Prepare metadata
                    metadata = {
                        "source": filename,
                        "page": min((i + j) // 2, num_pages),  # Rough page estimate
                        "category": category,
                        "chunk_index": i + j
                    }
                    
                    batch_ids.append(chunk_id)
                    batch_embeddings.append(embedding)
                    batch_metadatas.append(metadata)
                    
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk_id}: {str(e)}")
                    continue
            
            # Upsert batch to ChromaDB
            if batch_ids:
                try:
                    collection.upsert(
                        ids=batch_ids,
                        documents=batch_chunks[:len(batch_ids)],
                        embeddings=batch_embeddings,
                        metadatas=batch_metadatas
                    )
                    total_ingested += len(batch_ids)
                    logger.info(f"Ingested batch {i//batch_size + 1}: {len(batch_ids)} chunks")
                except Exception as e:
                    logger.error(f"Error upserting batch: {str(e)}")
        
        logger.info(f"✓ Completed {filename}: {total_ingested} chunks ingested")
        return total_ingested
        
    except Exception as e:
        logger.error(f"Error ingesting {pdf_path}: {str(e)}")
        return 0


def ingest_directory(data_dir: str = "./data", category: str = "General") -> None:
    """
    Ingest all PDF files from a directory.
    
    Args:
        data_dir: Directory containing PDF files
        category: Category for all documents
    """
    try:
        # Initialize services
        logger.info("Initializing RAG service and ChromaDB connection...")
        rag_service = RAGService()
        collection = get_collection()
        
        # Find PDF files
        data_path = Path(data_dir)
        if not data_path.exists():
            logger.error(f"Data directory not found: {data_dir}")
            logger.info(f"Creating directory: {data_dir}")
            data_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Please add PDF files to {data_dir} and run again")
            return
        
        pdf_files = list(data_path.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {data_dir}")
            return
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Process each PDF
        total_chunks = 0
        successful_files = 0
        
        for pdf_path in pdf_files:
            chunks_ingested = ingest_pdf(
                str(pdf_path),
                rag_service,
                collection,
                category
            )
            
            if chunks_ingested > 0:
                successful_files += 1
                total_chunks += chunks_ingested
        
        # Summary
        logger.info("=" * 60)
        logger.info("INGESTION COMPLETE")
        logger.info(f"Files processed: {successful_files}/{len(pdf_files)}")
        logger.info(f"Total chunks ingested: {total_chunks}")
        logger.info(f"ChromaDB collection count: {collection.count()}")
        logger.info("=" * 60)
        
    except VectorStoreError as e:
        logger.error(f"ChromaDB error: {str(e)}")
        logger.error("Make sure ChromaDB container is running: docker-compose up chroma")
    except Exception as e:
        logger.error(f"Fatal error during ingestion: {str(e)}")
        raise


if __name__ == "__main__":
    """
    Usage:
        python -m src.scripts.ingest
        python -m src.scripts.ingest --dir ./custom_data --category Depression
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest PDF files into ChromaDB")
    parser.add_argument(
        "--dir",
        default="./data",
        help="Directory containing PDF files (default: ./data)"
    )
    parser.add_argument(
        "--category",
        default="General",
        help="Category for documents (default: General)"
    )
    
    args = parser.parse_args()
    
    ingest_directory(args.dir, args.category)
