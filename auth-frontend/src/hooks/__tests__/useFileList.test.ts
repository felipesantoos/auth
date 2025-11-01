/**
 * useFileList Hook Tests
 */
import { renderHook, act } from '@testing-library/react';
import { useFileList } from '../useFileList';
import { fileService } from '../../infra/services/FileService';
import { FileInfo } from '../../types/file';

jest.mock('../../infra/services/FileService');

const mockFiles: FileInfo[] = [
  {
    id: '1',
    original_filename: 'test1.jpg',
    file_size: 1024,
    mime_type: 'image/jpeg',
    url: 'http://example.com/test1.jpg',
    created_at: '2025-01-01T00:00:00Z',
    uploaded_by: 'user1',
    storage_provider: 'local',
    checksum: 'abc123',
    file_path: '/uploads/test1.jpg'
  },
  {
    id: '2',
    original_filename: 'test2.png',
    file_size: 2048,
    mime_type: 'image/png',
    url: 'http://example.com/test2.png',
    created_at: '2025-01-02T00:00:00Z',
    uploaded_by: 'user1',
    storage_provider: 'local',
    checksum: 'def456',
    file_path: '/uploads/test2.png'
  }
];

describe('useFileList Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('initializes with default state', () => {
    const { result } = renderHook(() => useFileList());
    
    expect(result.current.files).toEqual([]);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('fetches files successfully', async () => {
    (fileService.listFiles as jest.Mock).mockResolvedValue({
      files: mockFiles,
      total: 2
    });

    const { result } = renderHook(() => useFileList());

    await act(async () => {
      await result.current.fetchFiles();
    });

    expect(result.current.files).toEqual(mockFiles);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('handles fetch error', async () => {
    const mockError = new Error('Fetch failed');
    (fileService.listFiles as jest.Mock).mockRejectedValue(mockError);

    const { result } = renderHook(() => useFileList());

    await act(async () => {
      await result.current.fetchFiles();
    });

    expect(result.current.files).toEqual([]);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe('Fetch failed');
  });

  it('deletes file successfully', async () => {
    (fileService.listFiles as jest.Mock).mockResolvedValue({
      files: mockFiles,
      total: 2
    });
    (fileService.deleteFile as jest.Mock).mockResolvedValue(true);

    const { result } = renderHook(() => useFileList());

    // Fetch files first
    await act(async () => {
      await result.current.fetchFiles();
    });

    // Delete a file
    await act(async () => {
      await result.current.deleteFile('1');
    });

    expect(fileService.deleteFile).toHaveBeenCalledWith('1');
  });

  it('sets loading state during fetch', async () => {
    (fileService.listFiles as jest.Mock).mockImplementation(() => {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({ files: mockFiles, total: 2 });
        }, 100);
      });
    });

    const { result } = renderHook(() => useFileList());

    act(() => {
      result.current.fetchFiles();
    });

    expect(result.current.loading).toBe(true);
  });

  it('refreshes file list', async () => {
    (fileService.listFiles as jest.Mock).mockResolvedValue({
      files: mockFiles,
      total: 2
    });

    const { result } = renderHook(() => useFileList());

    await act(async () => {
      await result.current.refresh();
    });

    expect(result.current.files).toEqual(mockFiles);
    expect(fileService.listFiles).toHaveBeenCalled();
  });
});

