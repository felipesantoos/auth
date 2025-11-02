/**
 * Audit Log Repository Interface
 * 
 * Defines contracts for audit data access
 */

import {
  AuditLog,
  AuditFilters,
  AuditStatistics,
  UserActivityTimeline,
  PaginationParams,
  AuditLogsResponse,
  AuditEventCategory
} from "../../domain/audit";

export interface IAuditLogRepository {
  /**
   * Get user audit trail
   */
  getUserAuditTrail(
    userId: string,
    filters?: AuditFilters,
    pagination?: PaginationParams
  ): Promise<AuditLogsResponse>;

  /**
   * Get complete entity history
   */
  getEntityAuditTrail(
    resourceType: string,
    resourceId: string,
    limit?: number
  ): Promise<AuditLog[]>;

  /**
   * Get recent events
   */
  getRecentEvents(
    category?: AuditEventCategory,
    limit?: number
  ): Promise<AuditLog[]>;

  /**
   * Search audit logs
   */
  searchAuditLogs(
    query: string,
    filters?: AuditFilters,
    limit?: number
  ): Promise<AuditLog[]>;

  /**
   * Get audit statistics
   */
  getStatistics(
    startDate: string,
    endDate: string
  ): Promise<AuditStatistics>;

  /**
   * Get user activity timeline
   */
  getUserActivityTimeline(
    userId: string,
    days?: number
  ): Promise<UserActivityTimeline[]>;

  /**
   * Export user data (GDPR)
   */
  exportUserData(userId: string): Promise<any>;
}

