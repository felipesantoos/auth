/**
 * Auth Service Interface
 * Defines contract for authentication operations
 */
import { User, LoginDTO, RegisterDTO, ForgotPasswordDTO, ResetPasswordDTO, MessageResponse } from '../../domain/auth';

export interface AuthServiceInterface {
  login(credentials: LoginDTO): Promise<User>;
  register(data: RegisterDTO): Promise<User>;
  logout(): Promise<void>;
  getCurrentUser(): Promise<User | null>;
  isAuthenticated(): boolean;
  getToken(): string | null;
  getRefreshToken(): string | null;
  getClientId(): string | null;
  setClientId(clientId: string): void;
  forgotPassword(data: ForgotPasswordDTO): Promise<MessageResponse>;
  resetPassword(data: ResetPasswordDTO): Promise<MessageResponse>;
}

