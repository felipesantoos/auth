"""
Global Exception Handlers
Maps domain exceptions to HTTP responses
"""
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from core.exceptions import (
    EntityNotFoundException,
    DuplicateEntityException,
    ValidationException,
    UnauthorizedException,
    ForbiddenException,
    IntegrityException,
    BusinessRuleException,
)

logger = logging.getLogger(__name__)


async def entity_not_found_handler(request: Request, exc: EntityNotFoundException) -> JSONResponse:
    """Handler for EntityNotFoundException"""
    logger.warning(
        "Entity not found",
        extra={
            "entity_type": exc.entity_type,
            "entity_id": exc.entity_id,
            "path": request.url.path
        }
    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": str(exc),
            "entity_type": exc.entity_type,
            "entity_id": exc.entity_id
        }
    )


async def duplicate_entity_handler(request: Request, exc: DuplicateEntityException) -> JSONResponse:
    """Handler for DuplicateEntityException"""
    logger.warning(
        "Duplicate entity",
        extra={
            "entity_type": exc.entity_type,
            "field": exc.field,
            "value": exc.value
        }
    )
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": str(exc),
            "entity_type": exc.entity_type,
            "field": exc.field
        }
    )


async def validation_handler(request: Request, exc: ValidationException) -> JSONResponse:
    """Handler for ValidationException"""
    logger.warning("Validation error", extra={"field": exc.field, "message": str(exc)})
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": str(exc),
            "field": exc.field
        }
    )


async def unauthorized_handler(request: Request, exc: UnauthorizedException) -> JSONResponse:
    """Handler for UnauthorizedException"""
    logger.warning("Unauthorized access attempt", extra={"path": request.url.path})
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc)}
    )


async def forbidden_handler(request: Request, exc: ForbiddenException) -> JSONResponse:
    """Handler for ForbiddenException"""
    logger.warning("Forbidden access attempt", extra={"path": request.url.path})
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc)}
    )


async def integrity_handler(request: Request, exc: IntegrityException) -> JSONResponse:
    """Handler for IntegrityException"""
    logger.warning(
        "Integrity constraint violation",
        extra={
            "entity_type": exc.entity_type,
            "entity_id": exc.entity_id,
            "dependent_entities": exc.dependent_entities
        }
    )
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": str(exc),
            "entity_type": exc.entity_type,
            "dependent_entities": exc.dependent_entities
        }
    )


async def business_rule_handler(request: Request, exc: BusinessRuleException) -> JSONResponse:
    """Handler for BusinessRuleException"""
    logger.warning("Business rule violation", extra={"rule": exc.rule})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": str(exc),
            "rule": exc.rule
        }
    )


def register_exception_handlers(app):
    """
    Register all custom exception handlers
    
    Call this in main.py after app creation
    """
    app.add_exception_handler(EntityNotFoundException, entity_not_found_handler)
    app.add_exception_handler(DuplicateEntityException, duplicate_entity_handler)
    app.add_exception_handler(ValidationException, validation_handler)
    app.add_exception_handler(UnauthorizedException, unauthorized_handler)
    app.add_exception_handler(ForbiddenException, forbidden_handler)
    app.add_exception_handler(IntegrityException, integrity_handler)
    app.add_exception_handler(BusinessRuleException, business_rule_handler)
    
    logger.info("Custom exception handlers registered")

