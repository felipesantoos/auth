"""
Unit tests for AuditEventCategory domain model
Tests domain logic without external dependencies
"""
import pytest
from core.domain.audit.audit_event_category import AuditEventCategory


@pytest.mark.unit
class TestAuditEventCategoryRetention:
    """Test retention period methods"""
    
    def test_authentication_retention_period(self):
        """Test authentication category has 365 days retention"""
        category = AuditEventCategory.AUTHENTICATION
        assert category.get_retention_days() == 365
    
    def test_authorization_retention_period(self):
        """Test authorization category has 730 days retention"""
        category = AuditEventCategory.AUTHORIZATION
        assert category.get_retention_days() == 730
    
    def test_data_access_retention_period(self):
        """Test data access category has 365 days retention"""
        category = AuditEventCategory.DATA_ACCESS
        assert category.get_retention_days() == 365
    
    def test_data_modification_retention_period(self):
        """Test data modification category has 2555 days retention (SOX)"""
        category = AuditEventCategory.DATA_MODIFICATION
        assert category.get_retention_days() == 2555
    
    def test_business_logic_retention_period(self):
        """Test business logic category has 1095 days retention"""
        category = AuditEventCategory.BUSINESS_LOGIC
        assert category.get_retention_days() == 1095
    
    def test_administrative_retention_period(self):
        """Test administrative category has 2555 days retention"""
        category = AuditEventCategory.ADMINISTRATIVE
        assert category.get_retention_days() == 2555
    
    def test_system_retention_period(self):
        """Test system category has 90 days retention"""
        category = AuditEventCategory.SYSTEM
        assert category.get_retention_days() == 90


@pytest.mark.unit
class TestAuditEventCategoryCompliance:
    """Test compliance-related methods"""
    
    def test_data_access_is_compliance_critical(self):
        """Test data access is compliance critical"""
        category = AuditEventCategory.DATA_ACCESS
        assert category.is_compliance_critical() is True
    
    def test_data_modification_is_compliance_critical(self):
        """Test data modification is compliance critical"""
        category = AuditEventCategory.DATA_MODIFICATION
        assert category.is_compliance_critical() is True
    
    def test_authorization_is_compliance_critical(self):
        """Test authorization is compliance critical"""
        category = AuditEventCategory.AUTHORIZATION
        assert category.is_compliance_critical() is True
    
    def test_administrative_is_compliance_critical(self):
        """Test administrative is compliance critical"""
        category = AuditEventCategory.ADMINISTRATIVE
        assert category.is_compliance_critical() is True
    
    def test_authentication_is_not_compliance_critical(self):
        """Test authentication is not marked as compliance critical"""
        category = AuditEventCategory.AUTHENTICATION
        assert category.is_compliance_critical() is False
    
    def test_business_logic_is_not_compliance_critical(self):
        """Test business logic is not compliance critical"""
        category = AuditEventCategory.BUSINESS_LOGIC
        assert category.is_compliance_critical() is False
    
    def test_system_is_not_compliance_critical(self):
        """Test system is not compliance critical"""
        category = AuditEventCategory.SYSTEM
        assert category.is_compliance_critical() is False


@pytest.mark.unit
class TestAuditEventCategoryDisplay:
    """Test display methods"""
    
    def test_get_display_name_for_authentication(self):
        """Test display name for authentication category"""
        category = AuditEventCategory.AUTHENTICATION
        assert category.get_display_name() == "Authentication & Identity"
    
    def test_get_display_name_for_authorization(self):
        """Test display name for authorization category"""
        category = AuditEventCategory.AUTHORIZATION
        assert category.get_display_name() == "Authorization & Access Control"
    
    def test_get_display_name_for_data_access(self):
        """Test display name for data access category"""
        category = AuditEventCategory.DATA_ACCESS
        assert category.get_display_name() == "Data Access (Read)"
    
    def test_get_display_name_for_data_modification(self):
        """Test display name for data modification category"""
        category = AuditEventCategory.DATA_MODIFICATION
        assert category.get_display_name() == "Data Modification (Write)"
    
    def test_get_display_name_for_business_logic(self):
        """Test display name for business logic category"""
        category = AuditEventCategory.BUSINESS_LOGIC
        assert category.get_display_name() == "Business Logic & Workflows"
    
    def test_get_display_name_for_administrative(self):
        """Test display name for administrative category"""
        category = AuditEventCategory.ADMINISTRATIVE
        assert category.get_display_name() == "Administrative Actions"
    
    def test_get_display_name_for_system(self):
        """Test display name for system category"""
        category = AuditEventCategory.SYSTEM
        assert category.get_display_name() == "System Events"
    
    def test_get_icon_for_authentication(self):
        """Test icon for authentication category"""
        category = AuditEventCategory.AUTHENTICATION
        assert category.get_icon() == "🔑"
    
    def test_get_icon_for_authorization(self):
        """Test icon for authorization category"""
        category = AuditEventCategory.AUTHORIZATION
        assert category.get_icon() == "🛡️"
    
    def test_get_icon_for_data_access(self):
        """Test icon for data access category"""
        category = AuditEventCategory.DATA_ACCESS
        assert category.get_icon() == "👁️"
    
    def test_get_icon_for_data_modification(self):
        """Test icon for data modification category"""
        category = AuditEventCategory.DATA_MODIFICATION
        assert category.get_icon() == "✏️"
    
    def test_get_icon_for_business_logic(self):
        """Test icon for business logic category"""
        category = AuditEventCategory.BUSINESS_LOGIC
        assert category.get_icon() == "⚙️"
    
    def test_get_icon_for_administrative(self):
        """Test icon for administrative category"""
        category = AuditEventCategory.ADMINISTRATIVE
        assert category.get_icon() == "⚡"
    
    def test_get_icon_for_system(self):
        """Test icon for system category"""
        category = AuditEventCategory.SYSTEM
        assert category.get_icon() == "🖥️"


@pytest.mark.unit
class TestAuditEventCategoryValues:
    """Test enum values"""
    
    def test_all_categories_have_string_values(self):
        """Test all categories have proper string values"""
        for category in AuditEventCategory:
            assert isinstance(category.value, str)
            assert len(category.value) > 0
    
    def test_category_values_are_unique(self):
        """Test all category values are unique"""
        values = [category.value for category in AuditEventCategory]
        assert len(values) == len(set(values))

