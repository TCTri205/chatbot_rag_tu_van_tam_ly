"""
Emotion detection utility.
Uses keyword-based detection for emotion classification.
"""
import re
from typing import Optional


# Emotion keyword mapping
EMOTION_KEYWORDS = {
    "sad": [
        "buồn", "chán", "thất vọng", "tuyệt vọng", "cô đơn", 
        "mệt mỏi", "kiệt sức", "chán nản", "sầu", "u buồn",
        "đau khổ", "khổ tâm", "nước mắt", "khóc"
    ],
    "angry": [
        "tức", "giận", "phẫn nộ", "bực", "cáu", "ghét", 
        "khó chịu", "bực mình", "điên tiết", "nổi điên"
    ],
    "anxious": [
        "lo lắng", "lo âu", "sợ", "sợ hãi", "hoảng sợ", "căng thẳng",
        "áp lực", "stress", "bồn chồn", "hồi hộp", "run rẩy",
        "hoang mang", "bất an", "day dứt"
    ],
    "happy": [
        "vui", "hạnh phúc", "vui vẻ", "phấn khởi", "hài lòng",
        "sướng", "thoải mái", "tốt", "vui mừng", "hân hoan",
        "tuyệt vời", "tích cực"
    ],
    "neutral": []  # Default fallback
}


def detect_emotion(text: str) -> Optional[str]:
    """
    Detect emotion from user message using keyword matching.
    
    Args:
        text: User message content
        
    Returns:
        Emotion tag (sad, angry, anxious, happy) or None if neutral
    """
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Score each emotion
    emotion_scores = {}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        if emotion == "neutral":
            continue
        
        score = 0
        for keyword in keywords:
            # Use word boundary to match whole words
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = len(re.findall(pattern, text_lower))
            score += matches
        
        if score > 0:
            emotion_scores[emotion] = score
    
    # Return emotion with highest score
    if emotion_scores:
        return max(emotion_scores, key=emotion_scores.get)
    
    return None  # Neutral
