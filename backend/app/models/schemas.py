from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ProcessingStatus(str, Enum):
    """Status of processing operations."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OCRResult(BaseModel):
    """Result of OCR text extraction."""
    text: str = Field(..., description="Extracted text from the image")
    confidence: float = Field(..., ge=0, le=100, description="Confidence score (0-100)")
    engine: str = Field(..., description="OCR engine used (tesseract or google_vision)")
    word_count: int = Field(..., ge=0, description="Number of words extracted")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")


class Artist(BaseModel):
    """Artist information."""
    name: str = Field(..., description="Artist name")
    confidence: float = Field(..., ge=0, le=100, description="Confidence score for artist identification")
    spotify_id: Optional[str] = Field(None, description="Spotify artist ID")
    genres: List[str] = Field(default_factory=list, description="Artist genres")
    popularity: Optional[int] = Field(None, ge=0, le=100, description="Spotify popularity score")


class Track(BaseModel):
    """Track information."""
    name: str = Field(..., description="Track name")
    artist: str = Field(..., description="Artist name")
    spotify_id: str = Field(..., description="Spotify track ID")
    preview_url: Optional[str] = Field(None, description="Preview URL")
    popularity: int = Field(..., ge=0, le=100, description="Track popularity")
    duration_ms: int = Field(..., ge=0, description="Track duration in milliseconds")


class Playlist(BaseModel):
    """Spotify playlist information."""
    name: str = Field(..., description="Playlist name")
    description: Optional[str] = Field(None, description="Playlist description")
    spotify_id: Optional[str] = Field(None, description="Spotify playlist ID")
    tracks: List[Track] = Field(default_factory=list, description="Tracks in the playlist")
    total_tracks: int = Field(default=0, ge=0, description="Total number of tracks")


class UploadResponse(BaseModel):
    """Response for file upload."""
    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    upload_time: str = Field(..., description="Upload timestamp")
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)


class OCRRequest(BaseModel):
    """Request for OCR processing."""
    file_id: str = Field(..., description="File identifier from upload")
    engine: Optional[str] = Field("tesseract", description="OCR engine to use")
    
    @field_validator('engine')
    @classmethod
    def validate_engine(cls, v):
        if v not in ['tesseract', 'google_vision']:
            raise ValueError('Engine must be either "tesseract" or "google_vision"')
        return v


class ArtistExtractionRequest(BaseModel):
    """Request for artist extraction from text."""
    text: str = Field(..., min_length=1, description="Text to extract artists from")
    use_ai: bool = Field(default=True, description="Whether to use AI for extraction")
    confidence_threshold: float = Field(default=0.7, ge=0, le=1, description="Minimum confidence threshold")


class ImageAnalysisRequest(BaseModel):
    """Request for artist extraction directly from image."""
    file_id: str = Field(..., description="File identifier from upload")
    confidence_threshold: float = Field(default=0.7, ge=0, le=1, description="Minimum confidence threshold")


class ArtistExtractionResponse(BaseModel):
    """Response for artist extraction."""
    artists: List[Artist] = Field(..., description="Extracted artists")
    total_found: int = Field(..., ge=0, description="Total number of artists found")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    method: str = Field(..., description="Extraction method used")


class PlaylistCreationRequest(BaseModel):
    """Request for playlist creation."""
    artists: List[str] = Field(..., min_length=1, description="List of artist names")
    playlist_name: str = Field(..., min_length=1, description="Name for the playlist")
    playlist_description: Optional[str] = Field(None, description="Playlist description")
    tracks_per_artist: int = Field(default=3, ge=1, le=10, description="Number of top tracks per artist")
    user_id: Optional[str] = Field(None, description="Spotify user ID")
    access_token: Optional[str] = Field(None, description="Spotify access token")


class PlaylistCreationResponse(BaseModel):
    """Response for playlist creation."""
    playlist: Playlist = Field(..., description="Created playlist information")
    successful_artists: List[str] = Field(..., description="Artists successfully added")
    failed_artists: List[str] = Field(..., description="Artists that couldn't be found")
    total_tracks_added: int = Field(..., ge=0, description="Total tracks added to playlist")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: Optional[str] = Field(None, description="Service version")
    timestamp: str = Field(..., description="Response timestamp")


class ProcessingJob(BaseModel):
    """Processing job status."""
    job_id: str = Field(..., description="Job identifier")
    status: ProcessingStatus = Field(..., description="Current job status")
    progress: float = Field(default=0, ge=0, le=100, description="Progress percentage")
    message: Optional[str] = Field(None, description="Status message")
    result: Optional[Dict[str, Any]] = Field(None, description="Job result when completed")
    created_at: str = Field(..., description="Job creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    error: Optional[str] = Field(None, description="Error message if failed")
