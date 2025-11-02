/**
 * Audit Context
 * 
 * Manages state and operations related to auditing
 */

import React, { createContext, useContext, useState, ReactNode } from "react";
import { IAuditService } from "../../core/interfaces/primary/IAuditService";
import { AuditService } from "../../core/services/audit/auditService";
import { auditLogRepository } from "../../infra/api/repositories/audit.repository";
import {
  AuditLog,
  AuditFilters,
  AuditStatistics,
  UserActivityTimeline,
  PaginationParams,
  AuditLogsResponse,
  AuditEventCategory
} from "../../core/domain/audit";

interface AuditContextData {
  // State
  logs: AuditLog[];
  loading: boolean;
  error: string | null;
  statistics: AuditStatistics | null;
  timeline: UserActivityTimeline[];
  total: number;
  
  // Operations
  getUserAuditTrail: (
    userId: string,
    filters?: AuditFilters,
    pagination?: PaginationParams
  ) => Promise<void>;
  getEntityAuditTrail: (
    resourceType: string,
    resourceId: string,
    limit?: number
  ) => Promise<void>;
  getRecentEvents: (
    category?: AuditEventCategory,
    limit?: number
  ) => Promise<void>;
  searchAuditLogs: (
    query: string,
    filters?: AuditFilters,
    limit?: number
  ) => Promise<void>;
  getStatistics: (
    startDate: string,
    endDate: string
  ) => Promise<void>;
  getUserActivityTimeline: (
    userId: string,
    days?: number
  ) => Promise<void>;
  exportUserData: (userId: string) => Promise<any>;
  clearLogs: () => void;
  clearError: () => void;
}

const AuditContext = createContext<AuditContextData | undefined>(undefined);

interface AuditProviderProps {
  children: ReactNode;
  service?: IAuditService;
}

export const AuditProvider: React.FC<AuditProviderProps> = ({
  children,
  service = new AuditService(auditLogRepository)
}) => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statistics, setStatistics] = useState<AuditStatistics | null>(null);
  const [timeline, setTimeline] = useState<UserActivityTimeline[]>([]);
  const [total, setTotal] = useState(0);

  const getUserAuditTrail = async (
    userId: string,
    filters?: AuditFilters,
    pagination?: PaginationParams
  ) => {
    setLoading(true);
    setError(null);
    
    try {
      const response: AuditLogsResponse = await service.getUserAuditTrail(
        userId,
        filters,
        pagination
      );
      setLogs(response.logs);
      setTotal(response.total);
    } catch (err: any) {
      setError(err.message || "Error fetching audit trail");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getEntityAuditTrail = async (
    resourceType: string,
    resourceId: string,
    limit?: number
  ) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await service.getEntityAuditTrail(resourceType, resourceId, limit);
      setLogs(data);
      setTotal(data.length);
    } catch (err: any) {
      setError(err.message || "Error fetching entity history");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getRecentEvents = async (
    category?: AuditEventCategory,
    limit?: number
  ) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await service.getRecentEvents(category, limit);
      setLogs(data);
      setTotal(data.length);
    } catch (err: any) {
      setError(err.message || "Error fetching recent events");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const searchAuditLogs = async (
    query: string,
    filters?: AuditFilters,
    limit?: number
  ) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await service.searchAuditLogs(query, filters, limit);
      setLogs(data);
      setTotal(data.length);
    } catch (err: any) {
      setError(err.message || "Error searching logs");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getStatistics = async (
    startDate: string,
    endDate: string
  ) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await service.getStatistics(startDate, endDate);
      setStatistics(data);
    } catch (err: any) {
      setError(err.message || "Error fetching statistics");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getUserActivityTimeline = async (
    userId: string,
    days?: number
  ) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await service.getUserActivityTimeline(userId, days);
      setTimeline(data);
    } catch (err: any) {
      setError(err.message || "Error fetching activity timeline");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const exportUserData = async (userId: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await service.exportUserData(userId);
      return data;
    } catch (err: any) {
      setError(err.message || "Error exporting user data");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const clearLogs = () => {
    setLogs([]);
    setTotal(0);
    setStatistics(null);
    setTimeline([]);
  };

  const clearError = () => {
    setError(null);
  };

  return (
    <AuditContext.Provider
      value={{
        logs,
        loading,
        error,
        statistics,
        timeline,
        total,
        getUserAuditTrail,
        getEntityAuditTrail,
        getRecentEvents,
        searchAuditLogs,
        getStatistics,
        getUserActivityTimeline,
        exportUserData,
        clearLogs,
        clearError
      }}
    >
      {children}
    </AuditContext.Provider>
  );
};

export const useAudit = (): AuditContextData => {
  const context = useContext(AuditContext);
  
  if (!context) {
    throw new Error("useAudit must be used within an AuditProvider");
  }
  
  return context;
};

