import React, { useMemo } from 'react';
import { ChartBarIcon, TrophyIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

export interface BenchmarkMetric {
  name: string;
  yourValue: number;
  industryAvg: number;
  topPerformer: number;
  unit?: string;
  format?: 'currency' | 'percentage' | 'number';
}

export interface BenchmarkOverlayProps {
  metrics: BenchmarkMetric[];
  title?: string;
  subtitle?: string;
  loading?: boolean;
}

/**
 * BenchmarkOverlay - Compare your metrics against industry benchmarks
 * Shows performance relative to industry average and top performers
 */
export const BenchmarkOverlay: React.FC<BenchmarkOverlayProps> = ({
  metrics,
  title = 'Industry Benchmarks',
  subtitle = 'Compare your performance against industry standards',
  loading = false,
}) => {
  // Format value based on type
  const formatValue = (value: number, format?: string, unit?: string) => {
    if (format === 'currency') {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(value);
    }

    if (format === 'percentage') {
      return `${value.toFixed(1)}%`;
    }

    const formatted = value.toLocaleString(undefined, {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    });

    return unit ? `${formatted} ${unit}` : formatted;
  };

  // Calculate performance status
  const getPerformanceStatus = (metric: BenchmarkMetric) => {
    const avgDiff = ((metric.yourValue - metric.industryAvg) / metric.industryAvg) * 100;

    if (avgDiff >= 10) {
      return {
        status: 'excellent' as const,
        label: 'Above Average',
        color: 'text-green-700 dark:text-green-400',
        bgColor: 'bg-green-50 dark:bg-green-900/20',
        icon: TrophyIcon,
        message: `${Math.abs(avgDiff).toFixed(0)}% above industry average`,
      };
    } else if (avgDiff >= 0) {
      return {
        status: 'good' as const,
        label: 'At Average',
        color: 'text-blue-700 dark:text-blue-400',
        bgColor: 'bg-blue-50 dark:bg-blue-900/20',
        icon: ChartBarIcon,
        message: 'Meeting industry standards',
      };
    } else if (avgDiff >= -10) {
      return {
        status: 'fair' as const,
        label: 'Below Average',
        color: 'text-orange-700 dark:text-orange-400',
        bgColor: 'bg-orange-50 dark:bg-orange-900/20',
        icon: ExclamationTriangleIcon,
        message: `${Math.abs(avgDiff).toFixed(0)}% below industry average`,
      };
    } else {
      return {
        status: 'poor' as const,
        label: 'Needs Improvement',
        color: 'text-red-700 dark:text-red-400',
        bgColor: 'bg-red-50 dark:bg-red-900/20',
        icon: ExclamationTriangleIcon,
        message: `${Math.abs(avgDiff).toFixed(0)}% below industry average`,
      };
    }
  };

  // Calculate overall performance score
  const overallScore = useMemo(() => {
    if (metrics.length === 0) return 0;

    const scores = metrics.map(metric => {
      const status = getPerformanceStatus(metric);
      switch (status.status) {
        case 'excellent': return 100;
        case 'good': return 75;
        case 'fair': return 50;
        case 'poor': return 25;
        default: return 0;
      }
    });

    return Math.round(scores.reduce((a: number, b: number) => a + b, 0) / scores.length);
  }, [metrics]);

  // Get overall rating
  const getOverallRating = () => {
    if (overallScore >= 85) return { label: 'Excellent', color: 'text-green-700 dark:text-green-400', icon: '🏆' };
    if (overallScore >= 70) return { label: 'Good', color: 'text-blue-700 dark:text-blue-400', icon: '👍' };
    if (overallScore >= 50) return { label: 'Fair', color: 'text-orange-700 dark:text-orange-400', icon: '⚠️' };
    return { label: 'Needs Improvement', color: 'text-red-700 dark:text-red-400', icon: '📉' };
  };

  // Loading skeleton
  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="animate-pulse space-y-4">
          <div className="w-48 h-6 bg-gray-300 dark:bg-gray-700 rounded"></div>
          <div className="w-full h-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
          <div className="w-full h-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  // Empty state
  if (metrics.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          {title}
        </h3>
        <div className="flex items-center justify-center h-32 text-gray-500 dark:text-gray-400">
          <p>No benchmark data available</p>
        </div>
      </div>
    );
  }

  const overallRating = getOverallRating();

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {title}
        </h3>
        {subtitle && (
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {subtitle}
          </p>
        )}
      </div>

      {/* Overall Score Card */}
      <div className={`${overallRating.color.includes('green') ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' :
        overallRating.color.includes('blue') ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800' :
        overallRating.color.includes('orange') ? 'bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800' :
        'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
      } border rounded-lg p-4 mb-6`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-3xl">{overallRating.icon}</span>
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Overall Performance
              </div>
              <div className={`text-xl font-bold ${overallRating.color}`}>
                {overallRating.label}
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className={`text-4xl font-bold ${overallRating.color}`}>
              {overallScore}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              out of 100
            </div>
          </div>
        </div>
      </div>

      {/* Metrics List */}
      <div className="space-y-4">
        {metrics.map((metric, index) => {
          const status = getPerformanceStatus(metric);
          const StatusIcon = status.icon;

          // Calculate bar widths (percentage of top performer)
          const yourWidth = (metric.yourValue / metric.topPerformer) * 100;
          const avgWidth = (metric.industryAvg / metric.topPerformer) * 100;

          return (
            <div
              key={index}
              className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              {/* Metric Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="text-sm font-semibold text-gray-900 dark:text-white">
                    {metric.name}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {status.message}
                  </div>
                </div>
                <div className={`flex items-center space-x-1 px-2 py-1 rounded-full ${status.bgColor}`}>
                  <StatusIcon className={`w-4 h-4 ${status.color}`} />
                  <span className={`text-xs font-medium ${status.color}`}>
                    {status.label}
                  </span>
                </div>
              </div>

              {/* Values Row */}
              <div className="grid grid-cols-3 gap-4 mb-3">
                <div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">Your Value</div>
                  <div className="text-sm font-bold text-gray-900 dark:text-white">
                    {formatValue(metric.yourValue, metric.format, metric.unit)}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">Industry Avg</div>
                  <div className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                    {formatValue(metric.industryAvg, metric.format, metric.unit)}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">Top Performer</div>
                  <div className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                    {formatValue(metric.topPerformer, metric.format, metric.unit)}
                  </div>
                </div>
              </div>

              {/* Visual Bar Chart */}
              <div className="space-y-2">
                {/* Your Value Bar */}
                <div>
                  <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
                    <span>You</span>
                    <span className={status.color}>
                      {((metric.yourValue / metric.topPerformer) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        status.status === 'excellent' ? 'bg-green-500' :
                        status.status === 'good' ? 'bg-blue-500' :
                        status.status === 'fair' ? 'bg-orange-500' :
                        'bg-red-500'
                      }`}
                      style={{ width: `${Math.min(yourWidth, 100)}%` }}
                    />
                  </div>
                </div>

                {/* Industry Average Bar */}
                <div>
                  <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
                    <span>Industry Avg</span>
                    <span>{((metric.industryAvg / metric.topPerformer) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-gray-400 dark:bg-gray-500 h-2 rounded-full transition-all"
                      style={{ width: `${Math.min(avgWidth, 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="flex items-center space-x-2">
            <TrophyIcon className="w-4 h-4 text-green-600 dark:text-green-400" />
            <span className="text-gray-600 dark:text-gray-400">Above Average</span>
          </div>
          <div className="flex items-center space-x-2">
            <ChartBarIcon className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <span className="text-gray-600 dark:text-gray-400">At Average</span>
          </div>
          <div className="flex items-center space-x-2">
            <ExclamationTriangleIcon className="w-4 h-4 text-orange-600 dark:text-orange-400" />
            <span className="text-gray-600 dark:text-gray-400">Below Average</span>
          </div>
          <div className="flex items-center space-x-2">
            <ExclamationTriangleIcon className="w-4 h-4 text-red-600 dark:text-red-400" />
            <span className="text-gray-600 dark:text-gray-400">Needs Improvement</span>
          </div>
        </div>
      </div>
    </div>
  );
};
