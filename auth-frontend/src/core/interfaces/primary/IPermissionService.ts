/**
 * Permission Service Interface
 * Primary port for permission business logic
 */

import {
  Permission,
  PermissionAction,
  GrantPermissionRequest,
} from '../../domain/permission';

export interface IPermissionService {
  grantPermission(request: GrantPermissionRequest): Promise<Permission>;
  listUserPermissions(userId: string): Promise<Permission[]>;
  revokePermission(permissionId: string): Promise<void>;
  
  // Permission checking
  hasPermission(
    userId: string,
    resourceType: string,
    action: PermissionAction,
    resourceId?: string
  ): Promise<boolean>;
  
  canManageResource(
    userId: string,
    resourceType: string,
    resourceId?: string
  ): Promise<boolean>;
}

