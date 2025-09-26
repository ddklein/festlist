import os
import time
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse

from app.models.schemas import (
    UploadResponse, OCRRequest, OCRResult, ArtistExtractionRequest, ImageAnalysisRequest,
    ArtistExtractionResponse, PlaylistCreationRequest, PlaylistCreationResponse,
    ErrorResponse, HealthResponse, ProcessingStatus
)
from app.services.ocr_service import OCRService
from app.services.artist_extraction_service import ArtistExtractionService
from app.utils.file_utils import (
    generate_file_id, is_allowed_file, validate_file_size,
    get_upload_path, save_upload_file, ensure_upload_directory
)
import structlog

logger = structlog.get_logger(__name__)

ocr_service = OCRService()

def get_artist_service():
    global _artist_service
    if '_artist_service' not in globals():
        global _artist_service
        _artist_service = ArtistExtractionService()
    return _artist_service

def get_spotify_service():
    from app.services.spotify_service import SpotifyService
    return SpotifyService()

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        service="festlist-api",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        if not file.content_type:
            raise HTTPException(status_code=400, detail="File content type not specified")

        if not is_allowed_file(file.filename, file.content_type):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Allowed types: JPEG, PNG, TIFF, BMP"
            )
        
        content = await file.read()
        file_size = len(content)
        
        if not validate_file_size(file_size):
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {10} MB"
            )
        
        file_id = generate_file_id()
        file_path = get_upload_path(file_id, file.filename)
        
        await file.seek(0)
        bytes_written = await save_upload_file(file, file_path)
        
        logger.info(
            "File uploaded successfully",
            file_id=file_id,
            filename=file.filename,
            size=bytes_written
        )
        
        background_tasks.add_task(cleanup_old_files)
        
        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            file_size=bytes_written,
            upload_time=datetime.now().isoformat(),
            status=ProcessingStatus.COMPLETED
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("File upload failed", error=str(e))
        raise HTTPException(status_code=500, detail="File upload failed")


