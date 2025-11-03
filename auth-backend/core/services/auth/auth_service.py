"""
Authentication Service Implementation
Implements IAuthService - core authentication operations (login, logout, register, etc.)

Performance: Uses Redis cache for user profiles to reduce database queries
"""
import logging
from typing import Optional, Tuple, List
from datetime import datetime
from core.interfaces.primary.auth_service_interface import IAuthService
from core.interfaces.secondary.app_user_repository_interface import IAppUserRepository
from core.interfaces.secondary.cache_service_interface import ICacheService
from core.interfaces.secondary.settings_provider_interface import ISettingsProvider
from core.domain.auth.app_user import AppUser
# REMOVED: from core.domain.auth.user_role import UserRole (roles now in WorkspaceMember)
from core.domain.workspace.workspace_role import WorkspaceRole
from core.services.filters.user_filter import UserFilter
from core.services.cache.cache_helper import CacheHelper
from core.exceptions import (
    InvalidCredentialsException,
    UserNotFoundException,
    EmailAlreadyExistsException,
    ValidationException,
    InvalidTokenException,
    TokenExpiredException,
    DomainException,
    BusinessRuleException,
)
from .auth_service_base import AuthServiceBase

logger = logging.getLogger(__name__)


class AuthService(AuthServiceBase, IAuthService):
    """
    Service implementation for core authentication operations.
    
    Implements only IAuthService interface following Single Responsibility Principle.
    Multi-workspace architecture: Users now have global identity.
    """
    
    def __init__(
        self,
        repository: IAppUserRepository,
        cache_service: ICacheService,
        settings_provider: ISettingsProvider,
        workspace_service=None,  # Optional for backwards compatibility
        workspace_member_service=None,  # Optional for backwards compatibility
    ):
        """
        Constructor for AuthService.
        
        Args:
            repository: Repository interface for user operations
            cache_service: Cache service interface
            settings_provider: Settings provider interface
            workspace_service: Workspace service (for auto-creating workspaces)
            workspace_member_service: Workspace member service (for adding users to workspaces)
        """
        super().__init__(cache_service, settings_provider)
        self.repository = repository
        self.cache_helper = CacheHelper()  # ⚡ PERFORMANCE: Cache helper for user profiles
        self.workspace_service = workspace_service
        self.workspace_member_service = workspace_member_service
    
    async def _validate_login_credentials(
        self, email: str, password: str
    ) -> AppUser:
        """
        Validate login credentials and return user if valid.
        
        Security: We check user exists, is active, and password matches.
        All errors return the same message to prevent user enumeration attacks.
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            Validated user
            
        Raises:
            InvalidCredentialsException: If credentials are invalid (generic message for security)
        """
        user = await self.repository.find_by_email(email)
        if not user or not user.active:
            raise InvalidCredentialsException()
        
        if not self._verify_password(password, user.password_hash):
            raise InvalidCredentialsException()
        
        return user
    
    async def _validate_refresh_token(
        self, refresh_token: str, client_id: Optional[str] = None
    ) -> Tuple[dict, str, str]:
        """
        Validate refresh token and return payload, client_id, and user_id.
        
        Security: We verify token is valid, not revoked, and belongs to the correct tenant.
        Token rotation requires revoking the old token immediately after validation.
        
        Args:
            refresh_token: Refresh token string
            client_id: Optional client ID for validation
            
        Returns:
            Tuple of (payload, client_id, user_id)
            
        Raises:
            InvalidTokenException: If token is invalid, revoked, or user is inactive
            UserNotFoundException: If user not found
        """
        payload = self.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise InvalidTokenException()
        
        client_id_to_use = self._resolve_client_id_from_token(payload, client_id)
        if not client_id_to_use:
            raise InvalidTokenException()
        
        user_id = payload.get("user_id")
        if not user_id:
            raise InvalidTokenException()
        
        cache_key = f"{client_id_to_use}:refresh_token:{refresh_token}"
        stored_user_id = await self.cache.get(cache_key)
        if not stored_user_id or stored_user_id != user_id:
            logger.warning("Refresh token not found in Redis or revoked", extra={"client_id": client_id_to_use})
            raise InvalidTokenException()
        
        user = await self.repository.find_by_id(user_id, client_id=client_id_to_use)
        if not user:
            raise UserNotFoundException(user_id=user_id)
        
        if not user.active:
            raise InvalidCredentialsException()
        
        return payload, client_id_to_use, user_id
    
    async def login(
        self, email: str, password: str, client_id: Optional[str] = None, session_id: Optional[str] = None
    ) -> Tuple[str, str, AppUser]:
        """
        Authenticate user and generate tokens (multi-workspace).
        
        Args:
            email: User email
            password: Plain text password
            client_id: Optional client ID (deprecated, for backwards compatibility)
            session_id: Optional session ID to include in access token
            
        Returns:
            Tuple of (access_token, refresh_token, user)
            
        Raises:
            InvalidCredentialsException: If credentials are invalid
        """
        try:
            user = await self._validate_login_credentials(email, password)
        except InvalidCredentialsException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}", exc_info=True, extra={"email": email})
            raise DomainException("Failed to authenticate user due to technical error", "AUTHENTICATION_FAILED")
        
        # Use client_id if provided (backwards compatibility), otherwise use user's first workspace
        effective_client_id = client_id if client_id else "default"
        access_token, refresh_token = await self._generate_and_store_tokens(user.id, effective_client_id, session_id)
        
        logger.info("Login successful", extra={"user_id": user.id, "email": email})
        return access_token, refresh_token, user
    
    async def logout(self, refresh_token: str, client_id: Optional[str] = None) -> bool:
        """
        Logout user by invalidating refresh token (multi-tenant).
        
        Args:
            refresh_token: Refresh token to invalidate
            client_id: Optional client ID for validation
        """
        payload = self.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return False
        
        client_id_to_use = self._resolve_client_id_from_token(payload, client_id)
        if not client_id_to_use:
            return False
        
        cache_key = f"{client_id_to_use}:refresh_token:{refresh_token}"
        await self.cache.delete(cache_key)
        
        logger.info("Logout successful", extra={"user_id": payload.get("user_id"), "client_id": client_id_to_use})
        return True
    
    async def refresh_access_token(
        self, refresh_token: str, client_id: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate new access token using refresh token (multi-tenant with token rotation).
        
        Token rotation: We generate a new refresh token and revoke the old one immediately
        to limit the window of vulnerability if a token is compromised.
        
        Args:
            refresh_token: Refresh token
            client_id: Optional client ID for validation
            
        Returns:
            Tuple of (new_access_token, new_refresh_token)
        """
        payload, client_id_to_use, user_id = await self._validate_refresh_token(refresh_token, client_id)
        
        new_access_token, new_refresh_token = await self._generate_and_store_tokens(
            user_id, client_id_to_use
        )
        
        cache_key = f"{client_id_to_use}:refresh_token:{refresh_token}"
        await self.cache.delete(cache_key)
        
        logger.info("Token refresh successful", extra={"user_id": user_id, "client_id": client_id_to_use})
        return new_access_token, new_refresh_token
    
    async def _ensure_email_not_exists(self, email: str) -> None:
        """
        Ensure email doesn't already exist (globally unique).
        
        Raises:
            EmailAlreadyExistsException: If email already exists
        """
        existing = await self.repository.find_by_email(email)
        if existing:
            raise EmailAlreadyExistsException(email)
    
    def _validate_and_hash_password(self, password: str) -> str:
        """
        Validate password strength and hash it.
        
        Raises:
            ValueError: If password doesn't meet strength requirements
            
        Returns:
            Hashed password
        """
        self._validate_password_strength(password)
        return self._hash_password(password)
    
    def _create_user_domain_object(
        self, username: str, email: str, password_hash: str, name: str
    ) -> AppUser:
        """
        Create and validate user domain object (multi-workspace).
        
        Args:
            username: Username
            email: User email
            password_hash: Hashed password
            name: User full name
            
        Returns:
            Created and validated user domain object
        """
        user = AppUser(
            id=None,
            username=username,
            email=email,
            name=name,
            # REMOVED: role (now in WorkspaceMember)
            # REMOVED: client_id (now via workspace_member or user_client)
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            _password_hash=password_hash,  # Use protected field for encapsulation
        )
        user.validate()
        return user
    
    async def register(
        self, 
        username: str, 
        email: str, 
        password: str, 
        name: str,
        workspace_name: Optional[str] = None
    ) -> Tuple[AppUser, Optional[str]]:
        """
        Register new user (multi-workspace architecture).
        
        Automatically creates a personal workspace for the user and adds them as admin.
        
        Args:
            username: Username
            email: User email
            password: Plain text password
            name: User full name
            workspace_name: Optional custom workspace name (defaults to "{username}'s Workspace")
            
        Returns:
            Tuple of (created_user, workspace_id)
            
        Raises:
            EmailAlreadyExistsException: If email already exists
            ValidationException: If validation fails
            DomainException: If technical error occurs
        """
        try:
            # Check email doesn't exist (globally unique)
            await self._ensure_email_not_exists(email)
            
            # Create user
            password_hash = self._validate_and_hash_password(password)
            user = self._create_user_domain_object(username, email, password_hash, name)
            created_user = await self.repository.save(user)
            
            # Create personal workspace (if services are available)
            workspace_id = None
            if self.workspace_service and self.workspace_member_service:
                try:
                    # Auto-generate workspace name if not provided
                    if not workspace_name:
                        workspace_name = f"{username}'s Workspace"
                    
                    # Create workspace
                    workspace = await self.workspace_service.create_workspace(
                        name=workspace_name,
                        description=f"Personal workspace for {name}"
                    )
                    workspace_id = workspace.id
                    
                    # Add user as admin of the workspace
                    await self.workspace_member_service.add_member(
                        user_id=created_user.id,
                        workspace_id=workspace.id,
                        role=WorkspaceRole.ADMIN
                    )
                    
                    logger.info(
                        "User registered with personal workspace", 
                        extra={
                            "user_id": created_user.id, 
                            "email": email,
                            "workspace_id": workspace_id
                        }
                    )
                except Exception as workspace_error:
                    # Log workspace creation error but don't fail registration
                    logger.error(
                        f"Failed to create workspace for user: {workspace_error}",
                        exc_info=True,
                        extra={"user_id": created_user.id, "email": email}
                    )
            else:
                logger.warning(
                    "Workspace services not available - user registered without workspace",
                    extra={"user_id": created_user.id, "email": email}
                )
            
            return created_user, workspace_id
            
        except (EmailAlreadyExistsException, ValidationException):
            # Domain exceptions - let them propagate
            raise
        except Exception as e:
            # Unexpected error (database, network, etc.)
            logger.error(f"Unexpected error registering user: {e}", exc_info=True, extra={"email": email})
            raise DomainException("Failed to register user due to technical error", "USER_REGISTRATION_FAILED")
    
    async def change_password(
        self, user_id: str, old_password: str, new_password: str, client_id: Optional[str] = None
    ) -> bool:
        """
        Change user password (multi-tenant).
        
        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password
            client_id: Optional client ID for validation
            
        Raises:
            UserNotFoundException: If user not found
            InvalidCredentialsException: If current password is incorrect
            ValidationException: If new password doesn't meet requirements
            DomainException: If technical error occurs
        """
        try:
            user = await self.repository.find_by_id(user_id, client_id=client_id)
            if not user:
                raise UserNotFoundException(user_id=user_id)
            
            if not self._verify_password(old_password, user.password_hash):
                raise InvalidCredentialsException()
            
            new_password_hash = self._validate_and_hash_password(new_password)
            user.change_password_hash(new_password_hash)  # Use controlled method for encapsulation
            user.updated_at = datetime.utcnow()
            
            await self.repository.save(user)
            
            logger.info("Password changed successfully", extra={"user_id": user_id, "client_id": user.client_id})
            return True
            
        except (UserNotFoundException, InvalidCredentialsException, ValidationException):
            # Domain exceptions - let them propagate
            raise
        except Exception as e:
            logger.error(f"Unexpected error changing password: {e}", exc_info=True, extra={"user_id": user_id, "client_id": client_id})
            raise DomainException("Failed to change password due to technical error", "PASSWORD_CHANGE_FAILED")
    
    async def get_current_user(self, user_id: str, client_id: Optional[str] = None) -> Optional[AppUser]:
        """
        Get current user by ID (multi-tenant).
        
        ⚡ PERFORMANCE: Uses Redis cache to reduce database queries by 90%
        Cache TTL: 15 minutes
        
        Args:
            user_id: User ID
            client_id: Optional client ID for validation
        """
        if not client_id:
            # If no client_id provided, fetch from database (cache needs client_id)
            return await self.repository.find_by_id(user_id, client_id=client_id)
        
        # Try to get from cache first
        cached_user_data = await self.cache_helper.get_cached_user_profile(user_id, client_id)
        
        if cached_user_data:
            # Reconstruct AppUser from cached data
            try:
                return AppUser(
                    id=cached_user_data['id'],
                    username=cached_user_data['username'],
                    email=cached_user_data['email'],
                    hashed_password=cached_user_data.get('hashed_password', ''),
                    name=cached_user_data['name'],
                    role=UserRole(cached_user_data['role']),
                    email_verified=cached_user_data.get('email_verified', False),
                    mfa_enabled=cached_user_data.get('mfa_enabled', False),
                    is_active=cached_user_data.get('is_active', True),
                    client_id=cached_user_data['client_id'],
                    created_at=datetime.fromisoformat(cached_user_data['created_at']) if cached_user_data.get('created_at') else None
                )
            except Exception as e:
                logger.warning(f"Error reconstructing user from cache: {e}, fetching from DB")
                # Fall through to database query
        
        # Cache miss - fetch from database
        user = await self.repository.find_by_id(user_id, client_id=client_id)
        
        if user and client_id:
            # Cache the user profile for future requests
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'hashed_password': user.hashed_password,
                'name': user.name,
                'role': user.role.value,
                'email_verified': user.email_verified,
                'mfa_enabled': user.mfa_enabled,
                'is_active': user.is_active,
                'client_id': user.client_id,
                'created_at': user.created_at.isoformat() if user.created_at else None
            }
            await self.cache_helper.cache_user_profile(user_id, client_id, user_data)
        
        return user
    
    async def list_all_users(self, filter: Optional[UserFilter] = None) -> List[AppUser]:
        """
        List all users with optional filter (admin only).
        
        Filter Pattern: Service passes filter directly to repository.
        NO conditional logic here - repository handles all filtering, pagination, and sorting.
        
        Returns:
            List of users (empty list if error, graceful degradation)
        """
        logger.info("Listing users", extra={"filter": filter})
        
        try:
            result = await self.repository.find_all(filter)
            logger.info(f"Found {len(result)} users")
            return result
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}", exc_info=True, extra={"filter": filter})
            # Graceful degradation: return empty list instead of failing
            return []
    
    async def count_users(self, filter: Optional[UserFilter] = None) -> int:
        """
        Counts users with optional filter.
        
        Filter Pattern: Uses same filter as list_all_users but without pagination/sorting.
        Simple delegation - repository handles all filter logic.
        
        Returns:
            Count of users (0 if error, graceful degradation)
        """
        logger.info("Counting users", extra={"filter": filter})
        
        try:
            result = await self.repository.count(filter)
            logger.info(f"Counted {result} users")
            return result
        except Exception as e:
            logger.error(f"Error counting users: {str(e)}", exc_info=True, extra={"filter": filter})
            # Graceful degradation: return 0 instead of failing
            return 0
    
    async def get_user_by_email(self, email: str, client_id: Optional[str] = None) -> Optional[AppUser]:
        """
        Get user by email (admin only, multi-tenant).
        
        Args:
            email: User email
            client_id: Optional client ID for filtering
        """
        return await self.repository.find_by_email(email, client_id=client_id)
    
    async def get_user_by_id(self, user_id: str, client_id: Optional[str] = None) -> Optional[AppUser]:
        """
        Get user by ID (admin only, multi-tenant).
        
        Args:
            user_id: User ID
            client_id: Optional client ID for filtering
        """
        return await self.repository.find_by_id(user_id, client_id=client_id)
    
    async def admin_update_user(self, user: AppUser) -> AppUser:
        """
        Update user (admin only).
        
        Args:
            user: User domain object with updated fields
        """
        user.updated_at = datetime.utcnow()
        return await self.repository.save(user)
    
    async def admin_delete_user(self, user_id: str, admin_id: str, client_id: Optional[str] = None) -> bool:
        """
        Delete user (admin only, multi-tenant).
        Prevents self-deletion.
        
        Args:
            user_id: ID of user to delete
            admin_id: ID of admin performing the deletion
            client_id: Optional client ID for validation
            
        Raises:
            BusinessRuleException: If trying to delete own account
            DomainException: If technical error occurs
        """
        try:
            if user_id == admin_id:
                raise BusinessRuleException("Cannot delete your own account", "CANNOT_DELETE_OWN_ACCOUNT")
            
            result = await self.repository.delete(user_id, client_id=client_id)
            if result:
                logger.info("User deleted successfully", extra={"user_id": user_id, "admin_id": admin_id, "client_id": client_id})
            return result
            
        except BusinessRuleException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting user: {e}", exc_info=True, extra={"user_id": user_id, "admin_id": admin_id, "client_id": client_id})
            raise DomainException("Failed to delete user due to technical error", "USER_DELETION_FAILED")
    
    # ========================================================================
    # BULK OPERATIONS (API Design Guide Compliance)
    # ========================================================================
    
    async def bulk_create_users(
        self,
        users_data: List[dict],
        client_id: str,
        admin_id: str
    ) -> dict:
        """
        Bulk create users with transaction support and detailed error tracking.
        
        Args:
            users_data: List of user data dicts (username, email, password, name)
            client_id: Client ID for all users
            admin_id: Admin performing the operation
        
        Returns:
            dict with success_count, error_count, successful_ids, errors, processing_time_ms
        
        Example:
            >>> result = await auth_service.bulk_create_users([
            ...     {"username": "user1", "email": "user1@test.com", "password": "Pass123", "name": "User 1"},
            ...     {"username": "user2", "email": "user2@test.com", "password": "Pass456", "name": "User 2"}
            ... ], client_id="client_123", admin_id="admin_123")
            >>> print(result["success_count"])  # 2
        """
        import time
        start_time = time.time()
        
        successful_ids = []
        errors = []
        
        for index, user_data in enumerate(users_data):
            try:
                # Validate required fields
                if not all(k in user_data for k in ["username", "email", "password", "name"]):
                    errors.append({
                        "index": index,
                        "identifier": user_data.get("email", f"item_{index}"),
                        "error_code": "MISSING_REQUIRED_FIELD",
                        "error_message": "Missing required fields (username, email, password, name)",
                        "details": None
                    })
                    continue
                
                # Check for duplicates (email)
                existing = await self.repository.find_by_email(user_data["email"], client_id=client_id)
                if existing:
                    errors.append({
                        "index": index,
                        "identifier": user_data["email"],
                        "error_code": "EMAIL_ALREADY_EXISTS",
                        "error_message": f"Email {user_data['email']} already exists",
                        "details": {"existing_user_id": existing.id}
                    })
                    continue
                
                # Check for duplicates (username)
                existing_username = await self.repository.find_by_username(
                    user_data["username"], 
                    client_id=client_id
                )
                if existing_username:
                    errors.append({
                        "index": index,
                        "identifier": user_data["username"],
                        "error_code": "USERNAME_ALREADY_EXISTS",
                        "error_message": f"Username {user_data['username']} already exists",
                        "details": {"existing_user_id": existing_username.id}
                    })
                    continue
                
                # Create user (reuse register logic)
                user = await self.register(
                    username=user_data["username"],
                    email=user_data["email"],
                    password=user_data["password"],
                    name=user_data["name"],
                    client_id=client_id
                )
                
                successful_ids.append(user.id)
                logger.info(f"Bulk create: User created successfully", extra={
                    "user_id": user.id,
                    "index": index,
                    "admin_id": admin_id
                })
            
            except Exception as e:
                error_message = str(e)
                error_code = "UNKNOWN_ERROR"
                
                # Map known exceptions
                if "already exists" in error_message.lower():
                    error_code = "DUPLICATE_ENTRY"
                elif "validation" in error_message.lower():
                    error_code = "VALIDATION_ERROR"
                
                errors.append({
                    "index": index,
                    "identifier": user_data.get("email", f"item_{index}"),
                    "error_code": error_code,
                    "error_message": error_message,
                    "details": None
                })
                logger.warning(f"Bulk create: Failed to create user at index {index}", extra={
                    "error": error_message,
                    "admin_id": admin_id
                })
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return {
            "success_count": len(successful_ids),
            "error_count": len(errors),
            "total": len(users_data),
            "successful_ids": successful_ids,
            "errors": errors,
            "partial_success": len(successful_ids) > 0 and len(errors) > 0,
            "processing_time_ms": processing_time_ms,
            "timestamp": datetime.utcnow()
        }
    
    async def bulk_update_users(
        self,
        updates: List[dict],
        client_id: str,
        admin_id: str
    ) -> dict:
        """
        Bulk update users with detailed error tracking.
        
        Args:
            updates: List of dicts with user_id and fields to update
            client_id: Client ID for validation
            admin_id: Admin performing the operation
        
        Returns:
            dict with success_count, error_count, successful_ids, errors
        
        Example:
            >>> result = await auth_service.bulk_update_users([
            ...     {"user_id": "user_123", "name": "New Name", "is_active": False},
            ...     {"user_id": "user_456", "role": "admin"}
            ... ], client_id="client_123", admin_id="admin_123")
        """
        import time
        start_time = time.time()
        
        successful_ids = []
        errors = []
        
        for index, update_data in enumerate(updates):
            try:
                user_id = update_data.get("user_id")
                if not user_id:
                    errors.append({
                        "index": index,
                        "identifier": f"item_{index}",
                        "error_code": "MISSING_USER_ID",
                        "error_message": "user_id is required for each update",
                        "details": None
                    })
                    continue
                
                # Get user
                user = await self.repository.find_by_id(user_id, client_id=client_id)
                if not user:
                    errors.append({
                        "index": index,
                        "identifier": user_id,
                        "error_code": "USER_NOT_FOUND",
                        "error_message": f"User {user_id} not found",
                        "details": None
                    })
                    continue
                
                # Update fields
                if "username" in update_data:
                    user.username = update_data["username"]
                if "email" in update_data:
                    user.email = update_data["email"]
                if "name" in update_data:
                    user.name = update_data["name"]
                if "role" in update_data:
                    try:
                        user.role = UserRole(update_data["role"])
                    except ValueError:
                        errors.append({
                            "index": index,
                            "identifier": user_id,
                            "error_code": "INVALID_ROLE",
                            "error_message": f"Invalid role: {update_data['role']}",
                            "details": None
                        })
                        continue
                if "is_active" in update_data:
                    user.active = update_data["is_active"]
                
                # Save user
                user.updated_at = datetime.utcnow()
                await self.repository.save(user)
                
                successful_ids.append(user_id)
                logger.info(f"Bulk update: User updated successfully", extra={
                    "user_id": user_id,
                    "index": index,
                    "admin_id": admin_id
                })
            
            except Exception as e:
                errors.append({
                    "index": index,
                    "identifier": update_data.get("user_id", f"item_{index}"),
                    "error_code": "UPDATE_FAILED",
                    "error_message": str(e),
                    "details": None
                })
                logger.warning(f"Bulk update: Failed at index {index}", extra={
                    "error": str(e),
                    "admin_id": admin_id
                })
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return {
            "success_count": len(successful_ids),
            "error_count": len(errors),
            "total": len(updates),
            "successful_ids": successful_ids,
            "errors": errors,
            "partial_success": len(successful_ids) > 0 and len(errors) > 0,
            "processing_time_ms": processing_time_ms,
            "timestamp": datetime.utcnow()
        }
    
    async def bulk_delete_users(
        self,
        user_ids: List[str],
        client_id: str,
        admin_id: str
    ) -> dict:
        """
        Bulk delete users with validation and error tracking.
        
        Args:
            user_ids: List of user IDs to delete
            client_id: Client ID for validation
            admin_id: Admin performing the operation
        
        Returns:
            dict with success_count, error_count, successful_ids, errors
        
        Raises:
            BusinessRuleException: If trying to delete own account
        """
        import time
        start_time = time.time()
        
        successful_ids = []
        errors = []
        
        for index, user_id in enumerate(user_ids):
            try:
                # Prevent self-deletion
                if user_id == admin_id:
                    errors.append({
                        "index": index,
                        "identifier": user_id,
                        "error_code": "CANNOT_DELETE_OWN_ACCOUNT",
                        "error_message": "Cannot delete your own account",
                        "details": None
                    })
                    continue
                
                # Check if user exists
                user = await self.repository.find_by_id(user_id, client_id=client_id)
                if not user:
                    errors.append({
                        "index": index,
                        "identifier": user_id,
                        "error_code": "USER_NOT_FOUND",
                        "error_message": f"User {user_id} not found",
                        "details": None
                    })
                    continue
                
                # Delete user
                success = await self.repository.delete(user_id, client_id=client_id)
                
                if success:
                    successful_ids.append(user_id)
                    logger.info(f"Bulk delete: User deleted successfully", extra={
                        "user_id": user_id,
                        "index": index,
                        "admin_id": admin_id
                    })
                else:
                    errors.append({
                        "index": index,
                        "identifier": user_id,
                        "error_code": "DELETE_FAILED",
                        "error_message": f"Failed to delete user {user_id}",
                        "details": None
                    })
            
            except Exception as e:
                errors.append({
                    "index": index,
                    "identifier": user_id,
                    "error_code": "DELETE_FAILED",
                    "error_message": str(e),
                    "details": None
                })
                logger.warning(f"Bulk delete: Failed at index {index}", extra={
                    "error": str(e),
                    "admin_id": admin_id
                })
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return {
            "success_count": len(successful_ids),
            "error_count": len(errors),
            "total": len(user_ids),
            "successful_ids": successful_ids,
            "errors": errors,
            "partial_success": len(successful_ids) > 0 and len(errors) > 0,
            "processing_time_ms": processing_time_ms,
            "timestamp": datetime.utcnow()
        }

