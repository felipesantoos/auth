/**
 * Permission Mapper
 * Converts between DTOs and Domain models
 */

import {
  Permission,
  PermissionAction,
  PermissionListResponse,
  GrantPermissionRequest,
} from '../../../core/domain/permission';
import {
  PermissionDTO,
  GrantPermissionDTO,
  PermissionListResponseDTO,
} from '../dtos/permission.dto';

export class PermissionMapper {
  /**
   * Convert DTO to Domain model
   */
  static toDomain(dto: PermissionDTO): Permission {
    return {
      id: dto.id,
      user_id: dto.user_id,
      client_id: dto.client_id,
      resource_type: dto.resource_type,
      resource_id: dto.resource_id,
      action: dto.action as PermissionAction,
      granted_by: dto.granted_by,
      created_at: new Date(dto.created_at),
    };
  }

  /**
   * Convert Domain model to DTO
   */
  static toDTO(permission: Permission): PermissionDTO {
    return {
      id: permission.id,
      user_id: permission.user_id,
      client_id: permission.client_id,
      resource_type: permission.resource_type,
      resource_id: permission.resource_id,
      action: permission.action,
      granted_by: permission.granted_by,
      created_at: permission.created_at.toISOString(),
    };
  }

  /**
   * Convert list response DTO to Domain
   */
  static listToDomain(dto: PermissionListResponseDTO): PermissionListResponse {
    return {
      permissions: dto.permissions.map(this.toDomain),
      total: dto.total,
    };
  }

  /**
   * Convert grant request to DTO
   */
  static grantRequestToDTO(request: GrantPermissionRequest): GrantPermissionDTO {
    return {
      user_id: request.user_id,
      resource_type: request.resource_type,
      action: request.action,
      resource_id: request.resource_id,
    };
  }
}

