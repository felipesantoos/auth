/**
 * Session Table Columns (Example)
 * Column definitions for @tanstack/react-table
 * Demonstrates best practices for DataTable usage
 * 
 * Compliance: 08d-ui-components.md Section 5.2
 * 
 * Note: This is an example for future use (sessions management, audit logs)
 * Not currently used in auth-frontend but demonstrates the pattern
 */

import { ColumnDef } from '@tanstack/react-table';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { ArrowUpDown, MoreHorizontal, Trash2, Eye } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import { format } from 'date-fns';

/**
 * Session Entity (Example)
 * Represents a user session for table display
 */
export interface Session {
  id: string;
  userId: string;
  userEmail: string;
  ipAddress: string;
  userAgent: string;
  active: boolean;
  createdAt: Date;
  lastActivityAt: Date;
  expiresAt: Date;
}

/**
 * Session Table Columns
 * Defines columns for @tanstack/react-table
 * 
 * Features:
 * - Sortable columns (email, createdAt)
 * - Custom cell renderers (badges, dates)
 * - Actions dropdown (view, revoke)
 */
export const sessionColumns: ColumnDef<Session>[] = [
  {
    accessorKey: 'userEmail',
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
        >
          Email
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
    cell: ({ row }) => {
      const email = row.getValue('userEmail') as string;
      return <div className="font-medium">{email}</div>;
    },
  },
  {
    accessorKey: 'ipAddress',
    header: 'IP Address',
    cell: ({ row }) => {
      const ip = row.getValue('ipAddress') as string;
      return <div className="text-sm text-muted-foreground font-mono">{ip}</div>;
    },
  },
  {
    accessorKey: 'active',
    header: 'Status',
    cell: ({ row }) => {
      const active = row.getValue('active') as boolean;
      return (
        <Badge variant={active ? 'success' : 'secondary'}>
          {active ? 'Ativa' : 'Expirada'}
        </Badge>
      );
    },
  },
  {
    accessorKey: 'createdAt',
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
        >
          Criada em
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
    cell: ({ row }) => {
      const date = row.getValue('createdAt') as Date;
      return <div className="text-sm">{format(date, 'dd/MM/yyyy HH:mm')}</div>;
    },
  },
  {
    accessorKey: 'lastActivityAt',
    header: 'Última Atividade',
    cell: ({ row }) => {
      const date = row.getValue('lastActivityAt') as Date;
      return <div className="text-sm text-muted-foreground">{format(date, 'dd/MM/yyyy HH:mm')}</div>;
    },
  },
  {
    id: 'actions',
    cell: ({ row, table }) => {
      const session = row.original;
      const { onEdit, onDelete } = (table.options.meta as any) || {};

      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Abrir menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Ações</DropdownMenuLabel>
            {onEdit && (
              <DropdownMenuItem onClick={() => onEdit(session.id)}>
                <Eye className="mr-2 h-4 w-4" />
                Ver Detalhes
              </DropdownMenuItem>
            )}
            {onDelete && session.active && (
              <DropdownMenuItem
                onClick={() => onDelete(session.id)}
                className="text-destructive"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Revogar Sessão
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  },
];

/**
 * Example Usage:
 * 
 * ```tsx
 * import { DataTable } from '@/app/components/common/DataTable';
 * import { sessionColumns, Session } from '@/app/components/auth/session-columns';
 * 
 * export function SessionsPage() {
 *   const sessions: Session[] = [
 *     {
 *       id: '1',
 *       userId: 'user-123',
 *       userEmail: 'user@example.com',
 *       ipAddress: '192.168.1.1',
 *       userAgent: 'Mozilla/5.0...',
 *       active: true,
 *       createdAt: new Date(),
 *       lastActivityAt: new Date(),
 *       expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000),
 *     },
 *   ];
 * 
 *   const handleViewDetails = (id: string) => {
 *     console.log('View session:', id);
 *   };
 * 
 *   const handleRevokeSession = async (id: string) => {
 *     if (confirm('Tem certeza que deseja revogar esta sessão?')) {
 *       // Call API to revoke session
 *     }
 *   };
 * 
 *   return (
 *     <div className="container mx-auto py-8">
 *       <h1 className="text-3xl font-bold mb-6">Sessões Ativas</h1>
 *       <DataTable
 *         columns={sessionColumns}
 *         data={sessions}
 *         onEdit={handleViewDetails}
 *         onDelete={handleRevokeSession}
 *         searchPlaceholder="Buscar por email..."
 *         searchColumn="userEmail"
 *       />
 *     </div>
 *   );
 * }
 * ```
 */

