"""
Seed default system settings for Phase 2.

Revision ID: seed_system_settings
Revises: d38c0ccb3422
Create Date: 2025-12-15 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'seed_system_settings'
down_revision = 'd38c0ccb3422'
branch_labels = None
depends_on = None


DEFAULT_SYSTEM_PROMPT = """Bạn là một chuyên gia tư vấn tâm lý AI nhân ái, thấu cảm và chuyên nghiệp.

Nhiệm vụ của bạn:
1. Sử dụng thông tin trong [CONTEXT] để trả lời câu hỏi của người dùng.
2. Luôn lắng nghe và xác nhận cảm xúc trước khi đưa lời khuyên.
3. Chỉ trả lời dựa trên kiến thức tâm lý học và context được cung cấp.
4. KHÔNG bịa đặt thông tin không có trong context.
5. Trích dẫn nguồn khi có thể (VD: "Theo nguồn X, ...").
6. Trả lời bằng tiếng Việt tự nhiên, ấm áp và dễ hiểu.
7. Nếu không có đủ thông tin trong context, hãy thừa nhận và đề xuất người dùng tìm kiếm chuyên gia.

Giọng điệu: Thấu cảm, nhẹ nhàng, không phán xét."""

DEFAULT_SOS_KEYWORDS = "tự tử,tự sát,chết,tự hại,kết thúc cuộc đời,không muốn sống,muốn chết,giết mình,tự kết liễu,nhảy lầu,cắt tay,uống thuốc,tự vẫn"

DEFAULT_HOTLINES = '''[
    {
        "name": "Đường dây nóng tâm lý - Trung tâm Phòng chống Tự tử",
        "number": "1800 599 913",
        "available": "24/7"
    },
    {
        "name": "Cấp cứu khẩn cấp",
        "number": "115",
        "available": "24/7"
    },
    {
        "name": "Tổng đài tư vấn tâm lý",
        "number": "1800 599 913",
        "available": "24/7"
    }
]'''


def upgrade() -> None:
    """Insert default system settings."""
    # Check if settings already exist (for idempotency)
    conn = op.get_bind()
    
    # Insert system prompt
    conn.execute(
        sa.text("""
            INSERT INTO system_settings (key, value, description, updated_at)
            VALUES (:key, :value, :description, NOW())
            ON CONFLICT (key) DO NOTHING
        """),
        {
            "key": "sys_prompt",
            "value": DEFAULT_SYSTEM_PROMPT,
            "description": "Default system prompt for AI assistant"
        }
    )
    
    # Insert SOS keywords
    conn.execute(
        sa.text("""
            INSERT INTO system_settings (key, value, description, updated_at)
            VALUES (:key, :value, :description, NOW())
            ON CONFLICT (key) DO NOTHING
        """),
        {
            "key": "sos_keywords",
            "value": DEFAULT_SOS_KEYWORDS,
            "description": "Comma-separated keywords for crisis detection"
        }
    )
    
    # Insert crisis hotlines
    conn.execute(
        sa.text("""
            INSERT INTO system_settings (key, value, description, updated_at)
            VALUES (:key, :value, :description, NOW())
            ON CONFLICT (key) DO NOTHING
        """),
        {
            "key": "crisis_hotlines",
            "value": DEFAULT_HOTLINES,
            "description": "JSON array of crisis hotline information"
        }
    )


def downgrade() -> None:
    """Remove default system settings."""
    op.execute(
        sa.text("""
            DELETE FROM system_settings 
            WHERE key IN ('sys_prompt', 'sos_keywords', 'crisis_hotlines')
        """)
    )
