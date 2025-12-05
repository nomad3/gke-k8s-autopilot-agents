import React from 'react';

const ClinicianDashboard: React.FC = () => {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Clinical Analytics</h1>
        <p className="text-gray-600">Treatment outcomes and clinical performance insights</p>
      </div>

      {/* Clinical KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow border p-6 text-center">
          <div className="text-2xl font-bold text-healthcare-treatment">94.8%</div>
          <div className="text-sm text-gray-600">Treatment Success Rate</div>
          <div className="text-xs text-green-600 mt-1">↑ 2.1% vs last month</div>
        </div>

        <div className="bg-white rounded-lg shadow border p-6 text-center">
          <div className="text-2xl font-bold text-healthcare-patient">156</div>
          <div className="text-sm text-gray-600">Patients This Month</div>
          <div className="text-xs text-green-600 mt-1">↑ 8.3% vs last month</div>
        </div>

        <div className="bg-white rounded-lg shadow border p-6 text-center">
          <div className="text-2xl font-bold text-healthcare-appointment">28 min</div>
          <div className="text-sm text-gray-600">Avg Treatment Time</div>
          <div className="text-xs text-green-600 mt-1">↓ 5% efficiency gain</div>
        </div>

        <div className="bg-white rounded-lg shadow border p-6 text-center">
          <div className="text-2xl font-bold text-healthcare-wellness">4.9</div>
          <div className="text-sm text-gray-600">Patient Satisfaction</div>
          <div className="text-xs text-green-600 mt-1">Above 4.8 target</div>
        </div>
      </div>

      {/* Treatment Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Treatment Outcomes</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Preventive Care</span>
              <div className="flex items-center space-x-2">
                <div className="w-16 bg-gray-200 rounded-full h-2">
                  <div className="bg-healthcare-wellness h-2 rounded-full" style={{width: '92%'}}></div>
                </div>
                <span className="text-sm font-medium">92%</span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Restorative</span>
              <div className="flex items-center space-x-2">
                <div className="w-16 bg-gray-200 rounded-full h-2">
                  <div className="bg-healthcare-treatment h-2 rounded-full" style={{width: '88%'}}></div>
                </div>
                <span className="text-sm font-medium">88%</span>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Surgical</span>
              <div className="flex items-center space-x-2">
                <div className="w-16 bg-gray-200 rounded-full h-2">
                  <div className="bg-healthcare-medical h-2 rounded-full" style={{width: '95%'}}></div>
                </div>
                <span className="text-sm font-medium">95%</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-gray-100">
            <p className="text-xs text-gray-500">📊 Treatment data from Dentrix clinical records</p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Clinical Efficiency</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Chair Utilization</span>
                <span className="font-medium">85.2%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-primary-500 h-2 rounded-full" style={{width: '85.2%'}}></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">On-time Performance</span>
                <span className="font-medium">91.8%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{width: '91.8%'}}></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Treatment Completion</span>
                <span className="font-medium">96.4%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-healthcare-treatment h-2 rounded-full" style={{width: '96.4%'}}></div>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-gray-100">
            <p className="text-xs text-gray-500">📊 Efficiency metrics from Dentrix scheduling and completion data</p>
          </div>
        </div>
      </div>

      {/* Integration Status for Manager */}
      <div className="bg-white rounded-lg shadow border p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">System Integration Health</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-green-600 text-lg mb-1">🟢</div>
            <div className="text-sm font-medium">Dentrix</div>
            <div className="text-xs text-gray-500">Real-time sync</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-green-600 text-lg mb-1">🟢</div>
            <div className="text-sm font-medium">Eaglesoft</div>
            <div className="text-xs text-gray-500">Connected</div>
          </div>
          <div className="text-center p-3 bg-yellow-50 rounded-lg">
            <div className="text-yellow-600 text-lg mb-1">🟡</div>
            <div className="text-sm font-medium">ADP</div>
            <div className="text-xs text-gray-500">Syncing payroll</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-green-600 text-lg mb-1">🟢</div>
            <div className="text-sm font-medium">DentalIntel</div>
            <div className="text-xs text-gray-500">Analytics updated</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClinicianDashboard;
