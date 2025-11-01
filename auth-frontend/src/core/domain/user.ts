/**
 * User Domain Model
 * Pure domain entity - no DTOs or API concerns
 */

export type UserRole = 'admin' | 'manager' | 'user';

export class User {
  constructor(
    public readonly id: string,
    public readonly username: string,
    public readonly email: string,
    public readonly name: string,
    public readonly role: UserRole,
    public readonly active: boolean,
    public readonly createdAt: Date,
    public readonly clientId?: string
  ) {}

  isAdmin(): boolean {
    return this.role === 'admin';
  }

  isManager(): boolean {
    return this.role === 'manager';
  }

  canManage(resource: string): boolean {
    return this.isAdmin() || this.isManager();
  }
}

