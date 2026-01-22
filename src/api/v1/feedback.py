"""
Feedback API router for message rating.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from src.database import get_db
from src.models.feedback import Feedback
from src.models.chat import Message
from src.schemas.feedback import FeedbackCreate, FeedbackResponse

router = APIRouter()


@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback_data: FeedbackCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit feedback for a message.
    
    Args:
        feedback_data: Feedback data (message_id, rating, comment)
        db: Database session
    
    Returns:
        FeedbackResponse: Created feedback entry
    
    Raises:
        HTTPException 404: Message not found
    """
    # Verify message exists
    result = await db.execute(
        select(Message).where(Message.id == feedback_data.message_id)
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Create feedback
    feedback = Feedback(
        id=uuid.uuid4(),
        message_id=feedback_data.message_id,
        rating=feedback_data.rating,
        comment=feedback_data.comment
    )
    
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    
    return feedback
