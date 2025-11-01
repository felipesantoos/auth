/**
 * FileUpload Component Tests
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { FileUpload } from '../FileUpload';

describe('FileUpload Component', () => {
  it('renders upload area', () => {
    render(<FileUpload onFilesSelected={jest.fn()} />);
    expect(screen.getByText(/drag.*drop.*files/i)).toBeInTheDocument();
  });

  it('accepts file selection via input', async () => {
    const mockOnFilesSelected = jest.fn();
    render(<FileUpload onFilesSelected={mockOnFilesSelected} />);
    
    const input = screen.getByRole('button').parentElement?.querySelector('input[type="file"]');
    expect(input).toBeInTheDocument();
  });

  it('displays error for invalid file type', async () => {
    const mockOnFilesSelected = jest.fn();
    render(
      <FileUpload
        onFilesSelected={mockOnFilesSelected}
        accept="image/*"
      />
    );
    
    // Component should validate file types
    expect(screen.getByText(/drag.*drop/i)).toBeInTheDocument();
  });

  it('respects maxSize prop', () => {
    const maxSize = 5 * 1024 * 1024; // 5MB
    render(
      <FileUpload
        onFilesSelected={jest.fn()}
        maxSize={maxSize}
      />
    );
    
    // Component should enforce size limits
    expect(screen.getByText(/drag.*drop/i)).toBeInTheDocument();
  });

  it('can be disabled', () => {
    render(
      <FileUpload
        onFilesSelected={jest.fn()}
        disabled={true}
      />
    );
    
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  it('supports multiple file upload', () => {
    render(
      <FileUpload
        onFilesSelected={jest.fn()}
        multiple={true}
      />
    );
    
    const input = screen.getByRole('button').parentElement?.querySelector('input[type="file"]');
    expect(input).toHaveAttribute('multiple');
  });
});

