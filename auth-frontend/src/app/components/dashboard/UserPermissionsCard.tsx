/**
 * User Permissions Card (Dumb Component)
 * Displays user role and client information
 * Only receives props and renders UI - no business logic
 * Memoized to prevent unnecessary re-renders
 * 
 * Compliance: 08c-react-best-practices.md Section 2.1, 6.1
 */

import React from 'react';
import { User } from '../../../core/domain/user';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Shield, Building } from 'lucide-react';

interface UserPermissionsCardProps {
  user: User;
}

/**
 * Memoized component - only re-renders if user.role or user.clientId changes
 */
export const UserPermissionsCard = React.memo<UserPermissionsCardProps>(
  ({ user }) => {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center space-x-2">
            <Shield className="h-5 w-5 text-slate-500" />
            <CardTitle>Permissões</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          <div>
            <p className="text-sm font-medium text-slate-500">Role</p>
            <span
              className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                user.role === 'admin'
                  ? 'bg-purple-100 text-purple-800'
                  : user.role === 'manager'
                  ? 'bg-blue-100 text-blue-800'
                  : 'bg-slate-100 text-slate-800'
              }`}
            >
              {user.role.toUpperCase()}
            </span>
          </div>
          {user.clientId && (
            <div>
              <p className="text-sm font-medium text-slate-500 flex items-center">
                <Building className="h-4 w-4 mr-1" />
                Client ID
              </p>
              <p className="text-sm font-mono">{user.clientId}</p>
            </div>
          )}
        </CardContent>
      </Card>
    );
  },
  (prevProps, nextProps) => {
    // Custom comparison: only re-render if role or clientId changes
    return (
      prevProps.user.role === nextProps.user.role &&
      prevProps.user.clientId === nextProps.user.clientId
    );
  }
);

UserPermissionsCard.displayName = 'UserPermissionsCard';

