"""
Rate limiting middleware using Firestore.
"""
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import structlog

from app.services.firebase_service import firebase_service

logger = structlog.get_logger(__name__)


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, detail: str = "Rate limit exceeded", remaining: int = 0):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"X-RateLimit-Remaining": str(remaining)}
        )


async def get_user_id_from_request(request: Request) -> Optional[str]:
    """
    Extract user ID from request.
    
    Tries multiple sources:
    1. Authorization header (Firebase ID token)
    2. Request body (user_id field)
    3. Query parameters (user_id)
    
    Args:
        request: FastAPI request object
        
    Returns:
        User ID or None if not found
    """
    # Try Authorization header first
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split('Bearer ')[1]
        try:
            decoded_token = firebase_service.verify_id_token(token)
            if decoded_token:
                return decoded_token.get('uid')
        except Exception as e:
            logger.warning("Failed to verify token", error=str(e))
    
    # Try request body
    try:
        if request.method in ['POST', 'PUT', 'PATCH']:
            # Store body for later use
            body = await request.body()
            request._body = body
            
            # Try to parse JSON
            import json
            try:
                body_data = json.loads(body.decode())
                if 'user_id' in body_data:
                    return body_data['user_id']
            except:
                pass
    except:
        pass
    
    # Try query parameters
    user_id = request.query_params.get('user_id')
    if user_id:
        return user_id
    
    return None


async def check_rate_limit(request: Request, limit: int = 3) -> tuple[bool, int, Optional[str]]:
    """
    Check if request should be rate limited.
    
    Args:
        request: FastAPI request object
        limit: Maximum requests per day
        
    Returns:
        Tuple of (is_allowed, remaining, user_id)
    """
    # Get user ID from request
    user_id = await get_user_id_from_request(request)
    
    if not user_id:
        # No user ID found - for now, allow the request
        # In production, you might want to require authentication
        logger.warning("No user ID found in request, allowing without rate limit")
        return True, limit, None
    
    # Check rate limit
    is_allowed, remaining = firebase_service.check_rate_limit(user_id, limit)
    
    return is_allowed, remaining, user_id


async def rate_limit_middleware(request: Request, call_next, limit: int = 3):
    """
    Middleware to enforce rate limiting on specific endpoints.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/handler
        limit: Maximum requests per day
        
    Returns:
        Response from next handler or rate limit error
    """
    # Only apply rate limiting to specific endpoints
    rate_limited_paths = [
        '/api/v1/analyze-image',
        '/api/v1/ocr',
    ]
    
    # Check if this path should be rate limited
    should_rate_limit = any(request.url.path.startswith(path) for path in rate_limited_paths)
    
    if not should_rate_limit:
        # Not a rate-limited endpoint, proceed normally
        response = await call_next(request)
        return response
    
    # Check rate limit
    is_allowed, remaining, user_id = await check_rate_limit(request, limit)
    
    if not is_allowed:
        logger.warning(
            "Rate limit exceeded",
            user_id=user_id,
            path=request.url.path,
            remaining=remaining
        )
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Daily image analysis limit exceeded. You can analyze up to 3 images per day.",
                "limit": limit,
                "remaining": remaining,
                "reset_info": "Limit resets at midnight UTC"
            },
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": str(remaining),
                "Retry-After": "86400"  # 24 hours in seconds
            }
        )
    
    # Proceed with request
    response = await call_next(request)
    
    # Add rate limit headers to response
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    
    # If request was successful and user_id exists, increment counter
    if response.status_code < 400 and user_id:
        firebase_service.increment_analysis_count(user_id)
        # Update remaining count in header
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining - 1))
    
    return response


def require_auth(request: Request) -> str:
    """
    Require authentication for a request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If authentication fails
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = auth_header.split('Bearer ')[1]
    
    try:
        decoded_token = firebase_service.verify_id_token(token)
        if not decoded_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return decoded_token.get('uid')
        
    except Exception as e:
        logger.error("Authentication failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )

