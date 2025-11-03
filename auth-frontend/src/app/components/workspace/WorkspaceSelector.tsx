/**
 * Workspace Selector Component
 * Dropdown to select active workspace
 */

import React from 'react';
import { Check, ChevronsUpDown, Building2 } from 'lucide-react';
import { useWorkspace } from '../../hooks/useWorkspace';
import { Button } from '../ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';

export const WorkspaceSelector: React.FC = () => {
  const { activeWorkspace, workspaces, switchWorkspace } = useWorkspace();

  if (workspaces.length === 0) {
    return null;
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="flex items-center gap-2">
          <Building2 className="h-4 w-4" />
          <span>{activeWorkspace?.name || 'Selecione um workspace'}</span>
          <ChevronsUpDown className="h-4 w-4 opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-[250px]">
        <DropdownMenuLabel>Workspaces</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {workspaces.map((workspace) => (
          <DropdownMenuItem
            key={workspace.id}
            onClick={() => switchWorkspace(workspace.id)}
            className="flex items-center justify-between cursor-pointer"
          >
            <div className="flex flex-col">
              <span className="font-medium">{workspace.name}</span>
              <span className="text-xs text-slate-500">{workspace.slug}</span>
            </div>
            {activeWorkspace?.id === workspace.id && (
              <Check className="h-4 w-4 text-blue-600" />
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

