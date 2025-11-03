/**
 * Audit Service
 * 
 * Implements business logic for auditing
 */

import type { IAuditService } from "../../interfaces/primary/IAuditService";
import type { IAuditLogRepository } from "../../interfaces/secondary/IAuditLogRepository";
import type {
  AuditLog,
  AuditFilters,
  AuditStatistics,
  UserActivityTimeline,
  PaginationParams,
  AuditLogsResponse,
  AuditEventCategory
} from "../../domain/audit";

export class AuditService implements IAuditService {
  private readonly repository: IAuditLogRepository;

  constructor(repository: IAuditLogRepository) {
    this.repository = repository;
  }

  /**
   * Get user audit trail
   */
  async getUserAuditTrail(
    userId: string,
    filters?: AuditFilters,
    pagination?: PaginationParams
  ): Promise<AuditLogsResponse> {
    return this.repository.getUserAuditTrail(userId, filters, pagination);
  }

  /**
   * Get complete entity history
   */
  async getEntityAuditTrail(
    resourceType: string,
    resourceId: string,
    limit?: number
  ): Promise<AuditLog[]> {
    return this.repository.getEntityAuditTrail(resourceType, resourceId, limit);
  }

  /**
   * Get recent events
   */
  async getRecentEvents(
    category?: AuditEventCategory,
    limit?: number
  ): Promise<AuditLog[]> {
    return this.repository.getRecentEvents(category, limit);
  }

  /**
   * Search audit logs
   */
  async searchAuditLogs(
    query: string,
    filters?: AuditFilters,
    limit?: number
  ): Promise<AuditLog[]> {
    return this.repository.searchAuditLogs(query, filters, limit);
  }

  /**
   * Get audit statistics
   */
  async getStatistics(
    startDate: string,
    endDate: string
  ): Promise<AuditStatistics> {
    return this.repository.getStatistics(startDate, endDate);
  }

  /**
   * Get user activity timeline
   */
  async getUserActivityTimeline(
    userId: string,
    days?: number
  ): Promise<UserActivityTimeline[]> {
    return this.repository.getUserActivityTimeline(userId, days);
  }

  /**
   * Export user data (GDPR)
   */
  async exportUserData(userId: string): Promise<any> {
    return this.repository.exportUserData(userId);
  }
}

