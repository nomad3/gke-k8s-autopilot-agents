import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { fetchTenants, type Tenant } from '../services/tenantApi';

interface TenantContextType {
  selectedTenant: Tenant | null;
  tenants: Tenant[];
  isLoading: boolean;
  error: Error | null;
  selectTenant: (tenantId: string) => void;
  refreshTenants: () => Promise<void>;
  clearTenant: () => void;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

const STORAGE_KEY = 'selected_tenant_id';

export const TenantProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // Load tenants from API
  const loadTenants = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await fetchTenants();
      setTenants(data);

      // Auto-select tenant from localStorage or first tenant
      const storedTenantId = localStorage.getItem(STORAGE_KEY);
      if (storedTenantId) {
        const stored = data.find(t => t.id === storedTenantId || t.tenant_code === storedTenantId);
        if (stored) {
          setSelectedTenant(stored);
        } else if (data.length > 0) {
          // Stored tenant not found, select first available
          const firstTenant = data[0];
          if (firstTenant) {
            setSelectedTenant(firstTenant);
            localStorage.setItem(STORAGE_KEY, firstTenant.tenant_code);
          }
        }
      } else if (data.length > 0) {
        // No stored tenant, auto-select first one
        const firstTenant = data[0];
        if (firstTenant) {
          setSelectedTenant(firstTenant);
          localStorage.setItem(STORAGE_KEY, firstTenant.tenant_code);
        }
      }
    } catch (err: any) {
      // Don't show error if it's just an authentication issue (user not logged in)
      // This is expected when the app first loads or user is on login page
      const isAuthError = err?.response?.status === 401 || err?.message?.includes('token');
      if (!isAuthError) {
        console.error('Failed to load tenants:', err);
        setError(err instanceof Error ? err : new Error('Failed to load tenants'));
      } else {
        console.debug('Tenants not loaded: user not authenticated');
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Check authentication and load tenants when auth state changes
  useEffect(() => {
    const checkAuthAndLoadTenants = () => {
      // Check if user is authenticated before loading tenants
      // The auth store persists under 'dental-erp-auth' key
      const authData = localStorage.getItem('dental-erp-auth');
      let isAuthenticated = false;

      if (authData) {
        try {
          const parsed = JSON.parse(authData);
          isAuthenticated = !!(parsed.state?.accessToken);
        } catch (e) {
          // Invalid JSON, not authenticated
          isAuthenticated = false;
        }
      }

      if (isAuthenticated) {
        loadTenants();
      } else {
        // Not authenticated, stop loading and don't set error
        setIsLoading(false);
      }
    };

    // Initial load
    checkAuthAndLoadTenants();

    // Listen for storage changes (login/logout in other tabs or windows)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'dental-erp-auth') {
        checkAuthAndLoadTenants();
      }
    };

    window.addEventListener('storage', handleStorageChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty deps = run once on mount, not on every loadTenants change

  // Select a tenant
  const selectTenant = useCallback((tenantId: string) => {
    const tenant = tenants.find(t => t.id === tenantId || t.tenant_code === tenantId);
    if (tenant) {
      setSelectedTenant(tenant);
      localStorage.setItem(STORAGE_KEY, tenant.tenant_code);

      // Trigger a custom event for other components to react to tenant change
      window.dispatchEvent(new CustomEvent('tenant-changed', { detail: tenant }));
    }
  }, [tenants]);

  // Clear tenant selection
  const clearTenant = useCallback(() => {
    setSelectedTenant(null);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  // Refresh tenants
  const refreshTenants = useCallback(async () => {
    await loadTenants();
  }, [loadTenants]);

  const value: TenantContextType = {
    selectedTenant,
    tenants,
    isLoading,
    error,
    selectTenant,
    refreshTenants,
    clearTenant,
  };

  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>;
};

/**
 * Hook to access tenant context
 */
export const useTenant = (): TenantContextType => {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  return context;
};

/**
 * Hook to get current tenant ID for API calls
 */
export const useTenantId = (): string | null => {
  const { selectedTenant } = useTenant();
  return selectedTenant?.tenant_code || null;
};
