/**
 * Dashboard Header (Dumb Component)
 * Displays app header with logout button
 * Only receives props and renders UI - no business logic
 * Memoized to prevent unnecessary re-renders
 * 
 * Compliance: 08c-react-best-practices.md Section 2.1, 6.1
 */

import React from 'react';
import { Button } from '../ui/button';
import { LogOut } from 'lucide-react';

interface DashboardHeaderProps {
  onLogout: () => void;
  loggingOut: boolean;
}

/**
 * Memoized component - only re-renders if loggingOut state changes
 */
export const DashboardHeader = React.memo<DashboardHeaderProps>(
  ({ onLogout, loggingOut }) => {
    return (
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
            <Button variant="outline" onClick={onLogout} loading={loggingOut}>
              <LogOut className="mr-2 h-4 w-4" />
              Sair
            </Button>
          </div>
        </div>
      </header>
    );
  },
  (prevProps, nextProps) => {
    // Only re-render if loggingOut state changes
    return prevProps.loggingOut === nextProps.loggingOut;
  }
);

DashboardHeader.displayName = 'DashboardHeader';

