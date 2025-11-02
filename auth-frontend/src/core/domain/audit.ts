/**
 * Audit Domain Models
 * 
 * Defines types and interfaces for the audit system
 */

/**
 * High-level event categories
 */
export const AuditEventCategory = {
  AUTHENTICATION: "authentication",
  AUTHORIZATION: "authorization",
  DATA_ACCESS: "data_access",
  DATA_MODIFICATION: "data_modification",
  BUSINESS_LOGIC: "business_logic",
  ADMINISTRATIVE: "administrative",
  SYSTEM: "system"
} as const;

export type AuditEventCategory = typeof AuditEventCategory[keyof typeof AuditEventCategory];

/**
 * Detailed audit event types
 */
export const AuditEventType = {
  // ===== Authentication =====
  USER_REGISTERED: "user.registered",
  USER_LOGIN: "user.login",
  USER_LOGOUT: "user.logout",
  USER_LOGIN_FAILED: "user.login.failed",
  PASSWORD_CHANGED: "user.password.changed",
  PASSWORD_RESET: "user.password.reset",
  EMAIL_VERIFIED: "user.email.verified",
  MFA_ENABLED: "user.mfa.enabled",
  MFA_DISABLED: "user.mfa.disabled",
  
  // ===== Authorization =====
  ROLE_ASSIGNED: "role.assigned",
  ROLE_REVOKED: "role.revoked",
  PERMISSION_GRANTED: "permission.granted",
  PERMISSION_REVOKED: "permission.revoked",
  ACCESS_DENIED: "access.denied",
  
  // ===== Data Access =====
  ENTITY_VIEWED: "entity.viewed",
  REPORT_VIEWED: "report.viewed",
  FILE_DOWNLOADED: "file.downloaded",
  DATA_EXPORTED: "data.exported",
  SENSITIVE_DATA_ACCESSED: "sensitive_data.accessed",
  
  // ===== Data Modification =====
  ENTITY_CREATED: "entity.created",
  ENTITY_UPDATED: "entity.updated",
  ENTITY_DELETED: "entity.deleted",
  ENTITY_RESTORED: "entity.restored",
  BULK_UPDATE: "entity.bulk_updated",
  BULK_DELETE: "entity.bulk_deleted",
  
  // ===== Business Logic =====
  WORKFLOW_STARTED: "workflow.started",
  WORKFLOW_COMPLETED: "workflow.completed",
  APPROVAL_REQUESTED: "approval.requested",
  APPROVAL_GRANTED: "approval.granted",
  APPROVAL_REJECTED: "approval.rejected",
  TASK_CREATED: "task.created",
  TASK_COMPLETED: "task.completed",
  DOCUMENT_PUBLISHED: "document.published",
  DOCUMENT_ARCHIVED: "document.archived",
  NOTIFICATION_SENT: "notification.sent",
  
  // ===== Administrative =====
  USER_ACTIVATED: "admin.user.activated",
  USER_DEACTIVATED: "admin.user.deactivated",
  USER_DELETED: "admin.user.deleted",
  SETTINGS_CHANGED: "admin.settings.changed",
  FEATURE_ENABLED: "admin.feature.enabled",
  FEATURE_DISABLED: "admin.feature.disabled",
  MAINTENANCE_MODE_ENABLED: "admin.maintenance.enabled",
  MAINTENANCE_MODE_DISABLED: "admin.maintenance.disabled",
  
  // ===== System =====
  DATABASE_BACKUP: "system.database.backup",
  DATABASE_RESTORE: "system.database.restore",
  MIGRATION_EXECUTED: "system.migration.executed",
  CACHE_CLEARED: "system.cache.cleared",
  ERROR_OCCURRED: "system.error"
} as const;

export type AuditEventType = typeof AuditEventType[keyof typeof AuditEventType];

/**
 * Change in an entity field
 */
export interface EntityChange {
  field: string;
  old_value: any;
  new_value: any;
  field_type: string;
  change_type: "added" | "modified" | "removed";
}

/**
 * Complete audit log
 */
export interface AuditLog {
  // Identification
  id: string;
  event_id: string;
  
  // Event details
  event_type: AuditEventType;
  event_category: AuditEventCategory;
  action: string;
  description?: string;
  
  // Actor (who)
  user_id?: string;
  username?: string;
  user_email?: string;
  impersonated_by?: string;
  
  // Resource (what)
  resource_type?: string;
  resource_id?: string;
  resource_name?: string;
  
  // Context (where, when, how)
  ip_address?: string;
  user_agent?: string;
  location?: string;
  request_id?: string;
  session_id?: string;
  
  // Changes (before/after)
  changes?: EntityChange[];
  old_values?: Record<string, any>;
  new_values?: Record<string, any>;
  
  // Additional context
  metadata?: Record<string, any>;
  tags?: string[];
  
  // Status
  success: boolean;
  error_message?: string;
  
  // Timestamps
  created_at: string;
}

/**
 * Filters for audit queries
 */
export interface AuditFilters {
  user_id?: string;
  username?: string;
  resource_type?: string;
  resource_id?: string;
  event_category?: AuditEventCategory;
  event_types?: AuditEventType[];
  start_date?: string;
  end_date?: string;
  tags?: string[];
  success?: boolean;
  search_query?: string;
}

/**
 * Audit statistics
 */
export interface AuditStatistics {
  total_events: number;
  events_by_category: Record<string, number>;
  top_users: Array<{
    username: string;
    count: number;
  }>;
  failed_events: number;
  success_rate: number;
}

/**
 * User activity timeline
 */
export interface UserActivityTimeline {
  date: string;
  count: number;
}

/**
 * Pagination parameters
 */
export interface PaginationParams {
  limit?: number;
  offset?: number;
}

/**
 * Paginated audit response
 */
export interface AuditLogsResponse {
  logs: AuditLog[];
  total: number;
  limit: number;
  offset: number;
}

