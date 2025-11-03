/**
 * Workspace Service Implementation
 * Business logic for workspace management
 */

import type { IWorkspaceService } from '../../interfaces/primary/IWorkspaceService';
import type { IWorkspaceRepository } from '../../interfaces/secondary/IWorkspaceRepository';
import type {
  Workspace,
  WorkspaceMember,
  WorkspaceListResponse,
  WorkspaceMemberListResponse,
  CreateWorkspaceRequest,
  UpdateWorkspaceRequest,
  AddMemberRequest,
  UpdateMemberRoleRequest,
} from '../../domain/workspace';
import { BusinessValidationError } from '../../domain/errors';

export class WorkspaceService implements IWorkspaceService {
  private readonly repository: IWorkspaceRepository;

  constructor(repository: IWorkspaceRepository) {
    this.repository = repository;
  }

  /**
   * Create a new workspace
   * Validates that name is provided and not empty
   */
  async createWorkspace(request: CreateWorkspaceRequest): Promise<Workspace> {
    // Validation
    if (!request.name || request.name.trim().length === 0) {
      throw new BusinessValidationError('Workspace name is required');
    }

    if (request.name.length > 200) {
      throw new BusinessValidationError('Workspace name must be less than 200 characters');
    }

    // Auto-generate slug if not provided
    if (!request.slug) {
      request.slug = this.generateSlug(request.name);
    }

    return this.repository.createWorkspace(request);
  }

  /**
   * List workspaces
   */
  async listWorkspaces(activeOnly: boolean = true): Promise<WorkspaceListResponse> {
    return this.repository.listWorkspaces(activeOnly);
  }

  /**
   * Get workspace by ID
   */
  async getWorkspace(workspaceId: string): Promise<Workspace> {
    if (!workspaceId) {
      throw new BusinessValidationError('Workspace ID is required');
    }

    return this.repository.getWorkspace(workspaceId);
  }

  /**
   * Update workspace
   */
  async updateWorkspace(
    workspaceId: string,
    request: UpdateWorkspaceRequest
  ): Promise<Workspace> {
    if (!workspaceId) {
      throw new BusinessValidationError('Workspace ID is required');
    }

    if (request.name !== undefined && request.name.trim().length === 0) {
      throw new BusinessValidationError('Workspace name cannot be empty');
    }

    return this.repository.updateWorkspace(workspaceId, request);
  }

  /**
   * Delete workspace
   */
  async deleteWorkspace(workspaceId: string): Promise<void> {
    if (!workspaceId) {
      throw new BusinessValidationError('Workspace ID is required');
    }

    return this.repository.deleteWorkspace(workspaceId);
  }

  /**
   * Add member to workspace
   */
  async addMember(workspaceId: string, request: AddMemberRequest): Promise<WorkspaceMember> {
    if (!workspaceId) {
      throw new BusinessValidationError('Workspace ID is required');
    }

    if (!request.user_id) {
      throw new BusinessValidationError('User ID is required');
    }

    if (!request.role) {
      throw new BusinessValidationError('Role is required');
    }

    return this.repository.addMember(workspaceId, request);
  }

  /**
   * List workspace members
   */
  async listMembers(
    workspaceId: string,
    activeOnly: boolean = true
  ): Promise<WorkspaceMemberListResponse> {
    if (!workspaceId) {
      throw new BusinessValidationError('Workspace ID is required');
    }

    return this.repository.listMembers(workspaceId, activeOnly);
  }

  /**
   * Update member role
   */
  async updateMemberRole(
    workspaceId: string,
    userId: string,
    request: UpdateMemberRoleRequest
  ): Promise<WorkspaceMember> {
    if (!workspaceId) {
      throw new BusinessValidationError('Workspace ID is required');
    }

    if (!userId) {
      throw new BusinessValidationError('User ID is required');
    }

    if (!request.role) {
      throw new BusinessValidationError('Role is required');
    }

    return this.repository.updateMemberRole(workspaceId, userId, request);
  }

  /**
   * Remove member from workspace
   */
  async removeMember(workspaceId: string, userId: string): Promise<void> {
    if (!workspaceId) {
      throw new BusinessValidationError('Workspace ID is required');
    }

    if (!userId) {
      throw new BusinessValidationError('User ID is required');
    }

    return this.repository.removeMember(workspaceId, userId);
  }

  /**
   * Get user's workspaces
   */
  async getUserWorkspaces(
    userId: string,
    activeOnly: boolean = true
  ): Promise<WorkspaceMemberListResponse> {
    if (!userId) {
      throw new BusinessValidationError('User ID is required');
    }

    return this.repository.getUserWorkspaces(userId, activeOnly);
  }

  /**
   * Leave workspace
   */
  async leaveWorkspace(workspaceId: string): Promise<void> {
    if (!workspaceId) {
      throw new BusinessValidationError('Workspace ID is required');
    }

    return this.repository.leaveWorkspace(workspaceId);
  }

  /**
   * Check if user can manage workspace (is admin or manager)
   */
  async canUserManageWorkspace(workspaceId: string, userId: string): Promise<boolean> {
    try {
      const member = await this.repository.getMember(workspaceId, userId);
      return member.role === 'admin' || member.role === 'manager';
    } catch {
      return false;
    }
  }

  /**
   * Check if user is workspace admin
   */
  async isUserWorkspaceAdmin(workspaceId: string, userId: string): Promise<boolean> {
    try {
      const member = await this.repository.getMember(workspaceId, userId);
      return member.role === 'admin';
    } catch {
      return false;
    }
  }

  /**
   * Generate URL-friendly slug from name
   */
  private generateSlug(name: string): string {
    return name
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, '')
      .replace(/[\s_-]+/g, '-')
      .replace(/^-+|-+$/g, '');
  }
}

