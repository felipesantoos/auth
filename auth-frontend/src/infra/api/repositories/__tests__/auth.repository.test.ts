/**
 * AuthRepository Integration Tests
 * Tests for AuthRepository with mocked HTTP client
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AuthRepository } from '../auth.repository';
import { IHttpClient } from '../../../../core/interfaces/secondary/IHttpClient';
import { TokenResponseDTO, UserResponseDTO } from '../../dtos/auth.dto';

describe('AuthRepository', () => {
  let authRepository: AuthRepository;
  let mockHttpClient: IHttpClient;

  const mockUserDTO: UserResponseDTO = {
    id: '123',
    username: 'testuser',
    email: 'test@example.com',
    name: 'Test User',
    role: 'user',
    active: true,
    created_at: '2024-01-01T00:00:00Z',
    client_id: 'client-1',
  };

  const mockTokenResponse: TokenResponseDTO = {
    access_token: 'mock-access-token',
    refresh_token: 'mock-refresh-token',
    token_type: 'Bearer',
    expires_in: 3600,
    user: mockUserDTO,
  };

  beforeEach(() => {
    mockHttpClient = {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      patch: vi.fn(),
    };

    authRepository = new AuthRepository(mockHttpClient);
  });

  describe('login', () => {
    it('deve fazer login e retornar token response', async () => {
      mockHttpClient.post = vi.fn().mockResolvedValue(mockTokenResponse);

      const credentials = {
        email: 'test@example.com',
        password: 'Password123',
      };

      const result = await authRepository.login(credentials);

      expect(mockHttpClient.post).toHaveBeenCalledWith('/api/auth/login', credentials);
      expect(result).toEqual(mockTokenResponse);
      expect(result.user.email).toBe('test@example.com');
    });
  });

  describe('register', () => {
    it('deve registrar usuário e retornar token response', async () => {
      mockHttpClient.post = vi.fn().mockResolvedValue(mockTokenResponse);

      const registerData = {
        username: 'newuser',
        email: 'new@example.com',
        password: 'Password123',
        name: 'New User',
      };

      const result = await authRepository.register(registerData);

      expect(mockHttpClient.post).toHaveBeenCalledWith('/api/auth/register', registerData);
      expect(result).toEqual(mockTokenResponse);
    });
  });

  describe('getCurrentUser', () => {
    it('deve buscar usuário atual', async () => {
      mockHttpClient.get = vi.fn().mockResolvedValue(mockUserDTO);

      const result = await authRepository.getCurrentUser();

      expect(mockHttpClient.get).toHaveBeenCalledWith('/api/auth/me');
      expect(result).toEqual(mockUserDTO);
    });
  });

  describe('logout', () => {
    it('deve fazer logout com refresh token', async () => {
      mockHttpClient.post = vi.fn().mockResolvedValue(undefined);

      await authRepository.logout('mock-refresh-token');

      expect(mockHttpClient.post).toHaveBeenCalledWith('/api/auth/logout', {
        refresh_token: 'mock-refresh-token',
      });
    });
  });

  describe('refreshToken', () => {
    it('deve atualizar token com sucesso', async () => {
      mockHttpClient.post = vi.fn().mockResolvedValue(mockTokenResponse);

      const result = await authRepository.refreshToken('mock-refresh-token');

      expect(mockHttpClient.post).toHaveBeenCalledWith('/api/auth/refresh', {
        refresh_token: 'mock-refresh-token',
      });
      expect(result).toEqual(mockTokenResponse);
    });
  });

  describe('forgotPassword', () => {
    it('deve enviar email de recuperação', async () => {
      const mockResponse = { message: 'Email sent' };
      mockHttpClient.post = vi.fn().mockResolvedValue(mockResponse);

      const result = await authRepository.forgotPassword({ email: 'test@example.com' });

      expect(mockHttpClient.post).toHaveBeenCalledWith('/api/auth/forgot-password', {
        email: 'test@example.com',
      });
      expect(result.message).toBe('Email sent');
    });
  });

  describe('resetPassword', () => {
    it('deve redefinir senha com token', async () => {
      const mockResponse = { message: 'Password reset successfully' };
      mockHttpClient.post = vi.fn().mockResolvedValue(mockResponse);

      const result = await authRepository.resetPassword({
        reset_token: 'token123',
        new_password: 'NewPassword123',
      });

      expect(mockHttpClient.post).toHaveBeenCalledWith('/api/auth/reset-password', {
        reset_token: 'token123',
        new_password: 'NewPassword123',
      });
      expect(result.message).toBe('Password reset successfully');
    });
  });
});

