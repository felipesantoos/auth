/**
 * Workspace Domain Models
 * Multi-workspace architecture support
 */

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  description?: string;
  settings?: Record<string, any>;
  active: boolean;
  created_at: Date;
  updated_at: Date;
}

export type WorkspaceRole = 'admin' | 'manager' | 'user';

export interface WorkspaceMember {
  id: string;
  user_id: string;
  workspace_id: string;
  role: WorkspaceRole;
  active: boolean;
  invited_at?: Date;
  joined_at?: Date;
  created_at: Date;
  updated_at: Date;
}

export interface CreateWorkspaceRequest {
  name: string;
  slug?: string;
  description?: string;
  settings?: Record<string, any>;
}

export interface UpdateWorkspaceRequest {
  name?: string;
  slug?: string;
  description?: string;
  settings?: Record<string, any>;
}

export interface AddMemberRequest {
  user_id: string;
  role: WorkspaceRole;
}

export interface UpdateMemberRoleRequest {
  role: WorkspaceRole;
}

export interface WorkspaceListResponse {
  workspaces: Workspace[];
  total: number;
}

export interface WorkspaceMemberListResponse {
  members: WorkspaceMember[];
  total: number;
}

