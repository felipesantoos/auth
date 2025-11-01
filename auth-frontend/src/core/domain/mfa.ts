/**
 * MFA (Multi-Factor Authentication) Domain Models
 * TypeScript types for MFA functionality
 */

export interface MFASetupResponse {
  secret: string;
  qr_code: string;  // Base64 data URL for QR code image
  backup_codes: string[];  // Array of 10 backup codes (12 digits each, format: XXXX-XXXX-XXXX)
}

export interface MFARequiredResponse {
  mfa_required: true;
  user_id: string;
  message: string;
}

export interface MFALoginDTO {
  user_id: string;
  client_id: string;
  totp_code?: string;  // 6-digit TOTP code from authenticator app
  backup_code?: string;  // 12-digit backup code (format: XXXX-XXXX-XXXX)
}

export interface MFAStatusResponse {
  mfa_enabled: boolean;
  backup_codes_remaining?: number;  // Number of unused backup codes
}

export interface EnableMFARequest {
  secret: string;  // Secret from setup response
  totp_code: string;  // 6-digit code to verify setup
  backup_codes: string[];  // Backup codes from setup response
}

export interface DisableMFARequest {
  password: string;  // Current password required for security
}

export interface RegenerateBackupCodesResponse {
  backup_codes: string[];
}

