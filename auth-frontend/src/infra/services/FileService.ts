/**
 * File Service Implementation
 * Handles all file upload and management operations
 */

import type { AxiosProgressEvent } from 'axios';
import axios from 'axios';
import type { IFileService } from '../../core/interfaces/secondary/IFileService';
import type {
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
} from '../../types/file';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

export class FileService implements IFileService {
  private apiClient = axios.create({
    baseURL: API_BASE_URL,
  });

  constructor() {
    // Add auth token interceptor
    this.apiClient.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  async uploadFile(
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.apiClient.post<FileUploadResponse>(
      '/api/files/upload',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent: AxiosProgressEvent) => {
          if (onProgress && progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(percent);
          }
        },
      }
    );

    return response.data;
  }

  async listFiles(filter: FileFilter): Promise<FileListResponse> {
    const response = await this.apiClient.get<FileListResponse>('/api/files', {
      params: filter,
    });
    return response.data;
  }

  async getFileInfo(fileId: string): Promise<FileInfoDetailed> {
    const response = await this.apiClient.get<FileInfoDetailed>(`/api/files/${fileId}`);
    return response.data;
  }

  async downloadFile(fileId: string): Promise<{ url: string }> {
    const response = await this.apiClient.get<{ url: string }>(
      `/api/files/${fileId}/download`
    );
    return response.data;
  }

  async deleteFile(fileId: string): Promise<void> {
    await this.apiClient.delete(`/api/files/${fileId}`);
  }

  async shareFile(
    fileId: string,
    request: FileShareRequest
  ): Promise<FileShareResponse> {
    const response = await this.apiClient.post<FileShareResponse>(
      `/api/files/${fileId}/share`,
      request
    );
    return response.data;
  }

  async getPresignedUrl(request: PresignedUrlRequest): Promise<PresignedUrlResponse> {
    const response = await this.apiClient.post<PresignedUrlResponse>(
      '/api/files/presigned-url',
      request
    );
    return response.data;
  }

  async completeDirectUpload(request: CompleteUploadRequest): Promise<{ url: string }> {
    const response = await this.apiClient.post<{ url: string }>(
      '/api/files/complete-upload',
      request
    );
    return response.data;
  }

  async initChunkedUpload(
    request: ChunkedUploadInitRequest
  ): Promise<ChunkedUploadInitResponse> {
    const response = await this.apiClient.post<ChunkedUploadInitResponse>(
      '/api/upload/chunked/init',
      request
    );
    return response.data;
  }

  async uploadChunk(
    uploadId: string,
    chunkNumber: number,
    chunk: Blob,
    onProgress?: (progress: number) => void
  ): Promise<ChunkedUploadChunkResponse> {
    const formData = new FormData();
    formData.append('chunk', chunk);

    const response = await this.apiClient.post<ChunkedUploadChunkResponse>(
      `/api/upload/chunked/${uploadId}/chunk`,
      formData,
      {
        params: { chunk_number: chunkNumber },
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent: AxiosProgressEvent) => {
          if (onProgress && progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(percent);
          }
        },
      }
    );

    return response.data;
  }

  async completeChunkedUpload(uploadId: string): Promise<ChunkedUploadCompleteResponse> {
    const response = await this.apiClient.post<ChunkedUploadCompleteResponse>(
      `/api/upload/chunked/${uploadId}/complete`
    );
    return response.data;
  }

  async abortChunkedUpload(uploadId: string): Promise<void> {
    await this.apiClient.delete(`/api/upload/chunked/${uploadId}/abort`);
  }

  async uploadAvatar(file: File): Promise<{ avatar_url: string }> {
    const formData = new FormData();
    formData.append('avatar', file);

    const response = await this.apiClient.post<{ avatar_url: string }>(
      '/api/auth/profile/avatar',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );

    return response.data;
  }

  async deleteAvatar(): Promise<void> {
    await this.apiClient.delete('/api/auth/profile/avatar');
  }
}

// Singleton instance
export const fileService = new FileService();

