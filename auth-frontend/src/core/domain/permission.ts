/**
 * Permission Domain Models
 * Fine-grained resource-level permissions
 */

export type PermissionAction = 'create' | 'read' | 'update' | 'delete' | 'manage';

export interface Permission {
  id: string;
  user_id: string;
  client_id: string;
  resource_type: string; // String livre - permite flexibilidade máxima
  resource_id?: string; // undefined = todas os recursos deste tipo
  action: PermissionAction;
  granted_by?: string;
  created_at: Date;
}

export interface GrantPermissionRequest {
  user_id: string;
  resource_type: string;
  action: PermissionAction;
  resource_id?: string;
}

export interface PermissionListResponse {
  permissions: Permission[];
  total: number;
}

/**
 * Helper class for permission checking
 */
export class PermissionChecker {
  /**
   * Check if a permission allows a specific action on a resource
   */
  static allows(
    permission: Permission,
    action: PermissionAction,
    resourceId?: string
  ): boolean {
    // MANAGE allows everything
    if (permission.action === 'manage') {
      return true;
    }

    // Check action match
    if (permission.action !== action) {
      return false;
    }

    // Check resource (if permission is resource-specific)
    if (permission.resource_id && resourceId && permission.resource_id !== resourceId) {
      return false;
    }

    return true;
  }

  /**
   * Check if user has permission for action on resource
   */
  static hasPermission(
    permissions: Permission[],
    resourceType: string,
    action: PermissionAction,
    resourceId?: string
  ): boolean {
    return permissions.some(
      (p) =>
        p.resource_type === resourceType &&
        this.allows(p, action, resourceId)
    );
  }
}

