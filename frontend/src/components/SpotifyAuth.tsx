import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Avatar,
  Chip,
  Divider,
} from '@mui/material';
import { MusicNote, Login, CheckCircle } from '@mui/icons-material';
import ApiService from '../services/api';
import { AuthService, SpotifyAuthData } from '../services/auth';
import { extractErrorMessage, ErrorMessages } from '../utils/errorHandling';



interface SpotifyAuthProps {
  onAuthSuccess: (authData: SpotifyAuthData) => void;
  onNext: () => void;
}

const SpotifyAuth: React.FC<SpotifyAuthProps> = ({ onAuthSuccess, onNext }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [authData, setAuthData] = useState<SpotifyAuthData | null>(null);
  const [checkingCallback, setCheckingCallback] = useState(false);

  useEffect(() => {
    // Check for existing authentication
    const existingAuth = AuthService.getAuth();
    if (existingAuth) {
      setAuthData(existingAuth);
      onAuthSuccess(existingAuth);
      return;
    }

    // Check if we're returning from Spotify OAuth callback
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    const error = urlParams.get('error');

    if (error) {
      setError(`Spotify authentication failed: ${error}`);
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
      return;
    }

    if (code) {
      setCheckingCallback(true);
      handleCallback(code, state);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCallback = async (code: string, state: string | null) => {
    try {
      const response = await ApiService.handleSpotifyCallback(code, state);

      // Save authentication data to localStorage
      const savedAuth = AuthService.saveAuth(response);
      setAuthData(savedAuth);
      onAuthSuccess(savedAuth);

      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } catch (err: any) {
      setError(extractErrorMessage(err, ErrorMessages.SPOTIFY_AUTH_FAILED));
    } finally {
      setCheckingCallback(false);
    }
  };

  const handleSpotifyLogin = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await ApiService.getSpotifyAuthUrl();
      // Redirect to Spotify authorization
      window.location.href = response.auth_url;
    } catch (err: any) {
      setError(extractErrorMessage(err, ErrorMessages.SPOTIFY_AUTH_URL_FAILED));
      setLoading(false);
    }
  };

  const handleContinue = () => {
    onNext();
  };

  if (checkingCallback) {
    return (
      <Box sx={{ maxWidth: 600, mx: 'auto', textAlign: 'center' }}>
        <CircularProgress size={60} sx={{ mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          Completing Spotify Authentication...
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Please wait while we verify your Spotify account.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto' }}>
      <Typography variant="h5" gutterBottom>
        Connect to Spotify
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Connect your Spotify account to create personalized playlists from festival lineups.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {!authData ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <MusicNote sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
          
          <Typography variant="h6" gutterBottom>
            Spotify Authentication Required
          </Typography>
          
          <Typography variant="body2" color="text.secondary" paragraph>
            To create playlists, we need permission to access your Spotify account.
            This will allow us to:
          </Typography>

          <Box sx={{ mb: 3 }}>
            <Chip
              label="Create playlists"
              variant="outlined"
              size="small"
              sx={{ m: 0.5 }}
            />
            <Chip
              label="Add tracks to playlists"
              variant="outlined"
              size="small"
              sx={{ m: 0.5 }}
            />
            <Chip
              label="Access your profile"
              variant="outlined"
              size="small"
              sx={{ m: 0.5 }}
            />
          </Box>

          <Button
            variant="contained"
            size="large"
            startIcon={loading ? <CircularProgress size={20} /> : <Login />}
            onClick={handleSpotifyLogin}
            disabled={loading}
            sx={{
              backgroundColor: '#1DB954',
              '&:hover': {
                backgroundColor: '#1ed760',
              },
              color: 'white',
              fontWeight: 'bold',
              py: 1.5,
              px: 4,
            }}
          >
            {loading ? 'Connecting...' : 'Connect with Spotify'}
          </Button>

          <Typography variant="caption" display="block" sx={{ mt: 2, color: 'text.secondary' }}>
            You'll be redirected to Spotify to authorize this application
          </Typography>
        </Paper>
      ) : (
        <Paper sx={{ p: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <CheckCircle sx={{ color: 'success.main', mr: 1 }} />
            <Typography variant="h6" color="success.main">
              Successfully Connected!
            </Typography>
          </Box>

          <Divider sx={{ mb: 3 }} />

          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <Avatar
              src={authData.user.images[0]?.url}
              sx={{ width: 64, height: 64, mr: 2 }}
            >
              {authData.user.display_name?.charAt(0) || authData.user.id.charAt(0)}
            </Avatar>
            
            <Box>
              <Typography variant="h6">
                {authData.user.display_name || authData.user.id}
              </Typography>
              {authData.user.email && (
                <Typography variant="body2" color="text.secondary">
                  {authData.user.email}
                </Typography>
              )}
              <Typography variant="body2" color="text.secondary">
                {authData.user.followers} followers
              </Typography>
            </Box>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Permissions granted:
            </Typography>
            {authData.scope.split(' ').map((scope) => (
              <Chip
                key={scope}
                label={scope.replace('-', ' ')}
                variant="outlined"
                size="small"
                sx={{ m: 0.5 }}
              />
            ))}
          </Box>

          <Button
            variant="contained"
            size="large"
            onClick={handleContinue}
            fullWidth
            sx={{ py: 1.5 }}
          >
            Continue to Upload Flyer
          </Button>
        </Paper>
      )}
    </Box>
  );
};

export default SpotifyAuth;
