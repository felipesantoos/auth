/**
 * MFA Service
 * Handles multi-factor authentication operations
 */
import apiClient from '../../repositories/api_client';
import type { 
  MFASetupResponse, 
  MFALoginDTO, 
  MFAStatusResponse,
  EnableMFARequest,
  RegenerateBackupCodesResponse
} from '../../domain/mfa';
import type { TokenResponse } from '../../domain/auth';

export class MFAService {
  /**
   * Initialize MFA setup
   * Returns QR code and backup codes for user to save
   */
  async setupMFA(): Promise<MFASetupResponse> {
    const response = await apiClient.post<MFASetupResponse>('/api/auth/mfa/setup');
    return response.data;
  }

  /**
   * Enable MFA after setup
   * Requires valid TOTP code verification
   */
  async enableMFA(data: EnableMFARequest): Promise<void> {
    await apiClient.post('/api/auth/mfa/enable', data);
  }

  /**
   * Complete login with MFA
   * Called after initial login returns mfa_required=true
   */
  async loginWithMFA(data: MFALoginDTO): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/api/auth/login/mfa', data);
    return response.data;
  }

  /**
   * Get MFA status for current user
   * Shows if MFA is enabled and remaining backup codes
   */
  async getMFAStatus(): Promise<MFAStatusResponse> {
    const response = await apiClient.get<MFAStatusResponse>('/api/auth/mfa/status');
    return response.data;
  }

  /**
   * Disable MFA
   * Requires password confirmation
   */
  async disableMFA(password: string): Promise<void> {
    await apiClient.post('/api/auth/mfa/disable', { password });
  }

  /**
   * Regenerate all backup codes
   * Invalidates existing codes and creates new ones
   */
  async regenerateBackupCodes(): Promise<string[]> {
    const response = await apiClient.post<RegenerateBackupCodesResponse>('/api/auth/mfa/regenerate-backup-codes');
    return response.data.backup_codes;
  }
}

