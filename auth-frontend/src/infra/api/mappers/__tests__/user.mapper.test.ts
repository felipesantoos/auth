/**
 * User Mapper Tests
 * Tests DTO ↔ Domain transformation
 */

import { describe, it, expect } from 'vitest';
import { UserMapper } from '../user.mapper';
import { User } from '../../../../core/domain/user';
import { UserResponseDTO } from '../../dtos/auth.dto';

describe('UserMapper', () => {
  describe('toDomain', () => {
    it('should map UserResponseDTO to User domain model', () => {
      const dto: UserResponseDTO = {
        id: '123',
        username: 'testuser',
        email: 'test@test.com',
        name: 'Test User',
        role: 'admin',
        active: true,
        client_id: 'client-1',
        created_at: '2024-01-01T00:00:00Z',
      };

      const user = UserMapper.toDomain(dto);

      expect(user).toBeInstanceOf(User);
      expect(user.id).toBe('123');
      expect(user.username).toBe('testuser');
      expect(user.email).toBe('test@test.com');
      expect(user.name).toBe('Test User');
      expect(user.role).toBe('admin');
      expect(user.active).toBe(true);
      expect(user.clientId).toBe('client-1');
      expect(user.createdAt).toBeInstanceOf(Date);
    });

    it('should handle optional client_id', () => {
      const dto: UserResponseDTO = {
        id: '123',
        username: 'testuser',
        email: 'test@test.com',
        name: 'Test User',
        role: 'user',
        active: true,
        created_at: '2024-01-01T00:00:00Z',
      };

      const user = UserMapper.toDomain(dto);

      expect(user.clientId).toBeUndefined();
    });
  });

  describe('toDTO', () => {
    it('should map User domain model to UserResponseDTO', () => {
      const user = new User(
        '123',
        'testuser',
        'test@test.com',
        'Test User',
        'manager',
        true,
        new Date('2024-01-01T00:00:00Z'),
        'client-1'
      );

      const dto = UserMapper.toDTO(user);

      expect(dto.id).toBe('123');
      expect(dto.username).toBe('testuser');
      expect(dto.email).toBe('test@test.com');
      expect(dto.name).toBe('Test User');
      expect(dto.role).toBe('manager');
      expect(dto.active).toBe(true);
      expect(dto.client_id).toBe('client-1');
      expect(dto.created_at).toBe('2024-01-01T00:00:00.000Z');
    });
  });
});
