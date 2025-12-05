import api from './api';

export interface FinancialSummary {
  practice_name: string;
  subsidiary_id: string;
  month_date: string;
  total_revenue: number;
  total_expenses: number;
  net_income: number;
  profit_margin_pct: number;
  mom_growth_pct: number;
  prev_month_revenue: number;
}

export interface FinancialSummaryResponse {
  data: FinancialSummary[];
  count: number;
  filters: {
    practice_name?: string;
    start_date?: string;
    end_date?: string;
  };
}

export interface PracticeComparisonResponse {
  practices: FinancialSummary[];
  count: number;
  period: string;
}

export const financialAPI = {
  getSummary: async (params?: {
    practice_name?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<FinancialSummaryResponse> => {
    // Now uses backend proxy instead of direct MCP call
    const response = await api.get('/analytics/financial/summary', {
      params
    });
    return response.data;
  },

  getByPracticeComparison: async (): Promise<PracticeComparisonResponse> => {
    // Now uses backend proxy instead of direct MCP call
    const response = await api.get('/analytics/financial/by-practice');
    return response.data;
  }
};
