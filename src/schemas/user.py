"""
User schemas for data transfer.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid


class UserBase(BaseModel):
    """Base user schema."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response (safe for client)."""
    id: uuid.UUID
    role: str
    is_anonymous: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True  # For SQLAlchemy ORM compatibility
