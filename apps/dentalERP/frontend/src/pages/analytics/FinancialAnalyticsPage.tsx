import React from 'react';
import { useFinancialSummary, usePracticeComparison } from '../../hooks/useFinancialAnalytics';
import { KPICard } from '../../components/dashboard/KPICard';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';

const FinancialAnalyticsPage: React.FC = () => {
  const { data: summary, isLoading, error } = useFinancialSummary();
  const { data: comparison } = usePracticeComparison();

  // Format currency helper
  const formatCurrency = (value?: number | null): string => {
    if (value === null || value === undefined) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Format percentage helper
  const formatPercent = (value?: number | null): string => {
    if (value === null || value === undefined) return '0%';
    return `${value.toFixed(1)}%`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-red-800 font-semibold mb-2">Error Loading Financial Data</h3>
        <p className="text-red-600 text-sm">{(error as Error).message}</p>
      </div>
    );
  }

  // Get latest month metrics
  const latestMonth = summary?.data[0];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-lg shadow border p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Financial Analytics</h1>
        <p className="text-gray-600">Real-time NetSuite data</p>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <KPICard
          label="Total Revenue"
          value={formatCurrency(latestMonth?.total_revenue)}
          change={latestMonth?.mom_growth_pct}
          trend={latestMonth?.mom_growth_pct && latestMonth?.mom_growth_pct > 0 ? 'up' : latestMonth?.mom_growth_pct && latestMonth?.mom_growth_pct < 0 ? 'down' : 'neutral'}
          icon="💰"
          color="green"
        />
        <KPICard
          label="Total Expenses"
          value={formatCurrency(latestMonth?.total_expenses)}
          icon="💸"
          color="orange"
        />
        <KPICard
          label="Net Income"
          value={formatCurrency(latestMonth?.net_income)}
          change={latestMonth?.mom_growth_pct}
          icon="📈"
          color="blue"
        />
        <KPICard
          label="Profit Margin"
          value={formatPercent(latestMonth?.profit_margin_pct)}
          icon="📊"
          color="purple"
        />
        <KPICard
          label="Practices"
          value={comparison?.count || 0}
          icon="🏥"
          color="blue"
        />
      </div>

      {/* Practice Comparison Table */}
      <div className="bg-white rounded-lg shadow border">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-xl font-semibold text-gray-900">Performance by Practice</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Practice
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Revenue
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Expenses
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Net Income
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Margin %
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  MoM Growth
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {comparison?.practices?.map((practice, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {practice.practice_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                    {formatCurrency(practice.total_revenue)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                    {formatCurrency(practice.total_expenses)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-gray-900">
                    {formatCurrency(practice.net_income)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                    {formatPercent(practice.profit_margin_pct)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      practice.mom_growth_pct && practice.mom_growth_pct > 0
                        ? 'bg-green-100 text-green-800'
                        : practice.mom_growth_pct && practice.mom_growth_pct < 0
                        ? 'bg-red-100 text-red-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {practice.mom_growth_pct && practice.mom_growth_pct > 0 ? '+' : ''}
                      {formatPercent(practice.mom_growth_pct)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {(!comparison?.practices || comparison.practices.length === 0) && (
            <div className="text-center py-12 text-gray-500">
              No practice data available
            </div>
          )}
        </div>
      </div>

      {/* Monthly Trend Chart */}
      <div className="bg-white rounded-lg shadow border p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-4">Revenue Trend</h3>
        <div className="h-64 flex items-center justify-center text-gray-500">
          Chart visualization coming soon
        </div>
      </div>
    </div>
  );
};

export default FinancialAnalyticsPage;
