import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { analyticsAPI } from '../services/api';
import { useAuthStore } from '../store/authStore';

// Executive BI Hooks
export const useExecutiveKPIs = (dateRange: string = '30d'): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);
  const practiceIds = user?.practiceIds || [];

  return useQuery({
    queryKey: ['executive-kpis', practiceIds, dateRange],
    queryFn: () => analyticsAPI.getExecutiveKPIs(practiceIds, dateRange),
    enabled: !!user && practiceIds.length > 0,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 10 * 60 * 1000, // 10 minutes for real-time BI
  });
};

export const useRevenueAnalytics = (dateRange: string = '6m'): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);
  const practiceIds = user?.practiceIds || [];

  return useQuery({
    queryKey: ['revenue-analytics', practiceIds, dateRange],
    queryFn: () => analyticsAPI.getRevenueAnalytics(practiceIds, dateRange),
    enabled: !!user && practiceIds.length > 0,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 15 * 60 * 1000, // 15 minutes for revenue data
  });
};

export const useLocationPerformance = (dateRange: string = '30d'): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);
  const practiceIds = user?.practiceIds || [];

  return useQuery({
    queryKey: ['location-performance', practiceIds, dateRange],
    queryFn: () => analyticsAPI.getLocationPerformance(practiceIds, dateRange),
    enabled: !!user && practiceIds.length > 0,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 10 * 60 * 1000,
  });
};

// Manager BI Hooks
export const useManagerMetrics = (date: string = new Date().toISOString().slice(0, 10)): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);
  const currentPractice = useAuthStore(state => state.currentPractice);
  return useQuery({
    queryKey: ['manager-metrics', currentPractice?.id ?? '', date],
    queryFn: async ({ queryKey }) => {
      const [, practiceId] = queryKey as [string, string, string];
      if (!practiceId) throw new Error('No practice selected');
      return analyticsAPI.getManagerMetrics(practiceId, date);
    },
    enabled: !!user && !!currentPractice?.id,
    staleTime: 2 * 60 * 1000, // 2 minutes for operational data
    refetchInterval: 5 * 60 * 1000, // 5 minutes for manager dashboard
  });
};

export const useOperationalInsights = (dateRange: string = '7d'): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);
  const currentPractice = useAuthStore(state => state.currentPractice);

  return useQuery({
    queryKey: ['operational-insights', currentPractice?.id ?? '', dateRange],
    queryFn: async ({ queryKey }) => {
      const [, practiceId] = queryKey as [string, string, string];
      if (!practiceId) throw new Error('No practice selected');
      return analyticsAPI.getOperationalInsights(practiceId, dateRange);
    },
    enabled: !!user && !!currentPractice?.id,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 10 * 60 * 1000,
  });
};

// Clinician BI Hooks
export const useClinicalMetrics = (dateRange: string = '30d'): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);

  return useQuery({
    queryKey: ['clinical-metrics', user?.id, dateRange],
    queryFn: () => analyticsAPI.getClinicalMetrics(user!.id, dateRange),
    enabled: !!user && user.role === 'clinician',
    staleTime: 10 * 60 * 1000, // 10 minutes for clinical data
    refetchInterval: 30 * 60 * 1000, // 30 minutes for clinical analytics
  });
};

export const useTreatmentOutcomes = (dateRange: string = '90d'): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);

  return useQuery({
    queryKey: ['treatment-outcomes', user?.id, dateRange],
    queryFn: () => analyticsAPI.getTreatmentOutcomes(user!.id, dateRange),
    enabled: !!user && user.role === 'clinician',
    staleTime: 15 * 60 * 1000,
    refetchInterval: 60 * 60 * 1000, // 1 hour for treatment outcomes
  });
};

// Integration Status Hook
export const useIntegrationStatus = (): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);

  return useQuery({
    queryKey: ['integration-status'],
    queryFn: () => analyticsAPI.getIntegrationStatus(),
    enabled: !!user,
    staleTime: 1 * 60 * 1000, // 1 minute for integration health
    refetchInterval: 2 * 60 * 1000, // 2 minutes for real-time monitoring
  });
};

// Patient Acquisition Hook
export const usePatientAcquisition = (dateRange: string = '30d'): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);
  const practiceIds = user?.practiceIds || [];

  return useQuery({
    queryKey: ['patient-acquisition', practiceIds, dateRange],
    queryFn: () => analyticsAPI.getPatientAcquisition(practiceIds, dateRange),
    enabled: !!user && practiceIds.length > 0,
    staleTime: 10 * 60 * 1000,
    refetchInterval: 15 * 60 * 1000,
  });
};

// Staff Productivity Hook
export const useStaffProductivity = (dateRange: string = '30d'): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);
  const practiceIds = user?.practiceIds || [];

  return useQuery({
    queryKey: ['staff-productivity', practiceIds, dateRange],
    queryFn: () => analyticsAPI.getStaffProductivity(practiceIds, dateRange),
    enabled: !!user && practiceIds.length > 0,
    staleTime: 10 * 60 * 1000,
    refetchInterval: 20 * 60 * 1000, // 20 minutes for staff data
  });
};

// Production Analytics Hooks - Direct Snowflake Gold Layer
export const useProductionDaily = (params: {
  practice_location?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
} = {}): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);

  return useQuery({
    queryKey: ['production-daily', params],
    queryFn: () => analyticsAPI.getProductionDaily(params),
    enabled: !!user,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 10 * 60 * 1000, // 10 minutes for production data
  });
};

export const useProductionSummary = (params: {
  practice_location?: string;
  start_date?: string;
  end_date?: string;
} = {}): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);

  return useQuery({
    queryKey: ['production-summary', params],
    queryFn: () => analyticsAPI.getProductionSummary(params),
    enabled: !!user,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 10 * 60 * 1000,
  });
};

export const useProductionByPractice = (params: {
  start_date?: string;
  end_date?: string;
} = {}): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);

  return useQuery({
    queryKey: ['production-by-practice', params],
    queryFn: () => analyticsAPI.getProductionByPractice(params),
    enabled: !!user,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 10 * 60 * 1000,
  });
};

// Utility hooks for common patterns
export const useRefreshAnalytics = () => {
  const user = useAuthStore(state => state.user);

  return {
    refreshAll: () => {
      // This would trigger a refetch of all analytics queries
      // Implementation would use React Query's invalidateQueries
      console.log('Refreshing all analytics data for user:', user?.id);
    },
    refreshIntegrations: () => {
      // Refresh integration status
      console.log('Refreshing integration status');
    }
  };
};
