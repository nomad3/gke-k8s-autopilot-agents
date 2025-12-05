import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { warehouseAPI } from '../../services/warehouse';

interface ProductionKPIWidgetProps {
  monthDate: string; // Format: YYYY-MM-01
  practiceFilter?: string[]; // Optional: filter by specific practices
}

/**
 * Production KPI Widget
 * Displays real-time production metrics from Snowflake Gold layer
 */
const ProductionKPIWidget: React.FC<ProductionKPIWidgetProps> = ({
  monthDate,
  practiceFilter = []
}) => {
  const { data: comparison, isLoading, error } = useQuery({
    queryKey: ['practice-comparison', monthDate],
    queryFn: () => warehouseAPI.getPracticeComparison(monthDate),
    refetchInterval: 300000, // Refresh every 5 minutes
  });

  // Filter by practices if specified
  const filteredData = practiceFilter.length > 0
    ? comparison?.filter(p => practiceFilter.includes(p.practiceName))
    : comparison;

  // Calculate totals
  const totals = filteredData?.reduce(
    (acc, practice) => ({
      production: acc.production + practice.totalProduction,
      expenses: acc.expenses + practice.totalExpenses,
      netIncome: acc.netIncome + practice.netIncome,
      newPatients: acc.newPatients + practice.newPatients,
      activePatients: acc.activePatients + practice.activePatients,
    }),
    { production: 0, expenses: 0, netIncome: 0, newPatients: 0, activePatients: 0 }
  );

  const avgMargin = filteredData?.length
    ? filteredData.reduce((sum, p) => sum + p.profitMargin, 0) / filteredData.length
    : 0;

  const avgGrowth = filteredData?.length
    ? filteredData.reduce((sum, p) => sum + p.momGrowth, 0) / filteredData.length
    : 0;

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow border p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="h-8 bg-gray-200 rounded w-3/4"></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow border p-6">
        <div className="text-red-600">
          <p className="font-semibold">Failed to load production KPIs</p>
          <p className="text-sm">Check warehouse connection</p>
        </div>
      </div>
    );
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
  };

  return (
    <div className="bg-white rounded-lg shadow border p-6 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center shadow-lg">
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Production Overview</h3>
            <p className="text-xs text-gray-500">
              {new Date(monthDate).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-1 text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
          </svg>
          <span>Snowflake</span>
        </div>
      </div>

      {/* Main Metrics Grid */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* Total Production */}
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-semibold text-green-700 uppercase">Production</p>
            {avgGrowth !== 0 && (
              <span className={`text-xs font-bold ${avgGrowth > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatPercent(avgGrowth)}
              </span>
            )}
          </div>
          <p className="text-2xl font-bold text-green-900">{formatCurrency(totals?.production || 0)}</p>
        </div>

        {/* Net Income */}
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
          <p className="text-xs font-semibold text-blue-700 uppercase mb-2">Net Income</p>
          <p className="text-2xl font-bold text-blue-900">{formatCurrency(totals?.netIncome || 0)}</p>
        </div>

        {/* Profit Margin */}
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
          <p className="text-xs font-semibold text-purple-700 uppercase mb-2">Avg Margin</p>
          <p className="text-2xl font-bold text-purple-900">{avgMargin.toFixed(1)}%</p>
        </div>

        {/* New Patients */}
        <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-4">
          <p className="text-xs font-semibold text-orange-700 uppercase mb-2">New Patients</p>
          <p className="text-2xl font-bold text-orange-900">{totals?.newPatients || 0}</p>
        </div>
      </div>

      {/* Practice Breakdown */}
      {filteredData && filteredData.length > 1 && (
        <div className="pt-4 border-t border-gray-100">
          <p className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-3">By Practice</p>
          <div className="space-y-2">
            {filteredData.map((practice) => (
              <div key={practice.practiceName} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${
                    practice.profitMargin > 28 ? 'bg-green-500' :
                    practice.profitMargin > 25 ? 'bg-yellow-500' :
                    'bg-red-500'
                  }`}></div>
                  <span className="text-sm font-medium text-gray-900 capitalize">
                    {practice.practiceName.replace('_', ' ')}
                  </span>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-gray-900">{formatCurrency(practice.totalProduction)}</p>
                  <p className="text-xs text-gray-500">{practice.profitMargin.toFixed(1)}% margin</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-1">
            <svg className="w-3 h-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <p className="text-xs text-gray-500">Snowflake Gold Layer</p>
          </div>
          <p className="text-xs text-gray-500">{filteredData?.length || 0} {filteredData?.length === 1 ? 'practice' : 'practices'}</p>
        </div>
      </div>
    </div>
  );
};

export default ProductionKPIWidget;
