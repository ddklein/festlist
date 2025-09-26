import os
import logging
from typing import Optional, Dict, Any
from PIL import Image
import cv2
import numpy as np
import pytesseract
from google.cloud import vision
from google.auth import default
import structlog

logger = structlog.get_logger(__name__)


class OCRService:
    """Service for performing OCR on festival flyer images."""
    
    def __init__(self):
        self.ocr_engine = os.getenv("OCR_ENGINE", "tesseract")
        self.tesseract_path = os.getenv("TESSERACT_PATH", "/usr/bin/tesseract")
        
        if self.ocr_engine == "tesseract":
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        
        self.vision_client = None
        if self.ocr_engine == "google_vision":
            try:
                self.vision_client = vision.ImageAnnotatorClient()
                logger.info("Google Vision API client initialized")
            except Exception as e:
                logger.error("Failed to initialize Google Vision API", error=str(e))
                # Fallback to Tesseract
                self.ocr_engine = "tesseract"
                logger.info("Falling back to Tesseract OCR")
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess image for better OCR results.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Preprocessed image as numpy array
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image from {image_path}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Morphological operations to clean up the image
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            logger.info("Image preprocessing completed", image_path=image_path)
            return cleaned
            
        except Exception as e:
            logger.error("Image preprocessing failed", error=str(e), image_path=image_path)
            raise
    
    def extract_text_tesseract(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text using Tesseract OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing extracted text and confidence scores
        """
        try:
            processed_image = self.preprocess_image(image_path)
            
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?@#$%^&*()_+-=[]{}|;:\'\"<>?/~` '
            
            text = pytesseract.image_to_string(processed_image, config=custom_config)
            
            data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
            
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            logger.info(
                "Tesseract OCR completed",
                image_path=image_path,
                text_length=len(text),
                avg_confidence=avg_confidence
            )
            
            return {
                "text": text.strip(),
                "confidence": avg_confidence,
                "engine": "tesseract",
                "word_count": len(text.split()),
                "detailed_data": data
            }
            
        except Exception as e:
            logger.error("Tesseract OCR failed", error=str(e), image_path=image_path)
            raise
    
    def extract_text_google_vision(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text using Google Vision API.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing extracted text and confidence scores
        """
        try:
            if not self.vision_client:
                raise ValueError("Google Vision client not initialized")
            
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            response = self.vision_client.text_detection(image=image)
            texts = response.text_annotations
            
            if response.error.message:
                raise Exception(f"Google Vision API error: {response.error.message}")
            
            if not texts:
                return {
                    "text": "",
                    "confidence": 0,
                    "engine": "google_vision",
                    "word_count": 0,
                    "detailed_data": []
                }
            
            full_text = texts[0].description
            
            confidences = []
            detailed_data = []
            
            for text in texts[1:]:
                if hasattr(text, 'confidence'):
                    confidences.append(text.confidence)
                
                detailed_data.append({
                    "text": text.description,
                    "confidence": getattr(text, 'confidence', 0),
                    "bounding_box": [
                        (vertex.x, vertex.y) for vertex in text.bounding_poly.vertices
                    ]
                })
            
            avg_confidence = (sum(confidences) / len(confidences) * 100) if confidences else 95
            
            logger.info(
                "Google Vision OCR completed",
                image_path=image_path,
                text_length=len(full_text),
                avg_confidence=avg_confidence
            )
            
            return {
                "text": full_text.strip(),
                "confidence": avg_confidence,
                "engine": "google_vision",
                "word_count": len(full_text.split()),
                "detailed_data": detailed_data
            }
            
        except Exception as e:
            logger.error("Google Vision OCR failed", error=str(e), image_path=image_path)
            raise
    
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text from image using the configured OCR engine.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            logger.info("Starting OCR extraction", image_path=image_path, engine=self.ocr_engine)
            
            if self.ocr_engine == "google_vision":
                return self.extract_text_google_vision(image_path)
            else:
                return self.extract_text_tesseract(image_path)
                
        except Exception as e:
            logger.error("OCR extraction failed", error=str(e), image_path=image_path)
            raise
    
    def validate_image(self, image_path: str) -> bool:
        """
        Validate that the image file is readable and suitable for OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            True if image is valid, False otherwise
        """
        try:
            if not os.path.exists(image_path):
                logger.error("Image file not found", image_path=image_path)
                return False
            
            with Image.open(image_path) as img:
                if img.format not in ['JPEG', 'PNG', 'TIFF', 'BMP']:
                    logger.error("Unsupported image format", format=img.format, image_path=image_path)
                    return False
                
                width, height = img.size
                if width < 100 or height < 100:
                    logger.error("Image too small", size=(width, height), image_path=image_path)
                    return False
                
                if width > 10000 or height > 10000:
                    logger.error("Image too large", size=(width, height), image_path=image_path)
                    return False
            
            logger.info("Image validation passed", image_path=image_path)
            return True
            
        except Exception as e:
            logger.error("Image validation failed", error=str(e), image_path=image_path)
            return False
