"""
Conversations management API router.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import Optional
import uuid
from datetime import datetime

from src.database import get_db
from src.core.redis import get_redis
from src.models.chat import Conversation, ConversationStatus, Message
from src.models.user import User
from fastapi.responses import Response
from sqlalchemy.orm import selectinload
import json
from src.schemas.conversation import (
    ConversationListResponse,
    ConversationDetail,
    ConversationTitleUpdate
)
from src.api.deps import get_current_user_optional

router = APIRouter()


@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = 20,
    offset: int = 0,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    List conversations for current user/session.
    
    For authenticated users: list all their conversations
    For guests: list conversation from current session only
    
    Args:
        limit: Maximum number of conversations to return
        offset: Offset for pagination
        x_session_id: Session ID header (for guest users)
        db: Database session
        redis: Redis connection
        current_user: Current authenticated user (optional)
    
    Returns:
        ConversationListResponse: List of conversations with metadata
    """
    conversations = []
    total = 0
    
    # Get user_id from session or auth
    if current_user:
        user_id = current_user.id
        # Query all user's conversations
        query = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .where(Conversation.status == ConversationStatus.ACTIVE)
            .order_by(desc(Conversation.updated_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(query)
        conversations = result.scalars().all()
        
        # Count total
        count_query = select(func.count(Conversation.id)).where(
            Conversation.user_id == user_id,
            Conversation.status == ConversationStatus.ACTIVE
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
    elif x_session_id:
        # Get conversation_id from session
        session_data = await redis.hgetall(f"session:{x_session_id}")
        if session_data and 'conversation_id' in session_data:
            conversation_id = uuid.UUID(session_data['conversation_id'])
            query = select(Conversation).where(Conversation.id == conversation_id)
            result = await db.execute(query)
            conversation = result.scalar_one_or_none()
            if conversation:
                conversations = [conversation]
                total = 1
    
    return ConversationListResponse(
        conversations=conversations,
        total=total,
        has_more=(offset + limit) < total
    )


@router.patch("/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: uuid.UUID,
    data: ConversationTitleUpdate,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Update conversation title.
    
    Args:
        conversation_id: ID of the conversation
        data: New title data
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        dict: Success message
    
    Raises:
        HTTPException 401: Not authenticated
        HTTPException 403: Not authorized
        HTTPException 404: Conversation not found
    
    Security:
        Requires session ownership or authenticated user ownership.
    """
    # Security: Require session or auth
    if not current_user and not x_session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Check ownership for authenticated users
    if current_user and conversation.user_id and conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Check ownership for guest users (session-based)
    if not current_user and x_session_id:
        session_data = await redis.hgetall(f"session:{x_session_id}")
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
        session_conv_id = session_data.get('conversation_id', '')
        if str(conversation_id) != session_conv_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this conversation"
            )
    
    conversation.title = data.title
    await db.commit()
    
    return {"message": "Title updated successfully"}


@router.delete("/{conversation_id}")
async def archive_conversation(
    conversation_id: uuid.UUID,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Archive a conversation (soft delete).
    
    Args:
        conversation_id: ID of the conversation
        x_session_id: Optional session ID for guest users
        db: Database session
        redis: Redis connection
        current_user: Current authenticated user
    
    Returns:
        dict: Success message
    
    Raises:
        HTTPException 404: Conversation not found
        HTTPException 403: Not authorized
    """
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Security: Check ownership based on conversation type
    if conversation.user_id:
        # User-owned conversation - require matching authenticated user
        if not current_user or conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
    else:
        # Guest conversation - require valid session that owns this conversation
        if not x_session_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session ID required for guest conversations"
            )
        session_data = await redis.hgetall(f"session:{x_session_id}")
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or expired session"
            )
        # Decode bytes if necessary
        session_conv_id = session_data.get('conversation_id') or session_data.get(b'conversation_id', b'').decode()
        if str(conversation_id) != session_conv_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to archive this conversation"
            )
    
    conversation.status = ConversationStatus.ARCHIVED
    await db.commit()
    
    return {"message": "Conversation archived successfully"}


@router.get("/export")
async def export_conversations(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Export all conversations for the current user as JSON.
    
    Note: Only authenticated users can export data.
    Guests must register to access export functionality.
    """
    # Security: Only authenticated users can export
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Export requires authentication. Please login or register."
        )
    
    conversations = []
    
    # Fetch all user conversations with messages
    user_id = current_user.id
    query = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.user_id == user_id)
        .where(Conversation.status != ConversationStatus.ARCHIVED) # Include active and ended
        .order_by(desc(Conversation.created_at))
    )
    result = await db.execute(query)
    conversations = result.scalars().all()

    # Build export data
    export_data = {
        "export_date": datetime.utcnow().isoformat(),
        "user_id": str(current_user.id),
        "conversations": []
    }

    for conv in conversations:
        conv_data = {
            "id": str(conv.id),
            "title": conv.title,
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
            "messages": []
        }
        for msg in conv.messages:
            conv_data["messages"].append({
                "role": msg.role.value,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
                "detected_emotion": msg.detected_emotion
            })
        export_data["conversations"].append(conv_data)

    # Return as file
    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
    filename = f"chat_history_{export_data['user_id']}.json"
    
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
