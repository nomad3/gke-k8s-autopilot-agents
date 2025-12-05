import React from 'react';
import { useTenant } from '../../contexts/TenantContext';

/**
 * TenantBadge - Visual indicator of current tenant
 * Shows tenant name and product count with color-coded status
 */
export const TenantBadge: React.FC<{
  variant?: 'default' | 'compact' | 'minimal';
  showProducts?: boolean;
}> = ({ variant = 'default', showProducts = true }) => {
  const { selectedTenant, isLoading } = useTenant();

  // Loading state
  if (isLoading) {
    return (
      <div className="inline-flex items-center space-x-2 px-3 py-1.5 bg-gray-100 dark:bg-gray-800 rounded-full animate-pulse">
        <div className="w-4 h-4 bg-gray-300 dark:bg-gray-700 rounded-full"></div>
        <div className="w-24 h-3 bg-gray-300 dark:bg-gray-700 rounded"></div>
      </div>
    );
  }

  // No tenant selected
  if (!selectedTenant) {
    return (
      <div className="inline-flex items-center space-x-2 px-3 py-1.5 bg-gray-100 dark:bg-gray-800 rounded-full text-gray-500 dark:text-gray-400 text-sm">
        <span className="text-xs">⚠️</span>
        <span>No tenant</span>
      </div>
    );
  }

  // Status color mapping
  const statusColors: Record<string, string> = {
    active: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 border-green-300 dark:border-green-700',
    inactive: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400 border-gray-300 dark:border-gray-700',
    suspended: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 border-red-300 dark:border-red-700',
  };

  const status = selectedTenant.status || 'active';
  const colorClass = statusColors[status] || statusColors.active;

  // Minimal variant (just icon)
  if (variant === 'minimal') {
    return (
      <div
        className={`inline-flex items-center justify-center w-8 h-8 rounded-full ${colorClass} border`}
        title={selectedTenant.tenant_name}
      >
        <span className="text-sm" role="img" aria-label="organization">
          🏢
        </span>
      </div>
    );
  }

  // Compact variant (icon + name only)
  if (variant === 'compact') {
    return (
      <div className={`inline-flex items-center space-x-2 px-2.5 py-1 rounded-full ${colorClass} border text-xs font-medium`}>
        <span className="text-xs" role="img" aria-label="organization">
          🏢
        </span>
        <span className="truncate max-w-[150px]">{selectedTenant.tenant_name}</span>
      </div>
    );
  }

  // Default variant (full details)
  return (
    <div className={`inline-flex items-center space-x-2 px-3 py-1.5 rounded-full ${colorClass} border`}>
      {/* Icon */}
      <span className="text-sm" role="img" aria-label="organization">
        🏢
      </span>

      {/* Tenant Name */}
      <span className="font-medium text-sm truncate max-w-[200px]">
        {selectedTenant.tenant_name}
      </span>

      {/* Product Count */}
      {showProducts && selectedTenant.products.length > 0 && (
        <>
          <span className="text-gray-400 dark:text-gray-500">·</span>
          <span className="text-xs font-normal">
            {selectedTenant.products.length} product{selectedTenant.products.length !== 1 ? 's' : ''}
          </span>
        </>
      )}
    </div>
  );
};
