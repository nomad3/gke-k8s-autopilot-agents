import { and, gte, inArray, lte } from 'drizzle-orm';
import * as schema from '../database/schema';
import { logger } from '../utils/logger';
import { DatabaseService } from './database';
import { getMCPClient } from './mcpClient';

type DateRange = '7d' | '30d' | '90d' | '6m' | '12m' | 'ytd' | string;

function parseDateRange(dateRange?: DateRange) {
  const now = new Date();
  let from = new Date();
  if (!dateRange) return { from: new Date(now.getTime() - 30 * 24 * 3600 * 1000), to: now }; // default 30d
  const lower = String(dateRange).toLowerCase();
  const map: Record<string, number> = {
    '7d': 7,
    '30d': 30,
    '90d': 90,
  };
  if (map[lower]) {
    from = new Date(now.getTime() - map[lower] * 24 * 3600 * 1000);
  } else if (lower === '6m') {
    from = new Date(now);
    from.setMonth(from.getMonth() - 6);
  } else if (lower === '12m') {
    from = new Date(now);
    from.setFullYear(from.getFullYear() - 1);
  } else if (lower === 'ytd') {
    from = new Date(now.getFullYear(), 0, 1);
  } else {
    // try ISO date range: 2024-01-01..2024-03-01
    const parts = lower.split('..');
    if (parts.length === 2) {
      const [fromStr, toStr] = parts as [string, string];
      const f = new Date(fromStr);
      const t = new Date(toStr);
      if (!isNaN(f.getTime()) && !isNaN(t.getTime())) return { from: f, to: t };
    }
    // fallback 30d
    from = new Date(now.getTime() - 30 * 24 * 3600 * 1000);
  }
  return { from, to: now };
}

export class AnalyticsService {
  private static instance: AnalyticsService;
  private mcpClient = getMCPClient();

  private constructor() {
  }

  static getInstance(): AnalyticsService {
    if (!this.instance) this.instance = new AnalyticsService();
    return this.instance;
  }

  async getExecutiveKPIs(practiceIds: string[] = [], dateRange?: DateRange) {
    const { from, to } = parseDateRange(dateRange);
    return {
      revenue: 2400000,
      growthRate: 12.5,
      targetProgress: 94,
      patients: 18245,
      efficiency: 95.1,
      timeframe: { from: from.toISOString(), to: to.toISOString() }
    };
  }

  async getRevenueTrends(practiceIds: string[] = [], dateRange?: DateRange) {
    const { from, to } = parseDateRange(dateRange);
    return {
      monthlyData: [
        { month: 'Jan', revenue: 180000, target: 200000, growth: 5.2 },
        { month: 'Feb', revenue: 195000, target: 205000, growth: 8.0 },
        { month: 'Mar', revenue: 210000, target: 210000, growth: 9.1 },
        { month: 'Apr', revenue: 205000, target: 215000, growth: 6.9 },
        { month: 'May', revenue: 215000, target: 218000, growth: 8.3 },
        { month: 'Jun', revenue: 225000, target: 220000, growth: 4.7 }
      ],
      summary: {
        ytdRevenue: 2400000,
        growthRate: 12.5,
        targetProgress: 94,
        bestMonth: 'Jun',
        projectedTotal: 3200000
      },
      timeframe: { from: from.toISOString(), to: to.toISOString() }
    };
  }

  async getLocationPerformance(practiceIds: string[] = [], dateRange?: DateRange) {
    const { from, to } = parseDateRange(dateRange);
    return {
      locations: [
        { id: 'loc-1', name: 'Downtown', revenue: 420000, revenueChange: 8.2, patients: 2847, patientChange: 5.1, efficiency: 96.2, status: 'excellent' },
        { id: 'loc-2', name: 'Westside', revenue: 385000, revenueChange: 3.4, patients: 2634, patientChange: 0.8, efficiency: 94.8, status: 'good' },
        { id: 'loc-3', name: 'Northgate', revenue: 362000, revenueChange: -2.1, patients: 2491, patientChange: -1.2, efficiency: 89.3, status: 'warning' }
      ],
      summary: { bestPerformer: 'Downtown', needsAttention: 'Northgate', totalRevenue: 1167000, avgEfficiency: 93.4 },
      timeframe: { from: from.toISOString(), to: to.toISOString() }
    };
  }

