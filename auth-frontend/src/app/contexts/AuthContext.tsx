/**
 * Auth Context
 * React Context for authentication state management
 * 
 * Features:
 * - Error state management with clearError
 * - Per-operation loading states (loggingIn, registering, loggingOut, refreshing)
 * - Performance optimizations with useCallback
 * - Consistent error handling pattern
 * - Uses DI Container to get services
 * 
 * Compliance: 08b-state-management.md Section 2, 6
 */
import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { User } from '../../core/domain/user';
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
      const errorMessage = err instanceof Error ? err.message : 'Login failed';
      setError(errorMessage);
      logger.error('Login error', err as Error);
      throw err; // Re-throw for UI to handle
    } finally {
      setLoggingIn(false);
    }
  }, [authService, logger]);

  /**
   * Register new user
   * Delegates to AuthService and manages UI state
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
      const errorMessage = err instanceof Error ? err.message : 'Registration failed';
      setError(errorMessage);
      logger.error('Registration error', err as Error);
      throw err;
    } finally {
      setRegistering(false);
    }
  }, [authService, logger]);

  /**
   * Logout user
   * Delegates to AuthService and clears UI state
   */
  const logout = useCallback(async () => {
    setError(null);
    setLoggingOut(true);
    try {
      await authService.logout();
      setUser(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Logout failed';
      setError(errorMessage);
      logger.error('Logout error', err as Error);
      throw err;
    } finally {
      setLoggingOut(false);
    }
  }, [authService, logger]);

  /**
   * Refresh current user data
   * Fetches latest user data from server
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
      const errorMessage = err instanceof Error ? err.message : 'Failed to refresh user';
      setError(errorMessage);
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
