import React, { useState } from 'react';
import { useProductionDaily, useProductionSummary, useProductionByPractice } from '../../hooks/useAnalytics';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { CalendarIcon, ChartBarIcon } from '@heroicons/react/24/outline';

const ProductionAnalyticsPage: React.FC = () => {
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [selectedPractice, setSelectedPractice] = useState<string>('');

  // Fetch data using our custom hooks
  const { data: dailyData, isLoading: dailyLoading, error: dailyError } = useProductionDaily({
    practice_location: selectedPractice || undefined,
    start_date: startDate || undefined,
    end_date: endDate || undefined,
    limit: 100,
  });

  const { data: summaryData, isLoading: summaryLoading } = useProductionSummary({
    practice_location: selectedPractice || undefined,
    start_date: startDate || undefined,
    end_date: endDate || undefined,
  });

  const { data: byPracticeData, isLoading: byPracticeLoading } = useProductionByPractice({
    start_date: startDate || undefined,
    end_date: endDate || undefined,
  });

  const isLoading = dailyLoading || summaryLoading || byPracticeLoading;

  // Get unique practice locations for filter
  const practiceLocations = React.useMemo(() => {
    if (!dailyData) return [];
    const locations = new Set<string>();
    dailyData.forEach((item: any) => {
      if (item.PRACTICE_LOCATION) locations.add(item.PRACTICE_LOCATION);
    });
    return Array.from(locations).sort();
  }, [dailyData]);

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

  if (isLoading && !dailyData) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingSpinner />
      </div>
    );
  }

  if (dailyError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="text-red-800 text-sm">
          Error loading production data: {(dailyError as Error)?.message || 'Unknown error'}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Production Analytics</h1>
        <p className="text-sm text-gray-600 mt-1">
          Real-time production metrics from Snowflake Gold Layer (AI-extracted from PDF day sheets)
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
              <option value="">All Locations</option>
              {practiceLocations.map((location) => (
                <option key={location} value={location}>
                  {location}
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
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={() => {
                setStartDate('');
                setEndDate('');
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
              {formatNumber(summaryData.DATE_COUNT)} days • {formatNumber(summaryData.PRACTICE_COUNT)} practices
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow p-6 text-white">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium opacity-90">Net Production</span>
              <ChartBarIcon className="h-5 w-5 opacity-80" />
            </div>
            <div className="text-3xl font-bold">
              {formatCurrency(summaryData.TOTAL_NET_PRODUCTION)}
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
                    Days
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Production
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Net Production
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
                      {practice.PRACTICE_LOCATION}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-right">
                      {formatNumber(practice.DAYS_REPORTED)}
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
                      {formatCurrency(practice.AVG_PRODUCTION_PER_VISIT)}
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

      {/* Daily Production Metrics Table */}
      <div className="bg-white rounded-lg shadow border">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Daily Production Metrics</h3>
          <p className="text-sm text-gray-600 mt-1">
            {dailyData?.length || 0} records • Showing most recent data
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
                  Adjustments
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
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Method
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Quality
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {dailyData && dailyData.length > 0 ? (
                dailyData.map((item: any, idx: number) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex flex-col">
                        <span className="font-medium">
                          {item.REPORT_DATE ? new Date(item.REPORT_DATE).toLocaleDateString() : 'N/A'}
                        </span>
                        <span className="text-xs text-gray-500">{item.DAY_NAME || ''}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {item.PRACTICE_LOCATION}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900 text-right">
                      {formatCurrency(item.TOTAL_PRODUCTION)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-right">
                      {formatCurrency(item.NET_PRODUCTION)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-right">
                      {formatCurrency(item.ADJUSTMENTS)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-right">
                      {formatCurrency(item.COLLECTIONS)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-right">
                      {formatNumber(item.PATIENT_VISITS)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                      {formatCurrency(item.PRODUCTION_PER_VISIT)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 text-right">
                      {formatPercent(item.COLLECTION_RATE_PCT)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          item.EXTRACTION_METHOD === 'ai'
                            ? 'bg-purple-100 text-purple-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {item.EXTRACTION_METHOD || 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          parseFloat(item.DATA_QUALITY_SCORE) >= 0.9
                            ? 'bg-green-100 text-green-800'
                            : parseFloat(item.DATA_QUALITY_SCORE) >= 0.7
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {item.DATA_QUALITY_SCORE
                          ? (parseFloat(item.DATA_QUALITY_SCORE) * 100).toFixed(0) + '%'
                          : 'N/A'}
                      </span>
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
            <h3 className="text-sm font-medium text-blue-900">About Production Analytics</h3>
            <div className="mt-2 text-sm text-blue-800">
              <p>
                This data is sourced directly from the Snowflake Gold Layer (<code className="bg-blue-100 px-1 rounded">bronze_gold.daily_production_metrics</code>).
                All calculations (aggregations, filtering, grouping) are performed in Snowflake for maximum performance.
                The backend simply passes queries through with no additional processing.
              </p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li><strong>AI Extraction:</strong> Uses GPT-4 Vision to extract structured data from PDF day sheets</li>
                <li><strong>Data Quality:</strong> Each record includes a quality score (90%+ = excellent)</li>
                <li><strong>Real-time:</strong> Data refreshes automatically every 10 minutes</li>
                <li><strong>Bronze → Silver → Gold:</strong> Full medallion architecture with dbt transformations</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductionAnalyticsPage;
