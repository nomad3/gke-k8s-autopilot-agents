import { Router } from 'express';
import { logger } from '../utils/logger';
import { getMCPClient } from '../services/mcpClient';

const router = Router();
const mcpClient = getMCPClient();

router.get('/monthly', async (req, res) => {
  try {
    const { practice_id, start_month, end_month, category, limit } = req.query;

    const response = await mcpClient.get('/api/v1/analytics/unified/monthly', {
      params: { practice_id, start_month, end_month, category, limit },
    });

    return res.json(response.data);
  } catch (error) {
    logger.error('Unified analytics monthly error:', error);
    return res.status(500).json({ error: 'Failed to fetch unified analytics' });
  }
});

router.get('/summary', async (req, res) => {
  try {
    const { practice_id, month } = req.query;

    const response = await mcpClient.get('/api/v1/analytics/unified/summary', {
      params: { practice_id, month },
    });

    return res.json(response.data);
  } catch (error) {
    logger.error('Unified analytics summary error:', error);
    return res.status(500).json({ error: 'Failed to fetch summary' });
  }
});

router.get('/by-practice', async (req, res) => {
  try {
    const { start_month, end_month } = req.query;

    const response = await mcpClient.get('/api/v1/analytics/unified/by-practice', {
      params: { start_month, end_month },
    });

    return res.json(response.data);
  } catch (error) {
    logger.error('Unified analytics by-practice error:', error);
    return res.status(500).json({ error: 'Failed to fetch by-practice' });
  }
});

export default router;
