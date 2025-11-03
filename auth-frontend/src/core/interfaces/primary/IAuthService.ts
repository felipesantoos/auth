/**
 * Auth Service Interface (Primary Port)
 * Defines the contract for authentication use cases
 * Uses only domain types - no infrastructure dependencies
 */

import type { User } from '../../domain/user';
import type {
  LoginCredentials,
  RegistrationData,
  PasswordResetRequest,
  PasswordReset,
} from '../../domain/auth';

export interface IAuthService {
  login(credentials: LoginCredentials): Promise<User>;
  register(data: RegistrationData): Promise<User>;
  logout(): Promise<void>;
  getCurrentUser(): Promise<User | null>;
  refreshToken(): Promise<void>;
  forgotPassword(request: PasswordResetRequest): Promise<{ message: string }>;
  resetPassword(reset: PasswordReset): Promise<{ message: string }>;
  isAuthenticated(): boolean;
  getAccessToken(): string | null;
  getRefreshToken(): string | null;
  getClientId(): string | null;
  setClientId(clientId: string): void;
}

