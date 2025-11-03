/**
 * Permission Service Implementation
 * Business logic for permission management
 */

import type { IPermissionService } from '../../interfaces/primary/IPermissionService';
import type { IPermissionRepository } from '../../interfaces/secondary/IPermissionRepository';
import type {
  Permission,
  PermissionAction,
  GrantPermissionRequest,
} from '../../domain/permission';
import { PermissionChecker } from '../../domain/permission';
import { BusinessValidationError } from '../../domain/errors';

export class PermissionService implements IPermissionService {
  private readonly repository: IPermissionRepository;

  constructor(repository: IPermissionRepository) {
    this.repository = repository;
  }

  /**
   * Grant permission to user
   */
  async grantPermission(request: GrantPermissionRequest): Promise<Permission> {
    // Validation
    if (!request.user_id) {
      throw new BusinessValidationError('User ID is required');
    }

    if (!request.resource_type || request.resource_type.trim().length === 0) {
      throw new BusinessValidationError('Resource type is required');
    }

    if (!request.action) {
      throw new BusinessValidationError('Action is required');
    }

    // Normalize resource type
    request.resource_type = request.resource_type.toLowerCase().trim();

    return this.repository.grantPermission(request);
  }

  /**
   * List user's permissions
   */
  async listUserPermissions(userId: string): Promise<Permission[]> {
    if (!userId) {
      throw new BusinessValidationError('User ID is required');
    }

    return this.repository.listUserPermissions(userId);
  }

  /**
   * Revoke permission
   */
  async revokePermission(permissionId: string): Promise<void> {
    if (!permissionId) {
      throw new BusinessValidationError('Permission ID is required');
    }

    return this.repository.revokePermission(permissionId);
  }

  /**
   * Check if user has specific permission
   */
  async hasPermission(
    userId: string,
    resourceType: string,
    action: PermissionAction,
    resourceId?: string
  ): Promise<boolean> {
    if (!userId || !resourceType || !action) {
      return false;
    }

    try {
      const permissions = await this.repository.listUserPermissions(userId);
      return PermissionChecker.hasPermission(
        permissions,
        resourceType.toLowerCase(),
        action,
        resourceId
      );
    } catch (error) {
      console.error('Error checking permission:', error);
      return false;
    }
  }

  /**
   * Check if user can manage resource (has MANAGE permission)
   */
  async canManageResource(
    userId: string,
    resourceType: string,
    resourceId?: string
  ): Promise<boolean> {
    return this.hasPermission(userId, resourceType, 'manage', resourceId);
  }
}

