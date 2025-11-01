/**
 * useFileUpload Hook Tests
 */
import { renderHook, act } from '@testing-library/react';
import { useFileUpload } from '../useFileUpload';
import { fileService } from '../../infra/services/FileService';

jest.mock('../../infra/services/FileService');

describe('useFileUpload Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('initializes with default state', () => {
    const { result } = renderHook(() => useFileUpload());
    
    expect(result.current.uploading).toBe(false);
    expect(result.current.progress).toBe(0);
    expect(result.current.error).toBeNull();
    expect(result.current.uploadedFile).toBeNull();
  });

  it('uploads file successfully', async () => {
    const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' });
    const mockResponse = {
      id: 'file123',
      filename: 'test.txt',
      url: 'http://example.com/test.txt'
    };

    (fileService.uploadFile as jest.Mock).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useFileUpload());

    await act(async () => {
      await result.current.upload(mockFile);
    });

    expect(result.current.uploading).toBe(false);
    expect(result.current.uploadedFile).toEqual(mockResponse);
    expect(result.current.error).toBeNull();
  });

  it('handles upload error', async () => {
    const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' });
    const mockError = new Error('Upload failed');

    (fileService.uploadFile as jest.Mock).mockRejectedValue(mockError);

    const { result } = renderHook(() => useFileUpload());

    await act(async () => {
      await result.current.upload(mockFile);
    });

    expect(result.current.uploading).toBe(false);
    expect(result.current.error).toBe('Upload failed');
    expect(result.current.uploadedFile).toBeNull();
  });

  it('tracks upload progress', async () => {
    const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' });
    
    (fileService.uploadFile as jest.Mock).mockImplementation(() => {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({ id: 'file123', filename: 'test.txt' });
        }, 100);
      });
    });

    const { result } = renderHook(() => useFileUpload());

    act(() => {
      result.current.upload(mockFile);
    });

    expect(result.current.uploading).toBe(true);
  });

  it('resets state', () => {
    const { result } = renderHook(() => useFileUpload());

    act(() => {
      result.current.reset();
    });

    expect(result.current.uploading).toBe(false);
    expect(result.current.progress).toBe(0);
    expect(result.current.error).toBeNull();
    expect(result.current.uploadedFile).toBeNull();
  });
});

