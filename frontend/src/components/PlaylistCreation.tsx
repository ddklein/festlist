import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  TextField,
  LinearProgress,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Slider,
} from '@mui/material';
import {
  ArrowBack,
  Refresh,
  PlaylistAdd,
  CheckCircle,
  Error,
  OpenInNew,
} from '@mui/icons-material';
import ApiService, { PlaylistCreationResponse } from '../services/api';
import { SpotifyAuthData } from '../services/auth';
import { extractErrorMessage, ErrorMessages } from '../utils/errorHandling';



interface PlaylistCreationProps {
  artists: string[];
  spotifyAuth: SpotifyAuthData | null;
  onPlaylistCreated: (result: PlaylistCreationResponse) => void;
  onBack: () => void;
  onReset: () => void;
}

const PlaylistCreation: React.FC<PlaylistCreationProps> = ({
  artists,
  spotifyAuth,
  onPlaylistCreated,
  onBack,
  onReset,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [playlistResult, setPlaylistResult] = useState<PlaylistCreationResponse | null>(null);
  const [playlistName, setPlaylistName] = useState('Festival Playlist');
  const [playlistDescription, setPlaylistDescription] = useState('');
  const [tracksPerArtist, setTracksPerArtist] = useState(3);

  const handleCreatePlaylist = async () => {
    if (!spotifyAuth) {
      setError('Spotify authentication required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await ApiService.createPlaylistWithAuth(
        artists,
        playlistName,
        spotifyAuth.user.id,
        spotifyAuth.access_token,
        playlistDescription || undefined,
        tracksPerArtist
      );

      setPlaylistResult(result);
      onPlaylistCreated(result);
    } catch (err: any) {
      setError(extractErrorMessage(err, ErrorMessages.PLAYLIST_CREATION_FAILED));
    } finally {
      setLoading(false);
    }
  };



  return (
    <Box sx={{ maxWidth: 800, mx: 'auto' }}>
      <Typography variant="h5" gutterBottom>
        Create Spotify Playlist
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Create a Spotify playlist with the top tracks from your selected artists.
      </Typography>

      {!playlistResult ? (
        <>
          {/* Playlist Configuration */}
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Playlist Configuration
            </Typography>

            <Box sx={{ mb: 3 }}>
              <TextField
                fullWidth
                label="Playlist Name"
                value={playlistName}
                onChange={(e) => setPlaylistName(e.target.value)}
                disabled={loading}
                sx={{ mb: 2 }}
              />
              
              <TextField
                fullWidth
                label="Description (Optional)"
                value={playlistDescription}
                onChange={(e) => setPlaylistDescription(e.target.value)}
                disabled={loading}
                multiline
                rows={2}
                sx={{ mb: 2 }}
              />

              {/* Authenticated Spotify User */}
              {spotifyAuth && (
                <Paper variant="outlined" sx={{ p: 2, mb: 2, backgroundColor: 'success.main', color: 'success.contrastText' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <CheckCircle sx={{ mr: 1 }} />
                    <Box>
                      <Typography variant="body2" fontWeight="bold">
                        Connected as: {spotifyAuth.user.display_name || spotifyAuth.user.id}
                      </Typography>
                      <Typography variant="caption">
                        User ID: {spotifyAuth.user.id}
                      </Typography>
                    </Box>
                  </Box>
                </Paper>
              )}

              <Box sx={{ mb: 2 }}>
                <Typography gutterBottom>
                  Tracks per Artist: {tracksPerArtist}
                </Typography>
                <Slider
                  value={tracksPerArtist}
                  onChange={(_, value) => setTracksPerArtist(value as number)}
                  min={1}
                  max={10}
                  step={1}
                  disabled={loading}
                  marks={[
                    { value: 1, label: '1' },
                    { value: 5, label: '5' },
                    { value: 10, label: '10' },
                  ]}
                />
              </Box>
            </Box>


          </Paper>

          {/* Selected Artists */}
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Selected Artists ({artists.length})
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {artists.map((artist, index) => (
                <Chip
                  key={index}
                  label={artist}
                  color="primary"
                  variant="outlined"
                />
              ))}
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              Estimated tracks: {artists.length * tracksPerArtist}
            </Typography>
          </Paper>

          {loading && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" gutterBottom>
                Creating playlist... This may take a few moments.
              </Typography>
              <LinearProgress />
            </Box>
          )}

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}
        </>
      ) : (
        /* Playlist Results */
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <PlaylistAdd sx={{ mr: 1, color: 'success.main' }} />
            <Typography variant="h6">
              Playlist Created Successfully!
            </Typography>
          </Box>

          <Divider sx={{ mb: 2 }} />

          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              <strong>{playlistResult.playlist.name}</strong>
            </Typography>
            {playlistResult.playlist.description && (
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {playlistResult.playlist.description}
              </Typography>
            )}
            
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
              <Chip
                label={`${playlistResult.total_tracks_added} tracks`}
                color="success"
                size="small"
              />
              <Chip
                label={`${playlistResult.successful_artists.length} artists found`}
                color="primary"
                size="small"
              />
              {playlistResult.failed_artists.length > 0 && (
                <Chip
                  label={`${playlistResult.failed_artists.length} artists not found`}
                  color="warning"
                  size="small"
                />
              )}
            </Box>

            {playlistResult.playlist.spotify_id && (
              <Button
                startIcon={<OpenInNew />}
                href={`https://open.spotify.com/playlist/${playlistResult.playlist.spotify_id}`}
                target="_blank"
                rel="noopener"
                sx={{ mt: 2 }}
              >
                Open in Spotify
              </Button>
            )}
          </Box>

          {/* Success/Failed Artists */}
          {playlistResult.successful_artists.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Successfully Added:
              </Typography>
              <List dense>
                {playlistResult.successful_artists.map((artist, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <CheckCircle color="success" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={artist} />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          {playlistResult.failed_artists.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Not Found on Spotify:
              </Typography>
              <List dense>
                {playlistResult.failed_artists.map((artist, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <Error color="warning" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={artist} />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          {playlistResult.processing_time && (
            <Typography variant="caption" color="text.secondary">
              Processing time: {playlistResult.processing_time.toFixed(2)}s
            </Typography>
          )}
        </Paper>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
        <Button
          startIcon={<ArrowBack />}
          onClick={onBack}
          variant="outlined"
          disabled={loading}
        >
          Back
        </Button>

        <Box sx={{ display: 'flex', gap: 2 }}>
          {playlistResult && (
            <Button
              startIcon={<Refresh />}
              onClick={onReset}
              variant="outlined"
            >
              Start Over
            </Button>
          )}
          
          {!playlistResult && (
            <Button
              startIcon={<PlaylistAdd />}
              onClick={handleCreatePlaylist}
              variant="contained"
              disabled={loading || !playlistName.trim() || !spotifyAuth}
            >
              Create Playlist
            </Button>
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default PlaylistCreation;
