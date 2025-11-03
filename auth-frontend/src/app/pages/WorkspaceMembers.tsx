/**
 * Workspace Members Page
 * Manage workspace members
 */

import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useWorkspaceMembers, useUpdateMemberRole, useRemoveMember } from '../hooks/useWorkspaces';
import { useWorkspace } from '../hooks/useWorkspace';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { WorkspaceMembersList } from '../components/workspace/WorkspaceMembersList';
import { InviteMemberDialog } from '../components/workspace/InviteMemberDialog';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

export const WorkspaceMembers: React.FC = () => {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { canManageWorkspace } = useWorkspace();
  const { data: membersData, isLoading, refetch } = useWorkspaceMembers(workspaceId || null);
  const updateRoleMutation = useUpdateMemberRole();
  const removeMemberMutation = useRemoveMember();

  const handleUpdateRole = async (userId: string, newRole: 'admin' | 'manager' | 'user') => {
    if (!workspaceId) return;

    try {
      await updateRoleMutation.mutateAsync({
        workspaceId,
        userId,
        request: { role: newRole },
      });
      refetch();
    } catch (error) {
      console.error('Error updating role:', error);
    }
  };

  const handleRemoveMember = async (userId: string) => {
    if (!workspaceId) return;

    if (!confirm('Tem certeza que deseja remover este membro?')) return;

    try {
      await removeMemberMutation.mutateAsync({ workspaceId, userId });
      refetch();
    } catch (error) {
      console.error('Error removing member:', error);
    }
  };

  if (isLoading) {
    return <LoadingSpinner message="Carregando membros..." />;
  }

  if (!membersData) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <p>Nenhum membro encontrado</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="mb-6 flex items-center justify-between">
          <Button variant="ghost" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Voltar
          </Button>
          {canManageWorkspace() && (
            <InviteMemberDialog workspaceId={workspaceId!} onSuccess={() => refetch()} />
          )}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Membros do Workspace</CardTitle>
          </CardHeader>
          <CardContent>
            <WorkspaceMembersList
              members={membersData.members}
              currentUserId={user?.id || ''}
              canManage={canManageWorkspace()}
              onUpdateRole={handleUpdateRole}
              onRemoveMember={handleRemoveMember}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default WorkspaceMembers;

