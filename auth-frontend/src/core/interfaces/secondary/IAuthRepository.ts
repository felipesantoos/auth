/**
 * Auth Repository Interface (Secondary Port)
 * Defines the contract for authentication data access
 */

import { 
  LoginDTO, 
  RegisterDTO, 
  ForgotPasswordDTO, 
  ResetPasswordDTO,
  TokenResponseDTO,
  UserResponseDTO,
  MessageResponseDTO
} from '../../../infra/api/dtos/auth.dto';

export interface IAuthRepository {
  login(credentials: LoginDTO): Promise<TokenResponseDTO>;
  register(data: RegisterDTO): Promise<TokenResponseDTO>;
  logout(refreshToken: string): Promise<void>;
  getCurrentUser(): Promise<UserResponseDTO>;
  refreshToken(refreshToken: string): Promise<TokenResponseDTO>;
  forgotPassword(data: ForgotPasswordDTO): Promise<MessageResponseDTO>;
  resetPassword(data: ResetPasswordDTO): Promise<MessageResponseDTO>;
  changePassword(oldPassword: string, newPassword: string): Promise<void>;
}

