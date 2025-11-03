/**
 * Permission DTOs
 * Data Transfer Objects for API communication
 */

export interface PermissionDTO {
  id: string;
  user_id: string;
  client_id: string;
  resource_type: string;
  resource_id?: string;
  action: string;
  granted_by?: string;
  created_at: string;
}

export interface GrantPermissionDTO {
  user_id: string;
  resource_type: string;
  action: string;
  resource_id?: string;
}

export interface PermissionListResponseDTO {
  permissions: PermissionDTO[];
  total: number;
}

