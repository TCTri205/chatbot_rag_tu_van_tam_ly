"""
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from src.config import settings
from src.core.redis import init_redis, close_redis
from src.api.v1 import auth, health, chat, sessions, moods, feedback, conversations

# Phase 4: Security & Monitoring
from src.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from src.middleware.metrics import LoggingMetricsMiddleware, setup_metrics_logging
# Prompt injection protection now handled via dependency injection
# in chat endpoint (see src.api.v1.chat::validate_prompt_injection)
# This avoids ASGI message flow conflicts that caused RuntimeError

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    # CRITICAL: Disable automatic trailing slash redirects
    # This prevents FastAPI from redirecting /endpoint/ to /endpoint (or vice versa)
    # which causes CORS errors when redirect changes the origin
    redirect_slashes=False
)

# CORS Middleware - Must be first
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sprint 1 Week 2: Logging-based metrics middleware (replaces Prometheus)
app.add_middleware(LoggingMetricsMiddleware)

# Phase 4: Security Middleware
if settings.RATE_LIMIT_ENABLED:
    # Register rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Phase 4: Monitoring
# Note: Prometheus instrumentator was removed due to conflict with --proxy-headers flag
# causing ERR_CONTENT_LENGTH_MISMATCH errors. Consider alternative monitoring solutions
# such as custom middleware or different Prometheus integration methods.

# Include routers - health at /api (no versioning for infrastructure endpoints)
app.include_router(health.router, prefix="/api", tags=["Health"])

# Phase 1 routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])

# Phase 2 routers
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat"])
app.include_router(sessions.router, prefix=f"{settings.API_V1_STR}/sessions", tags=["Sessions"])
app.include_router(moods.router, prefix=f"{settings.API_V1_STR}/moods", tags=["Mood Tracking"])

# Sprint 1 Week 2: Streaming chat endpoint
from src.api.v1 import chat_stream
app.include_router(chat_stream.router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat - Streaming"])

# Phase 3 routers
app.include_router(feedback.router, prefix=f"{settings.API_V1_STR}/feedback", tags=["Feedback"])
app.include_router(conversations.router, prefix=f"{settings.API_V1_STR}/conversations", tags=["Conversations"])

# Relaxation exercises
from src.api.v1 import exercises
app.include_router(exercises.router, prefix=f"{settings.API_V1_STR}/exercises", tags=["Exercises"])

# Admin routers (Week 2)
from src.api.v1.admin import stats, knowledge, config, users
app.include_router(stats.router, prefix=f"{settings.API_V1_STR}/admin/stats", tags=["Admin - Stats"])
app.include_router(knowledge.router, prefix=f"{settings.API_V1_STR}/admin/knowledge", tags=["Admin - Knowledge"])
app.include_router(config.router, prefix=f"{settings.API_V1_STR}/admin/config", tags=["Admin - Config"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/admin/users", tags=["Admin - Users"])

# Phase 4: Metrics endpoint removed due to HTTP/1.1 keep-alive conflicts
# causing RuntimeError: Unexpected message received: http.request
# Consider implementing custom metrics middleware as alternative


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    await init_redis()


@app.on_event("shutdown")
async def shutdown_event():
    """Close connections on shutdown."""
    await close_redis()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Chatbot Tư Vấn Tâm Lý API",
        "docs": f"{settings.API_V1_STR}/docs",
        "version": "1.0.0-phase4",
        "security": {
            "rate_limiting": settings.RATE_LIMIT_ENABLED
        }
    }

