import { NextFunction, Request, Response } from 'express';
import { logger } from '../utils/logger';

export const auditMiddleware = (req: Request, res: Response, next: NextFunction) => {
  // Log the request for audit purposes
  logger.info('API Request:', {
    method: req.method,
    url: req.url,
    ip: req.ip,
    userAgent: req.get('User-Agent'),
    userId: req.user?.userId,
    timestamp: new Date().toISOString(),
  });

  next();
};
