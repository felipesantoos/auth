/**
 * Auth Mutations Hooks
 * Custom hooks for authentication mutations using React Query
 * 
 * Features:
 * - Optimistic updates for instant UI feedback
 * - Automatic rollback on errors
 * - Cache invalidation for data consistency
 * 
 * Compliance: 08b-state-management.md Section 3.4
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import DIContainer from '../dicontainer/container';
import type { LoginDTO, RegisterDTO, ForgotPasswordDTO, ResetPasswordDTO } from '../../infra/api/dtos/auth.dto';

/**
 * Login Mutation Hook
 * Implements optimistic updates pattern:
 * - Shows "logging in" state immediately
 * - Rolls back on error
 * - Updates with real data on success
 */
export const useLogin = () => {
  const queryClient = useQueryClient();
  const authService = DIContainer.getAuthService();

  return useMutation({
    mutationFn: (credentials: LoginDTO) => authService.login(credentials),
    
    // Optimistic update: show logging in state immediately
    onMutate: async (credentials) => {
      // Cancel any outgoing queries to avoid race conditions
      await queryClient.cancelQueries({ queryKey: ['currentUser'] });
      
      // Snapshot the previous value for rollback
      const previousUser = queryClient.getQueryData(['currentUser']);
      
      // Optimistically update cache with "logging in" indicator
      queryClient.setQueryData(['currentUser'], {
        email: credentials.email,
        isLoggingIn: true,
      });
      
      // Return context with snapshot for potential rollback
      return { previousUser };
    },
    
    // On error: rollback to previous value
    onError: (err, credentials, context) => {
      if (context?.previousUser !== undefined) {
        queryClient.setQueryData(['currentUser'], context.previousUser);
      }
    },
    
    // On success: replace optimistic data with real user data
    onSuccess: (user) => {
      queryClient.setQueryData(['currentUser'], user);
    },
    
    // Always refetch after mutation to ensure sync with server
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
    },
  });
};

/**
 * Register Mutation Hook
 * Implements optimistic updates pattern for user registration
 */
export const useRegister = () => {
  const queryClient = useQueryClient();
  const authService = DIContainer.getAuthService();

  return useMutation({
    mutationFn: (data: RegisterDTO) => authService.register(data),
    
    // Optimistic update: show registering user immediately
    onMutate: async (data) => {
      await queryClient.cancelQueries({ queryKey: ['currentUser'] });
      const previousUser = queryClient.getQueryData(['currentUser']);
      
      // Optimistically show registering user with available data
      queryClient.setQueryData(['currentUser'], {
        email: data.email,
        name: data.name,
        username: data.username,
        isRegistering: true,
      });
      
      return { previousUser };
    },
    
    // On error: rollback to previous value
    onError: (err, data, context) => {
      if (context?.previousUser !== undefined) {
        queryClient.setQueryData(['currentUser'], context.previousUser);
      }
    },
    
    // On success: replace optimistic data with real user data
    onSuccess: (user) => {
      queryClient.setQueryData(['currentUser'], user);
    },
    
    // Always refetch after mutation
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
    },
  });
};

/**
 * Logout Mutation Hook
 * Implements optimistic updates pattern:
 * - Clears user immediately (logout feels instant)
 * - Restores user on error (if logout fails)
 */
export const useLogout = () => {
  const queryClient = useQueryClient();
  const authService = DIContainer.getAuthService();

  return useMutation({
    mutationFn: () => authService.logout(),
    
    // Optimistic update: clear user immediately for instant logout
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: ['currentUser'] });
      const previousUser = queryClient.getQueryData(['currentUser']);
      
      // Optimistically clear user (logout immediately in UI)
      queryClient.setQueryData(['currentUser'], null);
      
      return { previousUser };
    },
    
    // On error: rollback - restore user if logout fails
    onError: (err, variables, context) => {
      if (context?.previousUser !== undefined) {
        queryClient.setQueryData(['currentUser'], context.previousUser);
      }
    },
    
    // On success: clear all queries
    onSuccess: () => {
      queryClient.clear();
    },
  });
};

/**
 * Forgot Password Mutation Hook
 * No optimistic update needed (doesn't affect current user state)
 * But follows pattern for consistency
 */
export const useForgotPassword = () => {
  const authService = DIContainer.getAuthService();

  return useMutation({
    mutationFn: (data: ForgotPasswordDTO) => authService.forgotPassword(data),
    
    // No optimistic update needed - doesn't change user state
    // But we include onMutate for consistency with pattern
    onMutate: async (_data) => {
      // Could add "sending email" state here if needed in the future
      return {};
    },
  });
};

/**
 * Reset Password Mutation Hook
 * No optimistic update needed (doesn't affect current user state)
 * But follows pattern for consistency
 */
export const useResetPassword = () => {
  const authService = DIContainer.getAuthService();

  return useMutation({
    mutationFn: (data: ResetPasswordDTO) => authService.resetPassword(data),
    
    // No optimistic update needed - doesn't change user state
    // But we include onMutate for consistency with pattern
    onMutate: async (_data) => {
      // Could add "resetting password" state here if needed in the future
      return {};
    },
  });
};

