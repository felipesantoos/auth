/**
 * Email Verification Domain Models
 * TypeScript types for email verification functionality
 */

export interface VerifyEmailRequest {
  user_id: string;
  token: string;
  client_id?: string;
}

export interface EmailVerificationStatusResponse {
  email_verified: boolean;
}

export interface ResendVerificationResponse {
  success: boolean;
  message: string;
}

export interface VerifyEmailResponse {
  success: boolean;
  message: string;
}

