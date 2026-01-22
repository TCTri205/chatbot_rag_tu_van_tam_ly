import asyncio
import os
import sys

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from src.database import engine

async def migrate_audit_logs():
    """Add metadata column to audit_logs table."""
    print("Starting migration: Adding 'metadata' column to 'audit_logs'...")
    
    async with engine.begin() as conn:
        try:
            # Check if column exists
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'audit_logs' AND column_name = 'metadata';
            """)
            result = await conn.execute(check_query)
            if result.scalar():
                print("Column 'metadata' already exists in 'audit_logs'. Skipping.")
                return

            # Add column if not exists
            await conn.execute(text("ALTER TABLE audit_logs ADD COLUMN metadata JSONB NULL;"))
            print("Successfully added 'metadata' column to 'audit_logs'.")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            raise

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(migrate_audit_logs())
