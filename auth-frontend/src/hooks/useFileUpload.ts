/**
 * useFileUpload Hook
 * Hook for basic file upload with progress tracking
 */

import { useState } from 'react';
import { fileService } from '../infra/services/FileService';
import type { FileUploadResponse } from '../types/file';

export function useFileUpload() {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<FileUploadResponse | null>(null);

  const uploadFile = async (file: File): Promise<string> => {
    setUploading(true);
    setProgress(0);
    setError(null);
    setUploadedFile(null);

    try {
      const result = await fileService.uploadFile(file, (percent) => {
        setProgress(percent);
      });

      setUploadedFile(result);
      setUploading(false);
      return result.url;
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Upload failed');
      setUploading(false);
      throw err;
    }
  };

  const reset = () => {
    setUploading(false);
    setProgress(0);
    setError(null);
    setUploadedFile(null);
  };

  return {
    uploadFile,
    uploading,
    progress,
    error,
    uploadedFile,
    reset,
  };
}

