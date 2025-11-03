/**
 * ImageGallery Component Tests
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ImageGallery } from '../ImageGallery';
import type { FileInfo } from '../../../types/file';

const mockImages: FileInfo[] = [
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

describe('ImageGallery Component', () => {
  it('renders gallery with images', () => {
    render(<ImageGallery images={mockImages} />);
    
    const images = screen.getAllByRole('img');
    expect(images.length).toBe(2);
  });

  it('displays empty state when no images', () => {
    render(<ImageGallery images={[]} />);
    expect(screen.getByText(/no images/i)).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<ImageGallery images={[]} loading={true} />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('renders delete button for each image', () => {
    const mockOnDelete = jest.fn();
    render(<ImageGallery images={mockImages} onDelete={mockOnDelete} />);
    
    const deleteButtons = screen.getAllByText(/delete/i);
    expect(deleteButtons.length).toBe(2);
  });

  it('renders image with correct alt text', () => {
    render(<ImageGallery images={mockImages} />);
    
    expect(screen.getByAltText('test1.jpg')).toBeInTheDocument();
    expect(screen.getByAltText('test2.png')).toBeInTheDocument();
  });
});

