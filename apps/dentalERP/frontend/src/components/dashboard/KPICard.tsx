import React from 'react';
import { ArrowUpIcon, ArrowDownIcon, MinusIcon } from '@heroicons/react/24/solid';

export interface KPICardProps {
  label: string;
  value: string | number | null;
  change?: number | null; // Percentage change
  trend?: 'up' | 'down' | 'neutral';
  icon?: string; // Emoji icon
  color?: 'blue' | 'green' | 'orange' | 'purple' | 'red';
  subtitle?: string;
  loading?: boolean;
}

/**
 * KPICard - Modern metric display card for executive dashboard
 * Shows key performance indicators with trend arrows and color coding
 */
export const KPICard: React.FC<KPICardProps> = ({
  label,
  value,
  change,
  trend = 'neutral',
  icon = '📊',
  color = 'blue',
  subtitle,
  loading = false,
}) => {
  // Color mapping for different card types
  const colorClasses = {
    blue: {
      bg: 'bg-blue-50 dark:bg-blue-900/20',
      border: 'border-blue-200 dark:border-blue-800',
      icon: 'bg-blue-100 dark:bg-blue-900/40',
      text: 'text-blue-900 dark:text-blue-100',
    },
    green: {
      bg: 'bg-green-50 dark:bg-green-900/20',
      border: 'border-green-200 dark:border-green-800',
      icon: 'bg-green-100 dark:bg-green-900/40',
      text: 'text-green-900 dark:text-green-100',
    },
    orange: {
      bg: 'bg-orange-50 dark:bg-orange-900/20',
      border: 'border-orange-200 dark:border-orange-800',
      icon: 'bg-orange-100 dark:bg-orange-900/40',
      text: 'text-orange-900 dark:text-orange-100',
    },
    purple: {
      bg: 'bg-purple-50 dark:bg-purple-900/20',
      border: 'border-purple-200 dark:border-purple-800',
      icon: 'bg-purple-100 dark:bg-purple-900/40',
      text: 'text-purple-900 dark:text-purple-100',
    },
    red: {
      bg: 'bg-red-50 dark:bg-red-900/20',
      border: 'border-red-200 dark:border-red-800',
      icon: 'bg-red-100 dark:bg-red-900/40',
      text: 'text-red-900 dark:text-red-100',
    },
  };

  const colors = colorClasses[color];

  // Trend arrow icon and color
  const trendConfig = {
    up: {
      icon: ArrowUpIcon,
      color: 'text-green-600 dark:text-green-400',
      bg: 'bg-green-100 dark:bg-green-900/30',
    },
    down: {
      icon: ArrowDownIcon,
      color: 'text-red-600 dark:text-red-400',
      bg: 'bg-red-100 dark:bg-red-900/30',
    },
    neutral: {
      icon: MinusIcon,
      color: 'text-gray-600 dark:text-gray-400',
      bg: 'bg-gray-100 dark:bg-gray-900/30',
    },
  };

  const TrendIcon = trendConfig[trend].icon;

  // Loading skeleton
  if (loading) {
    return (
      <div className={`${colors.bg} ${colors.border} border rounded-lg p-6 animate-pulse`}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="w-24 h-4 bg-gray-300 dark:bg-gray-700 rounded mb-3"></div>
            <div className="w-32 h-8 bg-gray-300 dark:bg-gray-700 rounded mb-2"></div>
            <div className="w-20 h-3 bg-gray-300 dark:bg-gray-700 rounded"></div>
          </div>
          <div className={`${colors.icon} w-12 h-12 rounded-lg`}></div>
        </div>
      </div>
    );
  }

  // Format the value
  const displayValue = value !== null && value !== undefined ? value : '—';

  return (
    <div
      className={`${colors.bg} ${colors.border} border rounded-lg p-6 transition-all duration-200 hover:shadow-lg hover:scale-[1.02]`}
    >
      <div className="flex items-start justify-between">
        {/* Left side - Label and Value */}
        <div className="flex-1 min-w-0">
          {/* Label */}
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
            {label}
          </p>

          {/* Value */}
          <p className={`text-3xl font-bold ${colors.text} truncate`}>
            {displayValue}
          </p>

          {/* Change indicator and subtitle */}
          <div className="flex items-center space-x-2 mt-2">
            {change !== null && change !== undefined && (
              <div
                className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-medium ${trendConfig[trend].bg} ${trendConfig[trend].color}`}
              >
                <TrendIcon className="w-3 h-3" />
                <span>
                  {change > 0 ? '+' : ''}
                  {change.toFixed(1)}%
                </span>
              </div>
            )}

            {subtitle && (
              <span className="text-xs text-gray-500 dark:text-gray-400 truncate">
                {subtitle}
              </span>
            )}
          </div>
        </div>

        {/* Right side - Icon */}
        <div className={`${colors.icon} w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0 ml-4`}>
          <span className="text-2xl" role="img" aria-label={label}>
            {icon}
          </span>
        </div>
      </div>
    </div>
  );
};

/**
 * KPICardGrid - Responsive grid container for KPI cards
 */
export const KPICardGrid: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {children}
    </div>
  );
};
