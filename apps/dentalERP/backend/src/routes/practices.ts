import { Router } from 'express';
import { and, eq, inArray } from 'drizzle-orm';
import { DatabaseService } from '../services/database';
import { practices, locations, userPractices } from '../database/schema';
import { logger } from '../utils/logger';

const router = Router();

// List practices accessible to the authenticated user
router.get('/', async (req, res) => {
  try {
    const db = DatabaseService.getInstance().getDb();
    const userId = (req as any).user?.userId as string | undefined;

    if (!userId) return res.status(401).json({ error: 'Unauthorized' });

    // Admin/executive can see all practices
    const role = (req as any).user?.role as string | undefined;
    if (role && ['admin', 'executive'].includes(role)) {
      const rows = await db.select().from(practices).where(eq(practices.isActive, true as any));
      return res.json({ success: true, practices: rows });
    }

    // Otherwise, return practices linked to user
    const ups = await db.select().from(userPractices).where(eq(userPractices.userId, userId));
    const practiceIds = ups.map((u: { practiceId: string }) => u.practiceId);
    if (practiceIds.length === 0) return res.json({ success: true, practices: [] });
    const rows = await db.select().from(practices).where(and(inArray(practices.id, practiceIds), eq(practices.isActive, true as any)));
    return res.json({ success: true, practices: rows });
  } catch (error) {
    logger.error('Get practices failed:', error);
    return res.status(500).json({ error: 'Failed to fetch practices' });
  }
});

// Get single practice
router.get('/:id', async (req, res) => {
  try {
    const db = DatabaseService.getInstance().getDb();
    const [row] = await db.select().from(practices).where(eq(practices.id, req.params.id)).limit(1);
    if (!row) return res.status(404).json({ error: 'Practice not found' });
    return res.json({ success: true, practice: row });
  } catch (error) {
    logger.error('Get practice failed:', error);
    return res.status(500).json({ error: 'Failed to fetch practice' });
  }
});

// List locations for a practice
router.get('/:id/locations', async (req, res) => {
  try {
    const db = DatabaseService.getInstance().getDb();
    const rows = await db.select().from(locations).where(eq(locations.practiceId, req.params.id));
    return res.json({ success: true, locations: rows });
  } catch (error) {
    logger.error('Get locations failed:', error);
    return res.status(500).json({ error: 'Failed to fetch locations' });
  }
});

export default router;
