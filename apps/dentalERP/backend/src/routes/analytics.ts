import { Router } from 'express';
import { logger } from '../utils/logger';
import { AnalyticsService, parsePracticeIds } from '../services/analytics';

const router = Router();

// Executive BI Analytics Endpoints
router.get('/executive-kpis', async (req, res) => {
  try {
    const { practiceIds, dateRange } = req.query as { practiceIds?: string | string[]; dateRange?: string };

    logger.info('Executive KPIs requested', { practiceIds, dateRange, userId: (req as any).user?.userId });

    const ids = parsePracticeIds(practiceIds);
    const service = AnalyticsService.getInstance();
    const data = await service.getExecutiveKPIs(ids, dateRange);

    return res.json({ success: true, data, timestamp: new Date().toISOString(), practiceIds: ids, dateRange });
  } catch (error) {
    logger.error('Executive KPIs error:', error);
    return res.status(500).json({ error: 'Failed to fetch executive KPIs' });
  }
});

router.get('/revenue-trends', async (req, res) => {
  try {
    const { practiceIds, dateRange } = req.query as { practiceIds?: string | string[]; dateRange?: string };
    logger.info('Revenue trends requested', { practiceIds, dateRange });
    const ids = parsePracticeIds(practiceIds);
    const service = AnalyticsService.getInstance();
    const data = await service.getRevenueTrends(ids, dateRange);
    return res.json({ success: true, data, timestamp: new Date().toISOString() });
  } catch (error) {
    logger.error('Revenue trends error:', error);
    return res.status(500).json({ error: 'Failed to fetch revenue trends' });
  }
});

router.get('/location-performance', async (req, res) => {
  try {
    const { practiceIds, dateRange } = req.query as { practiceIds?: string | string[]; dateRange?: string };
    logger.info('Location performance requested', { practiceIds, dateRange });
    const ids = parsePracticeIds(practiceIds);
    const service = AnalyticsService.getInstance();
    const data = await service.getLocationPerformance(ids, dateRange);
    return res.json({ success: true, data, timestamp: new Date().toISOString() });
  } catch (error) {
    logger.error('Location performance error:', error);
    return res.status(500).json({ error: 'Failed to fetch location performance' });
  }
});

// Manager BI Analytics Endpoints
router.get('/manager-metrics', async (req, res) => {
  try {
    const { practiceId, date } = req.query as { practiceId?: string; date?: string };
    logger.info('Manager metrics requested', { practiceId, date });
    if (!practiceId) {
      return res.status(400).json({ error: 'practiceId is required' });
    }
    const service = AnalyticsService.getInstance();
    const data = await service.getManagerMetrics(practiceId, date);
    return res.json({ success: true, data, timestamp: new Date().toISOString() });
  } catch (error) {
    logger.error('Manager metrics error:', error);
    return res.status(500).json({ error: 'Failed to fetch manager metrics' });
  }
});

// Clinician BI Analytics
router.get('/clinical-metrics', async (req, res) => {
  try {
    const { providerId, dateRange } = req.query as { providerId?: string; dateRange?: string };
    if (!providerId) {
      return res.status(400).json({ error: 'providerId is required' });
    }
    const service = AnalyticsService.getInstance();
    const data = await service.getClinicalMetrics(providerId, dateRange);
    return res.json({ success: true, data, timestamp: new Date().toISOString() });
  } catch (error) {
    logger.error('Clinical metrics error:', error);
    return res.status(500).json({ error: 'Failed to fetch clinical metrics' });
  }
});

// Integration Status for BI monitoring
router.get('/integration-status', async (req, res) => {
  try {
    const service = AnalyticsService.getInstance();
    const data = await service.getIntegrationStatus();
    return res.json({ success: true, data, timestamp: new Date().toISOString() });
  } catch (error) {
    logger.error('Integration status error:', error);
    return res.status(500).json({ error: 'Failed to fetch integration status' });
  }
});

