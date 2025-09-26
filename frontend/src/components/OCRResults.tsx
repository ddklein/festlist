import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  LinearProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Divider,
} from '@mui/material';
import { TextFields, ArrowBack, ArrowForward } from '@mui/icons-material';
import ApiService, { OCRResult } from '../services/api';
import { extractErrorMessage, ErrorMessages } from '../utils/errorHandling';

interface OCRResultsProps {
  fileId: string | null;
  onTextExtracted: (text: string) => void;
  onBack: () => void;
}

const OCRResults: React.FC<OCRResultsProps> = ({ fileId, onTextExtracted, onBack }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ocrResult, setOcrResult] = useState<OCRResult | null>(null);
  const [selectedEngine, setSelectedEngine] = useState('tesseract');

  const performOCR = async () => {
    if (!fileId) {
      setError('No file uploaded');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await ApiService.extractText(fileId, selectedEngine);
      setOcrResult(result);
    } catch (err: any) {
      setError(extractErrorMessage(err, ErrorMessages.OCR_FAILED));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (fileId) {
      performOCR();
    }
  }, [fileId, performOCR]);

  const handleContinue = () => {
    if (ocrResult?.text) {
      onTextExtracted(ocrResult.text);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'success';
    if (confidence >= 60) return 'warning';
    return 'error';
  };



  return (
    <Box sx={{ maxWidth: 800, mx: 'auto' }}>
      <Typography variant="h5" gutterBottom>
        Text Extraction (OCR)
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Extracting text from your festival flyer using optical character recognition.
      </Typography>

      <Box sx={{ mb: 3 }}>
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>OCR Engine</InputLabel>
          <Select
            value={selectedEngine}
            label="OCR Engine"
            onChange={(e) => setSelectedEngine(e.target.value)}
            disabled={loading}
          >
            <MenuItem value="tesseract">Tesseract (Free)</MenuItem>
            <MenuItem value="google_vision">Google Vision (Better Quality)</MenuItem>
          </Select>
        </FormControl>
        
        {selectedEngine !== 'tesseract' && (
          <Typography variant="caption" display="block" sx={{ mt: 1, color: 'text.secondary' }}>
            Note: Google Vision requires API credentials to be configured
          </Typography>
        )}
      </Box>

      {loading && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" gutterBottom>
            Processing image with {selectedEngine}...
          </Typography>
          <LinearProgress />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
          <Button
            size="small"
            onClick={performOCR}
            sx={{ ml: 2 }}
          >
            Retry
          </Button>
        </Alert>
      )}

      {ocrResult && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <TextFields sx={{ mr: 1 }} />
            <Typography variant="h6">
              Extracted Text
            </Typography>
            <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
              <Chip
                label={`${ocrResult.confidence.toFixed(1)}% confidence`}
                color={getConfidenceColor(ocrResult.confidence)}
                size="small"
              />
              <Chip
                label={`${ocrResult.word_count} words`}
                variant="outlined"
                size="small"
              />
              <Chip
                label={ocrResult.engine}
                variant="outlined"
                size="small"
              />
            </Box>
          </Box>

          <Divider sx={{ mb: 2 }} />

          <Box
            sx={{
              maxHeight: 300,
              overflow: 'auto',
              p: 2,
              backgroundColor: 'grey.50',
              borderRadius: 1,
              fontFamily: 'monospace',
              fontSize: '0.875rem',
              lineHeight: 1.6,
              whiteSpace: 'pre-wrap',
            }}
          >
            {ocrResult.text || 'No text detected in the image.'}
          </Box>

          {ocrResult.processing_time && (
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Processing time: {ocrResult.processing_time.toFixed(2)}s
            </Typography>
          )}

          {ocrResult.confidence < 60 && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              Low confidence detected. Consider using a higher quality image or trying Google Vision OCR.
            </Alert>
          )}
        </Paper>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
        <Button
          startIcon={<ArrowBack />}
          onClick={onBack}
          variant="outlined"
        >
          Back
        </Button>

        <Box sx={{ display: 'flex', gap: 2 }}>
          {ocrResult && (
            <Button
              onClick={performOCR}
              disabled={loading}
              variant="outlined"
            >
              Re-process
            </Button>
          )}
          
          <Button
            endIcon={<ArrowForward />}
            onClick={handleContinue}
            variant="contained"
            disabled={!ocrResult?.text || loading}
          >
            Extract Artists with AI
          </Button>
        </Box>
      </Box>
    </Box>
  );
};

export default OCRResults;
