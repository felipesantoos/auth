/**
 * Permissions Page
 * Manage user permissions
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useUserPermissions, useRevokePermission } from '../hooks/usePermissions';
import { useAuth } from '../contexts/AuthContext';
import { useWorkspace } from '../hooks/useWorkspace';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { PermissionsList } from '../components/permissions/PermissionsList';
import { GrantPermissionDialog } from '../components/permissions/GrantPermissionDialog';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

export const Permissions: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { canManageWorkspace } = useWorkspace();
  const { data: permissions, isLoading, refetch } = useUserPermissions(user?.id || null);
  const revokeMutation = useRevokePermission();

  const handleRevokePermission = async (permissionId: string) => {
    if (!user) return;

    if (!confirm('Tem certeza que deseja revogar esta permissão?')) return;

    try {
      await revokeMutation.mutateAsync({ permissionId, userId: user.id });
      refetch();
    } catch (error) {
      console.error('Error revoking permission:', error);
    }
  };

  if (isLoading) {
    return <LoadingSpinner message="Carregando permissões..." />;
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
            <GrantPermissionDialog onSuccess={() => refetch()} />
          )}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Minhas Permissões</CardTitle>
          </CardHeader>
          <CardContent>
            <PermissionsList
              permissions={permissions || []}
              canManage={canManageWorkspace()}
              onRevokePermission={handleRevokePermission}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Permissions;

