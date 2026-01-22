"""
Rate limiting middleware using slowapi.
Protects against abuse and DDoS attacks.
"""
import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse


# Initialize limiter with Redis backend for distributed rate limiting
# Use DB 1 for rate limiting (separate from main app cache in DB 0)
redis_base_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
rate_limit_redis_url = redis_base_url.replace("/0", "/1")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],  # Global default: 60 requests per minute
    storage_uri=rate_limit_redis_url,
    enabled=True
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.
    Returns user-friendly error message.
    """
    return JSONResponse(
        status_code=429,
        content={
            "error": "RATE_LIMIT_EXCEEDED",
            "message": "Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau.",
            "detail": f"Giới hạn: {exc.detail}"
        }
    )
