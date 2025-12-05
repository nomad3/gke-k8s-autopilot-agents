import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ServerIcon,
  UserGroupIcon,
  PuzzlePieceIcon,
  CircleStackIcon,
  PlusIcon,
} from '@heroicons/react/24/outline';
import { MCPServerStatus } from '../../components/mcp/MCPServerStatus';
import mcpAPI, { Tenant } from '../../services/mcpAPI';

type TabType = 'status' | 'tenants' | 'integrations' | 'warehouses';

/**
 * MCPServerManagementPage - Admin interface for managing the MCP Server
 * Provides tabs for: Server Status, Tenant Management, Integrations, Warehouses
 */
export const MCPServerManagementPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('status');
  const [showCreateTenant, setShowCreateTenant] = useState(false);
  const queryClient = useQueryClient();

  // Fetch tenants
  const { data: tenants, isLoading: tenantsLoading } = useQuery({
    queryKey: ['mcp-tenants'],
    queryFn: mcpAPI.tenant.getTenants,
    enabled: activeTab === 'tenants',
  });

  // Fetch integrations
  const { data: integrations, isLoading: integrationsLoading } = useQuery({
    queryKey: ['mcp-integrations'],
    queryFn: mcpAPI.integration.getIntegrations,
    enabled: activeTab === 'integrations',
  });

  // Create tenant mutation
  const createTenantMutation = useMutation({
    mutationFn: mcpAPI.tenant.createTenant,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-tenants'] });
      setShowCreateTenant(false);
    },
  });

  // Tabs configuration
  const tabs = [
    { id: 'status' as TabType, name: 'Server Status', icon: ServerIcon },
    { id: 'tenants' as TabType, name: 'Tenants', icon: UserGroupIcon },
    { id: 'integrations' as TabType, name: 'Integrations', icon: PuzzlePieceIcon },
    { id: 'warehouses' as TabType, name: 'Warehouses', icon: CircleStackIcon },
  ];

  // Handle create tenant
  const handleCreateTenant = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const tenant: Tenant = {
      tenant_code: formData.get('tenant_code') as string,
      tenant_name: formData.get('tenant_name') as string,
      industry: formData.get('industry') as string,
      products: (formData.get('products') as string).split(',').map(p => p.trim()),
    };
    createTenantMutation.mutate(tenant);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center space-x-3">
            <ServerIcon className="w-10 h-10 text-sky-600" />
            <span>MCP Server Management</span>
          </h1>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            Configure and monitor the Mapping & Control Plane Server
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  isActive
                    ? 'border-sky-500 text-sky-600 dark:text-sky-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{tab.name}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {/* Status Tab */}
        {activeTab === 'status' && (
          <div className="space-y-6">
            <MCPServerStatus autoRefresh={true} refreshInterval={5000} />

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Total Tenants
                    </p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                      {tenants?.length || 0}
                    </p>
                  </div>
                  <UserGroupIcon className="w-12 h-12 text-sky-600 dark:text-sky-400" />
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Active Integrations
                    </p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                      {integrations?.length || 0}
                    </p>
                  </div>
                  <PuzzlePieceIcon className="w-12 h-12 text-green-600 dark:text-green-400" />
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Warehouses
                    </p>
                    <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                      {tenants?.reduce((sum, t) => sum + (t.warehouses?.length || 0), 0) || 0}
                    </p>
                  </div>
                  <CircleStackIcon className="w-12 h-12 text-purple-600 dark:text-purple-400" />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tenants Tab */}
        {activeTab === 'tenants' && (
          <div className="space-y-6">
            {/* Header with Create Button */}
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Tenant Management
              </h2>
              <button
                onClick={() => setShowCreateTenant(!showCreateTenant)}
                className="inline-flex items-center space-x-2 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg transition-colors"
              >
                <PlusIcon className="w-5 h-5" />
                <span>Create Tenant</span>
              </button>
            </div>

            {/* Create Tenant Form */}
            {showCreateTenant && (
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Create New Tenant
                </h3>
                <form onSubmit={handleCreateTenant} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Tenant Code
                      </label>
                      <input
                        type="text"
                        name="tenant_code"
                        required
                        placeholder="acme"
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Tenant Name
                      </label>
                      <input
                        type="text"
                        name="tenant_name"
                        required
                        placeholder="ACME Corp"
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Industry
                      </label>
                      <select
                        name="industry"
                        required
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                      >
                        <option value="dental">Dental</option>
                        <option value="medical">Medical</option>
                        <option value="other">Other</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Products (comma-separated)
                      </label>
                      <input
                        type="text"
                        name="products"
                        required
                        placeholder="dentalerp, agentprovision"
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                      />
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <button
                      type="submit"
                      disabled={createTenantMutation.isPending}
                      className="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg transition-colors disabled:opacity-50"
                    >
                      {createTenantMutation.isPending ? 'Creating...' : 'Create Tenant'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowCreateTenant(false)}
                      className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Tenants List */}
            {tenantsLoading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-600 mx-auto"></div>
                <p className="mt-4 text-gray-500 dark:text-gray-400">Loading tenants...</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                {tenants?.map((tenant) => (
                  <div
                    key={tenant.id}
                    className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                            {tenant.tenant_name}
                          </h3>
                          <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs rounded">
                            {tenant.tenant_code}
                          </span>
                          <span className={`px-2 py-1 text-xs rounded ${
                            tenant.status === 'active'
                              ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                              : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                          }`}>
                            {tenant.status || 'active'}
                          </span>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                          <div>
                            <p className="text-xs text-gray-500 dark:text-gray-400">Industry</p>
                            <p className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                              {tenant.industry}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500 dark:text-gray-400">Products</p>
                            <p className="text-sm font-medium text-gray-900 dark:text-white">
                              {tenant.products?.length || 0}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500 dark:text-gray-400">Warehouses</p>
                            <p className="text-sm font-medium text-gray-900 dark:text-white">
                              {tenant.warehouses?.length || 0}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500 dark:text-gray-400">Integrations</p>
                            <p className="text-sm font-medium text-gray-900 dark:text-white">
                              {tenant.integrations?.length || 0}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Integrations Tab */}
        {activeTab === 'integrations' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Available Integrations
            </h2>

            {integrationsLoading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-600 mx-auto"></div>
                <p className="mt-4 text-gray-500 dark:text-gray-400">Loading integrations...</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {integrations?.map((integration) => (
                  <div
                    key={integration.id}
                    className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow"
                  >
                    <div className="flex items-start space-x-4">
                      <PuzzlePieceIcon className="w-10 h-10 text-sky-600 dark:text-sky-400 flex-shrink-0" />
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                          {integration.name}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                          {integration.description}
                        </p>
                        <div className="flex items-center space-x-2">
                          <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs rounded">
                            {integration.type}
                          </span>
                          {integration.is_available && (
                            <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs rounded">
                              Available
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Warehouses Tab */}
        {activeTab === 'warehouses' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Warehouse Configuration
            </h2>

            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8 text-center">
              <CircleStackIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Warehouse Management
              </h3>
              <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
                Configure Snowflake warehouse connections for each tenant. Select a tenant from the Tenants tab to manage their warehouse settings.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MCPServerManagementPage;
