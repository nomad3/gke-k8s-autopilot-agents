import React, { useState, useRef, useEffect } from 'react';
import { useTenant } from '../../contexts/TenantContext';
import { ChevronDownIcon, MagnifyingGlassIcon, CheckIcon } from '@heroicons/react/24/outline';

/**
 * TenantSwitcher - Dropdown component for switching between tenants
 * Placed in dashboard header for multi-tenant navigation
 */
export const TenantSwitcher: React.FC = () => {
  const { selectedTenant, tenants, isLoading, error, selectTenant } = useTenant();
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchQuery('');
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      // Focus search input when dropdown opens
      setTimeout(() => searchInputRef.current?.focus(), 100);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Filter tenants based on search query
  const filteredTenants = tenants.filter(tenant =>
    tenant.tenant_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    tenant.tenant_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
    tenant.products.some(product => product.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  // Handle tenant selection
  const handleSelectTenant = (tenantId: string) => {
    selectTenant(tenantId);
    setIsOpen(false);
    setSearchQuery('');
  };

  // Handle keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Escape') {
      setIsOpen(false);
      setSearchQuery('');
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center space-x-2 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse">
        <div className="w-6 h-6 bg-gray-300 dark:bg-gray-700 rounded"></div>
        <div className="w-32 h-4 bg-gray-300 dark:bg-gray-700 rounded"></div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center space-x-2 px-3 py-2 bg-red-50 dark:bg-red-900/20 rounded-lg text-red-600 dark:text-red-400 text-sm">
        <span>⚠️</span>
        <span>Failed to load tenants</span>
      </div>
    );
  }

  // No tenant selected
  if (!selectedTenant) {
    return (
      <div className="flex items-center space-x-2 px-3 py-2 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg text-yellow-600 dark:text-yellow-400 text-sm">
        <span>⚠️</span>
        <span>No tenant selected</span>
      </div>
    );
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-sky-500"
        aria-haspopup="true"
        aria-expanded={isOpen}
      >
        {/* Tenant Icon */}
        <span className="text-lg" role="img" aria-label="organization">
          🏢
        </span>

        {/* Tenant Name */}
        <div className="flex flex-col items-start">
          <span className="text-sm font-medium text-gray-900 dark:text-white">
            {selectedTenant.tenant_name}
          </span>
          {selectedTenant.products.length > 0 && (
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {selectedTenant.products.length} product{selectedTenant.products.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>

        {/* Dropdown Icon */}
        <ChevronDownIcon
          className={`w-5 h-5 text-gray-500 dark:text-gray-400 transition-transform duration-200 ${
            isOpen ? 'transform rotate-180' : ''
          }`}
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          className="absolute right-0 mt-2 w-96 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl z-50 overflow-hidden"
          onKeyDown={handleKeyDown}
        >
          {/* Search Input */}
          <div className="p-3 border-b border-gray-200 dark:border-gray-700">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search tenants..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
          </div>

          {/* Tenant List */}
          <div className="max-h-96 overflow-y-auto">
            {filteredTenants.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
                <p className="text-sm">No tenants found</p>
                {searchQuery && (
                  <p className="text-xs mt-1">Try a different search term</p>
                )}
              </div>
            ) : (
              filteredTenants.map((tenant) => {
                const isSelected = tenant.id === selectedTenant.id;
                const statusColor =
                  tenant.status === 'active'
                    ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                    : tenant.status === 'inactive'
                    ? 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'
                    : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';

                return (
                  <button
                    key={tenant.id}
                    onClick={() => handleSelectTenant(tenant.id)}
                    className={`w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors duration-150 border-b border-gray-100 dark:border-gray-700 last:border-b-0 ${
                      isSelected ? 'bg-sky-50 dark:bg-sky-900/20' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        {/* Tenant Name */}
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {tenant.tenant_name}
                          </span>
                          {isSelected && (
                            <CheckIcon className="w-4 h-4 text-sky-600 dark:text-sky-400 flex-shrink-0" />
                          )}
                        </div>

                        {/* Tenant Code */}
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                          {tenant.tenant_code}
                        </p>

                        {/* Products */}
                        {tenant.products.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {tenant.products.map((product) => (
                              <span
                                key={product}
                                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-400"
                              >
                                {product}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Status Badge */}
                      <div className="ml-3 flex-shrink-0">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${statusColor}`}
                        >
                          {tenant.status}
                        </span>
                      </div>
                    </div>
                  </button>
                );
              })
            )}
          </div>

          {/* Footer */}
          {filteredTenants.length > 0 && (
            <div className="px-4 py-2 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
              <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                {filteredTenants.length} tenant{filteredTenants.length !== 1 ? 's' : ''} available
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
