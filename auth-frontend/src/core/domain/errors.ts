/**
 * Custom Error Classes for Domain Layer
 * Provides type-safe, structured error handling
 * 
 * Compliance: 08c-react-best-practices.md Section 5.2
 */

/**
 * Base Domain Error
 * All domain errors extend this class
 */
export class DomainError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 400
  ) {
    super(message);
    this.name = this.constructor.name;
    // Maintains proper prototype chain for instanceof checks
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/**
 * Business Validation Error
 * Thrown when business rules are violated
 * Status: 400 Bad Request
 */
export class BusinessValidationError extends DomainError {
  constructor(message: string) {
    super(message, 'BUSINESS_VALIDATION_ERROR', 400);
  }
}

/**
 * Authentication Error
 * Thrown when authentication fails (invalid credentials)
 * Status: 401 Unauthorized
 */
export class AuthenticationError extends DomainError {
  constructor(message: string = 'Authentication failed') {
    super(message, 'AUTHENTICATION_ERROR', 401);
  }
}

/**
 * Authorization Error
 * Thrown when user doesn't have permission for an action
 * Status: 403 Forbidden
 */
export class AuthorizationError extends DomainError {
  constructor(message: string = 'Insufficient permissions') {
    super(message, 'AUTHORIZATION_ERROR', 403);
  }
}

/**
 * Entity Not Found Error
 * Thrown when a requested entity doesn't exist
 * Status: 404 Not Found
 */
export class EntityNotFoundError extends DomainError {
  constructor(entityName: string, id: string) {
    super(`${entityName} with id ${id} not found`, 'ENTITY_NOT_FOUND', 404);
  }
}

/**
 * Duplicate Entity Error
 * Thrown when trying to create an entity that already exists
 * Status: 409 Conflict
 */
export class DuplicateEntityError extends DomainError {
  constructor(message: string) {
    super(message, 'DUPLICATE_ENTITY', 409);
  }
}

/**
 * Network Error
 * Thrown when network requests fail
 * Status: 500 Internal Server Error
 */
export class NetworkError extends DomainError {
  constructor(message: string = 'Network request failed') {
    super(message, 'NETWORK_ERROR', 500);
  }
}

