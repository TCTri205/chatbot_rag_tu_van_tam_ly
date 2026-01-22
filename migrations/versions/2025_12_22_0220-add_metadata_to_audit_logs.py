"""
Add metadata column to audit_logs table.

Revision ID: add_audit_metadata
Revises: 0b79e3ca1eff
Create Date: 2025-12-22

This migration adds the JSONB 'metadata' column to the audit_logs table,
which is required by the AuditLog model's extra_data field.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_audit_metadata'
down_revision = '0b79e3ca1eff'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add metadata column to audit_logs table."""
    # Check if column already exists before adding
    # Using raw SQL to avoid issues with different database states
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'audit_logs' AND column_name = 'metadata'
            ) THEN
                ALTER TABLE audit_logs ADD COLUMN metadata JSONB NULL;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Remove metadata column from audit_logs table."""
    op.drop_column('audit_logs', 'metadata')
