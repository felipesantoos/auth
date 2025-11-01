/**
 * Input Component Tests
 * Unit tests for the Input UI component
 * 
 * Tests:
 * - Render with label
 * - Error state
 * - Value changes
 * - ARIA attributes
 * - Required state
 * 
 * Compliance: 08e-frontend-testing.md Section 3.5
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { Input } from '../input';

describe('Input Component', () => {
  it('should render input with label', () => {
    render(<Input label="Email" />);
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
  });

  it('should display error message', () => {
    render(<Input label="Password" error="Password is required" />);
    
    expect(screen.getByText(/password is required/i)).toBeInTheDocument();
  });

  it('should handle value changes', async () => {
    const user = userEvent.setup();
    const handleChange = vi.fn();
    
    render(<Input label="Name" onChange={handleChange} />);
    
    const input = screen.getByLabelText(/name/i);
    await user.type(input, 'John');
    
    expect(handleChange).toHaveBeenCalled();
    expect(input).toHaveValue('John');
  });

  it('should show required indicator when required', () => {
    render(<Input label="Email" required />);
    
    const input = screen.getByLabelText(/email/i);
    expect(input).toBeRequired();
  });

  it('should have correct ARIA attributes when error is present', () => {
    render(<Input label="Email" error="Invalid email" />);
    
    const input = screen.getByLabelText(/email/i);
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(input).toHaveAttribute('aria-describedby');
  });

  it('should render with placeholder', () => {
    render(<Input label="Email" placeholder="Enter your email" />);
    
    expect(screen.getByPlaceholderText(/enter your email/i)).toBeInTheDocument();
  });

  it('should support different input types', () => {
    const { rerender } = render(<Input label="Email" type="email" />);
    expect(screen.getByLabelText(/email/i)).toHaveAttribute('type', 'email');
    
    rerender(<Input label="Password" type="password" />);
    expect(screen.getByLabelText(/password/i)).toHaveAttribute('type', 'password');
    
    rerender(<Input label="Number" type="number" />);
    expect(screen.getByLabelText(/number/i)).toHaveAttribute('type', 'number');
  });

  it('should be disabled when disabled prop is true', () => {
    render(<Input label="Email" disabled />);
    
    expect(screen.getByLabelText(/email/i)).toBeDisabled();
  });

  it('should accept custom className', () => {
    render(<Input label="Email" className="custom-input" />);
    
    expect(screen.getByLabelText(/email/i)).toHaveClass('custom-input');
  });

  it('should link label to input with htmlFor and id', () => {
    render(<Input label="Email" />);
    
    const input = screen.getByLabelText(/email/i);
    const label = screen.getByText(/email/i);
    
    expect(input.id).toBeTruthy();
    expect(label).toHaveAttribute('for', input.id);
  });

  it('should not show error when error prop is undefined', () => {
    render(<Input label="Email" />);
    
    const errorText = screen.queryByRole('alert');
    expect(errorText).not.toBeInTheDocument();
  });

  it('should forward ref correctly', () => {
    const ref = vi.fn();
    
    render(<Input label="Email" ref={ref} />);
    
    expect(ref).toHaveBeenCalled();
  });
});

