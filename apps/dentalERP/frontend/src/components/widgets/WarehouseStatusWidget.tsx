import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { warehouseAPI } from '../../services/warehouse';

/**
 * Warehouse Status Widget
 * Displays Snowflake connection status and data layer information
 */
const WarehouseStatusWidget: React.FC = () => {
  const { data: status, isLoading, error, refetch } = useQuery({
    queryKey: ['warehouse-status'],
    queryFn: () => warehouseAPI.getStatus(),
    refetchInterval: 60000, // Refresh every minute
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow border p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-3/4"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow border p-6">
        <div className="flex items-center space-x-3 text-red-600">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p className="font-semibold">Warehouse Connection Error</p>
            <p className="text-sm text-gray-600">Failed to connect to Snowflake</p>
          </div>
        </div>
      </div>
    );
  }

  const isConnected = status?.connected;
  const lastUpdate = status?.timestamp ? new Date(status.timestamp).toLocaleString() : 'Unknown';

  return (
    <div className="bg-white rounded-lg shadow border p-6 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className={`w-12 h-12 rounded-xl ${isConnected ? 'bg-gradient-to-br from-blue-400 to-blue-600' : 'bg-gray-300'} flex items-center justify-center shadow-lg`}>
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Data Warehouse</h3>
            <p className="text-xs text-gray-500">Snowflake</p>
          </div>
        </div>
        <button
          onClick={() => refetch()}
          className="text-gray-400 hover:text-gray-600 transition-colors"
          title="Refresh status"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>

      {/* Connection Status */}
      <div className="mb-4">
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
          <span className={`text-sm font-semibold ${isConnected ? 'text-green-700' : 'text-red-700'}`}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Warehouse Info */}
      {status?.warehouse && (
        <div className="space-y-2 mb-4">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Warehouse:</span>
            <span className="font-medium text-gray-900">{status.warehouse.WAREHOUSE}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Database:</span>
            <span className="font-medium text-gray-900">{status.warehouse.DATABASE}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Version:</span>
            <span className="font-medium text-gray-900">{status.warehouse.VERSION}</span>
          </div>
        </div>
      )}

      {/* Data Layers */}
      {status?.layers && (
        <div className="pt-4 border-t border-gray-100">
          <p className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-3">Data Layers</p>
          <div className="grid grid-cols-3 gap-3">
            <div className="text-center">
              <div className="text-2xl font-bold text-amber-600">{status.layers.bronze.table_count}</div>
              <div className="text-xs text-gray-500">Bronze</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">{status.layers.silver.table_count}</div>
              <div className="text-xs text-gray-500">Silver</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{status.layers.gold.table_count}</div>
              <div className="text-xs text-gray-500">Gold</div>
            </div>
          </div>
        </div>
      )}

      {/* Last Update */}
      <div className="mt-4 pt-3 border-t border-gray-100">
        <div className="flex items-center space-x-1">
          <svg className="w-3 h-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-xs text-gray-500">Last updated: {lastUpdate}</p>
        </div>
      </div>
    </div>
  );
};

export default WarehouseStatusWidget;
