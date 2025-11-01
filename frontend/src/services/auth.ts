// Music service types
export type MusicServiceType = 'spotify' | 'amazon' | 'soundcloud' | 'audiomack' | 'deezer' | 'apple';

// Base user interface
interface BaseUser {
  id: string;
  display_name: string;
  email?: string;
  country?: string;
  images?: Array<{ url: string; height: number; width: number }>;
}

// Spotify-specific user interface
interface SpotifyUser extends BaseUser {
  followers: number;
  external_urls: { spotify: string };
  images?: Array<{ url: string; height: number; width: number }>;
}

// Generic auth data interface
interface BaseAuthData {
  access_token: string;
  refresh_token?: string;
  expires_in: number;
  token_type: string;
  scope?: string;
  expires_at: number; // Timestamp when token expires
  service: MusicServiceType;
}

// Spotify-specific auth data
interface SpotifyAuthData extends BaseAuthData {
  refresh_token: string;
  scope: string;
  user: SpotifyUser;
  service: 'spotify';
}

// Union type for all auth data types
export type MusicServiceAuthData = SpotifyAuthData;

const AUTH_STORAGE_KEY = 'festlist_music_auth';
const LEGACY_SPOTIFY_KEY = 'festlist_spotify_auth';

export class AuthService {
  /**
   * Migrate legacy Spotify auth data to new format
   */
  private static migrateLegacyAuth(): void {
    try {
      const legacyAuth = localStorage.getItem(LEGACY_SPOTIFY_KEY);
      if (legacyAuth && !localStorage.getItem(AUTH_STORAGE_KEY)) {
        const parsed = JSON.parse(legacyAuth);
        const migratedAuth: SpotifyAuthData = {
          ...parsed,
          service: 'spotify' as const,
        };
        localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(migratedAuth));
        localStorage.removeItem(LEGACY_SPOTIFY_KEY);
      }
    } catch (error) {
      console.error('Error migrating legacy auth:', error);
    }
  }

  /**
   * Save authentication data to localStorage
   */
  static saveAuth(authData: Omit<SpotifyAuthData, 'expires_at'>): SpotifyAuthData {
    const expiresAt = Date.now() + (authData.expires_in * 1000);
    const authWithExpiry: SpotifyAuthData = {
      ...authData,
      expires_at: expiresAt,
      service: 'spotify',
    };

    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authWithExpiry));
    return authWithExpiry;
  }

  /**
   * Save authentication data for any music service
   */
  static saveMusicServiceAuth(authData: Omit<MusicServiceAuthData, 'expires_at'>): MusicServiceAuthData {
    const expiresAt = Date.now() + (authData.expires_in * 1000);
    const authWithExpiry = {
      ...authData,
      expires_at: expiresAt,
    } as MusicServiceAuthData;

    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authWithExpiry));
    return authWithExpiry;
  }

  /**
   * Get authentication data from localStorage
   */
  static getAuth(): SpotifyAuthData | null {
    this.migrateLegacyAuth();

    try {
      const stored = localStorage.getItem(AUTH_STORAGE_KEY);
      if (!stored) return null;

      const authData: MusicServiceAuthData = JSON.parse(stored);

      // Check if token is expired
      if (Date.now() >= authData.expires_at) {
        this.clearAuth();
        return null;
      }

      // For backward compatibility, return only if it's Spotify
      if (authData.service === 'spotify') {
        return authData as SpotifyAuthData;
      }

      return null;
    } catch (error) {
      console.error('Error retrieving auth data:', error);
      this.clearAuth();
      return null;
    }
  }

  /**
   * Get authentication data for any music service
   */
  static getMusicServiceAuth(): MusicServiceAuthData | null {
    this.migrateLegacyAuth();

    try {
      const stored = localStorage.getItem(AUTH_STORAGE_KEY);
      if (!stored) return null;

      const authData: MusicServiceAuthData = JSON.parse(stored);

      // Check if token is expired
      if (Date.now() >= authData.expires_at) {
        this.clearAuth();
        return null;
      }

      return authData;
    } catch (error) {
      console.error('Error retrieving auth data:', error);
      this.clearAuth();
      return null;
    }
  }

  /**
   * Check if user is authenticated and token is valid
   */
  static isAuthenticated(): boolean {
    return this.getMusicServiceAuth() !== null;
  }

  /**
   * Check if user is authenticated with a specific service
   */
  static isAuthenticatedWithService(service: MusicServiceType): boolean {
    const auth = this.getMusicServiceAuth();
    return auth !== null && auth.service === service;
  }

  /**
   * Get the current access token if valid
   */
  static getAccessToken(): string | null {
    const auth = this.getMusicServiceAuth();
    return auth?.access_token || null;
  }

  /**
   * Get the current user info if authenticated (Spotify only for now)
   */
  static getCurrentUser(): SpotifyUser | null {
    const auth = this.getAuth();
    return auth?.user || null;
  }

  /**
   * Get the current authenticated service
   */
  static getCurrentService(): MusicServiceType | null {
    const auth = this.getMusicServiceAuth();
    return auth?.service || null;
  }

  /**
   * Clear authentication data
   */
  static clearAuth(): void {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    localStorage.removeItem(LEGACY_SPOTIFY_KEY);
  }

  /**
   * Check if token will expire soon (within 5 minutes)
   */
  static isTokenExpiringSoon(): boolean {
    const auth = this.getMusicServiceAuth();
    if (!auth) return false;

    const fiveMinutesFromNow = Date.now() + (5 * 60 * 1000);
    return auth.expires_at <= fiveMinutesFromNow;
  }

  /**
   * Get time until token expires in seconds
   */
  static getTimeUntilExpiry(): number {
    const auth = this.getMusicServiceAuth();
    if (!auth) return 0;

    return Math.max(0, Math.floor((auth.expires_at - Date.now()) / 1000));
  }
}

export type { SpotifyAuthData, SpotifyUser, BaseUser, BaseAuthData };
