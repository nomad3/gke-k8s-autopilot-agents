import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ServerIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  CpuChipIcon,
} from '@heroicons/react/24/outline';
import mcpAPI from '../../services/mcpAPI';

export interface MCPServerStatusProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

/**
 * MCPServerStatus - Real-time MCP server health monitoring
 * Shows server status, version, uptime, and connection stats
 */
export const MCPServerStatus: React.FC<MCPServerStatusProps> = ({
  autoRefresh = true,
  refreshInterval = 5000,
}) => {
  // Fetch server health
  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['mcp-health'],
    queryFn: mcpAPI.health.getHealth,
    refetchInterval: autoRefresh ? refreshInterval : false,
    retry: 3,
  });

  // Fetch server info
  const { data: serverInfo, isLoading: infoLoading } = useQuery({
    queryKey: ['mcp-server-info'],
    queryFn: mcpAPI.health.getServerInfo,
    refetchInterval: autoRefresh ? refreshInterval : false,
    retry: 3,
  });

  const isLoading = healthLoading || infoLoading;
  const isHealthy = health?.status === 'healthy' || health?.status === 'ok';
  const isOnline = serverInfo?.status === 'running';

  // Format uptime
  const formatUptime = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="animate-pulse space-y-4">
          <div className="w-48 h-6 bg-gray-300 dark:bg-gray-700 rounded"></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="w-full h-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
            <div className="w-full h-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <ServerIcon className="w-8 h-8 text-sky-600 dark:text-sky-400" />
          <div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">
              MCP Server Status
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Mapping & Control Plane
            </p>
          </div>
        </div>

        {/* Status Badge */}
        <div className={`flex items-center space-x-2 px-4 py-2 rounded-full ${
          isHealthy && isOnline
            ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
            : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
        }`}>
          {isHealthy && isOnline ? (
            <>
              <CheckCircleIcon className="w-5 h-5" />
              <span className="text-sm font-semibold">Online</span>
            </>
          ) : (
            <>
              <ExclamationTriangleIcon className="w-5 h-5" />
              <span className="text-sm font-semibold">Offline</span>
            </>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Version */}
        <div className="bg-gray-50 dark:bg-gray-750 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2 mb-2">
            <CpuChipIcon className="w-5 h-5 text-gray-500 dark:text-gray-400" />
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Version
            </span>
          </div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {serverInfo?.version || 'N/A'}
          </div>
        </div>

        {/* Uptime */}
        <div className="bg-gray-50 dark:bg-gray-750 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2 mb-2">
            <ClockIcon className="w-5 h-5 text-gray-500 dark:text-gray-400" />
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Uptime
            </span>
          </div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white">
            {formatUptime(health?.uptime)}
          </div>
        </div>

        {/* Database Status */}
        <div className="bg-gray-50 dark:bg-gray-750 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2 mb-2">
            <ServerIcon className="w-5 h-5 text-gray-500 dark:text-gray-400" />
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Database
            </span>
          </div>
          <div className="flex items-center space-x-2">
            {health?.database === 'connected' || health?.database === 'ok' ? (
              <>
                <CheckCircleIcon className="w-5 h-5 text-green-600 dark:text-green-400" />
                <span className="text-sm font-semibold text-green-700 dark:text-green-400">
                  Connected
                </span>
              </>
            ) : (
              <>
                <ExclamationTriangleIcon className="w-5 h-5 text-red-600 dark:text-red-400" />
                <span className="text-sm font-semibold text-red-700 dark:text-red-400">
                  Disconnected
                </span>
              </>
            )}
          </div>
        </div>

        {/* Snowflake Status */}
        <div className="bg-gray-50 dark:bg-gray-750 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2 mb-2">
            <ServerIcon className="w-5 h-5 text-gray-500 dark:text-gray-400" />
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Snowflake
            </span>
          </div>
          <div className="flex items-center space-x-2">
            {health?.snowflake === 'connected' || health?.snowflake === 'ok' ? (
              <>
                <CheckCircleIcon className="w-5 h-5 text-green-600 dark:text-green-400" />
                <span className="text-sm font-semibold text-green-700 dark:text-green-400">
                  Connected
                </span>
              </>
            ) : (
              <>
                <ExclamationTriangleIcon className="w-5 h-5 text-orange-600 dark:text-orange-400" />
                <span className="text-sm font-semibold text-orange-700 dark:text-orange-400">
                  Not Configured
                </span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Additional Info */}
      {serverInfo?.docs && (
        <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">
              API Documentation
            </span>
            <a
              href={`http://localhost:8085${serverInfo.docs}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sky-600 hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300 font-medium"
            >
              View Swagger Docs →
            </a>
          </div>
        </div>
      )}

      {/* Auto-refresh indicator */}
      {autoRefresh && (
        <div className="mt-4 flex items-center justify-center text-xs text-gray-500 dark:text-gray-400">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span>Auto-refreshing every {refreshInterval / 1000}s</span>
          </div>
        </div>
      )}
    </div>
  );
};
