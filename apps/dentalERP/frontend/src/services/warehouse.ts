import api from './api';

/**
 * Snowflake Data Warehouse API
 * Connects frontend to MCP Server warehouse endpoints for real-time production KPIs
 */

// Type definitions
export interface WarehouseStatus {
  connected: boolean;
  warehouse: {
    WAREHOUSE: string;
    DATABASE: string;
    SCHEMA: string;
    VERSION: string;
  };
  layers: {
    bronze: {
      table_count: number;
    };
    silver: {
      table_count: number;
    };
    gold: {
      table_count: number;
    };
  };
  timestamp: string;
}

export interface BronzeLayerStatus {
  table_name: string;
  row_count: number;
  latest_extraction: string | null;
  oldest_extraction: string | null;
  freshness_hours: number | null;
  is_stale: boolean;
}

export interface DataFreshness {
  table_name: string;
  row_count: number;
  latest_extraction: string | null;
  freshness_hours: number | null;
  status: 'fresh' | 'stale' | 'very_stale' | 'no_data';
  threshold_hours: number;
}

export interface DbtRunResult {
  status: 'success' | 'error';
  duration_seconds: number;
  models_run: number;
  models_succeeded: number;
  models_failed: number;
  timestamp: string;
  logs?: string[];
  error?: string;
}

export interface MonthlyProductionKPI {
  PRACTICE_NAME: string;
  MONTH_DATE: string;
  YEAR_MONTH: string;
  TOTAL_PRODUCTION: string;
  TOTAL_EXPENSES: string;
  NET_INCOME: string;
  PROFIT_MARGIN_PCT: string;
  MOM_PRODUCTION_GROWTH_PCT: string;
}

export interface ProductionMetrics {
  PRACTICE_NAME: string;
  MONTH_DATE: string;
  TOTAL_PRODUCTION: string;
  TOTAL_COLLECTIONS: string;
  NEW_PATIENTS: number;
  ACTIVE_PATIENTS: number;
  APPOINTMENTS_SCHEDULED: number;
  APPOINTMENTS_COMPLETED: number;
  CANCELLATION_RATE: string;
  NO_SHOW_RATE: string;
}

