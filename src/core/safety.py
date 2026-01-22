"""
Safety module for crisis detection and response.
Implements SOS keyword detection and crisis intervention protocols.

Performance optimizations:
- [P2.1] SOS keywords caching with 5 minute TTL
"""
import re
import logging
import time
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.audit import SystemSetting

logger = logging.getLogger(__name__)

# [P2.1] SOS keywords cache
_sos_keywords_cache: Optional[List[str]] = None
_sos_keywords_cache_time: Optional[float] = None
_SOS_CACHE_TTL: int = 300  # 5 minutes TTL


# Default SOS keywords if database is not available
DEFAULT_SOS_KEYWORDS = [
    "tự tử", "tự sát", "chết", "tự hại", "kết thúc cuộc đời",
    "không muốn sống", "muốn chết", "giết mình", "tự kết liễu",
    "nhảy lầu", "cắt tay", "uống thuốc", "tự vẫn"
]

# Crisis hotlines for Vietnam
DEFAULT_CRISIS_HOTLINES = [
    {
        "name": "Đường dây nóng tâm lý - Trung tâm Phòng chống Tự tử",
        "number": "1800 599 913",
        "available": "24/7"
    },
    {
        "name": "Cấp cứu khẩn cấp",
        "number": "115",
        "available": "24/7"
    },
    {
        "name": "Tổng đài tư vấn tâm lý",
        "number": "1800 599 913",
        "available": "24/7"
    }
]

# Crisis hotlines cache
_crisis_hotlines_cache: Optional[List[Dict]] = None
_crisis_hotlines_cache_time: Optional[float] = None
_HOTLINES_CACHE_TTL: int = 300  # 5 minutes TTL


async def load_sos_keywords(db: AsyncSession) -> List[str]:
    """
    Load SOS keywords from database SystemSettings.
    [P2.1] Uses caching to avoid DB query on every request.
    
    Args:
        db: Database session
        
    Returns:
        List of SOS keywords
    """
    global _sos_keywords_cache, _sos_keywords_cache_time
    
    current_time = time.time()
    
    # [P2.1] Check cache validity
    if (_sos_keywords_cache is not None and
        _sos_keywords_cache_time is not None and
        current_time - _sos_keywords_cache_time < _SOS_CACHE_TTL):
        logger.debug("[P2.1] Using cached SOS keywords")
        return _sos_keywords_cache
    
    try:
        result = await db.execute(
            select(SystemSetting).where(SystemSetting.key == "sos_keywords")
        )
        setting = result.scalar_one_or_none()
        
        if setting and setting.value:
            # Parse CSV keywords
            keywords = [kw.strip() for kw in setting.value.split(",") if kw.strip()]
            logger.info(f"[P2.1] Loaded {len(keywords)} SOS keywords from database (cached)")
        else:
            logger.warning("[P2.1] SOS keywords not found in database, using defaults")
            keywords = DEFAULT_SOS_KEYWORDS
        
        # [P2.1] Cache the result
        _sos_keywords_cache = keywords
        _sos_keywords_cache_time = current_time
        return keywords
        
    except Exception as e:
        logger.error(f"Error loading SOS keywords: {str(e)}, using defaults")
        return DEFAULT_SOS_KEYWORDS


def check_sos_keywords(text: str, keywords: Optional[List[str]] = None) -> bool:
    """
    Check if text contains any SOS keywords indicating crisis situation.
    
    Args:
        text: User message to check
        keywords: Optional list of keywords (uses defaults if None)
        
    Returns:
        True if crisis keywords detected, False otherwise
    """
    if keywords is None:
        keywords = DEFAULT_SOS_KEYWORDS
    
    # Normalize text for better matching
    text_lower = text.lower()
    
    # Check for direct keyword matches
    for keyword in keywords:
        # Use word boundary regex for more accurate matching
        pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        if re.search(pattern, text_lower):
            logger.warning(f"SOS keyword detected: '{keyword}' in message")
            return True
    
    return False


