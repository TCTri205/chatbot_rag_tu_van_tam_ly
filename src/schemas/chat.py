"""
Chat message and conversation schemas.
"""
from pydantic import BaseModel, Field, UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    content: str = Field(..., min_length=1, max_length=2000, description="Message content")


class ChatRequest(BaseModel):
    """Chat message request for Phase 2."""
    content: str = Field(
        ..., 
        min_length=1,
        max_length=2000,
        description="User message content"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "Tôi cảm thấy rất lo lắng về công việc"
            }
        }


class RAGSource(BaseModel):
    """Schema for RAG source citation."""
    title: str = Field(..., description="Source document filename")
    page: int = Field(..., description="Page number")
    content_snippet: str = Field(..., description="Relevant content snippet")


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: uuid.UUID
    role: str
    content: str
    detected_emotion: Optional[str] = None
    rag_sources: Optional[List[Dict[str, Any]]] = None
    is_sos: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """Enhanced chat response with RAG sources for Phase 2."""
    message_id: UUID4 = Field(..., description="Unique message ID")
    role: str = Field(default="assistant", description="Message role")
    content: str = Field(..., description="Bot response content")
    emotion_tag: Optional[str] = Field(None, description="Detected emotion")
    sources: List[RAGSource] = Field(default=[], description="RAG source citations")
    is_crisis: bool = Field(default=False, description="Crisis situation detected")
    created_at: datetime = Field(..., description="Message timestamp")
    
    class Config:
        json_encoders = {
            uuid.UUID: str,  # Convert UUID to string for JSON serialization
            datetime: lambda v: v.isoformat()  # Ensure datetime is ISO format
        }



class CrisisResponse(BaseModel):
    """Crisis situation response."""
    is_crisis: bool = Field(True, description="Always true for crisis response")
    message: str = Field(..., description="Crisis intervention message")
    hotlines: List[Dict] = Field(..., description="Emergency hotlines")
    additional_resources: List[str] = Field(default=[], description="Additional help resources")


class MessageHistory(BaseModel):
    """Single message in chat history."""
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime
    is_sos: bool = False
    rag_sources: Optional[List[Dict[str, Any]]] = None  # Include sources for history reload
    
    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Chat history response with pagination."""
    messages: List[MessageHistory]
    total: int
    has_more: bool


class ConversationResponse(BaseModel):
    """Schema for conversation response."""
    id: uuid.UUID
    title: Optional[str] = None
    status: str
    created_at: datetime
    message_count: Optional[int] = None
    
    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""
    title: Optional[str] = Field(None, max_length=255)

