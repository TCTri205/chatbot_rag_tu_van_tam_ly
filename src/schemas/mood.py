"""
Mood tracking schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class MoodCreate(BaseModel):
    """Schema for creating a mood entry."""
    mood_value: int = Field(..., ge=1, le=5, description="Mood value from 1 (worst) to 5 (best)")
    mood_label: Optional[str] = Field(None, max_length=50)
    note: Optional[str] = Field(None, max_length=500)


class MoodResponse(BaseModel):
    """Schema for mood entry response."""
    id: uuid.UUID
    mood_value: int
    mood_label: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class MoodHistoryItem(BaseModel):
    """Schema for mood history data point."""
    date: str
    value: float  # Average mood value for the day
    label: Optional[str] = None
