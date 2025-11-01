/**
 * Dialog Component Tests
 * Unit tests for the Dialog UI component
 * 
 * Tests:
 * - Open/close
 * - Trigger interaction
 * - Content rendering
 * - Controlled state
 * 
 * Compliance: 08e-frontend-testing.md Section 3.5
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '../dialog';

describe('Dialog Component', () => {
  it('should render dialog trigger', () => {
    render(
      <Dialog>
        <DialogTrigger>Open Dialog</DialogTrigger>
        <DialogContent>
          <DialogTitle>Dialog Title</DialogTitle>
        </DialogContent>
      </Dialog>
    );
    
    expect(screen.getByText(/open dialog/i)).toBeInTheDocument();
  });

  it('should open dialog when trigger is clicked', async () => {
    const user = userEvent.setup();
    
    render(
      <Dialog>
        <DialogTrigger>Open</DialogTrigger>
        <DialogContent>
          <DialogTitle>Test Dialog</DialogTitle>
          <DialogDescription>Dialog content here</DialogDescription>
        </DialogContent>
      </Dialog>
    );
    
    // Dialog should not be visible initially
    expect(screen.queryByText(/test dialog/i)).not.toBeInTheDocument();
    
    // Click trigger
    await user.click(screen.getByText(/open/i));
    
    // Dialog should be visible
    await screen.findByText(/test dialog/i);
    expect(screen.getByText(/dialog content here/i)).toBeInTheDocument();
  });

  it('should render dialog header with title and description', async () => {
    const user = userEvent.setup();
    
    render(
      <Dialog>
        <DialogTrigger>Open</DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>My Title</DialogTitle>
            <DialogDescription>My Description</DialogDescription>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    );
    
    await user.click(screen.getByText(/open/i));
    
    expect(await screen.findByText(/my title/i)).toBeInTheDocument();
    expect(screen.getByText(/my description/i)).toBeInTheDocument();
  });

  it('should call onOpenChange when dialog state changes', async () => {
    const user = userEvent.setup();
    const handleOpenChange = vi.fn();
    
    render(
      <Dialog onOpenChange={handleOpenChange}>
        <DialogTrigger>Open</DialogTrigger>
        <DialogContent>
          <DialogTitle>Dialog</DialogTitle>
        </DialogContent>
      </Dialog>
    );
    
    await user.click(screen.getByText(/open/i));
    
    expect(handleOpenChange).toHaveBeenCalledWith(true);
  });

  it('should support controlled state', async () => {
    const handleOpenChange = vi.fn();
    
    const { rerender } = render(
      <Dialog open={false} onOpenChange={handleOpenChange}>
        <DialogTrigger>Open</DialogTrigger>
        <DialogContent>
          <DialogTitle>Controlled Dialog</DialogTitle>
        </DialogContent>
      </Dialog>
    );
    
    // Should not be visible when open=false
    expect(screen.queryByText(/controlled dialog/i)).not.toBeInTheDocument();
    
    // Rerender with open=true
    rerender(
      <Dialog open={true} onOpenChange={handleOpenChange}>
        <DialogTrigger>Open</DialogTrigger>
        <DialogContent>
          <DialogTitle>Controlled Dialog</DialogTitle>
        </DialogContent>
      </Dialog>
    );
    
    // Should be visible when open=true
    expect(await screen.findByText(/controlled dialog/i)).toBeInTheDocument();
  });

  it('should render custom content inside dialog', async () => {
    const user = userEvent.setup();
    
    render(
      <Dialog>
        <DialogTrigger>Open</DialogTrigger>
        <DialogContent>
          <DialogTitle>Custom Content</DialogTitle>
          <div data-testid="custom-content">
            <p>Custom paragraph</p>
            <button>Custom button</button>
          </div>
        </DialogContent>
      </Dialog>
    );
    
    await user.click(screen.getByText(/open/i));
    
    expect(await screen.findByTestId('custom-content')).toBeInTheDocument();
    expect(screen.getByText(/custom paragraph/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /custom button/i })).toBeInTheDocument();
  });
});

