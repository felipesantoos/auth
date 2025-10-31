"""
Auth Mapper
Converts between DTOs and Domain models
"""
from core.domain.auth.app_user import AppUser
from app.api.dtos.response.auth_response import UserResponse, TokenResponse
from config.settings import settings


class AuthMapper:
    """Converts between DTOs and Domain for authentication"""
    
    @staticmethod
    def to_user_response(user: AppUser) -> UserResponse:
        """Domain User → Response DTO"""
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            name=user.name,
            role=user.role.value,
            active=user.active,
            client_id=user.client_id,  # Multi-tenant
            created_at=user.created_at,
        )
    
    @staticmethod
    def to_token_response(
        access_token: str,
        refresh_token: str,
        user: AppUser
    ) -> TokenResponse:
        """Create token response with user data"""
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=AuthMapper.to_user_response(user),
        )

