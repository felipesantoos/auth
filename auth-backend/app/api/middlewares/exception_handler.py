"""
Global Exception Handlers
Maps domain exceptions to HTTP responses
"""
import logging
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from core.exceptions import (
    DomainException,
    ValidationException,
    NotFoundException,
    ConflictException,
    AuthorizationException,
    AuthenticationException,
    BusinessRuleException,
    ExternalServiceException,
    # Specific exceptions
    InvalidEmailException,
    InvalidPasswordException,
    MissingRequiredFieldException,
    InvalidValueException,
    UserNotFoundException,
    EntityNotFoundException,
    EmailAlreadyExistsException,
    UsernameAlreadyExistsException,
    DuplicateEntityException,
    PermissionDeniedException,
    ResourceOwnershipException,
    InvalidCredentialsException,
    TokenExpiredException,
    InvalidTokenException,
    # Legacy compatibility
    UnauthorizedException,
    ForbiddenException,
    IntegrityException,
)
from config.settings import settings

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response format"""
    
    def __init__(
        self,
        error: str,
        message: str,
        code: str = None,
        details: dict = None,
        status_code: int = 500
    ):
        self.error = error
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code
    
    def to_dict(self):
        response = {
            "error": self.error,
            "message": self.message
        }
        
        if self.code:
            response["code"] = self.code
        
        if self.details:
            response["details"] = self.details
        
        return response


async def exception_handler_middleware(request: Request, call_next):
    """
    Global exception handler middleware.
    
    Catches all exceptions and returns appropriate HTTP responses.
    """
    try:
        return await call_next(request)
    except Exception as exc:
        return handle_exception(request, exc)


def handle_exception(request: Request, exc: Exception) -> JSONResponse:
    """
    Map exceptions to HTTP responses.
    
    Domain Exception → HTTP Status Code
    """
    
    # ===================================================================
    # VALIDATION ERRORS → 400 Bad Request
    # ===================================================================
    if isinstance(exc, ValidationException):
        logger.warning(f"Validation error: {exc}", extra={"path": request.url.path})
        error_response = ErrorResponse(
            error="Validation Error",
            message=exc.message,
            code=exc.code,
            status_code=status.HTTP_400_BAD_REQUEST
        )
        return JSONResponse(
            status_code=error_response.status_code,
            content=error_response.to_dict()
        )
    
    # ===================================================================
    # NOT FOUND ERRORS → 404 Not Found
    # ===================================================================
    elif isinstance(exc, NotFoundException):
        logger.info(f"Not found: {exc}", extra={"path": request.url.path})
        error_response = ErrorResponse(
            error="Not Found",
            message=exc.message,
            code=exc.code,
            status_code=status.HTTP_404_NOT_FOUND
        )
        return JSONResponse(
            status_code=error_response.status_code,
            content=error_response.to_dict()
        )
    
    # ===================================================================
    # CONFLICT ERRORS → 409 Conflict
    # ===================================================================
    elif isinstance(exc, ConflictException):
        logger.warning(f"Conflict error: {exc}", extra={"path": request.url.path})
        error_response = ErrorResponse(
            error="Conflict",
            message=exc.message,
            code=exc.code,
            status_code=status.HTTP_409_CONFLICT
        )
        return JSONResponse(
            status_code=error_response.status_code,
            content=error_response.to_dict()
        )
    
    # ===================================================================
    # AUTHENTICATION ERRORS → 401 Unauthorized
    # ===================================================================
    elif isinstance(exc, AuthenticationException):
        logger.warning(f"Authentication error: {exc}", extra={"path": request.url.path})
        error_response = ErrorResponse(
            error="Authentication Failed",
            message=exc.message,
            code=exc.code,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
        return JSONResponse(
            status_code=error_response.status_code,
            content=error_response.to_dict(),
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # ===================================================================
    # AUTHORIZATION ERRORS → 403 Forbidden
    # ===================================================================
    elif isinstance(exc, AuthorizationException):
        logger.warning(f"Authorization error: {exc}", extra={"path": request.url.path})
        error_response = ErrorResponse(
            error="Permission Denied",
            message=exc.message,
            code=exc.code,
            status_code=status.HTTP_403_FORBIDDEN
        )
        return JSONResponse(
            status_code=error_response.status_code,
            content=error_response.to_dict()
        )
    
    # ===================================================================
    # BUSINESS RULE ERRORS → 422 Unprocessable Entity
    # ===================================================================
    elif isinstance(exc, BusinessRuleException):
        logger.warning(f"Business rule violation: {exc}", extra={"path": request.url.path})
        error_response = ErrorResponse(
            error="Business Rule Violation",
            message=exc.message,
            code=exc.code,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        return JSONResponse(
            status_code=error_response.status_code,
            content=error_response.to_dict()
        )
    
    # ===================================================================
    # EXTERNAL SERVICE ERRORS → 502/503 in API
    # ===================================================================
    elif isinstance(exc, ExternalServiceException):
        logger.error(f"External service error: {exc}", extra={"path": request.url.path})
        error_response = ErrorResponse(
            error="External Service Error",
            message="An external service is temporarily unavailable",
            code=exc.code,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
        return JSONResponse(
            status_code=error_response.status_code,
            content=error_response.to_dict()
        )
    
    # ===================================================================
    # GENERIC DOMAIN ERRORS → 500 Internal Server Error
    # ===================================================================
    elif isinstance(exc, DomainException):
        logger.error(f"Domain error: {exc}", extra={"path": request.url.path})
        error_response = ErrorResponse(
            error="Internal Error",
            message="An internal error occurred",
            code=exc.code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        return JSONResponse(
            status_code=error_response.status_code,
            content=error_response.to_dict()
        )
    
    # ===================================================================
    # FASTAPI VALIDATION ERRORS → 422 Unprocessable Entity
    # ===================================================================
    elif isinstance(exc, RequestValidationError):
        logger.warning(f"Request validation error: {exc}", extra={"path": request.url.path})
        error_response = ErrorResponse(
            error="Validation Error",
            message="Request validation failed",
            code="REQUEST_VALIDATION_ERROR",
            details={"errors": exc.errors()},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        return JSONResponse(
            status_code=error_response.status_code,
            content=error_response.to_dict()
        )
    
    # ===================================================================
    # STARLETTE HTTP EXCEPTIONS → Pass through
    # ===================================================================
    elif isinstance(exc, StarletteHTTPException):
        logger.info(f"HTTP exception: {exc.status_code} - {exc.detail}", extra={"path": request.url.path})
        error_response = ErrorResponse(
            error="HTTP Error",
            message=exc.detail,
            status_code=exc.status_code
        )
        return JSONResponse(
            status_code=error_response.status_code,
            content=error_response.to_dict()
        )
    
    # ===================================================================
    # UNEXPECTED ERRORS → 500 Internal Server Error
    # ===================================================================
    else:
        # Log full traceback for debugging (server-side only)
        logger.error(
            f"Unexpected error: {exc}\n"
            f"Request: {request.method} {request.url}\n"
            f"Traceback:\n{traceback.format_exc()}",
            extra={"path": request.url.path, "method": request.method}
        )
        
        # SECURITY: Don't leak internal details to client in production
        # Only show detailed errors in development/debug mode
        if settings.environment == "production" or not settings.debug:
            # Production: Generic error message (no stack trace, no internal details)
            error_response = ErrorResponse(
                error="Internal Server Error",
                message="An unexpected error occurred. Please try again later.",
                code="INTERNAL_ERROR",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        else:
            # Development: Show detailed error for debugging
            error_response = ErrorResponse(
                error="Internal Server Error",
                message=str(exc),
                code="UNEXPECTED_ERROR",
                details={"traceback": traceback.format_exc().split('\n')} if settings.debug else {},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return JSONResponse(
            status_code=error_response.status_code,
            content=error_response.to_dict()
        )


# Individual handlers for backward compatibility and explicit registration
async def entity_not_found_handler(request: Request, exc: EntityNotFoundException) -> JSONResponse:
    """Handler for EntityNotFoundException"""
    return handle_exception(request, exc)


async def duplicate_entity_handler(request: Request, exc: DuplicateEntityException) -> JSONResponse:
    """Handler for DuplicateEntityException"""
    return handle_exception(request, exc)


async def validation_handler(request: Request, exc: ValidationException) -> JSONResponse:
    """Handler for ValidationException"""
    return handle_exception(request, exc)


async def unauthorized_handler(request: Request, exc: UnauthorizedException) -> JSONResponse:
    """Handler for UnauthorizedException"""
    return handle_exception(request, exc)


async def forbidden_handler(request: Request, exc: ForbiddenException) -> JSONResponse:
    """Handler for ForbiddenException"""
    return handle_exception(request, exc)


async def integrity_handler(request: Request, exc: IntegrityException) -> JSONResponse:
    """Handler for IntegrityException"""
    return handle_exception(request, exc)


async def business_rule_handler(request: Request, exc: BusinessRuleException) -> JSONResponse:
    """Handler for BusinessRuleException"""
    return handle_exception(request, exc)


def register_exception_handlers(app):
    """
    Register all custom exception handlers.
    
    Call this in main.py after app creation.
    """
    # Register specific exception handlers
    app.add_exception_handler(EntityNotFoundException, entity_not_found_handler)
    app.add_exception_handler(DuplicateEntityException, duplicate_entity_handler)
    app.add_exception_handler(ValidationException, validation_handler)
    app.add_exception_handler(UnauthorizedException, unauthorized_handler)
    app.add_exception_handler(ForbiddenException, forbidden_handler)
    app.add_exception_handler(IntegrityException, integrity_handler)
    app.add_exception_handler(BusinessRuleException, business_rule_handler)
    
    # Register base exception handlers for all domain exceptions
    app.add_exception_handler(NotFoundException, handle_exception)
    app.add_exception_handler(ConflictException, handle_exception)
    app.add_exception_handler(AuthenticationException, handle_exception)
    app.add_exception_handler(AuthorizationException, handle_exception)
    app.add_exception_handler(ExternalServiceException, handle_exception)
    app.add_exception_handler(DomainException, handle_exception)
    
    # Register FastAPI validation errors
    app.add_exception_handler(RequestValidationError, handle_exception)
    
    # Register HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, handle_exception)
    
    # Register global exception handler middleware
    app.middleware("http")(exception_handler_middleware)
    
    logger.info("Custom exception handlers registered")
