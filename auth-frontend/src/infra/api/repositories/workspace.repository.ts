/**
 * Workspace Repository Implementation
 * HTTP-based implementation of IWorkspaceRepository
 */

import { httpClient } from '../http-client';
import { IWorkspaceRepository } from '../../../core/interfaces/secondary/IWorkspaceRepository';
import {
  Workspace,
  WorkspaceMember,
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
import { WorkspaceMapper } from '../mappers/workspace.mapper';

export class WorkspaceRepository implements IWorkspaceRepository {
  private readonly baseUrl = '/api/v1/workspaces';

  /**
   * Create a new workspace
   */
  async createWorkspace(request: CreateWorkspaceRequest): Promise<Workspace> {
    const dto = WorkspaceMapper.createRequestToDTO(request);
    const response = await httpClient.post<WorkspaceDTO>(this.baseUrl, dto);
    return WorkspaceMapper.toDomain(response);
  }

  /**
   * List workspaces the current user is a member of
   */
  async listWorkspaces(activeOnly: boolean = true): Promise<WorkspaceListResponse> {
    const params = new URLSearchParams();
    params.append('active_only', activeOnly.toString());
    
    const response = await httpClient.get<WorkspaceListResponseDTO>(
      `${this.baseUrl}?${params.toString()}`
    );
    return WorkspaceMapper.listToDomain(response);
  }

  /**
   * Get workspace by ID
   */
  async getWorkspace(workspaceId: string): Promise<Workspace> {
    const response = await httpClient.get<WorkspaceDTO>(`${this.baseUrl}/${workspaceId}`);
    return WorkspaceMapper.toDomain(response);
  }

  /**
   * Update workspace
   */
  async updateWorkspace(
    workspaceId: string,
    request: UpdateWorkspaceRequest
  ): Promise<Workspace> {
    const dto = WorkspaceMapper.updateRequestToDTO(request);
    const response = await httpClient.patch<WorkspaceDTO>(
      `${this.baseUrl}/${workspaceId}`,
      dto
    );
    return WorkspaceMapper.toDomain(response);
  }

  /**
   * Delete workspace
   */
  async deleteWorkspace(workspaceId: string): Promise<void> {
    await httpClient.delete(`${this.baseUrl}/${workspaceId}`);
  }

  /**
   * Activate workspace
   */
  async activateWorkspace(workspaceId: string): Promise<Workspace> {
    const response = await httpClient.post<WorkspaceDTO>(
      `${this.baseUrl}/${workspaceId}/activate`
    );
    return WorkspaceMapper.toDomain(response);
  }

  /**
   * Deactivate workspace
   */
  async deactivateWorkspace(workspaceId: string): Promise<Workspace> {
    const response = await httpClient.post<WorkspaceDTO>(
      `${this.baseUrl}/${workspaceId}/deactivate`
    );
    return WorkspaceMapper.toDomain(response);
  }

  /**
   * Add member to workspace
   */
  async addMember(workspaceId: string, request: AddMemberRequest): Promise<WorkspaceMember> {
    const dto = WorkspaceMapper.addMemberRequestToDTO(request);
    const response = await httpClient.post<WorkspaceMemberDTO>(
      `${this.baseUrl}/${workspaceId}/members`,
      dto
    );
    return WorkspaceMapper.memberToDomain(response);
  }

  /**
   * List workspace members
   */
  async listMembers(
    workspaceId: string,
    activeOnly: boolean = true
  ): Promise<WorkspaceMemberListResponse> {
    const params = new URLSearchParams();
    params.append('active_only', activeOnly.toString());
    
    const response = await httpClient.get<WorkspaceMemberListResponseDTO>(
      `${this.baseUrl}/${workspaceId}/members?${params.toString()}`
    );
    return WorkspaceMapper.memberListToDomain(response);
  }

  /**
   * Get specific member
   */
  async getMember(workspaceId: string, userId: string): Promise<WorkspaceMember> {
    const response = await httpClient.get<WorkspaceMemberDTO>(
      `${this.baseUrl}/${workspaceId}/members/${userId}`
    );
    return WorkspaceMapper.memberToDomain(response);
  }

  /**
   * Update member role
   */
  async updateMemberRole(
    workspaceId: string,
    userId: string,
    request: UpdateMemberRoleRequest
  ): Promise<WorkspaceMember> {
    const dto = WorkspaceMapper.updateMemberRoleRequestToDTO(request);
    const response = await httpClient.patch<WorkspaceMemberDTO>(
      `${this.baseUrl}/${workspaceId}/members/${userId}`,
      dto
    );
    return WorkspaceMapper.memberToDomain(response);
  }

  /**
   * Remove member from workspace
   */
  async removeMember(workspaceId: string, userId: string): Promise<void> {
    await httpClient.delete(`${this.baseUrl}/${workspaceId}/members/${userId}`);
  }

  /**
   * Get user's workspaces
   */
  async getUserWorkspaces(
    userId: string,
    activeOnly: boolean = true
  ): Promise<WorkspaceMemberListResponse> {
    const params = new URLSearchParams();
    params.append('active_only', activeOnly.toString());
    
    const response = await httpClient.get<WorkspaceMemberListResponseDTO>(
      `${this.baseUrl}/my-workspaces?${params.toString()}`
    );
    return WorkspaceMapper.memberListToDomain(response);
  }

  /**
   * Leave workspace
   */
  async leaveWorkspace(workspaceId: string): Promise<void> {
    await httpClient.post(`${this.baseUrl}/${workspaceId}/leave`);
  }
}

// Export singleton instance
export const workspaceRepository = new WorkspaceRepository();

