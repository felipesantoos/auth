/**
 * Auth Service Implementation
 * Implements IAuthService using IAuthRepository
 * 
 * Security:
 * - Tokens stored in httpOnly cookies (NOT localStorage)
 * - Only user data and client_id stored in localStorage (non-sensitive)
 * - XSS protection via cookie-based authentication
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

      // Tokens are stored in httpOnly cookies by backend (secure)
      // Only store non-sensitive data in localStorage

      // Store client_id if provided (not sensitive)
      if (credentials.client_id) {
        this.storage.setItem('client_id', credentials.client_id);
      }

      // Map DTO to Domain
      const user = UserMapper.toDomain(response.user);

      // Store user data (not sensitive - no password, tokens, etc)
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

      // Tokens are stored in httpOnly cookies by backend (secure)
      // Only store non-sensitive data in localStorage

      // Store client_id if provided (not sensitive)
      if (data.client_id) {
        this.storage.setItem('client_id', data.client_id);
      }

      // Map DTO to Domain
      const user = UserMapper.toDomain(response.user);

      // Store user data (not sensitive - no password, tokens, etc)
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
      // Call logout endpoint (backend will clear httpOnly cookies)
      // No need to pass refresh_token - it's sent via cookie automatically
      await this.repository.logout(''); // Empty string - backend reads from cookie

      // Clear only localStorage data (tokens are in cookies)
      this.storage.removeItem('user');
      this.storage.removeItem('client_id');

      this.logger.info('Logout successful');
    } catch (error) {
      this.logger.error('Logout failed', error as Error);
      // Clear storage anyway
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
      // Refresh token is sent via cookie automatically
      // Backend returns new tokens via cookies
      const response = await this.repository.refreshToken(''); // Empty string - backend reads from cookie

      // Tokens are stored in httpOnly cookies by backend
      // Only update user data in localStorage
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
    // Tokens are in httpOnly cookies (not accessible via JS)
    // Check if user is stored in localStorage as indication of auth state
    const user = this.storage.getItem('user');
    return !!user;
  }

  getAccessToken(): string | null {
    // Tokens are in httpOnly cookies (not accessible via JS)
    // This method is kept for interface compatibility but returns null
    console.warn('Tokens are now stored in httpOnly cookies and not accessible via JavaScript');
    return null;
  }

  getRefreshToken(): string | null {
    // Tokens are in httpOnly cookies (not accessible via JS)
    // This method is kept for interface compatibility but returns null
    console.warn('Tokens are now stored in httpOnly cookies and not accessible via JavaScript');
    return null;
  }

  getClientId(): string | null {
    return this.storage.getItem('client_id');
  }

  setClientId(clientId: string): void {
    this.storage.setItem('client_id', clientId);
  }
}
