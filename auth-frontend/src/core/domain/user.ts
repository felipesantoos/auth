/**
 * User Domain Model
 * Pure domain entity - no DTOs or API concerns
 * 
 * NOTE: Role is now per-workspace (via WorkspaceMember)
 * User model only contains core user data
 */

export class User {
  readonly id: string;
  readonly username: string;
  readonly email: string;
  readonly name: string;
  readonly active: boolean;
  readonly createdAt: Date;
  readonly emailVerified: boolean;
  readonly mfaEnabled: boolean;
  readonly avatarUrl?: string;
  readonly kycDocumentId?: string;
  readonly kycStatus?: 'pending' | 'approved' | 'rejected';
  readonly kycVerifiedAt?: Date;

  constructor(
    id: string,
    username: string,
    email: string,
    name: string,
    active: boolean,
    createdAt: Date,
    emailVerified?: boolean,
    mfaEnabled?: boolean,
    avatarUrl?: string,
    kycDocumentId?: string,
    kycStatus?: 'pending' | 'approved' | 'rejected',
    kycVerifiedAt?: Date
  ) {
    this.id = id;
    this.username = username;
    this.email = email;
    this.name = name;
    this.active = active;
    this.createdAt = createdAt;
    this.emailVerified = emailVerified ?? false;
    this.mfaEnabled = mfaEnabled ?? false;
    this.avatarUrl = avatarUrl;
    this.kycDocumentId = kycDocumentId;
    this.kycStatus = kycStatus;
    this.kycVerifiedAt = kycVerifiedAt;
  }

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

