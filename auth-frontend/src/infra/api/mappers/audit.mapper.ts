/**
 * Mapper for audit DTOs and Domain Models
 */

import type {
  AuditLog,
  AuditFilters,
  AuditStatistics,
  UserActivityTimeline,
  AuditLogsResponse,
  AuditEventType,
  AuditEventCategory,
  EntityChange
} from "../../../core/domain/audit";
import type {
  AuditLogDTO,
  AuditFiltersDTO,
  AuditStatisticsDTO,
  UserActivityTimelineDTO,
  AuditLogsResponseDTO,
  EntityChangeDTO
} from "../dtos/audit.dto";

export class AuditMapper {
  /**
   * Convert EntityChangeDTO to EntityChange
   */
  static toDomainEntityChange(dto: EntityChangeDTO): EntityChange {
    return {
      field: dto.field,
      old_value: dto.old_value,
      new_value: dto.new_value,
      field_type: dto.field_type,
      change_type: dto.change_type
    };
  }

  /**
   * Convert AuditLogDTO to AuditLog
   */
  static toDomain(dto: AuditLogDTO): AuditLog {
    return {
      id: dto.id,
      event_id: dto.event_id,
      event_type: dto.event_type as AuditEventType,
      event_category: dto.event_category as AuditEventCategory,
      action: dto.action,
      description: dto.description,
      user_id: dto.user_id,
      username: dto.username,
      user_email: dto.user_email,
      impersonated_by: dto.impersonated_by,
      resource_type: dto.resource_type,
      resource_id: dto.resource_id,
      resource_name: dto.resource_name,
      ip_address: dto.ip_address,
      user_agent: dto.user_agent,
      location: dto.location,
      request_id: dto.request_id,
      session_id: dto.session_id,
      changes: dto.changes?.map(this.toDomainEntityChange),
      old_values: dto.old_values,
      new_values: dto.new_values,
      metadata: dto.metadata,
      tags: dto.tags,
      success: dto.success,
      error_message: dto.error_message,
      created_at: dto.created_at
    };
  }

  /**
   * Convert array of AuditLogDTO to array of AuditLog
   */
  static toDomainArray(dtos: AuditLogDTO[]): AuditLog[] {
    return dtos.map(dto => this.toDomain(dto));
  }

  /**
   * Convert AuditFilters to AuditFiltersDTO
   */
  static toDTO(filters: AuditFilters): AuditFiltersDTO {
    return {
      user_id: filters.user_id,
      username: filters.username,
      resource_type: filters.resource_type,
      resource_id: filters.resource_id,
      event_category: filters.event_category,
      event_types: filters.event_types,
      start_date: filters.start_date,
      end_date: filters.end_date,
      tags: filters.tags,
      success: filters.success,
      search_query: filters.search_query
    };
  }

  /**
   * Convert AuditStatisticsDTO to AuditStatistics
   */
  static toDomainStatistics(dto: AuditStatisticsDTO): AuditStatistics {
    return {
      total_events: dto.total_events,
      events_by_category: dto.events_by_category,
      top_users: dto.top_users,
      failed_events: dto.failed_events,
      success_rate: dto.success_rate
    };
  }

  /**
   * Convert UserActivityTimelineDTO to UserActivityTimeline
   */
  static toDomainTimeline(dto: UserActivityTimelineDTO): UserActivityTimeline {
    return {
      date: dto.date,
      count: dto.count
    };
  }

  /**
   * Convert array of UserActivityTimelineDTO
   */
  static toDomainTimelineArray(dtos: UserActivityTimelineDTO[]): UserActivityTimeline[] {
    return dtos.map(dto => this.toDomainTimeline(dto));
  }

  /**
   * Convert AuditLogsResponseDTO to AuditLogsResponse
   */
  static toDomainResponse(dto: AuditLogsResponseDTO): AuditLogsResponse {
    return {
      logs: this.toDomainArray(dto.logs),
      total: dto.total,
      limit: dto.limit,
      offset: dto.offset
    };
  }
}

