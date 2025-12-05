import { useQuery, UseQueryResult } from '@tanstack/react-query';
import api from '../services/api';
import { useAuthStore } from '../store/authStore';

/**
 * Operations KPI Hooks - Monthly Practice Operations Tracking
 * Data flow: Frontend → Backend API → MCP Server → Snowflake
 * REUSES: useAnalytics.ts pattern for consistency
 */

export const useOperationsMonthly = (params: {
  practice_location?: string;
  start_month?: string;
  end_month?: string;
  limit?: number;
} = {}): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);

  return useQuery({
    queryKey: ['operations-monthly', params],
    queryFn: async () => {
      const response = await api.get('/operations/kpis/monthly', { params });
      return response.data;
    },
    enabled: !!user,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 30 * 60 * 1000, // 30 minutes
  });
};

export const useOperationsSummary = (params: {
  practice_location?: string;
  month?: string;
} = {}): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);

  return useQuery({
    queryKey: ['operations-summary', params],
    queryFn: async () => {
      const response = await api.get('/operations/kpis/summary', { params });
      return response.data;
    },
    enabled: !!user,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 30 * 60 * 1000,
  });
};

export const useOperationsByPractice = (params: {
  start_month?: string;
  end_month?: string;
} = {}): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);

  return useQuery({
    queryKey: ['operations-by-practice', params],
    queryFn: async () => {
      const response = await api.get('/operations/kpis/by-practice', { params });
      return response.data;
    },
    enabled: !!user,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 30 * 60 * 1000,
  });
};
