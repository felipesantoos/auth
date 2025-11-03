/**
 * Workspace Repository Interface
 * Secondary port for workspace data access
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

export interface IWorkspaceRepository {
  // Workspace CRUD
  createWorkspace(request: CreateWorkspaceRequest): Promise<Workspace>;
  listWorkspaces(activeOnly?: boolean): Promise<WorkspaceListResponse>;
  getWorkspace(workspaceId: string): Promise<Workspace>;
  updateWorkspace(workspaceId: string, request: UpdateWorkspaceRequest): Promise<Workspace>;
  deleteWorkspace(workspaceId: string): Promise<void>;
  activateWorkspace(workspaceId: string): Promise<Workspace>;
  deactivateWorkspace(workspaceId: string): Promise<Workspace>;

  // Member Management
  addMember(workspaceId: string, request: AddMemberRequest): Promise<WorkspaceMember>;
  listMembers(workspaceId: string, activeOnly?: boolean): Promise<WorkspaceMemberListResponse>;
  getMember(workspaceId: string, userId: string): Promise<WorkspaceMember>;
  updateMemberRole(workspaceId: string, userId: string, request: UpdateMemberRoleRequest): Promise<WorkspaceMember>;
  removeMember(workspaceId: string, userId: string): Promise<void>;
  
  // User's workspaces
  getUserWorkspaces(userId: string, activeOnly?: boolean): Promise<WorkspaceMemberListResponse>;
  leaveWorkspace(workspaceId: string): Promise<void>;
}

