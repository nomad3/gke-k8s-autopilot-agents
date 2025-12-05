import { Router, type Request, type Response } from 'express';
import fs from 'fs/promises';
import multer, { type FileFilterCallback } from 'multer';
import path from 'path';
import config from '../config/environment';
import { ManualIngestionService, type ManualIngestionStatus } from '../services/manualIngestion';
import { getMCPClient } from '../services/mcpClient';
import { logger } from '../utils/logger';

const router = Router();

const mcpClient = getMCPClient();

const hasIntegrationAdminRole = (req: Request): boolean => {
  const role = (req as any).user?.role as string | undefined;
  return Boolean(role && ['admin', 'executive'].includes(role));
};

const uploadRoot = path.isAbsolute(config.upload.ingestionExportPath)
  ? config.upload.ingestionExportPath
  : path.join(process.cwd(), config.upload.ingestionExportPath);

void fs.mkdir(uploadRoot, { recursive: true }).catch((err) => {
  logger.warn('Failed to create ingestion upload root', { uploadRoot, error: err });
});

const storage = multer.diskStorage({
  destination: (req: Request, _file: Express.Multer.File, cb: (error: Error | null, destination: string) => void) => {
    const practiceId = String((req.body?.practiceId || 'unknown')).trim() || 'unknown';
    const today = new Date().toISOString().slice(0, 10);
    const dir = path.join(uploadRoot, practiceId, today);
    fs.mkdir(dir, { recursive: true })
      .then(() => cb(null, dir))
      .catch((err) => {
        logger.error('Failed to create ingestion upload directory', { dir, error: err });
        cb(err as Error, uploadRoot);
      });
  },
  filename: (_req: Request, file: Express.Multer.File, cb: (error: Error | null, filename: string) => void) => {
    cb(null, `${Date.now()}_${file.originalname}`);
  },
});

const upload = multer({
  storage,
  limits: {
    fileSize: config.upload.maxFileSize,
  },
  fileFilter: (_req: Request, file: Express.Multer.File, cb: FileFilterCallback) => {
    const allowed = config.upload.allowedTypes || [];
    if (!allowed.length || allowed.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error(`Unsupported file type: ${file.mimetype}`));
    }
  },
});

