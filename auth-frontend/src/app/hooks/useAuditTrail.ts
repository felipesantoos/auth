/**
 * Audit Trail Hook
 * 
 * Facilitates the use of audit data in components
 */

import { useState, useEffect } from "react";
import { useAudit } from "../contexts/AuditContext";
import {
  AuditFilters,
  AuditEventCategory,
  PaginationParams
} from "../../core/domain/audit";

interface UseAuditTrailOptions {
  userId?: string;
  entityType?: string;
  entityId?: string;
  category?: AuditEventCategory;
  filters?: AuditFilters;
  pagination?: PaginationParams;
  autoLoad?: boolean;
}

export const useAuditTrail = (options: UseAuditTrailOptions = {}) => {
  const {
    logs,
    loading,
    error,
    total,
    getUserAuditTrail,
    getEntityAuditTrail,
    getRecentEvents,
    clearLogs,
    clearError
  } = useAudit();

  const [localFilters, setLocalFilters] = useState<AuditFilters>(
    options.filters || {}
  );

  // Load data automatically if autoLoad = true
  useEffect(() => {
    if (options.autoLoad !== false) {
      loadData();
    }

    return () => {
      clearLogs();
    };
  }, [
    options.userId,
    options.entityType,
    options.entityId,
    options.category,
    JSON.stringify(localFilters),
    JSON.stringify(options.pagination)
  ]);

  const loadData = async () => {
    try {
      if (options.userId) {
        await getUserAuditTrail(
          options.userId,
          { ...localFilters, event_category: options.category },
          options.pagination
        );
      } else if (options.entityType && options.entityId) {
        await getEntityAuditTrail(
          options.entityType,
          options.entityId,
          options.pagination?.limit
        );
      } else {
        await getRecentEvents(options.category, options.pagination?.limit);
      }
    } catch (err) {
      console.error("Error loading audit data:", err);
    }
  };

  const refresh = () => {
    loadData();
  };

  const applyFilters = (newFilters: AuditFilters) => {
    setLocalFilters(newFilters);
  };

  const clearFilters = () => {
    setLocalFilters({});
  };

  return {
    logs,
    loading,
    error,
    total,
    filters: localFilters,
    refresh,
    applyFilters,
    clearFilters,
    clearError
  };
};

export default useAuditTrail;

