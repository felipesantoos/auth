/**
 * Auth Repository Interface (Secondary Port)
 * Defines the contract for authentication data access
 * Uses only domain types - no infrastructure dependencies
 */

import type { User } from '../../domain/user';
import type {
  LoginCredentials,
  RegistrationData,
  PasswordResetRequest,
  PasswordReset,
  AuthenticationResult,
} from '../../domain/auth';

export interface IAuthRepository {
  login(credentials: LoginCredentials): Promise<AuthenticationResult>;
  register(data: RegistrationData): Promise<AuthenticationResult>;
  logout(refreshToken: string): Promise<void>;
  getCurrentUser(): Promise<User>;
  refreshToken(refreshToken: string): Promise<AuthenticationResult>;
  forgotPassword(request: PasswordResetRequest): Promise<{ message: string }>;
  resetPassword(reset: PasswordReset): Promise<{ message: string }>;
  changePassword(oldPassword: string, newPassword: string): Promise<void>;
}