router.get('/status', async (_req: Request, res: Response) => {
  try {
    logger.info('Integration status requested via MCP');

    // Fetch integration status from MCP Server
    const integrationStatuses = await mcpClient.getIntegrationStatus();

    return res.json({
      success: true,
      message: 'Integration statuses fetched from MCP Server',
      integrations: integrationStatuses,
      manualIngestion: {
        enabled: true,
        exportPath: config.upload.ingestionExportPath,
        externalTarget: config.upload.externalTarget,
      },
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    logger.error('Failed to fetch integration status from MCP', { error });
    return res.status(500).json({
      success: false,
      error: 'Failed to fetch integration status from MCP Server',
      fallback: {
        message: 'Manual uploads can be used as a fallback.',
        manualIngestion: {
          enabled: true,
          exportPath: config.upload.ingestionExportPath,
          externalTarget: config.upload.externalTarget,
        },
      },
      timestamp: new Date().toISOString(),
    });
  }
});

router.get('/ingestion/supported', (_req: Request, res: Response) => {
  return res.json({
    success: true,
    maxFileSize: config.upload.maxFileSize,
    allowedTypes: config.upload.allowedTypes,
    exportPath: config.upload.ingestionExportPath,
    externalTarget: config.upload.externalTarget,
  });
});

router.post('/ingestion/upload', upload.single('file'), async (req: Request, res: Response) => {
  try {
    const practiceId = String(req.body?.practiceId || '').trim();
    const sourceSystem = String(req.body?.sourceSystem || '').trim();
    const dataset = req.body?.dataset ? String(req.body.dataset) : undefined;
    const notes = req.body?.notes ? String(req.body.notes) : undefined;
    const userId = (req as any).user?.userId as string | undefined;

    if (!practiceId) {
      return res.status(400).json({ error: 'practiceId is required' });
    }

    if (!sourceSystem) {
      return res.status(400).json({ error: 'sourceSystem is required' });
    }

    if (!req.file) {
      return res.status(400).json({ error: 'File upload is required' });
    }

    const uploadRecord = await ManualIngestionService.createUpload({
      practiceId,
      uploadedBy: userId,
      sourceSystem,
      dataset,
      originalFilename: req.file.originalname,
      storagePath: req.file.path,
      status: 'stored',
      externalLocation: config.upload.externalTarget ?? null,
      notes,
    });

    // Note: Snowflake staging is now handled by MCP Server
    // The MCP Server will pick up files from the manual ingestion location

    return res.status(201).json({
      success: true,
      upload: uploadRecord,
      instructions: config.upload.externalTarget
        ? `File stored locally and ready to deliver to ${config.upload.externalTarget}. MCP Server will process this file.`
        : 'File stored locally and ready for MCP Server pickup.',
    });
  } catch (error: any) {
    logger.error('Manual ingestion upload failed', { error });
    return res.status(500).json({ error: error?.message || 'Failed to process upload' });
  }
});

router.get('/ingestion/uploads', async (req: Request, res: Response) => {
  try {
    const practiceId = req.query.practiceId ? String(req.query.practiceId) : undefined;
    const limitParam = req.query.limit ? Number(req.query.limit) : undefined;
    const limit = Number.isFinite(limitParam) ? Math.min(Math.max(limitParam!, 1), 200) : 100;
    const statusParam = req.query.status || req.query.statuses;
    const statuses = Array.isArray(statusParam)
      ? statusParam.map((value) => String(value))
      : statusParam
        ? String(statusParam).split(',').map((value) => value.trim()).filter(Boolean)
        : undefined;

    const practiceIds = practiceId
      ? [practiceId]
      : ((req as any).user?.practiceIds as string[] | undefined) || undefined;

    const uploads = await ManualIngestionService.listUploads({
      practiceIds,
      limit,
      statuses: statuses as ManualIngestionStatus[] | undefined,
    });
    return res.json({ success: true, uploads });
  } catch (error: any) {
    logger.error('Failed to list manual ingestion uploads', { error });
    return res.status(500).json({ error: error?.message || 'Failed to list uploads' });
  }
});

router.get('/ingestion/uploads/:id', async (req: Request, res: Response) => {
  try {
    const upload = await ManualIngestionService.getUpload(String(req.params.id));
    if (!upload) {
      return res.status(404).json({ error: 'Upload not found' });
    }
    return res.json({ success: true, upload });
  } catch (error: any) {
    logger.error('Failed to get manual ingestion upload', { id: req.params.id, error });
    return res.status(500).json({ error: error?.message || 'Failed to fetch upload' });
  }
});

router.post('/ingestion/uploads/:id/handoff', async (req: Request, res: Response) => {
  try {
    const allowedStatuses: ManualIngestionStatus[] = ['stored', 'delivered', 'failed', 'archived'];
    const status = req.body?.status ? String(req.body.status) as ManualIngestionStatus : undefined;
    const externalLocation = req.body?.externalLocation ? String(req.body.externalLocation) : undefined;
    const notes = req.body?.notes ? String(req.body.notes) : undefined;

    if (status && !allowedStatuses.includes(status)) {
      return res.status(400).json({ error: `status must be one of: ${allowedStatuses.join(', ')}` });
    }

    const upload = await ManualIngestionService.updateUpload(String(req.params.id), {
      status,
      externalLocation: externalLocation ?? null,
      notes: notes ?? null,
    });

    if (!upload) {
      return res.status(404).json({ error: 'Upload not found' });
    }

    return res.json({ success: true, upload });
  } catch (error: any) {
    logger.error('Failed to update manual ingestion upload', { id: req.params.id, error });
    return res.status(500).json({ error: error?.message || 'Failed to update upload' });
  }
});

router.delete('/ingestion/uploads/:id', async (req: Request, res: Response) => {
  try {
    const upload = await ManualIngestionService.deleteUpload(String(req.params.id));
    if (!upload) {
      return res.status(404).json({ error: 'Upload not found' });
    }

    if (upload.storagePath) {
      fs.unlink(upload.storagePath).catch((err) => {
        logger.warn('Failed to remove ingestion file from disk', { path: upload.storagePath, error: err });
      });
    }

    return res.json({ success: true, upload });
  } catch (error: any) {
    logger.error('Failed to delete manual ingestion upload', { id: req.params.id, error });
    return res.status(500).json({ error: error?.message || 'Failed to delete upload' });
  }
});

// Credentials are now managed by MCP Server
// These endpoints are deprecated but maintained for backward compatibility
router.get('/credentials', async (req: Request, res: Response) => {
  if (!hasIntegrationAdminRole(req)) {
    return res.status(403).json({ error: 'Forbidden' });
  }

  return res.json({
    success: true,
    message: 'Integration credentials are now managed by MCP Server. Please use MCP Server API directly.',
    credentials: [],
    deprecated: true
  });
});

router.get('/credentials/:practiceId/:integrationType', async (req: Request, res: Response) => {
  if (!hasIntegrationAdminRole(req)) {
    return res.status(403).json({ error: 'Forbidden' });
  }

  return res.json({
    success: false,
    message: 'Integration credentials are now managed by MCP Server. Please use MCP Server API directly.',
    deprecated: true
  });
});

router.put('/credentials/:practiceId/:integrationType', async (req: Request, res: Response) => {
  if (!hasIntegrationAdminRole(req)) {
    return res.status(403).json({ error: 'Forbidden' });
  }

  return res.status(501).json({
    success: false,
    message: 'Integration credentials are now managed by MCP Server. Please use MCP Server API directly.',
    deprecated: true
  });
});

router.delete('/credentials/:practiceId/:integrationType', async (req: Request, res: Response) => {
  if (!hasIntegrationAdminRole(req)) {
    return res.status(403).json({ error: 'Forbidden' });
  }

  return res.status(501).json({
    success: false,
    message: 'Integration credentials are now managed by MCP Server. Please use MCP Server API directly.',
    deprecated: true
  });
});

router.post('/test-connection/:practiceId/:integrationType', async (req: Request, res: Response) => {
  try {
    if (!hasIntegrationAdminRole(req)) {
      return res.status(403).json({ error: 'Forbidden' });
    }

    const integrationType = String(req.params.integrationType);

    // Test connection via MCP Server
    const isConnected = await mcpClient.testConnection();

    if (isConnected) {
      // Get specific integration status
      const statuses = await mcpClient.getIntegrationStatus(integrationType);
      const status = statuses.find(s => s.integrationType === integrationType);

      return res.json({
        success: true,
        message: 'MCP Server is accessible. Integration status retrieved.',
        integrationType,
        status: status || { integrationType, status: 'unknown' },
        note: 'Connection tests are now performed by MCP Server'
      });
    } else {
      return res.status(503).json({
        success: false,
        error: 'MCP Server is not accessible',
        integrationType
      });
    }
  } catch (error: any) {
    logger.error('Failed to test integration connection via MCP', { error });
    return res.status(500).json({
      success: false,
      error: error?.message || 'Failed to test integration connection via MCP Server'
    });
  }
});

export default router;
