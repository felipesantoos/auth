/**
 * User Domain Model Tests
 * Tests business logic in domain entities
 */

import { describe, it, expect } from 'vitest';
import { User } from '../user';

describe('User Domain Model', () => {
  describe('isAdmin', () => {
    it('should return true for admin users', () => {
      const user = new User(
        '1',
        'admin',
        'admin@test.com',
        'Admin User',
        'admin',
        true,
        new Date()
      );

      expect(user.isAdmin()).toBe(true);
    });

    it('should return false for non-admin users', () => {
      const user = new User(
        '1',
        'user',
        'user@test.com',
        'Regular User',
        'user',
        true,
        new Date()
      );

      expect(user.isAdmin()).toBe(false);
    });
  });

  describe('isManager', () => {
    it('should return true for manager users', () => {
      const user = new User(
        '1',
        'manager',
        'manager@test.com',
        'Manager User',
        'manager',
        true,
        new Date()
      );

      expect(user.isManager()).toBe(true);
    });

    it('should return false for non-manager users', () => {
      const user = new User(
        '1',
        'user',
        'user@test.com',
        'Regular User',
        'user',
        true,
        new Date()
      );

      expect(user.isManager()).toBe(false);
    });
  });

  describe('canManage', () => {
    it('should return true for admin users', () => {
      const user = new User(
        '1',
        'admin',
        'admin@test.com',
        'Admin User',
        'admin',
        true,
        new Date()
      );

      expect(user.canManage('projects')).toBe(true);
    });

    it('should return true for manager users', () => {
      const user = new User(
        '1',
        'manager',
        'manager@test.com',
        'Manager User',
        'manager',
        true,
        new Date()
      );

      expect(user.canManage('projects')).toBe(true);
    });

    it('should return false for regular users', () => {
      const user = new User(
        '1',
        'user',
        'user@test.com',
        'Regular User',
        'user',
        true,
        new Date()
      );

      expect(user.canManage('projects')).toBe(false);
    });
  });
});

