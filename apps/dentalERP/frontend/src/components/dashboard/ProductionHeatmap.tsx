import React from 'react';
import { CalendarIcon } from '@heroicons/react/24/outline';

export interface DailyProductionData {
  date: string;
  total_production: number;
  total_visits: number;
  avg_production_per_visit: number;
}

export interface ProductionHeatmapProps {
  data: DailyProductionData[];
  loading?: boolean;
  days?: number; // Number of days to show
}

/**
 * ProductionHeatmap - Visual calendar view of daily production
 * Shows last N days with color intensity based on production level
 */
export const ProductionHeatmap: React.FC<ProductionHeatmapProps> = ({
  data,
  loading = false,
  days = 30,
}) => {
  // Get last N days
  const recentData = React.useMemo(() => {
    if (!data || data.length === 0) return [];
    return [...data]
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
      .slice(-days);
  }, [data, days]);

  // Calculate min/max for color scaling
  const { min, max } = React.useMemo(() => {
    if (recentData.length === 0) return { min: 0, max: 0 };
    const values = recentData.map(d => d.total_production);
    return {
      min: Math.min(...values),
      max: Math.max(...values),
    };
  }, [recentData]);

  // Get color intensity based on production value
  const getColorIntensity = (value: number) => {
    if (max === min) return 'bg-sky-200 dark:bg-sky-800';

    const normalized = (value - min) / (max - min);

    if (normalized >= 0.8) return 'bg-sky-600 dark:bg-sky-400';
    if (normalized >= 0.6) return 'bg-sky-500 dark:bg-sky-500';
    if (normalized >= 0.4) return 'bg-sky-400 dark:bg-sky-600';
    if (normalized >= 0.2) return 'bg-sky-300 dark:bg-sky-700';
    return 'bg-sky-200 dark:bg-sky-800';
  };

  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Format date
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  // Get day of week (commented out - not currently used)
  // const getDayOfWeek = (dateStr: string) => {
  //   const date = new Date(dateStr);
  //   return date.toLocaleDateString('en-US', { weekday: 'short' });
  // };

  // Group by week
  const weeks = React.useMemo(() => {
    const grouped: DailyProductionData[][] = [];
    let currentWeek: DailyProductionData[] = [];

    recentData.forEach((day, index) => {
      currentWeek.push(day);

      // Start new week on Sunday or every 7 days
      if (currentWeek.length === 7 || index === recentData.length - 1) {
        grouped.push([...currentWeek]);
        currentWeek = [];
      }
    });

    return grouped;
  }, [recentData]);

  // Loading skeleton
  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="w-48 h-6 bg-gray-300 dark:bg-gray-700 rounded mb-4 animate-pulse"></div>
        <div className="grid grid-cols-7 gap-2">
          {Array.from({ length: 28 }).map((_, i) => (
            <div
              key={i}
              className="aspect-square bg-gray-300 dark:bg-gray-700 rounded animate-pulse"
            ></div>
          ))}
        </div>
      </div>
    );
  }

  // Empty state
  if (!recentData || recentData.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-12 text-center">
        <CalendarIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <p className="text-gray-500 dark:text-gray-400">No production data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center space-x-2">
          <CalendarIcon className="w-5 h-5 text-sky-500" />
          <span>Production Heatmap</span>
        </h3>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          Last {recentData.length} days
        </span>
      </div>

      {/* Day labels */}
      <div className="grid grid-cols-7 gap-2 mb-2">
        {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => (
          <div key={day} className="text-center text-xs font-medium text-gray-500 dark:text-gray-400">
            {day}
          </div>
        ))}
      </div>

      {/* Heatmap Grid */}
      <div className="space-y-2">
        {weeks.map((week, weekIndex) => (
          <div key={weekIndex} className="grid grid-cols-7 gap-2">
            {week.map((day, dayIndex) => {
              const colorClass = getColorIntensity(day.total_production);

              return (
                <div
                  key={dayIndex}
                  className={`aspect-square ${colorClass} rounded transition-all duration-200 hover:scale-110 hover:shadow-lg cursor-pointer group relative`}
                  title={`${formatDate(day.date)}: ${formatCurrency(day.total_production)}`}
                >
                  {/* Tooltip on hover */}
                  <div className="hidden group-hover:block absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 z-10">
                    <div className="bg-gray-900 dark:bg-gray-700 text-white text-xs rounded-lg px-3 py-2 shadow-lg whitespace-nowrap">
                      <div className="font-semibold">{formatDate(day.date)}</div>
                      <div className="text-gray-300 dark:text-gray-400 mt-1">
                        {formatCurrency(day.total_production)}
                      </div>
                      <div className="text-gray-400 dark:text-gray-500 text-[10px]">
                        {day.total_visits} visits
                      </div>
                      {/* Arrow */}
                      <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-px">
                        <div className="border-4 border-transparent border-t-gray-900 dark:border-t-gray-700"></div>
                      </div>
                    </div>
                  </div>

                  {/* Day number (mobile only) */}
                  <div className="sm:hidden flex items-center justify-center h-full text-xs text-white font-medium">
                    {new Date(day.date).getDate()}
                  </div>
                </div>
              );
            })}

            {/* Fill empty cells for incomplete weeks */}
            {Array.from({ length: 7 - week.length }).map((_, i) => (
              <div key={`empty-${i}`} className="aspect-square"></div>
            ))}
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="mt-6 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-xs text-gray-500 dark:text-gray-400">Less</span>
          <div className="flex space-x-1">
            <div className="w-4 h-4 bg-sky-200 dark:bg-sky-800 rounded"></div>
            <div className="w-4 h-4 bg-sky-300 dark:bg-sky-700 rounded"></div>
            <div className="w-4 h-4 bg-sky-400 dark:bg-sky-600 rounded"></div>
            <div className="w-4 h-4 bg-sky-500 dark:bg-sky-500 rounded"></div>
            <div className="w-4 h-4 bg-sky-600 dark:bg-sky-400 rounded"></div>
          </div>
          <span className="text-xs text-gray-500 dark:text-gray-400">More</span>
        </div>

        {/* Summary stats */}
        <div className="text-xs text-gray-500 dark:text-gray-400">
          <span className="font-medium">{formatCurrency(max)}</span> peak
        </div>
      </div>
    </div>
  );
};
