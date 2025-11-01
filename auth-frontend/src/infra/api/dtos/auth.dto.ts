/**
 * Auth API DTOs
 * Data Transfer Objects for API communication
 * These represent the contract with the backend API
 */

export interface LoginDTO {
  email: string;
  password: string;
  client_id?: string;
}

export interface RegisterDTO {
  username: string;
  email: string;
  password: string;
  name: string;
  client_id?: string;
}

export interface ForgotPasswordDTO {
  email: string;
  client_id?: string;
}

export interface ResetPasswordDTO {
  reset_token: string;
  new_password: string;
  client_id?: string;
}

export interface UserResponseDTO {
  id: string;
  username: string;
  email: string;
  name: string;
  role: string;
  active: boolean;
  client_id?: string;
  created_at: string;
}

export interface TokenResponseDTO {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserResponseDTO;
}

export interface MessageResponseDTO {
  message: string;
}

