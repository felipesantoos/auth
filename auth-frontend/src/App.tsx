/**
 * Main App Component
 * Sets up routing, React Query, authentication context, and error boundary
 * Implements code splitting with lazy loading for better performance
 * 
 * Compliance: 08c-react-best-practices.md Section 5.3, 6.3
 */
import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryProvider } from './app/providers/QueryProvider';
import { AuthProvider } from './app/contexts/AuthContext';
import { WorkspaceProvider } from './app/contexts/WorkspaceContext';
import { ErrorBoundary } from './app/components/ErrorBoundary';
import { ProtectedRoute } from './app/components/ProtectedRoute';
import { LoadingSpinner } from './app/components/common/LoadingSpinner';

// ⚡ PERFORMANCE: Lazy load all route components for code splitting
// Each route is loaded only when accessed, reducing initial bundle size
const Login = lazy(() => import('./app/pages/Login'));
const Register = lazy(() => import('./app/pages/Register'));
const Dashboard = lazy(() => import('./app/pages/Dashboard'));
const ForgotPassword = lazy(() => import('./app/pages/ForgotPassword'));
const ResetPassword = lazy(() => import('./app/pages/ResetPassword'));
const OAuthCallback = lazy(() => import('./app/pages/OAuthCallback'));
const MFASetup = lazy(() => import('./app/pages/MFASetup'));
const VerifyEmail = lazy(() => import('./app/pages/VerifyEmail'));
const AuditDashboard = lazy(() => import('./app/pages/AuditDashboard'));
const Workspaces = lazy(() => import('./app/pages/Workspaces'));
const WorkspaceSettings = lazy(() => import('./app/pages/WorkspaceSettings'));
const WorkspaceMembers = lazy(() => import('./app/pages/WorkspaceMembers'));
const Permissions = lazy(() => import('./app/pages/Permissions'));

// Page loader component for Suspense fallback
const PageLoader = () => <LoadingSpinner message="Carregando página..." />;

function App() {
  return (
    <ErrorBoundary>
      <QueryProvider>
        <AuthProvider>
          <WorkspaceProvider>
            <Router>
            <Routes>
              <Route
                path="/login"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <Login />
                  </Suspense>
                }
              />
              <Route
                path="/register"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <Register />
                  </Suspense>
                }
              />
              <Route
                path="/forgot-password"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <ForgotPassword />
                  </Suspense>
                }
              />
              <Route
                path="/reset-password"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <ResetPassword />
                  </Suspense>
                }
              />
              <Route
                path="/auth/oauth/callback"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <OAuthCallback />
                  </Suspense>
                }
              />
              <Route
                path="/dashboard"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <ProtectedRoute>
                      <Dashboard />
                    </ProtectedRoute>
                  </Suspense>
                }
              />
              <Route
                path="/mfa-setup"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <ProtectedRoute>
                      <MFASetup />
                    </ProtectedRoute>
                  </Suspense>
                }
              />
              <Route
                path="/verify-email"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <VerifyEmail />
                  </Suspense>
                }
              />
              <Route
                path="/audit"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <ProtectedRoute>
                      <AuditDashboard />
                    </ProtectedRoute>
                  </Suspense>
                }
              />
              <Route
                path="/workspaces"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <ProtectedRoute>
                      <Workspaces />
                    </ProtectedRoute>
                  </Suspense>
                }
              />
              <Route
                path="/workspaces/:workspaceId/settings"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <ProtectedRoute>
                      <WorkspaceSettings />
                    </ProtectedRoute>
                  </Suspense>
                }
              />
              <Route
                path="/workspaces/:workspaceId/members"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <ProtectedRoute>
                      <WorkspaceMembers />
                    </ProtectedRoute>
                  </Suspense>
                }
              />
              <Route
                path="/permissions"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <ProtectedRoute>
                      <Permissions />
                    </ProtectedRoute>
                  </Suspense>
                }
              />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Router>
          </WorkspaceProvider>
        </AuthProvider>
      </QueryProvider>
    </ErrorBoundary>
  );
}

export default App;
