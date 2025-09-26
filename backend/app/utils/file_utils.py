import os
import uuid
import hashlib
from typing import Optional, Tuple
from datetime import datetime
import aiofiles
from fastapi import UploadFile
import structlog

logger = structlog.get_logger(__name__)

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}
ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/png', 
    'image/tiff',
    'image/bmp'
}

MAX_FILE_SIZE = 10 * 1024 * 1024


def generate_file_id() -> str:
    return str(uuid.uuid4())


def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def is_allowed_file(filename: str, content_type: str) -> bool:
    """
    Check if file is allowed based on extension and MIME type.
    
    Args:
        filename: Original filename
        content_type: MIME type
        
    Returns:
        True if file is allowed, False otherwise
    """
    extension = get_file_extension(filename)
    return extension in ALLOWED_EXTENSIONS and content_type in ALLOWED_MIME_TYPES


def validate_file_size(file_size: int) -> bool:
    """
    Validate file size.
    
    Args:
        file_size: Size of file in bytes
        
    Returns:
        True if size is valid, False otherwise
    """
    return 0 < file_size <= MAX_FILE_SIZE


def get_upload_path(file_id: str, original_filename: str) -> str:
    """
    Generate upload path for file.
    
    Args:
        file_id: Unique file identifier
        original_filename: Original filename
        
    Returns:
        Path where file should be saved
    """
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    extension = get_file_extension(original_filename)
    filename = f"{file_id}{extension}"
    
    return os.path.join(upload_dir, filename)


async def save_upload_file(upload_file: UploadFile, file_path: str) -> int:
    """
    Save uploaded file to disk.
    
    Args:
        upload_file: FastAPI UploadFile object
        file_path: Path where to save the file
        
    Returns:
        Number of bytes written
    """
    try:
        bytes_written = 0
        
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await upload_file.read(8192):
                await f.write(chunk)
                bytes_written += len(chunk)
        
        logger.info("File saved successfully", file_path=file_path, bytes_written=bytes_written)
        return bytes_written
        
    except Exception as e:
        logger.error("Failed to save file", error=str(e), file_path=file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        raise


def calculate_file_hash(file_path: str) -> str:
    """
    Calculate SHA-256 hash of file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Hexadecimal hash string
    """
    try:
        hash_sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
        
    except Exception as e:
        logger.error("Failed to calculate file hash", error=str(e), file_path=file_path)
        raise


def get_file_info(file_path: str) -> dict:
    """
    Get file information.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with file information
    """
    try:
        stat = os.stat(file_path)
        
        return {
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "hash": calculate_file_hash(file_path)
        }
        
    except Exception as e:
        logger.error("Failed to get file info", error=str(e), file_path=file_path)
        raise


def cleanup_old_files(upload_dir: str, max_age_hours: int = 24) -> int:
    """
    Clean up old uploaded files.
    
    Args:
        upload_dir: Directory containing uploaded files
        max_age_hours: Maximum age of files to keep (in hours)
        
    Returns:
        Number of files deleted
    """
    try:
        if not os.path.exists(upload_dir):
            return 0
        
        current_time = datetime.now().timestamp()
        max_age_seconds = max_age_hours * 3600
        deleted_count = 0
        
        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                
                if file_age > max_age_seconds:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info("Deleted old file", file_path=file_path, age_hours=file_age/3600)
                    except Exception as e:
                        logger.error("Failed to delete old file", error=str(e), file_path=file_path)
        
        logger.info("Cleanup completed", deleted_count=deleted_count)
        return deleted_count
        
    except Exception as e:
        logger.error("Cleanup failed", error=str(e), upload_dir=upload_dir)
        return 0


def ensure_upload_directory() -> str:
    """
    Ensure upload directory exists and return its path.
    
    Returns:
        Path to upload directory
    """
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir
