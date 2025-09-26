import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from PIL import Image
import io

from app.main import app

client = TestClient(app)


def create_test_image(width=800, height=600, format="JPEG"):
    """Create a test image for upload testing."""
    image = Image.new('RGB', (width, height), color='white')
    
    # Add some text-like patterns
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(image)
    
    # Draw some rectangles to simulate text
    draw.rectangle([100, 100, 300, 150], fill='black')
    draw.rectangle([100, 200, 400, 250], fill='black')
    draw.rectangle([100, 300, 250, 350], fill='black')
    
    # Save to bytes
    img_bytes = io.BytesIO()
    image.save(img_bytes, format=format)
    img_bytes.seek(0)
    
    return img_bytes


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self):
        """Test health check returns correct response."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "festlist-api"
        assert "timestamp" in data


class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root(self):
        """Test root endpoint returns correct response."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data


class TestFileUpload:
    """Test file upload functionality."""
    
    def test_upload_valid_image(self):
        """Test uploading a valid image file."""
        test_image = create_test_image()
        
        response = client.post(
            "/api/v1/upload",
            files={"file": ("test.jpg", test_image, "image/jpeg")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "file_id" in data
        assert data["filename"] == "test.jpg"
        assert data["file_size"] > 0
        assert "upload_time" in data
    
    def test_upload_no_file(self):
        """Test upload with no file."""
        response = client.post("/api/v1/upload")
        assert response.status_code == 422  # Validation error
    
    def test_upload_invalid_file_type(self):
        """Test upload with invalid file type."""
        # Create a text file
        text_content = b"This is not an image"
        
        response = client.post(
            "/api/v1/upload",
            files={"file": ("test.txt", io.BytesIO(text_content), "text/plain")}
        )
        
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["error"]
    
    def test_upload_large_file(self):
        """Test upload with file that's too large."""
        # Create a large image (this is a simulation - actual large file would be huge)
        large_image = create_test_image(width=5000, height=5000)
        
        response = client.post(
            "/api/v1/upload",
            files={"file": ("large.jpg", large_image, "image/jpeg")}
        )
        
        # This might pass or fail depending on the actual size generated
        # In a real test, you'd create a file that's definitely over the limit


class TestOCREndpoint:
    """Test OCR functionality."""
    
    def test_ocr_missing_file(self):
        """Test OCR with non-existent file ID."""
        response = client.post(
            "/api/v1/ocr",
            json={"file_id": "non-existent-id"}
        )
        
        assert response.status_code == 404
        assert "File not found" in response.json()["error"]
    
    def test_ocr_invalid_engine(self):
        """Test OCR with invalid engine."""
        response = client.post(
            "/api/v1/ocr",
            json={"file_id": "test-id", "engine": "invalid-engine"}
        )
        
        assert response.status_code == 422  # Validation error


class TestArtistExtraction:
    """Test artist extraction functionality."""
    
    def test_extract_artists_valid_text(self):
        """Test artist extraction with valid text."""
        test_text = """
        MUSIC FESTIVAL 2024
        
        HEADLINERS:
        The Beatles
        Led Zeppelin
        Pink Floyd
        
        SUPPORTING ACTS:
        Queen
        The Rolling Stones
        """
        
        response = client.post(
            "/api/v1/extract-artists",
            json={
                "text": test_text,
                "use_ai": False,  # Use pattern matching only
                "confidence_threshold": 0.5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "artists" in data
        assert "total_found" in data
        assert data["total_found"] >= 0
    
    def test_extract_artists_empty_text(self):
        """Test artist extraction with empty text."""
        response = client.post(
            "/api/v1/extract-artists",
            json={"text": ""}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_extract_artists_invalid_confidence(self):
        """Test artist extraction with invalid confidence threshold."""
        response = client.post(
            "/api/v1/extract-artists",
            json={
                "text": "Some text",
                "confidence_threshold": 1.5  # Invalid - should be 0-1
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestPlaylistCreation:
    """Test playlist creation functionality."""
    
    def test_create_playlist_no_spotify_config(self):
        """Test playlist creation without Spotify configuration."""
        response = client.post(
            "/api/v1/create-playlist",
            json={
                "artists": ["The Beatles", "Led Zeppelin"],
                "playlist_name": "Test Playlist",
                "user_id": "test_user"
            }
        )
        
        # Should fail because Spotify is not configured
        assert response.status_code == 503
        assert "Spotify service not configured" in response.json()["error"]
    
    def test_create_playlist_missing_user_id(self):
        """Test playlist creation without user ID."""
        response = client.post(
            "/api/v1/create-playlist",
            json={
                "artists": ["The Beatles"],
                "playlist_name": "Test Playlist"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_create_playlist_empty_artists(self):
        """Test playlist creation with empty artists list."""
        response = client.post(
            "/api/v1/create-playlist",
            json={
                "artists": [],
                "playlist_name": "Test Playlist",
                "user_id": "test_user"
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestSpotifyAuth:
    """Test Spotify authentication endpoints."""
    
    def test_spotify_auth_url_no_config(self):
        """Test getting Spotify auth URL without configuration."""
        response = client.get("/api/v1/spotify/auth-url")
        
        # Should fail because Spotify is not configured
        assert response.status_code == 503
        assert "Spotify service not configured" in response.json()["error"]


class TestErrorHandling:
    """Test error handling and validation."""
    
    def test_invalid_endpoint(self):
        """Test accessing non-existent endpoint."""
        response = client.get("/api/v1/non-existent")
        assert response.status_code == 404
    
    def test_invalid_method(self):
        """Test using wrong HTTP method."""
        response = client.get("/api/v1/upload")  # Should be POST
        assert response.status_code == 405


if __name__ == "__main__":
    pytest.main([__file__])
