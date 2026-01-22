"""
Conversation schemas for request/response validation.
"""
from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import List


class ConversationDetail(BaseModel):
    """Conversation detail for list response."""
    id: UUID4
    title: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Response for conversation list endpoint."""
    conversations: List[ConversationDetail]
    total: int
    has_more: bool


class ConversationTitleUpdate(BaseModel):
    """Request schema for updating conversation title."""
    title: str
