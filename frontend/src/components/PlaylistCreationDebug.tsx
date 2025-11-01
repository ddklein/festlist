import React, { useState } from 'react';
import { Box, Button, Typography, Alert, CircularProgress } from '@mui/material';
import ApiService from '../services/api';

/**
 * Debug component to test playlist creation with minimal data
 */
const PlaylistCreationDebug: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Test data - minimal set for debugging
  const testData = {
    artists: ['GRIZ', 'SUBTRONICS', 'WOOLI'], // Just 3 artists for quick testing
    playlistName: 'Debug Test Playlist',
    userId: '22sdhpohie37ap2ja2v4xppoa', // From HAR file
    accessToken: 'BQDg9h922VnwZ78O9yC0z2_mdX867XJ5VhkrBQ_nJ0hmvrpmf0kXmIMQgESJdo21lQ3jb8yThOjFCfJapvsuyUCeNJ88itSe5IDcMFni2X_3-9GH1kwPONPM1w2Lg51Hd8e4Owvub4STj6xMKcCMB_3N-ngvwLFA4BYjPXSsaSLhTKGx_5tnEEtXzLCz8-5cy1d9Djvl57oo0LYV4BBR3Fe7_80_FsV8TGMQWuNUNdyflD9Hdae1XVmfI0OmoEdLcjkmqyzfqbk5FZU9jTMmzBNI5fFd8tlRtumFyRzI9v1VbJDFzeXoZZUmLiQ6BImsg_zHr7kS_YFEaMfX9M1U52Z71q94nDF_Cg',
    tracksPerArtist: 2
  };

  const handleTest = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    console.log('Starting debug test with data:', testData);

    try {
      const startTime = Date.now();
      
      const response = await ApiService.createPlaylistWithAuth(
        testData.artists,
        testData.playlistName,
        testData.userId,
        testData.accessToken,
        'Debug test playlist',
        testData.tracksPerArtist
      );

      const endTime = Date.now();
      const duration = endTime - startTime;

      console.log('Debug test successful:', response);
      console.log('Request duration:', duration, 'ms');

      setResult({
        ...response,
        requestDuration: duration
      });

    } catch (err: any) {
      console.error('Debug test failed:', err);
      
      const errorInfo = {
        message: err.message,
        code: err.code,
        name: err.name,
        status: err.response?.status,
        statusText: err.response?.statusText,
        data: err.response?.data,
        originalError: err.originalError
      };

      console.log('Error details:', errorInfo);
      setError(JSON.stringify(errorInfo, null, 2));
    } finally {
      setLoading(false);
    }
  };

  const handleHealthCheck = async () => {
    try {
      console.log('Testing health check...');
      const response = await ApiService.healthCheck();
      console.log('Health check response:', response);
      alert('Health check successful: ' + JSON.stringify(response));
    } catch (err: any) {
      console.error('Health check failed:', err);
      alert('Health check failed: ' + err.message);
    }
  };

  return (
    <Box sx={{ p: 3, maxWidth: 800, margin: '0 auto' }}>
      <Typography variant="h4" gutterBottom>
        Playlist Creation Debug
      </Typography>
      
      <Typography variant="body1" sx={{ mb: 3 }}>
        This component tests playlist creation with minimal data to help debug the issue.
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <Button
          variant="outlined"
          onClick={handleHealthCheck}
          disabled={loading}
        >
          Test Health Check
        </Button>
        
        <Button
          variant="contained"
          onClick={handleTest}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          {loading ? 'Testing...' : 'Test Playlist Creation'}
        </Button>
      </Box>

      {loading && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Testing playlist creation... This may take up to 2 minutes.
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="h6">Error:</Typography>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>
            {error}
          </pre>
        </Alert>
      )}

      {result && (
        <Alert severity="success" sx={{ mb: 2 }}>
          <Typography variant="h6">Success!</Typography>
          <Typography variant="body2">
            Playlist: {result.playlist?.name}<br/>
            Tracks added: {result.total_tracks_added}<br/>
            Request duration: {result.requestDuration}ms<br/>
            Processing time: {result.processing_time}s
          </Typography>
        </Alert>
      )}

      <Typography variant="h6" sx={{ mt: 3 }}>
        Test Data:
      </Typography>
      <pre style={{ 
        background: '#f5f5f5', 
        padding: '10px', 
        borderRadius: '4px',
        fontSize: '12px',
        overflow: 'auto'
      }}>
        {JSON.stringify(testData, null, 2)}
      </pre>
    </Box>
  );
};

export default PlaylistCreationDebug;
