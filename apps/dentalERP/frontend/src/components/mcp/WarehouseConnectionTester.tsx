import React, { useState } from 'react';
import {
  CircleStackIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import mcpAPI from '../../services/mcpAPI';

export interface WarehouseConnection {
  type: 'snowflake' | 'redshift' | 'bigquery';
  account: string;
  warehouse: string;
  database: string;
  schema: string;
  username: string;
  password: string;
  role: string;
  project_id?: string;
  dataset?: string;
}

export interface WarehouseConnectionTesterProps {
  tenantId: string;
  onConnectionSuccess?: (stats: Record<string, any>) => void;
}

/**
 * WarehouseConnectionTester - Test and monitor warehouse connections
 * Features: Connection testing, statistics display, multi-warehouse support
 */
export const WarehouseConnectionTester: React.FC<WarehouseConnectionTesterProps> = ({
  tenantId,
  onConnectionSuccess,
}) => {
  const [connection, setConnection] = useState<WarehouseConnection>({
    type: 'snowflake',
    account: '',
    warehouse: '',
    database: '',
    schema: '',
    username: '',
    password: '',
    role: '',
  });
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message?: string;
    stats?: Record<string, any>;
  } | null>(null);

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      // Test connection
      const result = await mcpAPI.warehouse.testConnection(connection);

      if (result.success) {
        // Fetch statistics if connection is successful
        const stats = await mcpAPI.warehouse.getWarehouseStats(tenantId);

        setTestResult({
          success: true,
          message: `Successfully connected to ${connection.type} warehouse`,
          stats,
        });

        if (onConnectionSuccess) {
          onConnectionSuccess(stats);
        }
      } else {
        setTestResult({
          success: false,
          message: result.message || 'Connection failed',
        });
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: error instanceof Error ? error.message : 'Unknown error occurred',
      });
    } finally {
      setTesting(false);
    }
  };

  const handleChange = (field: keyof WarehouseConnection, value: string) => {
    setConnection(prev => ({ ...prev, [field]: value }));
  };

  const getFieldsForType = () => {
    switch (connection.type) {
      case 'snowflake':
        return [
          { name: 'account', label: 'Account', type: 'text', placeholder: 'your-account.snowflakecomputing.com' },
          { name: 'warehouse', label: 'Warehouse', type: 'text', placeholder: 'COMPUTE_WH' },
          { name: 'database', label: 'Database', type: 'text', placeholder: 'DENTALERP_DB' },
          { name: 'schema', label: 'Schema', type: 'text', placeholder: 'PUBLIC' },
          { name: 'role', label: 'Role', type: 'text', placeholder: 'ACCOUNTADMIN' },
          { name: 'username', label: 'Username', type: 'text', placeholder: 'admin' },
          { name: 'password', label: 'Password', type: 'password', placeholder: '••••••••' },
        ];
      case 'redshift':
        return [
          { name: 'host', label: 'Host', type: 'text', placeholder: 'cluster.region.redshift.amazonaws.com' },
          { name: 'port', label: 'Port', type: 'text', placeholder: '5439' },
          { name: 'database', label: 'Database', type: 'text', placeholder: 'dentalerp' },
          { name: 'username', label: 'Username', type: 'text', placeholder: 'admin' },
          { name: 'password', label: 'Password', type: 'password', placeholder: '••••••••' },
        ];
      case 'bigquery':
        return [
          { name: 'project_id', label: 'Project ID', type: 'text', placeholder: 'my-project' },
          { name: 'dataset', label: 'Dataset', type: 'text', placeholder: 'dentalerp' },
          { name: 'credentials_json', label: 'Service Account JSON', type: 'textarea', placeholder: '{ "type": "service_account", ... }' },
        ];
      default:
        return [];
    }
  };

  const fields = getFieldsForType();
  const isFormValid = fields.every(f => (connection as any)[f.name]);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      {/* Header */}
      <div className="flex items-center space-x-3 mb-6">
        <CircleStackIcon className="w-8 h-8 text-purple-600 dark:text-purple-400" />
        <div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">
            Data Warehouse Connection
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Test and configure your data warehouse connection
          </p>
        </div>
      </div>

      {/* Warehouse Type Selector */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Warehouse Type
        </label>
        <div className="grid grid-cols-3 gap-3">
          {(['snowflake', 'redshift', 'bigquery'] as const).map((type) => (
            <button
              key={type}
              onClick={() => setConnection(prev => ({ ...prev, type }))}
              className={`px-4 py-3 border-2 rounded-lg text-sm font-medium transition-all ${
                connection.type === type
                  ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300'
                  : 'border-gray-300 dark:border-gray-600 hover:border-purple-300 dark:hover:border-purple-700 text-gray-700 dark:text-gray-300'
              }`}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Configuration Form */}
      <div className="space-y-4 mb-6">
        {fields.map((field) => (
          <div key={field.name}>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {field.label}
            </label>
            {field.type === 'textarea' ? (
              <textarea
                value={(connection as any)[field.name] || ''}
                onChange={(e) => handleChange(field.name as keyof WarehouseConnection, e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-gray-750 text-gray-900 dark:text-white"
                placeholder={field.placeholder}
                rows={4}
              />
            ) : (
              <input
                type={field.type}
                value={(connection as any)[field.name] || ''}
                onChange={(e) => handleChange(field.name as keyof WarehouseConnection, e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-gray-750 text-gray-900 dark:text-white"
                placeholder={field.placeholder}
              />
            )}
          </div>
        ))}
      </div>

      {/* Test Button */}
      <button
        onClick={handleTest}
        disabled={testing || !isFormValid}
        className={`w-full flex items-center justify-center space-x-2 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
          testing || !isFormValid
            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
            : 'bg-purple-600 hover:bg-purple-700 text-white'
        }`}
      >
        {testing && <ArrowPathIcon className="w-5 h-5 animate-spin" />}
        <span>{testing ? 'Testing Connection...' : 'Test Connection'}</span>
      </button>

      {/* Test Result */}
      {testResult && (
        <div
          className={`mt-6 p-4 rounded-lg border animate-in slide-in-from-top-2 duration-300 ${
            testResult.success
              ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
              : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
          }`}
        >
          <div className="flex items-start space-x-3">
            {testResult.success ? (
              <CheckCircleIcon className="w-6 h-6 text-green-600 dark:text-green-400 flex-shrink-0" />
            ) : (
              <ExclamationCircleIcon className="w-6 h-6 text-red-600 dark:text-red-400 flex-shrink-0" />
            )}
            <div className="flex-1">
              <div
                className={`text-sm font-semibold ${
                  testResult.success
                    ? 'text-green-900 dark:text-green-100'
                    : 'text-red-900 dark:text-red-100'
                }`}
              >
                {testResult.success ? 'Connection Successful!' : 'Connection Failed'}
              </div>
              <div
                className={`text-sm mt-1 ${
                  testResult.success
                    ? 'text-green-700 dark:text-green-300'
                    : 'text-red-700 dark:text-red-300'
                }`}
              >
                {testResult.message}
              </div>

              {/* Display Statistics */}
              {testResult.success && testResult.stats && (
                <div className="mt-4 pt-4 border-t border-green-200 dark:border-green-800">
                  <div className="flex items-center space-x-2 mb-3">
                    <ChartBarIcon className="w-5 h-5 text-green-600 dark:text-green-400" />
                    <span className="text-sm font-semibold text-green-900 dark:text-green-100">
                      Warehouse Statistics
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    {Object.entries(testResult.stats).map(([key, value]) => (
                      <div
                        key={key}
                        className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-green-200 dark:border-green-800"
                      >
                        <div className="text-xs text-green-700 dark:text-green-300">
                          {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </div>
                        <div className="text-sm font-bold text-green-900 dark:text-green-100 mt-1">
                          {typeof value === 'number' ? value.toLocaleString() : String(value)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
