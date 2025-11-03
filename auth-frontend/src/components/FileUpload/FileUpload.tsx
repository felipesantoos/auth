/**
 * FileUpload Component
 * Drag & drop file upload with progress tracking
 */

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X, File as FileIcon, Image, Video } from 'lucide-react';
import { useFileUpload } from '../../hooks/useFileUpload';
import { formatFileSize } from '../../utils/file';
import type { UploadedFileItem } from '../../types/file';

interface FileUploadProps {
  accept?: string;
  maxSize?: number; // MB
  maxFiles?: number;
  onUpload?: (urls: string[]) => void;
  multiple?: boolean;
  showPreview?: boolean;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  accept = 'image/*',
  maxSize = 10,
  maxFiles = 5,
  onUpload,
  multiple = true,
  showPreview = true,
}) => {
  const [files, setFiles] = useState<UploadedFileItem[]>([]);
  const { uploadFile } = useFileUpload();

  const uploadSingleFile = async (file: File): Promise<UploadedFileItem> => {
    const fileItem: UploadedFileItem = {
      id: Math.random().toString(36),
      file,
      progress: 0,
      status: 'uploading',
    };

    setFiles(prev => [...prev, fileItem]);

    try {
      const url = await uploadFile(file);

      const completedItem: UploadedFileItem = {
        ...fileItem,
        progress: 100,
        status: 'completed',
        url,
      };

      setFiles(prev => prev.map(f => (f.id === fileItem.id ? completedItem : f)));

      return completedItem;
    } catch (error: any) {
      const errorItem: UploadedFileItem = {
        ...fileItem,
        status: 'error',
        error: error.message,
      };

      setFiles(prev => prev.map(f => (f.id === fileItem.id ? errorItem : f)));
      throw error;
    }
  };

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      try {
        const uploadedFiles = await Promise.all(
          acceptedFiles.map(file => uploadSingleFile(file))
        );

        if (onUpload) {
          const urls = uploadedFiles.map(f => f.url).filter(Boolean) as string[];
          onUpload(urls);
        }
      } catch (error) {
        console.error('Upload failed:', error);
      }
    },
    [onUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: accept.split(',').reduce((acc, type) => {
      acc[type.trim()] = [];
      return acc;
    }, {} as Record<string, string[]>),
    maxSize: maxSize * 1024 * 1024,
    maxFiles,
    multiple,
  });

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  return (
    <div className="w-full space-y-4">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          transition-colors duration-200
          ${isDragActive ? 'border-primary bg-primary/10' : 'border-gray-300 hover:border-primary'}
        `}
      >
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        {isDragActive ? (
          <p className="text-primary font-medium">Solte os arquivos aqui...</p>
        ) : (
          <>
            <p className="text-lg font-medium mb-2">
              Arraste arquivos aqui ou clique para selecionar
            </p>
            <p className="text-sm text-gray-500">
              Máximo {maxSize}MB por arquivo, até {maxFiles} arquivos
            </p>
          </>
        )}
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          {files.map(fileItem => (
            <div
              key={fileItem.id}
              className="flex items-center gap-3 p-3 border rounded-lg"
            >
              <div className="flex-shrink-0">
                {fileItem.file.type.startsWith('image/') && showPreview && fileItem.url ? (
                  <img
                    src={fileItem.url}
                    alt={fileItem.file.name}
                    className="w-12 h-12 object-cover rounded"
                  />
                ) : fileItem.file.type.startsWith('image/') ? (
                  <Image className="w-6 h-6 text-gray-400" />
                ) : fileItem.file.type.startsWith('video/') ? (
                  <Video className="w-6 h-6 text-gray-400" />
                ) : (
                  <FileIcon className="w-6 h-6 text-gray-400" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{fileItem.file.name}</p>
                <p className="text-xs text-gray-500">{formatFileSize(fileItem.file.size)}</p>

                {/* Progress Bar */}
                {fileItem.status === 'uploading' && (
                  <div className="mt-1 w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className="bg-primary h-1.5 rounded-full transition-all"
                      style={{ width: `${fileItem.progress}%` }}
                    />
                  </div>
                )}

                {/* Error */}
                {fileItem.status === 'error' && (
                  <p className="text-xs text-red-500 mt-1">{fileItem.error}</p>
                )}
              </div>

              {/* Remove Button */}
              {fileItem.status === 'completed' && (
                <button
                  onClick={() => removeFile(fileItem.id)}
                  className="flex-shrink-0 p-1 hover:bg-gray-100 rounded"
                >
                  <X className="w-4 h-4" />
                </button>
              )}

              {/* Status Indicator */}
              <div className="flex-shrink-0">
                {fileItem.status === 'uploading' && (
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                )}
                {fileItem.status === 'completed' && (
                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                )}
                {fileItem.status === 'error' && (
                  <div className="w-2 h-2 bg-red-500 rounded-full" />
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

