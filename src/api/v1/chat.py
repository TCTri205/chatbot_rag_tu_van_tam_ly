"""
Chat API router with RAG integration.
Handles chat messages, safety checks, and response generation.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from src.database import get_db
from src.core.redis import get_redis
from src.core.safety import check_sos_keywords, get_crisis_response, load_sos_keywords, log_sos_detection
from src.core.emotion import detect_emotion
from src.services.rag_service import rag_service
from src.models.chat import Conversation, ConversationStatus, Message, MessageRole
from src.schemas.chat import (
    ChatRequest,
    ChatResponse,
    CrisisResponse,
    MessageHistory,
    ChatHistoryResponse,
    RAGSource
)
from src.middleware.rate_limit import limiter
from src.middleware.prompt_injection import validate_prompt_injection
from src.api.deps import get_current_user_optional
from src.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=ChatResponse | CrisisResponse)
@limiter.limit("5/second")  # Phase 4: Rate limiting - 5 requests per second
async def send_message(
    request: Request,  # MUST be named 'request' for slowapi
    body: ChatRequest = Depends(validate_prompt_injection),  # Prompt injection protection
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    """
    Send a chat message and receive AI response.
    
    - Verifies session
    - Checks for crisis keywords
    - Retrieves relevant knowledge via RAG
    - Generates empathetic response
    - Saves conversation to database
    
    Returns ChatResponse or CrisisResponse if crisis detected.
    """
    try:
        # 1. Verify session
        if not x_session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="X-Session-ID header is required"
            )
        
        # Get session from Redis
        session_key = f"session:{x_session_id}"
        session_data = await redis.hgetall(session_key)
        
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or expired. Please initialize a new session."
            )
        
        # Get conversation_id from session
        conversation_id = session_data.get('conversation_id', '')
        user_id_str = session_data.get('user_id', 'guest')
        
        # LAZY CONVERSATION CREATION: If 'pending', create conversation now (on first message)
        if conversation_id == 'pending' or not conversation_id:
            logger.info(f"📝 Creating conversation lazily on first message for session {x_session_id}")
            
            # Determine user_id
            if user_id_str != 'guest':
                user_id = uuid.UUID(user_id_str)
                conversation_title = "New Conversation"
            else:
                user_id = None
                conversation_title = "Guest Conversation"
            
            # Create conversation in PostgreSQL
            new_conversation_id = uuid.uuid4()
            conversation = Conversation(
                id=new_conversation_id,
                user_id=user_id,
                title=conversation_title,
                status=ConversationStatus.ACTIVE
            )
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)
            
            # Update Redis session with real conversation_id
            await redis.hset(session_key, "conversation_id", str(new_conversation_id))
            conversation_id = str(new_conversation_id)
            
            logger.info(f"✅ Lazy conversation created: {conversation_id} for user {user_id_str}")
        
        # 2. Safety check - Load SOS keywords and check
        sos_keywords = await load_sos_keywords(db)
        is_crisis = check_sos_keywords(body.content, sos_keywords)
        
        if is_crisis:
            # Save user message with SOS flag
            user_message = Message(
                id=uuid.uuid4(),
                conversation_id=uuid.UUID(conversation_id),
                role=MessageRole.USER,
                content=body.content,
                is_sos=True
            )
            db.add(user_message)
            await db.commit()
            
            # Load dynamic crisis hotlines from DB
            from src.core.safety import load_crisis_hotlines
            hotlines = await load_crisis_hotlines(db)
            
            # Return crisis response with dynamic hotlines
            crisis_data = get_crisis_response(hotlines=hotlines)
            logger.warning(f"Crisis detected in session {x_session_id}")
            
            # Log SOS detection for audit trail
            user_id_str = session_data.get('user_id', 'guest')
            await log_sos_detection(
                db=db,
                user_id=user_id_str if user_id_str != 'guest' else None,
                message_id=str(user_message.id),
                content=body.content[:100],  # Truncate for privacy
                detected_keywords=[kw for kw in sos_keywords if kw.lower() in body.content.lower()]
            )
            
            crisis_response = CrisisResponse(**crisis_data)
            crisis_json = crisis_response.model_dump_json()
            crisis_size = len(crisis_json.encode('utf-8'))
            
            return JSONResponse(
                content=crisis_response.model_dump(),
                status_code=200,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "Content-Length": str(crisis_size)
                }
            )
        
        # 3. Detect emotion from user message
        emotion_tag = detect_emotion(body.content)
        if emotion_tag:
            logger.info(f"Detected emotion: {emotion_tag}")
        
        # 4. Save user message with detected emotion
        user_message = Message(
            id=uuid.uuid4(),
            conversation_id=uuid.UUID(conversation_id),
            role=MessageRole.USER,
            content=body.content,
            detected_emotion=emotion_tag
        )
        db.add(user_message)
        
        # 5. Load chat history
        history_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == uuid.UUID(conversation_id))
            .order_by(desc(Message.created_at))
            .limit(10)
        )
        history_messages = history_result.scalars().all()
        
        # Format history for RAG
        chat_history = [
            {"role": msg.role.value, "content": msg.content}
            for msg in reversed(history_messages)
        ]
        
        # 5. RAG Query
        logger.info(f"Processing RAG query: {body.content[:50]}...")
        response_text, sources_data = await rag_service.rag_query(
            query=body.content,
            chat_history=chat_history,
            top_k=3,
            db=db
        )
        
        # 6. Convert sources to schema (ensure always list, never None)
        rag_sources = [
            RAGSource(**source) for source in (sources_data if sources_data else [])
        ]
        
        # 7. Save bot response
        bot_message = Message(
            id=uuid.uuid4(),
            conversation_id=uuid.UUID(conversation_id),
            role=MessageRole.ASSISTANT,
            content=response_text,
            rag_sources=sources_data if sources_data else None
        )
        db.add(bot_message)
        await db.commit()
        await db.refresh(bot_message)
        
        # 8. Build response with explicit JSON-safe serialization
        # CRITICAL: Explicitly convert UUID and datetime to prevent frontend parsing errors
        response_dict = {
            "message_id": str(bot_message.id),  # UUID -> string
            "conversation_id": conversation_id,  # Include for lazy creation - frontend needs this
            "role": "assistant",
            "content": bot_message.content,
            "emotion_tag": emotion_tag,  # Can be None, that's OK
            "sources": [
                {
                    "title": source.title,
                    "page": source.page,
                    "content_snippet": source.content_snippet
                }
                for source in rag_sources
            ],  # Always array, never null
            "is_crisis": False,
            "created_at": bot_message.created_at.isoformat()  # datetime -> ISO string
        }
        
        logger.info(f"✅ Chat response ready: msgId={str(bot_message.id)[:8]}..., "
                   f"content={len(bot_message.content)} chars, sources={len(rag_sources)}")
        logger.debug(f"📤 Response dict: {response_dict}")
        
        # Return JSONResponse with explicit serialization to ensure compatibility
        return JSONResponse(
            content=response_dict,
            status_code=200,
            headers={
                "Content-Type": "application/json; charset=utf-8"
            }
        )

        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing chat message"
        )


@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get chat history for a conversation with pagination.
    
    Args:
        conversation_id: UUID of the conversation
        limit: Number of messages to return (max 100)
        offset: Number of messages to skip
    
    Security:
        Requires session ownership or authenticated user ownership.
    """
    try:
        # Security: Require session or auth
        if not current_user and not x_session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Validate conversation_id
        try:
            conv_uuid = uuid.UUID(conversation_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conversation ID format"
            )
        
        # Security: Validate ownership based on authentication method
        if current_user:
            # CRITICAL: Authenticated users can only access their own conversations
            conv_result = await db.execute(
                select(Conversation).where(Conversation.id == conv_uuid)
            )
            conversation = conv_result.scalar_one_or_none()
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
            # Check that the conversation belongs to this user
            if conversation.user_id != current_user.id:
                logger.warning(f"Access denied: User {current_user.id} tried to access conversation {conv_uuid}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this conversation"
                )
        elif x_session_id:
            # Guest users: Validate session owns this conversation
            session_data = await redis.hgetall(f"session:{x_session_id}")
            if not session_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired session"
                )
            session_conv_id = session_data.get('conversation_id', '')
            if session_conv_id != conversation_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this conversation"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Limit max messages
        limit = min(limit, 100)
        
        # Get total count using COUNT(*) for efficiency
        count_result = await db.execute(
            select(func.count(Message.id))
            .where(Message.conversation_id == conv_uuid)
        )
        total = count_result.scalar() or 0
        
        # Get messages with pagination
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conv_uuid)
            .order_by(Message.created_at)
            .offset(offset)
            .limit(limit)
        )
        messages = result.scalars().all()
        
        # Convert to response schema (include rag_sources for history reload)
        history_items = [
            MessageHistory(
                id=msg.id,
                role=msg.role.value,
                content=msg.content,
                created_at=msg.created_at,
                is_sos=msg.is_sos,
                rag_sources=msg.rag_sources  # Preserve sources on page reload
            )
            for msg in messages
        ]
        
        return ChatHistoryResponse(
            messages=history_items,
            total=total,
            has_more=offset + len(messages) < total
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving chat history"
        )
