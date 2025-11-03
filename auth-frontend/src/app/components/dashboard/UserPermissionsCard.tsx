/**
 * User Permissions Card (Smart Component)
 * Displays user role in current workspace
 * Now uses WorkspaceContext for role information
 * 
 * Compliance: 08c-react-best-practices.md Section 2.1, 6.1
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Shield, Building2 } from 'lucide-react';
import { useWorkspace } from '../../hooks/useWorkspace';

/**
 * Smart component - connects with WorkspaceContext
 */
export const UserPermissionsCard: React.FC = () => {
  const { activeWorkspace, currentRole } = useWorkspace();

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center space-x-2">
          <Shield className="h-5 w-5 text-slate-500" />
          <CardTitle>Permissões</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {currentRole ? (
          <>
            <div>
              <p className="text-sm font-medium text-slate-500">Role no Workspace</p>
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  currentRole === 'admin'
                    ? 'bg-purple-100 text-purple-800'
                    : currentRole === 'manager'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-slate-100 text-slate-800'
                }`}
              >
                {currentRole.toUpperCase()}
              </span>
            </div>
            {activeWorkspace && (
              <div>
                <p className="text-sm font-medium text-slate-500 flex items-center">
                  <Building2 className="h-4 w-4 mr-1" />
                  Workspace Atual
                </p>
                <p className="text-sm">{activeWorkspace.name}</p>
                <p className="text-xs text-slate-400 font-mono">{activeWorkspace.slug}</p>
              </div>
            )}
          </>
        ) : (
          <div>
            <p className="text-sm text-slate-500">
              Selecione um workspace para ver suas permissões
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

UserPermissionsCard.displayName = 'UserPermissionsCard';

