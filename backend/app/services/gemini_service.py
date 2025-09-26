import os
import json
import re
from typing import List, Dict, Any, Optional
from PIL import Image
import structlog

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GENAI_AVAILABLE = True
except ImportError as e:
    GENAI_AVAILABLE = False
    genai = None
    HarmCategory = None
    HarmBlockThreshold = None

logger = structlog.get_logger(__name__)


class GeminiService:
    """Service for using Google Gemini to extract artist names from festival flyer text."""
    
    def __init__(self):
        """Initialize the Gemini service."""
        self.api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        self.model = None



        if not GENAI_AVAILABLE:
            logger.warning("google-generativeai package not available, Gemini service disabled")
            return

        if self.api_key and self.api_key != "your-gemini-api-key-here":
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash')
                logger.info("Gemini service initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize Gemini service", error=str(e))
                self.model = None
        else:
            logger.warning("GOOGLE_GEMINI_API_KEY not found or still has placeholder value, Gemini service disabled")
    
    def is_available(self) -> bool:
        """Check if Gemini service is available."""
        return self.model is not None
    
    async def extract_artists_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract artist names from festival flyer text using Gemini.
        
        Args:
            text: The OCR text from a festival flyer
            
        Returns:
            List of dictionaries containing artist names and confidence scores
        """
        if not self.is_available():
            logger.warning("Gemini service not available")
            return []
        
        try:
            prompt = self._create_artist_extraction_prompt(text)
            
            safety_settings = None
            if HarmCategory and HarmBlockThreshold:
                safety_settings = {
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                }
            
            generation_config = None
            if genai:
                generation_config = genai.types.GenerationConfig(
                    temperature=0.1,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=4096,
                )

            response = self.model.generate_content(
                prompt,
                safety_settings=safety_settings,
                generation_config=generation_config
            )
            
            if response.text:
                return self._parse_gemini_response(response.text)
            else:
                logger.warning("Empty response from Gemini")
                return []
                
        except Exception as e:
            logger.error("Gemini artist extraction failed", error=str(e))
            return []
    
    def _create_artist_extraction_prompt(self, text: str) -> str:
        """Create a detailed prompt for artist extraction."""
        return f"""
You are an expert music industry professional specializing in festival lineups and artist identification. 

Analyze the following text extracted from a music festival flyer and identify ALL artist and band names mentioned. This includes:
- Headliner artists
- Supporting acts
- DJs and electronic music artists
- Bands of all genres
- Solo performers
- Musical groups and collectives

IMPORTANT RULES:
1. ONLY extract actual artist/performer names
2. IGNORE: venue names, festival names, dates, times, ticket prices, sponsors, food vendors, general information
3. IGNORE: words like "presents", "featuring", "with", "and", "vs", "b2b", "live", "dj set"
4. Include confidence score (0.0-1.0) based on how certain you are it's an artist name
5. Consider context clues like typography, positioning, and surrounding text

Return ONLY a valid JSON array in this exact format:
[
    {{"name": "Artist Name", "confidence": 0.95}},
    {{"name": "Band Name", "confidence": 0.87}},
    {{"name": "DJ Name", "confidence": 0.92}}
]

Text to analyze:
{text}

JSON Response:"""
    
    def _parse_gemini_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse Gemini's response and extract artist data."""
        try:
            cleaned_text = response_text.strip()
            
            json_match = re.search(r'\[.*?\]', cleaned_text, re.DOTALL)
            if not json_match:
                logger.warning("No JSON array found in Gemini response")
                return []
            
            json_str = json_match.group()
            artists_data = json.loads(json_str)
            
            valid_artists = []
            for artist in artists_data:
                if not isinstance(artist, dict):
                    continue
                    
                name = artist.get('name', '').strip()
                confidence = artist.get('confidence', 0.0)
                
                if not name or not isinstance(confidence, (int, float)):
                    continue
                    
                confidence = max(0.0, min(1.0, float(confidence)))
                
                if self._is_likely_artist_name(name):
                    valid_artists.append({
                        "name": name,
                        "confidence": confidence,
                        "method": "gemini",
                        "context": ""
                    })
            
            logger.info("Gemini extraction completed", artists_found=len(valid_artists))
            return valid_artists
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Gemini JSON response", error=str(e), response=response_text[:200])
            return []
        except Exception as e:
            logger.error("Error parsing Gemini response", error=str(e))
            return []
    
    def _is_likely_artist_name(self, name: str) -> bool:
        """Basic validation to filter out obvious non-artist names."""
        name_lower = name.lower().strip()
        
        excluded_terms = {
            'festival', 'music', 'stage', 'main', 'tent', 'area', 'zone',
            'tickets', 'price', 'cost', 'free', 'admission', 'entry',
            'food', 'drinks', 'bar', 'restaurant', 'vendor',
            'parking', 'shuttle', 'transport', 'bus',
            'saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
            'am', 'pm', 'time', 'schedule', 'lineup',
            'sponsored', 'presents', 'featuring', 'with'
        }
        
        if len(name) < 2 or name_lower in excluded_terms:
            return False
            
        if re.match(r'^\d{1,2}:\d{2}', name) or re.match(r'^\d{1,2}(am|pm)', name_lower):
            return False
            
        if re.match(r'^\$\d+', name) or 'dollar' in name_lower:
            return False
            
        return True

    async def extract_artists_from_image(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Extract artist names directly from a festival flyer image using Gemini Vision.

        Args:
            image_path: Path to the festival flyer image

        Returns:
            List of artist dictionaries with confidence scores
        """
        if not self.is_available():
            logger.warning("Gemini service not available")
            return []

        try:
            image = Image.open(image_path)

            prompt = self._create_image_analysis_prompt()

            safety_settings = None
            if HarmCategory and HarmBlockThreshold:
                safety_settings = {
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                }

            generation_config = None
            if genai:
                generation_config = genai.types.GenerationConfig(
                    temperature=0.1,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=4096,
                )

            response = self.model.generate_content(
                [prompt, image],
                safety_settings=safety_settings,
                generation_config=generation_config
            )

            if response.text:
                return self._parse_gemini_response(response.text)
            else:
                logger.warning("Empty response from Gemini image analysis")
                return []

        except Exception as e:
            logger.error("Gemini image analysis failed", error=str(e))
            return []

    def _create_image_analysis_prompt(self) -> str:
        return """
You are an expert music industry professional analyzing a festival flyer image.

Look at this festival flyer image and identify ALL artist and band names that are performing. This includes:
- Headliner artists (usually in large text)
- Supporting acts (medium-sized text)
- DJs and electronic music artists
- Bands of all genres
- Solo performers
- Musical groups and collectives

IMPORTANT RULES:
1. ONLY extract actual artist/performer names that you can see in the image
2. IGNORE: venue names, festival names, dates, times, ticket prices, sponsors, food vendors, general information
3. IGNORE: words like "presents", "featuring", "with", "and", "vs", "b2b", "live", "dj set"
4. Pay attention to text size and positioning - larger text usually indicates headliners
5. Include confidence score (0.0-1.0) based on:
   - How clearly you can read the text
   - Text size and prominence (larger = higher confidence)
   - Context clues that indicate it's an artist name
   - Typography and design elements

Return ONLY a valid JSON array in this exact format:
[
    {"name": "Artist Name", "confidence": 0.95},
    {"name": "Band Name", "confidence": 0.87},
    {"name": "DJ Name", "confidence": 0.92}
]

Analyze the image carefully and extract all visible artist names:"""
