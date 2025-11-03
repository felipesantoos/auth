/**
 * Workspaces Page
 * List and manage workspaces
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useWorkspaces } from '../hooks/useWorkspaces';
import { useWorkspace } from '../hooks/useWorkspace';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { WorkspaceList } from '../components/workspace/WorkspaceList';
import { CreateWorkspaceDialog } from '../components/workspace/CreateWorkspaceDialog';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

export const Workspaces: React.FC = () => {
  const navigate = useNavigate();
  const { data: workspacesData, isLoading, refetch } = useWorkspaces();
  const { switchWorkspace } = useWorkspace();

  const handleSelectWorkspace = async (workspace: any) => {
    await switchWorkspace(workspace.id);
    navigate('/dashboard');
  };

  if (isLoading) {
    return <LoadingSpinner message="Carregando workspaces..." />;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Meus Workspaces</CardTitle>
              <CreateWorkspaceDialog onSuccess={() => refetch()} />
            </div>
          </CardHeader>
          <CardContent>
            <WorkspaceList
              workspaces={workspacesData?.workspaces || []}
              onSelectWorkspace={handleSelectWorkspace}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Workspaces;

