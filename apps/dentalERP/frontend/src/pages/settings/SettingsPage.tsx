import React, { useState } from 'react';
import ReportGenerator from '../../components/reports/ReportGenerator';
import { useAuthStore } from '../../store/authStore';

const SettingsPage: React.FC = () => {
  const user = useAuthStore(state => state.user);
  const [activeTab, setActiveTab] = useState('dashboard');

  const tabs = [
    { id: 'dashboard', name: 'Dashboard', icon: '📊' },
    { id: 'reports', name: 'Reports', icon: '📄' },
    { id: 'integrations', name: 'Integrations', icon: '🔗' },
    { id: 'notifications', name: 'Notifications', icon: '🔔' },
    { id: 'profile', name: 'Profile', icon: '👤' }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Dashboard Preferences</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Default Dashboard View
                  </label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-md">
                    <option>Auto (Based on Role)</option>
                    <option>Executive Overview</option>
                    <option>Manager Operations</option>
                    <option>Clinical Analytics</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Data Refresh Rate
                  </label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-md">
                    <option>Real-time (30 seconds)</option>
                    <option>Every 2 minutes</option>
                    <option>Every 5 minutes</option>
                    <option>Every 15 minutes</option>
                  </select>
                </div>

                <div>
                  <label className="flex items-center">
                    <input type="checkbox" className="text-primary-600 focus:ring-primary-500" />
                    <span className="ml-2 text-sm text-gray-700">Show integration status in header</span>
                  </label>
                </div>

                <div>
                  <label className="flex items-center">
                    <input type="checkbox" className="text-primary-600 focus:ring-primary-500" />
                    <span className="ml-2 text-sm text-gray-700">Enable sound notifications for alerts</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        );

      case 'reports':
        return <ReportGenerator />;

      case 'integrations':
        return (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Integration Settings</h3>

              <div className="space-y-4">
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900">Data Sync Frequency</h4>
                      <p className="text-sm text-gray-600">How often to sync data from external systems</p>
                    </div>
                    <select className="px-3 py-2 border border-gray-300 rounded-md">
                      <option>Every 5 minutes</option>
                      <option>Every 15 minutes</option>
                      <option>Every hour</option>
                    </select>
                  </div>
                </div>

                <div className="border border-gray-200 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-3">External System Priorities</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-700">Dentrix (Patient Data)</span>
                      <select className="px-2 py-1 text-xs border border-gray-300 rounded">
                        <option>High Priority</option>
                        <option>Normal</option>
                        <option>Low</option>
                      </select>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-700">DentalIntel (Analytics)</span>
                      <select className="px-2 py-1 text-xs border border-gray-300 rounded">
                        <option>High Priority</option>
                        <option>Normal</option>
                        <option>Low</option>
                      </select>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-700">Eaglesoft (Financial)</span>
                      <select className="px-2 py-1 text-xs border border-gray-300 rounded">
                        <option>High Priority</option>
                        <option>Normal</option>
                        <option>Low</option>
                      </select>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-700">ADP (Staff Data)</span>
                      <select className="px-2 py-1 text-xs border border-gray-300 rounded">
                        <option>High Priority</option>
                        <option>Normal</option>
                        <option>Low</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 'notifications':
        return (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">BI Alert Preferences</h3>

              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Performance Alerts</h4>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input type="checkbox" className="text-primary-600 focus:ring-primary-500" defaultChecked />
                      <span className="ml-2 text-sm text-gray-700">Revenue drops below target</span>
                    </label>
                    <label className="flex items-center">
                      <input type="checkbox" className="text-primary-600 focus:ring-primary-500" defaultChecked />
                      <span className="ml-2 text-sm text-gray-700">Location efficiency falls below 85%</span>
                    </label>
                    <label className="flex items-center">
                      <input type="checkbox" className="text-primary-600 focus:ring-primary-500" />
                      <span className="ml-2 text-gray-700">Staff productivity changes</span>
                    </label>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Integration Alerts</h4>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input type="checkbox" className="text-primary-600 focus:ring-primary-500" defaultChecked />
                      <span className="ml-2 text-sm text-gray-700">System disconnections</span>
                    </label>
                    <label className="flex items-center">
                      <input type="checkbox" className="text-primary-600 focus:ring-primary-500" defaultChecked />
                      <span className="ml-2 text-sm text-gray-700">Sync failures</span>
                    </label>
                    <label className="flex items-center">
                      <input type="checkbox" className="text-primary-600 focus:ring-primary-500" />
                      <span className="ml-2 text-sm text-gray-700">Data quality issues</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 'profile':
        return (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Profile Information</h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                  <input
                    type="text"
                    value={user?.firstName || ''}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    readOnly
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                  <input
                    type="text"
                    value={user?.lastName || ''}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    readOnly
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    value={user?.email || ''}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    readOnly
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                  <input
                    type="text"
                    value={user?.role || ''}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 capitalize"
                    readOnly
                  />
                </div>
              </div>

              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Practice Access</label>
                <div className="text-sm text-gray-600">
                  You have access to {user?.practiceIds?.length || 0} practice location(s)
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">BI Dashboard Settings</h1>
        <p className="text-gray-600">Configure your business intelligence dashboard preferences</p>
      </div>

      {/* Tab Navigation */}
      <div className="mb-6">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.name}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {renderTabContent()}
    </div>
  );
};

export default SettingsPage;
