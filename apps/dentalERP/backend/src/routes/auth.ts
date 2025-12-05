import { eq, inArray } from 'drizzle-orm';
import { Router } from 'express';
import { practices, userPractices, type UserPractice } from '../database/schema';
import { AuthService } from '../services/auth';
import { DatabaseService } from '../services/database';
import { AppError } from '../utils/errors';
import { logger } from '../utils/logger';

const router = Router();

// POST /api/auth/login
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body as { email?: string; password?: string };
    logger.info(`DEBUG: Login attempt for: ${email}`);
    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }

    const authService = AuthService.getInstance();
    const db = DatabaseService.getInstance().getDb();

    const { user, accessToken, refreshToken } = await authService.login({ email, password });

    const userPracticeRows = (await db
      .select()
      .from(userPractices)
      .where(eq(userPractices.userId, user.id))) as UserPractice[];
    const practiceIds = userPracticeRows.map((up) => up.practiceId);

    const practicesData = practiceIds.length
      ? await db.select().from(practices).where(inArray(practices.id, practiceIds))
      : [];

    const responseUser = {
      id: user.id,
      email: user.email,
      name: [user.firstName, user.lastName].filter(Boolean).join(' ').trim() || user.email,
      role: user.role,
      permissions: [] as string[],
      preferences: user.preferences || {},
      practiceIds,
      currentPracticeId: practiceIds[0],
    };

    return res.json({ user: responseUser, practices: practicesData, accessToken, refreshToken });
  } catch (error) {
    if (error instanceof AppError) {
      return res.status(error.statusCode).json({ error: error.message });
    }

    logger.error('Login error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
});

// POST /api/auth/logout
router.post('/logout', async (req, res) => {
  try {
    logger.info('Logout request');
    return res.json({ message: 'Logged out successfully' });
  } catch (error) {
    logger.error('Logout error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
});

// POST /api/auth/refresh
router.post('/refresh', async (req, res) => {
  try {
    logger.info('Token refresh request');
    const { refreshToken } = req.body as { refreshToken?: string };

    if (!refreshToken) {
      return res.status(400).json({ error: 'Refresh token is required' });
    }

    const authService = AuthService.getInstance();
    const tokens = await authService.refreshToken(refreshToken);

    return res.json(tokens);
  } catch (error) {
    if (error instanceof AppError) {
      return res.status(error.statusCode).json({ error: error.message });
    }

    logger.error('Token refresh error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
});

export default router;
