/**
 * End-to-End File Upload Flow Test
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { FilesPage } from '../../pages/Files/FilesPage';
import { fileService } from '../../infra/services/FileService';

jest.mock('../../infra/services/FileService');

describe('File Upload E2E Flow', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('completes full upload flow: select -> upload -> list -> delete', async () => {
    // Mock API responses
    const mockFile = {
      id: 'file123',
      original_filename: 'test.jpg',
      file_size: 1024,
      mime_type: 'image/jpeg',
      url: 'http://example.com/test.jpg',
      created_at: new Date().toISOString(),
      uploaded_by: 'user1',
      storage_provider: 'local',
      checksum: 'abc123',
      file_path: '/uploads/test.jpg'
    };

    (fileService.listFiles as jest.Mock).mockResolvedValue({
      files: [],
      total: 0
    });

    (fileService.uploadFile as jest.Mock).mockResolvedValue(mockFile);

    (fileService.deleteFile as jest.Mock).mockResolvedValue(true);

    // Render the FilesPage
    render(<FilesPage />);

    // 1. Verify page loads
    await waitFor(() => {
      expect(screen.getByText(/my files/i)).toBeInTheDocument();
    });

    // 2. Upload a file
    const file = new File(['test content'], 'test.jpg', { type: 'image/jpeg' });
    const input = screen.getByLabelText(/upload/i);
    
    await act(async () => {
      fireEvent.change(input, { target: { files: [file] } });
    });

    // 3. Verify upload success
    await waitFor(() => {
      expect(fileService.uploadFile).toHaveBeenCalled();
    });

    // 4. Mock list with uploaded file
    (fileService.listFiles as jest.Mock).mockResolvedValue({
      files: [mockFile],
      total: 1
    });

    // 5. Refresh to see uploaded file
    await waitFor(() => {
      expect(screen.getByText('test.jpg')).toBeInTheDocument();
    });

    // 6. Delete the file
    const deleteButton = screen.getByText(/delete/i);
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(fileService.deleteFile).toHaveBeenCalledWith('file123');
    });
  });

  it('handles upload errors gracefully', async () => {
    const mockError = new Error('Upload failed');
    (fileService.uploadFile as jest.Mock).mockRejectedValue(mockError);

    render(<FilesPage />);

    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
    const input = screen.getByLabelText(/upload/i);
    
    await act(async () => {
      fireEvent.change(input, { target: { files: [file] } });
    });

    // Verify error is displayed
    await waitFor(() => {
      expect(screen.getByText(/failed/i)).toBeInTheDocument();
    });
  });

  it('shows upload progress', async () => {
    (fileService.uploadFile as jest.Mock).mockImplementation(() => {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            id: 'file123',
            filename: 'test.jpg'
          });
        }, 100);
      });
    });

    render(<FilesPage />);

    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
    const input = screen.getByLabelText(/upload/i);
    
    act(() => {
      fireEvent.change(input, { target: { files: [file] } });
    });

    // Verify uploading state
    expect(screen.getByText(/uploading/i)).toBeInTheDocument();
  });

  it('validates file size before upload', async () => {
    render(<FilesPage />);

    // Create a file larger than allowed (e.g., > 100MB)
    const largeFile = new File(['A'.repeat(101 * 1024 * 1024)], 'large.jpg', { 
      type: 'image/jpeg' 
    });
    
    const input = screen.getByLabelText(/upload/i);
    
    await act(async () => {
      fireEvent.change(input, { target: { files: [largeFile] } });
    });

    // Verify error message for file too large
    await waitFor(() => {
      expect(screen.getByText(/too large|exceeds/i)).toBeInTheDocument();
    });
  });

  it('validates file type before upload', async () => {
    render(<FilesPage />);

    // Create an invalid file type
    const invalidFile = new File(['test'], 'test.exe', { 
      type: 'application/x-msdownload' 
    });
    
    const input = screen.getByLabelText(/upload/i);
    
    await act(async () => {
      fireEvent.change(input, { target: { files: [invalidFile] } });
    });

    // Verify error message for invalid file type
    await waitFor(() => {
      expect(screen.getByText(/not allowed|invalid type/i)).toBeInTheDocument();
    });
  });
});

// Helper for async act
import { act } from '@testing-library/react';

