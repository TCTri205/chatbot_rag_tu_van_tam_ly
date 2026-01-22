"""
Allow NULL user_id in conversations for guest users.

Revision ID: allow_guest_conversations
Revises: seed_system_settings
Create Date: 2025-12-15 10:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'allow_guest_conversations'
down_revision = 'seed_system_settings'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Allow NULL user_id in conversations table."""
    op.alter_column(
        'conversations',
        'user_id',
        existing_type=sa.UUID(),
        nullable=True  # Change to allow NULL
    )


def downgrade() -> None:
    """Disallow NULL user_id in conversations table."""
    # First, delete any conversations with NULL user_id
    op.execute("DELETE FROM conversations WHERE user_id IS NULL")
    
    # Then make the column NOT NULL again
    op.alter_column(
        'conversations',
        'user_id',
        existing_type=sa.UUID(),
        nullable=False
    )
