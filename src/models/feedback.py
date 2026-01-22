"""
Feedback model for message ratings.
"""
from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base
from src.models.base import UUIDMixin, TimestampMixin


class Feedback(Base, UUIDMixin, TimestampMixin):
    """Feedback model for message rating."""
    __tablename__ = "feedbacks"
    
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1 for like, -1 for dislike
    comment = Column(Text, nullable=True)
    
    # Relationships
    message = relationship("Message", back_populates="feedbacks")
    
    def __repr__(self):
        return f"<Feedback {self.id} - Rating: {self.rating}>"
