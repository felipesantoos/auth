/**
 * Workspace Members List Component
 * Display and manage workspace members
 */

import React from 'react';
import { Shield, Trash2 } from 'lucide-react';
import type { WorkspaceMember } from '../../../core/domain/workspace';
import { DataTable } from '../common/DataTable';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';

interface WorkspaceMembersListProps {
  members: WorkspaceMember[];
  currentUserId: string;
  canManage: boolean;
  onUpdateRole?: (userId: string, newRole: 'admin' | 'manager' | 'user') => void;
  onRemoveMember?: (userId: string) => void;
}

export const WorkspaceMembersList: React.FC<WorkspaceMembersListProps> = ({
  members,
  currentUserId,
  canManage,
  onUpdateRole,
  onRemoveMember,
}) => {
  const getRoleBadge = (role: string) => {
    const colors = {
      admin: 'bg-purple-100 text-purple-800',
      manager: 'bg-blue-100 text-blue-800',
      user: 'bg-slate-100 text-slate-800',
    };

    return (
      <Badge className={colors[role as keyof typeof colors] || colors.user}>
        {role.toUpperCase()}
      </Badge>
    );
  };

  const columns = [
    {
      accessorKey: 'user_id',
      header: 'Usuário ID',
      cell: (row: WorkspaceMember) => (
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm">{row.user_id.substring(0, 8)}...</span>
          {row.user_id === currentUserId && (
            <Badge variant="outline" className="text-xs">Você</Badge>
          )}
        </div>
      ),
    },
    {
      accessorKey: 'role',
      header: 'Role',
      cell: (row: WorkspaceMember) => getRoleBadge(row.role),
    },
    {
      accessorKey: 'active',
      header: 'Status',
      cell: (row: WorkspaceMember) => (
        row.active ? (
          <Badge className="bg-green-500">Ativo</Badge>
        ) : (
          <Badge variant="secondary">Inativo</Badge>
        )
      ),
    },
    {
      accessorKey: 'joined_at',
      header: 'Entrou em',
      cell: (row: WorkspaceMember) => (
        row.joined_at
          ? new Date(row.joined_at).toLocaleDateString('pt-BR')
          : 'Não entrou'
      ),
    },
    {
      accessorKey: 'actions',
      header: 'Ações',
      cell: (row: WorkspaceMember) => {
        if (!canManage || row.user_id === currentUserId) {
          return <span className="text-slate-400 text-sm">-</span>;
        }

        return (
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onUpdateRole?.(row.user_id, 'admin')}
              title="Tornar Admin"
            >
              <Shield className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onRemoveMember?.(row.user_id)}
            >
              <Trash2 className="h-4 w-4 text-red-500" />
            </Button>
          </div>
        );
      },
    },
  ];

  return (
    <div>
      <div className="mb-4">
        <h3 className="text-lg font-semibold">Membros ({members.length})</h3>
      </div>
      <DataTable columns={columns} data={members} />
    </div>
  );
};

