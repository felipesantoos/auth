/**
 * Auth Mutations Hooks
 * Custom hooks for authentication mutations using React Query
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import DIContainer from '../dicontainer/container';
import { LoginDTO, RegisterDTO, ForgotPasswordDTO, ResetPasswordDTO } from '../../infra/api/dtos/auth.dto';

export const useLogin = () => {
  const queryClient = useQueryClient();
  const authService = DIContainer.getAuthService();

  return useMutation({
    mutationFn: (credentials: LoginDTO) => authService.login(credentials),
    onSuccess: (user) => {
      // Invalidate current user query
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
      queryClient.setQueryData(['currentUser'], user);
    },
  });
};

export const useRegister = () => {
  const queryClient = useQueryClient();
  const authService = DIContainer.getAuthService();

  return useMutation({
    mutationFn: (data: RegisterDTO) => authService.register(data),
    onSuccess: (user) => {
      queryClient.invalidateQueries({ queryKey: ['currentUser'] });
      queryClient.setQueryData(['currentUser'], user);
    },
  });
};

export const useLogout = () => {
  const queryClient = useQueryClient();
  const authService = DIContainer.getAuthService();

  return useMutation({
    mutationFn: () => authService.logout(),
    onSuccess: () => {
      queryClient.clear(); // Clear all queries on logout
    },
  });
};

export const useForgotPassword = () => {
  const authService = DIContainer.getAuthService();

  return useMutation({
    mutationFn: (data: ForgotPasswordDTO) => authService.forgotPassword(data),
  });
};

export const useResetPassword = () => {
  const authService = DIContainer.getAuthService();

  return useMutation({
    mutationFn: (data: ResetPasswordDTO) => authService.resetPassword(data),
  });
};

