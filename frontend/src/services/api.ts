import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
});

export interface UploadResponse {
  file_id: string;
  filename: string;
  file_size: number;
  upload_time: string;
  status: string;
}

export interface OCRResult {
  text: string;
  confidence: number;
  engine: string;
  word_count: number;
  processing_time?: number;
}

export interface Artist {
  name: string;
  confidence: number;
  spotify_id?: string;
  genres: string[];
  popularity?: number;
}

export interface ArtistExtractionResponse {
  artists: Artist[];
  total_found: number;
  processing_time?: number;
  method: string;
}

export interface Track {
  name: string;
  artist: string;
  spotify_id: string;
  preview_url?: string;
  popularity: number;
  duration_ms: number;
}

export interface Playlist {
  name: string;
  description?: string;
  spotify_id?: string;
  tracks: Track[];
  total_tracks: number;
}

export interface PlaylistCreationResponse {
  playlist: Playlist;
  successful_artists: string[];
  failed_artists: string[];
  total_tracks_added: number;
  processing_time?: number;
}

export class ApiService {
  /**
   * Upload a festival flyer image
   */
  static async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  /**
   * Extract text from uploaded image using OCR
   */
  static async extractText(fileId: string, engine: string = 'tesseract'): Promise<OCRResult> {
    const response = await api.post('/ocr', {
      file_id: fileId,
      engine: engine,
    });

    return response.data;
  }

  /**
   * Extract artist names from text using Gemini AI
   */
  static async extractArtists(
    text: string,
    confidenceThreshold: number = 0.7
  ): Promise<ArtistExtractionResponse> {
    const response = await api.post('/extract-artists', {
      text: text,
      use_ai: true, // Always use AI (Gemini)
      confidence_threshold: confidenceThreshold,
    });

    return response.data;
  }

  /**
   * Analyze festival flyer image directly with Gemini Vision
   */
  static async analyzeImage(
    fileId: string,
    confidenceThreshold: number = 0.7
  ): Promise<ArtistExtractionResponse> {
    const response = await api.post('/analyze-image', {
      file_id: fileId,
      confidence_threshold: confidenceThreshold,
    });

    return response.data;
  }

  /**
   * Create a Spotify playlist from artists
   */
  static async createPlaylist(
    artists: string[],
    playlistName: string,
    userId: string,
    playlistDescription?: string,
    tracksPerArtist: number = 3
  ): Promise<PlaylistCreationResponse> {
    const response = await api.post('/create-playlist', {
      artists: artists,
      playlist_name: playlistName,
      user_id: userId,
      playlist_description: playlistDescription,
      tracks_per_artist: tracksPerArtist,
    });

    return response.data;
  }

  /**
   * Get Spotify authorization URL
   */
  static async getSpotifyAuthUrl(state?: string): Promise<{ auth_url: string }> {
    const response = await api.get('/spotify/auth-url', {
      params: state ? { state } : {},
    });

    return response.data;
  }

  /**
   * Handle Spotify OAuth callback
   */
  static async handleSpotifyCallback(code: string, state?: string | null): Promise<any> {
    // Send as query parameters since the backend expects them that way
    const params: any = { code };
    if (state) {
      params.state = state;
    }

    const response = await api.post('/spotify/callback', null, {
      params: params,
    });

    return response.data;
  }

  /**
   * Create a Spotify playlist with authentication token
   */
  static async createPlaylistWithAuth(
    artists: string[],
    playlistName: string,
    userId: string,
    accessToken: string,
    playlistDescription?: string,
    tracksPerArtist: number = 3
  ): Promise<PlaylistCreationResponse> {
    const response = await api.post('/create-playlist', {
      artists: artists,
      playlist_name: playlistName,
      user_id: userId,
      access_token: accessToken,
      playlist_description: playlistDescription,
      tracks_per_artist: tracksPerArtist,
    });

    return response.data;
  }

  /**
   * Health check
   */
  static async healthCheck(): Promise<any> {
    const response = await api.get('/health');
    return response.data;
  }
}

export default ApiService;
