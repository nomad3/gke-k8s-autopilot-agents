import { Server, Socket } from 'socket.io';
import { logger } from '../utils/logger';
import { AuthService } from './auth';

interface AuthenticatedSocket extends Socket {
  userId?: string;
  role?: string;
  practiceIds?: string[];
}

export function setupSocketHandlers(io: Server) {
  // Authentication middleware for WebSocket connections
  io.use(async (socket: AuthenticatedSocket, next) => {
    try {
      const token = socket.handshake.auth.token;

      if (!token) {
        return next(new Error('Authentication token required'));
      }

      const authService = AuthService.getInstance();
      const payload = authService.verifyAccessToken(token);

      socket.userId = payload.userId;
      socket.role = payload.role;
      socket.practiceIds = payload.practiceIds;

      logger.info('Socket authenticated:', {
        userId: payload.userId,
        role: payload.role,
        socketId: socket.id
      });

      next();
    } catch (error) {
      logger.error('Socket authentication failed:', error);
      next(new Error('Authentication failed'));
    }
  });

  io.on('connection', (socket: AuthenticatedSocket) => {
    logger.info('BI Dashboard client connected:', {
      socketId: socket.id,
      userId: socket.userId,
      role: socket.role
    });

    // Join role-based rooms for targeted updates
    if (socket.role) {
      socket.join(`role:${socket.role}`);
    }

    // Join practice-based rooms
    if (socket.practiceIds) {
      socket.practiceIds.forEach(practiceId => {
        socket.join(`practice:${practiceId}`);
      });
    }

    // Subscribe to analytics updates
    socket.on('subscribe-analytics', (data) => {
      logger.info('Client subscribed to analytics:', {
        socketId: socket.id,
        role: data.role,
        practiceIds: data.practiceIds
      });

      socket.join('analytics-updates');
      socket.emit('subscription-confirmed', {
        type: 'analytics',
        role: data.role,
        practiceIds: data.practiceIds
      });
    });

    // Handle analytics refresh requests
    socket.on('refresh-analytics', (data) => {
      logger.info('Analytics refresh requested:', {
        socketId: socket.id,
        role: data.role
      });

      // Trigger analytics refresh and emit updated data
      setTimeout(() => {
        socket.emit('analytics-update', {
          type: 'refresh',
          timestamp: new Date().toISOString(),
          message: 'Analytics data refreshed'
        });
      }, 1000);
    });

    // Handle integration sync requests
    socket.on('sync-integration', (data) => {
      logger.info('Integration sync requested:', {
        socketId: socket.id,
        system: data.system
      });

      // Simulate integration sync
      setTimeout(() => {
        socket.emit('integration-status-change', {
          system: data.system,
          status: 'syncing',
          timestamp: new Date().toISOString()
        });

        // Simulate completion
        setTimeout(() => {
          socket.emit('integration-status-change', {
            system: data.system,
            status: 'connected',
            timestamp: new Date().toISOString()
          });
        }, 3000);
      }, 500);
    });

    socket.on('disconnect', (reason) => {
      logger.info('BI Dashboard client disconnected:', {
        socketId: socket.id,
        userId: socket.userId,
        reason
      });
    });
  });

  // Simulate periodic BI updates (in production, this would be triggered by external system webhooks)
  setInterval(() => {
    // Send KPI updates to executives
    io.to('role:executive').emit('kpi-update', {
      type: 'scheduled',
      timestamp: new Date().toISOString(),
      data: {
        revenue: Math.floor(Math.random() * 100000) + 2300000,
        patients: Math.floor(Math.random() * 1000) + 15000,
        efficiency: Math.floor(Math.random() * 10) + 90
      }
    });

    // Send operational updates to managers
    io.to('role:manager').emit('operational-update', {
      type: 'scheduled',
      timestamp: new Date().toISOString(),
      data: {
        appointments: Math.floor(Math.random() * 10) + 25,
        revenue: Math.floor(Math.random() * 1000) + 8000,
        alerts: Math.floor(Math.random() * 5)
      }
    });
  }, 30000); // Every 30 seconds for demo purposes

  // Simulate integration status changes
  setInterval(() => {
    const systems = ['dentrix', 'dentalintel', 'adp', 'eaglesoft'];
    const randomSystem = systems[Math.floor(Math.random() * systems.length)];

    io.emit('integration-status-change', {
      system: randomSystem,
      status: Math.random() > 0.8 ? 'syncing' : 'connected',
      timestamp: new Date().toISOString(),
      health: 'healthy'
    });
  }, 60000); // Every minute
}
