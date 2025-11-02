/**
 * DTOs for Audit API
 */

export interface EntityChangeDTO {
  field: string;
  old_value: any;
  new_value: any;
  field_type: string;
  change_type: "added" | "modified" | "removed";
}

export interface AuditLogDTO {
  id: string;
  event_id: string;
  event_type: string;
  event_category: string;
  action: string;
  description?: string;
  user_id?: string;
  username?: string;
  user_email?: string;
  impersonated_by?: string;
  resource_type?: string;
  resource_id?: string;
  resource_name?: string;
  ip_address?: string;
  user_agent?: string;
  location?: string;
  request_id?: string;
  session_id?: string;
  changes?: EntityChangeDTO[];
  old_values?: Record<string, any>;
  new_values?: Record<string, any>;
  metadata?: Record<string, any>;
  tags?: string[];
  success: boolean;
  error_message?: string;
  created_at: string;
}

export interface AuditFiltersDTO {
  user_id?: string;
  username?: string;
  resource_type?: string;
  resource_id?: string;
  event_category?: string;
  event_types?: string[];
  start_date?: string;
  end_date?: string;
  tags?: string[];
  success?: boolean;
  search_query?: string;
}

export interface AuditStatisticsDTO {
  total_events: number;
  events_by_category: Record<string, number>;
  top_users: Array<{
    username: string;
    count: number;
  }>;
  failed_events: number;
  success_rate: number;
}

export interface UserActivityTimelineDTO {
  date: string;
  count: number;
}

export interface AuditLogsResponseDTO {
  logs: AuditLogDTO[];
  total: number;
  limit: number;
  offset: number;
}

