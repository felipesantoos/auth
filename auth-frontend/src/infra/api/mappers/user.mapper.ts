/**
 * User Mapper
 * Transforms between API DTOs and Domain Models
 */

import { User, UserRole } from '../../../core/domain/user';
import { UserResponseDTO } from '../dtos/auth.dto';

export class UserMapper {
  static toDomain(dto: UserResponseDTO): User {
    return new User(
      dto.id,
      dto.username,
      dto.email,
      dto.name,
      dto.role as UserRole,
      dto.active,
      new Date(dto.created_at),
      dto.client_id
    );
  }

  static toDTO(domain: User): UserResponseDTO {
    return {
      id: domain.id,
      username: domain.username,
      email: domain.email,
      name: domain.name,
      role: domain.role,
      active: domain.active,
      created_at: domain.createdAt.toISOString(),
      client_id: domain.clientId,
    };
  }
}

