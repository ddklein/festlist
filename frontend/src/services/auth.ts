interface SpotifyUser {
  id: string;
  display_name: string;
  email?: string;
  country?: string;
  followers: number;
  images: Array<{ url: string; height: number; width: number }>;
  external_urls: { spotify: string };
}

interface SpotifyAuthData {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
  scope: string;
  user: SpotifyUser;
  expires_at: number; // Timestamp when token expires
}

const AUTH_STORAGE_KEY = 'festlist_spotify_auth';

export class AuthService {
  /**
   * Save authentication data to localStorage
   */
  static saveAuth(authData: Omit<SpotifyAuthData, 'expires_at'>): SpotifyAuthData {
    const expiresAt = Date.now() + (authData.expires_in * 1000);
    const authWithExpiry: SpotifyAuthData = {
      ...authData,
      expires_at: expiresAt,
    };
    
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authWithExpiry));
    return authWithExpiry;
  }

  /**
   * Get authentication data from localStorage
   */
  static getAuth(): SpotifyAuthData | null {
    try {
      const stored = localStorage.getItem(AUTH_STORAGE_KEY);
      if (!stored) return null;

      const authData: SpotifyAuthData = JSON.parse(stored);
      
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
    return this.getAuth() !== null;
  }

  /**
   * Get the current access token if valid
   */
  static getAccessToken(): string | null {
    const auth = this.getAuth();
    return auth?.access_token || null;
  }

  /**
   * Get the current user info if authenticated
   */
  static getCurrentUser(): SpotifyUser | null {
    const auth = this.getAuth();
    return auth?.user || null;
  }

  /**
   * Clear authentication data
   */
  static clearAuth(): void {
    localStorage.removeItem(AUTH_STORAGE_KEY);
  }

  /**
   * Check if token will expire soon (within 5 minutes)
   */
  static isTokenExpiringSoon(): boolean {
    const auth = this.getAuth();
    if (!auth) return false;

    const fiveMinutesFromNow = Date.now() + (5 * 60 * 1000);
    return auth.expires_at <= fiveMinutesFromNow;
  }

  /**
   * Get time until token expires in seconds
   */
  static getTimeUntilExpiry(): number {
    const auth = this.getAuth();
    if (!auth) return 0;

    return Math.max(0, Math.floor((auth.expires_at - Date.now()) / 1000));
  }
}

export type { SpotifyAuthData, SpotifyUser };
