import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Avatar,
  Divider,
  Stack,
} from '@mui/material';
import {
  CheckCircle,
  ArrowForward
} from '@mui/icons-material';
import ApiService from '../services/api';
import { AuthService, SpotifyAuthData } from '../services/auth';
import { extractErrorMessage, ErrorMessages } from '../utils/errorHandling';
import {
  SpotifyIcon,
  AmazonMusicIcon,
  SoundCloudIcon,
  AppleMusicIcon,
  DeezerIcon,
  AudiomackIcon
} from './ServiceIcons';

// Service configuration
export interface MusicService {
  id: 'spotify' | 'amazon' | 'soundcloud' | 'audiomack' | 'deezer' | 'apple';
  name: string;
  displayName: string;
  color: string;
  hoverColor: string;
  icon: React.ReactNode;
  description: string;
  isAvailable: boolean;
}

const musicServices: MusicService[] = [
  {
    id: 'spotify',
    name: 'spotify',
    displayName: 'Connect Spotify',
    color: '#1DB954',
    hoverColor: '#1ed760',
    icon: <SpotifyIcon />,
    description: 'Stream and create playlists',
    isAvailable: true,
  },
  {
    id: 'amazon',
    name: 'amazon',
    displayName: 'Connect Amazon Music',
    color: '#00A8E1',
    hoverColor: '#1BB8F1',
    icon: <AmazonMusicIcon />,
    description: 'Amazon Music streaming',
    isAvailable: false, // Not implemented yet
  },
  {
    id: 'soundcloud',
    name: 'soundcloud',
    displayName: 'Connect Soundcloud',
    color: '#FF5500',
    hoverColor: '#FF7733',
    icon: <SoundCloudIcon />,
    description: 'Discover independent music',
    isAvailable: false, // Not implemented yet
  },
  {
    id: 'audiomack',
    name: 'audiomack',
    displayName: 'Connect Audiomack',
    color: '#FF6600',
    hoverColor: '#FF8833',
    icon: <AudiomackIcon />,
    description: 'Hip-hop and R&B music',
    isAvailable: false, // Not implemented yet
  },
  {
    id: 'deezer',
    name: 'deezer',
    displayName: 'Connect Deezer',
    color: '#A238FF',
    hoverColor: '#B555FF',
    icon: <DeezerIcon />,
    description: 'High-quality music streaming',
    isAvailable: false, // Not implemented yet
  },
  {
    id: 'apple',
    name: 'apple',
    displayName: 'Connect Apple Music',
    color: '#FA243C',
    hoverColor: '#FB4757',
    icon: <AppleMusicIcon />,
    description: 'Apple Music streaming',
    isAvailable: false, // Not implemented yet
  },
];

interface MusicServiceAuthProps {
  onAuthSuccess: (authData: SpotifyAuthData, service: string) => void;
  onNext: () => void;
}

