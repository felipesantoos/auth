/**
 * Workspace List Component
 * Display list of user's workspaces
 */

import React from 'react';
import { Building2, Users, Settings } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Workspace } from '../../../core/domain/workspace';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';

interface WorkspaceListProps {
  workspaces: Workspace[];
  onSelectWorkspace?: (workspace: Workspace) => void;
}

export const WorkspaceList: React.FC<WorkspaceListProps> = ({
  workspaces,
  onSelectWorkspace,
}) => {
  const navigate = useNavigate();

  if (workspaces.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <Building2 className="h-12 w-12 text-slate-400 mx-auto mb-4" />
          <p className="text-slate-500">Você ainda não faz parte de nenhum workspace.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {workspaces.map((workspace) => (
        <Card
          key={workspace.id}
          className="hover:shadow-md transition-shadow cursor-pointer"
          onClick={() => onSelectWorkspace?.(workspace)}
        >
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <Building2 className="h-5 w-5 text-blue-600" />
                <CardTitle className="text-lg">{workspace.name}</CardTitle>
              </div>
              {workspace.active ? (
                <Badge variant="default" className="bg-green-500">Ativo</Badge>
              ) : (
                <Badge variant="secondary">Inativo</Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-500 mb-4">
              {workspace.description || 'Sem descrição'}
            </p>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className="font-mono bg-slate-100 px-2 py-1 rounded">
                {workspace.slug}
              </span>
            </div>
            <div className="flex items-center justify-between mt-4">
              <Button
                size="sm"
                variant="ghost"
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/workspaces/${workspace.id}/members`);
                }}
              >
                <Users className="h-4 w-4 mr-1" />
                Membros
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/workspaces/${workspace.id}/settings`);
                }}
              >
                <Settings className="h-4 w-4 mr-1" />
                Config
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

