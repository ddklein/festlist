"""
Firebase/Firestore service for user management and data persistence.
"""
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore, auth
import structlog

logger = structlog.get_logger(__name__)


class FirebaseService:
    """Service for Firebase/Firestore operations."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Firebase Admin SDK."""
        if not FirebaseService._initialized:
            self._initialize_firebase()
            FirebaseService._initialized = True
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK with credentials."""
        try:
            # Check if already initialized
            if firebase_admin._apps:
                logger.info("Firebase already initialized")
                self.db = firestore.client()
                return
            
            # Try to get credentials from environment variable (JSON string or file path)
            cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
            cred_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
            
            if cred_json:
                # Parse JSON string
                import json
                cred_dict = json.loads(cred_json)
                cred = credentials.Certificate(cred_dict)
                logger.info("Initializing Firebase with JSON credentials")
            elif cred_path and os.path.exists(cred_path):
                # Use file path
                cred = credentials.Certificate(cred_path)
                logger.info("Initializing Firebase with credentials file", path=cred_path)
            else:
                # Use Application Default Credentials (for GCP deployment)
                cred = credentials.ApplicationDefault()
                logger.info("Initializing Firebase with Application Default Credentials")
            
            # Initialize Firebase
            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            logger.info("Firebase initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Firebase", error=str(e))
            # For development, we can continue without Firebase
            self.db = None
    
    @property
    def is_available(self) -> bool:
        """Check if Firebase is available."""
        return self.db is not None
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user document from Firestore.
        
        Args:
            user_id: User ID (typically from Firebase Auth)
            
        Returns:
            User document data or None if not found
        """
        if not self.is_available:
            logger.warning("Firebase not available")
            return None
        
        try:
            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                return user_doc.to_dict()
            return None
            
        except Exception as e:
            logger.error("Failed to get user", user_id=user_id, error=str(e))
            return None
    
    def create_or_update_user(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """
        Create or update user document in Firestore.
        
        Args:
            user_id: User ID
            user_data: User data to store
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available:
            logger.warning("Firebase not available")
            return False
        
        try:
            user_ref = self.db.collection('users').document(user_id)
            
            # Add timestamps
            now = datetime.utcnow()
            user_data['updated_at'] = now
            
            # Check if user exists
            if not user_ref.get().exists:
                user_data['created_at'] = now
                user_data['image_analyses_count'] = 0
                user_data['playlists_created_count'] = 0
            
            user_ref.set(user_data, merge=True)
            logger.info("User created/updated", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Failed to create/update user", user_id=user_id, error=str(e))
            return False
    
    def check_rate_limit(self, user_id: str, limit: int = 3) -> tuple[bool, int]:
        """
        Check if user has exceeded daily rate limit for image analysis.
        
        Args:
            user_id: User ID
            limit: Maximum number of analyses per day (default: 3)
            
        Returns:
            Tuple of (is_allowed, remaining_count)
        """
        if not self.is_available:
            logger.warning("Firebase not available, allowing request")
            return True, limit
        
        try:
            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                # New user, create document
                self.create_or_update_user(user_id, {})
                return True, limit - 1
            
            user_data = user_doc.to_dict()
            
            # Get today's date (UTC)
            today = datetime.utcnow().date()
            
            # Check last reset date
            last_reset = user_data.get('rate_limit_reset_date')
            if last_reset:
                # Convert Firestore timestamp to date
                if hasattr(last_reset, 'date'):
                    last_reset_date = last_reset.date()
                else:
                    last_reset_date = last_reset
                
                # Reset counter if it's a new day
                if last_reset_date < today:
                    user_ref.update({
                        'daily_analyses_count': 0,
                        'rate_limit_reset_date': datetime.utcnow()
                    })
                    return True, limit - 1
            else:
                # First time, set reset date
                user_ref.update({
                    'daily_analyses_count': 0,
                    'rate_limit_reset_date': datetime.utcnow()
                })
                return True, limit - 1
            
            # Check current count
            daily_count = user_data.get('daily_analyses_count', 0)
            
            if daily_count >= limit:
                logger.warning("Rate limit exceeded", user_id=user_id, count=daily_count)
                return False, 0
            
            remaining = limit - daily_count
            return True, remaining
            
        except Exception as e:
            logger.error("Failed to check rate limit", user_id=user_id, error=str(e))
            # On error, allow the request
            return True, limit
    
    def increment_analysis_count(self, user_id: str) -> bool:
        """
        Increment the daily analysis count for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            user_ref = self.db.collection('users').document(user_id)
            user_ref.update({
                'daily_analyses_count': firestore.Increment(1),
                'image_analyses_count': firestore.Increment(1)
            })
            logger.info("Analysis count incremented", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Failed to increment analysis count", user_id=user_id, error=str(e))
            return False
    
    def save_playlist(self, user_id: str, playlist_data: Dict[str, Any]) -> Optional[str]:
        """
        Save playlist information to Firestore.
        
        Args:
            user_id: User ID
            playlist_data: Playlist data to save
            
        Returns:
            Playlist document ID or None if failed
        """
        if not self.is_available:
            return None
        
        try:
            # Add metadata
            playlist_data['user_id'] = user_id
            playlist_data['created_at'] = datetime.utcnow()
            
            # Save to playlists collection
            playlist_ref = self.db.collection('playlists').add(playlist_data)
            playlist_id = playlist_ref[1].id
            
            # Update user's playlist count
            user_ref = self.db.collection('users').document(user_id)
            user_ref.update({
                'playlists_created_count': firestore.Increment(1)
            })
            
            logger.info("Playlist saved", user_id=user_id, playlist_id=playlist_id)
            return playlist_id
            
        except Exception as e:
            logger.error("Failed to save playlist", user_id=user_id, error=str(e))
            return None
    
    def get_user_playlists(self, user_id: str, limit: int = 10) -> list[Dict[str, Any]]:
        """
        Get user's playlists from Firestore.
        
        Args:
            user_id: User ID
            limit: Maximum number of playlists to return
            
        Returns:
            List of playlist documents
        """
        if not self.is_available:
            return []
        
        try:
            playlists_ref = self.db.collection('playlists')
            query = playlists_ref.where('user_id', '==', user_id).order_by(
                'created_at', direction=firestore.Query.DESCENDING
            ).limit(limit)
            
            playlists = []
            for doc in query.stream():
                playlist_data = doc.to_dict()
                playlist_data['id'] = doc.id
                playlists.append(playlist_data)
            
            return playlists
            
        except Exception as e:
            logger.error("Failed to get user playlists", user_id=user_id, error=str(e))
            return []
    
    def verify_id_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Firebase ID token.
        
        Args:
            id_token: Firebase ID token from client
            
        Returns:
            Decoded token data or None if invalid
        """
        if not self.is_available:
            return None
        
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            logger.error("Failed to verify ID token", error=str(e))
            return None


# Singleton instance
firebase_service = FirebaseService()

