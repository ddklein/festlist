"""
User management API endpoints.
"""
from typing import List
from fastapi import APIRouter, HTTPException, Request, Depends, Header
from fastapi import status
import structlog

from app.models.user import (
    UserProfile,
    UserCreate,
    UserUpdate,
    UserStats,
    RateLimitInfo,
    PlaylistRecord
)
from app.services.firebase_service import firebase_service
from app.middleware.rate_limit import require_auth

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


def get_current_user_id(authorization: str = Header(None)) -> str:
    """
    Dependency to get current user ID from authorization header.
    
    Args:
        authorization: Authorization header
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If authentication fails
    """
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = authorization.split('Bearer ')[1]
    
    try:
        decoded_token = firebase_service.verify_id_token(token)
        if not decoded_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        return decoded_token.get('uid')
        
    except Exception as e:
        logger.error("Authentication failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


@router.post("/", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a new user profile.
    
    Requires authentication. User ID is extracted from the auth token.
    """
    try:
        # Check if user already exists
        existing_user = firebase_service.get_user(user_id)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )
        
        # Create user
        user_dict = user_data.model_dump(exclude_none=True)
        success = firebase_service.create_or_update_user(user_id, user_dict)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        # Get created user
        created_user = firebase_service.get_user(user_id)
        if not created_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User created but could not be retrieved"
            )
        
        created_user['user_id'] = user_id
        return UserProfile(**created_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create user", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get("/me", response_model=UserProfile)
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    """
    Get current user's profile.
    
    Requires authentication.
    """
    try:
        user_data = firebase_service.get_user(user_id)
        
        if not user_data:
            # User doesn't exist, create a basic profile
            firebase_service.create_or_update_user(user_id, {})
            user_data = firebase_service.get_user(user_id)
        
        user_data['user_id'] = user_id
        return UserProfile(**user_data)
        
    except Exception as e:
        logger.error("Failed to get user", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.patch("/me", response_model=UserProfile)
async def update_current_user(
    user_update: UserUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Update current user's profile.
    
    Requires authentication.
    """
    try:
        # Update user
        update_dict = user_update.model_dump(exclude_none=True)
        success = firebase_service.create_or_update_user(user_id, update_dict)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )
        
        # Get updated user
        updated_user = firebase_service.get_user(user_id)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User updated but could not be retrieved"
            )
        
        updated_user['user_id'] = user_id
        return UserProfile(**updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update user", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.get("/me/stats", response_model=UserStats)
async def get_user_stats(user_id: str = Depends(get_current_user_id)):
    """
    Get current user's statistics and rate limit info.
    
    Requires authentication.
    """
    try:
        user_data = firebase_service.get_user(user_id)
        
        if not user_data:
            # New user
            return UserStats(
                total_analyses=0,
                total_playlists=0,
                daily_analyses=0,
                rate_limit=RateLimitInfo(limit=3, remaining=3, is_exceeded=False)
            )
        
        # Check rate limit
        is_allowed, remaining = firebase_service.check_rate_limit(user_id, limit=3)
        
        return UserStats(
            total_analyses=user_data.get('image_analyses_count', 0),
            total_playlists=user_data.get('playlists_created_count', 0),
            daily_analyses=user_data.get('daily_analyses_count', 0),
            rate_limit=RateLimitInfo(
                limit=3,
                remaining=remaining,
                is_exceeded=not is_allowed
            )
        )
        
    except Exception as e:
        logger.error("Failed to get user stats", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )


@router.get("/me/playlists", response_model=List[PlaylistRecord])
async def get_user_playlists(
    limit: int = 10,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get current user's playlists.
    
    Requires authentication.
    """
    try:
        playlists = firebase_service.get_user_playlists(user_id, limit=limit)
        return [PlaylistRecord(**playlist) for playlist in playlists]
        
    except Exception as e:
        logger.error("Failed to get user playlists", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve playlists"
        )


@router.get("/me/rate-limit", response_model=RateLimitInfo)
async def get_rate_limit_info(user_id: str = Depends(get_current_user_id)):
    """
    Get current user's rate limit information.
    
    Requires authentication.
    """
    try:
        is_allowed, remaining = firebase_service.check_rate_limit(user_id, limit=3)
        
        return RateLimitInfo(
            limit=3,
            remaining=remaining,
            is_exceeded=not is_allowed
        )
        
    except Exception as e:
        logger.error("Failed to get rate limit info", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rate limit information"
        )

