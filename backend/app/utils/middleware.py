import time
from typing import Dict, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger(__name__)


class RateLimitMiddleware:
    """Simple in-memory rate limiting middleware."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed based on rate limit."""
        current_time = time.time()
        
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if current_time - req_time < 60
            ]
        else:
            self.requests[client_ip] = []
        
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return False
        
        self.requests[client_ip].append(current_time)
        return True


rate_limiter = RateLimitMiddleware()


async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware."""
    client_ip = request.client.host if request.client else "unknown"
    
    if not rate_limiter.is_allowed(client_ip):
        logger.warning("Rate limit exceeded", client_ip=client_ip)
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "detail": f"Maximum {rate_limiter.requests_per_minute} requests per minute allowed",
                "status_code": 429
            }
        )
    
    response = await call_next(request)
    return response


async def request_size_middleware(request: Request, call_next):
    """Middleware to check request size."""
    max_size = 15 * 1024 * 1024
    
    content_length = request.headers.get("content-length")
    if content_length:
        content_length = int(content_length)
        if content_length > max_size:
            logger.warning("Request too large", size=content_length, max_size=max_size)
            return JSONResponse(
                status_code=413,
                content={
                    "error": "Request too large",
                    "detail": f"Maximum request size is {max_size // 1024 // 1024}MB",
                    "status_code": 413
                }
            )
    
    response = await call_next(request)
    return response


async def security_headers_middleware(request: Request, call_next):
    """Add security headers to responses."""
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    return response


async def request_logging_middleware(request: Request, call_next):
    """Log all incoming requests and responses."""
    start_time = time.time()

    # Log request
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown")
    )

    try:
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log response
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=round(process_time, 3)
        )

        return response

    except Exception as e:
        # Calculate processing time for failed requests
        process_time = time.time() - start_time

        # Log error
        logger.error(
            "Request failed",
            method=request.method,
            url=str(request.url),
            error=str(e),
            error_type=type(e).__name__,
            process_time=round(process_time, 3)
        )

        raise
