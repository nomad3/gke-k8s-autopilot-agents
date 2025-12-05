import React, { useState } from 'react';
import {
  XMarkIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import mcpAPI from '../../services/mcpAPI';

export interface IntegrationTestModalProps {
  isOpen: boolean;
  onClose: () => void;
  tenantId?: string;
  integrationType: string;
  integrationName: string;
}

/**
 * IntegrationTestModal - Modal for testing integration connections
 * Features: Configuration form, real-time testing, success/error feedback
 */
export const IntegrationTestModal: React.FC<IntegrationTestModalProps> = ({
  isOpen,
  onClose,
  tenantId,
  integrationType,
  integrationName,
}) => {
  const [config, setConfig] = useState<Record<string, string>>({
    endpoint: '',
    api_key: '',
    username: '',
    password: '',
  });
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message?: string;
  } | null>(null);

  if (!isOpen) return null;

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      const result = await mcpAPI.integration.testIntegration(
        tenantId || 'default',
        integrationType,
        config
      );

      setTestResult({
        success: result.success,
        message: result.success
          ? `Successfully connected to ${integrationName}`
          : result.message || 'Connection failed',
      });
    } catch (error) {
      setTestResult({
        success: false,
        message: error instanceof Error ? error.message : 'Unknown error occurred',
      });
    } finally {
      setTesting(false);
    }
  };

  const handleChange = (field: string, value: string) => {
    setConfig(prev => ({ ...prev, [field]: value }));
  };

  const getFieldsForType = () => {
    switch (integrationType.toLowerCase()) {
      case 'netsuite':
        return [
          { name: 'account_id', label: 'Account ID', type: 'text' },
          { name: 'consumer_key', label: 'Consumer Key', type: 'text' },
          { name: 'consumer_secret', label: 'Consumer Secret', type: 'password' },
          { name: 'token_id', label: 'Token ID', type: 'text' },
          { name: 'token_secret', label: 'Token Secret', type: 'password' },
        ];
      case 'adp':
        return [
          { name: 'client_id', label: 'Client ID', type: 'text' },
          { name: 'client_secret', label: 'Client Secret', type: 'password' },
          { name: 'api_endpoint', label: 'API Endpoint', type: 'text' },
        ];
      case 'dentrix':
        return [
          { name: 'server_url', label: 'Server URL', type: 'text' },
          { name: 'database_name', label: 'Database Name', type: 'text' },
          { name: 'username', label: 'Username', type: 'text' },
          { name: 'password', label: 'Password', type: 'password' },
        ];
      default:
        return [
          { name: 'endpoint', label: 'API Endpoint', type: 'text' },
          { name: 'api_key', label: 'API Key', type: 'password' },
        ];
    }
  };

  const fields = getFieldsForType();

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-50 animate-in fade-in duration-200"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div
          className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl pointer-events-auto animate-in zoom-in-95 duration-200"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                Test {integrationName} Connection
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Enter credentials and test the integration connection
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <XMarkIcon className="w-6 h-6 text-gray-500 dark:text-gray-400" />
            </button>
          </div>

          {/* Body */}
          <div className="p-6 space-y-6">
            {/* Configuration Form */}
            <div className="space-y-4">
              {fields.map((field) => (
                <div key={field.name}>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {field.label}
                  </label>
                  <input
                    type={field.type}
                    value={config[field.name] || ''}
                    onChange={(e) => handleChange(field.name, e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-transparent bg-white dark:bg-gray-750 text-gray-900 dark:text-white"
                    placeholder={`Enter ${field.label.toLowerCase()}`}
                  />
                </div>
              ))}
            </div>

            {/* Test Result */}
            {testResult && (
              <div
                className={`p-4 rounded-lg border animate-in slide-in-from-top-2 duration-300 ${
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
                  <div>
                    <div
                      className={`text-sm font-semibold ${
                        testResult.success
                          ? 'text-green-900 dark:text-green-100'
                          : 'text-red-900 dark:text-red-100'
                      }`}
                    >
                      {testResult.success ? 'Connection Successful' : 'Connection Failed'}
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
                  </div>
                </div>
              </div>
            )}

            {/* Help Text */}
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
              <div className="flex items-start space-x-3">
                <div className="text-blue-600 dark:text-blue-400 text-xl">💡</div>
                <div>
                  <div className="text-sm font-semibold text-blue-900 dark:text-blue-100">
                    Testing Tips
                  </div>
                  <ul className="text-sm text-blue-700 dark:text-blue-300 mt-2 space-y-1 list-disc list-inside">
                    <li>Ensure all required fields are filled correctly</li>
                    <li>Check that API credentials have proper permissions</li>
                    <li>Verify network connectivity to the service endpoint</li>
                    <li>Contact support if issues persist after verification</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors text-sm font-medium"
            >
              Cancel
            </button>
            <button
              onClick={handleTest}
              disabled={testing || fields.some(f => !config[f.name])}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                testing || fields.some(f => !config[f.name])
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-sky-600 hover:bg-sky-700 text-white'
              }`}
            >
              {testing && <ArrowPathIcon className="w-4 h-4 animate-spin" />}
              <span>{testing ? 'Testing...' : 'Test Connection'}</span>
            </button>
          </div>
        </div>
      </div>
    </>
  );
};
