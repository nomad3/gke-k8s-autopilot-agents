import React, { useState } from 'react';
import { useUnifiedSummary, useUnifiedByPractice } from '../../hooks/useUnifiedAnalytics';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { ChartBarIcon, BanknotesIcon, UsersIcon, ArrowTrendingUpIcon } from '@heroicons/react/24/outline';

const OverviewPage: React.FC = () => {
  const [selectedPractice, setSelectedPractice] = useState<string>('');
  const [startMonth, setStartMonth] = useState<string>('');
  const [endMonth, setEndMonth] = useState<string>('');

  const { data: summaryData, isLoading: summaryLoading } = useUnifiedSummary({
    practice_id: selectedPractice || undefined,
    month: endMonth || undefined,
  });

  const { data: byPracticeData, isLoading: byPracticeLoading } = useUnifiedByPractice({
    start_month: startMonth || undefined,
    end_month: endMonth || undefined,
  });

  const isLoading = summaryLoading || byPracticeLoading;

  // Format helpers
  const formatCurrency = (value: any) => {
    if (!value || isNaN(parseFloat(value))) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(parseFloat(value));
  };

  const formatPercent = (value: any) => {
    if (!value || isNaN(parseFloat(value))) return 'N/A';
    return `${parseFloat(value).toFixed(1)}%`;
  };

  const formatNumber = (value: any) => {
    if (!value || isNaN(parseFloat(value))) return 'N/A';
    return new Intl.NumberFormat('en-US').format(parseFloat(value));
  };

  // Get unique practices for filter
  const practices = React.useMemo(() => {
    if (!byPracticeData) return [];
    return byPracticeData.map((p: any) => ({
      id: p.practice_id || p.PRACTICE_ID,
      name: p.practice_display_name || p.PRACTICE_DISPLAY_NAME,
    }));
  }, [byPracticeData]);

  if (isLoading && !summaryData) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Practice Analytics Overview</h1>
        <p className="text-sm text-gray-600 mt-1">
          Unified view combining Operations Report + NetSuite + PMS data
        </p>
      </div>

      <div className="bg-white rounded-lg shadow border p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Practice
            </label>
            <select
              value={selectedPractice}
              onChange={(e) => setSelectedPractice(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-500"
            >
              <option value="">All Practices</option>
              {practices.map((p: any) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Month
            </label>
            <input
              type="month"
              value={startMonth}
              onChange={(e) => setStartMonth(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Month
            </label>
            <input
              type="month"
              value={endMonth}
              onChange={(e) => setEndMonth(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={() => {
                setSelectedPractice('');
                setStartMonth('');
                setEndMonth('');
              }}
              className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {summaryData && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-sky-500 to-sky-600 rounded-lg shadow p-6 text-white">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium opacity-90">Total Production</span>
                <ChartBarIcon className="h-5 w-5 opacity-80" />
              </div>
              <div className="text-3xl font-bold">
                {formatCurrency(summaryData.total_production || summaryData.TOTAL_PRODUCTION)}
              </div>
              <div className="text-xs opacity-80 mt-1">
                Across {formatNumber(summaryData.practice_count || summaryData.PRACTICE_COUNT)} practices
              </div>
            </div>

            <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow p-6 text-white">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium opacity-90">Collections</span>
                <BanknotesIcon className="h-5 w-5 opacity-80" />
              </div>
              <div className="text-3xl font-bold">
                {formatCurrency(summaryData.total_collections || summaryData.TOTAL_COLLECTIONS)}
              </div>
              <div className="text-xs opacity-80 mt-1">
                Rate: {formatPercent(summaryData.avg_collection_rate || summaryData.AVG_COLLECTION_RATE)}
              </div>
            </div>

            <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow p-6 text-white">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium opacity-90">Patient Visits</span>
                <UsersIcon className="h-5 w-5 opacity-80" />
              </div>
              <div className="text-3xl font-bold">
                {formatNumber(summaryData.total_visits || summaryData.TOTAL_VISITS)}
              </div>
              <div className="text-xs opacity-80 mt-1">
                PPV: {formatCurrency(summaryData.avg_ppv || summaryData.AVG_PPV)}
              </div>
            </div>

            <div className="bg-gradient-to-br from-amber-500 to-amber-600 rounded-lg shadow p-6 text-white">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium opacity-90">Net Income</span>
                <ArrowTrendingUpIcon className="h-5 w-5 opacity-80" />
              </div>
              <div className="text-3xl font-bold">
                {formatCurrency(summaryData.total_net_income || summaryData.TOTAL_NET_INCOME)}
              </div>
              <div className="text-xs opacity-80 mt-1">
                From NetSuite
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow p-6 text-white">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium opacity-90">Case Acceptance</span>
                <ChartBarIcon className="h-5 w-5 opacity-80" />
              </div>
              <div className="text-3xl font-bold">
                {formatPercent(summaryData.avg_case_acceptance || summaryData.AVG_CASE_ACCEPTANCE)}
              </div>
              <div className="text-xs opacity-80 mt-1">
                Treatment acceptance rate
              </div>
            </div>

            <div className="bg-gradient-to-br from-teal-500 to-teal-600 rounded-lg shadow p-6 text-white">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium opacity-90">Hygiene Efficiency</span>
                <ChartBarIcon className="h-5 w-5 opacity-80" />
              </div>
              <div className="text-3xl font-bold">
                {(summaryData.avg_hygiene_ratio || summaryData.AVG_HYGIENE_RATIO)?.toFixed(2) || 'N/A'}
              </div>
              <div className="text-xs opacity-80 mt-1">
                Productivity ratio
              </div>
            </div>

            <div className="bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-lg shadow p-6 text-white">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium opacity-90">Revenue (NetSuite)</span>
                <BanknotesIcon className="h-5 w-5 opacity-80" />
              </div>
              <div className="text-3xl font-bold">
                {formatCurrency(summaryData.total_revenue || summaryData.TOTAL_REVENUE)}
              </div>
              <div className="text-xs opacity-80 mt-1">
                From financial system
              </div>
            </div>

            <div className="bg-gradient-to-br from-rose-500 to-rose-600 rounded-lg shadow p-6 text-white">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium opacity-90">LTM Production</span>
                <ArrowTrendingUpIcon className="h-5 w-5 opacity-80" />
              </div>
              <div className="text-3xl font-bold">
                {formatCurrency(summaryData.ltm_production || summaryData.LTM_PRODUCTION)}
              </div>
              <div className="text-xs opacity-80 mt-1">
                Rolling 12 months
              </div>
            </div>
          </div>
        </>
      )}

      {byPracticeData && byPracticeData.length > 0 && (
        <div className="bg-white rounded-lg shadow border">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-semibold">Practice Performance Comparison</h3>
            <p className="text-sm text-gray-600 mt-1">All practices ranked by total production</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Practice</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Months</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Production</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Collections</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Visits</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">PPV</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Collection %</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {byPracticeData.map((practice: any, idx: number) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      {practice.practice_display_name || practice.PRACTICE_DISPLAY_NAME}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 text-right">
                      {practice.months_tracked || practice.MONTHS_TRACKED}
                    </td>
                    <td className="px-6 py-4 text-sm font-semibold text-gray-900 text-right">
                      {formatCurrency(practice.total_production || practice.TOTAL_PRODUCTION)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 text-right">
                      {formatCurrency(practice.total_collections || practice.TOTAL_COLLECTIONS)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 text-right">
                      {formatNumber(practice.total_visits || practice.TOTAL_VISITS)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 text-right">
                      {formatCurrency(practice.avg_ppv || practice.AVG_PPV)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 text-right">
                      {formatPercent(practice.avg_collection_rate || practice.AVG_COLLECTION_RATE)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default OverviewPage;
