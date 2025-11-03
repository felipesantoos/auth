/**
 * Invite Member Dialog Component
 * Modal for adding members to workspace
 */

import React, { useState } from 'react';
import { UserPlus } from 'lucide-react';
import { useAddMember } from '../../hooks/useWorkspaces';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { WorkspaceRole } from '../../../core/domain/workspace';

interface InviteMemberDialogProps {
  workspaceId: string;
  onSuccess?: () => void;
}

export const InviteMemberDialog: React.FC<InviteMemberDialogProps> = ({
  workspaceId,
  onSuccess,
}) => {
  const [open, setOpen] = useState(false);
  const [userId, setUserId] = useState('');
  const [role, setRole] = useState<WorkspaceRole>('user');

  const addMemberMutation = useAddMember();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await addMemberMutation.mutateAsync({
        workspaceId,
        request: { user_id: userId, role },
      });

      setOpen(false);
      setUserId('');
      setRole('user');
      onSuccess?.();
    } catch (error) {
      console.error('Error adding member:', error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <UserPlus className="h-4 w-4 mr-2" />
          Adicionar Membro
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Adicionar Membro ao Workspace</DialogTitle>
          <DialogDescription>
            Convide um usuário para participar deste workspace.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="userId">ID do Usuário *</Label>
            <Input
              id="userId"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="Digite o ID do usuário"
              required
            />
          </div>
          <div>
            <Label htmlFor="role">Role</Label>
            <select
              id="role"
              value={role}
              onChange={(e) => setRole(e.target.value as WorkspaceRole)}
              className="w-full border rounded px-3 py-2"
            >
              <option value="user">User</option>
              <option value="manager">Manager</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={addMemberMutation.isPending}>
              {addMemberMutation.isPending ? 'Adicionando...' : 'Adicionar'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

