/**
 * Audit API Repository
 */

import { httpClient } from "../http-client";
import { IAuditLogRepository } from "../../../core/interfaces/secondary/IAuditLogRepository";
import {
  AuditLog,
  AuditFilters,
  AuditStatistics,
  UserActivityTimeline,
  PaginationParams,
  AuditLogsResponse,
  AuditEventCategory
} from "../../../core/domain/audit";
import {
  AuditLogDTO,
  AuditLogsResponseDTO,
  AuditStatisticsDTO,
  UserActivityTimelineDTO
} from "../dtos/audit.dto";
import { AuditMapper } from "../mappers/audit.mapper";

class AuditLogRepository implements IAuditLogRepository {
  private readonly baseUrl = "/audit";

  /**
   * Get user audit trail
   */
  async getUserAuditTrail(
    userId: string,
    filters?: AuditFilters,
    pagination?: PaginationParams
  ): Promise<AuditLogsResponse> {
    const params = new URLSearchParams();
    
    if (filters?.event_category) {
      params.append("category", filters.event_category);
    }
    
    if (filters?.event_types) {
      filters.event_types.forEach(type => {
        params.append("event_types", type);
      });
    }
    
    if (filters?.start_date) {
      params.append("start_date", filters.start_date);
    }
    
    if (filters?.end_date) {
      params.append("end_date", filters.end_date);
    }
    
    if (pagination?.limit) {
      params.append("limit", pagination.limit.toString());
    }
    
    if (pagination?.offset) {
      params.append("offset", pagination.offset.toString());
    }

    const response = await httpClient.get<AuditLogsResponseDTO>(
      `${this.baseUrl}/users/${userId}?${params.toString()}`
    );
    
    return AuditMapper.toDomainResponse(response.data);
  }

  /**
   * Get complete entity history
   */
  async getEntityAuditTrail(
    resourceType: string,
    resourceId: string,
    limit: number = 100
  ): Promise<AuditLog[]> {
    const response = await httpClient.get<AuditLogDTO[]>(
      `${this.baseUrl}/entities/${resourceType}/${resourceId}?limit=${limit}`
    );
    
    return AuditMapper.toDomainArray(response.data);
  }

  /**
   * Get recent events
   */
  async getRecentEvents(
    category?: AuditEventCategory,
    limit: number = 50
  ): Promise<AuditLog[]> {
    const params = new URLSearchParams();
    params.append("limit", limit.toString());
    
    if (category) {
      params.append("category", category);
    }

    const response = await httpClient.get<AuditLogDTO[]>(
      `${this.baseUrl}/recent?${params.toString()}`
    );
    
    return AuditMapper.toDomainArray(response.data);
  }

  /**
   * Search audit logs
   */
  async searchAuditLogs(
    query: string,
    filters?: AuditFilters,
    limit: number = 100
  ): Promise<AuditLog[]> {
    const params = new URLSearchParams();
    params.append("query", query);
    params.append("limit", limit.toString());
    
    if (filters?.user_id) {
      params.append("user_id", filters.user_id);
    }
    
    if (filters?.resource_type) {
      params.append("resource_type", filters.resource_type);
    }
    
    if (filters?.event_category) {
      params.append("event_category", filters.event_category);
    }
    
    if (filters?.tags) {
      filters.tags.forEach(tag => {
        params.append("tags", tag);
      });
    }
    
    if (filters?.success !== undefined) {
      params.append("success", filters.success.toString());
    }

    const response = await httpClient.get<AuditLogDTO[]>(
      `${this.baseUrl}/search?${params.toString()}`
    );
    
    return AuditMapper.toDomainArray(response.data);
  }

  /**
   * Get audit statistics
   */
  async getStatistics(
    startDate: string,
    endDate: string
  ): Promise<AuditStatistics> {
    const response = await httpClient.get<AuditStatisticsDTO>(
      `${this.baseUrl}/statistics?start_date=${startDate}&end_date=${endDate}`
    );
    
    return AuditMapper.toDomainStatistics(response.data);
  }

  /**
   * Get user activity timeline
   */
  async getUserActivityTimeline(
    userId: string,
    days: number = 30
  ): Promise<UserActivityTimeline[]> {
    const response = await httpClient.get<UserActivityTimelineDTO[]>(
      `${this.baseUrl}/users/${userId}/timeline?days=${days}`
    );
    
    return AuditMapper.toDomainTimelineArray(response.data);
  }

  /**
   * Export user data (GDPR)
   */
  async exportUserData(userId: string): Promise<any> {
    const response = await httpClient.get(
      `${this.baseUrl}/users/${userId}/export`
    );
    
    return response.data;
  }
}

export const auditLogRepository = new AuditLogRepository();

