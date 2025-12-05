import compression from 'compression';
import cors, { CorsOptions } from 'cors';
import dotenv from 'dotenv';
import express from 'express';
import rateLimit from 'express-rate-limit';
import helmet from 'helmet';
import { createServer } from 'http';
import morgan from 'morgan';
import path from 'path';
import { Server } from 'socket.io';
import swaggerUi from 'swagger-ui-express';
import YAML from 'yamljs';

// Import middleware
import { validateEnvironment } from './config/environment';
import { auditMiddleware } from './middleware/audit';
import { authMiddleware } from './middleware/auth';
import { errorHandler } from './middleware/errorHandler';

// Import routes
import analyticsRoutes from './routes/analytics';
import appointmentRoutes from './routes/appointments';
import authRoutes from './routes/auth';
import dashboardRoutes from './routes/dashboard';
import integrationRoutes from './routes/integrations';
import locationRoutes from './routes/locations';
import operationsRoutes from './routes/operations';
import analyticsUnifiedRoutes from './routes/analyticsUnified';
import patientRoutes from './routes/patients';
import practiceRoutes from './routes/practices';
import reportRoutes from './routes/reports';
import tenantRoutes from './routes/tenants';
import userRoutes from './routes/users';
import widgetRoutes from './routes/widgets';

// Import services
import { DatabaseService } from './services/database';
import { setupSocketHandlers } from './services/socket';
import { logger } from './utils/logger';

// Load environment variables
dotenv.config();

// Validate environment variables
validateEnvironment();

// Note: Integration connectors are now managed by MCP Server
// No local initialization needed

const app = express();
// Respect reverse proxies (e.g. Nginx) so rate limiting sees the correct client IP
const trustProxySetting = process.env.TRUST_PROXY ?? '1';
app.set('trust proxy', trustProxySetting);
const server = createServer(app);
const io = new Server(server, {
  cors: {
    origin: process.env.FRONTEND_URL || 'http://localhost:3000',
    methods: ['GET', 'POST'],
    credentials: true,
  },
});

const PORT = process.env.PORT || 3001;

// Rate limiting - increased for production frontend
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 1000, // limit each IP to 1000 requests per windowMs (frontend needs higher limit)
  message: 'Too many requests from this IP, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
  skip: (req) => {
    // Skip rate limiting for health checks
    return req.path === '/health' || req.path === '/api/health';
  }
});

// CORS configuration (must be early to handle preflight before other middleware)
const allowedOrigins = (process.env.FRONTEND_URL || process.env.CORS_ORIGIN || 'http://localhost:3000,http://localhost:5173')
  .split(',')
  .map((o) => o.trim())
  .filter(Boolean);

const corsOptions: CorsOptions = {
  origin: (origin, callback) => {
    if (!origin) return callback(null, true); // allow non-browser or same-origin
    if (allowedOrigins.includes(origin)) return callback(null, true);
    return callback(new Error(`Origin ${origin} not allowed by CORS`));
  },
  credentials: true,
  optionsSuccessStatus: 200,
};

app.use(cors(corsOptions));
app.options('*', cors(corsOptions));

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
}));

// Apply rate limiting to API routes (after CORS so preflight returns proper headers)
app.use('/api/', limiter);

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Compression middleware
app.use(compression());

// Logging middleware
app.use(morgan('combined', {
  stream: {
    write: (message: string) => logger.info(message.trim()),
  },
}));

// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    // Check database connection
    const dbStatus = await DatabaseService.getInstance().checkHealth();

    const healthStatus = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      services: {
        database: dbStatus ? 'connected' : 'disconnected',
      },
      version: process.env.npm_package_version || '1.0.0',
      environment: process.env.NODE_ENV || 'development',
    };

    res.json(healthStatus);
  } catch (error) {
    logger.error('Health check failed:', error);
    res.status(503).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: 'Service unavailable',
    });
  }
});

// API Documentation
try {
  const swaggerDocument = YAML.load(path.join(__dirname, '../docs/swagger.yaml'));
  app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerDocument));
} catch (error) {
  logger.warn('Swagger documentation not found');
}

// Public routes (no authentication required)
app.use('/api/auth', authRoutes);

// Protected routes (authentication required)
app.use('/api/dashboard', authMiddleware, auditMiddleware, dashboardRoutes);
app.use('/api/practices', authMiddleware, auditMiddleware, practiceRoutes);
app.use('/api/locations', authMiddleware, auditMiddleware, locationRoutes);
app.use('/api/integrations', authMiddleware, auditMiddleware, integrationRoutes);
app.use('/api/patients', authMiddleware, auditMiddleware, patientRoutes);
app.use('/api/appointments', authMiddleware, auditMiddleware, appointmentRoutes);
app.use('/api/users', authMiddleware, auditMiddleware, userRoutes);
app.use('/api/widgets', authMiddleware, auditMiddleware, widgetRoutes);
app.use('/api/analytics', authMiddleware, auditMiddleware, analyticsRoutes);
app.use('/api/operations', authMiddleware, auditMiddleware, operationsRoutes);
app.use('/api/analytics-unified', authMiddleware, auditMiddleware, analyticsUnifiedRoutes);
app.use('/api/reports', authMiddleware, auditMiddleware, reportRoutes);
app.use('/api/tenants', authMiddleware, auditMiddleware, tenantRoutes);

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Route ${req.originalUrl} not found`,
  });
});

// Global error handler (must be last)
app.use(errorHandler);

// Socket.IO setup
setupSocketHandlers(io);

// Graceful shutdown
process.on('SIGTERM', async () => {
  logger.info('SIGTERM received, shutting down gracefully');

  server.close(() => {
    logger.info('HTTP server closed');
  });

  try {
    await DatabaseService.getInstance().close();
    logger.info('Database connections closed');
  } catch (error) {
    logger.error('Error closing database connections:', error);
  }

  process.exit(0);
});

process.on('SIGINT', async () => {
  logger.info('SIGINT received, shutting down gracefully');

  server.close(() => {
    logger.info('HTTP server closed');
  });

  try {
    await DatabaseService.getInstance().close();
    logger.info('Database connections closed');
  } catch (error) {
    logger.error('Error closing database connections:', error);
  }

  process.exit(0);
});

// Start server
async function startServer() {
  try {
    // Initialize database connection
    await DatabaseService.getInstance().initialize();
    logger.info('Database connected successfully');

    // Start HTTP server
    server.listen(PORT, () => {
      logger.info(`Server running on port ${PORT}`);
      logger.info(`Health check available at http://localhost:${PORT}/health`);
      logger.info(`API documentation available at http://localhost:${PORT}/api-docs`);
      logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
    });

  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception:', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

if (require.main === module) {
  startServer();
}

export { app, io, server };
export default app;
