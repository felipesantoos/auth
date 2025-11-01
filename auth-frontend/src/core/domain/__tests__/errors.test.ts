/**
 * Custom Error Classes Tests
 * Verifies error classes have correct properties
 * 
 * Compliance: 08c-react-best-practices.md Section 5.2
 */

import { describe, it, expect } from 'vitest';
import {
  DomainError,
  AuthenticationError,
  BusinessValidationError,
  AuthorizationError,
  EntityNotFoundError,
  DuplicateEntityError,
  NetworkError,
} from '../errors';

describe('Custom Error Classes', () => {
  describe('DomainError', () => {
    it('should create error with correct properties', () => {
      const error = new DomainError('Test message', 'TEST_ERROR', 400);

      expect(error.message).toBe('Test message');
      expect(error.code).toBe('TEST_ERROR');
      expect(error.statusCode).toBe(400);
      expect(error.name).toBe('DomainError');
      expect(error instanceof Error).toBe(true);
    });
  });

  describe('AuthenticationError', () => {
    it('should create authentication error with correct properties', () => {
      const error = new AuthenticationError('Invalid credentials');

      expect(error.message).toBe('Invalid credentials');
      expect(error.code).toBe('AUTHENTICATION_ERROR');
      expect(error.statusCode).toBe(401);
      expect(error.name).toBe('AuthenticationError');
      expect(error instanceof DomainError).toBe(true);
    });

    it('should use default message if not provided', () => {
      const error = new AuthenticationError();

      expect(error.message).toBe('Authentication failed');
      expect(error.code).toBe('AUTHENTICATION_ERROR');
      expect(error.statusCode).toBe(401);
    });
  });

  describe('BusinessValidationError', () => {
    it('should create validation error with correct properties', () => {
      const error = new BusinessValidationError('Name is required');

      expect(error.message).toBe('Name is required');
      expect(error.code).toBe('BUSINESS_VALIDATION_ERROR');
      expect(error.statusCode).toBe(400);
      expect(error.name).toBe('BusinessValidationError');
    });
  });

  describe('AuthorizationError', () => {
    it('should create authorization error with correct properties', () => {
      const error = new AuthorizationError('Access denied');

      expect(error.message).toBe('Access denied');
      expect(error.code).toBe('AUTHORIZATION_ERROR');
      expect(error.statusCode).toBe(403);
    });

    it('should use default message if not provided', () => {
      const error = new AuthorizationError();

      expect(error.message).toBe('Insufficient permissions');
    });
  });

  describe('EntityNotFoundError', () => {
    it('should create not found error with entity name and id', () => {
      const error = new EntityNotFoundError('User', '123');

      expect(error.message).toBe('User with id 123 not found');
      expect(error.code).toBe('ENTITY_NOT_FOUND');
      expect(error.statusCode).toBe(404);
    });
  });

  describe('DuplicateEntityError', () => {
    it('should create duplicate error with correct properties', () => {
      const error = new DuplicateEntityError('Email already exists');

      expect(error.message).toBe('Email already exists');
      expect(error.code).toBe('DUPLICATE_ENTITY');
      expect(error.statusCode).toBe(409);
    });
  });

  describe('NetworkError', () => {
    it('should create network error with correct properties', () => {
      const error = new NetworkError('Connection timeout');

      expect(error.message).toBe('Connection timeout');
      expect(error.code).toBe('NETWORK_ERROR');
      expect(error.statusCode).toBe(500);
    });

    it('should use default message if not provided', () => {
      const error = new NetworkError();

      expect(error.message).toBe('Network request failed');
    });
  });

  describe('instanceof checks', () => {
    it('should work with instanceof operator', () => {
      const authError = new AuthenticationError();
      const validationError = new BusinessValidationError('Test');
      const notFoundError = new EntityNotFoundError('User', '1');

      expect(authError instanceof AuthenticationError).toBe(true);
      expect(authError instanceof DomainError).toBe(true);
      expect(authError instanceof Error).toBe(true);

      expect(validationError instanceof BusinessValidationError).toBe(true);
      expect(validationError instanceof DomainError).toBe(true);

      expect(notFoundError instanceof EntityNotFoundError).toBe(true);
      expect(notFoundError instanceof DomainError).toBe(true);

      // Should not be instance of unrelated error
      expect(authError instanceof BusinessValidationError).toBe(false);
    });
  });
});

