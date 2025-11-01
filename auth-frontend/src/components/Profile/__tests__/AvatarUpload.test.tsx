/**
 * AvatarUpload Component Tests
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { AvatarUpload } from '../AvatarUpload';

describe('AvatarUpload Component', () => {
  it('renders upload button when no avatar', () => {
    render(<AvatarUpload currentAvatarUrl={null} onUpload={jest.fn()} />);
    expect(screen.getByText(/upload avatar/i)).toBeInTheDocument();
  });

  it('displays current avatar when provided', () => {
    const avatarUrl = 'http://example.com/avatar.jpg';
    render(<AvatarUpload currentAvatarUrl={avatarUrl} onUpload={jest.fn()} />);
    
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', avatarUrl);
  });

  it('shows remove button when avatar exists', () => {
    render(
      <AvatarUpload
        currentAvatarUrl="http://example.com/avatar.jpg"
        onUpload={jest.fn()}
        onRemove={jest.fn()}
      />
    );
    
    expect(screen.getByText(/remove/i)).toBeInTheDocument();
  });

  it('calls onRemove when remove button clicked', () => {
    const mockOnRemove = jest.fn();
    render(
      <AvatarUpload
        currentAvatarUrl="http://example.com/avatar.jpg"
        onUpload={jest.fn()}
        onRemove={mockOnRemove}
      />
    );
    
    const removeButton = screen.getByText(/remove/i);
    fireEvent.click(removeButton);
    
    expect(mockOnRemove).toHaveBeenCalled();
  });

  it('can be disabled', () => {
    render(
      <AvatarUpload
        currentAvatarUrl={null}
        onUpload={jest.fn()}
        disabled={true}
      />
    );
    
    const button = screen.getByText(/upload avatar/i);
    expect(button).toBeDisabled();
  });

  it('shows loading state', () => {
    render(
      <AvatarUpload
        currentAvatarUrl={null}
        onUpload={jest.fn()}
        loading={true}
      />
    );
    
    expect(screen.getByText(/uploading/i)).toBeInTheDocument();
  });
});

