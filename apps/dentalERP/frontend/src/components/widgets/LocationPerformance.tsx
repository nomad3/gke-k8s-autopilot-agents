import React from 'react';
import { useLocationPerformance } from '../../hooks/useAnalytics';

type LocationData = {
  id?: string;
  name: string;
  revenue: number;
  revenueChange: number;
  patients: number;
  patientChange: number;
  efficiency: number;
  status: 'excellent' | 'good' | 'warning' | 'poor' | 'neutral';
};

const LocationPerformance: React.FC = () => {
  const { data, error } = useLocationPerformance('30d');
  const isBlank = !!error || !data?.data;

  const locations: LocationData[] = isBlank
    ? [
        { name: '—', revenue: 0, revenueChange: 0, patients: 0, patientChange: 0, efficiency: 0, status: 'neutral' },
        { name: '—', revenue: 0, revenueChange: 0, patients: 0, patientChange: 0, efficiency: 0, status: 'neutral' },
        { name: '—', revenue: 0, revenueChange: 0, patients: 0, patientChange: 0, efficiency: 0, status: 'neutral' },
      ]
    : (data!.data.locations as any[]);

  const getStatusIndicator = (status: LocationData['status']) => {
    const indicators = {
      excellent: { color: 'bg-green-500', text: '🟢' },
      good: { color: 'bg-blue-500', text: '🟡' },
      warning: { color: 'bg-yellow-500', text: '🟡' },
      poor: { color: 'bg-red-500', text: '🔴' },
      neutral: { color: 'bg-gray-300', text: '—' },
    } as const;
    return indicators[status] || indicators.neutral;
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getChangeIcon = (change: number) => {
    if (change > 0) return '↑';
    if (change < 0) return '↓';
    return '→';
  };

  return (
    <div className="bg-white rounded-lg shadow border p-6">
      {/* Widget Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Multi-Location Performance</h3>
          <p className="text-sm text-gray-600">Comparative analytics across practice locations</p>
        </div>
        <div className="flex space-x-2">
          <button className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200">Filter</button>
          <button className="px-3 py-1 text-xs bg-primary-100 text-primary-700 rounded-md hover:bg-primary-200">Export</button>
        </div>
      </div>

      {/* Performance Table */}
      <div className="overflow-hidden">
        <div className="space-y-3">
          {/* Header */}
          <div className="grid grid-cols-5 gap-4 px-3 py-2 bg-gray-50 rounded-lg text-xs font-medium text-gray-700 uppercase tracking-wide">
            <div>Location</div>
            <div className="text-center">Revenue</div>
            <div className="text-center">Patients</div>
            <div className="text-center">Efficiency</div>
            <div className="text-center">Status</div>
          </div>

          {/* Location Rows */}
          {locations.map((location) => (
            <div
              key={location.id || location.name}
              className="grid grid-cols-5 gap-4 px-3 py-3 border border-gray-100 rounded-lg hover:bg-gray-50 transition-colors"
            >
              {/* Location Name */}
              <div className="flex items-center">
                <div className="w-2 h-2 bg-primary-500 rounded-full mr-2"></div>
                <span className="font-medium text-gray-900">{location.name}</span>
              </div>

              {/* Revenue */}
              <div className="text-center">
                <div className="font-semibold text-gray-900">{isBlank ? '—' : `$${location.revenue.toLocaleString()}`}</div>
                <div className={`text-xs ${getChangeColor(location.revenueChange || 0)}`}>
                  {getChangeIcon(location.revenueChange || 0)} {isBlank ? '—' : Math.abs(location.revenueChange).toString() + '%'}
                </div>
              </div>

              {/* Patients */}
              <div className="text-center">
                <div className="font-semibold text-gray-900">{isBlank ? '—' : location.patients.toLocaleString()}</div>
                <div className={`text-xs ${getChangeColor(location.patientChange || 0)}`}>
                  {getChangeIcon(location.patientChange || 0)} {isBlank ? '—' : Math.abs(location.patientChange).toString() + '%'}
                </div>
              </div>

              {/* Efficiency */}
              <div className="text-center">
                <div className="font-semibold text-gray-900">{isBlank ? '—' : `${location.efficiency}%`}</div>
                <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                  <div
                    className="bg-primary-500 h-1.5 rounded-full transition-all"
                    style={{ width: `${isBlank ? 0 : location.efficiency}%` }}
                  />
                </div>
              </div>

              {/* Status */}
              <div className="text-center">
                <span className="text-sm">{getStatusIndicator(location.status).text}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Summary */}
      <div className="mt-6 pt-4 border-t border-gray-100 flex items-center justify-between">
        <div className="text-sm text-gray-600">
          🎯 <span className="font-medium">Best Performer:</span> {isBlank ? '—' : data!.data.summary.bestPerformer}
        </div>
        <div className="text-sm text-gray-600">
          ⚠️ <span className="font-medium">Needs Attention:</span> {isBlank ? '—' : data!.data.summary.needsAttention}
        </div>
      </div>

      {/* Data Sources */}
      <div className="mt-2">
        <p className="text-xs text-gray-500">
          📊 Integrated data from Dentrix appointments, Eaglesoft financials, and DentalIntel benchmarks
        </p>
      </div>
    </div>
  );
};

export default LocationPerformance;

