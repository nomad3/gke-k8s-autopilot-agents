import { Router } from 'express';
import { getMCPClient } from '../services/mcpClient';
import { logger } from '../utils/logger';

const router = Router();
const mcpClient = getMCPClient();

/**
 * Tenant Management Routes
 * Proxies tenant operations to MCP Server
 */

// Get all tenants
router.get('/', async (req, res, next) => {
  try {
    const response = await mcpClient.get('/api/v1/tenants/');
    res.json(response.data);
  } catch (error: any) {
    logger.error('Failed to fetch tenants from MCP', { error });
    next(error);
  }
});

// Get specific tenant
router.get('/:tenantId', async (req, res, next) => {
  try {
    const { tenantId } = req.params;
    const response = await mcpClient.get(`/api/v1/tenants/${tenantId}`);
    res.json(response.data);
  } catch (error: any) {
    logger.error('Failed to fetch tenant from MCP', { tenantId: req.params.tenantId, error });
    next(error);
  }
});

// Create new tenant
router.post('/', async (req, res, next) => {
  try {
    const response = await mcpClient.post('/api/v1/tenants/', req.body);
    res.status(201).json(response.data);
  } catch (error: any) {
    logger.error('Failed to create tenant in MCP', { error });
    next(error);
  }
});

// Update tenant
router.put('/:tenantId', async (req, res, next) => {
  try {
    const { tenantId } = req.params;
    const response = await mcpClient.put(`/api/v1/tenants/${tenantId}`, req.body);
    res.json(response.data);
  } catch (error: any) {
    logger.error('Failed to update tenant in MCP', { tenantId: req.params.tenantId, error });
    next(error);
  }
});

// Delete tenant
router.delete('/:tenantId', async (req, res, next) => {
  try {
    const { tenantId } = req.params;
    await mcpClient.delete(`/api/v1/tenants/${tenantId}`);
    res.status(204).send();
  } catch (error: any) {
    logger.error('Failed to delete tenant in MCP', { tenantId: req.params.tenantId, error });
    next(error);
  }
});

// Get tenant warehouses
router.get('/:tenantId/warehouses', async (req, res, next) => {
  try {
    const { tenantId } = req.params;
    const response = await mcpClient.get(`/api/v1/tenants/${tenantId}/warehouses`);
    res.json(response.data);
  } catch (error: any) {
    logger.error('Failed to fetch tenant warehouses from MCP', { tenantId: req.params.tenantId, error });
    next(error);
  }
});

// Add tenant warehouse
router.post('/:tenantId/warehouses', async (req, res, next) => {
  try {
    const { tenantId } = req.params;
    const response = await mcpClient.post(`/api/v1/tenants/${tenantId}/warehouses`, req.body);
    res.status(201).json(response.data);
  } catch (error: any) {
    logger.error('Failed to add tenant warehouse in MCP', { tenantId: req.params.tenantId, error });
    next(error);
  }
});

// Get tenant integrations
router.get('/:tenantId/integrations', async (req, res, next) => {
  try {
    const { tenantId } = req.params;
    const response = await mcpClient.get(`/api/v1/tenants/${tenantId}/integrations`);
    res.json(response.data);
  } catch (error: any) {
    logger.error('Failed to fetch tenant integrations from MCP', { tenantId: req.params.tenantId, error });
    next(error);
  }
});

// Add tenant integration
router.post('/:tenantId/integrations', async (req, res, next) => {
  try {
    const { tenantId } = req.params;
    const response = await mcpClient.post(`/api/v1/tenants/${tenantId}/integrations`, req.body);
    res.status(201).json(response.data);
  } catch (error: any) {
    logger.error('Failed to add tenant integration in MCP', { tenantId: req.params.tenantId, error });
    next(error);
  }
});

// Update tenant integration
router.put('/:tenantId/integrations/:integrationId', async (req, res, next) => {
  try {
    const { tenantId, integrationId } = req.params;
    const response = await mcpClient.put(
      `/api/v1/tenants/${tenantId}/integrations/${integrationId}`,
      req.body
    );
    res.json(response.data);
  } catch (error: any) {
    logger.error('Failed to update tenant integration in MCP', {
      tenantId: req.params.tenantId,
      integrationId: req.params.integrationId,
      error
    });
    next(error);
  }
});

// Get all available integrations
router.get('/catalog/integrations', async (req, res, next) => {
  try {
    const response = await mcpClient.get('/api/v1/integrations/');
    res.json(response.data);
  } catch (error: any) {
    logger.error('Failed to fetch integrations catalog from MCP', { error });
    next(error);
  }
});

// Get integration details
router.get('/catalog/integrations/:integrationId', async (req, res, next) => {
  try {
    const { integrationId } = req.params;
    const response = await mcpClient.get(`/api/v1/integrations/${integrationId}`);
    res.json(response.data);
  } catch (error: any) {
    logger.error('Failed to fetch integration details from MCP', { integrationId: req.params.integrationId, error });
    next(error);
  }
});

// Test integration connection
router.post('/test-integration', async (req, res, next) => {
  try {
    const { tenantId, integrationType, config } = req.body;
    const response = await mcpClient.post(
      '/api/v1/integrations/test',
      { type: integrationType, config },
      { headers: { 'X-Tenant-ID': tenantId } }
    );
    res.json(response.data);
  } catch (error: any) {
    logger.error('Failed to test integration connection via MCP', { error });
    next(error);
  }
});

// Test warehouse connection
router.post('/test-warehouse', async (req, res, next) => {
  try {
    const response = await mcpClient.post('/api/v1/warehouse/test', req.body);
    res.json(response.data);
  } catch (error: any) {
    logger.error('Failed to test warehouse connection via MCP', { error });
    next(error);
  }
});

// Get warehouse stats
router.get('/:tenantId/warehouse/stats', async (req, res, next) => {
  try {
    const { tenantId } = req.params;
    const response = await mcpClient.get('/api/v1/warehouse/stats', {
      headers: { 'X-Tenant-ID': tenantId }
    });
    res.json(response.data);
  } catch (error: any) {
    logger.error('Failed to fetch warehouse stats from MCP', { tenantId: req.params.tenantId, error });
    next(error);
  }
});

// Get all products
router.get('/catalog/products', async (req, res, next) => {
  try {
    const response = await mcpClient.get('/api/v1/products/');
    res.json(response.data);
  } catch (error: any) {
    logger.error('Failed to fetch products catalog from MCP', { error });
    next(error);
  }
});

// Get product details
router.get('/catalog/products/:productCode', async (req, res, next) => {
  try {
    const { productCode } = req.params;
    const response = await mcpClient.get(`/api/v1/products/${productCode}`);
    res.json(response.data);
  } catch (error: any) {
    logger.error('Failed to fetch product details from MCP', { productCode: req.params.productCode, error });
    next(error);
  }
});

export default router;
