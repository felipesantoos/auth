/**
 * Auth Domain Models
 * TypeScript domain models for authentication
 */

export interface User {
  id: string;
  username: string;
  email: string;
  name: string;
  role: 'admin' | 'manager' | 'user';
  active: boolean;
  client_id?: string;
  created_at: string;
}

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

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface UserResponse {
  id: string;
  username: string;
  email: string;
  name: string;
  role: string;
  active: boolean;
  client_id?: string;
  created_at: string;
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

export interface MessageResponse {
  message: string;
}

