"""
Custom Metrics Middleware for monitoring without ASGI conflicts.

This module provides alternative monitoring via structured logging instead of 
Prometheus instrumentator which causes RuntimeError with uvicorn --proxy-headers.

Metrics are logged to JSON format for aggregation by external tools:
- Loki/Promtail
- CloudWatch Logs Insights
- ELK Stack
- Datadog
"""
import time
import logging
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("metrics")


class LoggingMetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs HTTP request metrics in JSON format.
    
    Logged metrics:
    - Request duration (latency)
    - HTTP method, path, status code
    - User agent
    - Response size
    - Timestamp
    
    Safe to use with uvicorn --proxy-headers (no ASGI conflicts).
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log metrics."""
        start_time = time.time()
        
        # Call next middleware/endpoint
        response = await call_next(request)
        
        # Calculate metrics
        duration = time.time() - start_time
        
        # Extract metadata
        method = request.method
        path = request.url.path
        status_code = response.status_code
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Get response size if available
        content_length = response.headers.get("content-length")
        response_size = int(content_length) if content_length else None
        
        # Log structured metrics
        metrics_dict = {
            "event": "http_request",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_seconds": round(duration, 4),
            "response_size_bytes": response_size,
            "user_agent": user_agent[:100],  # Truncate long UA strings
            "timestamp": time.time()
        }
        
        # Log as JSON for easy parsing
        logger.info(json.dumps(metrics_dict))
        
        # Add custom header with request duration
        response.headers["X-Response-time"] = str(round(duration * 1000, 2))
        
        return response


def setup_metrics_logging():
    """
    Configure metrics logger with JSON formatter.
    
    Call this during app startup to ensure metrics are properly formatted.
    """
    # Create dedicated metrics logger
    metrics_logger = logging.getLogger("metrics")
    metrics_logger.setLevel(logging.INFO)
    
    # Prevent propagation to root logger (avoid duplicate logs)
    metrics_logger.propagate = False
    
    # Create handler for metrics
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    
    # JSON formatter for structured logging
    formatter = logging.Formatter('%(message)s')  # Message already JSON
    handler.setFormatter(formatter)
    
    metrics_logger.addHandler(handler)
    
    return metrics_logger


# Application-level metrics tracking
class ApplicationMetrics:
    """
    In-memory metrics tracking for application-level stats.
    
    Can be exposed via /api/metrics endpoint for Grafana/Prometheus scraping.
    """
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.rag_queries = 0
        self.crisis_detections = 0
        self.total_response_time = 0.0
        
    def record_request(self, duration: float, status_code: int):
        """Record HTTP request metrics."""
        self.request_count += 1
        self.total_response_time += duration
        
        if status_code >= 500:
            self.error_count += 1
    
    def record_rag_query(self):
        """Record RAG query execution."""
        self.rag_queries += 1
    
    def record_crisis(self):
        """Record crisis detection event."""
        self.crisis_detections += 1
    
    def get_stats(self) -> dict:
        """Get current application statistics."""
        avg_response_time = (
            self.total_response_time / self.request_count 
            if self.request_count > 0 
            else 0
        )
        
        return {
            "requests_total": self.request_count,
            "errors_total": self.error_count,
            "rag_queries_total": self.rag_queries,
            "crisis_detections_total": self.crisis_detections,
            "avg_response_time_seconds": round(avg_response_time, 4),
            "error_rate": round(self.error_count / max(self.request_count, 1), 4)
        }
    
    def reset(self):
        """Reset all metrics (for testing)."""
        self.request_count = 0
        self.error_count = 0
        self.rag_queries = 0
        self.crisis_detections = 0
        self.total_response_time = 0.0


# Global metrics instance
app_metrics = ApplicationMetrics()
