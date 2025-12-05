import api from './api';
import { Product } from './mcpAPI';

// Tenant type matching backend response
export interface Tenant {
  id: string;
  tenant_code: string;
  tenant_name: string;
  industry?: string;
  products: string[];
  status: string;
  settings?: Record<string, any>;
}

export type TenantProduct = Product;

/**
 * Fetch all tenants accessible to the current user
 * Routes through backend API which proxies to MCP
 */
export const fetchTenants = async (): Promise<Tenant[]> => {
  const response = await api.get('/tenants');
  return response.data;
};

/**
 * Fetch a specific tenant by ID
 * Routes through backend API which proxies to MCP
 */
export const fetchTenantById = async (tenantId: string): Promise<Tenant> => {
  const response = await api.get(`/tenants/${tenantId}`);
  return response.data;
};

/**
 * Fetch products available to a tenant
 * Routes through backend API which proxies to MCP
 */
export const fetchTenantProducts = async (): Promise<TenantProduct[]> => {
  const response = await api.get('/tenants/catalog/products');
  return response.data;
};

/**
 * Fetch all available products (catalog)
 * Routes through backend API which proxies to MCP
 */
export const fetchAllProducts = async (): Promise<TenantProduct[]> => {
  const response = await api.get('/tenants/catalog/products');
  return response.data;
};
