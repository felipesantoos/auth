/**
 * usePermissions Hook
 * React Query hooks for permission operations
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import DIContainer from '../dicontainer/container';
import {
  GrantPermissionRequest,
  PermissionAction,
} from '../../core/domain/permission';

const permissionService = DIContainer.getPermissionService();

/**
 * Query key factory
 */
export const permissionKeys = {
  all: ['permissions'] as const,
  lists: () => [...permissionKeys.all, 'list'] as const,
  list: (userId: string) => [...permissionKeys.lists(), userId] as const,
};

/**
 * List user permissions
 */
export const useUserPermissions = (userId: string | null) => {
  return useQuery({
    queryKey: permissionKeys.list(userId || ''),
    queryFn: () => permissionService.listUserPermissions(userId!),
    enabled: !!userId,
  });
};

/**
 * Grant permission
 */
export const useGrantPermission = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: GrantPermissionRequest) =>
      permissionService.grantPermission(request),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: permissionKeys.list(variables.user_id) });
    },
  });
};

/**
 * Revoke permission
 */
export const useRevokePermission = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ permissionId, userId }: { permissionId: string; userId: string }) =>
      permissionService.revokePermission(permissionId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: permissionKeys.list(variables.userId) });
    },
  });
};

/**
 * Check if user has permission
 */
export const useHasPermission = (
  userId: string | null,
  resourceType: string,
  action: PermissionAction,
  resourceId?: string
) => {
  return useQuery({
    queryKey: [...permissionKeys.list(userId || ''), 'check', resourceType, action, resourceId],
    queryFn: () => permissionService.hasPermission(userId!, resourceType, action, resourceId),
    enabled: !!userId && !!resourceType && !!action,
  });
};

/**
 * Check if user can manage resource
 */
export const useCanManageResource = (
  userId: string | null,
  resourceType: string,
  resourceId?: string
) => {
  return useHasPermission(userId, resourceType, 'manage', resourceId);
};

