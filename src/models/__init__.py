"""
Models package initialization.
Import all models here for Alembic auto-generation.
"""
from src.models.base import UUIDMixin, TimestampMixin
from src.models.user import User, UserRole
from src.models.chat import Conversation, Message, ConversationStatus, MessageRole
from src.models.mood import MoodEntry, MoodLabel
from src.models.feedback import Feedback
from src.models.audit import AuditLog, SystemSetting

__all__ = [
    "UUIDMixin",
    "TimestampMixin",
    "User",
    "UserRole",
    "Conversation",
    "Message",
    "ConversationStatus",
    "MessageRole",
    "MoodEntry",
    "MoodLabel",
    "Feedback",
    "AuditLog",
    "SystemSetting",
]
