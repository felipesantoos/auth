/**
 * User Client Access Domain Models
 * Direct user-to-client access management
 */

export interface UserClientAccess {
  id: string;
  user_id: string;
  client_id: string;
  workspace_id?: string;
  active: boolean;
  granted_at: Date;
  created_at: Date;
  updated_at: Date;
}

export interface GrantClientAccessRequest {
  client_id: string;
  workspace_id?: string;
}

export interface UserClientAccessListResponse {
  accesses: UserClientAccess[];
  total: number;
}

