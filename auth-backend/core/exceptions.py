"""
Domain Exceptions - Pure business logic errors.

These exceptions:
- Represent business rule violations
- Are independent of infrastructure
- Should be meaningful to business stakeholders
- Never contain HTTP status codes or database details
"""
from typing import Optional


class DomainException(Exception):
    """
    Base exception for all domain errors.
    
    All domain exceptions inherit from this.
    Services catch these and decide how to handle them.
    """
    
    def __init__(self, message: str, code: str = None):
        """
        Args:
            message: Human-readable error message
            code: Optional error code for client handling
        """
        self.message = message
        self.code = code or self.__class__.__name__
        super().__init__(self.message)
    
    def __str__(self):
        return f"{self.code}: {self.message}"


# ===================================================================
# VALIDATION ERRORS (400 Bad Request in API)
# ===================================================================

class ValidationException(DomainException):
    """Base for validation errors (invalid input)"""
    pass


class InvalidEmailException(ValidationException):
    """Email format is invalid"""
    def __init__(self, email: str):
        super().__init__(
            message=f"Invalid email format: {email}",
            code="INVALID_EMAIL"
        )


class InvalidPasswordException(ValidationException):
    """Password doesn't meet requirements"""
    def __init__(self, reason: str):
        super().__init__(
            message=f"Password validation failed: {reason}",
            code="INVALID_PASSWORD"
        )


class MissingRequiredFieldException(ValidationException):
    """Required field is missing"""
    def __init__(self, field_name: str):
        super().__init__(
            message=f"Required field '{field_name}' is missing",
            code="MISSING_REQUIRED_FIELD"
        )


class InvalidValueException(ValidationException):
    """Value is invalid for this field"""
    def __init__(self, field_name: str, value: any, reason: str = None):
        message = f"Invalid value for '{field_name}': {value}"
        if reason:
            message += f" - {reason}"
        super().__init__(message=message, code="INVALID_VALUE")


# ===================================================================
# NOT FOUND ERRORS (404 Not Found in API)
# ===================================================================

class NotFoundException(DomainException):
    """Base for not found errors"""
    pass


class EntityNotFoundException(NotFoundException):
    """Entity with given ID not found"""
    def __init__(self, entity_type: str, entity_id: Optional[str] = None):
        message = f"{entity_type} not found"
        if entity_id:
            message += f" (id: {entity_id})"
        super().__init__(
            message=message,
            code="ENTITY_NOT_FOUND"
        )


class UserNotFoundException(NotFoundException):
    """User not found"""
    def __init__(self, user_id: Optional[str] = None, email: Optional[str] = None):
        if user_id:
            identifier = f"ID {user_id}"
        elif email:
            identifier = f"email {email}"
        else:
            identifier = "given identifier"
        
        super().__init__(
            message=f"User with {identifier} not found",
            code="USER_NOT_FOUND"
        )


# ===================================================================
# CONFLICT ERRORS (409 Conflict in API)
# ===================================================================

class ConflictException(DomainException):
    """Base for conflict errors (duplicate, already exists)"""
    pass


class DuplicateEntityException(ConflictException):
    """Entity already exists"""
    def __init__(self, entity_type: str, field_name: str, value: any):
        super().__init__(
            message=f"{entity_type} with {field_name}='{value}' already exists",
            code="DUPLICATE_ENTITY"
        )


class EmailAlreadyExistsException(ConflictException):
    """Email is already registered"""
    def __init__(self, email: str):
        super().__init__(
            message=f"Email '{email}' is already registered",
            code="EMAIL_ALREADY_EXISTS"
        )


class UsernameAlreadyExistsException(ConflictException):
    """Username is already taken"""
    def __init__(self, username: str):
        super().__init__(
            message=f"Username '{username}' is already taken",
            code="USERNAME_ALREADY_EXISTS"
        )


# ===================================================================
# AUTHORIZATION ERRORS (403 Forbidden in API)
# ===================================================================

class AuthorizationException(DomainException):
    """Base for authorization errors"""
    pass


class PermissionDeniedException(AuthorizationException):
    """User doesn't have permission"""
    def __init__(self, action: str, resource: str = None):
        message = f"Permission denied for action: {action}"
        if resource:
            message += f" on resource: {resource}"
        super().__init__(message=message, code="PERMISSION_DENIED")


