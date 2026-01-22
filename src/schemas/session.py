"""
Session management schemas.
"""
from pydantic import BaseModel, Field, UUID4
from typing import Optional
from datetime import datetime


class SessionInitRequest(BaseModel):
    """Request to initialize a new session.
    
    Note: user_id is NOT accepted from body for security reasons.
    User identity is determined by JWT token if present.
    """
    # SECURITY: user_id removed - was allowing impersonation attacks
    # User identity now comes from JWT token only
    
    class Config:
        json_schema_extra = {
            "example": {}  # Empty body - user_id from JWT only
        }


class SessionInitResponse(BaseModel):
    """Response after session initialization.
    
    Note: conversation_id may be None initially.
    Conversation is created lazily on first message to avoid spam empty conversations.
    """
    session_id: UUID4 = Field(..., description="New session ID")
    conversation_id: Optional[UUID4] = Field(None, description="Conversation ID (None until first message)")
    greeting: str = Field(..., description="Welcome message")
    created_at: datetime = Field(..., description="Session creation timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "conversation_id": None,  # Created on first message
                "greeting": "Chào bạn! Tôi có thể giúp gì cho bạn hôm nay?",
                "created_at": "2024-01-15T10:00:00Z"
            }
        }


class SessionInfo(BaseModel):
    """Session information response."""
    session_id: UUID4
    user_id: Optional[UUID4]
    conversation_id: UUID4
    is_active: bool
    created_at: datetime
    expires_at: datetime
