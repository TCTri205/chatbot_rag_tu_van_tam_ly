"""
Mood tracking model.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from src.database import Base
from src.models.base import UUIDMixin, TimestampMixin


class MoodLabel(str, enum.Enum):
    """Mood label enumeration."""
    ANGRY = "angry"
    SAD = "sad"
    NEUTRAL = "neutral"
    HAPPY = "happy"
    EXCITED = "excited"


class MoodEntry(Base, UUIDMixin, TimestampMixin):
    """Mood entry model for mood tracking."""
    __tablename__ = "mood_entries"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    mood_value = Column(Integer, nullable=False)  # 1-5 scale
    mood_label = Column(String(50), nullable=True)
    note = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="mood_entries")
    
    def __repr__(self):
        return f"<MoodEntry {self.id} - Value: {self.mood_value}>"