class ResourceOwnershipException(AuthorizationException):
    """User doesn't own the resource"""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"You don't have permission to access {resource_type} {resource_id}",
            code="RESOURCE_OWNERSHIP_DENIED"
        )


# ===================================================================
# AUTHENTICATION ERRORS (401 Unauthorized in API)
# ===================================================================

class AuthenticationException(DomainException):
    """Base for authentication errors"""
    pass


class InvalidCredentialsException(AuthenticationException):
    """Invalid username/password"""
    def __init__(self):
        super().__init__(
            message="Invalid email or password",
            code="INVALID_CREDENTIALS"
        )


class TokenExpiredException(AuthenticationException):
    """JWT token has expired"""
    def __init__(self, message: str = "Authentication token has expired"):
        super().__init__(
            message=message,
            code="TOKEN_EXPIRED"
        )


class InvalidTokenException(AuthenticationException):
    """JWT token is invalid"""
    def __init__(self, message: str = "Invalid authentication token"):
        super().__init__(
            message=message,
            code="INVALID_TOKEN"
        )


# ===================================================================
# BUSINESS RULE ERRORS (422 Unprocessable Entity in API)
# ===================================================================

class BusinessRuleException(DomainException):
    """Base for business rule violations"""
    pass


class InsufficientBalanceException(BusinessRuleException):
    """Not enough balance for operation"""
    def __init__(self, current: float, required: float):
        super().__init__(
            message=f"Insufficient balance. Current: {current}, Required: {required}",
            code="INSUFFICIENT_BALANCE"
        )


class MaximumLimitExceededException(BusinessRuleException):
    """Maximum limit exceeded"""
    def __init__(self, limit_type: str, current: int, maximum: int):
        super().__init__(
            message=f"{limit_type} limit exceeded. Current: {current}, Maximum: {maximum}",
            code="MAXIMUM_LIMIT_EXCEEDED"
        )


class InvalidStateTransitionException(BusinessRuleException):
    """Invalid state transition"""
    def __init__(self, from_state: str, to_state: str, reason: str = None):
        message = f"Cannot transition from '{from_state}' to '{to_state}'"
        if reason:
            message += f": {reason}"
        super().__init__(message=message, code="INVALID_STATE_TRANSITION")


# ===================================================================
# EXTERNAL SERVICE ERRORS (502/503 in API)
# ===================================================================

class ExternalServiceException(DomainException):
    """Base for external service errors"""
    pass


class PaymentGatewayException(ExternalServiceException):
    """Payment gateway error"""
    def __init__(self, reason: str):
        super().__init__(
            message=f"Payment gateway error: {reason}",
            code="PAYMENT_GATEWAY_ERROR"
        )


class EmailServiceException(ExternalServiceException):
    """Email service error"""
    def __init__(self, reason: str):
        super().__init__(
            message=f"Email service error: {reason}",
            code="EMAIL_SERVICE_ERROR"
        )


class AIServiceException(ExternalServiceException):
    """AI service error (OpenAI, etc.)"""
    def __init__(self, service_name: str, reason: str):
        super().__init__(
            message=f"{service_name} error: {reason}",
            code="AI_SERVICE_ERROR"
        )


# ===================================================================
# LEGACY COMPATIBILITY (for backward compatibility)
# ===================================================================

# Keep these aliases for backward compatibility with existing code
# These will be replaced gradually with more specific exceptions

UnauthorizedException = AuthenticationException
ForbiddenException = AuthorizationException


class IntegrityException(DomainException):
    """
    Raised when there's a database integrity constraint violation.
    
    Note: This is a legacy exception. Prefer using ConflictException
    or DuplicateEntityException for new code.
    """
    def __init__(self, entity_type: str, entity_id: Optional[str] = None, dependent_entities: Optional[list] = None):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.dependent_entities = dependent_entities or []
        message = f"Cannot delete {entity_type}"
        if dependent_entities:
            message += f" - it has dependent entities: {', '.join(dependent_entities)}"
        super().__init__(message=message, code="INTEGRITY_ERROR")
