/**
 * Auth Service Unit Tests
 * Tests business logic in isolation with mocked repository
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AuthService } from '../authService';
import { IAuthRepository } from '../../../interfaces/secondary/IAuthRepository';
import { IStorage } from '../../../interfaces/secondary/IStorage';
import { ILogger } from '../../../interfaces/secondary/ILogger';
import { TokenResponseDTO, UserResponseDTO } from '../../../../infra/api/dtos/auth.dto';

describe('AuthService', () => {
  let authService: AuthService;
  let mockRepository: IAuthRepository;
  let mockStorage: IStorage;
  let mockLogger: ILogger;

  beforeEach(() => {
    // Create mocks
    mockRepository = {
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      getCurrentUser: vi.fn(),
      refreshToken: vi.fn(),
      forgotPassword: vi.fn(),
      resetPassword: vi.fn(),
      changePassword: vi.fn(),
    };

    mockStorage = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    };

    mockLogger = {
      debug: vi.fn(),
      info: vi.fn(),
      warn: vi.fn(),
      error: vi.fn(),
    };

    authService = new AuthService(mockRepository, mockStorage, mockLogger);
  });

  describe('login', () => {
    it('should login successfully and store tokens', async () => {
      const mockUser: UserResponseDTO = {
        id: '123',
        username: 'testuser',
        email: 'test@test.com',
        name: 'Test User',
        role: 'user',
        active: true,
        created_at: '2024-01-01T00:00:00Z',
      };

      const mockResponse: TokenResponseDTO = {
        access_token: 'access-token-123',
        refresh_token: 'refresh-token-123',
        token_type: 'Bearer',
        expires_in: 3600,
        user: mockUser,
      };

      vi.mocked(mockRepository.login).mockResolvedValue(mockResponse);

      const user = await authService.login({
        email: 'test@test.com',
        password: 'password123',
      });

      expect(user.email).toBe('test@test.com');
      expect(user.id).toBe('123');
      expect(mockRepository.login).toHaveBeenCalledWith({
        email: 'test@test.com',
        password: 'password123',
      });
      expect(mockStorage.setItem).toHaveBeenCalledWith('access_token', 'access-token-123');
      expect(mockStorage.setItem).toHaveBeenCalledWith('refresh_token', 'refresh-token-123');
      expect(mockLogger.info).toHaveBeenCalledWith('Login successful', { userId: '123' });
    });

    it('should log error when login fails', async () => {
      const error = new Error('Invalid credentials');
      vi.mocked(mockRepository.login).mockRejectedValue(error);

      await expect(
        authService.login({
          email: 'test@test.com',
          password: 'wrong-password',
        })
      ).rejects.toThrow('Invalid credentials');

      expect(mockLogger.error).toHaveBeenCalled();
    });
  });

  describe('logout', () => {
    it('should logout and clear storage', async () => {
      vi.mocked(mockStorage.getItem).mockReturnValue('refresh-token-123');
      vi.mocked(mockRepository.logout).mockResolvedValue();

      await authService.logout();

      expect(mockRepository.logout).toHaveBeenCalledWith('refresh-token-123');
      expect(mockStorage.removeItem).toHaveBeenCalledWith('access_token');
      expect(mockStorage.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(mockStorage.removeItem).toHaveBeenCalledWith('user');
      expect(mockStorage.removeItem).toHaveBeenCalledWith('client_id');
      expect(mockLogger.info).toHaveBeenCalledWith('Logout successful');
    });

    it('should clear storage even if logout request fails', async () => {
      vi.mocked(mockStorage.getItem).mockReturnValue('refresh-token-123');
      vi.mocked(mockRepository.logout).mockRejectedValue(new Error('Network error'));

      await expect(authService.logout()).rejects.toThrow('Network error');

      expect(mockStorage.removeItem).toHaveBeenCalledWith('access_token');
      expect(mockStorage.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(mockLogger.error).toHaveBeenCalled();
    });
  });

  describe('isAuthenticated', () => {
    it('should return true when access token exists', () => {
      vi.mocked(mockStorage.getItem).mockReturnValue('access-token-123');

      expect(authService.isAuthenticated()).toBe(true);
    });

    it('should return false when access token does not exist', () => {
      vi.mocked(mockStorage.getItem).mockReturnValue(null);

      expect(authService.isAuthenticated()).toBe(false);
    });
  });

  describe('getCurrentUser', () => {
    it('should return null when not authenticated', async () => {
      vi.mocked(mockStorage.getItem).mockReturnValue(null);

      const user = await authService.getCurrentUser();

      expect(user).toBeNull();
      expect(mockRepository.getCurrentUser).not.toHaveBeenCalled();
    });

    it('should fetch and return user when authenticated', async () => {
      const mockUser: UserResponseDTO = {
        id: '123',
        username: 'testuser',
        email: 'test@test.com',
        name: 'Test User',
        role: 'user',
        active: true,
        created_at: '2024-01-01T00:00:00Z',
      };

      vi.mocked(mockStorage.getItem).mockReturnValue('access-token-123');
      vi.mocked(mockRepository.getCurrentUser).mockResolvedValue(mockUser);

      const user = await authService.getCurrentUser();

      expect(user?.email).toBe('test@test.com');
      expect(mockRepository.getCurrentUser).toHaveBeenCalled();
      expect(mockStorage.setItem).toHaveBeenCalled();
    });
  });
});
