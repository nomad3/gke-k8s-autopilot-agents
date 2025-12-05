import React from 'react';

const ManagerDashboard: React.FC = () => {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Manager Dashboard</h1>
        <p className="text-gray-600">Operational analytics and daily performance insights</p>
      </div>

      {/* Today's Overview (3x1) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Today's Performance</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Appointments:</span>
              <span className="font-semibold">32 scheduled</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Revenue:</span>
              <span className="font-semibold text-green-600">$8,420</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Efficiency:</span>
              <span className="font-semibold">78% of goal</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Staff Status</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Present:</span>
              <span className="font-semibold text-green-600">10/12</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Utilization:</span>
              <span className="font-semibold">91.7%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Remote:</span>
              <span className="font-semibold">2 staff</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Alerts</h3>
          <div className="space-y-2">
            <div className="text-sm text-red-600">🚨 2 Schedule conflicts</div>
            <div className="text-sm text-yellow-600">📞 3 Confirmations needed</div>
            <div className="text-sm text-blue-600">💊 1 Prescription renewal</div>
          </div>
        </div>
      </div>

      {/* Performance Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Weekly Performance Trends</h3>
          <div className="h-32 bg-gray-50 rounded-lg flex items-center justify-center">
            <p className="text-gray-500">Performance chart - Data from DentalIntel</p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Integration Health</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm">Dentrix Sync</span>
              <span className="text-green-600 text-sm">✅ Real-time</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Eaglesoft Billing</span>
              <span className="text-green-600 text-sm">✅ Connected</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">ADP Payroll</span>
              <span className="text-yellow-600 text-sm">🟡 Syncing</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">DentalIntel Analytics</span>
              <span className="text-green-600 text-sm">✅ Updated</span>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Analytics */}
      <div className="bg-white rounded-lg shadow border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Operational Insights</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-xl font-bold text-primary-600">$9,500</div>
            <div className="text-xs text-gray-500">Daily Goal</div>
            <div className="text-xs text-green-600">88.6% achieved</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold text-blue-600">12 min</div>
            <div className="text-xs text-gray-500">Avg Wait Time</div>
            <div className="text-xs text-green-600">Below target</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold text-green-600">96.2%</div>
            <div className="text-xs text-gray-500">Patient Satisfaction</div>
            <div className="text-xs text-green-600">Above benchmark</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold text-primary-600">85%</div>
            <div className="text-xs text-gray-500">Resource Utilization</div>
            <div className="text-xs text-gray-600">Within range</div>
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-gray-100">
          <p className="text-xs text-gray-500">
            📊 Real-time operational data aggregated from all integrated systems
          </p>
        </div>
      </div>
    </div>
  );
};

export default ManagerDashboard;
