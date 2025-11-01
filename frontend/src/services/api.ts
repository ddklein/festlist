import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 120000, // Increased timeout to 2 minutes for playlist creation
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', {
      method: config.method,
      url: config.url,
      baseURL: config.baseURL,
      timeout: config.timeout,
      headers: config.headers,
    });
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', {
      status: response.status,
      statusText: response.statusText,
      url: response.config.url,
      data: response.data,
    });
    return response;
  },
  (error) => {
    console.error('API Response Error:', {
      message: error.message,
      code: error.code,
      status: error.response?.status,
      statusText: error.response?.statusText,
      url: error.config?.url,
      data: error.response?.data,
    });
    return Promise.reject(error);
  }
);

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
    try {
      const response = await api.post('/create-playlist', {
        artists: artists,
        playlist_name: playlistName,
        user_id: userId,
        access_token: accessToken,
        playlist_description: playlistDescription,
        tracks_per_artist: tracksPerArtist,
      });

      return response.data;
    } catch (error: any) {
      // If we get a network error or timeout, but the status is 0,
      // it might mean the request was processed but the response failed
      if (error.code === 'ECONNABORTED' || error.response?.status === 0) {
        // Re-throw with additional context
        const enhancedError = new Error('Request may have succeeded but response failed');
        enhancedError.name = 'ResponseError';
        (enhancedError as any).originalError = error;
        (enhancedError as any).code = error.code;
        (enhancedError as any).response = error.response;
        throw enhancedError;
      }
      throw error;
    }
  }

  /**
   * Get Amazon Music authorization URL (placeholder)
   */
  static async getAmazonMusicAuthUrl(state?: string): Promise<{ auth_url: string }> {
    throw new Error('Amazon Music integration is not yet implemented');
  }

  /**
   * Handle Amazon Music OAuth callback (placeholder)
   */
  static async handleAmazonMusicCallback(code: string, state?: string | null): Promise<any> {
    throw new Error('Amazon Music integration is not yet implemented');
  }

  /**
   * Get SoundCloud authorization URL (placeholder)
   */
  static async getSoundCloudAuthUrl(state?: string): Promise<{ auth_url: string }> {
    throw new Error('SoundCloud integration is not yet implemented');
  }

  /**
   * Handle SoundCloud OAuth callback (placeholder)
   */
  static async handleSoundCloudCallback(code: string, state?: string | null): Promise<any> {
    throw new Error('SoundCloud integration is not yet implemented');
  }

  /**
   * Get Apple Music authorization URL (placeholder)
   */
  static async getAppleMusicAuthUrl(state?: string): Promise<{ auth_url: string }> {
    throw new Error('Apple Music integration is not yet implemented');
  }

  /**
   * Handle Apple Music OAuth callback (placeholder)
   */
  static async handleAppleMusicCallback(code: string, state?: string | null): Promise<any> {
    throw new Error('Apple Music integration is not yet implemented');
  }

  /**
   * Get Deezer authorization URL (placeholder)
   */
  static async getDeezerAuthUrl(state?: string): Promise<{ auth_url: string }> {
    throw new Error('Deezer integration is not yet implemented');
  }

  /**
   * Handle Deezer OAuth callback (placeholder)
   */
  static async handleDeezerCallback(code: string, state?: string | null): Promise<any> {
    throw new Error('Deezer integration is not yet implemented');
  }

  /**
   * Get Audiomack authorization URL (placeholder)
   */
  static async getAudiomackAuthUrl(state?: string): Promise<{ auth_url: string }> {
    throw new Error('Audiomack integration is not yet implemented');
  }

  /**
   * Handle Audiomack OAuth callback (placeholder)
   */
  static async handleAudiomackCallback(code: string, state?: string | null): Promise<any> {
    throw new Error('Audiomack integration is not yet implemented');
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
