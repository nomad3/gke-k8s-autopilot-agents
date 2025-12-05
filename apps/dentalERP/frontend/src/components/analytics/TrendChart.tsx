import React, { useMemo, useState } from 'react';
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/react/24/outline';

export interface TrendDataPoint {
  date: string;
  value: number;
  label?: string;
}

export interface TrendChartProps {
  data: TrendDataPoint[];
  title?: string;
  subtitle?: string;
  valuePrefix?: string;
  valueSuffix?: string;
  height?: number;
  color?: 'blue' | 'green' | 'orange' | 'purple' | 'red';
  showTrendLine?: boolean;
  showDataPoints?: boolean;
  loading?: boolean;
}

/**
 * TrendChart - SVG-based line chart for time-series data
 * Pure React implementation without external charting libraries
 */
export const TrendChart: React.FC<TrendChartProps> = ({
  data,
  title,
  subtitle,
  valuePrefix = '',
  valueSuffix = '',
  height = 300,
  color = 'blue',
  showTrendLine = true,
  showDataPoints = true,
  loading = false,
}) => {
  const [hoveredPoint, setHoveredPoint] = useState<number | null>(null);

  // Color schemes
  const colorSchemes = {
    blue: {
      line: '#3b82f6',
      gradient: ['#3b82f6', '#93c5fd'],
      dot: '#2563eb',
      hover: '#1d4ed8',
    },
    green: {
      line: '#10b981',
      gradient: ['#10b981', '#6ee7b7'],
      dot: '#059669',
      hover: '#047857',
    },
    orange: {
      line: '#f59e0b',
      gradient: ['#f59e0b', '#fcd34d'],
      dot: '#d97706',
      hover: '#b45309',
    },
    purple: {
      line: '#8b5cf6',
      gradient: ['#8b5cf6', '#c4b5fd'],
      dot: '#7c3aed',
      hover: '#6d28d9',
    },
    red: {
      line: '#ef4444',
      gradient: ['#ef4444', '#fca5a5'],
      dot: '#dc2626',
      hover: '#b91c1c',
    },
  };

  const scheme = colorSchemes[color];

  // Calculate chart dimensions
  const padding = { top: 20, right: 20, bottom: 40, left: 60 };
  const chartHeight = height - padding.top - padding.bottom;

  // Calculate min/max values
  const { minValue, range } = useMemo(() => {
    if (data.length === 0) return { minValue: 0, range: 100 };

    const values = data.map(d => d.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const buffer = (max - min) * 0.1; // 10% padding

    return {
      minValue: Math.max(0, min - buffer),
      range: (max + buffer) - (min - buffer),
    };
  }, [data]);

  // Calculate trend percentage
  const trendPercentage = useMemo(() => {
    if (data.length < 2) return 0;
    const first = data[0]?.value || 0;
    const last = data[data.length - 1]?.value || 0;
    if (first === 0) return 0;
    return ((last - first) / first) * 100;
  }, [data]);

  // Generate SVG path for line chart
  const linePath = useMemo(() => {
    if (data.length === 0) return '';

    const points = data.map((point, index) => {
      const x = (index / (data.length - 1)) * 100;
      const y = padding.top + (1 - (point.value - minValue) / range) * chartHeight;
      return `${x},${y}`;
    });

    return `M ${points.join(' L ')}`;
  }, [data, minValue, range, chartHeight, padding.top]);

  // Generate SVG path for area gradient
  const areaPath = useMemo(() => {
    if (data.length === 0) return '';

    const points = data.map((point, index) => {
      const x = (index / (data.length - 1)) * 100;
      const y = padding.top + (1 - (point.value - minValue) / range) * chartHeight;
      return { x, y };
    });

    const lastPoint = points[points.length - 1];
    const firstPoint = points[0];
    const bottomRight = `${lastPoint?.x || 0},${padding.top + chartHeight}`;
    const bottomLeft = `${firstPoint?.x || 0},${padding.top + chartHeight}`;

    const topPoints = points.map(p => `${p.x},${p.y}`).join(' L ');

    return `M ${topPoints} L ${bottomRight} L ${bottomLeft} Z`;
  }, [data, minValue, range, chartHeight, padding.top]);

  // Format value for display
  const formatValue = (value: number) => {
    const formatted = value.toLocaleString(undefined, {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    });
    return `${valuePrefix}${formatted}${valueSuffix}`;
  };

  // Format date for display
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  };

  // Loading skeleton
  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="animate-pulse space-y-4">
          <div className="w-48 h-6 bg-gray-300 dark:bg-gray-700 rounded"></div>
          <div className="w-full h-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  // Empty state
  if (data.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        {title && (
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            {title}
          </h3>
        )}
        <div className="flex items-center justify-center h-64 text-gray-500 dark:text-gray-400">
          <p>No trend data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          {title && (
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {title}
            </h3>
          )}
          {subtitle && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {subtitle}
            </p>
          )}
        </div>

        {/* Trend Indicator */}
        <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${
          trendPercentage >= 0
            ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
            : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
        }`}>
          {trendPercentage >= 0 ? (
            <ArrowTrendingUpIcon className="w-4 h-4" />
          ) : (
            <ArrowTrendingDownIcon className="w-4 h-4" />
          )}
          <span className="text-sm font-semibold">
            {Math.abs(trendPercentage).toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Chart */}
      <div className="relative" style={{ height: `${height}px` }}>
        <svg
          width="100%"
          height="100%"
          viewBox={`0 0 100 ${height}`}
          preserveAspectRatio="none"
          className="overflow-visible"
        >
          <defs>
            {/* Gradient for area fill */}
            <linearGradient id={`gradient-${color}`} x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor={scheme.gradient[0]} stopOpacity="0.3" />
              <stop offset="100%" stopColor={scheme.gradient[1]} stopOpacity="0.05" />
            </linearGradient>
          </defs>

          {/* Y-axis grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const y = padding.top + (1 - ratio) * chartHeight;
            return (
              <g key={ratio}>
                <line
                  x1="0"
                  y1={y}
                  x2="100"
                  y2={y}
                  stroke="currentColor"
                  strokeWidth="0.1"
                  strokeDasharray="1,1"
                  className="text-gray-300 dark:text-gray-600"
                />
              </g>
            );
          })}

          {/* Area gradient fill */}
          <path
            d={areaPath}
            fill={`url(#gradient-${color})`}
            vectorEffect="non-scaling-stroke"
          />

          {/* Line */}
          {showTrendLine && (
            <path
              d={linePath}
              fill="none"
              stroke={scheme.line}
              strokeWidth="0.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              vectorEffect="non-scaling-stroke"
            />
          )}

          {/* Data points */}
          {showDataPoints && data.map((point, index) => {
            const x = (index / (data.length - 1)) * 100;
            const y = padding.top + (1 - (point.value - minValue) / range) * chartHeight;
            const isHovered = hoveredPoint === index;

            return (
              <g key={index}>
                <circle
                  cx={x}
                  cy={y}
                  r={isHovered ? '1' : '0.5'}
                  fill={isHovered ? scheme.hover : scheme.dot}
                  className="transition-all cursor-pointer"
                  onMouseEnter={() => setHoveredPoint(index)}
                  onMouseLeave={() => setHoveredPoint(null)}
                  vectorEffect="non-scaling-stroke"
                />
              </g>
            );
          })}
        </svg>

        {/* Y-axis labels (absolute positioned) */}
        <div className="absolute left-0 top-0 bottom-0 flex flex-col justify-between text-xs text-gray-500 dark:text-gray-400 pointer-events-none" style={{ width: '50px' }}>
          {[1, 0.75, 0.5, 0.25, 0].map((ratio) => {
            const value = minValue + ratio * range;
            return (
              <div key={ratio} className="text-right pr-2">
                {formatValue(value)}
              </div>
            );
          })}
        </div>

        {/* Tooltip */}
        {hoveredPoint !== null && data[hoveredPoint] && (
          <div
            className="absolute bg-gray-900 dark:bg-gray-700 text-white px-3 py-2 rounded-lg shadow-xl text-sm pointer-events-none z-10"
            style={{
              left: `${(hoveredPoint / (data.length - 1)) * 100}%`,
              top: `${padding.top + (1 - (data[hoveredPoint]?.value - minValue) / range) * chartHeight - 60}px`,
              transform: 'translateX(-50%)',
            }}
          >
            <div className="font-semibold">{formatValue(data[hoveredPoint]?.value || 0)}</div>
            <div className="text-xs text-gray-300 mt-1">
              {formatDate(data[hoveredPoint]?.date || '')}
            </div>
            {data[hoveredPoint]?.label && (
              <div className="text-xs text-gray-400 mt-1">
                {data[hoveredPoint]?.label}
              </div>
            )}
          </div>
        )}
      </div>

      {/* X-axis labels */}
      <div className="flex justify-between mt-2 text-xs text-gray-500 dark:text-gray-400 pl-14 pr-4">
        <span>{formatDate(data[0]?.date || '')}</span>
        {data.length > 2 && (
          <span>{formatDate(data[Math.floor(data.length / 2)]?.date || '')}</span>
        )}
        <span>{formatDate(data[data.length - 1]?.date || '')}</span>
      </div>
    </div>
  );
};
