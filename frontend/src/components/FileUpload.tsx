import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Paper,
  Typography,
  Button,
  LinearProgress,
  Alert,
  Chip,
} from '@mui/material';
import { CloudUpload, Image } from '@mui/icons-material';
import ApiService from '../services/api';
import { extractErrorMessage, ErrorMessages } from '../utils/errorHandling';

interface FileUploadProps {
  onFileUploaded: (fileId: string) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileUploaded }) => {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setUploading(true);
    setError(null);
    setUploadProgress(0);

    try {
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const response = await ApiService.uploadFile(file);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      setTimeout(() => {
        onFileUploaded(response.file_id);
      }, 500);
      
    } catch (err: any) {
      setError(extractErrorMessage(err, ErrorMessages.UPLOAD_FAILED));
      setUploadProgress(0);
    } finally {
      setUploading(false);
    }
  }, [onFileUploaded]);

  const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.tiff', '.tif', '.bmp']
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto' }}>
      <Typography variant="h5" gutterBottom>
        Upload Festival Flyer
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Upload an image of a festival flyer to extract the artist lineup.
      </Typography>

      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          textAlign: 'center',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            borderColor: 'primary.main',
            backgroundColor: 'action.hover',
          },
        }}
      >
        <input {...getInputProps()} />
        
        <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        
        {isDragActive ? (
          <Typography variant="h6">Drop the flyer here...</Typography>
        ) : (
          <>
            <Typography variant="h6" gutterBottom>
              Drag & drop a festival flyer here
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              or click to select a file
            </Typography>
            <Button variant="outlined" sx={{ mt: 2 }}>
              Choose File
            </Button>
          </>
        )}

        <Box sx={{ mt: 2 }}>
          <Chip
            icon={<Image />}
            label="JPEG, PNG, TIFF, BMP"
            size="small"
            variant="outlined"
          />
          <Chip
            label="Max 10MB"
            size="small"
            variant="outlined"
            sx={{ ml: 1 }}
          />
        </Box>
      </Paper>

      {uploading && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" gutterBottom>
            Uploading... {uploadProgress}%
          </Typography>
          <LinearProgress variant="determinate" value={uploadProgress} />
        </Box>
      )}

      {acceptedFiles.length > 0 && !uploading && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2">
            Selected: {acceptedFiles[0].name} ({(acceptedFiles[0].size / 1024 / 1024).toFixed(2)} MB)
          </Typography>
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ mt: 3 }}>
        <Typography variant="body2" color="text.secondary">
          <strong>Tips for best results:</strong>
        </Typography>
        <Typography variant="body2" color="text.secondary" component="ul" sx={{ mt: 1 }}>
          <li>Use high-resolution images</li>
          <li>Ensure text is clearly visible</li>
          <li>Avoid blurry or rotated images</li>
          <li>Good lighting and contrast work best</li>
        </Typography>
      </Box>
    </Box>
  );
};

export default FileUpload;
