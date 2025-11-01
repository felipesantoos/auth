/**
 * Token Mapper
 * Transforms between API DTOs and Domain Models
 */

import { Token } from '../../../core/domain/token';
import { TokenResponseDTO } from '../dtos/auth.dto';

export class TokenMapper {
  static toDomain(dto: TokenResponseDTO): Token {
    return new Token(
      dto.access_token,
      dto.refresh_token,
      dto.token_type,
      dto.expires_in
    );
  }
}

