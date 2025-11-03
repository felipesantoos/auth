/**
 * User Client Access Mapper
 * Converts between DTOs and Domain models
 */

import type {
  UserClientAccess,
  UserClientAccessListResponse,
  GrantClientAccessRequest,
} from '../../../core/domain/user-client';
import type {
  UserClientAccessDTO,
  GrantClientAccessDTO,
  UserClientAccessListResponseDTO,
} from '../dtos/user-client.dto';

export class UserClientMapper {
  /**
   * Convert DTO to Domain model
   */
  static toDomain(dto: UserClientAccessDTO): UserClientAccess {
    return {
      id: dto.id,
      user_id: dto.user_id,
      client_id: dto.client_id,
      workspace_id: dto.workspace_id,
      active: dto.active,
      granted_at: new Date(dto.granted_at),
      created_at: new Date(dto.created_at),
      updated_at: new Date(dto.updated_at),
    };
  }

  /**
   * Convert Domain model to DTO
   */
  static toDTO(access: UserClientAccess): UserClientAccessDTO {
    return {
      id: access.id,
      user_id: access.user_id,
      client_id: access.client_id,
      workspace_id: access.workspace_id,
      active: access.active,
      granted_at: access.granted_at.toISOString(),
      created_at: access.created_at.toISOString(),
      updated_at: access.updated_at.toISOString(),
    };
  }

  /**
   * Convert list response DTO to Domain
   */
  static listToDomain(dto: UserClientAccessListResponseDTO): UserClientAccessListResponse {
    return {
      accesses: dto.accesses.map(this.toDomain),
      total: dto.total,
    };
  }

  /**
   * Convert grant request to DTO
   */
  static grantRequestToDTO(request: GrantClientAccessRequest): GrantClientAccessDTO {
    return {
      client_id: request.client_id,
      workspace_id: request.workspace_id,
    };
  }
}

