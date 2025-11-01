/**
 * AuthContext Tests
 * Integration tests for AuthContext + AuthService
 * 
 * Tests:
 * - Initial user loading from localStorage
 * - Login mutation (success/error cases)
 * - Register mutation (success/error cases)
 * - Logout mutation
 * - Refresh user data
 * - Error state management
 * - Loading states (per-operation)
 * - Type-safe error handling
 * 
 * Compliance: 08e-frontend-testing.md Section 3.4
 */

import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../AuthContext';
import { ReactNode } from 'react';
import DIContainer from '../../dicontainer/container';
import { User } from '../../../core/domain/user';
import { 
  AuthenticationError, 
  BusinessValidationError,
  DuplicateEntityError,
  NetworkError 
} from '../../../core/domain/errors';

// Mock DI Container
vi.mock('../../dicontainer/container', () => ({
  default: {
    getAuthService: vi.fn(),
    getLogger: vi.fn(),
  },
}));

describe('AuthContext', () => {
  // Mock services
  const mockAuthService = {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
    isAuthenticated: vi.fn(),
    forgotPassword: vi.fn(),
    resetPassword: vi.fn(),
  };

  const mockLogger = {
    info: vi.fn(),
    error: vi.fn(),
    warn: vi.fn(),
    debug: vi.fn(),
  };

  // Mock user
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

  // Wrapper component
  const wrapper = ({ children }: { children: ReactNode }) => (
    <AuthProvider>{children}</AuthProvider>
  );

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mocks
    (DIContainer.getAuthService as Mock).mockReturnValue(mockAuthService);
    (DIContainer.getLogger as Mock).mockReturnValue(mockLogger);
    
    // Default: not authenticated
    mockAuthService.isAuthenticated.mockReturnValue(false);
  });

  describe('Initial Load', () => {
    it('should complete initial load and set loading to false', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial load to complete
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Should have no user initially
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should load user from localStorage if authenticated', async () => {
      mockAuthService.isAuthenticated.mockReturnValue(true);
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Initial state
      expect(result.current.loading).toBe(true);

      // Wait for user to load
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Verify user loaded
      expect(mockAuthService.getCurrentUser).toHaveBeenCalled();
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('should handle user load failure by clearing auth', async () => {
      mockAuthService.isAuthenticated.mockReturnValue(true);
      mockAuthService.getCurrentUser.mockRejectedValue(new Error('Token invalid'));

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Verify logout called and user cleared
      expect(mockAuthService.logout).toHaveBeenCalled();
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should not fetch user if not authenticated', async () => {
      mockAuthService.isAuthenticated.mockReturnValue(false);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(mockAuthService.getCurrentUser).not.toHaveBeenCalled();
      expect(result.current.user).toBeNull();
    });
  });

  describe('Login', () => {
    it('should login successfully and set user', async () => {
      mockAuthService.login.mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for initial load
      await waitFor(() => expect(result.current.loading).toBe(false));

      // Perform login
      await act(async () => {
        await result.current.login('test@example.com', 'password123');
      });

      // Verify service called with correct params
      expect(mockAuthService.login).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
        client_id: undefined,
      });

      // Verify user set
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.error).toBeNull();
    });

    it('should set loggingIn state during login', async () => {
      mockAuthService.login.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockUser), 100))
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => expect(result.current.loading).toBe(false));

      // Start login
      act(() => {
        result.current.login('test@example.com', 'password123');
      });

      // Verify loggingIn is true
      await waitFor(() => {
        expect(result.current.loggingIn).toBe(true);
      });

      // Wait for login to complete
      await waitFor(() => {
        expect(result.current.loggingIn).toBe(false);
      });

      expect(result.current.user).toEqual(mockUser);
    });

    it('should handle AuthenticationError', async () => {
      mockAuthService.login.mockRejectedValue(
        new AuthenticationError('Invalid credentials')
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => expect(result.current.loading).toBe(false));

      // Attempt login
      await act(async () => {
        try {
          await result.current.login('test@example.com', 'wrongpassword');
        } catch {
          // Expected to throw
        }
      });

      // Verify error message
      expect(result.current.error).toBe('Email ou senha incorretos. Verifique suas credenciais.');
      expect(result.current.user).toBeNull();
      expect(mockLogger.error).toHaveBeenCalled();
    });

    it('should handle NetworkError', async () => {
      mockAuthService.login.mockRejectedValue(
        new NetworkError('Network failure')
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => expect(result.current.loading).toBe(false));

      await act(async () => {
        try {
          await result.current.login('test@example.com', 'password123');
        } catch {
          // Expected
        }
      });

      expect(result.current.error).toBe('Não foi possível conectar ao servidor. Verifique sua conexão.');
    });

    it('should clear previous error before new login attempt', async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => expect(result.current.loading).toBe(false));

      // First login fails
      mockAuthService.login.mockRejectedValueOnce(new AuthenticationError('Failed'));
      await act(async () => {
        try {
          await result.current.login('test@example.com', 'wrong');
        } catch {
          // Expected
        }
      });

      expect(result.current.error).not.toBeNull();

      // Second login succeeds
      mockAuthService.login.mockResolvedValueOnce(mockUser);
      await act(async () => {
        await result.current.login('test@example.com', 'correct');
      });

      // Error should be cleared
      expect(result.current.error).toBeNull();
      expect(result.current.user).toEqual(mockUser);
    });
  });

  describe('Register', () => {
    it('should register successfully and set user', async () => {
      mockAuthService.register.mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => expect(result.current.loading).toBe(false));

      await act(async () => {
        await result.current.register('testuser', 'test@example.com', 'password123', 'Test User');
      });

      expect(mockAuthService.register).toHaveBeenCalledWith({
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123',
        name: 'Test User',
        client_id: undefined,
      });

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('should set registering state during registration', async () => {
      mockAuthService.register.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockUser), 100))
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => expect(result.current.loading).toBe(false));

      act(() => {
        result.current.register('testuser', 'test@example.com', 'password123', 'Test User');
      });

      await waitFor(() => {
        expect(result.current.registering).toBe(true);
      });

      await waitFor(() => {
        expect(result.current.registering).toBe(false);
      });

      expect(result.current.user).toEqual(mockUser);
    });

    it('should handle DuplicateEntityError', async () => {
      mockAuthService.register.mockRejectedValue(
        new DuplicateEntityError('Email already exists')
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => expect(result.current.loading).toBe(false));

      await act(async () => {
        try {
          await result.current.register('testuser', 'duplicate@example.com', 'password123', 'Test');
        } catch {
          // Expected
        }
      });

      expect(result.current.error).toBe('Email ou nome de usuário já cadastrado. Use credenciais diferentes.');
      expect(result.current.user).toBeNull();
    });

    it('should handle BusinessValidationError', async () => {
      mockAuthService.register.mockRejectedValue(
        new BusinessValidationError('Password too weak')
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => expect(result.current.loading).toBe(false));

      await act(async () => {
        try {
          await result.current.register('testuser', 'test@example.com', '123', 'Test');
        } catch {
          // Expected
        }
      });

      expect(result.current.error).toBe('Password too weak');
    });
  });

  describe('Logout', () => {
    it('should logout successfully and clear user', async () => {
      // Setup: user logged in
      mockAuthService.isAuthenticated.mockReturnValue(true);
      mockAuthService.getCurrentUser.mockResolvedValue(mockUser);
      mockAuthService.logout.mockResolvedValue(undefined);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => expect(result.current.user).toEqual(mockUser));

      // Perform logout
      await act(async () => {
        await result.current.logout();
      });

      expect(mockAuthService.logout).toHaveBeenCalled();
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should set loggingOut state during logout', async () => {
      mockAuthService.logout.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => expect(result.current.loading).toBe(false));

      act(() => {
        result.current.logout();
      });

      await waitFor(() => {
        expect(result.current.loggingOut).toBe(true);
      });

      await waitFor(() => {
        expect(result.current.loggingOut).toBe(false);
      });
    });

    it('should handle logout NetworkError', async () => {
      mockAuthService.logout.mockRejectedValue(
        new NetworkError('Network failure')
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => expect(result.current.loading).toBe(false));

      await act(async () => {
        try {
          await result.current.logout();
        } catch {
          // Expected
        }
      });

      expect(result.current.error).toBe('Não foi possível conectar ao servidor. Tentando novamente...');
    });
  });

  describe('Refresh User', () => {
    it('should refresh user data successfully', async () => {
      const updatedUser: User = { ...mockUser, name: 'Updated Name' };
      mockAuthService.getCurrentUser.mockResolvedValue(updatedUser);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => expect(result.current.loading).toBe(false));

      await act(async () => {
        await result.current.refreshUser();
      });

      expect(mockAuthService.getCurrentUser).toHaveBeenCalled();
      expect(result.current.user).toEqual(updatedUser);
    });

    it('should set refreshing state during refresh', async () => {
      mockAuthService.getCurrentUser.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockUser), 100))
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => expect(result.current.loading).toBe(false));

      act(() => {
        result.current.refreshUser();
      });

      await waitFor(() => {
        expect(result.current.refreshing).toBe(true);
      });

      await waitFor(() => {
        expect(result.current.refreshing).toBe(false);
      });
    });

    it('should handle AuthenticationError during refresh', async () => {
      mockAuthService.getCurrentUser.mockRejectedValue(
        new AuthenticationError('Token expired')
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => expect(result.current.loading).toBe(false));

      await act(async () => {
        await result.current.refreshUser();
      });

      expect(result.current.error).toBe('Sessão expirada. Faça login novamente.');
    });
  });

  describe('Error Management', () => {
    it('should clear error with clearError', async () => {
      mockAuthService.login.mockRejectedValue(
        new AuthenticationError('Failed')
      );

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => expect(result.current.loading).toBe(false));

      // Create an error
      await act(async () => {
        try {
          await result.current.login('test@example.com', 'wrong');
        } catch {
          // Expected
        }
      });

      expect(result.current.error).not.toBeNull();

      // Clear error
      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('Hook Error', () => {
    it('should throw error if used outside AuthProvider', () => {
      // Suppress console.error for this test
      const consoleError = console.error;
      console.error = vi.fn();

      expect(() => {
        renderHook(() => useAuth());
      }).toThrow('useAuth must be used within an AuthProvider');

      console.error = consoleError;
    });
  });
});

