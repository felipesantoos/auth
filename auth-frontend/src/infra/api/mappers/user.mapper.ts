/**
 * User Mapper
 * Transforms between API DTOs and Domain Models
 * 
 * Note: Backend still returns 'role' and 'client_id' but we ignore them
 * in the new domain model (roles are now per-workspace)
 */

import { User } from '../../../core/domain/user';
import type { UserResponseDTO } from '../dtos/auth.dto';

export class UserMapper {
  static toDomain(dto: UserResponseDTO): User {
    return new User(
      dto.id,
      dto.username,
      dto.email,
      dto.name,
      dto.active,
      new Date(dto.created_at),
      false, // emailVerified - TODO: add to backend response
      false, // mfaEnabled - TODO: add to backend response
      undefined, // avatarUrl - TODO: add to backend response
      undefined, // kycDocumentId
      undefined, // kycStatus
      undefined  // kycVerifiedAt
    );
  }

  static toDTO(domain: User): UserResponseDTO {
    return {
      id: domain.id,
      username: domain.username,
      email: domain.email,
      name: domain.name,
      role: 'user', // Deprecated - keeping for backward compatibility
      active: domain.active,
      created_at: domain.createdAt.toISOString(),
      client_id: undefined, // Deprecated - now via workspace
    };
  }
}

