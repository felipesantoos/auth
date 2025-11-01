/**
 * Storage Interface (Secondary Port)
 * Defines the contract for local storage operations
 */

export interface IStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
  clear(): void;
}

