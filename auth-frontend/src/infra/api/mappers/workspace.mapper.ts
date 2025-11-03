/**
 * Workspace Mapper
 * Converts between DTOs and Domain models
 */

import {
  Workspace,
  WorkspaceMember,
  WorkspaceRole,
  WorkspaceListResponse,
  WorkspaceMemberListResponse,
  CreateWorkspaceRequest,
  UpdateWorkspaceRequest,
  AddMemberRequest,
  UpdateMemberRoleRequest,
} from '../../../core/domain/workspace';
import {
  WorkspaceDTO,
  WorkspaceMemberDTO,
  WorkspaceListResponseDTO,
  WorkspaceMemberListResponseDTO,
  CreateWorkspaceDTO,
  UpdateWorkspaceDTO,
  AddMemberDTO,
  UpdateMemberRoleDTO,
} from '../dtos/workspace.dto';

export class WorkspaceMapper {
  /**
   * Convert DTO to Domain model
   */
  static toDomain(dto: WorkspaceDTO): Workspace {
    return {
      id: dto.id,
      name: dto.name,
      slug: dto.slug,
      description: dto.description,
      settings: dto.settings,
      active: dto.active,
      created_at: new Date(dto.created_at),
      updated_at: new Date(dto.updated_at),
    };
  }

  /**
   * Convert Domain model to DTO
   */
  static toDTO(workspace: Workspace): WorkspaceDTO {
    return {
      id: workspace.id,
      name: workspace.name,
      slug: workspace.slug,
      description: workspace.description,
      settings: workspace.settings,
      active: workspace.active,
      created_at: workspace.created_at.toISOString(),
      updated_at: workspace.updated_at.toISOString(),
    };
  }

  /**
   * Convert WorkspaceMember DTO to Domain model
   */
  static memberToDomain(dto: WorkspaceMemberDTO): WorkspaceMember {
    return {
      id: dto.id,
      user_id: dto.user_id,
      workspace_id: dto.workspace_id,
      role: dto.role as WorkspaceRole,
      active: dto.active,
      invited_at: dto.invited_at ? new Date(dto.invited_at) : undefined,
      joined_at: dto.joined_at ? new Date(dto.joined_at) : undefined,
      created_at: new Date(dto.created_at),
      updated_at: new Date(dto.updated_at),
    };
  }

  /**
   * Convert WorkspaceMember Domain model to DTO
   */
  static memberToDTO(member: WorkspaceMember): WorkspaceMemberDTO {
    return {
      id: member.id,
      user_id: member.user_id,
      workspace_id: member.workspace_id,
      role: member.role,
      active: member.active,
      invited_at: member.invited_at?.toISOString(),
      joined_at: member.joined_at?.toISOString(),
      created_at: member.created_at.toISOString(),
      updated_at: member.updated_at.toISOString(),
    };
  }

  /**
   * Convert list response DTO to Domain
   */
  static listToDomain(dto: WorkspaceListResponseDTO): WorkspaceListResponse {
    return {
      workspaces: dto.workspaces.map(this.toDomain),
      total: dto.total,
    };
  }

  /**
   * Convert member list response DTO to Domain
   */
  static memberListToDomain(dto: WorkspaceMemberListResponseDTO): WorkspaceMemberListResponse {
    return {
      members: dto.members.map(this.memberToDomain),
      total: dto.total,
    };
  }

  /**
   * Convert create request to DTO
   */
  static createRequestToDTO(request: CreateWorkspaceRequest): CreateWorkspaceDTO {
    return {
      name: request.name,
      slug: request.slug,
      description: request.description,
      settings: request.settings,
    };
  }

  /**
   * Convert update request to DTO
   */
  static updateRequestToDTO(request: UpdateWorkspaceRequest): UpdateWorkspaceDTO {
    return {
      name: request.name,
      slug: request.slug,
      description: request.description,
      settings: request.settings,
    };
  }

  /**
   * Convert add member request to DTO
   */
  static addMemberRequestToDTO(request: AddMemberRequest): AddMemberDTO {
    return {
      user_id: request.user_id,
      role: request.role,
    };
  }

  /**
   * Convert update member role request to DTO
   */
  static updateMemberRoleRequestToDTO(request: UpdateMemberRoleRequest): UpdateMemberRoleDTO {
    return {
      role: request.role,
    };
  }
}

