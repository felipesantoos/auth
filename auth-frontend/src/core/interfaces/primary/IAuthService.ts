/**
 * Auth Service Interface (Primary Port)
 * Defines the contract for authentication use cases
 */

import { User } from '../../domain/user';
import { LoginDTO, RegisterDTO, ForgotPasswordDTO, ResetPasswordDTO } from '../../../infra/api/dtos/auth.dto';

export interface IAuthService {
  login(credentials: LoginDTO): Promise<User>;
  register(data: RegisterDTO): Promise<User>;
  logout(): Promise<void>;
  getCurrentUser(): Promise<User | null>;
  refreshToken(): Promise<void>;
  forgotPassword(data: ForgotPasswordDTO): Promise<{ message: string }>;
  resetPassword(data: ResetPasswordDTO): Promise<{ message: string }>;
  isAuthenticated(): boolean;
  getAccessToken(): string | null;
  getRefreshToken(): string | null;
  getClientId(): string | null;
  setClientId(clientId: string): void;
}

