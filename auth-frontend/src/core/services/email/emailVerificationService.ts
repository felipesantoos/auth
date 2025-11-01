/**
 * Email Verification Service
 * Handles email verification operations
 */
import apiClient from '../../repositories/api_client';
import { 
  VerifyEmailRequest, 
  EmailVerificationStatusResponse,
  ResendVerificationResponse,
  VerifyEmailResponse 
} from '../../domain/email';

export class EmailVerificationService {
  /**
   * Verify email address with token
   * Token is received via email link after registration
   */
  async verifyEmail(request: VerifyEmailRequest): Promise<VerifyEmailResponse> {
    const response = await apiClient.post<VerifyEmailResponse>('/api/auth/email/verify', request);
    return response.data;
  }

  /**
   * Resend verification email
   * Can only be called if email is not yet verified
   */
  async resendVerification(): Promise<ResendVerificationResponse> {
    const response = await apiClient.post<ResendVerificationResponse>('/api/auth/email/resend-verification');
    return response.data;
  }

  /**
   * Get email verification status for current user
   */
  async getStatus(): Promise<EmailVerificationStatusResponse> {
    const response = await apiClient.get<EmailVerificationStatusResponse>('/api/auth/email/status');
    return response.data;
  }
}

