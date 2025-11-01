/**
 * Token Domain Model
 * Pure domain entity for authentication tokens
 */

export class Token {
  constructor(
    public readonly accessToken: string,
    public readonly refreshToken: string,
    public readonly tokenType: string,
    public readonly expiresIn: number
  ) {}

  isExpired(): boolean {
    // This would need expiry timestamp logic in real implementation
    return false;
  }

  getBearerToken(): string {
    return `${this.tokenType} ${this.accessToken}`;
  }
}

