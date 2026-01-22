"""
Prompt Injection Detection.

This module provides prompt injection detection via dependency injection
rather than middleware to avoid ASGI message flow conflicts.

Use validate_prompt_injection() as a dependency in endpoints that need protection.
The BaseHTTPMiddleware approach is deprecated due to issues with Starlette's
disconnect listener receiving unexpected http.request messages.
"""
import re
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.schemas.chat import ChatRequest


# Dangerous keywords that indicate prompt injection attempts
INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+instructions?",
    r"disregard\s+(previous|all)\s+instructions?",
    r"system\s+prompt",
    r"you\s+are\s+now",
    r"act\s+as\s+(DAN|DEV|developer|admin)",
    r"jailbreak",
    r"reveal\s+(your|the)\s+(prompt|system|instructions?)",
    r"forget\s+(everything|all|previous)",
    r"<\s*script",  # XSS attempts
    r"javascript:",
    r"onerror\s*=",
    r"eval\s*\(",
]

# Compile patterns for performance
COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in INJECTION_PATTERNS]


def detect_prompt_injection(text: str) -> tuple[bool, str | None]:
    """
    Scan text for prompt injection patterns.
    
    Args:
        text: User input to scan
        
    Returns:
        (is_malicious, matched_pattern)
    """
    if not text or len(text) > 5000:  # Also check length limit
        return True, "Input too long (max 5000 characters)"
    
    for pattern in COMPILED_PATTERNS:
        if pattern.search(text):
            return True, pattern.pattern
    
    return False, None


async def validate_prompt_injection(body: ChatRequest) -> ChatRequest:
    """
    FastAPI dependency to validate chat input for prompt injection attempts.
    
    This replaces the middleware approach to avoid ASGI message flow conflicts
    that caused RuntimeError: Unexpected message received: http.request
    
    Args:
        body: ChatRequest with content to validate
        
    Returns:
        Validated ChatRequest body
        
    Raises:
        HTTPException(400): If malicious input detected
    """
    from fastapi import HTTPException, status
    
    is_malicious, pattern = detect_prompt_injection(body.content)
    
    if is_malicious:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_INPUT",
                "message": "Đầu vào không hợp lệ. Vui lòng không cố gắng thao túng hệ thống.",
                "pattern": pattern if pattern else "Input validation failed"
            }
        )
    
    return body


class PromptInjectionMiddleware(BaseHTTPMiddleware):
    """
    DEPRECATED: This middleware causes RuntimeError due to ASGI receive callable issues.
    
    The custom receive() function (lines 87-90) only returns one http.request message,
    which breaks Starlette's disconnect listener that expects to receive disconnect signals.
    
    Use validate_prompt_injection() dependency instead.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Only check POST requests to chat endpoints
        if request.method == "POST" and "/chat" in request.url.path:
            try:
                # Read body
                body = await request.body()
                body_str = body.decode("utf-8")
                
                # Parse JSON to get content field
                import json
                try:
                    data = json.loads(body_str)
                    content = data.get("content", "")
                    
                    # Check for injection
                    is_malicious, pattern = detect_prompt_injection(content)
                    
                    if is_malicious:
                        return JSONResponse(
                            status_code=400,
                            content={
                                "error": "INVALID_INPUT",
                                "message": "Đầu vào không hợp lệ. Vui lòng không cố gắng thao túng hệ thống.",
                                "detail": f"Detected pattern: {pattern}" if pattern else "Input validation failed"
                            }
                        )
                except json.JSONDecodeError:
                    pass  # Let the endpoint handle invalid JSON
                
                # Reconstruct request with body
                async def receive():
                    return {"type": "http.request", "body": body}
                
                request._receive = receive
                
            except Exception as e:
                # Don't block request if scanning fails
                pass
        
        response = await call_next(request)
        return response
