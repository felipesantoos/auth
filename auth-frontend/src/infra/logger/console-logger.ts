/**
 * Console Logger Implementation
 * Browser console implementation of ILogger
 */

import { ILogger, LogLevel } from '../../core/interfaces/secondary/ILogger';

export class ConsoleLogger implements ILogger {
  private isDevelopment: boolean;

  constructor() {
    this.isDevelopment = import.meta.env.MODE === 'development';
  }

  debug(message: string, ...args: any[]): void {
    if (this.isDevelopment) {
      console.debug(`[DEBUG] ${message}`, ...args);
    }
  }

  info(message: string, ...args: any[]): void {
    console.info(`[INFO] ${message}`, ...args);
  }

  warn(message: string, ...args: any[]): void {
    console.warn(`[WARN] ${message}`, ...args);
  }

  error(message: string, error?: Error, ...args: any[]): void {
    console.error(`[ERROR] ${message}`, error, ...args);
  }
}

// Export singleton instance
export const logger = new ConsoleLogger();

