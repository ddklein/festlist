"""
User models for Firestore.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """User profile model."""
    user_id: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Usage statistics
    image_analyses_count: int = 0
    playlists_created_count: int = 0
    daily_analyses_count: int = 0
    
    # Rate limiting
    rate_limit_reset_date: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "firebase_user_123",
                "email": "user@example.com",
                "display_name": "John Doe",
                "image_analyses_count": 5,
                "playlists_created_count": 3,
                "daily_analyses_count": 2
            }
        }


class UserCreate(BaseModel):
    """Model for creating a new user."""
    email: Optional[str] = None
    display_name: Optional[str] = None
    photo_url: Optional[str] = None


class UserUpdate(BaseModel):
    """Model for updating user profile."""
    display_name: Optional[str] = None
    photo_url: Optional[str] = None


class PlaylistRecord(BaseModel):
    """Playlist record model."""
    id: Optional[str] = None
    user_id: str
    playlist_name: str
    spotify_playlist_id: Optional[str] = None
    artists: List[str]
    total_tracks: int
    created_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "firebase_user_123",
                "playlist_name": "Coachella 2024",
                "spotify_playlist_id": "spotify:playlist:abc123",
                "artists": ["Artist 1", "Artist 2", "Artist 3"],
                "total_tracks": 30
            }
        }


class RateLimitInfo(BaseModel):
    """Rate limit information."""
    limit: int = 3
    remaining: int
    reset_time: Optional[datetime] = None
    is_exceeded: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "limit": 3,
                "remaining": 1,
                "is_exceeded": False
            }
        }


class UserStats(BaseModel):
    """User statistics."""
    total_analyses: int = 0
    total_playlists: int = 0
    daily_analyses: int = 0
    rate_limit: RateLimitInfo
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_analyses": 15,
                "total_playlists": 5,
                "daily_analyses": 2,
                "rate_limit": {
                    "limit": 3,
                    "remaining": 1,
                    "is_exceeded": False
                }
            }
        }

