"""
Unit tests for MFA Service
Tests 2FA/MFA functionality including TOTP and backup codes
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import pyotp
from core.services.auth.mfa_service import MFAService
from core.domain.auth.backup_code import BackupCode
from core.exceptions import BusinessRuleException, ValidationException
from tests.factories import UserFactory, BackupCodeFactory


@pytest.fixture
def mock_repositories():
    """Create mock repositories"""
    user_repo = Mock()
    user_repo.save = AsyncMock()
    user_repo.find_by_id = AsyncMock()
    
    backup_repo = Mock()
    backup_repo.save = AsyncMock()
    backup_repo.find_by_user = AsyncMock()
    backup_repo.delete_by_user = AsyncMock()
    
    return user_repo, backup_repo


@pytest.fixture
def mock_settings():
    """Create mock settings"""
    settings_provider = Mock()
    settings = Mock()
    settings.mfa_issuer_name = "Test Auth System"
    settings.mfa_backup_codes_count = 10
    settings_provider.get_settings.return_value = settings
    return settings_provider


@pytest.fixture
def mfa_service(mock_repositories, mock_settings):
    """Create MFA service instance"""
    user_repo, backup_repo = mock_repositories
    return MFAService(user_repo, backup_repo, mock_settings)


@pytest.mark.unit
class TestMFASetup:
    """Test MFA setup process"""
    
    @pytest.mark.asyncio
    async def test_setup_mfa_generates_secret_and_qr(self, mfa_service, mock_repositories):
        """Test MFA setup generates TOTP secret and QR code"""
        user = UserFactory.create()
        user_repo, backup_repo = mock_repositories
        user_repo.find_by_id.return_value = user
        user_repo.save.return_value = user
        
        result = await mfa_service.setup_mfa(user.id, user.client_id)
        
        assert "secret" in result
        assert "qr_code" in result
        assert "backup_codes" in result
        assert len(result["secret"]) > 0
        assert result["qr_code"].startswith("data:image/png;base64,")
        assert len(result["backup_codes"]) == 10
    
    @pytest.mark.asyncio
    async def test_setup_mfa_generates_backup_codes(self, mfa_service, mock_repositories):
        """Test MFA setup generates backup codes"""
        user = UserFactory.create()
        user_repo, backup_repo = mock_repositories
        user_repo.find_by_id.return_value = user
        user_repo.save.return_value = user
        
        result = await mfa_service.setup_mfa(user.id, user.client_id)
        
        assert len(result["backup_codes"]) == 10
        assert all(len(code) == 8 for code in result["backup_codes"])
        # Backup codes should be saved
        assert backup_repo.save.call_count == 10
    
    @pytest.mark.asyncio
    async def test_setup_mfa_does_not_enable_immediately(self, mfa_service, mock_repositories):
        """Test MFA setup doesn't enable MFA immediately"""
        user = UserFactory.create(mfa_enabled=False)
        user_repo, backup_repo = mock_repositories
        user_repo.find_by_id.return_value = user
        user_repo.save.return_value = user
        
        await mfa_service.setup_mfa(user.id, user.client_id)
        
        # MFA should not be enabled yet (requires verification)
        assert user.mfa_enabled is False


@pytest.mark.unit
class TestMFAEnable:
    """Test MFA enable/disable"""
    
    @pytest.mark.asyncio
    async def test_enable_mfa_with_valid_totp(self, mfa_service, mock_repositories):
        """Test enabling MFA with valid TOTP code"""
        user = UserFactory.create(mfa_enabled=False)
        secret = pyotp.random_base32()
        user.mfa_secret = secret
        
        user_repo, backup_repo = mock_repositories
        user_repo.find_by_id.return_value = user
        user_repo.save.return_value = user
        
        # Generate valid TOTP code
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()
        
        result = await mfa_service.enable_mfa(user.id, user.client_id, valid_code)
        
        assert result.mfa_enabled is True
        assert user_repo.save.called
    
    @pytest.mark.asyncio
    async def test_enable_mfa_with_invalid_totp_fails(self, mfa_service, mock_repositories):
        """Test enabling MFA with invalid TOTP fails"""
        user = UserFactory.create(mfa_enabled=False)
        user.mfa_secret = pyotp.random_base32()
        
        user_repo, backup_repo = mock_repositories
        user_repo.find_by_id.return_value = user
        
        with pytest.raises(ValidationException, match="Invalid"):
            await mfa_service.enable_mfa(user.id, user.client_id, "000000")
    
    @pytest.mark.asyncio
    async def test_disable_mfa(self, mfa_service, mock_repositories):
        """Test disabling MFA"""
        user = UserFactory.create_with_mfa()
        
        user_repo, backup_repo = mock_repositories
        user_repo.find_by_id.return_value = user
        user_repo.save.return_value = user
        
        result = await mfa_service.disable_mfa(user.id, user.client_id)
        
        assert result.mfa_enabled is False
        assert result.mfa_secret is None
        # Backup codes should be deleted
        assert backup_repo.delete_by_user.called


