"""
Admin statistics API endpoints.
Provides aggregated metrics for dashboard visualization.
"""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Dict, List

from src.database import get_db
from src.models.user import User
from src.models.chat import Message, Conversation, MessageRole
from src.models.mood import MoodEntry
from src.api.deps import require_admin

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/overview")
async def get_overview_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> Dict:
    """
    Get overview statistics for admin dashboard.
    
    Returns:
        Dashboard overview metrics
    """
    try:
        # Total users
        users_count = await db.scalar(select(func.count(User.id)))
        
        # Total conversations
        convs_count = await db.scalar(select(func.count(Conversation.id)))
        
        # Total messages
        msgs_count = await db.scalar(select(func.count(Message.id)))
        
        # SOS alerts (messages with is_sos=True)
        sos_count = await db.scalar(
            select(func.count(Message.id)).where(Message.is_sos == True)
        )
        
        # Active users (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        active_users = await db.scalar(
            select(func.count(func.distinct(Conversation.user_id)))
            .where(
                and_(
                    Conversation.created_at >= seven_days_ago,
                    Conversation.user_id.isnot(None)
                )
            )
        )
        
        # Average messages per conversation
        avg_msgs = await db.scalar(
            select(func.avg(
                select(func.count(Message.id))
                .where(Message.conversation_id == Conversation.id)
                .scalar_subquery()
            ))
        )
        
        return {
            "total_users": users_count or 0,
            "total_conversations": convs_count or 0,
            "total_messages": msgs_count or 0,
            "sos_alerts": sos_count or 0,
            "active_users_7d": active_users or 0,
            "avg_messages_per_conversation": round(float(avg_msgs or 0), 2)
        }
        
    except Exception as e:
        logger.error(f"Error fetching overview stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving statistics"
        )


@router.get("/word-cloud")
async def get_word_cloud_data(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> Dict:
    """
    Get word frequency data for word cloud generation.
    
    Args:
        limit: Number of top words to return
        
    Returns:
        Word frequency data
    """
    try:
        # Get recent user messages (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        result = await db.execute(
            select(Message.content)
            .where(
                and_(
                    Message.role == MessageRole.USER,
                    Message.created_at >= thirty_days_ago
                )
            )
            .limit(1000)  # Limit to avoid memory issues
        )
        messages = result.scalars().all()
        
        # Simple word frequency counter
        word_counts = {}
        stopwords = {'là', 'của', 'và', 'có', 'được', 'một', 'trong', 'với', 'cho', 'tôi', 'bạn', 'này', 'đó'}
        
        for msg in messages:
            if msg:
                words = msg.lower().split()
                for word in words:
                    # Basic filtering
                    word = word.strip('.,!?;:"()[]{}')
                    if len(word) > 2 and word not in stopwords:
                        word_counts[word] = word_counts.get(word, 0) + 1
        
        # Sort and get top words
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return {
            "words": [{"text": word, "value": count} for word, count in sorted_words],
            "total_messages_analyzed": len(messages)
        }
        
    except Exception as e:
        logger.error(f"Error generating word cloud data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating word cloud"
        )


@router.get("/mood-trends")
async def get_mood_trends(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
) -> Dict:
    """
    Get mood trends over time.
    
    Args:
        days: Number of days to analyze
        
    Returns:
        Mood distribution and trends
    """
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get mood distribution
        result = await db.execute(
            select(
                MoodEntry.mood_value,
                func.count(MoodEntry.id).label('count')
            )
            .where(MoodEntry.created_at >= start_date)
            .group_by(MoodEntry.mood_value)
        )
        
        mood_distribution = {row.mood_value: row.count for row in result}
        
        # Total mood entries
        total_entries = sum(mood_distribution.values())
        
        # Average mood value
        avg_mood = await db.scalar(
            select(func.avg(MoodEntry.mood_value))
            .where(MoodEntry.created_at >= start_date)
        )
        
        return {
            "mood_distribution": mood_distribution,
            "total_entries": total_entries,
            "average_mood": round(float(avg_mood or 0), 2),
            "period_days": days
        }
        
    except Exception as e:
        logger.error(f"Error fetching mood trends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving mood trends"
        )
