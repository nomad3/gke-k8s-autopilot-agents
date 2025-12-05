import React, { useState } from 'react';
import {
  PencilIcon,
  TrashIcon,
  KeyIcon,
  CircleStackIcon,
  PuzzlePieceIcon,
  CheckCircleIcon,
  XCircleIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline';
import { Tenant } from '../../services/mcpAPI';

export interface TenantCardProps {
  tenant: Tenant;
  onEdit?: (tenant: Tenant) => void;
  onDelete?: (tenantId: string) => void;
  onViewWarehouses?: (tenant: Tenant) => void;
  onViewIntegrations?: (tenant: Tenant) => void;
  onManageAPIKeys?: (tenant: Tenant) => void;
}

/**
 * TenantCard - Beautiful, interactive card for displaying tenant information
 * Features: Expandable details, action buttons, status indicators, smooth animations
 */
export const TenantCard: React.FC<TenantCardProps> = ({
  tenant,
  onEdit,
  onDelete,
  onViewWarehouses,
  onViewIntegrations,
  onManageAPIKeys,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const isActive = tenant.status === 'active';

  return (
    <div
      className={`group bg-white dark:bg-gray-800 rounded-xl border-2 transition-all duration-300 ${
        isActive
          ? 'border-gray-200 dark:border-gray-700 hover:border-sky-400 dark:hover:border-sky-500'
          : 'border-gray-300 dark:border-gray-600 opacity-75'
      } hover:shadow-xl transform hover:-translate-y-1`}
    >
      {/* Main Content */}
      <div className="p-6">
        {/* Header Row */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            {/* Title & Code */}
            <div className="flex items-center space-x-3 mb-2">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                {tenant.tenant_name}
              </h3>
              <span className="px-3 py-1 bg-gradient-to-r from-sky-100 to-blue-100 dark:from-sky-900/30 dark:to-blue-900/30 text-sky-700 dark:text-sky-300 text-sm font-mono rounded-full">
                {tenant.tenant_code}
              </span>

              {/* Status Badge */}
              {isActive ? (
                <span className="flex items-center space-x-1 px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs rounded-full">
                  <CheckCircleIcon className="w-4 h-4" />
                  <span>Active</span>
                </span>
              ) : (
                <span className="flex items-center space-x-1 px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 text-xs rounded-full">
                  <XCircleIcon className="w-4 h-4" />
                  <span>Inactive</span>
                </span>
              )}
            </div>

            {/* Industry Badge */}
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">Industry:</span>
              <span className="px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 text-sm rounded capitalize">
                {tenant.industry}
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            {onEdit && (
              <button
                onClick={() => onEdit(tenant)}
                className="p-2 hover:bg-sky-100 dark:hover:bg-sky-900/30 text-sky-600 dark:text-sky-400 rounded-lg transition-colors"
                title="Edit Tenant"
              >
                <PencilIcon className="w-5 h-5" />
              </button>
            )}

            {onDelete && (
              <div className="relative">
                {!showDeleteConfirm ? (
                  <button
                    onClick={() => setShowDeleteConfirm(true)}
                    className="p-2 hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400 rounded-lg transition-colors"
                    title="Delete Tenant"
                  >
                    <TrashIcon className="w-5 h-5" />
                  </button>
                ) : (
                  <div className="flex items-center space-x-1 animate-in fade-in slide-in-from-right-2 duration-200">
                    <button
                      onClick={() => {
                        onDelete(tenant.id!);
                        setShowDeleteConfirm(false);
                      }}
                      className="px-2 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded transition-colors"
                    >
                      Confirm
                    </button>
                    <button
                      onClick={() => setShowDeleteConfirm(false)}
                      className="px-2 py-1 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-xs rounded transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          {/* Products */}
          <div className="bg-gradient-to-br from-blue-50 to-sky-50 dark:from-blue-900/20 dark:to-sky-900/20 rounded-lg p-3 border border-blue-200 dark:border-blue-800">
            <div className="flex items-center space-x-2 mb-1">
              <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm font-bold">P</span>
              </div>
              <span className="text-xs text-gray-600 dark:text-gray-400">Products</span>
            </div>
            <div className="text-2xl font-bold text-blue-700 dark:text-blue-400">
              {tenant.products?.length || 0}
            </div>
          </div>

          {/* Warehouses */}
          <div
            className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-lg p-3 border border-purple-200 dark:border-purple-800 cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => onViewWarehouses?.(tenant)}
          >
            <div className="flex items-center space-x-2 mb-1">
              <CircleStackIcon className="w-8 h-8 text-purple-600 dark:text-purple-400" />
              <span className="text-xs text-gray-600 dark:text-gray-400">Warehouses</span>
            </div>
            <div className="text-2xl font-bold text-purple-700 dark:text-purple-400">
              {tenant.warehouses?.length || 0}
            </div>
          </div>

          {/* Integrations */}
          <div
            className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg p-3 border border-green-200 dark:border-green-800 cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => onViewIntegrations?.(tenant)}
          >
            <div className="flex items-center space-x-2 mb-1">
              <PuzzlePieceIcon className="w-8 h-8 text-green-600 dark:text-green-400" />
              <span className="text-xs text-gray-600 dark:text-gray-400">Integrations</span>
            </div>
            <div className="text-2xl font-bold text-green-700 dark:text-green-400">
              {tenant.integrations?.length || 0}
            </div>
          </div>

          {/* API Keys */}
          <div
            className="bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-900/20 dark:to-amber-900/20 rounded-lg p-3 border border-orange-200 dark:border-orange-800 cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => onManageAPIKeys?.(tenant)}
          >
            <div className="flex items-center space-x-2 mb-1">
              <KeyIcon className="w-8 h-8 text-orange-600 dark:text-orange-400" />
              <span className="text-xs text-gray-600 dark:text-gray-400">API Keys</span>
            </div>
            <div className="text-2xl font-bold text-orange-700 dark:text-orange-400">
              {tenant.api_keys?.length || 0}
            </div>
          </div>
        </div>

        {/* Expand/Collapse Button */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-center space-x-2 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
        >
          <span>{isExpanded ? 'Hide Details' : 'Show Details'}</span>
          {isExpanded ? (
            <ChevronUpIcon className="w-4 h-4" />
          ) : (
            <ChevronDownIcon className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-6 animate-in slide-in-from-top-2 duration-300">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Products List */}
            {tenant.products && tenant.products.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center space-x-2">
                  <div className="w-6 h-6 bg-blue-500 rounded flex items-center justify-center">
                    <span className="text-white text-xs font-bold">P</span>
                  </div>
                  <span>Products</span>
                </h4>
                <div className="flex flex-wrap gap-2">
                  {tenant.products.map((product, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-sm rounded-full"
                    >
                      {product}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Timestamps */}
            <div>
              <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
                Timestamps
              </h4>
              <div className="space-y-2 text-sm">
                {tenant.created_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Created:</span>
                    <span className="text-gray-900 dark:text-white">
                      {new Date(tenant.created_at).toLocaleDateString()}
                    </span>
                  </div>
                )}
                {tenant.updated_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Updated:</span>
                    <span className="text-gray-900 dark:text-white">
                      {new Date(tenant.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                )}
                {tenant.id && (
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Tenant ID:</span>
                    <span className="text-gray-900 dark:text-white font-mono text-xs">
                      {tenant.id.substring(0, 8)}...
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Action Buttons Row */}
          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700 flex flex-wrap gap-3">
            {onViewWarehouses && (
              <button
                onClick={() => onViewWarehouses(tenant)}
                className="flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors text-sm"
              >
                <CircleStackIcon className="w-4 h-4" />
                <span>Manage Warehouses</span>
              </button>
            )}

            {onViewIntegrations && (
              <button
                onClick={() => onViewIntegrations(tenant)}
                className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors text-sm"
              >
                <PuzzlePieceIcon className="w-4 h-4" />
                <span>Configure Integrations</span>
              </button>
            )}

            {onManageAPIKeys && (
              <button
                onClick={() => onManageAPIKeys(tenant)}
                className="flex items-center space-x-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-colors text-sm"
              >
                <KeyIcon className="w-4 h-4" />
                <span>Manage API Keys</span>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
