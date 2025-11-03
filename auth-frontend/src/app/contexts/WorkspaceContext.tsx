/**
 * Workspace Context
 * Global state management for workspaces
 */

import React, { createContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { Workspace, WorkspaceMember } from '../../core/domain/workspace';
import DIContainer from '../dicontainer/container';

interface WorkspaceContextType {
  // Current active workspace
  activeWorkspace: Workspace | null;
  setActiveWorkspace: (workspace: Workspace | null) => void;
  
  // User's workspaces
  workspaces: Workspace[];
  setWorkspaces: (workspaces: Workspace[]) => void;
  
  // User's workspace memberships
  memberships: WorkspaceMember[];
  setMemberships: (memberships: WorkspaceMember[]) => void;
  
  // Current user's role in active workspace
  currentRole: 'admin' | 'manager' | 'user' | null;
  
  // Loading states
  loading: boolean;
  
  // Helper functions
  isWorkspaceAdmin: () => boolean;
  isWorkspaceManager: () => boolean;
  canManageWorkspace: () => boolean;
  
  // Actions
  refreshWorkspaces: () => Promise<void>;
  switchWorkspace: (workspaceId: string) => Promise<void>;
}

export const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

interface WorkspaceProviderProps {
  children: ReactNode;
}

const STORAGE_KEY = 'active_workspace';

export const WorkspaceProvider: React.FC<WorkspaceProviderProps> = ({ children }) => {
  const [activeWorkspace, setActiveWorkspaceState] = useState<Workspace | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [memberships, setMemberships] = useState<WorkspaceMember[]>([]);
  const [currentRole, setCurrentRole] = useState<'admin' | 'manager' | 'user' | null>(null);
  const [loading, setLoading] = useState(true);

  const workspaceService = DIContainer.getWorkspaceService();

  /**
   * Set active workspace and persist to localStorage
   */
  const setActiveWorkspace = useCallback((workspace: Workspace | null) => {
    setActiveWorkspaceState(workspace);
    
    if (workspace) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(workspace));
      
      // Find and set current role
      const membership = memberships.find(m => m.workspace_id === workspace.id);
      setCurrentRole(membership?.role || null);
    } else {
      localStorage.removeItem(STORAGE_KEY);
      setCurrentRole(null);
    }
  }, [memberships]);

  /**
   * Load workspaces from API
   */
  const refreshWorkspaces = useCallback(async () => {
    try {
      setLoading(true);
      const response = await workspaceService.listWorkspaces(true);
      setWorkspaces(response.workspaces);
      
      // If no active workspace, set the first one
      if (!activeWorkspace && response.workspaces.length > 0) {
        setActiveWorkspace(response.workspaces[0]);
      }
    } catch (error) {
      console.error('Error loading workspaces:', error);
    } finally {
      setLoading(false);
    }
  }, [workspaceService, activeWorkspace, setActiveWorkspace]);

  /**
   * Switch to a different workspace
   */
  const switchWorkspace = useCallback(async (workspaceId: string) => {
    try {
      const workspace = workspaces.find(w => w.id === workspaceId);
      if (workspace) {
        setActiveWorkspace(workspace);
      } else {
        // Fetch workspace if not in list
        const fetchedWorkspace = await workspaceService.getWorkspace(workspaceId);
        setActiveWorkspace(fetchedWorkspace);
      }
    } catch (error) {
      console.error('Error switching workspace:', error);
      throw error;
    }
  }, [workspaces, workspaceService, setActiveWorkspace]);

  /**
   * Check if current user is admin in active workspace
   */
  const isWorkspaceAdmin = useCallback(() => {
    return currentRole === 'admin';
  }, [currentRole]);

  /**
   * Check if current user is manager in active workspace
   */
  const isWorkspaceManager = useCallback(() => {
    return currentRole === 'manager';
  }, [currentRole]);

  /**
   * Check if current user can manage active workspace (admin or manager)
   */
  const canManageWorkspace = useCallback(() => {
    return currentRole === 'admin' || currentRole === 'manager';
  }, [currentRole]);

  /**
   * Load active workspace from localStorage on mount
   */
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const workspace = JSON.parse(stored);
        setActiveWorkspaceState(workspace);
      } catch (error) {
        console.error('Error loading workspace from storage:', error);
      }
    }
  }, []);

  /**
   * Update current role when active workspace or memberships change
   */
  useEffect(() => {
    if (activeWorkspace) {
      const membership = memberships.find(m => m.workspace_id === activeWorkspace.id);
      setCurrentRole(membership?.role || null);
    } else {
      setCurrentRole(null);
    }
  }, [activeWorkspace, memberships]);

  const value: WorkspaceContextType = {
    activeWorkspace,
    setActiveWorkspace,
    workspaces,
    setWorkspaces,
    memberships,
    setMemberships,
    currentRole,
    loading,
    isWorkspaceAdmin,
    isWorkspaceManager,
    canManageWorkspace,
    refreshWorkspaces,
    switchWorkspace,
  };

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  );
};

