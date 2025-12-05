import { NextFunction, Request, Response } from 'express';
import { AuthService } from '../services/auth';
import { AppError } from '../utils/errors';
import { logger } from '../utils/logger';

// Extend Express Request interface to include user data
declare global {
  namespace Express {
    interface Request {
      user?: {
        userId: string;
        email: string;
        role: string;
        practiceIds: string[];
      };
    }
  }
}

export const authMiddleware = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const authHeader = req.headers.authorization;

    if (!authHeader) {
      throw new AppError('Access token is required', 401);
    }

    const token = authHeader.split(' ')[1]; // Bearer <token>

    if (!token) {
      throw new AppError('Access token is required', 401);
    }

    const authService = AuthService.getInstance();

    // Check if token is blacklisted
    const isBlacklisted = await authService.isTokenBlacklisted(token);
    if (isBlacklisted) {
      throw new AppError('Token has been revoked', 401);
    }

    // Verify token
    const payload = authService.verifyAccessToken(token);

    // Add user data to request object
    req.user = {
      userId: payload.userId,
      email: payload.email,
      role: payload.role,
      practiceIds: payload.practiceIds,
    };

    return next();
  } catch (error) {
    logger.error('Authentication error:', error);

    if (error instanceof AppError) {
      return res.status(error.statusCode).json({
        error: error.message,
        code: 'AUTH_ERROR',
      });
    } else {
      return res.status(401).json({
        error: 'Invalid or expired token',
        code: 'AUTH_ERROR',
      });
    }
  }
};

// Middleware to check user roles
export const requireRole = (roles: string | string[]) => {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({
        error: 'Authentication required',
        code: 'AUTH_REQUIRED',
      });
    }

    const allowedRoles = Array.isArray(roles) ? roles : [roles];

    if (!allowedRoles.includes(req.user.role)) {
      return res.status(403).json({
        error: 'Insufficient permissions',
        code: 'INSUFFICIENT_PERMISSIONS',
        required: allowedRoles,
        current: req.user.role,
      });
    }

    return next();
  };
};

// Middleware to check practice access
export const requirePracticeAccess = (practiceIdParam = 'practiceId') => {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({
        error: 'Authentication required',
        code: 'AUTH_REQUIRED',
      });
    }

    const practiceIdCandidate = req.params[practiceIdParam] ?? (req.body as Record<string, unknown> | undefined)?.practiceId ?? req.query.practiceId;
    const practiceId = Array.isArray(practiceIdCandidate)
      ? practiceIdCandidate[0]
      : practiceIdCandidate;

    if (!practiceId || typeof practiceId !== 'string') {
      return res.status(400).json({
        error: 'Practice ID is required',
        code: 'PRACTICE_ID_REQUIRED',
      });
    }

    // Admin and executive roles have access to all practices
    if (['admin', 'executive'].includes(req.user.role)) {
      return next();
    }

    // Check if user has access to this practice
    if (!req.user.practiceIds.includes(practiceId)) {
      return res.status(403).json({
        error: 'No access to this practice',
        code: 'PRACTICE_ACCESS_DENIED',
      });
    }

    return next();
  };
};

// Optional authentication middleware (doesn't fail if no token)
export const optionalAuth = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const authHeader = req.headers.authorization;

    if (authHeader) {
      const token = authHeader.split(' ')[1];

      if (token) {
        const authService = AuthService.getInstance();

        // Check if token is blacklisted
        const isBlacklisted = await authService.isTokenBlacklisted(token);
        if (!isBlacklisted) {
          try {
            const payload = authService.verifyAccessToken(token);
            req.user = {
              userId: payload.userId,
              email: payload.email,
              role: payload.role,
              practiceIds: payload.practiceIds,
            };
          } catch (error) {
            // Token is invalid, but we continue without authentication
            logger.warn('Invalid token in optional auth:', error);
          }
        }
      }
    }

    return next();
  } catch (error) {
    logger.error('Optional authentication error:', error);
    return next(); // Continue without authentication
  }
};

// Middleware to check API key authentication (for external integrations)
export const apiKeyAuth = (req: Request, res: Response, next: NextFunction) => {
  try {
    const apiKey = req.headers['x-api-key'] as string;

    if (!apiKey) {
      throw new AppError('API key is required', 401);
    }

    // Validate API key (this would typically check against a database)
    if (apiKey !== process.env.API_KEY) {
      throw new AppError('Invalid API key', 401);
    }

    // For API key auth, we don't set user context
    // Instead, we might set some other context like service name
    req.user = {
      userId: 'system',
      email: 'system@dental-erp.com',
      role: 'system',
      practiceIds: [], // System access to all practices
    };

    return next();
  } catch (error) {
    logger.error('API key authentication error:', error);

    if (error instanceof AppError) {
      return res.status(error.statusCode).json({
        error: error.message,
        code: 'API_KEY_ERROR',
      });
    } else {
      return res.status(401).json({
        error: 'Invalid API key',
        code: 'API_KEY_ERROR',
      });
    }
  }
};

// Middleware for rate limiting per user
export const userRateLimit = (maxRequests: number, windowMs: number) => {
  const userRequests = new Map<string, { count: number; resetTime: number }>();

  return (req: Request, res: Response, next: NextFunction) => {
    const userId: string = req.user?.userId ?? req.ip ?? 'anonymous';
    const now = Date.now();

    let userLimit = userRequests.get(userId);

    if (!userLimit || now > userLimit.resetTime) {
      userLimit = {
        count: 0,
        resetTime: now + windowMs,
      };
    }

    userLimit.count += 1;
    userRequests.set(userId, userLimit);

    if (userLimit.count > maxRequests) {
      return res.status(429).json({
        error: 'Too many requests',
        code: 'RATE_LIMIT_EXCEEDED',
        retryAfter: Math.ceil((userLimit.resetTime - now) / 1000),
      });
    }

    // Set rate limit headers
    res.set({
      'X-RateLimit-Limit': maxRequests.toString(),
      'X-RateLimit-Remaining': Math.max(0, maxRequests - userLimit.count).toString(),
      'X-RateLimit-Reset': Math.ceil(userLimit.resetTime / 1000).toString(),
    });

    return next();
  };
};

// Middleware to validate user session
export const validateSession = async (req: Request, res: Response, next: NextFunction) => {
  try {
    if (!req.user) {
      throw new AppError('Authentication required', 401);
    }

    // Here you could add additional session validation
    // For example, check if user is still active, practice access is still valid, etc.

    return next();
  } catch (error) {
    logger.error('Session validation error:', error);

    if (error instanceof AppError) {
      return res.status(error.statusCode).json({
        error: error.message,
        code: 'SESSION_ERROR',
      });
    } else {
      return res.status(401).json({
        error: 'Session validation failed',
        code: 'SESSION_ERROR',
      });
    }
  }
};