// Additional BI endpoints used by frontend hooks (stubs for MVP)
router.get('/operational-insights', async (req, res) => {
  try {
    const { practiceId, dateRange } = req.query as { practiceId?: string; dateRange?: string };
    logger.info('Operational insights requested', { practiceId, dateRange });
    return res.json({
      success: true,
      data: {
        scheduleUtilization: 87.4,
        avgWaitTime: 11,
        cancellations: 3,
        confirmationsPending: 5
      },
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('Operational insights error:', error);
    return res.status(500).json({ error: 'Failed to fetch operational insights' });
  }
});

// Financial overview (AR, collections, claims)
router.get('/financial-overview', async (req, res) => {
  try {
    const { practiceIds, dateRange } = req.query as { practiceIds?: string | string[]; dateRange?: string };
    const ids = parsePracticeIds(practiceIds);
    const service = AnalyticsService.getInstance();
    const data = await service.getFinancialOverview(ids, dateRange);
    return res.json({ success: true, data, timestamp: new Date().toISOString() });
  } catch (error) {
    logger.error('Financial overview error:', error);
    return res.status(500).json({ error: 'Failed to fetch financial overview' });
  }
});

// Scheduling overview (utilization, no-shows, cancellations, wait time)
router.get('/scheduling-overview', async (req, res) => {
  try {
    const { practiceIds, dateRange } = req.query as { practiceIds?: string | string[]; dateRange?: string };
    const ids = parsePracticeIds(practiceIds);
    const service = AnalyticsService.getInstance();
    const data = await service.getSchedulingOverview(ids, dateRange);
    return res.json({ success: true, data, timestamp: new Date().toISOString() });
  } catch (error) {
    logger.error('Scheduling overview error:', error);
    return res.status(500).json({ error: 'Failed to fetch scheduling overview' });
  }
});

// Retention cohorts
router.get('/retention-cohorts', async (req, res) => {
  try {
    const { practiceIds, months } = req.query as { practiceIds?: string | string[]; months?: string };
    const ids = parsePracticeIds(practiceIds);
    const service = AnalyticsService.getInstance();
    const data = await service.getRetentionCohorts(ids, months ? parseInt(months, 10) : 6);
    return res.json({ success: true, data, timestamp: new Date().toISOString() });
  } catch (error) {
    logger.error('Retention cohorts error:', error);
    return res.status(500).json({ error: 'Failed to fetch retention cohorts' });
  }
});

// Benchmarking
router.get('/benchmarking', async (req, res) => {
  try {
    const { practiceIds, dateRange } = req.query as { practiceIds?: string | string[]; dateRange?: string };
    const ids = parsePracticeIds(practiceIds);
    const service = AnalyticsService.getInstance();
    const data = await service.getBenchmarking(ids, dateRange);
    return res.json({ success: true, data, timestamp: new Date().toISOString() });
  } catch (error) {
    logger.error('Benchmarking error:', error);
    return res.status(500).json({ error: 'Failed to fetch benchmarking' });
  }
});

// Forecasting
router.get('/forecasting', async (req, res) => {
  try {
    const { practiceIds } = req.query as { practiceIds?: string | string[] };
    const ids = parsePracticeIds(practiceIds);
    const service = AnalyticsService.getInstance();
    const data = await service.getForecasting(ids);
    return res.json({ success: true, data, timestamp: new Date().toISOString() });
  } catch (error) {
    logger.error('Forecasting error:', error);
    return res.status(500).json({ error: 'Failed to fetch forecasting' });
  }
});

router.get('/treatment-outcomes', async (req, res) => {
  try {
    const { providerId, dateRange } = req.query as { providerId?: string; dateRange?: string };
    logger.info('Treatment outcomes requested', { providerId, dateRange });
    return res.json({
      success: true,
      data: {
        preventiveCare: { successRate: 92, volume: 45 },
        restorative: { successRate: 88, volume: 32 },
        surgical: { successRate: 95, volume: 18 }
      },
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('Treatment outcomes error:', error);
    return res.status(500).json({ error: 'Failed to fetch treatment outcomes' });
  }
});

router.get('/patient-acquisition', async (req, res) => {
  try {
    const { practiceIds, dateRange } = req.query as { practiceIds?: string | string[]; dateRange?: string };
    logger.info('Patient acquisition requested', { practiceIds, dateRange });
    return res.json({
      success: true,
      data: {
        referrals: 42,
        marketing: 58,
        walkIns: 16,
        total: 116,
        trend: 'up'
      },
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('Patient acquisition error:', error);
    return res.status(500).json({ error: 'Failed to fetch patient acquisition' });
  }
});

router.get('/staff-productivity', async (req, res) => {
  try {
    const { practiceIds, dateRange } = req.query as { practiceIds?: string | string[]; dateRange?: string };
    logger.info('Staff productivity requested', { practiceIds, dateRange });
    return res.json({
      success: true,
      data: {
        utilization: 91.7,
        avgAppointmentsPerProvider: 14,
        overtimeHours: 6,
        remoteStaff: 2
      },
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('Staff productivity error:', error);
    return res.status(500).json({ error: 'Failed to fetch staff productivity' });
  }
});

// Production Analytics - Proxy to MCP Server (Snowflake Gold Layer)
// These endpoints proxy directly to MCP server with proper authentication
router.get('/production/daily', async (req, res) => {
  try {
    const { practice_location, start_date, end_date, limit } = req.query as {
      practice_location?: string;
      start_date?: string;
      end_date?: string;
      limit?: string;
    };
    logger.info('Production daily requested', { practice_location, start_date, end_date, limit });

    const service = AnalyticsService.getInstance();
    const data = await service.getProductionDaily({
      practice_location,
      start_date,
      end_date,
      limit: limit ? parseInt(limit, 10) : undefined
    });

    return res.json(data);
  } catch (error) {
    logger.error('Production daily error:', error);
    return res.status(500).json({ error: 'Failed to fetch production daily' });
  }
});

router.get('/production/summary', async (req, res) => {
  try {
    const { practice_location, start_date, end_date } = req.query as {
      practice_location?: string;
      start_date?: string;
      end_date?: string;
    };
    logger.info('Production summary requested', { practice_location, start_date, end_date });

    const service = AnalyticsService.getInstance();
    const data = await service.getProductionSummary({
      practice_location,
      start_date,
      end_date
    });

    return res.json(data);
  } catch (error) {
    logger.error('Production summary error:', error);
    return res.status(500).json({ error: 'Failed to fetch production summary' });
  }
});

router.get('/production/by-practice', async (req, res) => {
  try {
    const { start_date, end_date } = req.query as {
      start_date?: string;
      end_date?: string;
    };
    logger.info('Production by practice requested', { start_date, end_date });

    const service = AnalyticsService.getInstance();
    const data = await service.getProductionByPractice({
      start_date,
      end_date
    });

    return res.json(data);
  } catch (error) {
    logger.error('Production by practice error:', error);
    return res.status(500).json({ error: 'Failed to fetch production by practice' });
  }
});

// AI Insights - Proxy to MCP Server
router.get('/insights', async (req, res) => {
  try {
    logger.info('AI insights requested');
    const { getMCPClient } = await import('../services/mcpClient');
    const mcpClient = getMCPClient();
    const response = await mcpClient.get('/api/v1/analytics/insights', {
      params: req.query
    });
    return res.json(response.data);
  } catch (error) {
    logger.error('AI insights error:', error);
    return res.status(500).json({ error: 'Failed to fetch AI insights' });
  }
});

// Financial Summary - Proxy to MCP Server (Snowflake Gold Layer)
router.get('/financial/summary', async (req, res) => {
  try {
    const { practice_name, start_date, end_date } = req.query as {
      practice_name?: string;
      start_date?: string;
      end_date?: string;
    };
    logger.info('Financial summary requested', { practice_name, start_date, end_date });

    const { getMCPClient } = await import('../services/mcpClient');
    const mcpClient = getMCPClient();
    const response = await mcpClient.get('/api/v1/analytics/financial/summary', {
      params: { practice_name, start_date, end_date }
    });
    return res.json(response.data);
  } catch (error) {
    logger.error('Financial summary error:', error);
    return res.status(500).json({ error: 'Failed to fetch financial summary' });
  }
});

// Financial By Practice - Proxy to MCP Server
router.get('/financial/by-practice', async (req, res) => {
  try {
    logger.info('Financial by practice requested');
    const { getMCPClient } = await import('../services/mcpClient');
    const mcpClient = getMCPClient();
    const response = await mcpClient.get('/api/v1/analytics/financial/by-practice', {
      params: req.query
    });
    return res.json(response.data);
  } catch (error) {
    logger.error('Financial by practice error:', error);
    return res.status(500).json({ error: 'Failed to fetch financial by practice' });
  }
});

export default router;
