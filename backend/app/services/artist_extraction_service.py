import os
import re
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from google.cloud import aiplatform
from google.auth import default
import structlog

from .gemini_service import GeminiService

logger = structlog.get_logger(__name__)


class ArtistExtractionService:
    """Service for extracting artist names from festival flyer text."""
    
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        self.location = "us-central1"

        self.gemini_service = GeminiService()

        if self.project_id:
            try:
                aiplatform.init(project=self.project_id, location=self.location)
                logger.info("Vertex AI initialized", project_id=self.project_id)
            except Exception as e:
                logger.error("Failed to initialize Vertex AI", error=str(e))
                self.project_id = None
        
        self.filter_words = {
            'festival', 'fest', 'music', 'stage', 'main', 'tent', 'arena', 'hall',
            'presents', 'featuring', 'with', 'special', 'guest', 'guests', 'live',
            'concert', 'show', 'performance', 'event', 'venue', 'location', 'date',
            'time', 'tickets', 'admission', 'price', 'cost', 'age', 'limit', 'door',
            'doors', 'open', 'start', 'end', 'saturday', 'sunday', 'monday', 'tuesday',
            'wednesday', 'thursday', 'friday', 'january', 'february', 'march', 'april',
            'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december',
            'am', 'pm', 'sponsored', 'by', 'presented', 'produced', 'organized'
        }
        
        self.artist_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
            r'\b[A-Z]+\b',
            r'\b[A-Z][a-z]+(?:\s+&\s+[A-Z][a-z]+)+\b',
            r'\b[A-Z][a-z]+(?:\s+and\s+[A-Z][a-z]+)+\b',
        ]
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text for processing.
        
        Args:
            text: Raw text from OCR
            
        Returns:
            Cleaned text
        """
        text = re.sub(r'\s+', ' ', text.strip())
        
        text = re.sub(r'\b\d{1,2}[:/]\d{2}\b', '', text)
        text = re.sub(r'\$\d+', '', text)
        text = re.sub(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', '', text)
        text = re.sub(r'\bwww\.\S+\b', '', text)
        text = re.sub(r'\b\S+@\S+\.\S+\b', '', text)
        
        return text.strip()
    
    def extract_with_patterns(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract potential artist names using regex patterns.
        
        Args:
            text: Cleaned text
            
        Returns:
            List of potential artists with confidence scores
        """
        potential_artists = []
        text_lines = text.split('\n')
        
        for line in text_lines:
            line = line.strip()
            if not line or len(line) < 2:
                continue
            
            for pattern in self.artist_patterns:
                matches = re.findall(pattern, line)
                
                for match in matches:
                    words = match.lower().split()
                    if any(word in self.filter_words for word in words):
                        continue
                    
                    if len(match) < 2 or len(match) > 50:
                        continue
                    
                    confidence = self.calculate_pattern_confidence(match, line, text)
                    
                    if confidence > 0.3:
                        potential_artists.append({
                            "name": match.strip(),
                            "confidence": confidence,
                            "method": "pattern_matching",
                            "context": line.strip()
                        })
        
        seen = set()
        unique_artists = []
        
        for artist in sorted(potential_artists, key=lambda x: x['confidence'], reverse=True):
            name_lower = artist['name'].lower()
            if name_lower not in seen:
                seen.add(name_lower)
                unique_artists.append(artist)
        
        return unique_artists[:20]
    
    def calculate_pattern_confidence(self, match: str, line: str, full_text: str) -> float:
        """
        Calculate confidence score for a pattern match.
        
        Args:
            match: The matched text
            line: The line containing the match
            full_text: The full text
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.5
        
        # Boost for proper capitalization
        if match[0].isupper() and any(c.islower() for c in match[1:]):
            confidence += 0.2
        
        # Boost for being on its own line
        if line.strip() == match.strip():
            confidence += 0.3
        
        # Boost for typical artist name length
        if 3 <= len(match.split()) <= 4:
            confidence += 0.1
        
        # Penalty for containing numbers
        if any(c.isdigit() for c in match):
            confidence -= 0.2
        
        # Boost for appearing multiple times
        occurrences = full_text.lower().count(match.lower())
        if occurrences > 1:
            confidence += min(0.2, occurrences * 0.05)
        
        return min(1.0, max(0.0, confidence))
    
    async def extract_with_vertex_ai(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract artist names using Vertex AI.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of extracted artists with confidence scores
        """
        if not self.project_id:
            logger.warning("Vertex AI not available, skipping AI extraction")
            return []
        
        try:
            prompt = f"""
            You are an expert at extracting artist and band names from festival flyer text.
            
            Please analyze the following text from a music festival flyer and extract all artist/band names.
            Return only a JSON array of objects with "name" and "confidence" fields.
            Confidence should be between 0.0 and 1.0.
            
            Rules:
            - Only extract actual artist/band names
            - Ignore venue names, dates, times, prices, and general festival information
            - Include solo artists, bands, DJs, and musical acts
            - Be conservative with confidence scores
            
            Text to analyze:
            {text}
            
            Response format:
            [
                {{"name": "Artist Name", "confidence": 0.95}},
                {{"name": "Band Name", "confidence": 0.87}}
            ]
            """
            
            from vertexai.language_models import TextGenerationModel
            
            model = TextGenerationModel.from_pretrained("text-bison@001")
            
            response = model.predict(
                prompt,
                temperature=0.1,
                max_output_tokens=1024,
                top_p=0.8,
                top_k=40
            )
            
            response_text = response.text.strip()
            
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                artists_data = json.loads(json_match.group())
                
                valid_artists = []
                for artist in artists_data:
                    if isinstance(artist, dict) and 'name' in artist and 'confidence' in artist:
                        name = str(artist['name']).strip()
                        confidence = float(artist['confidence'])
                        
                        if name and 0 <= confidence <= 1:
                            valid_artists.append({
                                "name": name,
                                "confidence": confidence,
                                "method": "vertex_ai",
                                "context": ""
                            })
                
                logger.info("Vertex AI extraction completed", artists_found=len(valid_artists))
                return valid_artists
            
        except Exception as e:
            logger.error("Vertex AI extraction failed", error=str(e))
        
        return []

    async def extract_with_gemini(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract artist names using Google Gemini.

        Args:
            text: Text to analyze

        Returns:
            List of extracted artists with confidence scores
        """
        if not self.gemini_service.is_available():
            logger.warning("Gemini service not available, skipping Gemini extraction")
            return []

        try:
            return await self.gemini_service.extract_artists_from_text(text)
        except Exception as e:
            logger.error("Gemini extraction failed", error=str(e))
            return []

    async def extract_artists(self, text: str, use_ai: bool = True, confidence_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Extract artist names from text using multiple methods.
        
        Args:
            text: Text to extract artists from
            use_ai: Whether to use AI extraction
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            Dictionary with extracted artists and metadata
        """
        try:
            logger.info("Starting artist extraction", text_length=len(text), use_ai=use_ai)
            
            cleaned_text = self.clean_text(text)
            
            pattern_artists = self.extract_with_patterns(cleaned_text)
            
            ai_artists = []
            if use_ai:
                ai_artists = await self.extract_with_gemini(cleaned_text)

                if not ai_artists:
                    ai_artists = await self.extract_with_vertex_ai(cleaned_text)
            
            all_artists = pattern_artists + ai_artists
            
            merged_artists = {}
            for artist in all_artists:
                name_key = artist['name'].lower()
                
                if name_key in merged_artists:
                    # Keep the one with higher confidence
                    if artist['confidence'] > merged_artists[name_key]['confidence']:
                        merged_artists[name_key] = artist
                else:
                    merged_artists[name_key] = artist
            
            final_artists = [
                artist for artist in merged_artists.values()
                if artist['confidence'] >= confidence_threshold
            ]
            
            final_artists.sort(key=lambda x: x['confidence'], reverse=True)
            
            logger.info(
                "Artist extraction completed",
                total_found=len(final_artists),
                pattern_count=len(pattern_artists),
                ai_count=len(ai_artists)
            )
            
            return {
                "artists": final_artists,
                "total_found": len(final_artists),
                "method": "combined" if use_ai and ai_artists else "pattern_matching",
                "pattern_results": len(pattern_artists),
                "ai_results": len(ai_artists)
            }
            
        except Exception as e:
            logger.error("Artist extraction failed", error=str(e))
            raise
