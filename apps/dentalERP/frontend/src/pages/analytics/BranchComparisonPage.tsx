import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTenant } from '../../contexts/TenantContext';
import { TenantBadge } from '../../components/tenant/TenantBadge';
import { PracticeSelector, Practice } from '../../components/analytics/PracticeSelector';
import { ComparisonTable, PracticeMetrics } from '../../components/analytics/ComparisonTable';
import { analyticsAPI } from '../../services/api';
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline';

/**
 * BranchComparisonPage - Side-by-side practice comparison
 * Compare 2-5 practices with detailed metrics and rankings
 */
export const BranchComparisonPage: React.FC = () => {
  const { selectedTenant, isLoading: tenantLoading } = useTenant();
  const [selectedPractices, setSelectedPractices] = useState<string[]>([]);

  // Fetch production by practice
  const { data: byPracticeData, isLoading: practiceLoading } = useQuery({
    queryKey: ['production-by-practice', selectedTenant?.tenant_code],
    queryFn: () => analyticsAPI.getProductionByPractice({}),
    enabled: !!selectedTenant,
  });

  // Transform data for PracticeSelector
  const availablePractices: Practice[] = useMemo(() => {
    if (!byPracticeData || !Array.isArray(byPracticeData)) return [];

    return byPracticeData.map((practice: any) => ({
      practice_location: practice.PRACTICE_LOCATION || practice.practice_location || 'Unknown',
      total_production: Number(practice.TOTAL_PRODUCTION || practice.total_production || 0),
    }));
  }, [byPracticeData]);

  // Transform data for ComparisonTable (only selected practices)
  const comparisonData: PracticeMetrics[] = useMemo(() => {
    if (!byPracticeData || !Array.isArray(byPracticeData) || selectedPractices.length === 0) {
      return [];
    }

    const filtered = byPracticeData.filter((practice: any) => {
      const location = practice.PRACTICE_LOCATION || practice.practice_location;
      return selectedPractices.includes(location);
    });

    // Rank by total production
    const sorted = [...filtered].sort((a: any, b: any) => {
      const aVal = Number(a.TOTAL_PRODUCTION || a.total_production || 0);
      const bVal = Number(b.TOTAL_PRODUCTION || b.total_production || 0);
      return bVal - aVal;
    });

    return sorted.map((practice: any, index: number) => ({
      practice_location: practice.PRACTICE_LOCATION || practice.practice_location || 'Unknown',
      total_production: Number(practice.TOTAL_PRODUCTION || practice.total_production || 0),
      total_visits: Number(practice.TOTAL_VISITS || practice.total_visits || 0),
      avg_production_per_visit: Number(practice.AVG_PRODUCTION_PER_VISIT || practice.avg_production_per_visit || 0),
      collection_rate: Number(practice.COLLECTION_RATE || 95), // Default to 95% if not available
      quality_score: Number(practice.QUALITY_SCORE || 90), // Default to 90 if not available
      rank: index + 1,
    }));
  }, [byPracticeData, selectedPractices]);

  // Export to CSV
  const exportToCSV = () => {
    if (comparisonData.length === 0) return;

    // Create CSV content
    const headers = [
      'Practice',
      'Total Production',
      'Total Visits',
      'Avg Production/Visit',
      'Collection Rate %',
      'Quality Score',
      'Rank',
    ];

    const rows = comparisonData.map((practice) => [
      practice.practice_location,
      practice.total_production,
      practice.total_visits,
      practice.avg_production_per_visit.toFixed(2),
      practice.collection_rate.toFixed(1),
      practice.quality_score.toFixed(1),
      practice.rank,
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.join(',')),
    ].join('\n');

    // Create download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', `practice-comparison-${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const isLoading = tenantLoading || practiceLoading;
  const showComparison = selectedPractices.length >= 2;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center space-x-3">
            <span className="text-4xl" role="img" aria-label="comparison">
              ⚖️
            </span>
            <span>Branch Comparison</span>
          </h1>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            Compare performance across multiple practice locations
          </p>
        </div>

        <div>
          <TenantBadge variant="compact" showProducts={false} />
        </div>
      </div>

      {/* Practice Selector */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Select Practices
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Choose 2-5 practices to compare side-by-side
            </p>
          </div>

          {showComparison && (
            <button
              onClick={exportToCSV}
              className="inline-flex items-center space-x-2 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg transition-colors text-sm font-medium"
            >
              <ArrowDownTrayIcon className="w-4 h-4" />
              <span>Export CSV</span>
            </button>
          )}
        </div>

        <PracticeSelector
          practices={availablePractices}
          selectedPractices={selectedPractices}
          onChange={setSelectedPractices}
          minSelect={2}
          maxSelect={5}
          loading={isLoading}
        />
      </div>

      {/* Comparison Table */}
      {showComparison ? (
        <div>
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Performance Comparison
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Side-by-side metrics with rankings and best/worst indicators
            </p>
          </div>

          <ComparisonTable
            practices={comparisonData}
            loading={practiceLoading}
          />

          {/* Summary Insights */}
          {comparisonData.length > 0 && (
            <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Top Performer */}
              <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
                <div className="flex items-start space-x-3">
                  <span className="text-2xl">🏆</span>
                  <div>
                    <p className="text-sm font-medium text-green-900 dark:text-green-100">
                      Top Producer
                    </p>
                    <p className="text-lg font-bold text-green-900 dark:text-green-100 mt-1">
                      {comparisonData[0]?.practice_location || 'N/A'}
                    </p>
                    <p className="text-xs text-green-700 dark:text-green-300 mt-1">
                      ${comparisonData[0]?.total_production.toLocaleString() || '0'} total production
                    </p>
                  </div>
                </div>
              </div>

              {/* Highest Efficiency */}
              {(() => {
                const sorted = [...comparisonData].sort(
                  (a, b) => b.avg_production_per_visit - a.avg_production_per_visit
                );
                return (
                  <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                    <div className="flex items-start space-x-3">
                      <span className="text-2xl">💎</span>
                      <div>
                        <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                          Highest Efficiency
                        </p>
                        <p className="text-lg font-bold text-blue-900 dark:text-blue-100 mt-1">
                          {sorted[0]?.practice_location || 'N/A'}
                        </p>
                        <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                          ${sorted[0]?.avg_production_per_visit.toFixed(0) || '0'} avg per visit
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* Most Visits */}
              {(() => {
                const sorted = [...comparisonData].sort(
                  (a, b) => b.total_visits - a.total_visits
                );
                return (
                  <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
                    <div className="flex items-start space-x-3">
                      <span className="text-2xl">👥</span>
                      <div>
                        <p className="text-sm font-medium text-purple-900 dark:text-purple-100">
                          Most Patient Visits
                        </p>
                        <p className="text-lg font-bold text-purple-900 dark:text-purple-100 mt-1">
                          {sorted[0]?.practice_location || 'N/A'}
                        </p>
                        <p className="text-xs text-purple-700 dark:text-purple-300 mt-1">
                          {sorted[0]?.total_visits.toLocaleString() || '0'} total visits
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })()}
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-12 text-center">
          <div className="text-6xl mb-4">⚖️</div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Ready to Compare
          </h3>
          <p className="text-gray-500 dark:text-gray-400 max-w-md mx-auto">
            Select at least 2 practices from the dropdown above to see a detailed side-by-side comparison
          </p>
        </div>
      )}
    </div>
  );
};

export default BranchComparisonPage;
