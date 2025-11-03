/**
 * Permission Repository Interface
 * Secondary port for permission data access
 */

import {
  Permission,
  GrantPermissionRequest,
} from '../../domain/permission';

export interface IPermissionRepository {
  grantPermission(request: GrantPermissionRequest): Promise<Permission>;
  listUserPermissions(userId: string): Promise<Permission[]>;
  revokePermission(permissionId: string): Promise<void>;
  
  // Helper methods for permission checking
  hasPermission(
    userId: string,
    resourceType: string,
    action: string,
    resourceId?: string
  ): Promise<boolean>;
}

