/**
 * Grant Permission Dialog Component
 * Modal for granting permissions
 */

import React, { useState } from 'react';
import { Shield } from 'lucide-react';
import { useGrantPermission } from '../../hooks/usePermissions';
import { PermissionAction } from '../../../core/domain/permission';
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

interface GrantPermissionDialogProps {
  onSuccess?: () => void;
}

export const GrantPermissionDialog: React.FC<GrantPermissionDialogProps> = ({ onSuccess }) => {
  const [open, setOpen] = useState(false);
  const [userId, setUserId] = useState('');
  const [resourceType, setResourceType] = useState('');
  const [resourceId, setResourceId] = useState('');
  const [action, setAction] = useState<PermissionAction>('read');

  const grantMutation = useGrantPermission();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await grantMutation.mutateAsync({
        user_id: userId,
        resource_type: resourceType,
        action,
        resource_id: resourceId || undefined,
      });

      setOpen(false);
      setUserId('');
      setResourceType('');
      setResourceId('');
      setAction('read');
      onSuccess?.();
    } catch (error) {
      console.error('Error granting permission:', error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Shield className="h-4 w-4 mr-2" />
          Conceder Permissão
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Conceder Permissão</DialogTitle>
          <DialogDescription>
            Atribua uma permissão específica a um usuário.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="userId">ID do Usuário *</Label>
            <Input
              id="userId"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="ID do usuário"
              required
            />
          </div>
          <div>
            <Label htmlFor="resourceType">Tipo de Recurso *</Label>
            <Input
              id="resourceType"
              value={resourceType}
              onChange={(e) => setResourceType(e.target.value)}
              placeholder="Ex: ticket, project, document"
              required
            />
            <p className="text-xs text-slate-500 mt-1">
              String livre - pode ser qualquer tipo de recurso
            </p>
          </div>
          <div>
            <Label htmlFor="resourceId">ID do Recurso (opcional)</Label>
            <Input
              id="resourceId"
              value={resourceId}
              onChange={(e) => setResourceId(e.target.value)}
              placeholder="Deixe em branco para todos"
            />
          </div>
          <div>
            <Label htmlFor="action">Ação *</Label>
            <select
              id="action"
              value={action}
              onChange={(e) => setAction(e.target.value as PermissionAction)}
              className="w-full border rounded px-3 py-2"
            >
              <option value="read">Read</option>
              <option value="create">Create</option>
              <option value="update">Update</option>
              <option value="delete">Delete</option>
              <option value="manage">Manage (todas)</option>
            </select>
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" disabled={grantMutation.isPending}>
              {grantMutation.isPending ? 'Concedendo...' : 'Conceder'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

