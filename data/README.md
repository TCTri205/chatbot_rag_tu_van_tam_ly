# Data Directory

This directory is for storing PDF documents to be ingested into the knowledge base.

## Usage

1. **Add PDF Files**: Place your psychology-related PDF documents in this directory
   - These can be textbooks, research papers, treatment guides, etc.
   - Ensure PDFs are readable (not scanned images without OCR)

2. **Run Ingestion Script**:

   ```bash
   docker-compose exec backend python -m src.scripts.ingest
   ```

## Example Files

For testing purposes, you can add:

- Mental health guides
- Psychology textbooks
- Counseling best practices documents
- CBT/DBT therapy manuals (in Vietnamese if available)

## Notes

- Files are processed and chunked automatically
- Each chunk is embedded using Google Gemini Embeddings
- Processed data is stored in ChromaDB (not here)
- Original PDF files can be removed after ingestion if needed
