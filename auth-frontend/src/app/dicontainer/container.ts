/**
 * Dependency Injection Container
 * Manages all service instances and their dependencies
 */

import { IAuthService } from '../../core/interfaces/primary/IAuthService';
import { IAuthRepository } from '../../core/interfaces/secondary/IAuthRepository';
import { IAuditService } from '../../core/interfaces/primary/IAuditService';
import { IAuditLogRepository } from '../../core/interfaces/secondary/IAuditLogRepository';
import { IWorkspaceService } from '../../core/interfaces/primary/IWorkspaceService';
import { IWorkspaceRepository } from '../../core/interfaces/secondary/IWorkspaceRepository';
import { IPermissionService } from '../../core/interfaces/primary/IPermissionService';
import { IPermissionRepository } from '../../core/interfaces/secondary/IPermissionRepository';
import { IHttpClient } from '../../core/interfaces/secondary/IHttpClient';
import { IStorage } from '../../core/interfaces/secondary/IStorage';
import { ILogger } from '../../core/interfaces/secondary/ILogger';

import { AuthService } from '../../core/services/auth/authService';
import { AuthRepository } from '../../infra/api/repositories/auth.repository';
import { AuditService } from '../../core/services/audit/auditService';
import { auditLogRepository } from '../../infra/api/repositories/audit.repository';
import { WorkspaceService } from '../../core/services/workspace/workspaceService';
import { WorkspaceRepository } from '../../infra/api/repositories/workspace.repository';
import { PermissionService } from '../../core/services/permission/permissionService';
import { PermissionRepository } from '../../infra/api/repositories/permission.repository';
import { HttpClient } from '../../infra/api/http-client';
import { LocalStorage } from '../../infra/storage/local-storage';
import { ConsoleLogger } from '../../infra/logger/console-logger';

class DIContainer {
  private static instances = new Map<string, any>();
  private static httpClient: IHttpClient;
  private static storage: IStorage;
  private static logger: ILogger;

  static init(baseURL: string): void {
    this.httpClient = new HttpClient(baseURL);
    this.storage = new LocalStorage();
    this.logger = new ConsoleLogger();

    this.logger.info('DI Container initialized', { baseURL });
  }

  static getHttpClient(): IHttpClient {
    if (!this.httpClient) {
      throw new Error('DIContainer not initialized. Call DIContainer.init() first.');
    }
    return this.httpClient;
  }

  static getStorage(): IStorage {
    if (!this.storage) {
      throw new Error('DIContainer not initialized. Call DIContainer.init() first.');
    }
    return this.storage;
  }

  static getLogger(): ILogger {
    if (!this.logger) {
      throw new Error('DIContainer not initialized. Call DIContainer.init() first.');
    }
    return this.logger;
  }

  static getAuthRepository(): IAuthRepository {
    if (!this.instances.has('authRepository')) {
      const httpClient = this.getHttpClient();
      this.instances.set('authRepository', new AuthRepository(httpClient));
    }
    return this.instances.get('authRepository');
  }

  static getAuthService(): IAuthService {
    if (!this.instances.has('authService')) {
      const repository = this.getAuthRepository();
      const storage = this.getStorage();
      const logger = this.getLogger();
      this.instances.set('authService', new AuthService(repository, storage, logger));
    }
    return this.instances.get('authService');
  }

  static getAuditService(): IAuditService {
    if (!this.instances.has('auditService')) {
      this.instances.set('auditService', new AuditService(auditLogRepository));
    }
    return this.instances.get('auditService');
  }

  static getWorkspaceRepository(): IWorkspaceRepository {
    if (!this.instances.has('workspaceRepository')) {
      this.instances.set('workspaceRepository', new WorkspaceRepository());
    }
    return this.instances.get('workspaceRepository');
  }

  static getWorkspaceService(): IWorkspaceService {
    if (!this.instances.has('workspaceService')) {
      const repository = this.getWorkspaceRepository();
      this.instances.set('workspaceService', new WorkspaceService(repository));
    }
    return this.instances.get('workspaceService');
  }

  static getPermissionRepository(): IPermissionRepository {
    if (!this.instances.has('permissionRepository')) {
      this.instances.set('permissionRepository', new PermissionRepository());
    }
    return this.instances.get('permissionRepository');
  }

  static getPermissionService(): IPermissionService {
    if (!this.instances.has('permissionService')) {
      const repository = this.getPermissionRepository();
      this.instances.set('permissionService', new PermissionService(repository));
    }
    return this.instances.get('permissionService');
  }

  static reset(): void {
    this.instances.clear();
    this.logger?.info('DI Container reset');
  }
}

export default DIContainer;

