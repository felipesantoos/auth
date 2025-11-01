/**
 * useFileList Hook
 * Hook for listing and managing files
 */

import { useState, useEffect } from 'react';
import { fileService } from '../infra/services/FileService';
import { FileInfo, FileType } from '../types/file';

export function useFileList(fileType?: FileType, autoLoad: boolean = true) {
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  const loadFiles = async (pageNum: number = page) => {
    setLoading(true);
    setError(null);

    try {
      const result = await fileService.listFiles({
        file_type: fileType,
        page: pageNum,
        per_page: 20,
      });

      setFiles(result.data);
      setPage(result.pagination.page);
      setTotalPages(result.pagination.total_pages);
      setTotal(result.pagination.total);
      setLoading(false);
    } catch (err: any) {
      setError(err.message || 'Failed to load files');
      setLoading(false);
    }
  };

  const deleteFile = async (fileId: string) => {
    try {
      await fileService.deleteFile(fileId);
      setFiles(prev => prev.filter(f => f.id !== fileId));
      setTotal(prev => prev - 1);
    } catch (err: any) {
      throw new Error(err.message || 'Failed to delete file');
    }
  };

  const refresh = () => loadFiles(page);

  const nextPage = () => {
    if (page < totalPages) {
      loadFiles(page + 1);
    }
  };

  const prevPage = () => {
    if (page > 1) {
      loadFiles(page - 1);
    }
  };

  useEffect(() => {
    if (autoLoad) {
      loadFiles(1);
    }
  }, [fileType, autoLoad]);

  return {
    files,
    loading,
    error,
    page,
    totalPages,
    total,
    loadFiles,
    deleteFile,
    refresh,
    nextPage,
    prevPage,
  };
}

