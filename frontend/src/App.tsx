import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Container, Typography, Box, Stepper, Step, StepLabel } from '@mui/material';
import MusicServiceAuth from './components/MusicServiceAuth';
import FileUpload from './components/FileUpload';
import ArtistReview from './components/ArtistReview';
import PlaylistCreation from './components/PlaylistCreation';
import { AuthService, SpotifyAuthData } from './services/auth';
import './App.css';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#7C3AED', contrastText: '#FFFFFF' },
    secondary: { main: '#22C55E' },
    background: { default: '#0B1020', paper: 'rgba(16, 18, 30, 0.85)' },
  },
  shape: { borderRadius: 14 },
  typography: {
    fontFamily: "Inter, system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif",
    h3: { fontWeight: 800 },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        a: { color: '#A78BFA' },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backdropFilter: 'blur(8px)',
          border: '1px solid rgba(124, 58, 237, 0.15)',
          boxShadow: '0 10px 30px rgba(0,0,0,0.25)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { borderRadius: 999, textTransform: 'none', fontWeight: 600, paddingInline: '1rem' },
        containedPrimary: { boxShadow: '0 8px 20px rgba(124,58,237,0.35)' },
      },
    },
    MuiChip: { styleOverrides: { root: { borderRadius: 999 } } },
    MuiSlider: {
      styleOverrides: {
        thumb: { boxShadow: '0 0 0 6px rgba(124,58,237,0.2)' },
        track: { border: 0 },
      },
    },
    MuiStepIcon: {
      styleOverrides: {
        root: { color: 'rgba(124,58,237,0.35)' },
        active: { color: '#7C3AED' },
        completed: { color: '#22C55E' },
      },
    },
  },
});


const steps = ['Connect Music Service', 'Upload Flyer', 'AI Analysis', 'Create Playlist'];



interface AppState {
  activeStep: number;
  spotifyAuth: SpotifyAuthData | null;
  fileId: string | null;
  extractedArtists: any[];
  playlistResult: any;
}

function App() {
  const [state, setState] = useState<AppState>({
    activeStep: 0,
    spotifyAuth: null,
    fileId: null,
    extractedArtists: [],
    playlistResult: null,
  });

  useEffect(() => {
    const savedAuth = AuthService.getAuth();
    if (savedAuth) {
      setState(prev => ({
        ...prev,
        spotifyAuth: savedAuth,
        activeStep: 1, // Skip to file upload if already authenticated
      }));
    }
  }, []);

  const handleNext = () => {
    setState(prev => ({ ...prev, activeStep: prev.activeStep + 1 }));
  };

  const handleBack = () => {
    setState(prev => ({ ...prev, activeStep: prev.activeStep - 1 }));
  };

  const handleReset = () => {
    AuthService.clearAuth();
    setState({
      activeStep: 0,
      spotifyAuth: null,
      fileId: null,
      extractedArtists: [],
      playlistResult: null,
    });
  };

  const updateState = (updates: Partial<AppState>) => {
    setState(prev => ({ ...prev, ...updates }));
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <MusicServiceAuth
            onAuthSuccess={(authData, service) => {
              updateState({ spotifyAuth: authData });
            }}
            onNext={handleNext}
          />
        );
      case 1:
        return (
          <FileUpload
            onFileUploaded={(fileId) => {
              updateState({ fileId });
              handleNext();
            }}
          />
        );
      case 2:
        return (
          <ArtistReview
            fileId={state.fileId}
            onArtistsConfirmed={(artists) => {
              updateState({ extractedArtists: artists });
              handleNext();
            }}
            onBack={handleBack}
          />
        );
      case 3:
        return (
          <PlaylistCreation
            artists={state.extractedArtists}
            spotifyAuth={state.spotifyAuth}
            onPlaylistCreated={(result) => {
              updateState({ playlistResult: result });
            }}
            onBack={handleBack}
            onReset={handleReset}
          />
        );
      default:
        return <div>Unknown step</div>;
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Typography
            variant="h3"
            component="h1"
            gutterBottom
            align="center"
            sx={{
              fontWeight: 800,
              letterSpacing: '-0.02em',
              background: 'linear-gradient(90deg, #A78BFA, #22C55E)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            🎪 FestList
          </Typography>
          <Typography variant="h6" component="h2" gutterBottom align="center" color="text.secondary">
            Upload a festival flyer image and let us create a Spotify discovery playlist for you
          </Typography>

          <Box sx={{ mt: 4, mb: 4 }}>
            <Stepper activeStep={state.activeStep} alternativeLabel>
              {steps.map((label) => (
                <Step key={label}>
                  <StepLabel>{label}</StepLabel>
                </Step>
              ))}
            </Stepper>
          </Box>

          <Box sx={{ mt: 4 }}>
            {renderStepContent(state.activeStep)}
          </Box>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;
