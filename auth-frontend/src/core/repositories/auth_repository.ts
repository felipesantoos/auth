/**
 * Auth Repository
 * API calls for authentication
 */
import apiClient from './api_client';
import { LoginDTO, RegisterDTO, TokenResponse, UserResponse, ForgotPasswordDTO, ResetPasswordDTO, MessageResponse } from '../domain/auth';

export class AuthRepository {
  async login(credentials: LoginDTO): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/api/auth/login', credentials);
    return response.data;
  }

  async register(data: RegisterDTO): Promise<UserResponse> {
    const response = await apiClient.post<UserResponse>('/api/auth/register', data);
    return response.data;
  }

  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/api/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  }

  async logout(refreshToken: string): Promise<void> {
    await apiClient.post('/api/auth/logout', {
      refresh_token: refreshToken,
    });
  }

  async getCurrentUser(): Promise<UserResponse> {
    const response = await apiClient.get<UserResponse>('/api/auth/me');
    return response.data;
  }

  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await apiClient.post('/api/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  }

  async forgotPassword(data: ForgotPasswordDTO): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>('/api/auth/forgot-password', data);
    return response.data;
  }

  async resetPassword(data: ResetPasswordDTO): Promise<MessageResponse> {
    const response = await apiClient.post<MessageResponse>('/api/auth/reset-password', data);
    return response.data;
  }
}

