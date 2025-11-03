/**
 * Dashboard Page (Smart Component)
 * Manages state and connects with Context
 * Delegates rendering to dumb components
 * 
 * Compliance: 08c-react-best-practices.md Section 2.1
 */
import React, { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { DashboardHeader } from '../components/dashboard/DashboardHeader';
import { UserProfileCard } from '../components/dashboard/UserProfileCard';
import { UserContactCard } from '../components/dashboard/UserContactCard';
import { UserPermissionsCard } from '../components/dashboard/UserPermissionsCard';
import { WelcomeCard } from '../components/dashboard/WelcomeCard';

/**
 * Dashboard - Smart Component
 * - Connects with Context (useAuth)
 * - Manages business logic (handleLogout)
 * - Delegates UI to Dumb Components
 */
export const Dashboard: React.FC = () => {
  // Smart: Connects with Context
  const { user, logout, loggingOut } = useAuth();
  const navigate = useNavigate();

  // Smart: Business logic
  const handleLogout = useCallback(async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      // Even if logout fails, navigate to login
      navigate('/login');
    }
  }, [logout, navigate]);

  if (!user) return null;

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Dumb: receives props, no business logic */}
      <DashboardHeader onLogout={handleLogout} loggingOut={loggingOut} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {/* Dumb: only renders UI with data */}
          <UserProfileCard user={user} />
          <UserContactCard user={user} />
          {/* Smart: now connects with WorkspaceContext */}
          <UserPermissionsCard />
        </div>

        {/* Dumb: static content */}
        <WelcomeCard />
      </main>
    </div>
  );
};

export default Dashboard;
