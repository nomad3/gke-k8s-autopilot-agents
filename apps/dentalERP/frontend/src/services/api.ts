import axios from 'axios';
import type { Practice } from '../store/authStore';
import { useAuthStore } from '../store/authStore';

// Prefer relative default so Vite dev proxy can handle backend routing in all envs
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// MCP Server URL for direct analytics queries (bypasses backend)
const MCP_BASE_URL = import.meta.env.VITE_MCP_API_URL || 'http://localhost:8085';

// Create axios instance with interceptors
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create MCP axios instance for direct analytics queries
const mcpApi = axios.create({
  baseURL: MCP_BASE_URL,
  timeout: 30000, // Longer timeout for warehouse queries
  headers: {
    'Content-Type': 'application/json',
    // MCP server requires its own API key for authentication
    'Authorization': `Bearer ${import.meta.env.VITE_MCP_API_KEY || 'replace-with-32+-char-random-secret'}`,
  },
});

// Request interceptor to add auth token and tenant ID
const addAuthHeaders = (config: any) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  } else {
    // Fallback to localStorage if state is not yet updated (race condition)
    try {
      const authData = localStorage.getItem('dental-erp-auth');
      if (authData) {
        const parsed = JSON.parse(authData);
        const storedToken = parsed.state?.accessToken;
        if (storedToken) {
          config.headers.Authorization = `Bearer ${storedToken}`;
        }
      }
    } catch (e) {
      // Ignore parsing errors
    }
  }

  // Add tenant ID header for multi-tenant support
  // Use "default" tenant if no tenant is explicitly selected
  const selectedTenantId = localStorage.getItem('selected_tenant_id') || 'default';
  config.headers['X-Tenant-ID'] = selectedTenantId;

  return config;
};

// Request interceptor for backend API (adds user JWT token)
api.interceptors.request.use(addAuthHeaders, (error) => Promise.reject(error));

// Request interceptor for MCP API (only adds tenant ID, Authorization already set)
mcpApi.interceptors.request.use((config) => {
  // Add tenant ID header for multi-tenant support
  const selectedTenantId = localStorage.getItem('selected_tenant_id') || 'default';
  config.headers['X-Tenant-ID'] = selectedTenantId;
  return config;
}, (error) => Promise.reject(error));

// Response interceptor with refresh-token retry
let isRefreshing = false as boolean;
let refreshQueue: Array<{ resolve: (token: string) => void; reject: (err: any) => void }> = [];

