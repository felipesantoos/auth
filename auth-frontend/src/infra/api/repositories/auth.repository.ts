/**
 * Auth Repository Implementation
 * HTTP-based implementation of IAuthRepository
 * Transforms API errors to domain-specific errors
 * 
 * Compliance: 08c-react-best-practices.md Section 5.1
 */

import axios from 'axios';
import type { IAuthRepository } from '../../../core/interfaces/secondary/IAuthRepository';
import type { IHttpClient } from '../../../core/interfaces/secondary/IHttpClient';
import { User } from '../../../core/domain/user';
import type {
  LoginCredentials,
  RegistrationData,
  PasswordResetRequest,
  PasswordReset,
  AuthenticationResult,
} from '../../../core/domain/auth';
import type {
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
  private httpClient: IHttpClient;

  constructor(httpClient: IHttpClient) {
    this.httpClient = httpClient;
  }

  async login(credentials: LoginCredentials): Promise<AuthenticationResult> {
    try {
      // Convert domain type to DTO
      const dto: LoginDTO = {
        email: credentials.email,
        password: credentials.password,
        client_id: credentials.client_id,
      };
      
      const response = await this.httpClient.post<TokenResponseDTO>('/api/auth/login', dto);
      
      // Convert DTO to domain type
      return this.mapToAuthenticationResult(response);
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

  async register(data: RegistrationData): Promise<AuthenticationResult> {
    try {
      // Convert domain type to DTO
      const dto: RegisterDTO = {
        username: data.username,
        email: data.email,
        password: data.password,
        name: data.name,
        client_id: data.client_id,
      };
      
      const response = await this.httpClient.post<TokenResponseDTO>('/api/auth/register', dto);
      
      // Convert DTO to domain type
      return this.mapToAuthenticationResult(response);
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

  async getCurrentUser(): Promise<User> {
    try {
      const response = await this.httpClient.get<UserResponseDTO>('/api/auth/me');
      
      // Convert DTO to domain type
      return this.mapToUser(response);
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

  async refreshToken(refreshToken: string): Promise<AuthenticationResult> {
    try {
      const response = await this.httpClient.post<TokenResponseDTO>('/api/auth/refresh', {
        refresh_token: refreshToken,
      });
      
      // Convert DTO to domain type
      return this.mapToAuthenticationResult(response);
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

  async forgotPassword(request: PasswordResetRequest): Promise<{ message: string }> {
    try {
      // Convert domain type to DTO
      const dto: ForgotPasswordDTO = {
        email: request.email,
        client_id: request.client_id,
      };
      
      const response = await this.httpClient.post<MessageResponseDTO>('/api/auth/forgot-password', dto);
      return { message: response.message };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 404) {
          throw new EntityNotFoundError('User', request.email);
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

  async resetPassword(reset: PasswordReset): Promise<{ message: string }> {
    try {
      // Convert domain type to DTO
      const dto: ResetPasswordDTO = {
        reset_token: reset.reset_token,
        new_password: reset.new_password,
        client_id: reset.client_id,
      };
      
      const response = await this.httpClient.post<MessageResponseDTO>('/api/auth/reset-password', dto);
      return { message: response.message };
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

  /**
   * Map TokenResponseDTO to AuthenticationResult (domain type)
   */
  private mapToAuthenticationResult(dto: TokenResponseDTO): AuthenticationResult {
    return {
      user: this.mapToUser(dto.user),
      access_token: dto.access_token,
      refresh_token: dto.refresh_token,
      token_type: dto.token_type,
      expires_in: dto.expires_in,
    };
  }

  /**
   * Map UserResponseDTO to User (domain type)
   */
  private mapToUser(dto: UserResponseDTO): User {
    return new User(
      dto.id,
      dto.username,
      dto.email,
      dto.name,
      dto.active,
      new Date(dto.created_at),
      false, // emailVerified - adjust based on your API
      false, // mfaEnabled - adjust based on your API
      undefined, // avatarUrl
      undefined, // kycDocumentId
      undefined, // kycStatus
      undefined  // kycVerifiedAt
    );
  }
}

