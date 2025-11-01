/**
 * Auth Service Implementation
 * Implements IAuthService using IAuthRepository
 */

import { IAuthService } from '../../interfaces/primary/IAuthService';
import { IAuthRepository } from '../../interfaces/secondary/IAuthRepository';
import { IStorage } from '../../interfaces/secondary/IStorage';
import { ILogger } from '../../interfaces/secondary/ILogger';
import { User } from '../../domain/user';
import { UserMapper } from '../../../infra/api/mappers/user.mapper';
import { TokenMapper } from '../../../infra/api/mappers/token.mapper';
import {
  LoginDTO,
  RegisterDTO,
  ForgotPasswordDTO,
  ResetPasswordDTO,
} from '../../../infra/api/dtos/auth.dto';

export class AuthService implements IAuthService {
  constructor(
    private repository: IAuthRepository,
    private storage: IStorage,
    private logger: ILogger
  ) {}

  async login(credentials: LoginDTO): Promise<User> {
    try {
      this.logger.info('Login attempt', { email: credentials.email });

      const response = await this.repository.login(credentials);

      // Store tokens using IStorage
      this.storage.setItem('access_token', response.access_token);
      this.storage.setItem('refresh_token', response.refresh_token);

      // Store client_id if provided
      if (credentials.client_id) {
        this.storage.setItem('client_id', credentials.client_id);
      }

      // Map DTO to Domain
      const user = UserMapper.toDomain(response.user);

      // Store user
      this.storage.setItem('user', JSON.stringify(response.user));

      this.logger.info('Login successful', { userId: user.id });

      return user;
    } catch (error) {
      this.logger.error('Login failed', error as Error, { email: credentials.email });
      throw error;
    }
  }

  async register(data: RegisterDTO): Promise<User> {
    try {
      this.logger.info('Registration attempt', { email: data.email });

      const response = await this.repository.register(data);

      // Store tokens using IStorage
      this.storage.setItem('access_token', response.access_token);
      this.storage.setItem('refresh_token', response.refresh_token);

      // Store client_id if provided
      if (data.client_id) {
        this.storage.setItem('client_id', data.client_id);
      }

      // Map DTO to Domain
      const user = UserMapper.toDomain(response.user);

      // Store user
      this.storage.setItem('user', JSON.stringify(response.user));

      this.logger.info('Registration successful', { userId: user.id });

      return user;
    } catch (error) {
      this.logger.error('Registration failed', error as Error, { email: data.email });
      throw error;
    }
  }

  async logout(): Promise<void> {
    try {
      const refreshToken = this.storage.getItem('refresh_token');

      if (refreshToken) {
        await this.repository.logout(refreshToken);
      }

      // Clear all auth data
      this.storage.removeItem('access_token');
      this.storage.removeItem('refresh_token');
      this.storage.removeItem('user');
      this.storage.removeItem('client_id');

      this.logger.info('Logout successful');
    } catch (error) {
      this.logger.error('Logout failed', error as Error);
      // Clear storage anyway
      this.storage.removeItem('access_token');
      this.storage.removeItem('refresh_token');
      this.storage.removeItem('user');
      this.storage.removeItem('client_id');
      throw error;
    }
  }

  async getCurrentUser(): Promise<User | null> {
    try {
      if (!this.isAuthenticated()) {
        return null;
      }

      const response = await this.repository.getCurrentUser();
      const user = UserMapper.toDomain(response);

      // Update stored user
      this.storage.setItem('user', JSON.stringify(response));

      return user;
    } catch (error) {
      this.logger.error('Failed to get current user', error as Error);
      return null;
    }
  }

  async refreshToken(): Promise<void> {
    try {
      const refreshToken = this.storage.getItem('refresh_token');

      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await this.repository.refreshToken(refreshToken);

      // Store new tokens
      this.storage.setItem('access_token', response.access_token);
      this.storage.setItem('refresh_token', response.refresh_token);

      // Update user
      this.storage.setItem('user', JSON.stringify(response.user));

      this.logger.info('Token refreshed successfully');
    } catch (error) {
      this.logger.error('Token refresh failed', error as Error);
      throw error;
    }
  }

  async forgotPassword(data: ForgotPasswordDTO): Promise<{ message: string }> {
    try {
      this.logger.info('Forgot password request', { email: data.email });
      const response = await this.repository.forgotPassword(data);
      this.logger.info('Forgot password email sent', { email: data.email });
      return response;
    } catch (error) {
      this.logger.error('Forgot password failed', error as Error);
      throw error;
    }
  }

  async resetPassword(data: ResetPasswordDTO): Promise<{ message: string }> {
    try {
      this.logger.info('Reset password attempt');
      const response = await this.repository.resetPassword(data);
      this.logger.info('Password reset successful');
      return response;
    } catch (error) {
      this.logger.error('Password reset failed', error as Error);
      throw error;
    }
  }

  isAuthenticated(): boolean {
    const accessToken = this.storage.getItem('access_token');
    return !!accessToken;
  }

  getAccessToken(): string | null {
    return this.storage.getItem('access_token');
  }

  getRefreshToken(): string | null {
    return this.storage.getItem('refresh_token');
  }

  getClientId(): string | null {
    return this.storage.getItem('client_id');
  }

  setClientId(clientId: string): void {
    this.storage.setItem('client_id', clientId);
  }
}
