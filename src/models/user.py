"""
User model for authentication and authorization.
"""
from sqlalchemy import Column, String, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from src.database import Base
from src.models.base import UUIDMixin, TimestampMixin


class UserRole(str, enum.Enum):
    """User role enumeration."""
    GUEST = "guest"
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class User(Base, UUIDMixin, TimestampMixin):
    """User account model."""
    __tablename__ = "users"
    
    username = Column(String(50), nullable=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.GUEST, nullable=False)
    is_anonymous = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    mood_entries = relationship("MoodEntry", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email or self.username or self.id}>"
