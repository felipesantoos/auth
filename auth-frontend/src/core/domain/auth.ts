/**
 * Auth Domain Models
 * Pure domain types for authentication
 */

import type { User } from './user';

// Re-export User for convenience
export type { User };

export interface LoginCredentials {
  email: string;
  password: string;
  client_id?: string;
}

export interface RegistrationData {
  username: string;
  email: string;
  password: string;
  name: string;
  client_id?: string;
}

export interface PasswordResetRequest {
  email: string;
  client_id?: string;
}

export interface PasswordReset {
  reset_token: string;
  new_password: string;
  client_id?: string;
}

export interface AuthenticationResult {
  user: User;
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// Alias for backward compatibility
export type TokenResponse = AuthenticationResult;