  async getManagerMetrics(practiceId: string, date?: string) {
    try {
      // Fetch production metrics and alerts from MCP
      const [productionMetrics, alerts, integrationStatuses] = await Promise.all([
        this.mcpClient.getProductionMetrics(practiceId, date, date).catch(() => null),
        this.mcpClient.getAlerts(practiceId).catch(() => []),
        this.mcpClient.getIntegrationStatus().catch(() => [])
      ]);

      // Transform integration statuses
      const integrationHealth: Record<string, any> = {};
      for (const integration of integrationStatuses) {
        integrationHealth[integration.integrationType] = {
          status: integration.status,
          lastSync: integration.lastSyncAt || new Date().toISOString()
        };
      }

      return {
        todaysPerformance: {
          appointments: {
            scheduled: productionMetrics?.appointmentsScheduled || 0,
            completed: productionMetrics?.appointmentsCompleted || 0,
            pending: (productionMetrics?.appointmentsScheduled || 0) - (productionMetrics?.appointmentsCompleted || 0),
            conflicts: 0
          },
          revenue: {
            current: productionMetrics?.totalCollections || 0,
            goal: productionMetrics?.totalProduction || 0,
            percentage: productionMetrics?.totalProduction ?
              Math.round((productionMetrics.totalCollections / productionMetrics.totalProduction) * 1000) / 10 : 0
          },
          staff: { present: 0, total: 0, utilization: 0, remote: 0 }
        },
        alerts: alerts.slice(0, 10).map(a => ({ type: a.severity, message: a.message })),
        integrationHealth
      };
    } catch (error) {
      logger.error('Failed to fetch manager metrics from MCP', { practiceId, error });
      // Fallback data
      return {
        todaysPerformance: {
          appointments: { scheduled: 0, completed: 0, pending: 0, conflicts: 0 },
          revenue: { current: 0, goal: 0, percentage: 0 },
          staff: { present: 0, total: 0, utilization: 0, remote: 0 }
        },
        alerts: [],
        integrationHealth: {}
      };
    }
  }

  async getClinicalMetrics(providerId: string, dateRange?: DateRange) {
    const { from, to } = parseDateRange(dateRange);
    return {
      treatmentMetrics: {
        successRate: 94.8,
        patientsThisMonth: 156,
        avgTreatmentTime: 28,
        patientSatisfaction: 4.9
      },
      treatmentOutcomes: {
        preventiveCare: { successRate: 92, volume: 45 },
        restorative: { successRate: 88, volume: 32 },
        surgical: { successRate: 95, volume: 18 }
      },
      efficiency: { chairUtilization: 85.2, ontimePerformance: 91.8, treatmentCompletion: 96.4 },
      timeframe: { from: from.toISOString(), to: to.toISOString() }
    };
  }

  async getIntegrationStatus() {
    try {
      // Fetch integration status from MCP Server
      const statuses = await this.mcpClient.getIntegrationStatus();

      // Transform MCP response to legacy format for backward compatibility
      const result: Record<string, any> = {};
      for (const integration of statuses) {
        result[integration.integrationType] = {
          status: integration.status,
          health: integration.status === 'connected' ? 'healthy' : integration.status === 'error' ? 'unhealthy' : 'warning',
          lastSync: integration.lastSyncAt,
          nextSync: integration.nextSyncAt,
          dataPoints: integration.metadata?.dataPoints || []
        };
      }

      return result;
    } catch (error) {
      logger.error('Failed to fetch integration status from MCP', { error });
      // Return fallback data if MCP is unavailable
      return {
        dentrix: { status: 'disconnected', health: 'unavailable', dataPoints: [] },
        dentalintel: { status: 'disconnected', health: 'unavailable', dataPoints: [] },
        adp: { status: 'disconnected', health: 'unavailable', dataPoints: [] },
        eaglesoft: { status: 'disconnected', health: 'unavailable', dataPoints: [] },
        netsuite: { status: 'disconnected', health: 'unavailable', dataPoints: [] }
      };
    }
  }

  // Financial overview (AR buckets, collections, claims)
  async getFinancialOverview(practiceIds: string[] = [], dateRange?: DateRange) {
    const { from, to } = parseDateRange(dateRange);
    const db = DatabaseService.getInstance().getDb();
    const whereClauses = [gte(schema.biDailyMetrics.date, from), lte(schema.biDailyMetrics.date, to)];
    if (practiceIds.length) {
      whereClauses.push(inArray(schema.biDailyMetrics.practiceId, practiceIds as any));
    }
    const rows = await db
      .select({
        collectionsAmount: schema.biDailyMetrics.collectionsAmount,
        arCurrent: schema.biDailyMetrics.arCurrent,
        ar30: schema.biDailyMetrics.ar30,
        ar60: schema.biDailyMetrics.ar60,
        ar90: schema.biDailyMetrics.ar90,
        claimsSubmitted: schema.biDailyMetrics.claimsSubmitted,
        claimsDenied: schema.biDailyMetrics.claimsDenied,
      })
      .from(schema.biDailyMetrics)
      .where(and(...whereClauses));

    const agg = rows.reduce((a: { collections: number; ar: { current: number; '30': number; '60': number; '90': number }; claims: { submitted: number; denied: number } }, r: any) => {
      a.collections += r.collectionsAmount || 0;
      a.ar.current = r.arCurrent || a.ar.current;
      a.ar['30'] = r.ar30 || a.ar['30'];
      a.ar['60'] = r.ar60 || a.ar['60'];
      a.ar['90'] = r.ar90 || a.ar['90'];
      a.claims.submitted += r.claimsSubmitted || 0;
      a.claims.denied += r.claimsDenied || 0;
      return a;
    }, { collections: 0, ar: { current: 0, '30': 0, '60': 0, '90': 0 }, claims: { submitted: 0, denied: 0 } } as any);
    const approvalRate = agg.claims.submitted ? Math.round(((agg.claims.submitted - agg.claims.denied) / agg.claims.submitted) * 1000)/10 : 0;
    return {
      arBuckets: agg.ar,
      collectionsTotal: agg.collections,
      claims: { ...agg.claims, approvalRate },
      timeframe: { from: from.toISOString(), to: to.toISOString() }
    };
  }

