"""
Domain Exceptions
Custom exceptions for business logic and error handling
"""
from typing import Optional


class DomainException(Exception):
    """Base exception for all domain exceptions"""
    pass


class EntityNotFoundException(DomainException):
    """Raised when an entity is not found"""
    
    def __init__(self, entity_type: str, entity_id: Optional[str] = None):
        self.entity_type = entity_type
        self.entity_id = entity_id
        message = f"{entity_type} not found"
        if entity_id:
            message += f" (id: {entity_id})"
        super().__init__(message)


class DuplicateEntityException(DomainException):
    """Raised when trying to create a duplicate entity"""
    
    def __init__(self, entity_type: str, field: str, value: str):
        self.entity_type = entity_type
        self.field = field
        self.value = value
        super().__init__(f"{entity_type} with {field}='{value}' already exists")


class ValidationException(DomainException):
    """Raised when validation fails"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message)


class UnauthorizedException(DomainException):
    """Raised when user is not authenticated"""
    pass


class ForbiddenException(DomainException):
    """Raised when user is not authorized to perform action"""
    pass


class IntegrityException(DomainException):
    """Raised when there's a database integrity constraint violation"""
    
    def __init__(self, entity_type: str, entity_id: Optional[str] = None, dependent_entities: Optional[list] = None):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.dependent_entities = dependent_entities or []
        message = f"Cannot delete {entity_type}"
        if dependent_entities:
            message += f" - it has dependent entities: {', '.join(dependent_entities)}"
        super().__init__(message)


class BusinessRuleException(DomainException):
    """Raised when a business rule is violated"""
    
    def __init__(self, message: str, rule: Optional[str] = None):
        self.rule = rule
        super().__init__(message)

