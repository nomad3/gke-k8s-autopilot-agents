import React from 'react';
import { useStaffProductivity } from '../../hooks/useAnalytics';

const StaffProductivity: React.FC = () => {
  const { data, error } = useStaffProductivity('30d');
  const isBlank = !!error || !data?.data;

  const totals = isBlank
    ? { utilization: 0, avgAppointmentsPerProvider: 0, overtimeHours: 0, remoteStaff: 0 }
    : data!.data;

  // Placeholder top performers for demo; when API adds performers, this can be replaced
  const topPerformers = isBlank
    ? []
    : [
        { name: 'Team A', revenue: '$—', utilization: `${totals.utilization}%`, rating: 4.8 },
      ];

  return (
    <div className="bg-white rounded-lg shadow border p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Staff Productivity</h3>
          <p className="text-sm text-gray-600">Performance metrics and efficiency tracking</p>
        </div>
        <button className="text-primary-600 text-sm hover:text-primary-700">View All</button>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <div className="text-xl font-bold text-gray-900">{isBlank ? '—' : `${totals.utilization}%`}</div>
          <div className="text-xs text-gray-500">Avg Utilization</div>
        </div>
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <div className="text-xl font-bold text-green-600">{isBlank ? '—' : totals.avgAppointmentsPerProvider}</div>
          <div className="text-xs text-gray-500">Avg Appts/Provider</div>
        </div>
      </div>

      <div className="space-y-3">
        {topPerformers.length === 0 && (
          <div className="p-3 bg-gray-50 rounded-lg text-center text-sm text-gray-500">No data</div>
        )}
        {topPerformers.map((performer, index) => (
          <div key={performer.name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <div className="text-lg">
                {index === 0 ? '🏆' : index === 1 ? '🥈' : '🥉'}
              </div>
              <div>
                <div className="font-medium text-gray-900">{performer.name}</div>
                <div className="text-xs text-gray-500">Revenue/Day: {performer.revenue}</div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm font-semibold text-gray-900">{performer.utilization}</div>
              <div className="text-xs text-gray-500">⭐ {performer.rating}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-3 border-t border-gray-100">
        <p className="text-xs text-gray-500">
          📊 Productivity data from ADP timekeeping and Dentrix appointment completion rates
        </p>
      </div>
    </div>
  );
};

export default StaffProductivity;
