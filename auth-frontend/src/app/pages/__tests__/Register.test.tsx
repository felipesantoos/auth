/**
 * Register Page Tests
 * Component tests for the user registration page
 * 
 * Tests:
 * - Form rendering
 * - Field validations (required, email format, password strength)
 * - Successful registration
 * - Error handling
 * - Navigation after registration
 * - Loading states
 * 
 * Compliance: 08e-frontend-testing.md Section 3.5
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { Register } from '../Register';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../contexts/AuthContext';
import DIContainer from '../../dicontainer/container';
import { DuplicateEntityError } from '../../../core/domain/errors';

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
    getLogger: vi.fn(),
  },
}));

describe('Register Page', () => {
  const mockAuthService = {
    register: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
    isAuthenticated: vi.fn().mockReturnValue(false),
  };

  const mockLogger = {
    info: vi.fn(),
    error: vi.fn(),
    warn: vi.fn(),
    debug: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (DIContainer.getAuthService as any).mockReturnValue(mockAuthService);
    (DIContainer.getLogger as any).mockReturnValue(mockLogger);
  });

  const renderComponent = () => {
    return render(
      <BrowserRouter>
        <AuthProvider>
          <Register />
        </AuthProvider>
      </BrowserRouter>
    );
  };

  it('should render registration form', () => {
    renderComponent();

    expect(screen.getByRole('heading', { name: /criar conta/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/nome/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getAllByLabelText(/email/i)[0]).toBeInTheDocument();
    expect(screen.getByLabelText(/senha/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /criar conta/i })).toBeInTheDocument();
  });

  it('should show validation errors for empty fields', async () => {
    const user = userEvent.setup();
    renderComponent();

    const submitButton = screen.getByRole('button', { name: /criar conta/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/nome.*obrigatório/i)).toBeInTheDocument();
    });

    expect(mockAuthService.register).not.toHaveBeenCalled();
  });

  it('should validate email format', async () => {
    const user = userEvent.setup();
    renderComponent();

    const emailInputs = screen.getAllByLabelText(/email/i);
    const emailInput = emailInputs.find(input => input.getAttribute('placeholder') === 'seu@email.com');
    await user.type(emailInput!, 'invalid-email');
    await user.tab(); // Trigger blur

    await waitFor(() => {
      expect(screen.getByText(/email.*inválido/i)).toBeInTheDocument();
    });
  });

  it('should validate password strength', async () => {
    const user = userEvent.setup();
    renderComponent();

    const passwordInput = screen.getByLabelText(/senha/i);
    await user.type(passwordInput, '123'); // Too short
    await user.tab();

    await waitFor(() => {
      expect(screen.getByText(/senha.*8 caracteres/i)).toBeInTheDocument();
    });
  });

  it('should register successfully with valid data', async () => {
    const user = userEvent.setup();
    const mockUser = {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      name: 'Test User',
      isActive: true,
      emailVerified: false,
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    mockAuthService.register.mockResolvedValue(mockUser);

    renderComponent();

    // Fill form
    await user.type(screen.getByLabelText(/nome/i), 'Test User');
    await user.type(screen.getByLabelText(/username/i), 'testuser');
    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.type(screen.getByLabelText(/senha/i), 'Password123!');

    // Submit
    await user.click(screen.getByRole('button', { name: /criar conta/i }));

    await waitFor(() => {
      expect(mockAuthService.register).toHaveBeenCalledWith({
        username: 'testuser',
        email: 'test@example.com',
        password: 'Password123!',
        name: 'Test User',
        client_id: undefined,
      });
    });

    // Should navigate to dashboard
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('should handle duplicate email error', async () => {
    const user = userEvent.setup();
    
    mockAuthService.register.mockRejectedValue(
      new DuplicateEntityError('Email already exists')
    );

    renderComponent();

    // Fill form
    await user.type(screen.getByLabelText(/nome/i), 'Test User');
    await user.type(screen.getByLabelText(/username/i), 'testuser');
    const emailInputs = screen.getAllByLabelText(/email/i);
    const emailInput = emailInputs.find(input => input.getAttribute('placeholder') === 'seu@email.com');
    await user.type(emailInput!, 'duplicate@example.com');
    await user.type(screen.getByLabelText(/senha/i), 'Password123!');

    // Submit
    await user.click(screen.getByRole('button', { name: /criar conta/i }));

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(/já cadastrado/i)).toBeInTheDocument();
    });

    // Should not navigate
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should show loading state during registration', async () => {
    const user = userEvent.setup();
    
    mockAuthService.register.mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );

    renderComponent();

    // Fill form
    await user.type(screen.getByLabelText(/nome/i), 'Test User');
    await user.type(screen.getByLabelText(/username/i), 'testuser');
    const emailInputs = screen.getAllByLabelText(/email/i);
    const emailInput = emailInputs.find(input => input.getAttribute('placeholder') === 'seu@email.com');
    await user.type(emailInput!, 'test@example.com');
    await user.type(screen.getByLabelText(/senha/i), 'Password123!');

    // Submit
    const submitButton = screen.getByRole('button', { name: /criar conta/i });
    await user.click(submitButton);

    // Button should be disabled during loading
    await waitFor(() => {
      expect(submitButton).toBeDisabled();
    });
  });

  it('should allow clearing error message', async () => {
    const user = userEvent.setup();
    
    mockAuthService.register.mockRejectedValue(
      new Error('Registration failed')
    );

    renderComponent();

    // Fill and submit form to generate error
    await user.type(screen.getByLabelText(/nome/i), 'Test User');
    await user.type(screen.getByLabelText(/username/i), 'testuser');
    const emailInputs = screen.getAllByLabelText(/email/i);
    const emailInput = emailInputs.find(input => input.getAttribute('placeholder') === 'seu@email.com');
    await user.type(emailInput!, 'test@example.com');
    await user.type(screen.getByLabelText(/senha/i), 'Password123!');
    await user.click(screen.getByRole('button', { name: /criar conta/i }));

    // Wait for error to appear
    await waitFor(() => {
      expect(screen.getByText(/erro/i)).toBeInTheDocument();
    });

    // Click dismiss button
    const dismissButton = screen.getByText(/dismiss/i);
    await user.click(dismissButton);

    // Error should be cleared
    await waitFor(() => {
      expect(screen.queryByText(/erro/i)).not.toBeInTheDocument();
    });
  });

  it('should include client_id if provided', async () => {
    const user = userEvent.setup();
    const mockUser = {
      id: '1',
      username: 'testuser',
      email: 'test@example.com',
      name: 'Test User',
      isActive: true,
      emailVerified: false,
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    mockAuthService.register.mockResolvedValue(mockUser);

    renderComponent();

    // Fill client_id
    const clientIdInput = screen.getByPlaceholderText(/client_id/i);
    await user.type(clientIdInput, 'test-client-123');

    // Fill other fields
    await user.type(screen.getByLabelText(/nome/i), 'Test User');
    await user.type(screen.getByLabelText(/username/i), 'testuser');
    const emailInputs = screen.getAllByLabelText(/email/i);
    const emailInput = emailInputs.find(input => input.getAttribute('placeholder') === 'seu@email.com');
    await user.type(emailInput!, 'test@example.com');
    await user.type(screen.getByLabelText(/senha/i), 'Password123!');

    // Submit
    await user.click(screen.getByRole('button', { name: /criar conta/i }));

    await waitFor(() => {
      expect(mockAuthService.register).toHaveBeenCalledWith(
        expect.objectContaining({
          client_id: 'test-client-123',
        })
      );
    });
  });

  it('should have link to login page', () => {
    renderComponent();

    const loginLink = screen.getByText(/faça login/i);
    expect(loginLink).toBeInTheDocument();
    expect(loginLink.closest('a')).toHaveAttribute('href', '/login');
  });
});

