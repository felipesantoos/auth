/**
 * Auth Context
 * React Context for authentication state management
 * 
 * Features:
 * - Error state management with clearError
 * - Per-operation loading states (loggingIn, registering, loggingOut, refreshing)
 * - Performance optimizations with useCallback
 * - Type-safe error handling with custom error classes
 * - Consistent error handling pattern
 * - Uses DI Container to get services
 * 
 * Compliance: 
 * - 08b-state-management.md Section 2, 6
 * - 08c-react-best-practices.md Section 5.1
 */
import type { ReactNode } from 'react';
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { User } from '../../core/domain/user';
import { 
  DomainError, 
  AuthenticationError, 
  BusinessValidationError,
  DuplicateEntityError,
  NetworkError 
} from '../../core/domain/errors';
import DIContainer from '../dicontainer/container';

/**
 * Auth Context Type
 * Provides authentication state and operations
 */
interface AuthContextType {
  // User state
  user: User | null;
  isAuthenticated: boolean;
  
  // Loading states (per-operation)
  loading: boolean;        // Initial load only
  loggingIn: boolean;      // Login operation
  registering: boolean;    // Register operation
  loggingOut: boolean;     // Logout operation
  refreshing: boolean;     // Refresh user operation
  
  // Error state
  error: string | null;
  
  // Actions
  login: (email: string, password: string, clientId?: string) => Promise<void>;
  register: (username: string, email: string, password: string, name: string, clientId?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Hook to consume Auth Context
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Auth Provider
 * Primary adapter that connects UI with AuthService
 */
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  // UI State
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true); // Initial load only
  const [loggingIn, setLoggingIn] = useState(false);
  const [registering, setRegistering] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get services from DI Container
  const authService = DIContainer.getAuthService();
  const logger = DIContainer.getLogger();

  // Load user from localStorage on mount
  useEffect(() => {
    const loadUser = async () => {
      try {
        if (authService.isAuthenticated()) {
          // Verify token is still valid by fetching current user
          const currentUser = await authService.getCurrentUser();
          if (currentUser) {
            setUser(currentUser);
          } else {
            // Token invalid, clear auth
            await authService.logout();
            setUser(null);
          }
        }
      } catch (error) {
        logger.error('Error loading user', error as Error);
        await authService.logout();
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, [authService, logger]);

  /**
   * Login user
   * Delegates to AuthService and manages UI state
   * Type-safe error handling with custom error classes
   */
  const login = useCallback(async (email: string, password: string, clientId?: string) => {
    setError(null); // Clear previous errors
    setLoggingIn(true);
    try {
      const loggedInUser = await authService.login({ 
        email, 
        password, 
        client_id: clientId 
      });
      setUser(loggedInUser);
    } catch (err) {
      // Type-safe error handling
      if (err instanceof AuthenticationError) {
        setError('Email ou senha incorretos. Verifique suas credenciais.');
      } else if (err instanceof BusinessValidationError) {
        setError(err.message);
      } else if (err instanceof NetworkError) {
        setError('Não foi possível conectar ao servidor. Verifique sua conexão.');
      } else if (err instanceof DomainError) {
        setError(err.message);
      } else {
        setError('Ocorreu um erro inesperado. Tente novamente.');
      }
      logger.error('Login error', err as Error);
      throw err; // Re-throw for UI to handle
    } finally {
      setLoggingIn(false);
    }
  }, [authService, logger]);

  /**
   * Register new user
   * Delegates to AuthService and manages UI state
   * Type-safe error handling with custom error classes
   */
  const register = useCallback(async (
    username: string, 
    email: string, 
    password: string, 
    name: string, 
    clientId?: string
  ) => {
    setError(null);
    setRegistering(true);
    try {
      const registeredUser = await authService.register({ 
        username, 
        email, 
        password, 
        name, 
        client_id: clientId 
      });
      setUser(registeredUser);
    } catch (err) {
      // Type-safe error handling
      if (err instanceof DuplicateEntityError) {
        setError('Email ou nome de usuário já cadastrado. Use credenciais diferentes.');
      } else if (err instanceof BusinessValidationError) {
        setError(err.message);
      } else if (err instanceof NetworkError) {
        setError('Não foi possível conectar ao servidor. Verifique sua conexão.');
      } else if (err instanceof DomainError) {
        setError(err.message);
      } else {
        setError('Ocorreu um erro no registro. Tente novamente.');
      }
      logger.error('Registration error', err as Error);
      throw err;
    } finally {
      setRegistering(false);
    }
  }, [authService, logger]);

  /**
   * Logout user
   * Delegates to AuthService and clears UI state
   * Type-safe error handling with custom error classes
   */
  const logout = useCallback(async () => {
    setError(null);
    setLoggingOut(true);
    try {
      await authService.logout();
      setUser(null);
    } catch (err) {
      // Type-safe error handling
      if (err instanceof NetworkError) {
        setError('Não foi possível conectar ao servidor. Tentando novamente...');
      } else if (err instanceof DomainError) {
        setError(err.message);
      } else {
        setError('Erro ao fazer logout. Tente novamente.');
      }
      logger.error('Logout error', err as Error);
      throw err;
    } finally {
      setLoggingOut(false);
    }
  }, [authService, logger]);

  /**
   * Refresh current user data
   * Fetches latest user data from server
   * Type-safe error handling with custom error classes
   */
  const refreshUser = useCallback(async () => {
    setError(null);
    setRefreshing(true);
    try {
      const currentUser = await authService.getCurrentUser();
      if (currentUser) {
        setUser(currentUser);
      }
    } catch (err) {
      // Type-safe error handling
      if (err instanceof AuthenticationError) {
        setError('Sessão expirada. Faça login novamente.');
      } else if (err instanceof NetworkError) {
        setError('Não foi possível atualizar os dados. Verifique sua conexão.');
      } else if (err instanceof DomainError) {
        setError(err.message);
      } else {
        setError('Erro ao atualizar usuário. Tente novamente.');
      }
      logger.error('Refresh user error', err as Error);
    } finally {
      setRefreshing(false);
    }
  }, [authService, logger]);

  /**
   * Clear error state
   * Used by UI to dismiss error messages
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        loading,
        loggingIn,
        registering,
        loggingOut,
        refreshing,
        error,
        login,
        register,
        logout,
        refreshUser,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
