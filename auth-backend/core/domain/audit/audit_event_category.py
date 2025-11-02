"""
Audit Event Categories
High-level categorization of audit events for compliance and reporting
"""
from enum import Enum


class AuditEventCategory(str, Enum):
    """
    High-level audit event categories.
    
    Used for:
    - Compliance reporting (group events by category)
    - Retention policies (different retention per category)
    - Analytics dashboards
    - Filtering and search
    """
    
    # Authentication & Identity
    AUTHENTICATION = "authentication"
    """Login, logout, password changes, email verification, MFA"""
    
    # Authorization & Access Control
    AUTHORIZATION = "authorization"
    """Role changes, permission grants/revokes, access denied"""
    
    # Data Access (Read Operations)
    DATA_ACCESS = "data_access"
    """Views, downloads, exports - critical for GDPR/HIPAA compliance"""
    
    # Data Modification (Write Operations)
    DATA_MODIFICATION = "data_modification"
    """Creates, updates, deletes - critical for SOX compliance"""
    
    # Business Logic & Workflows
    BUSINESS_LOGIC = "business_logic"
    """Workflows, approvals, tasks, notifications, document publishing"""
    
    # Administrative Actions
    ADMINISTRATIVE = "administrative"
    """User management, settings, feature toggles, maintenance mode"""
    
    # System Events
    SYSTEM = "system"
    """Backups, migrations, cache operations, errors"""
    
    def get_retention_days(self) -> int:
        """
        Get retention period for this category (compliance requirements).
        
        Returns:
            Number of days to retain audit logs
        """
        retention_map = {
            self.AUTHENTICATION: 365,  # 1 year
            self.AUTHORIZATION: 730,  # 2 years
            self.DATA_ACCESS: 365,  # 1 year (GDPR/HIPAA)
            self.DATA_MODIFICATION: 2555,  # 7 years (SOX requirement)
            self.BUSINESS_LOGIC: 1095,  # 3 years
            self.ADMINISTRATIVE: 2555,  # 7 years
            self.SYSTEM: 90,  # 90 days
        }
        return retention_map.get(self, 365)
    
    def is_compliance_critical(self) -> bool:
        """Check if this category has compliance requirements"""
        return self in [
            self.DATA_ACCESS,
            self.DATA_MODIFICATION,
            self.AUTHORIZATION,
            self.ADMINISTRATIVE
        ]
    
    def get_display_name(self) -> str:
        """Get human-readable display name"""
        display_names = {
            self.AUTHENTICATION: "Authentication & Identity",
            self.AUTHORIZATION: "Authorization & Access Control",
            self.DATA_ACCESS: "Data Access (Read)",
            self.DATA_MODIFICATION: "Data Modification (Write)",
            self.BUSINESS_LOGIC: "Business Logic & Workflows",
            self.ADMINISTRATIVE: "Administrative Actions",
            self.SYSTEM: "System Events",
        }
        return display_names.get(self, self.value.title())
    
    def get_icon(self) -> str:
        """Get emoji icon for UI display"""
        icons = {
            self.AUTHENTICATION: "🔑",
            self.AUTHORIZATION: "🛡️",
            self.DATA_ACCESS: "👁️",
            self.DATA_MODIFICATION: "✏️",
            self.BUSINESS_LOGIC: "⚙️",
            self.ADMINISTRATIVE: "⚡",
            self.SYSTEM: "🖥️",
        }
        return icons.get(self, "📋")

