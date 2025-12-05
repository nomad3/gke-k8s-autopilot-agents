import React from 'react';
import { NavLink, Route, Routes, Navigate } from 'react-router-dom';
import OverviewPage from './OverviewPage';
import OperationsAnalyticsPage from './OperationsAnalyticsPage';
import FinancialAnalyticsPage from './FinancialAnalyticsPage';
import ProductionAnalyticsPage from './ProductionAnalyticsPage';

const tabs = [
  { to: 'overview', label: 'Overview' },
  { to: 'operations', label: 'Operations' },
  { to: 'financial', label: 'Financial' },
  { to: 'production', label: 'Production' },
];

const AnalyticsPage: React.FC = () => {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
        <p className="text-gray-600">Deep-dive BI views across key domains</p>
      </div>

      {/* Sub-navigation tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex flex-wrap gap-2" aria-label="Analytics sections">
          {tabs.map((t) => (
            <NavLink
              key={t.to}
              to={t.to}
              className={({ isActive }) => `
                px-4 py-2 text-sm font-medium rounded-t-md border-b-2
                ${isActive ? 'border-primary-600 text-primary-700 bg-primary-50' : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'}
              `}
            >
              {t.label}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Nested analytics routes */}
      <div>
        <Routes>
          <Route index element={<Navigate to="overview" replace />} />
          <Route path="overview" element={<OverviewPage />} />
          <Route path="operations" element={<OperationsAnalyticsPage />} />
          <Route path="financial" element={<FinancialAnalyticsPage />} />
          <Route path="production" element={<ProductionAnalyticsPage />} />
          <Route path="*" element={<Navigate to="overview" replace />} />
        </Routes>
      </div>
    </div>
  );
};

export default AnalyticsPage;
