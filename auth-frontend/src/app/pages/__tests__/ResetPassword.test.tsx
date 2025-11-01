/**
 * ResetPassword Page Tests
 * Component tests for the password reset page
 * 
 * Tests:
 * - Form rendering with token from URL
 * - Password validation
 * - Password match validation
 * - Successful reset
 * - Invalid token handling
 * - Navigation after success
 * - Loading states
 * 
 * Compliance: 08e-frontend-testing.md Section 3.5
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { ResetPassword } from '../ResetPassword';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DIContainer from '../../dicontainer/container';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('../../dicontainer/container', () => ({
  default: {
    getAuthService: vi.fn(),
  },
}));

describe('ResetPassword Page', () => {
  const mockAuthService = {
    resetPassword: vi.fn(),
  };

  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    (DIContainer.getAuthService as any).mockReturnValue(mockAuthService);
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  const renderComponent = (token = 'valid-token-123') => {
    return render(
      <MemoryRouter initialEntries={[`/reset-password?token=${token}`]}>
        <QueryClientProvider client={queryClient}>
          <ResetPassword />
        </QueryClientProvider>
      </MemoryRouter>
    );
  };

  it('should render reset password form', () => {
    renderComponent();

    expect(screen.getByText('Redefinir Senha')).toBeInTheDocument();
    expect(screen.getByLabelText(/nova senha/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirmar senha/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /redefinir senha/i })).toBeInTheDocument();
  });

  it('should extract token from URL', () => {
    renderComponent('token-from-url');

    // Token should be in the form (hidden field)
    const form = screen.getByRole('button', { name: /redefinir senha/i }).closest('form');
    expect(form).toBeInTheDocument();
  });

  it('should validate password strength', async () => {
    const user = userEvent.setup({ delay: null });
    renderComponent();

    const passwordInput = screen.getByLabelText(/nova senha/i);
    await user.type(passwordInput, '123'); // Too short
    await user.tab();

    await waitFor(() => {
      expect(screen.getByText(/senha.*8 caracteres/i)).toBeInTheDocument();
    });
  });

  it('should validate password match', async () => {
    const user = userEvent.setup({ delay: null });
    renderComponent();

    const passwordInput = screen.getByLabelText(/nova senha/i);
    const confirmInput = screen.getByLabelText(/confirmar senha/i);

    await user.type(passwordInput, 'Password123!');
    await user.type(confirmInput, 'DifferentPassword!');
    await user.tab();

    await waitFor(() => {
      expect(screen.getByText(/senhas.*não.*coincidem/i)).toBeInTheDocument();
    });
  });

  it('should reset password successfully', async () => {
    const user = userEvent.setup({ delay: null });
    mockAuthService.resetPassword.mockResolvedValue({ message: 'Password reset successful' });

    renderComponent('valid-token');

    // Fill form
    await user.type(screen.getByLabelText(/nova senha/i), 'NewPassword123!');
    await user.type(screen.getByLabelText(/confirmar senha/i), 'NewPassword123!');

    // Submit
    await user.click(screen.getByRole('button', { name: /redefinir senha/i }));

    await waitFor(() => {
      expect(mockAuthService.resetPassword).toHaveBeenCalledWith({
        reset_token: 'valid-token',
        new_password: 'NewPassword123!',
        client_id: undefined,
      });
    });

    // Should show success message
    await waitFor(() => {
      expect(screen.getByText(/senha redefinida/i)).toBeInTheDocument();
    });

    // Should navigate to login after 2 seconds
    vi.advanceTimersByTime(2000);
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  it('should handle invalid token error', async () => {
    const user = userEvent.setup({ delay: null });
    
    mockAuthService.resetPassword.mockRejectedValue({
      response: {
        data: {
          detail: 'Invalid or expired token',
        },
      },
    });

    renderComponent('invalid-token');

    await user.type(screen.getByLabelText(/nova senha/i), 'NewPassword123!');
    await user.type(screen.getByLabelText(/confirmar senha/i), 'NewPassword123!');
    await user.click(screen.getByRole('button', { name: /redefinir senha/i }));

    await waitFor(() => {
      expect(screen.getByText(/token.*expirado/i)).toBeInTheDocument();
    });

    // Should not navigate
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should show loading state during reset', async () => {
    const user = userEvent.setup({ delay: null });
    
    mockAuthService.resetPassword.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({ message: 'Success' }), 100))
    );

    renderComponent();

    await user.type(screen.getByLabelText(/nova senha/i), 'NewPassword123!');
    await user.type(screen.getByLabelText(/confirmar senha/i), 'NewPassword123!');
    
    const submitButton = screen.getByRole('button', { name: /redefinir senha/i });
    await user.click(submitButton);

    // Button should be disabled during loading
    await waitFor(() => {
      expect(submitButton).toBeDisabled();
    });
  });

  it('should include client_id if provided', async () => {
    const user = userEvent.setup({ delay: null });
    mockAuthService.resetPassword.mockResolvedValue({ message: 'Success' });

    renderComponent();

    // Fill client_id
    const clientIdInput = screen.getByPlaceholderText(/client_id/i);
    await user.type(clientIdInput, 'test-client-123');

    // Fill passwords
    await user.type(screen.getByLabelText(/nova senha/i), 'NewPassword123!');
    await user.type(screen.getByLabelText(/confirmar senha/i), 'NewPassword123!');

    // Submit
    await user.click(screen.getByRole('button', { name: /redefinir senha/i }));

    await waitFor(() => {
      expect(mockAuthService.resetPassword).toHaveBeenCalledWith(
        expect.objectContaining({
          client_id: 'test-client-123',
        })
      );
    });
  });

  it('should hide form after successful reset', async () => {
    const user = userEvent.setup({ delay: null });
    mockAuthService.resetPassword.mockResolvedValue({ message: 'Success' });

    renderComponent();

    await user.type(screen.getByLabelText(/nova senha/i), 'NewPassword123!');
    await user.type(screen.getByLabelText(/confirmar senha/i), 'NewPassword123!');
    await user.click(screen.getByRole('button', { name: /redefinir senha/i }));

    // Wait for success message
    await waitFor(() => {
      expect(screen.getByText(/senha redefinida/i)).toBeInTheDocument();
    });

    // Form should be hidden
    expect(screen.queryByLabelText(/nova senha/i)).not.toBeInTheDocument();
  });

  it('should have link back to login', () => {
    renderComponent();

    const loginLink = screen.getByText(/voltar para o login/i);
    expect(loginLink).toBeInTheDocument();
    expect(loginLink.closest('a')).toHaveAttribute('href', '/login');
  });
});

