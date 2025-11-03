/**
 * Workspace DTOs
 * Data Transfer Objects for API communication
 */

export interface WorkspaceDTO {
  id: string;
  name: string;
  slug: string;
  description?: string;
  settings?: Record<string, unknown>;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceMemberDTO {
  id: string;
  user_id: string;
  workspace_id: string;
  role: string;
  active: boolean;
  invited_at?: string;
  joined_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateWorkspaceDTO {
  name: string;
  slug?: string;
  description?: string;
  settings?: Record<string, unknown>;
}

export interface UpdateWorkspaceDTO {
  name?: string;
  slug?: string;
  description?: string;
  settings?: Record<string, unknown>;
}

export interface AddMemberDTO {
  user_id: string;
  role: string;
}

export interface UpdateMemberRoleDTO {
  role: string;
}

export interface WorkspaceListResponseDTO {
  workspaces: WorkspaceDTO[];
  total: number;
}

export interface WorkspaceMemberListResponseDTO {
  members: WorkspaceMemberDTO[];
  total: number;
}

