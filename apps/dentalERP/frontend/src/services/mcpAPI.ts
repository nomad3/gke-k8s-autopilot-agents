/**
 * MCP Server API Service
 * Provides methods to interact with the MCP (Mapping & Control Plane) Server
 *
 * NOTE: All API calls now go through the backend API (/api/*) instead of directly
 * to the MCP server. This fixes CORS issues and maintains proper architecture.
 */

// Use backend API base URL - let the backend proxy to MCP
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// Helper to add authentication header from local storage
const getAuthHeaders = () => {
  const token = localStorage.getItem('accessToken');
  const tenantId = localStorage.getItem('selected_tenant_id') || 'default';

  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    'X-Tenant-ID': tenantId,
  };
};

// Health & Status (still direct to MCP for health checks - no auth required)
const MCP_BASE_URL = import.meta.env.VITE_MCP_API_URL || 'http://localhost:8085';

export const healthAPI = {
  getHealth: async () => {
    const response = await fetch(`${MCP_BASE_URL}/health`);
    return response.json();
  },

  getServerInfo: async () => {
    const response = await fetch(`${MCP_BASE_URL}/`);
    return response.json();
  },
};

// Tenant Management
export interface Tenant {
  id?: string;
  tenant_code: string;
  tenant_name: string;
  industry: string;
  products: string[];
  warehouses?: TenantWarehouse[];
  integrations?: TenantIntegration[];
  api_keys?: TenantAPIKey[];
  status?: string;
  created_at?: string;
  updated_at?: string;
}

export interface TenantWarehouse {
  id?: string;
  tenant_id: string;
  warehouse_type: string;
  account: string;
  username: string;
  password?: string;
  database_name: string;
  schema_name: string;
  warehouse_name: string;
  role_name: string;
  is_primary: boolean;
  is_active: boolean;
  config?: Record<string, any>;
}

export interface TenantIntegration {
  id?: string;
  tenant_id: string;
  integration_type: string;
  config: Record<string, any>;
  is_active: boolean;
  sync_status?: string;
  last_sync_at?: string;
}

export interface TenantAPIKey {
  id?: string;
  tenant_id: string;
  key_name: string;
  api_key: string;
  is_active: boolean;
  expires_at?: string;
  created_at?: string;
}

