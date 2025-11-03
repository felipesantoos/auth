/**
 * useWorkspaces Hook
 * React Query hooks for workspace CRUD operations
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import DIContainer from '../dicontainer/container';
import type {
  CreateWorkspaceRequest,
  UpdateWorkspaceRequest,
  AddMemberRequest,
  UpdateMemberRoleRequest,
} from '../../core/domain/workspace';

const workspaceService = DIContainer.getWorkspaceService();

/**
 * Query key factory
 */
export const workspaceKeys = {
  all: ['workspaces'] as const,
  lists: () => [...workspaceKeys.all, 'list'] as const,
  list: (filters: string) => [...workspaceKeys.lists(), { filters }] as const,
  details: () => [...workspaceKeys.all, 'detail'] as const,
  detail: (id: string) => [...workspaceKeys.details(), id] as const,
  members: (id: string) => [...workspaceKeys.detail(id), 'members'] as const,
};

/**
 * List workspaces
 */
export const useWorkspaces = (activeOnly: boolean = true) => {
  return useQuery({
    queryKey: workspaceKeys.list(activeOnly ? 'active' : 'all'),
    queryFn: () => workspaceService.listWorkspaces(activeOnly),
  });
};

/**
 * Get workspace by ID
 */
export const useWorkspace = (workspaceId: string | null) => {
  return useQuery({
    queryKey: workspaceKeys.detail(workspaceId || ''),
    queryFn: () => workspaceService.getWorkspace(workspaceId!),
    enabled: !!workspaceId,
  });
};

/**
 * Get workspace members
 */
export const useWorkspaceMembers = (workspaceId: string | null, activeOnly: boolean = true) => {
  return useQuery({
    queryKey: [...workspaceKeys.members(workspaceId || ''), activeOnly],
    queryFn: () => workspaceService.listMembers(workspaceId!, activeOnly),
    enabled: !!workspaceId,
  });
};

/**
 * Create workspace
 */
export const useCreateWorkspace = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: CreateWorkspaceRequest) =>
      workspaceService.createWorkspace(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() });
    },
  });
};

/**
 * Update workspace
 */
export const useUpdateWorkspace = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ workspaceId, request }: { workspaceId: string; request: UpdateWorkspaceRequest }) =>
      workspaceService.updateWorkspace(workspaceId, request),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.detail(variables.workspaceId) });
      queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() });
    },
  });
};

/**
 * Delete workspace
 */
export const useDeleteWorkspace = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (workspaceId: string) =>
      workspaceService.deleteWorkspace(workspaceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() });
    },
  });
};

/**
 * Add member to workspace
 */
export const useAddMember = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ workspaceId, request }: { workspaceId: string; request: AddMemberRequest }) =>
      workspaceService.addMember(workspaceId, request),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.members(variables.workspaceId) });
    },
  });
};

/**
 * Update member role
 */
export const useUpdateMemberRole = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      workspaceId,
      userId,
      request,
    }: {
      workspaceId: string;
      userId: string;
      request: UpdateMemberRoleRequest;
    }) => workspaceService.updateMemberRole(workspaceId, userId, request),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.members(variables.workspaceId) });
    },
  });
};

/**
 * Remove member from workspace
 */
export const useRemoveMember = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ workspaceId, userId }: { workspaceId: string; userId: string }) =>
      workspaceService.removeMember(workspaceId, userId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.members(variables.workspaceId) });
    },
  });
};

/**
 * Leave workspace
 */
export const useLeaveWorkspace = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (workspaceId: string) =>
      workspaceService.leaveWorkspace(workspaceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() });
    },
  });
};

