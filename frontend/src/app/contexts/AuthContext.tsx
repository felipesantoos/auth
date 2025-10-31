/**
 * Auth Context
 * React Context for authentication state management
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '../../core/domain/auth';
import { AuthService } from '../../core/services/auth/authService';
import { AuthRepository } from '../../core/repositories/auth_repository';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string, clientId?: string) => Promise<void>;
  register: (username: string, email: string, password: string, name: string, clientId?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

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

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const authRepository = new AuthRepository();
  const authService = new AuthService(authRepository);

  // Load user from localStorage on mount
  useEffect(() => {
    const loadUser = async () => {
      try {
        const storedUser = localStorage.getItem('user');
        if (storedUser && authService.isAuthenticated()) {
          setUser(JSON.parse(storedUser));
          
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
        console.error('Error loading user:', error);
        await authService.logout();
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    loadUser();
  }, []);

  const login = async (email: string, password: string, clientId?: string) => {
    setIsLoading(true);
    try {
      const loggedInUser = await authService.login({ email, password, client_id: clientId });
      setUser(loggedInUser);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (username: string, email: string, password: string, name: string, clientId?: string) => {
    setIsLoading(true);
    try {
      const registeredUser = await authService.register({ username, email, password, name, client_id: clientId });
      setUser(registeredUser);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await authService.logout();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshUser = async () => {
    try {
      const currentUser = await authService.getCurrentUser();
      if (currentUser) {
        setUser(currentUser);
      }
    } catch (error) {
      console.error('Error refreshing user:', error);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

