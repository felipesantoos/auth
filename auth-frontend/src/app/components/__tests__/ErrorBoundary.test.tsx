/**
 * Error Boundary Component Tests
 * Verifies error catching and fallback UI rendering
 * 
 * Compliance: 08c-react-best-practices.md Section 5.3
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ErrorBoundary } from '../ErrorBoundary';

// Component that throws an error
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error message');
  }
  return <div>No error</div>;
};

describe('ErrorBoundary', () => {
  // Suppress console.error in tests
  const originalError = console.error;
  
  beforeEach(() => {
    console.error = vi.fn();
  });
  
  afterEach(() => {
    console.error = originalError;
  });

  it('should render children when there is no error', () => {
    render(
      <ErrorBoundary>
        <div>Test content</div>
      </ErrorBoundary>
    );

    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('should catch errors and display fallback UI', () => {
    // Suppress React's error logging
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByRole('heading', { name: /Algo deu errado/i })).toBeInTheDocument();
    expect(screen.getAllByText(/Test error message/i).length).toBeGreaterThan(0);
    
    consoleError.mockRestore();
  });

  it('should display error details in expandable section', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    const details = screen.getByText(/Detalhes do erro/i);
    expect(details).toBeInTheDocument();
    
    consoleError.mockRestore();
  });

  it('should display retry and go home buttons', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByRole('button', { name: /Tentar Novamente/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Ir para Início/i })).toBeInTheDocument();
    
    consoleError.mockRestore();
  });

  it('should use custom fallback if provided', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    const customFallback = <div>Custom error UI</div>;

    render(
      <ErrorBoundary fallback={customFallback}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Custom error UI')).toBeInTheDocument();
    expect(screen.queryByText(/Algo deu errado/i)).not.toBeInTheDocument();
    
    consoleError.mockRestore();
  });
});