// Warehouse API service
export const warehouseAPI = {
  /**
   * Get warehouse connection status and layer information
   */
  getStatus: async (): Promise<WarehouseStatus> => {
    const response = await api.get('/v1/warehouse/status');
    return response.data;
  },

  /**
   * Get Bronze layer data freshness status
   */
  getBronzeStatus: async (): Promise<BronzeLayerStatus[]> => {
    const response = await api.get('/v1/warehouse/bronze/status');
    return response.data;
  },

  /**
   * Check data freshness across all layers
   * @param thresholdHours - Number of hours before data is considered stale (default: 24)
   */
  getDataFreshness: async (thresholdHours: number = 24): Promise<DataFreshness[]> => {
    const response = await api.get('/v1/warehouse/freshness', {
      params: { threshold_hours: thresholdHours }
    });
    return response.data;
  },

  /**
   * Trigger dbt transformations (Bronze → Silver → Gold)
   * @param models - Optional array of specific models to run
   */
  runDbtTransformation: async (models?: string[]): Promise<DbtRunResult> => {
    const response = await api.post('/v1/warehouse/dbt/run', {
      models: models || []
    });
    return response.data;
  },

  /**
   * Execute custom SQL query against Snowflake
   * @param sql - SQL query to execute
   */
  executeQuery: async <T = any>(sql: string): Promise<T[]> => {
    const response = await api.get('/v1/warehouse/query', {
      params: { sql }
    });
    return response.data;
  },

  /**
   * Get monthly production KPIs for all practices
   * @param monthDate - Month date in YYYY-MM-DD format (e.g., '2024-11-01')
   */
  getMonthlyProductionKPIs: async (monthDate: string): Promise<MonthlyProductionKPI[]> => {
    const sql = `
      SELECT
        practice_name,
        month_date,
        year_month,
        total_production,
        total_expenses,
        net_income,
        profit_margin_pct,
        mom_production_growth_pct
      FROM gold.monthly_production_kpis
      WHERE month_date = '${monthDate}'
      ORDER BY total_production DESC
    `;
    return warehouseAPI.executeQuery<MonthlyProductionKPI>(sql);
  },

  /**
   * Get production KPI trends over time
   * @param practiceNames - Array of practice names (e.g., ['downtown', 'eastside'])
   * @param startDate - Start date in YYYY-MM-DD format
   * @param endDate - End date in YYYY-MM-DD format
   */
  getProductionTrends: async (
    practiceNames: string[],
    startDate: string,
    endDate: string
  ): Promise<MonthlyProductionKPI[]> => {
    const practiceFilter = practiceNames.length > 0
      ? `AND practice_name IN ('${practiceNames.join("','")}')`
      : '';

    const sql = `
      SELECT
        practice_name,
        month_date,
        year_month,
        total_production,
        total_expenses,
        net_income,
        profit_margin_pct,
        mom_production_growth_pct
      FROM gold.monthly_production_kpis
      WHERE month_date BETWEEN '${startDate}' AND '${endDate}'
      ${practiceFilter}
      ORDER BY practice_name, month_date
    `;
    return warehouseAPI.executeQuery<MonthlyProductionKPI>(sql);
  },

  /**
   * Get production metrics (appointments, patients, rates)
   * @param monthDate - Month date in YYYY-MM-DD format
   */
  getProductionMetrics: async (monthDate: string): Promise<ProductionMetrics[]> => {
    const sql = `
      SELECT
        practice_name,
        month_date,
        total_production,
        total_collections,
        new_patients,
        active_patients,
        appointments_scheduled,
        appointments_completed,
        cancellation_rate,
        no_show_rate
      FROM gold.fact_production
      WHERE month_date = '${monthDate}'
      ORDER BY total_production DESC
    `;
    return warehouseAPI.executeQuery<ProductionMetrics>(sql);
  },

  /**
   * Get practice performance comparison
   * @param monthDate - Month date in YYYY-MM-DD format
   */
  getPracticeComparison: async (monthDate: string) => {
    const [kpis, metrics] = await Promise.all([
      warehouseAPI.getMonthlyProductionKPIs(monthDate),
      warehouseAPI.getProductionMetrics(monthDate)
    ]);

    return kpis.map(kpi => {
      const metric = metrics.find(m => m.PRACTICE_NAME === kpi.PRACTICE_NAME);
      return {
        practiceName: kpi.PRACTICE_NAME,
        monthDate: kpi.MONTH_DATE,
        // Financial metrics
        totalProduction: parseFloat(kpi.TOTAL_PRODUCTION),
        totalExpenses: parseFloat(kpi.TOTAL_EXPENSES),
        netIncome: parseFloat(kpi.NET_INCOME),
        profitMargin: parseFloat(kpi.PROFIT_MARGIN_PCT),
        momGrowth: parseFloat(kpi.MOM_PRODUCTION_GROWTH_PCT),
        // Operational metrics
        newPatients: metric?.NEW_PATIENTS || 0,
        activePatients: metric?.ACTIVE_PATIENTS || 0,
        appointmentsScheduled: metric?.APPOINTMENTS_SCHEDULED || 0,
        appointmentsCompleted: metric?.APPOINTMENTS_COMPLETED || 0,
        cancellationRate: parseFloat(metric?.CANCELLATION_RATE || '0'),
        noShowRate: parseFloat(metric?.NO_SHOW_RATE || '0'),
        // Collections
        totalCollections: parseFloat(metric?.TOTAL_COLLECTIONS || '0'),
        collectionRate: metric
          ? (parseFloat(metric.TOTAL_COLLECTIONS) / parseFloat(kpi.TOTAL_PRODUCTION)) * 100
          : 0
      };
    });
  },

  /**
   * Get aggregate summary across all practices
   * @param monthDate - Month date in YYYY-MM-DD format
   */
  getAggregateSummary: async (monthDate: string) => {
    const sql = `
      SELECT
        COUNT(DISTINCT practice_name) as practice_count,
        SUM(total_production) as total_production,
        SUM(total_expenses) as total_expenses,
        SUM(net_income) as total_net_income,
        AVG(profit_margin_pct) as avg_profit_margin,
        AVG(mom_production_growth_pct) as avg_growth
      FROM gold.monthly_production_kpis
      WHERE month_date = '${monthDate}'
    `;
    const results = await warehouseAPI.executeQuery(sql);
    return results[0] || null;
  },

  /**
   * Get top performing practices by metric
   * @param metric - Metric to sort by (production, margin, growth)
   * @param monthDate - Month date in YYYY-MM-DD format
   * @param limit - Number of results to return (default: 5)
   */
  getTopPractices: async (
    metric: 'production' | 'margin' | 'growth',
    monthDate: string,
    limit: number = 5
  ) => {
    const orderBy = {
      production: 'total_production',
      margin: 'profit_margin_pct',
      growth: 'mom_production_growth_pct'
    }[metric];

    const sql = `
      SELECT
        practice_name,
        total_production,
        net_income,
        profit_margin_pct,
        mom_production_growth_pct
      FROM gold.monthly_production_kpis
      WHERE month_date = '${monthDate}'
      ORDER BY ${orderBy} DESC
      LIMIT ${limit}
    `;
    return warehouseAPI.executeQuery(sql);
  }
};

export default warehouseAPI;
