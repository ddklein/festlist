import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  LinearProgress,
  Alert,
  Chip,

  List,
  ListItem,
  ListItemText,

  Slider,
  Divider,
  TextField,
} from '@mui/material';
import { Add, ArrowBack, ArrowForward, Person } from '@mui/icons-material';
import ApiService, { ArtistExtractionResponse } from '../services/api';
import { extractErrorMessage, ErrorMessages } from '../utils/errorHandling';

interface ArtistReviewProps {
  fileId: string | null;
  onArtistsConfirmed: (artists: string[]) => void;
  onBack: () => void;
}

const ArtistReview: React.FC<ArtistReviewProps> = ({ fileId, onArtistsConfirmed, onBack }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [extractionResult, setExtractionResult] = useState<ArtistExtractionResponse | null>(null);
  const [selectedArtists, setSelectedArtists] = useState<string[]>([]);
  const [confidenceThreshold, setConfidenceThreshold] = useState(70);
  const [newArtist, setNewArtist] = useState('');

  const extractArtists = useCallback(async () => {
    if (!fileId) {
      setError('No file uploaded');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await ApiService.analyzeImage(
        fileId,
        confidenceThreshold / 100
      );
      setExtractionResult(result);
      // Auto-select all artists initially
      setSelectedArtists(result.artists.map(artist => artist.name));
    } catch (err: any) {
      setError(extractErrorMessage(err, ErrorMessages.ARTIST_EXTRACTION_FAILED));
    } finally {
      setLoading(false);
    }
  }, [fileId, confidenceThreshold]);

  useEffect(() => {
    if (fileId) {
      extractArtists();
    }
  }, [fileId, extractArtists]);

  const handleArtistToggle = (artistName: string) => {
    setSelectedArtists(prev => 
      prev.includes(artistName)
        ? prev.filter(name => name !== artistName)
        : [...prev, artistName]
    );
  };

  const handleAddArtist = () => {
    if (newArtist.trim() && !selectedArtists.includes(newArtist.trim())) {
      setSelectedArtists(prev => [...prev, newArtist.trim()]);
      setNewArtist('');
    }
  };

  const handleRemoveArtist = (artistName: string) => {
    setSelectedArtists(prev => prev.filter(name => name !== artistName));
  };

  const handleContinue = () => {
    onArtistsConfirmed(selectedArtists);
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'success';
    if (confidence >= 60) return 'warning';
    return 'error';
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', px: { xs: 2, sm: 0 } }}>
      <Typography variant="h5" gutterBottom>
        AI Analysis Results
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Our artist AI agent has analyzed your festival flyer image and extracted the following artists. Review and edit as needed.
      </Typography>

      {/* Extraction Settings */}
      <Paper sx={{ p: { xs: 2, sm: 3 }, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
            Artist AI Agent Settings
        </Typography>

        <Typography variant="body2" color="text.secondary" paragraph>
          Our artist AI agent analyzes your festival flyer image directly to identify artist names.
        </Typography>

        <Box sx={{ mb: 2 }}>
          <Typography gutterBottom>
            Confidence Threshold: {confidenceThreshold}%
          </Typography>
          <Typography variant="caption" color="text.secondary" paragraph>
            Only show artists that our AI is at least {confidenceThreshold}% confident about.
          </Typography>
          <Slider
            value={confidenceThreshold}
            onChange={(_, value) => setConfidenceThreshold(value as number)}
            min={0}
            max={100}
            step={5}
            disabled={loading}
            marks={[
              { value: 0, label: '0%' },
              { value: 50, label: '50%' },
              { value: 100, label: '100%' },
            ]}
          />
        </Box>

        <Button
          onClick={extractArtists}
          disabled={loading}
          variant="outlined"
        >
          Re-analyze
        </Button>
      </Paper>

      {loading && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" gutterBottom>
            Our artist AI agent is analyzing your festival flyer image and identifying artist names...
          </Typography>
          <LinearProgress />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {extractionResult && (
        <Paper sx={{ p: { xs: 2, sm: 3 }, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Person sx={{ mr: 1 }} />
            <Typography variant="h6">
              Extracted Artists ({extractionResult.total_found} found)
            </Typography>
            <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
              {extractionResult.processing_time && (
                <Chip
                  label={`${extractionResult.processing_time.toFixed(2)}s`}
                  variant="outlined"
                  size="small"
                />
              )}
            </Box>
          </Box>

          <Divider sx={{ mb: 2 }} />

          {extractionResult.artists.length === 0 ? (
            <Typography color="text.secondary">
              Our AI didn't find any artists above the confidence threshold. Try lowering the threshold or add artists manually.
            </Typography>
          ) : (
            <List>
              {extractionResult.artists.map((artist, index) => (
                <ListItem
                  key={index}
                  onClick={() => handleArtistToggle(artist.name)}
                  sx={{
                    border: 1,
                    borderColor: 'divider',
                    borderRadius: 1,
                    mb: 1,
                    py: 1,
                    backgroundColor: selectedArtists.includes(artist.name)
                      ? 'action.selected'
                      : 'background.paper',
                    cursor: 'pointer',
                    '&:hover': {
                      backgroundColor: 'action.hover',
                    },
                  }}
                >
                  <ListItemText
                    primary={artist.name}
                    secondary={
                      <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                        <Chip
                          label={`${artist.confidence.toFixed(1)}% confidence`}
                          color={getConfidenceColor(artist.confidence)}
                          size="small"
                        />
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          )}
        </Paper>
      )}

      {/* Selected Artists */}
      <Paper sx={{ p: { xs: 2, sm: 3 }, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Selected Artists ({selectedArtists.length})
        </Typography>
        
        {/* Add new artist */}
        <Box sx={{ display: 'flex', gap: 1, mb: 2, flexDirection: { xs: 'column', sm: 'row' } }}>
          <TextField
            size="small"
            placeholder="Add artist manually"
            value={newArtist}
            onChange={(e) => setNewArtist(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleAddArtist()}
            sx={{ flexGrow: 1 }}
          />
          <Button
            startIcon={<Add />}
            onClick={handleAddArtist}
            disabled={!newArtist.trim()}
            sx={{ width: { xs: '100%', sm: 'auto' } }}
          >
            Add
          </Button>
        </Box>

        <Divider sx={{ mb: 2 }} />

        {selectedArtists.length === 0 ? (
          <Typography color="text.secondary">
            No artists selected. Select artists from the extracted list or add them manually.
          </Typography>
        ) : (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {selectedArtists.map((artist, index) => (
              <Chip
                key={index}
                label={artist}
                onDelete={() => handleRemoveArtist(artist)}
                color="primary"
                variant="outlined"
              />
            ))}
          </Box>
        )}
      </Paper>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3, flexDirection: { xs: 'column', sm: 'row' }, gap: 2 }}>
        <Button
          startIcon={<ArrowBack />}
          onClick={onBack}
          variant="outlined"
          sx={{ width: { xs: '100%', sm: 'auto' } }}
        >
          Back
        </Button>

        <Button
          endIcon={<ArrowForward />}
          onClick={handleContinue}
          variant="contained"
          disabled={selectedArtists.length === 0}
          sx={{ width: { xs: '100%', sm: 'auto' } }}
        >
          Create Playlist ({selectedArtists.length} artists)
        </Button>
      </Box>
    </Box>
  );
};

export default ArtistReview;
