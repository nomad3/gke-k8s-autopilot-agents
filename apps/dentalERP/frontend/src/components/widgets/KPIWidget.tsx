import React from 'react';

interface KPIWidgetProps {
  title: string;
  value: string;
  change: string;
  trend: 'up' | 'down' | 'neutral';
  source: string;
  icon?: React.ReactNode;
  iconColor?: string;
}

const KPIWidget: React.FC<KPIWidgetProps> = ({
  title,
  value,
  change,
  trend,
  source,
  icon,
  iconColor = 'blue'
}) => {
  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return 'text-green-600';
      case 'down':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3.293 9.707a1 1 0 010-1.414l6-6a1 1 0 011.414 0l6 6a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L4.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
          </svg>
        );
      case 'down':
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 10.293a1 1 0 010 1.414l-6 6a1 1 0 01-1.414 0l-6-6a1 1 0 111.414-1.414L9 14.586V3a1 1 0 012 0v11.586l4.293-4.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        );
      default:
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  const getIconBgColor = () => {
    const colorMap: Record<string, string> = {
      blue: 'from-blue-400 to-blue-600',
      green: 'from-green-400 to-green-600',
      purple: 'from-purple-400 to-purple-600',
      orange: 'from-orange-400 to-orange-600',
      indigo: 'from-indigo-400 to-indigo-600',
      pink: 'from-pink-400 to-pink-600',
    };
    return colorMap[iconColor] || colorMap.blue;
  };

  return (
    <div className="bg-white rounded-lg shadow border p-6 hover:shadow-md transition-shadow relative overflow-hidden">
      {/* Decorative Background */}
      <div className="absolute top-0 right-0 w-32 h-32 transform translate-x-8 -translate-y-8 opacity-5">
        <div className={`w-full h-full rounded-full bg-gradient-to-br ${getIconBgColor()}`}></div>
      </div>

      {/* Widget Header */}
      <div className="flex items-center justify-between mb-4 relative">
        <div className="flex items-center space-x-3">
          {icon && (
            <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${getIconBgColor()} flex items-center justify-center shadow-lg`}>
              <div className="text-white">
                {icon}
              </div>
            </div>
          )}
          <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">{title}</h3>
        </div>
        <button className="text-gray-400 hover:text-gray-600 transition-colors">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
          </svg>
        </button>
      </div>

      {/* Main Value */}
      <div className="mb-3 relative">
        <p className="text-3xl font-bold text-gray-900">{value}</p>
      </div>

      {/* Change Indicator */}
      <div className="flex items-center justify-between relative">
        <div className={`flex items-center space-x-1 ${getTrendColor()}`}>
          {getTrendIcon()}
          <span className="text-sm font-semibold">{change}</span>
          <span className="text-xs text-gray-500 ml-1">vs last period</span>
        </div>
      </div>

      {/* Data Source */}
      <div className="mt-3 pt-3 border-t border-gray-100 relative">
        <div className="flex items-center space-x-1">
          <svg className="w-3 h-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <p className="text-xs text-gray-500">{source}</p>
        </div>
      </div>
    </div>
  );
};

export default KPIWidget;
