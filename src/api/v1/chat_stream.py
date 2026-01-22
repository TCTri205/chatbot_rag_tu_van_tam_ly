"""
Streaming chat endpoint for Server-Sent Events.
Provides real-time response streaming to improve perceived latency.
"""
import logging
import uuid
import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from src.database import get_db
from src.core.redis import get_redis
from src.core.safety import check_sos_keywords, get_crisis_response, load_sos_keywords, load_crisis_hotlines
from src.core.emotion import detect_emotion
from src.services.rag_service import rag_service, load_sys_prompt
from src.models.chat import Conversation, Message, MessageRole
from src.schemas.chat import ChatRequest
from src.middleware.rate_limit import limiter
from src.middleware.prompt_injection import validate_prompt_injection

router = APIRouter()
logger = logging.getLogger(__name__)


async def chat_event_stream(
    content: str,
    session_id: str,
    db: AsyncSession,
    redis
):
    """
    Async generator for Server-Sent Events streaming.
    
    Yields:
        SSE-formatted data chunks
    """
    try:
        # 1. Verify session
        session_key = f"session:{session_id}"
        session_data = await redis.hgetall(session_key)
        
        if not session_data:
            yield f"data: {json.dumps({'error': 'Session not found'})}\n\n"
            return
        
        conversation_id = session_data.get('conversation_id', '')
        if not conversation_id:
            yield f"data: {json.dumps({'error': 'Invalid session data'})}\n\n"
            return
        
        # 2. Safety check
        sos_keywords = await load_sos_keywords(db)
        is_crisis = check_sos_keywords(content, sos_keywords)
        
        if is_crisis:
            # Save user message with SOS flag
            user_message = Message(
                id=uuid.uuid4(),
                conversation_id=uuid.UUID(conversation_id),
                role=MessageRole.USER,
                content=content,
                is_sos=True
            )
            db.add(user_message)
            await db.commit()
            
            # Stream crisis response with DB hotlines
            hotlines = await load_crisis_hotlines(db)
            crisis_data = get_crisis_response(hotlines=hotlines)
            yield f"data: {json.dumps({'type': 'crisis', **crisis_data})}\n\n"
            yield "data: [DONE]\n\n"
            return
        
        # 3. Detect emotion
        emotion_tag = detect_emotion(content)
        
        # 4. Save user message
        user_message = Message(
            id=uuid.uuid4(),
            conversation_id=uuid.UUID(conversation_id),
            role=MessageRole.USER,
            content=content,
            detected_emotion=emotion_tag
        )
        db.add(user_message)
        await db.flush()  # Flush to get ID but don't commit yet
        
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
        
        # 6. RAG retrieval (non-streaming part)
        # [Round 2 Fix #3] Generate embedding once and reuse to save API call
        query_embedding = rag_service.generate_embedding(content, task_type="retrieval_query")
        search_results = rag_service.hybrid_search(content, top_k=10, query_embedding=query_embedding)
        top_results = rag_service.rerank_results(content, search_results, top_k=3)
        context, sources = rag_service.build_context(top_results)
        
        # Send sources first
        sources_data = {
            "type": "sources",
            "sources": sources,
            "emotion_tag": emotion_tag
        }
        yield f"data: {json.dumps(sources_data)}\n\n"
        
        # 7. Load custom sys_prompt from database
        custom_sys_prompt = await load_sys_prompt(db)
        
        # 8. Stream AI response generation
        full_response = ""
        async for chunk in rag_service.generate_response_stream(
            query=content,
            context=context,
            chat_history=chat_history,
            system_prompt=custom_sys_prompt
        ):
            full_response += chunk
            chunk_data = {
                "type": "chunk",
                "content": chunk
            }
            yield f"data: {json.dumps(chunk_data)}\n\n"
        
        # 8. Save bot response
        bot_message = Message(
            id=uuid.uuid4(),
            conversation_id=uuid.UUID(conversation_id),
            role=MessageRole.ASSISTANT,
            content=full_response,
            rag_sources=sources if sources else None
        )
        db.add(bot_message)
        await db.commit()
        
        # Send completion event with message ID
        done_data = {
            "type": "done",
            "message_id": str(bot_message.id),
            "created_at": bot_message.created_at.isoformat()
        }
        yield f"data: {json.dumps(done_data)}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Error in streaming chat: {str(e)}")
        error_data = {
            "type": "error",
            "message": "Đã xảy ra lỗi. Vui lòng thử lại."
        }
        yield f"data: {json.dumps(error_data)}\n\n"
        yield "data: [DONE]\n\n"


@router.post("/stream")
@limiter.limit("5/second")
async def send_message_stream(
    request: Request,
    body: ChatRequest = Depends(validate_prompt_injection),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    """
    Send a chat message and receive streaming AI response via Server-Sent Events.
    
    - Verifies session
    - Checks for crisis keywords
    - Retrieves relevant knowledge via RAG
    - Streams empathetic response in real-time
    - Saves conversation to database
    
    Returns streaming SSE response.
    
    Event types:
    - sources: RAG sources and metadata
    - chunk: Text chunk from AI response
    - done: Completion event with message ID
    - crisis: Crisis detected response
    - error: Error occurred
    """
    if not x_session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Session-ID header is required"
        )
    
    return StreamingResponse(
        chat_event_stream(body.content, x_session_id, db, redis),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable Nginx buffering
        }
    )
