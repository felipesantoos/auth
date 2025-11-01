/**
 * Dashboard Page Tests
 * Component tests for the main dashboard page
 * 
 * Tests:
 * - Rendering user info cards
 * - Logout functionality
 * - Loading state during logout
 * - Navigation after logout
 * - Null user handling
 * 
 * Compliance: 08e-frontend-testing.md Section 3.5
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { Dashboard } from '../Dashboard';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../contexts/AuthContext';
import DIContainer from '../../dicontainer/container';
import { User } from '../../../core/domain/user';

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

describe('Dashboard Page', () => {
  const mockUser: User = {
    id: '1',
    username: 'testuser',
    email: 'test@example.com',
    name: 'Test User',
    isActive: true,
    emailVerified: true,
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  const mockAuthService = {
    logout: vi.fn(),
    login: vi.fn(),
    register: vi.fn(),
    getCurrentUser: vi.fn(),
    isAuthenticated: vi.fn(),
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

  const renderComponent = async (user: User | null = mockUser) => {
    mockAuthService.isAuthenticated.mockReturnValue(!!user);
    mockAuthService.getCurrentUser.mockResolvedValue(user);

    const result = render(
      <BrowserRouter>
        <AuthProvider>
          <Dashboard />
        </AuthProvider>
      </BrowserRouter>
    );

    // Wait for initial auth load to complete
    if (user) {
      await waitFor(() => {
        expect(screen.queryByText(user.name)).toBeInTheDocument();
      }, { timeout: 3000 });
    }

    return result;
  };

  it('should render dashboard with user info', async () => {
    await renderComponent();

    // Check if user cards are rendered
    expect(screen.getByText(mockUser.name)).toBeInTheDocument();
    expect(screen.getByText(mockUser.email)).toBeInTheDocument();
    expect(screen.getByText(mockUser.username)).toBeInTheDocument();
  });

  it('should render welcome card', async () => {
    await renderComponent();

    expect(screen.getByText(/bem-vindo/i)).toBeInTheDocument();
  });

  it('should have logout button', async () => {
    await renderComponent();

    expect(screen.getByRole('button', { name: /sair/i })).toBeInTheDocument();
  });

  it('should logout successfully and navigate to login', async () => {
    const user = userEvent.setup();
    mockAuthService.logout.mockResolvedValue(undefined);

    await renderComponent();

    // Click logout button
    const logoutButton = screen.getByRole('button', { name: /sair/i });
    await user.click(logoutButton);

    // Should call logout service
    await waitFor(() => {
      expect(mockAuthService.logout).toHaveBeenCalled();
    });

    // Should navigate to login
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  it('should show loading state during logout', async () => {
    const user = userEvent.setup();
    
    mockAuthService.logout.mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );

    await renderComponent();

    const logoutButton = screen.getByRole('button', { name: /sair/i });
    await user.click(logoutButton);

    // Button should be disabled during logout
    await waitFor(() => {
      expect(logoutButton).toBeDisabled();
    });
  });

  it('should navigate to login even if logout fails', async () => {
    const user = userEvent.setup();
    
    mockAuthService.logout.mockRejectedValue(new Error('Logout failed'));

    await renderComponent();

    const logoutButton = screen.getByRole('button', { name: /sair/i });
    await user.click(logoutButton);

    // Should still navigate to login
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  it('should render null if no user', () => {
    mockAuthService.isAuthenticated.mockReturnValue(false);
    mockAuthService.getCurrentUser.mockResolvedValue(null);

    const { container } = render(
      <BrowserRouter>
        <AuthProvider>
          <Dashboard />
        </AuthProvider>
      </BrowserRouter>
    );

    // Should render nothing (null)
    expect(container.firstChild).toBeNull();
  });

  it('should render user profile card with correct data', async () => {
    await renderComponent();

    expect(screen.getByText('Perfil do Usuário')).toBeInTheDocument();
    expect(screen.getByText(mockUser.name)).toBeInTheDocument();
    expect(screen.getByText(mockUser.username)).toBeInTheDocument();
  });

  it('should render user contact card with email', async () => {
    await renderComponent();

    expect(screen.getByText('Contato')).toBeInTheDocument();
    expect(screen.getByText(mockUser.email)).toBeInTheDocument();
  });

  it('should render permissions card', async () => {
    await renderComponent();

    expect(screen.getByText('Permissões')).toBeInTheDocument();
  });
});