export const tenantAPI = {
  // Get all tenants (via backend proxy)
  getTenants: async (): Promise<Tenant[]> => {
    const response = await fetch(`${API_BASE_URL}/tenants`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error(`Failed to fetch tenants: ${response.statusText}`);
    return response.json();
  },

  // Get specific tenant (via backend proxy)
  getTenant: async (tenantId: string): Promise<Tenant> => {
    const response = await fetch(`${API_BASE_URL}/tenants/${tenantId}`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error(`Failed to fetch tenant: ${response.statusText}`);
    return response.json();
  },

  // Create new tenant (via backend proxy)
  createTenant: async (tenant: Tenant): Promise<Tenant> => {
    const response = await fetch(`${API_BASE_URL}/tenants`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(tenant),
    });
    if (!response.ok) throw new Error(`Failed to create tenant: ${response.statusText}`);
    return response.json();
  },

  // Update tenant (via backend proxy)
  updateTenant: async (tenantId: string, tenant: Partial<Tenant>): Promise<Tenant> => {
    const response = await fetch(`${API_BASE_URL}/tenants/${tenantId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(tenant),
    });
    if (!response.ok) throw new Error(`Failed to update tenant: ${response.statusText}`);
    return response.json();
  },

  // Delete tenant (via backend proxy)
  deleteTenant: async (tenantId: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/tenants/${tenantId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error(`Failed to delete tenant: ${response.statusText}`);
  },

  // Get tenant warehouses (via backend proxy)
  getTenantWarehouses: async (tenantId: string): Promise<TenantWarehouse[]> => {
    const response = await fetch(`${API_BASE_URL}/tenants/${tenantId}/warehouses`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error(`Failed to fetch tenant warehouses: ${response.statusText}`);
    return response.json();
  },

  // Add tenant warehouse (via backend proxy)
  addTenantWarehouse: async (tenantId: string, warehouse: TenantWarehouse): Promise<TenantWarehouse> => {
    const response = await fetch(`${API_BASE_URL}/tenants/${tenantId}/warehouses`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(warehouse),
    });
    if (!response.ok) throw new Error(`Failed to add tenant warehouse: ${response.statusText}`);
    return response.json();
  },

  // Get tenant integrations (via backend proxy)
  getTenantIntegrations: async (tenantId: string): Promise<TenantIntegration[]> => {
    const response = await fetch(`${API_BASE_URL}/tenants/${tenantId}/integrations`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error(`Failed to fetch tenant integrations: ${response.statusText}`);
    return response.json();
  },

  // Add tenant integration (via backend proxy)
  addTenantIntegration: async (tenantId: string, integration: TenantIntegration): Promise<TenantIntegration> => {
    const response = await fetch(`${API_BASE_URL}/tenants/${tenantId}/integrations`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(integration),
    });
    if (!response.ok) throw new Error(`Failed to add tenant integration: ${response.statusText}`);
    return response.json();
  },

  // Update tenant integration (via backend proxy)
  updateTenantIntegration: async (tenantId: string, integrationId: string, integration: Partial<TenantIntegration>): Promise<TenantIntegration> => {
    const response = await fetch(`${API_BASE_URL}/tenants/${tenantId}/integrations/${integrationId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(integration),
    });
    if (!response.ok) throw new Error(`Failed to update tenant integration: ${response.statusText}`);
    return response.json();
  },
};

// Integration Management
export interface Integration {
  id: string;
  name: string;
  type: string;
  description: string;
  config_schema?: Record<string, any>;
  is_available: boolean;
}

export const integrationAPI = {
  // Get all available integrations (via backend proxy)
  getIntegrations: async (): Promise<Integration[]> => {
    const response = await fetch(`${API_BASE_URL}/tenants/catalog/integrations`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error(`Failed to fetch integrations: ${response.statusText}`);
    return response.json();
  },

  // Get integration details (via backend proxy)
  getIntegration: async (integrationId: string): Promise<Integration> => {
    const response = await fetch(`${API_BASE_URL}/tenants/catalog/integrations/${integrationId}`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error(`Failed to fetch integration: ${response.statusText}`);
    return response.json();
  },

  // Test integration connection (via backend proxy)
  testIntegration: async (tenantId: string, integrationType: string, config: Record<string, any>): Promise<{ success: boolean; message: string }> => {
    const response = await fetch(`${API_BASE_URL}/tenants/test-integration`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ tenantId, integrationType, config }),
    });
    if (!response.ok) throw new Error(`Failed to test integration: ${response.statusText}`);
    return response.json();
  },
};

// Warehouse Management
export interface WarehouseConnection {
  account: string;
  username: string;
  password: string;
  database: string;
  schema: string;
  warehouse: string;
  role: string;
}

export const warehouseAPI = {
  // Test warehouse connection (via backend proxy)
  testConnection: async (connection: WarehouseConnection): Promise<{ success: boolean; message: string }> => {
    const response = await fetch(`${API_BASE_URL}/tenants/test-warehouse`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(connection),
    });
    if (!response.ok) throw new Error(`Failed to test warehouse connection: ${response.statusText}`);
    return response.json();
  },

  // Get warehouse stats (via backend proxy)
  getWarehouseStats: async (tenantId: string): Promise<Record<string, any>> => {
    const response = await fetch(`${API_BASE_URL}/tenants/${tenantId}/warehouse/stats`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error(`Failed to fetch warehouse stats: ${response.statusText}`);
    return response.json();
  },
};

// Products Management
export interface Product {
  id: string;
  code: string;
  name: string;
  description: string;
  version: string;
  status: string;
  capabilities: string[];
}

export const productAPI = {
  // Get all products (via backend proxy)
  getProducts: async (): Promise<Product[]> => {
    const response = await fetch(`${API_BASE_URL}/tenants/catalog/products`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error(`Failed to fetch products: ${response.statusText}`);
    return response.json();
  },

  // Get product details (via backend proxy)
  getProduct: async (productCode: string): Promise<Product> => {
    const response = await fetch(`${API_BASE_URL}/tenants/catalog/products/${productCode}`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error(`Failed to fetch product: ${response.statusText}`);
    return response.json();
  },
};

export default {
  health: healthAPI,
  tenant: tenantAPI,
  integration: integrationAPI,
  warehouse: warehouseAPI,
  product: productAPI,
};
