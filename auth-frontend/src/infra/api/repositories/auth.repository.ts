/**
 * Auth Repository Implementation
 * HTTP-based implementation of IAuthRepository
 */

import { IAuthRepository } from '../../../core/interfaces/secondary/IAuthRepository';
import { IHttpClient } from '../../../core/interfaces/secondary/IHttpClient';
import {
  LoginDTO,
  RegisterDTO,
  ForgotPasswordDTO,
  ResetPasswordDTO,
  TokenResponseDTO,
  UserResponseDTO,
  MessageResponseDTO,
} from '../dtos/auth.dto';

export class AuthRepository implements IAuthRepository {
  constructor(private httpClient: IHttpClient) {}

  async login(credentials: LoginDTO): Promise<TokenResponseDTO> {
    return this.httpClient.post<TokenResponseDTO>('/api/auth/login', credentials);
  }

  async register(data: RegisterDTO): Promise<TokenResponseDTO> {
    return this.httpClient.post<TokenResponseDTO>('/api/auth/register', data);
  }

  async logout(refreshToken: string): Promise<void> {
    await this.httpClient.post<void>('/api/auth/logout', {
      refresh_token: refreshToken,
    });
  }

  async getCurrentUser(): Promise<UserResponseDTO> {
    return this.httpClient.get<UserResponseDTO>('/api/auth/me');
  }

  async refreshToken(refreshToken: string): Promise<TokenResponseDTO> {
    return this.httpClient.post<TokenResponseDTO>('/api/auth/refresh', {
      refresh_token: refreshToken,
    });
  }

  async forgotPassword(data: ForgotPasswordDTO): Promise<MessageResponseDTO> {
    return this.httpClient.post<MessageResponseDTO>('/api/auth/forgot-password', data);
  }

  async resetPassword(data: ResetPasswordDTO): Promise<MessageResponseDTO> {
    return this.httpClient.post<MessageResponseDTO>('/api/auth/reset-password', data);
  }

  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await this.httpClient.post<void>('/api/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  }
}

