"""
Session management API router.
Handles session initialization and management.
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.core.redis import get_redis
from src.models.chat import Conversation, ConversationStatus
from src.models.user import User
from src.schemas.session import SessionInitRequest, SessionInitResponse, SessionInfo
from src.api.deps import get_current_user_optional

router = APIRouter()
logger = logging.getLogger(__name__)

# Session TTL: 24 hours
SESSION_TTL = 60 * 60 * 24


@router.post("/init", response_model=SessionInitResponse)
async def initialize_session(
    request: SessionInitRequest,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Initialize a new chat session.
    
    - Creates session in Redis
    - Conversation is created LAZILY on first message (to avoid spam empty conversations)
    - Returns session ID and greeting
    
    Works for both authenticated users and guests.
    """
    try:
        # SECURITY: User identity comes ONLY from JWT token
        if current_user:
            user_id = current_user.id
            logger.info(f"Initializing session for authenticated user {user_id}")
        else:
            logger.info("Initializing guest session")
            user_id = None
        
        # Create session ID
        session_id = uuid.uuid4()
        
        # LAZY CONVERSATION: Don't create conversation in DB yet
        # conversation_id = 'pending' means it will be created on first message
        # This avoids spam empty conversations when users just open the page
        
        # Store session in Redis with 'pending' conversation
        session_key = f"session:{session_id}"
        session_data = {
            "conversation_id": "pending",  # Will be created on first message
            "user_id": str(user_id) if user_id else "guest",
            "created_at": datetime.utcnow().isoformat()
        }
        
        await redis.hset(session_key, mapping=session_data)
        
        # TTL POLICY: Guest sessions expire after 24h
        if not user_id:
            await redis.expire(session_key, SESSION_TTL)
            logger.info(f"Guest session TTL set: {SESSION_TTL}s")
        
        # Generate greeting
        greeting = "Chào bạn! Tôi là trợ lý tâm lý AI. Tôi có thể giúp gì cho bạn hôm nay?"
        
        logger.info(f"Session initialized: {session_id} (conversation will be created on first message)")
        
        return SessionInitResponse(
            session_id=session_id,
            conversation_id=None,  # No conversation yet - will be created lazily
            greeting=greeting,
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Error initializing session: {str(e)}")
        logger.error(f"Traceback: {error_traceback}")
        
        # Provide more specific error details
        error_detail = "Failed to initialize session"
        if "redis" in str(e).lower():
            error_detail = "Session storage (Redis) unavailable. Please try again."
        elif "database" in str(e).lower() or "psycopg" in str(e).lower():
            error_detail = "Database connection error. Please try again."
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


@router.get("/info", response_model=SessionInfo)
async def get_session_info(
    x_session_id: str = Header(..., alias="X-Session-ID"),
    redis = Depends(get_redis)
):
    """
    Get information about the current session.
    """
    try:
        session_key = f"session:{x_session_id}"
        session_data = await redis.hgetall(session_key)
        
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or expired"
            )
        
        # Get TTL
        ttl = await redis.ttl(session_key)
        # Redis decode_responses=True, so data is already strings
        created_at = datetime.fromisoformat(session_data['created_at'])
        expires_at = created_at + timedelta(seconds=SESSION_TTL)
        
        user_id_str = session_data.get('user_id', '')
        user_id = uuid.UUID(user_id_str) if user_id_str != "guest" else None
        
        return SessionInfo(
            session_id=uuid.UUID(x_session_id),
            user_id=user_id,
            conversation_id=uuid.UUID(session_data['conversation_id']),
            is_active=ttl > 0,
            created_at=created_at,
            expires_at=expires_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving session information"
        )


@router.delete("/")
async def end_session(
    x_session_id: str = Header(..., alias="X-Session-ID"),
    redis = Depends(get_redis)
):
    """
    End a session (delete from Redis).
    """
    try:
        session_key = f"session:{x_session_id}"
        deleted = await redis.delete(session_key)
        
        if deleted == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        logger.info(f"Session ended: {x_session_id}")
        return {"message": "Session ended successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error ending session"
        )
