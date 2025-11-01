/**
 * File Service Interface (Secondary Port)
 * Defines the contract for file storage operations
 */

import {
  FileUploadResponse,
  FileListResponse,
  FileInfoDetailed,
  PresignedUrlRequest,
  PresignedUrlResponse,
  CompleteUploadRequest,
  ChunkedUploadInitRequest,
  ChunkedUploadInitResponse,
  ChunkedUploadChunkResponse,
  ChunkedUploadCompleteResponse,
  FileShareRequest,
  FileShareResponse,
  FileFilter,
} from '../../../types/file';

export interface IFileService {
  /**
   * Upload file with progress tracking
   */
  uploadFile(
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<FileUploadResponse>;

  /**
   * List user files with pagination
   */
  listFiles(filter: FileFilter): Promise<FileListResponse>;

  /**
   * Get file information
   */
  getFileInfo(fileId: string): Promise<FileInfoDetailed>;

  /**
   * Download file (get download URL)
   */
  downloadFile(fileId: string): Promise<{ url: string }>;

  /**
   * Delete file
   */
  deleteFile(fileId: string): Promise<void>;

  /**
   * Share file with another user
   */
  shareFile(fileId: string, request: FileShareRequest): Promise<FileShareResponse>;

  /**
   * Get presigned URL for direct upload
   */
  getPresignedUrl(request: PresignedUrlRequest): Promise<PresignedUrlResponse>;

  /**
   * Complete direct upload
   */
  completeDirectUpload(request: CompleteUploadRequest): Promise<{ url: string }>;

  /**
   * Initialize chunked upload
   */
  initChunkedUpload(request: ChunkedUploadInitRequest): Promise<ChunkedUploadInitResponse>;

  /**
   * Upload chunk
   */
  uploadChunk(
    uploadId: string,
    chunkNumber: number,
    chunk: Blob,
    onProgress?: (progress: number) => void
  ): Promise<ChunkedUploadChunkResponse>;

  /**
   * Complete chunked upload
   */
  completeChunkedUpload(uploadId: string): Promise<ChunkedUploadCompleteResponse>;

  /**
   * Abort chunked upload
   */
  abortChunkedUpload(uploadId: string): Promise<void>;

  /**
   * Upload avatar
   */
  uploadAvatar(file: File): Promise<{ avatar_url: string }>;

  /**
   * Delete avatar
   */
  deleteAvatar(): Promise<void>;
}

