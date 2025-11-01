/**
 * ForgotPassword Page Tests
 * Component tests for the password reset request page
 * 
 * Tests:
 * - Form rendering
 * - Email validation
 * - Successful request
 * - Error handling
 * - Success message display
 * - Loading states
 * 
 * Compliance: 08e-frontend-testing.md Section 3.5
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { ForgotPassword } from '../ForgotPassword';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DIContainer from '../../dicontainer/container';

vi.mock('../../dicontainer/container', () => ({
  default: {
    getAuthService: vi.fn(),
  },
}));

describe('ForgotPassword Page', () => {
  const mockAuthService = {
    forgotPassword: vi.fn(),
  };

  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    (DIContainer.getAuthService as any).mockReturnValue(mockAuthService);
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
  });

  const renderComponent = () => {
    return render(
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <ForgotPassword />
        </QueryClientProvider>
      </BrowserRouter>
    );
  };

  it('should render forgot password form', () => {
    renderComponent();

    expect(screen.getByText('Esqueceu a Senha?')).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /enviar link/i })).toBeInTheDocument();
  });

  it('should validate empty email', async () => {
    const user = userEvent.setup();
    renderComponent();

    const submitButton = screen.getByRole('button', { name: /enviar link/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/email.*obrigatório/i)).toBeInTheDocument();
    });

    expect(mockAuthService.forgotPassword).not.toHaveBeenCalled();
  });

  it('should validate email format', async () => {
    const user = userEvent.setup();
    renderComponent();

    const emailInput = screen.getByLabelText(/email/i);
    await user.type(emailInput, 'invalid-email');
    await user.tab();

    await waitFor(() => {
      expect(screen.getByText(/email.*inválido/i)).toBeInTheDocument();
    });
  });

  it('should send reset email successfully', async () => {
    const user = userEvent.setup();
    mockAuthService.forgotPassword.mockResolvedValue({ message: 'Email sent' });

    renderComponent();

    // Fill email
    const emailInput = screen.getByLabelText(/email/i);
    await user.type(emailInput, 'test@example.com');

    // Submit
    await user.click(screen.getByRole('button', { name: /enviar link/i }));

    await waitFor(() => {
      expect(mockAuthService.forgotPassword).toHaveBeenCalledWith({
        email: 'test@example.com',
        client_id: undefined,
      });
    });

    // Should show success message
    await waitFor(() => {
      expect(screen.getByText(/email enviado/i)).toBeInTheDocument();
    });
  });

  it('should show loading state during request', async () => {
    const user = userEvent.setup();
    
    mockAuthService.forgotPassword.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({ message: 'Email sent' }), 100))
    );

    renderComponent();

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    
    const submitButton = screen.getByRole('button', { name: /enviar link/i });
    await user.click(submitButton);

    // Button should be disabled during loading
    await waitFor(() => {
      expect(submitButton).toBeDisabled();
    });

    // Wait for success
    await waitFor(() => {
      expect(screen.getByText(/email enviado/i)).toBeInTheDocument();
    });
  });

  it('should handle server errors', async () => {
    const user = userEvent.setup();
    
    mockAuthService.forgotPassword.mockRejectedValue(
      new Error('Server error')
    );

    renderComponent();

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.click(screen.getByRole('button', { name: /enviar link/i }));

    await waitFor(() => {
      expect(screen.getByText(/erro/i)).toBeInTheDocument();
    });
  });

  it('should include client_id if provided', async () => {
    const user = userEvent.setup();
    mockAuthService.forgotPassword.mockResolvedValue({ message: 'Email sent' });

    renderComponent();

    // Fill client_id
    const clientIdInput = screen.getByPlaceholderText(/client_id/i);
    await user.type(clientIdInput, 'test-client-123');

    // Fill email
    await user.type(screen.getByLabelText(/email/i), 'test@example.com');

    // Submit
    await user.click(screen.getByRole('button', { name: /enviar link/i }));

    await waitFor(() => {
      expect(mockAuthService.forgotPassword).toHaveBeenCalledWith({
        email: 'test@example.com',
        client_id: 'test-client-123',
      });
    });
  });

  it('should have link back to login', () => {
    renderComponent();

    const loginLink = screen.getByText(/voltar para o login/i);
    expect(loginLink).toBeInTheDocument();
    expect(loginLink.closest('a')).toHaveAttribute('href', '/login');
  });

  it('should hide form after successful submission', async () => {
    const user = userEvent.setup();
    mockAuthService.forgotPassword.mockResolvedValue({ message: 'Email sent' });

    renderComponent();

    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.click(screen.getByRole('button', { name: /enviar link/i }));

    // Wait for success message
    await waitFor(() => {
      expect(screen.getByText(/email enviado/i)).toBeInTheDocument();
    });

    // Form should be hidden
    expect(screen.queryByLabelText(/email/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /enviar link/i })).not.toBeInTheDocument();
  });
});

