import React, { useState } from 'react';
import {
  BellIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  XMarkIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline';

export type AlertSeverity = 'critical' | 'warning' | 'info' | 'success';

export interface Alert {
  id: string;
  title: string;
  message: string;
  severity: AlertSeverity;
  metric?: string;
  value?: string | number;
  threshold?: string | number;
  timestamp: string;
  practice?: string;
  actionable?: boolean;
  dismissed?: boolean;
}

export interface AlertsPanelProps {
  alerts: Alert[];
  onDismiss?: (alertId: string) => void;
  onAction?: (alertId: string) => void;
  loading?: boolean;
  collapsible?: boolean;
}

/**
 * AlertsPanel - Display KPI alerts and notifications
 * Shows critical issues, warnings, and important updates
 */
export const AlertsPanel: React.FC<AlertsPanelProps> = ({
  alerts,
  onDismiss,
  onAction,
  loading = false,
  collapsible = true,
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const [filterSeverity, setFilterSeverity] = useState<AlertSeverity | 'all'>('all');

  // Filter alerts by severity
  const filteredAlerts = alerts.filter(alert => {
    if (filterSeverity === 'all') return !alert.dismissed;
    return alert.severity === filterSeverity && !alert.dismissed;
  });

  // Group alerts by severity
  const alertCounts = {
    critical: alerts.filter(a => a.severity === 'critical' && !a.dismissed).length,
    warning: alerts.filter(a => a.severity === 'warning' && !a.dismissed).length,
    info: alerts.filter(a => a.severity === 'info' && !a.dismissed).length,
    success: alerts.filter(a => a.severity === 'success' && !a.dismissed).length,
  };

  // Get severity config
  const getSeverityConfig = (severity: AlertSeverity) => {
    switch (severity) {
      case 'critical':
        return {
          icon: ExclamationTriangleIcon,
          color: 'text-red-700 dark:text-red-400',
          bgColor: 'bg-red-50 dark:bg-red-900/20',
          borderColor: 'border-red-200 dark:border-red-800',
          badgeColor: 'bg-red-500',
          label: 'Critical',
        };
      case 'warning':
        return {
          icon: ExclamationTriangleIcon,
          color: 'text-orange-700 dark:text-orange-400',
          bgColor: 'bg-orange-50 dark:bg-orange-900/20',
          borderColor: 'border-orange-200 dark:border-orange-800',
          badgeColor: 'bg-orange-500',
          label: 'Warning',
        };
      case 'info':
        return {
          icon: InformationCircleIcon,
          color: 'text-blue-700 dark:text-blue-400',
          bgColor: 'bg-blue-50 dark:bg-blue-900/20',
          borderColor: 'border-blue-200 dark:border-blue-800',
          badgeColor: 'bg-blue-500',
          label: 'Info',
        };
      case 'success':
        return {
          icon: CheckCircleIcon,
          color: 'text-green-700 dark:text-green-400',
          bgColor: 'bg-green-50 dark:bg-green-900/20',
          borderColor: 'border-green-200 dark:border-green-800',
          badgeColor: 'bg-green-500',
          label: 'Success',
        };
    }
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  // Loading skeleton
  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="animate-pulse space-y-4">
          <div className="w-48 h-6 bg-gray-300 dark:bg-gray-700 rounded"></div>
          <div className="w-full h-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
          <div className="w-full h-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <BellIcon className="w-6 h-6 text-gray-700 dark:text-gray-300" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Alerts & Notifications
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {filteredAlerts.length} active alert{filteredAlerts.length !== 1 ? 's' : ''}
              </p>
            </div>
          </div>

          {collapsible && (
            <button
              onClick={() => setCollapsed(!collapsed)}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-750 rounded-lg transition-colors"
            >
              {collapsed ? (
                <ChevronDownIcon className="w-5 h-5 text-gray-500" />
              ) : (
                <ChevronUpIcon className="w-5 h-5 text-gray-500" />
              )}
            </button>
          )}
        </div>

        {/* Filter Tabs */}
        {!collapsed && (
          <div className="flex items-center space-x-2 mt-4 overflow-x-auto">
            <button
              onClick={() => setFilterSeverity('all')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                filterSeverity === 'all'
                  ? 'bg-gray-900 dark:bg-gray-700 text-white'
                  : 'bg-gray-100 dark:bg-gray-750 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
            >
              All ({alerts.filter(a => !a.dismissed).length})
            </button>

            {alertCounts.critical > 0 && (
              <button
                onClick={() => setFilterSeverity('critical')}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center space-x-1 whitespace-nowrap ${
                  filterSeverity === 'critical'
                    ? 'bg-red-500 text-white'
                    : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-900/50'
                }`}
              >
                <span>Critical</span>
                <span className="bg-white/30 px-1.5 py-0.5 rounded text-xs">
                  {alertCounts.critical}
                </span>
              </button>
            )}

            {alertCounts.warning > 0 && (
              <button
                onClick={() => setFilterSeverity('warning')}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center space-x-1 whitespace-nowrap ${
                  filterSeverity === 'warning'
                    ? 'bg-orange-500 text-white'
                    : 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 hover:bg-orange-200 dark:hover:bg-orange-900/50'
                }`}
              >
                <span>Warning</span>
                <span className="bg-white/30 px-1.5 py-0.5 rounded text-xs">
                  {alertCounts.warning}
                </span>
              </button>
            )}

            {alertCounts.info > 0 && (
              <button
                onClick={() => setFilterSeverity('info')}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center space-x-1 whitespace-nowrap ${
                  filterSeverity === 'info'
                    ? 'bg-blue-500 text-white'
                    : 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50'
                }`}
              >
                <span>Info</span>
                <span className="bg-white/30 px-1.5 py-0.5 rounded text-xs">
                  {alertCounts.info}
                </span>
              </button>
            )}

            {alertCounts.success > 0 && (
              <button
                onClick={() => setFilterSeverity('success')}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center space-x-1 whitespace-nowrap ${
                  filterSeverity === 'success'
                    ? 'bg-green-500 text-white'
                    : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-900/50'
                }`}
              >
                <span>Success</span>
                <span className="bg-white/30 px-1.5 py-0.5 rounded text-xs">
                  {alertCounts.success}
                </span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Alerts List */}
      {!collapsed && (
        <div className="max-h-96 overflow-y-auto">
          {filteredAlerts.length === 0 ? (
            <div className="p-12 text-center">
              <CheckCircleIcon className="w-12 h-12 text-green-500 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400">
                {filterSeverity === 'all'
                  ? 'No active alerts - everything looks good!'
                  : `No ${filterSeverity} alerts`}
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredAlerts.map((alert) => {
                const config = getSeverityConfig(alert.severity);
                const AlertIcon = config.icon;

                return (
                  <div
                    key={alert.id}
                    className={`p-4 ${config.bgColor} border-l-4 ${config.borderColor} hover:shadow-md transition-shadow`}
                  >
                    <div className="flex items-start space-x-3">
                      {/* Icon */}
                      <AlertIcon className={`w-6 h-6 flex-shrink-0 ${config.color}`} />

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-1">
                              <h4 className={`text-sm font-semibold ${config.color}`}>
                                {alert.title}
                              </h4>
                              {alert.practice && (
                                <span className="text-xs bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-2 py-0.5 rounded">
                                  {alert.practice}
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                              {alert.message}
                            </p>

                            {/* Metric Details */}
                            {alert.metric && (
                              <div className="flex items-center space-x-4 text-xs text-gray-600 dark:text-gray-400 mb-2">
                                <span>
                                  <strong>Metric:</strong> {alert.metric}
                                </span>
                                {alert.value && (
                                  <span>
                                    <strong>Value:</strong> {alert.value}
                                  </span>
                                )}
                                {alert.threshold && (
                                  <span>
                                    <strong>Threshold:</strong> {alert.threshold}
                                  </span>
                                )}
                              </div>
                            )}

                            <div className="flex items-center space-x-3">
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                {formatTimestamp(alert.timestamp)}
                              </span>

                              {alert.actionable && onAction && (
                                <button
                                  onClick={() => onAction(alert.id)}
                                  className={`text-xs font-medium ${config.color} hover:underline`}
                                >
                                  Take Action →
                                </button>
                              )}
                            </div>
                          </div>

                          {/* Dismiss Button */}
                          {onDismiss && (
                            <button
                              onClick={() => onDismiss(alert.id)}
                              className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors flex-shrink-0"
                              title="Dismiss"
                            >
                              <XMarkIcon className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Summary Footer (when collapsed) */}
      {collapsed && (
        <div className="p-4 flex items-center justify-between text-sm">
          <div className="flex items-center space-x-4">
            {alertCounts.critical > 0 && (
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                <span className="text-gray-700 dark:text-gray-300">
                  {alertCounts.critical} Critical
                </span>
              </div>
            )}
            {alertCounts.warning > 0 && (
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                <span className="text-gray-700 dark:text-gray-300">
                  {alertCounts.warning} Warning
                </span>
              </div>
            )}
            {alertCounts.info > 0 && (
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span className="text-gray-700 dark:text-gray-300">
                  {alertCounts.info} Info
                </span>
              </div>
            )}
          </div>
          <span className="text-gray-500 dark:text-gray-400">
            Click to expand
          </span>
        </div>
      )}
    </div>
  );
};
