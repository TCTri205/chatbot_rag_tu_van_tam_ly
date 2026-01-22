"""
Script to purge orphaned ChromaDB data.
Run: docker-compose exec backend python -m src.scripts.purge_orphans_data
"""
import asyncio
from pathlib import Path
from typing import Set

from src.core.vector_store import get_collection, delete_document
from src.core.semantic_cache import semantic_cache


async def main():
    """Purge orphaned ChromaDB data."""
    print("🔍 Scanning for orphaned ChromaDB data...")
    
    # 1. Get list of existing PDF files
    data_dir = Path("./data")
    existing_files: Set[str] = set()
    if data_dir.exists():
        existing_files = {pdf.name for pdf in data_dir.glob("*.pdf")}
    
    print(f"📂 Found {len(existing_files)} existing PDF files: {existing_files}")
    
    # 2. Get all unique sources from ChromaDB
    collection = get_collection()
    all_data = collection.get(include=["metadatas"])
    
    if not all_data['metadatas']:
        print("✅ No data in ChromaDB to purge")
        return
    
    # Find unique sources
    sources_in_db: Set[str] = set()
    for metadata in all_data['metadatas']:
        if metadata and 'source' in metadata:
            sources_in_db.add(metadata['source'])
    
    print(f"📊 Found {len(sources_in_db)} unique sources in ChromaDB: {sources_in_db}")
    
    # 3. Find orphans (in DB but no file)
    orphans = sources_in_db - existing_files
    
    if not orphans:
        print("✅ No orphaned data found. All ChromaDB data has corresponding PDF files.")
        return
    
    print(f"\n🗑️ Found {len(orphans)} orphaned sources:")
    for orphan in orphans:
        print(f"   - {orphan}")
    
    # 4. Delete orphaned data
    total_deleted = 0
    for orphan_source in orphans:
        deleted = delete_document(orphan_source)
        total_deleted += deleted
        print(f"   ✅ Deleted {deleted} chunks for orphan: {orphan_source}")
    
    # 5. Clear semantic cache
    cache_cleared = await semantic_cache.clear_all()
    print(f"\n🗑️ Cleared {cache_cleared} semantic cache entries")
    
    print(f"\n✅ SUCCESS: Purged {total_deleted} chunks from {len(orphans)} orphaned sources")


if __name__ == "__main__":
    asyncio.run(main())