async def load_crisis_hotlines(db: AsyncSession) -> List[Dict]:
    """
    Load crisis hotlines from database SystemSettings.
    Uses caching to avoid DB query on every request.
    
    Args:
        db: Database session
        
    Returns:
        List of crisis hotline dictionaries
    """
    global _crisis_hotlines_cache, _crisis_hotlines_cache_time
    
    current_time = time.time()
    
    # Check cache validity
    if (_crisis_hotlines_cache is not None and
        _crisis_hotlines_cache_time is not None and
        current_time - _crisis_hotlines_cache_time < _HOTLINES_CACHE_TTL):
        logger.debug("Using cached crisis hotlines")
        return _crisis_hotlines_cache
    
    try:
        import json
        result = await db.execute(
            select(SystemSetting).where(SystemSetting.key == "crisis_hotlines")
        )
        setting = result.scalar_one_or_none()
        
        if setting and setting.value:
            try:
                hotlines = json.loads(setting.value)
                _crisis_hotlines_cache = hotlines
                _crisis_hotlines_cache_time = current_time
                logger.info(f"Loaded {len(hotlines)} crisis hotlines from database")
                return hotlines
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in crisis_hotlines setting, using defaults")
                return DEFAULT_CRISIS_HOTLINES
                
        # No custom hotlines in DB, use defaults
        _crisis_hotlines_cache = DEFAULT_CRISIS_HOTLINES
        _crisis_hotlines_cache_time = current_time
        return DEFAULT_CRISIS_HOTLINES
        
    except Exception as e:
        logger.error(f"Failed to load crisis hotlines from database: {str(e)}")
        return DEFAULT_CRISIS_HOTLINES


def get_crisis_response(hotlines: Optional[List[Dict]] = None) -> Dict:
    """
    Generate crisis response message and hotline information.
    
    Args:
        hotlines: Optional list of hotlines (uses defaults if None)
    
    Returns:
        Dict containing crisis response message and hotlines
    """
    if hotlines is None:
        hotlines = DEFAULT_CRISIS_HOTLINES
    
    return {
        "is_crisis": True,
        "message": (
            "Chúng tôi rất lo lắng cho bạn. Những suy nghĩ này có thể rất đau đớn, "
            "nhưng xin hãy nhớ rằng bạn không đơn độc và có những người sẵn sàng hỗ trợ bạn. "
            "\n\nChúng tôi khuyến khích bạn liên hệ ngay với các đường dây nóng chuyên nghiệp bên dưới. "
            "Họ có chuyên gia được đào tạo để lắng nghe và giúp đỡ bạn vượt qua giai đoạn khó khăn này."
        ),
        "hotlines": hotlines,
        "additional_resources": [
            "Hãy nói chuyện với người thân, bạn bè mà bạn tin tưởng",
            "Tìm đến bác sĩ tâm lý hoặc bệnh viện có khoa tâm thần gần nhất",
            "Không tự ý ngừng dùng thuốc nếu đang điều trị"
        ]
    }


async def log_sos_detection(
    db: AsyncSession,
    user_id: str,
    message_id: str,
    content: str,
    detected_keywords: List[str]
) -> None:
    """
    Log SOS detection event to audit logs for monitoring.
    
    Args:
        db: Database session
        user_id: User ID who sent the message
        message_id: Message ID with SOS content
        content: Message content (truncated for privacy)
        detected_keywords: Keywords that triggered detection
    """
    try:
        from src.models.audit import AuditLog
        import uuid
        
        audit = AuditLog(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id) if user_id else None,
            action="SOS_DETECTED",
            ip_address=None,  # Can be added if available from request
            user_agent=f"Keywords: {', '.join(detected_keywords)}"
        )
        
        db.add(audit)
        await db.commit()
        logger.critical(f"SOS detection logged for user {user_id}, message {message_id}")
    except Exception as e:
        logger.error(f"Failed to log SOS detection: {str(e)}")
        # Don't raise - logging failure shouldn't block crisis response
