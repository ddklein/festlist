import os
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import structlog

logger = structlog.get_logger(__name__)


class SpotifyService:
    """Service for interacting with Spotify API."""
    
    def __init__(self):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:3000/callback")

        self.client_credentials_manager = None
        self.sp_public = None
        self.is_configured = False

        if self.client_id and self.client_secret:
            try:
                self.client_credentials_manager = SpotifyClientCredentials(
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )

                self.sp_public = spotipy.Spotify(
                    client_credentials_manager=self.client_credentials_manager
                )

                self.is_configured = True
                logger.info("Spotify service initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize Spotify service", error=str(e))
        else:
            logger.warning("Spotify credentials not configured - Spotify features will be disabled")
    
    def get_user_spotify_client(self, access_token: str) -> spotipy.Spotify:
        """
        Get Spotify client with user authentication.
        
        Args:
            access_token: User's Spotify access token
            
        Returns:
            Authenticated Spotify client
        """
        return spotipy.Spotify(auth=access_token)
    
    def get_auth_url(self, state: str = None) -> str:
        """
        Get Spotify authorization URL for user authentication.

        Args:
            state: Optional state parameter for security

        Returns:
            Authorization URL
        """
        scope = "playlist-modify-public playlist-modify-private"

        auth_manager = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=scope,
            state=state
        )

        return auth_manager.get_authorize_url()

    def exchange_code_for_token(self, authorization_code: str, state: str = None) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for access token.

        Args:
            authorization_code: Authorization code from Spotify callback
            state: Optional state parameter for security

        Returns:
            Token information including access_token, refresh_token, expires_in, etc.
        """
        try:
            scope = "playlist-modify-public playlist-modify-private"

            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=scope,
                state=state
            )

            token_info = auth_manager.get_access_token(authorization_code)

            if token_info:
                logger.info("Successfully exchanged authorization code for access token")
                return token_info
            else:
                logger.error("Failed to exchange authorization code for access token")
                return None

        except Exception as e:
            logger.error("Error exchanging authorization code for token", error=str(e))
            return None

    def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from Spotify.

        Args:
            access_token: User's access token

        Returns:
            User information including user ID, display name, etc.
        """
        try:
            sp_user = self.get_user_spotify_client(access_token)
            user_info = sp_user.current_user()

            logger.info("Retrieved user info", user_id=user_info.get('id'))

            return {
                "id": user_info.get('id'),
                "display_name": user_info.get('display_name'),
                "email": user_info.get('email'),
                "country": user_info.get('country'),
                "followers": user_info.get('followers', {}).get('total', 0),
                "images": user_info.get('images', []),
                "external_urls": user_info.get('external_urls', {})
            }

        except Exception as e:
            logger.error("Failed to get user info", error=str(e))
            return None
    
    async def search_artist(self, artist_name: str) -> Optional[Dict[str, Any]]:
        """
        Search for an artist on Spotify.

        Args:
            artist_name: Name of the artist to search for

        Returns:
            Artist information or None if not found
        """
        if not self.is_configured:
            logger.error("Spotify service not configured")
            return None

        try:
            cleaned_name = artist_name.strip().replace("&", "and")
            
            results = self.sp_public.search(
                q=f'artist:"{cleaned_name}"',
                type='artist',
                limit=10
            )
            
            artists = results['artists']['items']
            
            if not artists:
                results = self.sp_public.search(
                    q=cleaned_name,
                    type='artist',
                    limit=10
                )
                artists = results['artists']['items']
            
            if artists:
                best_match = None
                best_score = 0
                
                for artist in artists:
                    score = self.calculate_artist_match_score(artist_name, artist['name'])
                    if score > best_score:
                        best_score = score
                        best_match = artist
                
                if best_match and best_score > 0.7:
                    logger.info(
                        "Artist found",
                        search_name=artist_name,
                        found_name=best_match['name'],
                        score=best_score
                    )
                    
                    return {
                        "id": best_match['id'],
                        "name": best_match['name'],
                        "genres": best_match.get('genres', []),
                        "popularity": best_match.get('popularity', 0),
                        "followers": best_match.get('followers', {}).get('total', 0),
                        "external_urls": best_match.get('external_urls', {}),
                        "images": best_match.get('images', [])
                    }
            
            logger.warning("Artist not found", artist_name=artist_name)
            return None
            
        except Exception as e:
            logger.error("Artist search failed", error=str(e), artist_name=artist_name)
            return None
    
    def calculate_artist_match_score(self, search_name: str, found_name: str) -> float:
        """
        Calculate similarity score between search name and found name.
        
        Args:
            search_name: Original search term
            found_name: Name found in Spotify
            
        Returns:
            Similarity score between 0 and 1
        """
        search_lower = search_name.lower().strip()
        found_lower = found_name.lower().strip()
        
        if search_lower == found_lower:
            return 1.0
        
        if search_lower in found_lower or found_lower in search_lower:
            return 0.9
        
        search_words = set(search_lower.split())
        found_words = set(found_lower.split())
        
        if not search_words or not found_words:
            return 0.0
        
        overlap = len(search_words.intersection(found_words))
        total = len(search_words.union(found_words))
        
        return overlap / total if total > 0 else 0.0
    
    async def get_artist_top_tracks(self, artist_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top tracks for an artist.
        
        Args:
            artist_id: Spotify artist ID
            limit: Maximum number of tracks to return
            
        Returns:
            List of track information
        """
        try:
            results = self.sp_public.artist_top_tracks(artist_id, country='US')
            tracks = results['tracks'][:limit]
            
            track_list = []
            for track in tracks:
                track_info = {
                    "id": track['id'],
                    "name": track['name'],
                    "artist": track['artists'][0]['name'],
                    "album": track['album']['name'],
                    "popularity": track.get('popularity', 0),
                    "duration_ms": track.get('duration_ms', 0),
                    "preview_url": track.get('preview_url'),
                    "external_urls": track.get('external_urls', {}),
                    "explicit": track.get('explicit', False)
                }
                track_list.append(track_info)
            
            logger.info("Retrieved top tracks", artist_id=artist_id, track_count=len(track_list))
            return track_list
            
        except Exception as e:
            logger.error("Failed to get top tracks", error=str(e), artist_id=artist_id)
            return []
    
    async def create_playlist(
        self,
        user_id: str,
        playlist_name: str,
        description: str = None,
        public: bool = True,
        access_token: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new Spotify playlist.
        
        Args:
            user_id: Spotify user ID
            playlist_name: Name for the playlist
            description: Optional playlist description
            public: Whether playlist should be public
            access_token: User's access token
            
        Returns:
            Playlist information or None if failed
        """
        try:
            if not access_token:
                logger.error("Access token required for playlist creation")
                return None
            
            sp_user = self.get_user_spotify_client(access_token)
            
            playlist = sp_user.user_playlist_create(
                user=user_id,
                name=playlist_name,
                public=public,
                description=description
            )
            
            logger.info("Playlist created", playlist_id=playlist['id'], name=playlist_name)
            
            return {
                "id": playlist['id'],
                "name": playlist['name'],
                "description": playlist.get('description', ''),
                "public": playlist.get('public', False),
                "external_urls": playlist.get('external_urls', {}),
                "tracks_total": playlist['tracks']['total']
            }
            
        except Exception as e:
            logger.error("Playlist creation failed", error=str(e), playlist_name=playlist_name)
            return None
    
    async def add_tracks_to_playlist(
        self,
        playlist_id: str,
        track_ids: List[str],
        access_token: str
    ) -> bool:
        """
        Add tracks to a Spotify playlist.
        
        Args:
            playlist_id: Spotify playlist ID
            track_ids: List of Spotify track IDs
            access_token: User's access token
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not track_ids:
                return True
            
            sp_user = self.get_user_spotify_client(access_token)
            
            batch_size = 100
            
            for i in range(0, len(track_ids), batch_size):
                batch = track_ids[i:i + batch_size]
                track_uris = [f"spotify:track:{track_id}" for track_id in batch]
                
                sp_user.playlist_add_items(playlist_id, track_uris)
                
                logger.info(
                    "Added tracks to playlist",
                    playlist_id=playlist_id,
                    batch_size=len(batch),
                    total_added=min(i + batch_size, len(track_ids))
                )
            
            return True
            
        except Exception as e:
            logger.error("Failed to add tracks to playlist", error=str(e), playlist_id=playlist_id)
            return False
    
    async def process_artists_to_playlist(
        self,
        artist_names: List[str],
        playlist_name: str,
        user_id: str,
        access_token: str,
        tracks_per_artist: int = 3,
        playlist_description: str = None
    ) -> Dict[str, Any]:
        """
        Process a list of artists and create a playlist with their top tracks.
        
        Args:
            artist_names: List of artist names
            playlist_name: Name for the new playlist
            user_id: Spotify user ID
            access_token: User's access token
            tracks_per_artist: Number of tracks per artist
            playlist_description: Optional playlist description
            
        Returns:
            Dictionary with results and statistics
        """
        try:
            logger.info(
                "Starting playlist creation process",
                artist_count=len(artist_names),
                tracks_per_artist=tracks_per_artist
            )
            
            successful_artists = []
            failed_artists = []
            all_tracks = []
            
            for artist_name in artist_names:
                artist_info = await self.search_artist(artist_name)
                
                if artist_info:
                    tracks = await self.get_artist_top_tracks(
                        artist_info['id'],
                        limit=tracks_per_artist
                    )
                    
                    if tracks:
                        all_tracks.extend(tracks)
                        successful_artists.append(artist_name)
                        logger.info(
                            "Artist processed successfully",
                            artist_name=artist_name,
                            tracks_found=len(tracks)
                        )
                    else:
                        failed_artists.append(artist_name)
                        logger.warning("No tracks found for artist", artist_name=artist_name)
                else:
                    failed_artists.append(artist_name)
                    logger.warning("Artist not found", artist_name=artist_name)
            
            if not all_tracks:
                logger.error("No tracks found for any artists")
                return {
                    "success": False,
                    "error": "No tracks found for any artists",
                    "successful_artists": successful_artists,
                    "failed_artists": failed_artists,
                    "total_tracks": 0
                }
            
            if not playlist_description:
                playlist_description = f"Festival playlist with {len(successful_artists)} artists"
            
            playlist_info = await self.create_playlist(
                user_id=user_id,
                playlist_name=playlist_name,
                description=playlist_description,
                access_token=access_token
            )
            
            if not playlist_info:
                logger.error("Failed to create playlist")
                return {
                    "success": False,
                    "error": "Failed to create playlist",
                    "successful_artists": successful_artists,
                    "failed_artists": failed_artists,
                    "total_tracks": len(all_tracks)
                }
            
            track_ids = [track['id'] for track in all_tracks]
            
            success = await self.add_tracks_to_playlist(
                playlist_id=playlist_info['id'],
                track_ids=track_ids,
                access_token=access_token
            )
            
            if not success:
                logger.error("Failed to add tracks to playlist")
                return {
                    "success": False,
                    "error": "Failed to add tracks to playlist",
                    "playlist_info": playlist_info,
                    "successful_artists": successful_artists,
                    "failed_artists": failed_artists,
                    "total_tracks": len(all_tracks)
                }
            
            logger.info(
                "Playlist creation completed successfully",
                playlist_id=playlist_info['id'],
                total_tracks=len(all_tracks),
                successful_artists=len(successful_artists),
                failed_artists=len(failed_artists)
            )
            
            return {
                "success": True,
                "playlist_info": playlist_info,
                "successful_artists": successful_artists,
                "failed_artists": failed_artists,
                "total_tracks": len(all_tracks),
                "tracks": all_tracks
            }
            
        except Exception as e:
            logger.error("Playlist creation process failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "successful_artists": [],
                "failed_artists": artist_names,
                "total_tracks": 0
            }
