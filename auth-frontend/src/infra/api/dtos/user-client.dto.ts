/**
 * User Client Access DTOs
 * Data Transfer Objects for API communication
 */

export interface UserClientAccessDTO {
  id: string;
  user_id: string;
  client_id: string;
  workspace_id?: string;
  active: boolean;
  granted_at: string;
  created_at: string;
  updated_at: string;
}

export interface GrantClientAccessDTO {
  client_id: string;
  workspace_id?: string;
}

export interface UserClientAccessListResponseDTO {
  accesses: UserClientAccessDTO[];
  total: number;
}