  // Scheduling/operations overview (utilization, no-shows, cancellations, wait time)
  async getSchedulingOverview(practiceIds: string[] = [], dateRange?: DateRange) {
    const { from, to } = parseDateRange(dateRange);
    const db = DatabaseService.getInstance().getDb();
    const whereClauses = [gte(schema.biDailyMetrics.date, from), lte(schema.biDailyMetrics.date, to)];
    if (practiceIds.length) {
      whereClauses.push(inArray(schema.biDailyMetrics.practiceId, practiceIds as any));
    }
    const rows = await db
      .select({
        scheduleUtilization: schema.biDailyMetrics.scheduleUtilization,
        noShows: schema.biDailyMetrics.noShows,
        cancellations: schema.biDailyMetrics.cancellations,
        avgWaitTime: schema.biDailyMetrics.avgWaitTime,
      })
      .from(schema.biDailyMetrics)
      .where(and(...whereClauses));
    const n = rows.length || 1;
    const totals = rows.reduce((a: { utilization: number; noShows: number; cancellations: number; wait: number }, r: any) => ({
      utilization: a.utilization + (r.scheduleUtilization || 0),
      noShows: a.noShows + (r.noShows || 0),
      cancellations: a.cancellations + (r.cancellations || 0),
      wait: a.wait + (r.avgWaitTime || 0),
    }), { utilization: 0, noShows: 0, cancellations: 0, wait: 0 });
    return {
      scheduleUtilization: Math.round((totals.utilization / n) * 10)/10,
      noShows: totals.noShows,
      cancellations: totals.cancellations,
      avgWaitTime: Math.round((totals.wait / n) * 10)/10,
      timeframe: { from: from.toISOString(), to: to.toISOString() }
    };
  }

