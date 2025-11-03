/**
 * User Domain Model
 * Pure domain entity - no DTOs or API concerns
 * 
 * NOTE: Role is now per-workspace (via WorkspaceMember)
 * User model only contains core user data
 */

export class User {
  constructor(
    public readonly id: string,
    public readonly username: string,
    public readonly email: string,
    public readonly name: string,
    public readonly active: boolean,
    public readonly createdAt: Date,
    public readonly emailVerified: boolean = false,
    public readonly mfaEnabled: boolean = false,
    public readonly avatarUrl?: string,
    public readonly kycDocumentId?: string,
    public readonly kycStatus?: 'pending' | 'approved' | 'rejected',
    public readonly kycVerifiedAt?: Date
  ) {}

  /**
   * Check if user has completed KYC verification
   */
  isKycVerified(): boolean {
    return this.kycStatus === 'approved' && !!this.kycVerifiedAt;
  }

  /**
   * Check if user needs to verify email
   */
  needsEmailVerification(): boolean {
    return !this.emailVerified;
  }

  /**
   * Check if user has MFA enabled
   */
  hasMfaEnabled(): boolean {
    return this.mfaEnabled;
  }
}

/**
 * User with workspace context
 * Includes the user's role in a specific workspace
 */
export interface UserWithWorkspace extends User {
  workspaceId: string;
  workspaceRole: 'admin' | 'manager' | 'user';
}

/**
 * Legacy interface for backward compatibility
 * @deprecated Use User class instead
 */
export interface UserLegacy {
  id: string;
  username: string;
  email: string;
  name: string;
  role: 'admin' | 'manager' | 'user';
  active: boolean;
  createdAt: Date;
  clientId?: string;
}

