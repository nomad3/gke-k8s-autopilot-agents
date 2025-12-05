import { useQuery, UseQueryResult } from '@tanstack/react-query';
import api from '../services/api';
import { useAuthStore } from '../store/authStore';

/**
 * Unified Analytics Hooks
 * Single source for all practice metrics (Operations + Financial + PMS)
 */

export const useUnifiedMonthly = (params: {
  practice_id?: string;
  start_month?: string;
  end_month?: string;
  category?: 'all' | 'operations' | 'financial' | 'production';
  limit?: number;
} = {}): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);

  return useQuery({
    queryKey: ['unified-monthly', params],
    queryFn: async () => {
      const response = await api.get('/analytics-unified/monthly', { params });
      return response.data;
    },
    enabled: !!user,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 30 * 60 * 1000,
  });
};

export const useUnifiedSummary = (params: {
  practice_id?: string;
  month?: string;
} = {}): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);

  return useQuery({
    queryKey: ['unified-summary', params],
    queryFn: async () => {
      const response = await api.get('/analytics-unified/summary', { params });
      return response.data;
    },
    enabled: !!user,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 30 * 60 * 1000,
  });
};

export const useUnifiedByPractice = (params: {
  start_month?: string;
  end_month?: string;
} = {}): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);

  return useQuery({
    queryKey: ['unified-by-practice', params],
    queryFn: async () => {
      const response = await api.get('/analytics-unified/by-practice', { params });
      return response.data;
    },
    enabled: !!user,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 30 * 60 * 1000,
  });
};