  // Synthetic retention cohorts (6 cohorts, 6 months trail)
  async getRetentionCohorts(practiceIds: string[] = [], months = 6) {
    const now = new Date();
    const cohorts = [] as any[];
    for (let i = months; i >= 1; i--) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const label = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`;
      const arr = [100];
      for (let k = 1; k < months; k++) {
        const drop = 8 + Math.floor(Math.random()*7);
        const prev = arr[k-1] ?? 100;
        arr[k] = Math.max(20, Math.round(prev * (1 - drop/100)));
      }
      cohorts.push({ cohort: label, retained: arr });
    }
    return { cohorts };
  }

  // Benchmarking against peer locations
  async getBenchmarking(practiceIds: string[] = [], dateRange?: DateRange) {
    const { from, to } = parseDateRange(dateRange);
    const db = DatabaseService.getInstance().getDb();
    const whereClauses = [gte(schema.biDailyMetrics.date, from), lte(schema.biDailyMetrics.date, to)];
    if (practiceIds.length) {
      whereClauses.push(inArray(schema.biDailyMetrics.practiceId, practiceIds as any));
    }
    const rows = await db
      .select({
        locationId: schema.biDailyMetrics.locationId,
        revenue: schema.biDailyMetrics.revenue,
        scheduleUtilization: schema.biDailyMetrics.scheduleUtilization,
        staffUtilization: schema.biDailyMetrics.staffUtilization,
        benchmarkScore: schema.biDailyMetrics.benchmarkScore,
      })
      .from(schema.biDailyMetrics)
      .where(and(...whereClauses));

    const byLoc: Record<string, any> = {};
    for (const r of rows) {
      const key = String(r.locationId || 'all');
      byLoc[key] = byLoc[key] || { revenue: 0, util: 0, sutil: 0, bench: 0, n: 0 };
      byLoc[key].revenue += r.revenue || 0;
      byLoc[key].util += r.scheduleUtilization || 0;
      byLoc[key].sutil += r.staffUtilization || 0;
      byLoc[key].bench += r.benchmarkScore || 0;
      byLoc[key].n += 1;
    }
    const locations = Object.entries(byLoc).map(([locId, v]) => ({
      id: locId,
      revenue: v.revenue,
      scheduleUtilization: Math.round((v.util / v.n) * 10)/10,
      staffUtilization: Math.round((v.sutil / v.n) * 10)/10,
      benchmarkScore: Math.round((v.bench / v.n) * 10)/10,
    }));
    const peerAvg = locations.reduce((a, l) => ({
      revenue: a.revenue + l.revenue,
      scheduleUtilization: a.scheduleUtilization + l.scheduleUtilization,
      staffUtilization: a.staffUtilization + l.staffUtilization,
      benchmarkScore: a.benchmarkScore + l.benchmarkScore,
    }), { revenue: 0, scheduleUtilization: 0, staffUtilization: 0, benchmarkScore: 0 });
    const count = Math.max(1, locations.length);
    return {
      locations,
      peerAverages: {
        revenue: peerAvg.revenue,
        scheduleUtilization: Math.round((peerAvg.scheduleUtilization / count) * 10)/10,
        staffUtilization: Math.round((peerAvg.staffUtilization / count) * 10)/10,
        benchmarkScore: Math.round((peerAvg.benchmarkScore / count) * 10)/10,
      },
      timeframe: { from: from.toISOString(), to: to.toISOString() }
    };
  }

  // Simple forecasting based on last 30d vs previous 30d growth
  async getForecasting(practiceIds: string[] = []) {
    const db = DatabaseService.getInstance().getDb();
    const now = new Date();
    const from1 = new Date(now.getTime() - 30*24*3600*1000);
    const from2 = new Date(now.getTime() - 60*24*3600*1000);
    const baseWhere = (start: Date, end: Date) => {
      const clauses = [gte(schema.biDailyMetrics.date, start), lte(schema.biDailyMetrics.date, end)];
      if (practiceIds.length) {
        clauses.push(inArray(schema.biDailyMetrics.practiceId, practiceIds as any));
      }
      return and(...clauses);
    };

    const rows1 = await db.select({ revenue: schema.biDailyMetrics.revenue, newPatients: schema.biDailyMetrics.newPatients, returningPatients: schema.biDailyMetrics.returningPatients })
      .from(schema.biDailyMetrics)
      .where(baseWhere(from1, now));
    const rows2 = await db.select({ revenue: schema.biDailyMetrics.revenue, newPatients: schema.biDailyMetrics.newPatients, returningPatients: schema.biDailyMetrics.returningPatients })
      .from(schema.biDailyMetrics)
      .where(baseWhere(from2, from1));
    const sum = (arr: any[], k: string) => arr.reduce((a, r) => a + (r[k] || 0), 0);
    const rev1 = sum(rows1, 'revenue');
    const rev2 = sum(rows2, 'revenue');
    const pts1 = sum(rows1, 'newPatients') + sum(rows1, 'returningPatients');
    const pts2 = sum(rows2, 'newPatients') + sum(rows2, 'returningPatients');
    const revGrowth = rev2 ? (rev1 - rev2) / rev2 : 0.05;
    const ptsGrowth = pts2 ? (pts1 - pts2) / pts2 : 0.05;
    return {
      projectedRevenueNext30d: Math.round(rev1 * (1 + revGrowth)),
      projectedPatientsNext30d: Math.round(pts1 * (1 + ptsGrowth)),
      growthAssumptions: { revenueGrowth: Math.round(revGrowth*1000)/10, patientsGrowth: Math.round(ptsGrowth*1000)/10 },
      timeframe: { last30d: from1.toISOString() + '..' + now.toISOString() }
    };
  }

  // Production Analytics - Proxy to MCP Server (Snowflake Gold Layer)
  async getProductionDaily(params: {
    practice_location?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }): Promise<any> {
    const response = await this.mcpClient.get('/api/v1/analytics/production/daily', { params });
    return response.data;
  }

  async getProductionSummary(params: {
    practice_location?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<any> {
    const response = await this.mcpClient.get('/api/v1/analytics/production/summary', { params });
    return response.data;
  }

  async getProductionByPractice(params: {
    start_date?: string;
    end_date?: string;
  }): Promise<any> {
    const response = await this.mcpClient.get('/api/v1/analytics/production/by-practice', { params });
    return response.data;
  }
}

export function parsePracticeIds(input?: string | string[]): string[] {
  if (!input) return [];
  if (Array.isArray(input)) return input.flatMap(i => String(i).split(',')).map(s => s.trim()).filter(Boolean);
  return String(input).split(',').map(s => s.trim()).filter(Boolean);
}
