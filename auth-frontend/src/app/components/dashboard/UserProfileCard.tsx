/**
 * User Profile Card (Dumb Component)
 * Displays user profile information
 * Only receives props and renders UI - no business logic
 * Memoized to prevent unnecessary re-renders
 * 
 * Compliance: 08c-react-best-practices.md Section 2.1, 6.1
 */

import React from 'react';
import type { User } from '../../../core/domain/user';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { User as UserIcon } from 'lucide-react';

interface UserProfileCardProps {
  user: User;
}

/**
 * Memoized component - only re-renders if user.name or user.username changes
 */
export const UserProfileCard = React.memo<UserProfileCardProps>(
  ({ user }) => {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center space-x-2">
            <UserIcon className="h-5 w-5 text-slate-500" />
            <CardTitle>Perfil do Usuário</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          <div>
            <p className="text-sm font-medium text-slate-500">Nome</p>
            <p className="text-lg font-semibold">{user.name}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Username</p>
            <p className="text-lg">{user.username}</p>
          </div>
        </CardContent>
      </Card>
    );
  },
  (prevProps, nextProps) => {
    // Custom comparison: only re-render if relevant fields change
    return (
      prevProps.user.name === nextProps.user.name &&
      prevProps.user.username === nextProps.user.username
    );
  }
);

UserProfileCard.displayName = 'UserProfileCard';

