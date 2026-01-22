"""
Metrics API stub endpoint.
Removed to prevent HTTP/1.1 keep-alive conflicts.
"""
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter()


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics_endpoint():
    """
    Metrics endpoint disabled.
    
    Prometheus instrumentation was removed due to conflicts causing
    RuntimeError: Unexpected message received: http.request
    
    Returns empty response to prevent monitoring errors.
    """
    # Return empty plain text - prevents HTTP/1.1 keep-alive conflicts
    # that were causing ERR_CONTENT_LENGTH_MISMATCH and server instability
    return ""
