/**
 * User Contact Card (Dumb Component)
 * Displays user contact information and status
 * Only receives props and renders UI - no business logic
 * Memoized to prevent unnecessary re-renders
 * 
 * Compliance: 08c-react-best-practices.md Section 2.1, 6.1
 */

import React from 'react';
import type { User } from '../../../core/domain/user';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Mail } from 'lucide-react';

interface UserContactCardProps {
  user: User;
}

/**
 * Memoized component - only re-renders if user.email or user.active changes
 */
export const UserContactCard = React.memo<UserContactCardProps>(
  ({ user }) => {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center space-x-2">
            <Mail className="h-5 w-5 text-slate-500" />
            <CardTitle>Contato</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          <div>
            <p className="text-sm font-medium text-slate-500">Email</p>
            <p className="text-lg">{user.email}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Status</p>
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                user.active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}
            >
              {user.active ? 'Ativo' : 'Inativo'}
            </span>
          </div>
        </CardContent>
      </Card>
    );
  },
  (prevProps, nextProps) => {
    // Custom comparison: only re-render if email or active status changes
    return (
      prevProps.user.email === nextProps.user.email &&
      prevProps.user.active === nextProps.user.active
    );
  }
);

UserContactCard.displayName = 'UserContactCard';

