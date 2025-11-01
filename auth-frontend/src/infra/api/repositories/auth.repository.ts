/**
 * Auth Repository Implementation
 * HTTP-based implementation of IAuthRepository
 * Transforms API errors to domain-specific errors
 * 
 * Compliance: 08c-react-best-practices.md Section 5.1
 */

import axios from 'axios';
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
import {
  AuthenticationError,
  BusinessValidationError,
  DuplicateEntityError,
  NetworkError,
  EntityNotFoundError,
} from '../../../core/domain/errors';

export class AuthRepository implements IAuthRepository {
  constructor(private httpClient: IHttpClient) {}

  async login(credentials: LoginDTO): Promise<TokenResponseDTO> {
    try {
      return await this.httpClient.post<TokenResponseDTO>('/api/auth/login', credentials);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 401) {
          throw new AuthenticationError('Invalid email or password');
        }
        if (error.response?.status === 422) {
          throw new BusinessValidationError('Invalid request data');
        }
        if (error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK') {
          throw new NetworkError('Unable to connect to server');
        }
      }
      throw error;
    }
  }

  async register(data: RegisterDTO): Promise<TokenResponseDTO> {
    try {
      return await this.httpClient.post<TokenResponseDTO>('/api/auth/register', data);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 409) {
          throw new DuplicateEntityError('Email or username already exists');
        }
        if (error.response?.status === 422) {
          throw new BusinessValidationError('Invalid registration data');
        }
        if (error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK') {
          throw new NetworkError('Unable to connect to server');
        }
      }
      throw error;
    }
  }

  async logout(refreshToken: string): Promise<void> {
    try {
      await this.httpClient.post<void>('/api/auth/logout', {
        refresh_token: refreshToken,
      });
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK') {
          throw new NetworkError('Unable to connect to server');
        }
      }
      throw error;
    }
  }

  async getCurrentUser(): Promise<UserResponseDTO> {
    try {
      return await this.httpClient.get<UserResponseDTO>('/api/auth/me');
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 401) {
          throw new AuthenticationError('Session expired');
        }
        if (error.response?.status === 404) {
          throw new EntityNotFoundError('User', 'current');
        }
        if (error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK') {
          throw new NetworkError('Unable to connect to server');
        }
      }
      throw error;
    }
  }

  async refreshToken(refreshToken: string): Promise<TokenResponseDTO> {
    try {
      return await this.httpClient.post<TokenResponseDTO>('/api/auth/refresh', {
        refresh_token: refreshToken,
      });
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 401) {
          throw new AuthenticationError('Refresh token expired');
        }
        if (error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK') {
          throw new NetworkError('Unable to connect to server');
        }
      }
      throw error;
    }
  }

  async forgotPassword(data: ForgotPasswordDTO): Promise<MessageResponseDTO> {
    try {
      return await this.httpClient.post<MessageResponseDTO>('/api/auth/forgot-password', data);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 404) {
          throw new EntityNotFoundError('User', data.email);
        }
        if (error.response?.status === 422) {
          throw new BusinessValidationError('Invalid email format');
        }
        if (error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK') {
          throw new NetworkError('Unable to connect to server');
        }
      }
      throw error;
    }
  }

  async resetPassword(data: ResetPasswordDTO): Promise<MessageResponseDTO> {
    try {
      return await this.httpClient.post<MessageResponseDTO>('/api/auth/reset-password', data);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 400) {
          throw new BusinessValidationError('Invalid or expired reset token');
        }
        if (error.response?.status === 422) {
          throw new BusinessValidationError('Invalid password format');
        }
        if (error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK') {
          throw new NetworkError('Unable to connect to server');
        }
      }
      throw error;
    }
  }

  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    try {
      await this.httpClient.post<void>('/api/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword,
      });
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 401) {
          throw new AuthenticationError('Current password is incorrect');
        }
        if (error.response?.status === 422) {
          throw new BusinessValidationError('Invalid new password format');
        }
        if (error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK') {
          throw new NetworkError('Unable to connect to server');
        }
      }
      throw error;
    }
  }
}

