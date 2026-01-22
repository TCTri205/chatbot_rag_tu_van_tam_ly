"""
Mood tracking API router.
Handles mood logging and history retrieval.
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, Header, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from src.database import get_db
from src.core.redis import get_redis
from src.models.mood import MoodEntry
from src.schemas.mood import MoodCreate, MoodResponse
from src.api.deps import get_current_user_optional
from src.models.user import User
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=MoodResponse, status_code=status.HTTP_201_CREATED)
async def log_mood(
    mood_data: MoodCreate,
    x_session_id: str = Header(..., alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Log a mood entry for the current user.
    
    Security: JWT token takes priority over session for user identity.
    Only registered users can log moods.
    """
    try:
        # SECURITY: Prefer JWT token over session for user identity
        if current_user:
            user_id = current_user.id
            logger.info(f"Mood log: Using JWT user {user_id}")
        else:
            # Fallback to session for backwards compatibility
            session_key = f"session:{x_session_id}"
            session_data = await redis.hgetall(session_key)
            
            if not session_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found or expired"
                )
            
            user_id_str = session_data.get('user_id', '')
            
            if user_id_str == "guest":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Mood tracking is only available for registered users"
                )
            
            user_id = uuid.UUID(user_id_str)
        
        # Create mood entry
        mood_entry = MoodEntry(
            id=uuid.uuid4(),
            user_id=user_id,
            mood_value=mood_data.mood_value,
            mood_label=mood_data.mood_label,
            note=mood_data.note
        )
        
        db.add(mood_entry)
        await db.commit()
        await db.refresh(mood_entry)
        
        logger.info(f"Mood logged for user {user_id}: value={mood_data.mood_value}")
        
        return MoodResponse(
            id=mood_entry.id,
            mood_value=mood_entry.mood_value,
            mood_label=mood_entry.mood_label,
            note=mood_entry.note,
            created_at=mood_entry.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging mood: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error saving mood entry"
        )


@router.get("/history/", response_model=List[MoodResponse])
async def get_mood_history(
    days: int = Query(7, ge=1, le=90, description="Number of days of history to retrieve"),
    x_session_id: str = Header(..., alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get mood history for the current user.
    
    Security: JWT token takes priority over session for user identity.
    Returns raw mood entries (not aggregated).
    
    Args:
        days: Number of days to retrieve (1-90, default: 7)
    """
    try:
        # SECURITY: Prefer JWT token over session for user identity
        if current_user:
            user_id = current_user.id
            logger.info(f"Mood history: Using JWT user {user_id}")
        else:
            # Fallback to session for backwards compatibility
            session_key = f"session:{x_session_id}"
            session_data = await redis.hgetall(session_key)
            
            if not session_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found or expired"
                )
            
            user_id_str = session_data.get('user_id', '')
            
            if user_id_str == "guest":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Mood history is only available for registered users"
                )
            
            user_id = uuid.UUID(user_id_str)
        
        # Calculate datetime range for filtering
        end_datetime = datetime.utcnow()
        start_datetime = end_datetime - timedelta(days=days)
        
        # Query individual mood entries (NOT aggregated)
        result = await db.execute(
            select(MoodEntry)
            .where(
                and_(
                    MoodEntry.user_id == user_id,
                    MoodEntry.created_at >= start_datetime,
                    MoodEntry.created_at <= end_datetime
                )
            )
            .order_by(MoodEntry.created_at.desc())  # Newest first
        )
        
        entries = result.scalars().all()
        
        # Convert to response format (preserves all fields including notes)
        history = [
            MoodResponse(
                id=entry.id,
                mood_value=entry.mood_value,
                mood_label=entry.mood_label,
                note=entry.note,
                created_at=entry.created_at
            )
            for entry in entries
        ]
        
        logger.info(f"Retrieved {len(history)} mood entries for user {user_id_str}")
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving mood history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving mood history"
        )
