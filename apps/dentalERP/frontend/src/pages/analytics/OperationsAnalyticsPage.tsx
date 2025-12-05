import React, { useState } from 'react';
import { useUnifiedMonthly, useUnifiedSummary, useUnifiedByPractice } from '../../hooks/useUnifiedAnalytics';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { CalendarIcon, ChartBarIcon } from '@heroicons/react/24/outline';

const OperationsAnalyticsPage: React.FC = () => {
  const [startMonth, setStartMonth] = useState<string>('');
  const [endMonth, setEndMonth] = useState<string>('');
  const [selectedPractice, setSelectedPractice] = useState<string>('');

  // Fetch data using unified hooks with operations category
  const { data: monthlyData, isLoading: monthlyLoading, error: monthlyError } = useUnifiedMonthly({
    practice_id: selectedPractice || undefined,
    start_month: startMonth || undefined,
    end_month: endMonth || undefined,
    category: 'operations',
    limit: 100,
  });

  const { data: summaryData, isLoading: summaryLoading } = useUnifiedSummary({
    practice_id: selectedPractice || undefined,
    month: endMonth || undefined,
  });

  const { data: byPracticeData, isLoading: byPracticeLoading } = useUnifiedByPractice({
    start_month: startMonth || undefined,
    end_month: endMonth || undefined,
  });

  const isLoading = monthlyLoading || summaryLoading || byPracticeLoading;

  // Get unique practices for filter from byPracticeData
  const practices = React.useMemo(() => {
    if (!byPracticeData) return [];
    return byPracticeData.map((p: any) => ({
      id: p.practice_id || p.PRACTICE_ID,
      name: p.practice_display_name || p.PRACTICE_DISPLAY_NAME,
    }));
  }, [byPracticeData]);

  // Format currency
  const formatCurrency = (value: any) => {
    if (!value || isNaN(parseFloat(value))) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(parseFloat(value));
  };

  // Format percentage
  const formatPercent = (value: any) => {
    if (!value || isNaN(parseFloat(value))) return 'N/A';
    return `${parseFloat(value).toFixed(1)}%`;
  };

  // Format number
  const formatNumber = (value: any) => {
    if (!value || isNaN(parseFloat(value))) return 'N/A';
    return new Intl.NumberFormat('en-US').format(parseFloat(value));
  };

  if (isLoading && !monthlyData) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingSpinner />
      </div>
    );
  }

  if (monthlyError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="text-red-800 text-sm">
          Error loading operations data: {(monthlyError as Error)?.message || 'Unknown error'}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Operations KPI Dashboard</h1>
        <p className="text-sm text-gray-600 mt-1">
          Monthly operations metrics tracking 60+ KPIs across all practice locations
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow border p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Practice Location
            </label>
            <select
              value={selectedPractice}
              onChange={(e) => setSelectedPractice(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
            >
              <option value="">All Practices</option>
              {practices.map((practice: any) => (
                <option key={practice.id} value={practice.id}>
                  {practice.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="date"
              value={startMonth}
              onChange={(e) => setStartMonth(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              type="date"
              value={endMonth}
              onChange={(e) => setEndMonth(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={() => {
                setStartMonth('');
                setEndMonth('');
                setSelectedPractice('');
              }}
              className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      {summaryData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-sky-500 to-sky-600 rounded-lg shadow p-6 text-white">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium opacity-90">Total Production</span>
              <ChartBarIcon className="h-5 w-5 opacity-80" />
            </div>
            <div className="text-3xl font-bold">
              {formatCurrency(summaryData.TOTAL_PRODUCTION)}
            </div>
            <div className="text-xs opacity-80 mt-1">
              {formatNumber(summaryData.MONTHS_TRACKED)} days • {formatNumber(summaryData.PRACTICE_COUNT)} practices
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow p-6 text-white">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium opacity-90">Net Production</span>
              <ChartBarIcon className="h-5 w-5 opacity-80" />
            </div>
            <div className="text-3xl font-bold">
              {formatCurrency(summaryData.TOTAL_COLLECTIONS)}
            </div>
            <div className="text-xs opacity-80 mt-1">
              After adjustments
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow p-6 text-white">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium opacity-90">Patient Visits</span>
              <CalendarIcon className="h-5 w-5 opacity-80" />
            </div>
            <div className="text-3xl font-bold">
              {formatNumber(summaryData.TOTAL_VISITS)}
            </div>
            <div className="text-xs opacity-80 mt-1">
              Total appointments
            </div>
          </div>

          <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg shadow p-6 text-white">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium opacity-90">Avg Per Visit</span>
              <ChartBarIcon className="h-5 w-5 opacity-80" />
            </div>
            <div className="text-3xl font-bold">
              {formatCurrency(summaryData.AVG_PRODUCTION_PER_VISIT)}
            </div>
            <div className="text-xs opacity-80 mt-1">
              Production efficiency
            </div>
          </div>
        </div>
      )}

      {/* Additional KPI Cards Row 2 */}
      {summaryData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow p-6 text-white">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium opacity-90">Collection Rate</span>
              <ChartBarIcon className="h-5 w-5 opacity-80" />
            </div>
            <div className="text-3xl font-bold">
              {formatPercent(summaryData.AVG_COLLECTION_RATE_PCT)}
            </div>
            <div className="text-xs opacity-80 mt-1">
              Average across all practices
            </div>
          </div>

          <div className="bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-lg shadow p-6 text-white">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium opacity-90">Case Acceptance</span>
              <ChartBarIcon className="h-5 w-5 opacity-80" />
            </div>
            <div className="text-3xl font-bold">
              {formatPercent(summaryData.AVG_CASE_ACCEPTANCE_RATE)}
            </div>
            <div className="text-xs opacity-80 mt-1">
              Treatment acceptance rate
            </div>
          </div>

          <div className="bg-gradient-to-br from-teal-500 to-teal-600 rounded-lg shadow p-6 text-white">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium opacity-90">Hygiene Productivity</span>
              <ChartBarIcon className="h-5 w-5 opacity-80" />
            </div>
            <div className="text-3xl font-bold">
              {summaryData.AVG_HYGIENE_PRODUCTIVITY ? summaryData.AVG_HYGIENE_PRODUCTIVITY.toFixed(2) : 'N/A'}
            </div>
            <div className="text-xs opacity-80 mt-1">
              Production / Compensation ratio
            </div>
          </div>

          <div className="bg-gradient-to-br from-rose-500 to-rose-600 rounded-lg shadow p-6 text-white">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium opacity-90">LTM Production</span>
              <ChartBarIcon className="h-5 w-5 opacity-80" />
            </div>
            <div className="text-3xl font-bold">
              {formatCurrency(summaryData.LTM_PRODUCTION)}
            </div>
            <div className="text-xs opacity-80 mt-1">
              Last twelve months total
            </div>
          </div>
        </div>
      )}

      {/* By Practice Performance */}
      {byPracticeData && byPracticeData.length > 0 && (
        <div className="bg-white rounded-lg shadow border">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Performance by Practice</h3>
            <p className="text-sm text-gray-600 mt-1">Aggregated metrics by practice location</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Practice
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Months
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Production
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Collections
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Visits
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Avg $/Visit
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Collection Rate
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {byPracticeData.map((practice: any, idx: number) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {practice.practice_display_name || practice.PRACTICE_DISPLAY_NAME || practice.PRACTICE_ID}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-right">
                      {formatNumber(practice.MONTHS_TRACKED)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900 text-right">
                      {formatCurrency(practice.TOTAL_PRODUCTION)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-right">
                      {formatCurrency(practice.TOTAL_NET_PRODUCTION)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-right">
                      {formatNumber(practice.TOTAL_VISITS)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                      {formatCurrency(practice.AVG_PPV)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-right">
                      {formatPercent(practice.AVG_COLLECTION_RATE)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Monthly Operations Metrics Table */}
      <div className="bg-white rounded-lg shadow border">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Monthly Operations Metrics</h3>
          <p className="text-sm text-gray-600 mt-1">
            {monthlyData?.length || 0} records • Showing most recent data
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Practice
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Production
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Net
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Collections
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Visits
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  $/Visit
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Collection %
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Case Accept %
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Hygiene Ratio
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {monthlyData && monthlyData.length > 0 ? (
                monthlyData.map((item: any, idx: number) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex flex-col">
                        <span className="font-medium">
                          {item.REPORT_MONTH ? new Date(item.REPORT_MONTH).toLocaleDateString('en-US', { year: 'numeric', month: 'long' }) : 'N/A'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {item.practice_display_name || item.PRACTICE_DISPLAY_NAME || item.PRACTICE_ID}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900 text-right">
                      {formatCurrency(item.TOTAL_PRODUCTION)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-right">
                      {formatCurrency(item.NET_PRODUCTION)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-right">
                      {formatCurrency(item.COLLECTIONS)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-right">
                      {formatNumber(item.VISITS_TOTAL)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                      {formatCurrency(item.PPV_OVERALL)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-right">
                      {formatPercent(item.COLLECTION_RATE_PCT)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-right">
                      {formatPercent(item.CASE_ACCEPTANCE_RATE_PCT)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                      {item.HYGIENE_PRODUCTIVITY_RATIO ? parseFloat(item.HYGIENE_PRODUCTIVITY_RATIO).toFixed(2) : 'N/A'}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={11} className="px-6 py-12 text-center text-sm text-gray-500">
                    No production data found. Try adjusting your filters or upload PDF day sheets.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Info Footer */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <ChartBarIcon className="h-5 w-5 text-blue-600" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-900">About Operations KPIs</h3>
            <div className="mt-2 text-sm text-blue-800">
              <p>
                This data is sourced from the Snowflake Gold Layer (<code className="bg-blue-100 px-1 rounded">bronze_gold.operations_kpis_monthly</code>).
                All calculations (KPIs, ratios, LTM rollups) are performed in Snowflake dynamic tables for maximum performance.
              </p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li><strong>Monthly Tracking:</strong> 60+ operational KPIs tracked per practice per month</li>
                <li><strong>Auto-Refresh:</strong> Dynamic tables update automatically (1-hour lag)</li>
                <li><strong>LTM Calculations:</strong> Last Twelve Months rolling totals for trend analysis</li>
                <li><strong>Hybrid Data:</strong> NetSuite integration + Excel upload for complete coverage</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OperationsAnalyticsPage;