@router.post("/ocr", response_model=OCRResult)
async def extract_text(request: OCRRequest):
    try:
        upload_dir = ensure_upload_directory()
        file_path = None
        
        for filename in os.listdir(upload_dir):
            if filename.startswith(request.file_id):
                file_path = os.path.join(upload_dir, filename)
                break
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        if not ocr_service.validate_image(file_path):
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        start_time = time.time()
        
        original_engine = ocr_service.ocr_engine
        if request.engine:
            ocr_service.ocr_engine = request.engine
        
        try:
            result = ocr_service.extract_text(file_path)
        finally:
            ocr_service.ocr_engine = original_engine
        
        processing_time = time.time() - start_time
        
        logger.info(
            "OCR completed",
            file_id=request.file_id,
            engine=result['engine'],
            text_length=len(result['text']),
            processing_time=processing_time
        )
        
        return OCRResult(
            text=result['text'],
            confidence=result['confidence'],
            engine=result['engine'],
            word_count=result['word_count'],
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("OCR processing failed", error=str(e), file_id=request.file_id)
        raise HTTPException(status_code=500, detail="OCR processing failed")


@router.post("/extract-artists", response_model=ArtistExtractionResponse)
async def extract_artists(request: ArtistExtractionRequest):
    try:
        start_time = time.time()
        
        result = await get_artist_service().extract_artists(
            text=request.text,
            use_ai=request.use_ai,
            confidence_threshold=request.confidence_threshold
        )
        
        processing_time = time.time() - start_time
        
        artists = []
        for artist_data in result['artists']:
            artists.append({
                "name": artist_data['name'],
                "confidence": artist_data['confidence'] * 100,
                "spotify_id": None,
                "genres": [],
                "popularity": None
            })
        
        logger.info(
            "Artist extraction completed",
            artists_found=len(artists),
            processing_time=processing_time
        )
        
        return ArtistExtractionResponse(
            artists=artists,
            total_found=len(artists),
            processing_time=processing_time,
            method=result['method']
        )
        
    except Exception as e:
        logger.error("Artist extraction failed", error=str(e))
        raise HTTPException(status_code=500, detail="Artist extraction failed")


@router.post("/analyze-image", response_model=ArtistExtractionResponse)
async def analyze_image(request: ImageAnalysisRequest):
    try:
        upload_dir = ensure_upload_directory()
        file_path = None

        for filename in os.listdir(upload_dir):
            if filename.startswith(request.file_id):
                file_path = os.path.join(upload_dir, filename)
                break

        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        if not ocr_service.validate_image(file_path):
            raise HTTPException(status_code=400, detail="Invalid image file")

        start_time = time.time()

        artist_service = get_artist_service()
        raw_artists = await artist_service.gemini_service.extract_artists_from_image(file_path)

        artists = [
            {
                "name": artist["name"],
                "confidence": artist["confidence"] * 100,
                "spotify_id": None,
                "genres": [],
                "popularity": None
            }
            for artist in raw_artists
            if artist["confidence"] >= request.confidence_threshold
        ]

        processing_time = time.time() - start_time

        logger.info(
            "Image analysis completed",
            file_id=request.file_id,
            artists_found=len(artists),
            processing_time=processing_time
        )

        return ArtistExtractionResponse(
            artists=artists,
            total_found=len(artists),
            processing_time=processing_time,
            method="gemini_vision"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Image analysis failed", error=str(e), file_id=request.file_id)
        raise HTTPException(status_code=500, detail="Image analysis failed")


@router.post("/create-playlist", response_model=PlaylistCreationResponse)
async def create_playlist(request: PlaylistCreationRequest):
    try:
        spotify_service = get_spotify_service()
        if not spotify_service.is_configured:
            raise HTTPException(
                status_code=503,
                detail="Spotify service not configured. Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET."
            )

        if not request.user_id:
            raise HTTPException(status_code=400, detail="User ID required for playlist creation")

        if not request.access_token:
            raise HTTPException(
                status_code=401,
                detail="Spotify authentication required. Please authenticate with Spotify first."
            )

        access_token = request.access_token
        
        start_time = time.time()
        
        result = await spotify_service.process_artists_to_playlist(
            artist_names=request.artists,
            playlist_name=request.playlist_name,
            user_id=request.user_id,
            access_token=access_token,
            tracks_per_artist=request.tracks_per_artist,
            playlist_description=request.playlist_description
        )
        
        processing_time = time.time() - start_time
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', 'Playlist creation failed'))
        
        tracks = []
        for track in result.get('tracks', []):
            tracks.append({
                "name": track['name'],
                "artist": track['artist'],
                "spotify_id": track['id'],
                "preview_url": track.get('preview_url'),
                "popularity": track.get('popularity', 0),
                "duration_ms": track.get('duration_ms', 0)
            })
        
        playlist_info = result['playlist_info']
        playlist = {
            "name": playlist_info['name'],
            "description": playlist_info.get('description'),
            "spotify_id": playlist_info['id'],
            "tracks": tracks,
            "total_tracks": len(tracks)
        }
        
        logger.info(
            "Playlist created successfully",
            playlist_id=playlist_info['id'],
            total_tracks=len(tracks),
            processing_time=processing_time
        )
        
        return PlaylistCreationResponse(
            playlist=playlist,
            successful_artists=result['successful_artists'],
            failed_artists=result['failed_artists'],
            total_tracks_added=len(tracks),
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Playlist creation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Playlist creation failed")


@router.get("/spotify/auth-url")
async def get_spotify_auth_url(state: Optional[str] = None):
    try:
        spotify_service = get_spotify_service()
        if not spotify_service.is_configured:
            raise HTTPException(
                status_code=503,
                detail="Spotify service not configured. Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET."
            )

        auth_url = spotify_service.get_auth_url(state=state)
        return {"auth_url": auth_url}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate Spotify auth URL", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate auth URL")


@router.post("/spotify/callback")
async def spotify_callback(code: str, state: Optional[str] = None):
    try:
        spotify_service = get_spotify_service()
        if not spotify_service.is_configured:
            raise HTTPException(
                status_code=503,
                detail="Spotify service not configured. Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET."
            )

        token_info = spotify_service.exchange_code_for_token(code, state)

        if not token_info:
            raise HTTPException(
                status_code=400,
                detail="Failed to exchange authorization code for access token"
            )

        access_token = token_info.get('access_token')
        user_info = spotify_service.get_user_info(access_token)

        if not user_info:
            raise HTTPException(
                status_code=400,
                detail="Failed to retrieve user information"
            )

        logger.info("Spotify OAuth callback successful", user_id=user_info.get('id'))

        return {
            "access_token": access_token,
            "refresh_token": token_info.get('refresh_token'),
            "expires_in": token_info.get('expires_in'),
            "token_type": token_info.get('token_type', 'Bearer'),
            "scope": token_info.get('scope'),
            "user": user_info
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Spotify OAuth callback failed", error=str(e))
        raise HTTPException(status_code=500, detail="OAuth callback failed")


async def cleanup_old_files():
    try:
        from app.utils.file_utils import cleanup_old_files
        upload_dir = ensure_upload_directory()
        deleted_count = cleanup_old_files(upload_dir, max_age_hours=24)
        logger.info("File cleanup completed", deleted_files=deleted_count)
    except Exception as e:
        logger.error("File cleanup failed", error=str(e))
