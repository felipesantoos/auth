/**
 * Auth Custom Hooks
 * React Query hooks for authentication operations
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import DIContainer from '../dicontainer/container';
import { User } from '../../core/domain/user';
import { LoginFormData, RegisterFormData, ForgotPasswordFormData, ResetPasswordFormData } from '../schemas/auth.schema';

const AUTH_KEYS = {
  currentUser: ['auth', 'currentUser'] as const,
  isAuthenticated: ['auth', 'isAuthenticated'] as const,
};

/**
 * Hook para obter usuário atual
 */
export const useCurrentUser = () => {
  const authService = DIContainer.getAuthService();

  return useQuery({
    queryKey: AUTH_KEYS.currentUser,
    queryFn: () => authService.getCurrentUser(),
    enabled: authService.isAuthenticated(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false,
  });
};

/**
 * Hook para login
 */
export const useLogin = () => {
  const authService = DIContainer.getAuthService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (credentials: LoginFormData) => authService.login(credentials),
    onSuccess: (user: User) => {
      // Update current user cache
      queryClient.setQueryData(AUTH_KEYS.currentUser, user);
      queryClient.invalidateQueries({ queryKey: AUTH_KEYS.currentUser });
    },
  });
};

/**
 * Hook para registro
 */
export const useRegister = () => {
  const authService = DIContainer.getAuthService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: RegisterFormData) => authService.register(data),
    onSuccess: (user: User) => {
      // Update current user cache
      queryClient.setQueryData(AUTH_KEYS.currentUser, user);
      queryClient.invalidateQueries({ queryKey: AUTH_KEYS.currentUser });
    },
  });
};

/**
 * Hook para logout
 */
export const useLogout = () => {
  const authService = DIContainer.getAuthService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => authService.logout(),
    onSuccess: () => {
      // Clear all auth-related cache
      queryClient.setQueryData(AUTH_KEYS.currentUser, null);
      queryClient.clear();
    },
  });
};

/**
 * Hook para forgot password
 */
export const useForgotPassword = () => {
  const authService = DIContainer.getAuthService();

  return useMutation({
    mutationFn: (data: ForgotPasswordFormData) => authService.forgotPassword(data),
  });
};

/**
 * Hook para reset password
 */
export const useResetPassword = () => {
  const authService = DIContainer.getAuthService();

  return useMutation({
    mutationFn: (data: ResetPasswordFormData) => authService.resetPassword(data),
  });
};

/**
 * Hook para verificar se está autenticado
 */
export const useIsAuthenticated = () => {
  const authService = DIContainer.getAuthService();
  return authService.isAuthenticated();
};

