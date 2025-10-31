/**
 * Auth Service Implementation
 * Handles authentication logic and token management
 */
import { AuthServiceInterface } from './authServiceInterface';
import { AuthRepository } from '../../repositories/auth_repository';
import { User, LoginDTO, RegisterDTO, ForgotPasswordDTO, ResetPasswordDTO, MessageResponse } from '../../domain/auth';

export class AuthService implements AuthServiceInterface {
  private repository: AuthRepository;

  constructor(repository: AuthRepository) {
    this.repository = repository;
  }

  async login(credentials: LoginDTO): Promise<User> {
    const tokenResponse = await this.repository.login(credentials);

    // Store tokens
    localStorage.setItem('access_token', tokenResponse.access_token);
    localStorage.setItem('refresh_token', tokenResponse.refresh_token);

    // Store client_id if provided
    if (tokenResponse.user.client_id) {
      localStorage.setItem('client_id', tokenResponse.user.client_id);
    }

    // Store user data
    localStorage.setItem('user', JSON.stringify(tokenResponse.user));

    return tokenResponse.user;
  }

  async register(data: RegisterDTO): Promise<User> {
    const userResponse = await this.repository.register(data);

    // Store client_id if provided
    if (userResponse.client_id) {
      localStorage.setItem('client_id', userResponse.client_id);
    }

    return userResponse as User;
  }

  async logout(): Promise<void> {
    const refreshToken = this.getRefreshToken();
    if (refreshToken) {
      try {
        await this.repository.logout(refreshToken);
      } catch (error) {
        console.error('Logout error:', error);
      }
    }

    // Clear all auth data
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('client_id');
    localStorage.removeItem('user');
  }

  async getCurrentUser(): Promise<User | null> {
    try {
      const userResponse = await this.repository.getCurrentUser();
      localStorage.setItem('user', JSON.stringify(userResponse));
      return userResponse as User;
    } catch (error) {
      console.error('Error getting current user:', error);
      return null;
    }
  }

  isAuthenticated(): boolean {
    const token = this.getToken();
    return !!token;
  }

  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  getClientId(): string | null {
    return localStorage.getItem('client_id');
  }

  setClientId(clientId: string): void {
    localStorage.setItem('client_id', clientId);
  }

  async forgotPassword(data: ForgotPasswordDTO): Promise<MessageResponse> {
    return await this.repository.forgotPassword(data);
  }

  async resetPassword(data: ResetPasswordDTO): Promise<MessageResponse> {
    return await this.repository.resetPassword(data);
  }
}