@pytest.mark.unit
class TestMFAVerification:
    """Test MFA verification"""
    
    @pytest.mark.asyncio
    async def test_verify_totp_with_valid_code(self, mfa_service):
        """Test TOTP verification with valid code"""
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()
        
        result = mfa_service.verify_totp(secret, valid_code)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_totp_with_invalid_code(self, mfa_service):
        """Test TOTP verification with invalid code"""
        secret = pyotp.random_base32()
        
        result = mfa_service.verify_totp(secret, "000000")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_backup_code_success(self, mfa_service, mock_repositories):
        """Test backup code verification"""
        user = UserFactory.create_with_mfa()
        plain_code = "12345678"
        
        # Create backup code
        backup_code = BackupCodeFactory.create(
            user_id=user.id,
            client_id=user.client_id,
            code=plain_code,
            used=False
        )
        
        user_repo, backup_repo = mock_repositories
        backup_repo.find_by_user.return_value = [backup_code]
        backup_repo.save.return_value = backup_code
        
        with patch('bcrypt.checkpw', return_value=True):
            result = await mfa_service.verify_backup_code(
                user.id,
                user.client_id,
                plain_code
            )
        
        assert result is True
        # Code should be marked as used
        assert backup_repo.save.called
    
    @pytest.mark.asyncio
    async def test_verify_backup_code_already_used_fails(self, mfa_service, mock_repositories):
        """Test backup code that's already used fails"""
        user = UserFactory.create_with_mfa()
        
        # Create used backup code
        backup_code = BackupCodeFactory.create_used(
            user_id=user.id,
            client_id=user.client_id
        )
        
        user_repo, backup_repo = mock_repositories
        backup_repo.find_by_user.return_value = [backup_code]
        
        result = await mfa_service.verify_backup_code(
            user.id,
            user.client_id,
            "12345678"
        )
        
        assert result is False


@pytest.mark.unit
class TestBackupCodeRegeneration:
    """Test backup code regeneration"""
    
    @pytest.mark.asyncio
    async def test_regenerate_backup_codes(self, mfa_service, mock_repositories):
        """Test regenerating backup codes"""
        user = UserFactory.create_with_mfa()
        
        user_repo, backup_repo = mock_repositories
        user_repo.find_by_id.return_value = user
        
        new_codes = await mfa_service.regenerate_backup_codes(user.id, user.client_id)
        
        assert len(new_codes) == 10
        # Old codes should be deleted
        assert backup_repo.delete_by_user.called
        # New codes should be saved
        assert backup_repo.save.call_count == 10
    
    @pytest.mark.asyncio
    async def test_regenerate_backup_codes_without_mfa_enabled_fails(self, mfa_service, mock_repositories):
        """Test regenerating backup codes without MFA enabled fails"""
        user = UserFactory.create(mfa_enabled=False)
        
        user_repo, backup_repo = mock_repositories
        user_repo.find_by_id.return_value = user
        
        with pytest.raises(BusinessRuleException, match="MFA.*not enabled"):
            await mfa_service.regenerate_backup_codes(user.id, user.client_id)


@pytest.mark.unit
class TestTOTPGeneration:
    """Test TOTP secret and QR code generation"""
    
    def test_generate_totp_secret(self, mfa_service):
        """Test TOTP secret generation"""
        secret = mfa_service._generate_totp_secret()
        
        assert len(secret) == 32  # Base32 encoded
        assert secret.isalnum()
        assert secret.isupper()
    
    def test_generate_totp_uri(self, mfa_service):
        """Test TOTP URI generation"""
        secret = "JBSWY3DPEHPK3PXP"
        email = "user@example.com"
        
        uri = mfa_service._generate_totp_uri(secret, email)
        
        assert uri.startswith("otpauth://totp/")
        assert email in uri
        assert secret in uri
        assert "Test Auth System" in uri
    
    def test_generate_qr_code(self, mfa_service):
        """Test QR code generation"""
        uri = "otpauth://totp/Test:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Test"
        
        qr_code = mfa_service._generate_qr_code(uri)
        
        assert qr_code.startswith("data:image/png;base64,")
        assert len(qr_code) > 100  # Should be a substantial base64 string


@pytest.mark.unit
class TestBackupCodeGeneration:
    """Test backup code generation"""
    
    def test_generate_backup_code(self, mfa_service):
        """Test backup code generation"""
        code = mfa_service._generate_backup_code()
        
        assert len(code) == 8
        assert code.isdigit()
    
    def test_generate_unique_backup_codes(self, mfa_service):
        """Test backup codes are unique"""
        codes = [mfa_service._generate_backup_code() for _ in range(10)]
        
        # All codes should be unique
        assert len(codes) == len(set(codes))

