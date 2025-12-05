import React from 'react';
import { ArrowUpIcon, ArrowDownIcon, TrophyIcon } from '@heroicons/react/24/solid';

export interface PracticePerformance {
  practice_location: string;
  total_production: number;
  total_visits: number;
  avg_production_per_visit: number;
  collection_rate: number;
  quality_score: number;
  trend?: number; // Percentage change
}

export interface PracticeLeaderboardProps {
  practices: PracticePerformance[];
  loading?: boolean;
  metric?: 'production' | 'visits' | 'avg_value' | 'collection' | 'quality';
  limit?: number;
}

/**
 * PracticeLeaderboard - Ranked list of practice locations with performance metrics
 * Shows top performers with medals and trend indicators
 */
export const PracticeLeaderboard: React.FC<PracticeLeaderboardProps> = ({
  practices,
  loading = false,
  metric = 'production',
  limit = 10,
}) => {
  // Sort practices by selected metric
  const sortedPractices = React.useMemo(() => {
    if (!practices || practices.length === 0) return [];

    const sorted = [...practices].sort((a, b) => {
      switch (metric) {
        case 'production':
          return b.total_production - a.total_production;
        case 'visits':
          return b.total_visits - a.total_visits;
        case 'avg_value':
          return b.avg_production_per_visit - a.avg_production_per_visit;
        case 'collection':
          return b.collection_rate - a.collection_rate;
        case 'quality':
          return b.quality_score - a.quality_score;
        default:
          return 0;
      }
    });

    return sorted.slice(0, limit);
  }, [practices, metric, limit]);

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

  // Get medal emoji for top 3
  const getMedal = (rank: number) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return null;
  };

  // Get metric display value
  const getMetricValue = (practice: PracticePerformance) => {
    switch (metric) {
      case 'production':
        return formatCurrency(practice.total_production);
      case 'visits':
        return formatNumber(practice.total_visits);
      case 'avg_value':
        return formatCurrency(practice.avg_production_per_visit);
      case 'collection':
        return `${practice.collection_rate.toFixed(1)}%`;
      case 'quality':
        return `${practice.quality_score.toFixed(1)}`;
      default:
        return '—';
    }
  };

  // Get metric label
  const getMetricLabel = () => {
    switch (metric) {
      case 'production':
        return 'Total Production';
      case 'visits':
        return 'Total Visits';
      case 'avg_value':
        return 'Avg Production/Visit';
      case 'collection':
        return 'Collection Rate';
      case 'quality':
        return 'Quality Score';
      default:
        return 'Metric';
    }
  };

  // Loading skeleton
  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="w-48 h-6 bg-gray-300 dark:bg-gray-700 rounded animate-pulse"></div>
        </div>
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="px-6 py-4 flex items-center space-x-4 animate-pulse">
              <div className="w-8 h-8 bg-gray-300 dark:bg-gray-700 rounded"></div>
              <div className="flex-1">
                <div className="w-32 h-4 bg-gray-300 dark:bg-gray-700 rounded mb-2"></div>
                <div className="w-24 h-3 bg-gray-300 dark:bg-gray-700 rounded"></div>
              </div>
              <div className="w-20 h-6 bg-gray-300 dark:bg-gray-700 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Empty state
  if (!sortedPractices || sortedPractices.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-12 text-center">
        <TrophyIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <p className="text-gray-500 dark:text-gray-400">No practice data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center space-x-2">
          <TrophyIcon className="w-5 h-5 text-yellow-500" />
          <span>Top Performers</span>
        </h3>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          by {getMetricLabel()}
        </span>
      </div>

      {/* Practice List */}
      <div className="divide-y divide-gray-200 dark:divide-gray-700">
        {sortedPractices.map((practice, index) => {
          const rank = index + 1;
          const medal = getMedal(rank);
          const hasTrend = practice.trend !== null && practice.trend !== undefined;
          const trendUp = practice.trend && practice.trend > 0;

          return (
            <div
              key={practice.practice_location}
              className={`px-6 py-4 flex items-center space-x-4 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors cursor-pointer ${
                rank <= 3 ? 'bg-yellow-50/30 dark:bg-yellow-900/10' : ''
              }`}
            >
              {/* Rank / Medal */}
              <div className="w-10 flex-shrink-0 text-center">
                {medal ? (
                  <span className="text-2xl" role="img" aria-label={`Rank ${rank}`}>
                    {medal}
                  </span>
                ) : (
                  <span className="text-lg font-bold text-gray-400 dark:text-gray-500">
                    {rank}
                  </span>
                )}
              </div>

              {/* Practice Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {practice.practice_location}
                  </p>
                  {hasTrend && (
                    <span
                      className={`inline-flex items-center space-x-0.5 text-xs font-medium ${
                        trendUp
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}
                    >
                      {trendUp ? (
                        <ArrowUpIcon className="w-3 h-3" />
                      ) : (
                        <ArrowDownIcon className="w-3 h-3" />
                      )}
                      <span>
                        {Math.abs(practice.trend!).toFixed(1)}%
                      </span>
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  {formatNumber(practice.total_visits)} visits
                </p>
              </div>

              {/* Metric Value */}
              <div className="text-right flex-shrink-0">
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {getMetricValue(practice)}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      {sortedPractices.length === limit && practices.length > limit && (
        <div className="px-6 py-3 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 text-center">
          <button className="text-sm text-sky-600 dark:text-sky-400 hover:text-sky-700 dark:hover:text-sky-300 font-medium">
            View All {practices.length} Practices →
          </button>
        </div>
      )}
    </div>
  );
};
