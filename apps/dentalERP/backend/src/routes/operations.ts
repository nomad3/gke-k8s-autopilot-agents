import { Router } from 'express';
import { logger } from '../utils/logger';
import { getMCPClient } from '../services/mcpClient';

const router = Router();
const mcpClient = getMCPClient();

/**
 * Operations KPI Routes - Proxy to MCP Server
 * Simple pass-through to MCP Server operations endpoints
 */

router.get('/kpis/monthly', async (req, res) => {
  try {
    const { practice_location, start_month, end_month, limit } = req.query;

    logger.info('Operations monthly KPIs requested', { practice_location, start_month, end_month });

    const response = await mcpClient.get('/api/v1/operations/kpis/monthly', {
      params: { practice_location, start_month, end_month, limit },
    });

    return res.json(response.data);
  } catch (error) {
    logger.error('Operations monthly KPIs error:', error);
    return res.status(500).json({ error: 'Failed to fetch operations KPIs' });
  }
});

router.get('/kpis/summary', async (req, res) => {
  try {
    const { practice_location, month } = req.query;

    logger.info('Operations summary requested', { practice_location, month });

    const response = await mcpClient.get('/api/v1/operations/kpis/summary', {
      params: { practice_location, month },
    });

    return res.json(response.data);
  } catch (error) {
    logger.error('Operations summary error:', error);
    return res.status(500).json({ error: 'Failed to fetch operations summary' });
  }
});

router.get('/kpis/by-practice', async (req, res) => {
  try {
    const { start_month, end_month } = req.query;

    logger.info('Operations by-practice requested', { start_month, end_month });

    const response = await mcpClient.get('/api/v1/operations/kpis/by-practice', {
      params: { start_month, end_month },
    });

    return res.json(response.data);
  } catch (error) {
    logger.error('Operations by-practice error:', error);
    return res.status(500).json({ error: 'Failed to fetch operations by practice' });
  }
});

export default router;
