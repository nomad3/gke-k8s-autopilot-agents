import React, { Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { ErrorBoundary } from './components/ui/ErrorBoundary';
import { LoadingSpinner } from './components/ui/LoadingSpinner';
import { useAuth } from './hooks/useAuth';

// Lazy load components for better performance
const LoginPage = React.lazy(() => import('./pages/auth/LoginPage'));
const RegisterPage = React.lazy(() => import('./pages/auth/RegisterPage'));
const DashboardPage = React.lazy(() => import('./pages/dashboard/DashboardPage'));
const ExecutiveOverview = React.lazy(() => import('./pages/dashboard/ExecutiveOverview'));
const BranchComparisonPage = React.lazy(() => import('./pages/analytics/BranchComparisonPage'));
// const EnhancedAnalyticsPage = React.lazy(() => import('./pages/analytics/EnhancedAnalyticsPage')); // Hidden for demo
const MCPServerManagementPage = React.lazy(() => import('./pages/admin/MCPServerManagementPage'));
const PatientsPage = React.lazy(() => import('./pages/patients/PatientsPage'));
const AppointmentsPage = React.lazy(() => import('./pages/appointments/AppointmentsPage'));
const PracticesPage = React.lazy(() => import('./pages/practices/PracticesPage'));
const IntegrationsPage = React.lazy(() => import('./pages/integrations/IntegrationsPage'));
const ManualIngestionPage = React.lazy(() => import('./pages/integrations/ManualIngestionPage'));
const SettingsPage = React.lazy(() => import('./pages/settings/SettingsPage'));
const AnalyticsPage = React.lazy(() => import('./pages/analytics/AnalyticsPage'));
const NotFoundPage = React.lazy(() => import('./pages/NotFoundPage'));

// Layout components
const AuthLayout = React.lazy(() => import('./layouts/AuthLayout'));
const DashboardLayout = React.lazy(() => import('./layouts/DashboardLayout'));

// Protected route wrapper
interface ProtectedRouteProps {
  children: React.ReactNode;
  roles?: string[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, roles }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/auth/login" replace />;
  }

  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

// Public route wrapper (redirect to dashboard if already logged in)
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

function App() {
  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        <Suspense
          fallback={
            <div className="min-h-screen flex items-center justify-center">
              <LoadingSpinner size="lg" />
            </div>
          }
        >
          <Routes>
            {/* Public routes */}
            <Route
              path="/auth/*"
              element={
                <PublicRoute>
                  <AuthLayout>
                    <Routes>
                      <Route path="login" element={<LoginPage />} />
                      <Route path="register" element={<RegisterPage />} />
                      <Route path="*" element={<Navigate to="login" replace />} />
                    </Routes>
                  </AuthLayout>
                </PublicRoute>
              }
            />

            {/* Protected routes */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <DashboardPage />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/executive"
              element={
                <ProtectedRoute roles={['admin', 'executive']}>
                  <DashboardLayout>
                    <ExecutiveOverview />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/compare"
              element={
                <ProtectedRoute roles={['admin', 'executive', 'manager']}>
                  <DashboardLayout>
                    <BranchComparisonPage />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />

            {/* Hidden for demo - has mock benchmark data */}
            {/* <Route
              path="/analytics/enhanced"
              element={
                <ProtectedRoute roles={['admin', 'executive', 'manager']}>
                  <DashboardLayout>
                    <EnhancedAnalyticsPage />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            /> */}

            <Route
              path="/admin/mcp"
              element={
                <ProtectedRoute roles={['admin']}>
                  <DashboardLayout>
                    <MCPServerManagementPage />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/patients/*"
              element={
                <ProtectedRoute roles={['admin', 'executive', 'manager', 'clinician']}>
                  <DashboardLayout>
                    <PatientsPage />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/appointments/*"
              element={
                <ProtectedRoute roles={['admin', 'executive', 'manager', 'clinician']}>
                  <DashboardLayout>
                    <AppointmentsPage />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/practices/*"
              element={
                <ProtectedRoute roles={['admin', 'executive', 'manager']}>
                  <DashboardLayout>
                    <PracticesPage />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/integrations/*"
              element={
                <ProtectedRoute roles={['admin', 'executive', 'manager']}>
                  <DashboardLayout>
                    <Routes>
                      <Route path="" element={<IntegrationsPage />} />
                      <Route path="ingestion" element={<React.Suspense fallback={<div />}> <ManualIngestionPage /> </React.Suspense>} />
                    </Routes>
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/analytics/*"
              element={
                <ProtectedRoute roles={['admin', 'executive', 'manager']}>
                  <DashboardLayout>
                    <AnalyticsPage />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/settings/*"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <SettingsPage />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />

            {/* Root redirect */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />

            {/* 404 page */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Suspense>
      </div>
    </ErrorBoundary>
  );
}

export default App;
