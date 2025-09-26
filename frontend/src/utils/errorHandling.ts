/**
 * Extract a user-friendly error message from an API error response
 * @param err - The error object from axios or similar HTTP client
 * @param defaultMessage - Default message to use if no specific error is found
 * @returns A user-friendly error message string
 */
export function extractErrorMessage(err: any, defaultMessage: string): string {
  if (!err?.response?.data) {
    return defaultMessage;
  }

  const errorData = err.response.data;

  // Handle string detail (most common case)
  if (typeof errorData.detail === 'string') {
    return errorData.detail;
  }

  // Handle validation errors (array of error objects)
  if (Array.isArray(errorData.detail)) {
    const validationErrors = errorData.detail.map((error: any) => {
      const location = error.loc?.join('.') || 'unknown';
      const message = error.msg || 'validation error';
      return `${location} - ${message}`;
    }).join(', ');
    return `Validation error: ${validationErrors}`;
  }

  // Handle simple error field
  if (errorData.error) {
    return errorData.error;
  }

  // Fallback to default message
  return defaultMessage;
}

/**
 * Common error messages used throughout the application
 */
export const ErrorMessages = {
  UPLOAD_FAILED: 'Upload failed. Please try again.',
  OCR_FAILED: 'OCR processing failed. Please try again.',
  ARTIST_EXTRACTION_FAILED: 'AI image analysis failed. Please try again.',
  PLAYLIST_CREATION_FAILED: 'Playlist creation failed',
  SPOTIFY_AUTH_FAILED: 'Failed to complete Spotify authentication',
  SPOTIFY_AUTH_URL_FAILED: 'Failed to get Spotify authorization URL',
} as const;
