import { Router } from 'express';
import { and, eq } from 'drizzle-orm';
import { DatabaseService } from '../services/database';
import { userDashboards } from '../database/schema';
import { logger } from '../utils/logger';

const router = Router();

// Default layout used if user hasn't saved one yet
const defaultLayout = {
  layout: [
    { id: 'kpi_total_revenue' },
    { id: 'kpi_patient_volume' },
    { id: 'kpi_appointment_efficiency' },
    { id: 'kpi_profit_margin' },
    { id: 'revenue_trends' },
    { id: 'location_performance' },
    { id: 'patient_acquisition' },
    { id: 'staff_productivity' },
  ],
  widgets: {
    kpi_total_revenue: { refreshRate: 30 },
    kpi_patient_volume: { refreshRate: 30 },
    kpi_appointment_efficiency: { refreshRate: 30 },
    kpi_profit_margin: { refreshRate: 30 },
    revenue_trends: { chart: 'line' },
    location_performance: { chart: 'bar' },
    patient_acquisition: { chart: 'bar' },
    staff_productivity: { chart: 'bar' },
  }
};

// Get the current user's dashboard layout for a practice
router.get('/layout', async (req, res) => {
  try {
    const userId = (req as any).user?.userId as string | undefined;
    const practiceId = (req.query.practiceId as string) || (req as any).user?.practiceIds?.[0];
    if (!userId || !practiceId) {
      return res.status(400).json({ error: 'practiceId and auth required' });
    }

    const db = DatabaseService.getInstance().getDb();
    const [row] = await db.select().from(userDashboards).where(and(eq(userDashboards.userId, userId), eq(userDashboards.practiceId, practiceId))).limit(1);
    if (!row) {
      return res.json({ success: true, ...defaultLayout, source: 'default' });
    }
    return res.json({ success: true, layout: row.layout, widgets: row.widgets, source: 'user' });
  } catch (error) {
    logger.error('Get dashboard layout failed:', error);
    return res.status(500).json({ error: 'Failed to fetch dashboard layout' });
  }
});

// Save or update user dashboard layout
router.post('/layout', async (req, res) => {
  try {
    const userId = (req as any).user?.userId as string | undefined;
    const { practiceId, layout, widgets } = req.body as any;
    if (!userId) {
      return res.status(401).json({ error: 'Unauthorized' });
    }
    if (!practiceId || !layout || !widgets) {
      return res.status(400).json({ error: 'practiceId, layout and widgets are required' });
    }

    const db = DatabaseService.getInstance().getDb();
    const existing = await db.select().from(userDashboards).where(and(eq(userDashboards.userId, userId), eq(userDashboards.practiceId, practiceId))).limit(1);

    if (existing[0]) {
      const [updated] = await db.update(userDashboards).set({ layout, widgets, updatedAt: new Date() }).where(and(eq(userDashboards.userId, userId), eq(userDashboards.practiceId, practiceId))).returning();
      return res.json({ success: true, layout: updated.layout, widgets: updated.widgets });
    }

    const [inserted] = await db.insert(userDashboards).values({ userId, practiceId, layout, widgets, isActive: true, createdAt: new Date(), updatedAt: new Date() }).returning();
    return res.json({ success: true, layout: inserted.layout, widgets: inserted.widgets });
  } catch (error) {
    logger.error('Save dashboard layout failed:', error);
    return res.status(500).json({ error: 'Failed to save dashboard layout' });
  }
});

export default router;
