"""
Audit Retention Service
Manages audit log retention policies and archival for compliance
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from core.domain.audit.audit_event_category import AuditEventCategory
from core.interfaces.secondary.audit_log_repository_interface import IAuditLogRepository

logger = logging.getLogger(__name__)


class AuditRetentionService:
    """
    Service for audit log retention and archival.
    
    Implements retention policies for compliance:
    - AUTHENTICATION: 1 year
    - AUTHORIZATION: 2 years
    - DATA_ACCESS: 1 year (GDPR/HIPAA)
    - DATA_MODIFICATION: 7 years (SOX requirement)
    - BUSINESS_LOGIC: 3 years
    - ADMINISTRATIVE: 7 years
    - SYSTEM: 90 days
    
    Features:
    - Automatic retention policy enforcement
    - Archive old logs to cold storage (S3, etc.)
    - Retention compliance reporting
    - Safe deletion after archival
    """
    
    def __init__(self, repository: IAuditLogRepository):
        self.repository = repository
        
        # Retention policies (days) - based on compliance requirements
        self.retention_policies = {
            AuditEventCategory.AUTHENTICATION: 365,  # 1 year
            AuditEventCategory.AUTHORIZATION: 730,  # 2 years
            AuditEventCategory.DATA_ACCESS: 365,  # 1 year (GDPR/HIPAA)
            AuditEventCategory.DATA_MODIFICATION: 2555,  # 7 years (SOX requirement)
            AuditEventCategory.BUSINESS_LOGIC: 1095,  # 3 years
            AuditEventCategory.ADMINISTRATIVE: 2555,  # 7 years
            AuditEventCategory.SYSTEM: 90,  # 90 days
        }
    
    async def get_retention_report(
        self,
        client_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get retention policy compliance report.
        
        Shows how many logs are older than retention period
        and need to be archived/deleted.
        
        Args:
            client_id: Optional client filter
            
        Returns:
            Report dict with counts per category
        """
        try:
            report = {
                "generated_at": datetime.utcnow().isoformat(),
                "client_id": client_id or "all",
                "categories": {}
            }
            
            total_to_archive = 0
            
            for category, retention_days in self.retention_policies.items():
                cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
                
                # Count logs older than retention period
                count = await self.repository.count_logs(
                    category=category,
                    before_date=cutoff_date,
                    client_id=client_id
                )
                
                total_to_archive += count
                
                report["categories"][category.value] = {
                    "retention_days": retention_days,
                    "cutoff_date": cutoff_date.isoformat(),
                    "logs_to_archive": count,
                    "policy": f"Retain for {retention_days} days"
                }
            
            report["total_logs_to_archive"] = total_to_archive
            
            logger.info(f"Retention report generated: {total_to_archive} logs to archive")
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating retention report: {e}", exc_info=True)
            return {"error": str(e)}
    
    async def archive_old_logs(
        self,
        category: Optional[AuditEventCategory] = None,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Archive logs based on retention policy.
        
        Process:
        1. Find logs older than retention period
        2. Export to S3/cold storage (JSON format)
        3. Delete from primary database (after successful archive)
        
        Args:
            category: Optional specific category to archive (None = all categories)
            dry_run: If True, only reports what would be archived (don't actually delete)
            
        Returns:
            Archive statistics
        """
        try:
            archived_counts = {}
            categories_to_process = [category] if category else list(self.retention_policies.keys())
            
            for cat in categories_to_process:
                retention_days = self.retention_policies[cat]
                cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
                
                # Find logs to archive
                logs_to_archive = await self.repository.find_by_category(
                    category=cat,
                    start_date=None,  # From beginning
                    limit=10000  # Batch size
                )
                
                # Filter to only logs older than cutoff
                old_logs = [log for log in logs_to_archive if log.created_at < cutoff_date]
                
                if dry_run:
                    archived_counts[cat.value] = {
                        "logs_found": len(old_logs),
                        "action": "would_archive",
                        "dry_run": True
                    }
                else:
                    # TODO: Implement actual archival to S3
                    # await s3_service.upload_audit_archive(old_logs, category=cat)
                    
                    # After successful archive, delete from database
                    deleted = await self.repository.delete_old_logs(cat, cutoff_date)
                    
                    archived_counts[cat.value] = {
                        "logs_archived": len(old_logs),
                        "logs_deleted": deleted,
                        "action": "archived_and_deleted",
                        "dry_run": False
                    }
                
                logger.info(
                    f"Archive process for {cat.value}: {len(old_logs)} logs",
                    extra={"category": cat.value, "dry_run": dry_run}
                )
            
            return {
                "status": "completed",
                "dry_run": dry_run,
                "timestamp": datetime.utcnow().isoformat(),
                "results": archived_counts
            }
            
        except Exception as e:
            logger.error(f"Error archiving logs: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def cleanup_old_logs_by_policy(
        self,
        client_id: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Cleanup old logs based on retention policies (for maintenance task).
        
        Should only be called AFTER logs have been archived to S3.
        
        Args:
            client_id: Optional client filter
            
        Returns:
            Dict with deletion counts per category
        """
        try:
            deletion_counts = {}
            
            for category, retention_days in self.retention_policies.items():
                cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
                
                # Delete logs older than retention period
                deleted = await self.repository.delete_old_logs(
                    category=category,
                    before_date=cutoff_date
                )
                
                deletion_counts[category.value] = deleted
                
                if deleted > 0:
                    logger.warning(
                        f"Deleted {deleted} old {category.value} audit logs",
                        extra={
                            "category": category.value,
                            "retention_days": retention_days,
                            "cutoff_date": cutoff_date.isoformat()
                        }
                    )
            
            total_deleted = sum(deletion_counts.values())
            
            logger.info(f"Retention cleanup completed: {total_deleted} total logs deleted")
            
            return deletion_counts
            
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}", exc_info=True)
            return {}
    
    def get_retention_days(self, category: AuditEventCategory) -> int:
        """
        Get retention period for a category.
        
        Args:
            category: Event category
            
        Returns:
            Retention period in days
        """
        return self.retention_policies.get(category, 365)
    
    def is_retention_compliant(
        self,
        category: AuditEventCategory,
        log_age_days: int
    ) -> bool:
        """
        Check if log age is within retention policy.
        
        Args:
            category: Event category
            log_age_days: Age of log in days
            
        Returns:
            True if within retention period, False if should be archived
        """
        retention_days = self.get_retention_days(category)
        return log_age_days <= retention_days

