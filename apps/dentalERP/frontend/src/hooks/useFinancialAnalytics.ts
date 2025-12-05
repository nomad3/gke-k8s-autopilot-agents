import { useQuery } from '@tanstack/react-query';
import { financialAPI } from '../services/financialAPI';

export function useFinancialSummary(params?: {
  practice_name?: string;
  start_date?: string;
  end_date?: string;
}) {
  return useQuery({
    queryKey: ['financial-summary', params],
    queryFn: () => financialAPI.getSummary(params),
    staleTime: 5 * 60 * 1000,  // 5 minutes
    retry: 2
  });
}

export function usePracticeComparison() {
  return useQuery({
    queryKey: ['practice-comparison'],
    queryFn: () => financialAPI.getByPracticeComparison(),
    staleTime: 5 * 60 * 1000
  });
}
