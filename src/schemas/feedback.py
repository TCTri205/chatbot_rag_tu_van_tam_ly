"""
Feedback schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class FeedbackCreate(BaseModel):
    """Schema for creating feedback."""
    message_id: uuid.UUID
    rating: int = Field(..., ge=-1, le=1, description="Rating: 1 for like, -1 for dislike")
    comment: Optional[str] = Field(None, max_length=1000)


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""
    id: uuid.UUID
    message_id: uuid.UUID
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