const MusicServiceAuth: React.FC<MusicServiceAuthProps> = ({ onAuthSuccess, onNext }) => {
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [authData, setAuthData] = useState<SpotifyAuthData | null>(null);
  const [connectedService, setConnectedService] = useState<string | null>(null);
  const [checkingCallback, setCheckingCallback] = useState(false);

  useEffect(() => {
    // Check for existing authentication
    const existingAuth = AuthService.getAuth();
    if (existingAuth) {
      setAuthData(existingAuth);
      setConnectedService('spotify'); // Currently only Spotify is supported
      onAuthSuccess(existingAuth, 'spotify');
      return;
    }

    // Check if we're returning from OAuth callback
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    const error = urlParams.get('error');

    if (error) {
      setError(`Authentication failed: ${error}`);
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
      // Currently only Spotify is implemented
      const response = await ApiService.handleSpotifyCallback(code, state);

      // Save authentication data to localStorage
      const savedAuth = AuthService.saveAuth(response);
      setAuthData(savedAuth);
      setConnectedService('spotify');
      onAuthSuccess(savedAuth, 'spotify');

      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } catch (err: any) {
      setError(extractErrorMessage(err, ErrorMessages.SPOTIFY_AUTH_FAILED));
    } finally {
      setCheckingCallback(false);
    }
  };

  const handleServiceConnect = async (service: MusicService) => {
    if (!service.isAvailable) {
      setError(`${service.displayName} integration is coming soon!`);
      return;
    }

    setLoading(service.id);
    setError(null);

    try {
      if (service.id === 'spotify') {
        const response = await ApiService.getSpotifyAuthUrl();
        // Redirect to Spotify authorization
        window.location.href = response.auth_url;
      } else {
        // Placeholder for other services
        setError(`${service.displayName} integration is not yet implemented.`);
      }
    } catch (err: any) {
      setError(extractErrorMessage(err, ErrorMessages.SPOTIFY_AUTH_URL_FAILED));
    } finally {
      setLoading(null);
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
          Completing Authentication...
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Please wait while we verify your account.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 500, mx: 'auto' }}>
      <Box sx={{ textAlign: 'center', mb: 5 }}>
        <Typography
          variant="h3"
          gutterBottom
          sx={{
            fontWeight: 800,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            mb: 2,
            fontSize: { xs: '1.5rem', sm: '2rem' }
          }}
        >
          Connect your music service
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {!authData ? (
        <Box sx={{
          background: 'rgba(255, 255, 255, 0.05)',
          borderRadius: '24px',
          p: 3,
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          <Stack spacing={2.5}>
            {musicServices.map((service) => (
              <Button
                key={service.id}
                variant="contained"
                size="large"
                fullWidth
                startIcon={
                  loading === service.id ? (
                    <CircularProgress size={24} color="inherit" />
                  ) : (
                    <Box sx={{ fontSize: '24px' }}>{service.icon}</Box>
                  )
                }
                endIcon={<ArrowForward sx={{ fontSize: '20px' }} />}
                onClick={() => handleServiceConnect(service)}
                disabled={loading !== null}
                sx={{
                  backgroundColor: service.isAvailable ? service.color : 'rgba(255,255,255,0.08)',
                  '&:hover': {
                    backgroundColor: service.isAvailable ? service.hoverColor : 'rgba(255,255,255,0.12)',
                    transform: service.isAvailable ? 'translateY(-2px)' : 'none',
                  },
                  color: 'white',
                  fontWeight: 600,
                  py: 3,
                  px: 4,
                  borderRadius: '50px',
                  textTransform: 'none',
                  fontSize: '1.1rem',
                  opacity: service.isAvailable ? 1 : 0.7,
                  justifyContent: 'space-between',
                  minHeight: '72px',
                  boxShadow: service.isAvailable ? '0 8px 24px rgba(0,0,0,0.15)' : '0 4px 12px rgba(0,0,0,0.1)',
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  border: service.isAvailable ? 'none' : '1px solid rgba(255,255,255,0.1)',
                  '& .MuiButton-startIcon': {
                    marginRight: 3,
                    marginLeft: 0,
                  },
                  '& .MuiButton-endIcon': {
                    marginLeft: 'auto',
                    opacity: 0.8,
                  },
                  '&:disabled': {
                    opacity: 0.7,
                    color: 'white',
                  },
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                  {service.displayName}
                </Box>
              </Button>
            ))}
          </Stack>
        </Box>
      ) : (
        <Box sx={{
          background: 'rgba(255, 255, 255, 0.05)',
          borderRadius: '24px',
          p: 4,
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(34, 197, 94, 0.3)'
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <CheckCircle sx={{ color: 'success.main', mr: 2, fontSize: '32px' }} />
            <Typography variant="h5" color="success.main" sx={{ fontWeight: 600 }}>
              Successfully Connected!
            </Typography>
          </Box>

          <Divider sx={{ mb: 4, borderColor: 'rgba(255,255,255,0.1)' }} />

          <Box sx={{ display: 'flex', alignItems: 'center', mb: 4 }}>
            <Avatar
              src={authData.user.images?.[0]?.url}
              sx={{
                width: 72,
                height: 72,
                mr: 3,
                border: '3px solid rgba(255,255,255,0.1)'
              }}
            >
              {authData.user.display_name?.charAt(0) || authData.user.id.charAt(0)}
            </Avatar>

            <Box>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                {authData.user.display_name || authData.user.id}
              </Typography>
              {authData.user.email && (
                <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                  {authData.user.email}
                </Typography>
              )}
              <Typography variant="body2" color="success.main" sx={{ fontWeight: 500 }}>
                Connected via {connectedService}
              </Typography>
            </Box>
          </Box>

          <Button
            variant="contained"
            size="large"
            onClick={handleContinue}
            fullWidth
            sx={{
              py: 2.5,
              borderRadius: '50px',
              fontSize: '1.1rem',
              fontWeight: 600,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                transform: 'translateY(-2px)',
              },
              boxShadow: '0 8px 24px rgba(102, 126, 234, 0.3)',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
          >
            Continue to Upload Flyer
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default MusicServiceAuth;
