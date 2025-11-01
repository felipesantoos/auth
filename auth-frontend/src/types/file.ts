/**
 * File Upload & Storage Types
 * TypeScript interfaces for file operations
 */

export enum StorageProvider {
  LOCAL = 'local',
  S3 = 's3',
  AZURE = 'azure',
  GCS = 'gcs',
  CLOUDINARY = 'cloudinary',
  CLOUDFLARE = 'cloudflare',
}

export interface FileInfo {
  id: string;
  filename: string;
  url: string;
  size: number;
  mime_type: string;
  uploaded_at?: string;
}

export interface FileUploadResponse {
  id: string;
  filename: string;
  url: string;
  size: number;
  mime_type: string;
  checksum: string;
  duplicate?: boolean;
}

export interface FileInfoDetailed {
  id: string;
  filename: string;
  url: string;
  size: number;
  mime_type: string;
  checksum: string;
  is_public: boolean;
  tags: string[];
  uploaded_at?: string;
}

export interface FileListResponse {
  data: FileInfo[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
  };
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percent: number;
  status: 'uploading' | 'completed' | 'error';
}

export interface PresignedUrlResponse {
  url: string;
  fields: Record<string, string>;
  file_path: string;
  file_id: string;
  expires_in: number;
}

export interface PresignedUrlRequest {
  filename: string;
  mime_type: string;
  file_size: number;
}

export interface CompleteUploadRequest {
  upload_id: string;
  file_size: number;
  checksum?: string;
}

export interface ChunkedUploadInitRequest {
  filename: string;
  mime_type: string;
  total_size: number;
}

export interface ChunkedUploadInitResponse {
  upload_id: string;
  file_id: string;
  chunk_size: number;
}

export interface ChunkedUploadChunkResponse {
  part_number: number;
  etag: string;
  uploaded: number;
}

export interface ChunkedUploadCompleteResponse {
  id: string;
  url: string;
  size: number;
}

export interface ChunkedUploadState {
  uploadId: string;
  fileId: string;
  chunkSize: number;
  totalChunks: number;
  uploadedChunks: number;
  progress: number;
  status: 'init' | 'uploading' | 'completed' | 'error' | 'aborted';
  error?: string;
}

export interface FileShareRequest {
  share_with_user_id: string;
  permission: 'read' | 'write';
  expires_hours?: number;
}

export interface FileShareResponse {
  share_id: string;
  file_id: string;
  shared_with: string;
  permission: 'read' | 'write';
  expires_at?: string;
}

export interface AvatarUploadResponse {
  avatar_url: string;
  message: string;
}

export interface FileValidationError {
  field: string;
  message: string;
}

export interface FileValidation {
  valid: boolean;
  errors: string[];
}

export type FileType = 'image' | 'video' | 'audio' | 'document' | 'all';

export interface FileFilter {
  file_type?: FileType;
  page?: number;
  per_page?: number;
}

// Utility type for uploaded file item
export interface UploadedFileItem {
  id: string;
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  error?: string;
  url?: string;
  preview?: string;
}

