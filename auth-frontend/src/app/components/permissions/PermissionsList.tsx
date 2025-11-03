/**
 * Permissions List Component
 * Display user permissions
 */

import React from 'react';
import { Shield, Trash2 } from 'lucide-react';
import { Permission } from '../../../core/domain/permission';
import { DataTable } from '../common/DataTable';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';

interface PermissionsListProps {
  permissions: Permission[];
  canManage: boolean;
  onRevokePermission?: (permissionId: string) => void;
}

export const PermissionsList: React.FC<PermissionsListProps> = ({
  permissions,
  canManage,
  onRevokePermission,
}) => {
  const getActionBadge = (action: string) => {
    const colors = {
      manage: 'bg-purple-100 text-purple-800',
      create: 'bg-green-100 text-green-800',
      read: 'bg-blue-100 text-blue-800',
      update: 'bg-yellow-100 text-yellow-800',
      delete: 'bg-red-100 text-red-800',
    };

    return (
      <Badge className={colors[action as keyof typeof colors] || 'bg-slate-100'}>
        {action.toUpperCase()}
      </Badge>
    );
  };

  const columns = [
    {
      accessorKey: 'resource_type',
      header: 'Recurso',
      cell: (row: Permission) => (
        <span className="font-medium">{row.resource_type}</span>
      ),
    },
    {
      accessorKey: 'resource_id',
      header: 'ID do Recurso',
      cell: (row: Permission) => (
        <span className="font-mono text-sm">
          {row.resource_id || 'Todos'}
        </span>
      ),
    },
    {
      accessorKey: 'action',
      header: 'Ação',
      cell: (row: Permission) => getActionBadge(row.action),
    },
    {
      accessorKey: 'granted_by',
      header: 'Concedido por',
      cell: (row: Permission) => (
        <span className="text-sm text-slate-500">
          {row.granted_by ? row.granted_by.substring(0, 8) + '...' : '-'}
        </span>
      ),
    },
    {
      accessorKey: 'created_at',
      header: 'Criado em',
      cell: (row: Permission) => (
        new Date(row.created_at).toLocaleDateString('pt-BR')
      ),
    },
    {
      accessorKey: 'actions',
      header: 'Ações',
      cell: (row: Permission) => {
        if (!canManage) {
          return <span className="text-slate-400 text-sm">-</span>;
        }

        return (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onRevokePermission?.(row.id)}
          >
            <Trash2 className="h-4 w-4 text-red-500" />
          </Button>
        );
      },
    },
  ];

  if (permissions.length === 0) {
    return (
      <div className="text-center py-8">
        <Shield className="h-12 w-12 text-slate-400 mx-auto mb-4" />
        <p className="text-slate-500">Nenhuma permissão encontrada.</p>
      </div>
    );
  }

  return <DataTable columns={columns} data={permissions} />;
};