const processRefreshQueue = (error: any, token: string | null) => {
  refreshQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error);
    else if (token) resolve(token);
  });
  refreshQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error?.config || {};
    const status = error?.response?.status;
    const url: string = (originalRequest?.url || '') as string;

    // Only handle 401 once per request and skip auth endpoints
    const isAuthEndpoint = url.includes('/auth/login') || url.includes('/auth/refresh');
    if (status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true;

      const { refreshToken } = useAuthStore.getState();
      if (!refreshToken) {
        useAuthStore.getState().clearAuth();
        window.location.href = '/auth/login';
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // Queue this request until refresh finishes
        return new Promise((resolve, reject) => {
          refreshQueue.push({
            resolve: (token: string) => {
              originalRequest.headers = originalRequest.headers || {};
              originalRequest.headers['Authorization'] = `Bearer ${token}`;
              resolve(api(originalRequest));
            },
            reject,
          });
        });
      }

      isRefreshing = true;
      try {
        // Use a bare axios to avoid interceptors recursion
        const resp = await axios.post(
          `${API_BASE_URL}/auth/refresh`,
          { refreshToken },
          { headers: { 'Content-Type': 'application/json' } }
        );

        const data = resp?.data || {};
        const newAccess = data.accessToken;
        const newRefresh = data.refreshToken || refreshToken;

        if (!newAccess) {
          throw new Error('No access token in refresh response');
        }

        // Update store tokens and default header
        useAuthStore.getState().setTokens(newAccess, newRefresh);
        api.defaults.headers.common['Authorization'] = `Bearer ${newAccess}`;

        processRefreshQueue(null, newAccess);

        // Retry original request with new token
        originalRequest.headers = originalRequest.headers || {};
        originalRequest.headers['Authorization'] = `Bearer ${newAccess}`;
        return api(originalRequest);
      } catch (refreshErr) {
        processRefreshQueue(refreshErr, null);
        useAuthStore.getState().clearAuth();
        window.location.href = '/auth/login';
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// BI Analytics API services
export const analyticsAPI = {
  // Executive BI endpoints
  getExecutiveKPIs: async (practiceIds: string[], dateRange: string) => {
    const response = await api.get('/analytics/executive-kpis', {
      params: { practiceIds: practiceIds.join(','), dateRange }
    });
    const body = response.data || {};
    const raw = body.data || {};
    // Normalize backend shape to frontend KPI structure expected by widgets
    const growth = typeof raw.growthRate === 'number' ? raw.growthRate : null;
    const trend = growth == null ? 'neutral' : growth > 0 ? 'up' : growth < 0 ? 'down' : 'neutral';
    const normalized = {
      totalRevenue: {
        value: typeof raw.revenue === 'number' ? raw.revenue : null,
        change: growth,
        trend,
        source: 'Eaglesoft + DentalIntel',
      },
      patientVolume: {
        value: typeof raw.patients === 'number' ? raw.patients : null,
        change: null,
        trend: 'neutral',
        source: 'Dentrix + DentalIntel',
      },
      appointmentEfficiency: {
        value: typeof raw.efficiency === 'number' ? raw.efficiency : null,
        change: null,
        trend: 'neutral',
        source: 'Dentrix + Scheduling',
      },
      profitMargin: {
        value: typeof raw.profitMargin === 'number' ? raw.profitMargin : null,
        change: null,
        trend: 'neutral',
        source: 'Eaglesoft + ADP',
      },
    };
    return { ...body, data: normalized };
  },

  getRevenueAnalytics: async (practiceIds: string[], dateRange: string) => {
    const response = await api.get('/analytics/revenue-trends', {
      params: { practiceIds: practiceIds.join(','), dateRange }
    });
    return response.data;
  },

  getLocationPerformance: async (practiceIds: string[], dateRange: string) => {
    const response = await api.get('/analytics/location-performance', {
      params: { practiceIds: practiceIds.join(','), dateRange }
    });
    return response.data;
  },

  // Manager BI endpoints
  getManagerMetrics: async (practiceId: string, date: string) => {
    const response = await api.get('/analytics/manager-metrics', {
      params: { practiceId, date }
    });
    return response.data;
  },

  getOperationalInsights: async (practiceId: string, dateRange: string) => {
    const response = await api.get('/analytics/operational-insights', {
      params: { practiceId, dateRange }
    });
    return response.data;
  },

  // Clinician BI endpoints
  getClinicalMetrics: async (providerId: string, dateRange: string) => {
    const response = await api.get('/analytics/clinical-metrics', {
      params: { providerId, dateRange }
    });
    return response.data;
  },

  getTreatmentOutcomes: async (providerId: string, dateRange: string) => {
    const response = await api.get('/analytics/treatment-outcomes', {
      params: { providerId, dateRange }
    });
    return response.data;
  },

  // Integration health monitoring
  getIntegrationStatus: async () => {
    const response = await api.get('/integrations/status');
    return response.data;
  },

  // Patient acquisition analytics
  getPatientAcquisition: async (practiceIds: string[], dateRange: string) => {
    const response = await api.get('/analytics/patient-acquisition', {
      params: { practiceIds: practiceIds.join(','), dateRange }
    });
    return response.data;
  },

  // Staff productivity analytics
  getStaffProductivity: async (practiceIds: string[], dateRange: string) => {
    const response = await api.get('/analytics/staff-productivity', {
      params: { practiceIds: practiceIds.join(','), dateRange }
    });
    return response.data;
  },

  // Financial overview (AR, collections, claims)
  getFinancialOverview: async (practiceIds: string[], dateRange: string) => {
    const response = await api.get('/analytics/financial-overview', {
      params: { practiceIds: practiceIds.join(','), dateRange }
    });
    return response.data;
  },

  // Scheduling overview (utilization, no-shows, cancellations)
  getSchedulingOverview: async (practiceIds: string[], dateRange: string) => {
    const response = await api.get('/analytics/scheduling-overview', {
      params: { practiceIds: practiceIds.join(','), dateRange }
    });
    return response.data;
  },

  // Retention cohorts
  getRetentionCohorts: async (practiceIds: string[], months = 6) => {
    const response = await api.get('/analytics/retention-cohorts', {
      params: { practiceIds: practiceIds.join(','), months }
    });
    return response.data;
  },

  // Benchmarking
  getBenchmarking: async (practiceIds: string[], dateRange: string) => {
    const response = await api.get('/analytics/benchmarking', {
      params: { practiceIds: practiceIds.join(','), dateRange }
    });
    return response.data;
  },

  // Forecasting
  getForecasting: async (practiceIds: string[]) => {
    const response = await api.get('/analytics/forecasting', {
      params: { practiceIds: practiceIds.join(',') }
    });
    return response.data;
  },

  // Production Analytics - Via Backend API (proxies to MCP Server/Snowflake)
  // Backend handles authentication with MCP server for security
  getProductionDaily: async (params: {
    practice_location?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }) => {
    const response = await api.get('/analytics/production/daily', { params });
    return response.data;
  },

  getProductionSummary: async (params: {
    practice_location?: string;
    start_date?: string;
    end_date?: string;
  }) => {
    const response = await api.get('/analytics/production/summary', { params });
    return response.data;
  },

  getProductionByPractice: async (params: {
    start_date?: string;
    end_date?: string;
  }) => {
    const response = await api.get('/analytics/production/by-practice', { params });
    return response.data;
  },
};

// Authentication API
export const authAPI = {
  login: async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },

  logout: async () => {
    const response = await api.post('/auth/logout');
    return response.data;
  },

  refreshToken: async (refreshToken: string) => {
    const response = await api.post('/auth/refresh', { refreshToken });
    return response.data;
  },

  getProfile: async () => {
    const response = await api.get('/auth/profile');
    return response.data;
  },
};

// Practice management API
export const practiceAPI = {
  getPractices: async (): Promise<{ practices: Practice[] }> => {
    const response = await api.get('/practices');
    return response.data;
  },

  getPracticeById: async (id: string) => {
    const response = await api.get(`/practices/${id}`);
    return response.data;
  },

  getLocations: async (practiceId: string) => {
    const response = await api.get(`/practices/${practiceId}/locations`);
    return response.data;
  },
};

export default api;

export const integrationCredentialsAPI = {
  listSummaries: async (params?: { practiceId?: string }) => {
    const response = await api.get('/integrations/credentials', { params });
    return response.data;
  },

  getCredential: async (practiceId: string, integrationType: string) => {
    const response = await api.get(`/integrations/credentials/${practiceId}/${integrationType}`);
    return response.data;
  },

  upsertCredential: async (
    practiceId: string,
    integrationType: string,
    payload: { name: string; credentials: Record<string, string>; metadata?: Record<string, unknown> },
  ) => {
    const response = await api.put(`/integrations/credentials/${practiceId}/${integrationType}`, payload);
    return response.data;
  },

  deleteCredential: async (practiceId: string, integrationType: string) => {
    const response = await api.delete(`/integrations/credentials/${practiceId}/${integrationType}`);
    return response.data;
  },

  testConnection: async (practiceId: string, integrationType: string) => {
    const response = await api.post(`/integrations/test-connection/${practiceId}/${integrationType}`);
    return response.data;
  },
};

// Manual ingestion API
export const ingestionAPI = {
  getSupported: async () => {
    const response = await api.get('/integrations/ingestion/supported');
    return response.data;
  },

  upload: async (params: { practiceId: string; sourceSystem: string; dataset?: string; notes?: string; file: File; }) => {
    const form = new FormData();
    form.append('practiceId', params.practiceId);
    form.append('sourceSystem', params.sourceSystem);
    if (params.dataset) form.append('dataset', params.dataset);
    if (params.notes) form.append('notes', params.notes);
    form.append('file', params.file);
    const response = await api.post('/integrations/ingestion/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  listUploads: async (params?: { practiceId?: string; limit?: number; statuses?: string[] }) => {
    const response = await api.get('/integrations/ingestion/uploads', { params });
    return response.data;
  },

  getUpload: async (id: string) => {
    const response = await api.get(`/integrations/ingestion/uploads/${id}`);
    return response.data;
  },

  handoffUpload: async (id: string, payload: { status?: string; externalLocation?: string; notes?: string }) => {
    const response = await api.post(`/integrations/ingestion/uploads/${id}/handoff`, payload);
    return response.data;
  },

  deleteUpload: async (id: string) => {
    const response = await api.delete(`/integrations/ingestion/uploads/${id}`);
    return response.data;
  },
};
