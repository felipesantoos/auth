/**
 * Permission Repository Implementation
 * HTTP-based implementation of IPermissionRepository
 */

import { httpClient } from '../http-client';
import type { IPermissionRepository } from '../../../core/interfaces/secondary/IPermissionRepository';
import type {
  Permission,
  GrantPermissionRequest,
} from '../../../core/domain/permission';
import {
  PermissionChecker,
} from '../../../core/domain/permission';
import type {
  PermissionDTO,
} from '../dtos/permission.dto';
import { PermissionMapper } from '../mappers/permission.mapper';

export class PermissionRepository implements IPermissionRepository {
  private readonly baseUrl = '/api/v1/auth/permissions';

  /**
   * Grant permission to user
   */
  async grantPermission(request: GrantPermissionRequest): Promise<Permission> {
    const dto = PermissionMapper.grantRequestToDTO(request);
    const response = await httpClient.post<PermissionDTO>(this.baseUrl, dto);
    return PermissionMapper.toDomain(response);
  }

  /**
   * List user's permissions
   */
  async listUserPermissions(userId: string): Promise<Permission[]> {
    const response = await httpClient.get<PermissionDTO[]>(
      `${this.baseUrl}/user/${userId}`
    );
    return response.map(PermissionMapper.toDomain);
  }

  /**
   * Revoke permission
   */
  async revokePermission(permissionId: string): Promise<void> {
    await httpClient.delete(`${this.baseUrl}/${permissionId}`);
  }

  /**
   * Check if user has specific permission
   * This is a client-side check based on cached permissions
   */
  async hasPermission(
    userId: string,
    resourceType: string,
    action: string,
    resourceId?: string
  ): Promise<boolean> {
    try {
      const permissions = await this.listUserPermissions(userId);
      return PermissionChecker.hasPermission(
        permissions,
        resourceType,
        action as any,
        resourceId
      );
    } catch (error) {
      console.error('Error checking permission:', error);
      return false;
    }
  }
}

// Export singleton instance
export const permissionRepository = new PermissionRepository();

