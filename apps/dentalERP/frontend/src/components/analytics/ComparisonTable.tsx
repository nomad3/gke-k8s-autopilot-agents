import React from 'react';

export interface PracticeMetrics {
  practice_location: string;
  total_production: number;
  total_visits: number;
  avg_production_per_visit: number;
  collection_rate: number;
  quality_score: number;
  rank?: number;
}

export interface ComparisonTableProps {
  practices: PracticeMetrics[];
  loading?: boolean;
}

/**
 * ComparisonTable - Side-by-side practice comparison with rankings
 * Shows medals for top performers and highlights best/worst metrics
 */
export const ComparisonTable: React.FC<ComparisonTableProps> = ({
  practices,
  loading = false,
}) => {
  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Format number
  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('en-US').format(value);
  };

  // Get medal for rank
  const getMedal = (rank: number) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `${rank}${getRankSuffix(rank)}`;
  };

  const getRankSuffix = (rank: number) => {
    const j = rank % 10;
    const k = rank % 100;
    if (j === 1 && k !== 11) return 'st';
    if (j === 2 && k !== 12) return 'nd';
    if (j === 3 && k !== 13) return 'rd';
    return 'th';
  };

  // Rank practices for each metric
  const rankMetric = (metricKey: keyof PracticeMetrics, reverse = false) => {
    const sorted = [...practices].sort((a, b) => {
      const aVal = Number(a[metricKey]);
      const bVal = Number(b[metricKey]);
      return reverse ? aVal - bVal : bVal - aVal;
    });

    return sorted.map((practice, index) => ({
      location: practice.practice_location,
      rank: index + 1,
      value: practice[metricKey],
    }));
  };

  // Get best/worst indicators
  const getBestWorst = (practice: string, metricKey: keyof PracticeMetrics, reverse = false) => {
    const ranked = rankMetric(metricKey, reverse);
    const practiceRank = ranked.find(r => r.location === practice);

    if (!practiceRank) return null;

    if (practiceRank.rank === 1) {
      return { type: 'best', icon: '🏆' };
    }
    if (practiceRank.rank === ranked.length) {
      return { type: 'worst', icon: '⚠️' };
    }
    return null;
  };

  // Metrics configuration
  const metrics = [
    {
      key: 'total_production' as keyof PracticeMetrics,
      label: 'Total Production',
      format: formatCurrency,
      reverse: false,
    },
    {
      key: 'total_visits' as keyof PracticeMetrics,
      label: 'Total Visits',
      format: formatNumber,
      reverse: false,
    },
    {
      key: 'avg_production_per_visit' as keyof PracticeMetrics,
      label: 'Avg $/Visit',
      format: formatCurrency,
      reverse: false,
    },
    {
      key: 'collection_rate' as keyof PracticeMetrics,
      label: 'Collection %',
      format: (v: number) => `${v.toFixed(1)}%`,
      reverse: false,
    },
    {
      key: 'quality_score' as keyof PracticeMetrics,
      label: 'Quality Score',
      format: (v: number) => `${v.toFixed(1)}`,
      reverse: false,
    },
  ];

  // Loading skeleton
  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-6 py-4 text-left">
                  <div className="w-24 h-4 bg-gray-300 dark:bg-gray-700 rounded animate-pulse"></div>
                </th>
                {[1, 2, 3].map((i) => (
                  <th key={i} className="px-6 py-4">
                    <div className="w-32 h-4 bg-gray-300 dark:bg-gray-700 rounded animate-pulse mx-auto"></div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[1, 2, 3, 4, 5].map((i) => (
                <tr key={i} className="border-t border-gray-200 dark:border-gray-700">
                  <td className="px-6 py-4">
                    <div className="w-32 h-4 bg-gray-300 dark:bg-gray-700 rounded animate-pulse"></div>
                  </td>
                  {[1, 2, 3].map((j) => (
                    <td key={j} className="px-6 py-4">
                      <div className="w-24 h-4 bg-gray-300 dark:bg-gray-700 rounded animate-pulse mx-auto"></div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  // Empty state
  if (!practices || practices.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-12 text-center">
        <p className="text-gray-500 dark:text-gray-400">
          Select at least 2 practices to compare
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900 dark:text-white sticky left-0 bg-gray-50 dark:bg-gray-900 z-10">
                Metric
              </th>
              {practices.map((practice) => (
                <th
                  key={practice.practice_location}
                  className="px-6 py-4 text-center text-sm font-semibold text-gray-900 dark:text-white min-w-[180px]"
                >
                  <div className="flex flex-col items-center space-y-1">
                    <span>{practice.practice_location}</span>
                    {practice.rank && (
                      <span className="text-xs font-normal text-gray-500 dark:text-gray-400">
                        {getMedal(practice.rank)}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {metrics.map((metric) => (
              <tr key={metric.key} className="hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
                <td className="px-6 py-4 text-sm font-medium text-gray-900 dark:text-white whitespace-nowrap sticky left-0 bg-white dark:bg-gray-800 z-10">
                  {metric.label}
                </td>
                {practices.map((practice) => {
                  const value = practice[metric.key] as number;
                  const indicator = getBestWorst(practice.practice_location, metric.key, metric.reverse);
                  const ranked = rankMetric(metric.key, metric.reverse);
                  const practiceRank = ranked.find(r => r.location === practice.practice_location);

                  return (
                    <td
                      key={practice.practice_location}
                      className={`px-6 py-4 text-center transition-colors ${
                        indicator?.type === 'best'
                          ? 'bg-green-50 dark:bg-green-900/20'
                          : indicator?.type === 'worst'
                          ? 'bg-red-50 dark:bg-red-900/20'
                          : ''
                      }`}
                    >
                      <div className="flex flex-col items-center space-y-1">
                        <div className="flex items-center space-x-2">
                          {indicator && (
                            <span className="text-lg">{indicator.icon}</span>
                          )}
                          <span className="text-sm font-semibold text-gray-900 dark:text-white">
                            {metric.format(value)}
                          </span>
                        </div>
                        {practiceRank && (
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {getMedal(practiceRank.rank)}
                          </span>
                        )}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="px-6 py-4 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-center space-x-6 text-xs text-gray-600 dark:text-gray-400">
          <div className="flex items-center space-x-1">
            <span>🏆</span>
            <span>Best Performer</span>
          </div>
          <div className="flex items-center space-x-1">
            <span>⚠️</span>
            <span>Needs Improvement</span>
          </div>
          <div className="flex items-center space-x-1">
            <span>🥇🥈🥉</span>
            <span>Rankings</span>
          </div>
        </div>
      </div>
    </div>
  );
};
