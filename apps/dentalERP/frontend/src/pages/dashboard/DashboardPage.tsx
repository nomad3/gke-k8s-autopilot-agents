import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import ManagerDashboard from '../../components/dashboards/ManagerDashboard';
import ClinicianDashboard from '../../components/dashboards/ClinicianDashboard';

const DashboardPage: React.FC = () => {
  const user = useAuthStore(state => state.user);
  const navigate = useNavigate();

  // Redirect executives/admins to the new ExecutiveOverview
  useEffect(() => {
    if (user && (user.role === 'executive' || user.role === 'admin')) {
      navigate('/executive', { replace: true });
    }
  }, [user, navigate]);

  if (!user) {
    return (
      <div className="p-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Access Denied</h1>
          <p className="text-gray-600">Please log in to access the BI dashboard</p>
        </div>
      </div>
    );
  }

  // Render role-based BI dashboard following our wireframe specifications
  const renderDashboard = () => {
    switch (user.role) {
      case 'executive':
      case 'admin':
        // Redirected via useEffect above
        return null;
      case 'manager':
        return <ManagerDashboard />;
      case 'clinician':
        return <ClinicianDashboard />;
      default:
        return (
          <div className="p-6">
            <div className="bg-white rounded-lg shadow border p-6 text-center">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Business Intelligence Dashboard
              </h2>
              <p className="text-gray-600">
                Role-specific BI dashboard will be displayed here based on your permissions.
              </p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {renderDashboard()}
    </div>
  );
};

export default DashboardPage;
