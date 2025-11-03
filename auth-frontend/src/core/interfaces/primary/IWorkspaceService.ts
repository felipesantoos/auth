/**
 * Workspace Service Interface
 * Primary port for workspace business logic
 */

import {
  Workspace,
  WorkspaceMember,
  WorkspaceListResponse,
  WorkspaceMemberListResponse,
  CreateWorkspaceRequest,
  UpdateWorkspaceRequest,
  AddMemberRequest,
  UpdateMemberRoleRequest,
} from '../../domain/workspace';

export interface IWorkspaceService {
  // Workspace management
  createWorkspace(request: CreateWorkspaceRequest): Promise<Workspace>;
  listWorkspaces(activeOnly?: boolean): Promise<WorkspaceListResponse>;
  getWorkspace(workspaceId: string): Promise<Workspace>;
  updateWorkspace(workspaceId: string, request: UpdateWorkspaceRequest): Promise<Workspace>;
  deleteWorkspace(workspaceId: string): Promise<void>;
  
  // Member management
  addMember(workspaceId: string, request: AddMemberRequest): Promise<WorkspaceMember>;
  listMembers(workspaceId: string, activeOnly?: boolean): Promise<WorkspaceMemberListResponse>;
  updateMemberRole(workspaceId: string, userId: string, request: UpdateMemberRoleRequest): Promise<WorkspaceMember>;
  removeMember(workspaceId: string, userId: string): Promise<void>;
  
  // User operations
  getUserWorkspaces(userId: string, activeOnly?: boolean): Promise<WorkspaceMemberListResponse>;
  leaveWorkspace(workspaceId: string): Promise<void>;
  
  // Business rules
  canUserManageWorkspace(workspaceId: string, userId: string): Promise<boolean>;
  isUserWorkspaceAdmin(workspaceId: string, userId: string): Promise<boolean>;
}

