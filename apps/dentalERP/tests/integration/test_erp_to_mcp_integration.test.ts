/**
 * ERP Backend to MCP Server Integration Tests
 * Tests the complete flow from ERP → MCP → Response
 */

import { describe, it, expect, beforeAll } from '@jest/globals';
import axios from 'axios';
import { getMCPClient } from '../../backend/src/services/mcpClient';

describe('ERP to MCP Integration Tests', () => {
  const MCP_URL = process.env.MCP_API_URL || 'http://localhost:8085';
  const MCP_API_KEY = process.env.MCP_API_KEY || 'dev-mcp-api-key-change-in-production-min-32-chars';
  
  let mcpClient: ReturnType<typeof getMCPClient>;
  
  beforeAll(() => {
    // Set environment for tests
    process.env.MCP_API_URL = MCP_URL;
    process.env.MCP_API_KEY = MCP_API_KEY;
    
    mcpClient = getMCPClient();
  });
  
  describe('Health Check', () => {
    it('should successfully connect to MCP Server', async () => {
      const isHealthy = await mcpClient.testConnection();
      expect(isHealthy).toBe(true);
    });
    
    it('should get health status via HTTP', async () => {
      const response = await axios.get(`${MCP_URL}/health`);
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('status', 'ok');
      expect(response.data).toHaveProperty('service', 'mcp-server');
    });
  });
  
  describe('Integration Status', () => {
    it('should fetch integration statuses from MCP', async () => {
      const statuses = await mcpClient.getIntegrationStatus();
      
      expect(Array.isArray(statuses)).toBe(true);
      expect(statuses.length).toBeGreaterThan(0);
      
      // Verify structure
      const status = statuses[0];
      expect(status).toHaveProperty('integrationType');
      expect(status).toHaveProperty('status');
    });
    
    it('should filter integration status by type', async () => {
      const statuses = await mcpClient.getIntegrationStatus('netsuite');
      
      if (statuses.length > 0) {
        expect(statuses.every(s => s.integrationType === 'netsuite')).toBe(true);
      }
    });
  });
  
  describe('Financial Data', () => {
    it('should fetch financial summary from MCP', async () => {
      const summary = await mcpClient.getFinancialSummary('downtown');
      
      expect(summary).toHaveProperty('locationId');
      expect(summary).toHaveProperty('revenue');
      expect(summary).toHaveProperty('expenses');
      expect(summary).toHaveProperty('netIncome');
      expect(summary).toHaveProperty('dateRange');
      
      // Verify numeric values
      expect(typeof summary.revenue).toBe('number');
      expect(typeof summary.expenses).toBe('number');
    });
    
    it('should respect date range parameters', async () => {
      const summary = await mcpClient.getFinancialSummary(
        'downtown',
        '2025-01-01',
        '2025-01-31'
      );
      
      expect(summary.dateRange.from).toBe('2025-01-01');
      expect(summary.dateRange.to).toBe('2025-01-31');
    });
  });
  
  describe('Production Metrics', () => {
    it('should fetch production metrics from MCP', async () => {
      const metrics = await mcpClient.getProductionMetrics('downtown');
      
      expect(metrics).toHaveProperty('locationId');
      expect(metrics).toHaveProperty('totalProduction');
      expect(metrics).toHaveProperty('totalCollections');
      expect(metrics).toHaveProperty('newPatients');
      expect(metrics).toHaveProperty('appointmentsScheduled');
    });
  });
  
  describe('Sync Operations', () => {
    it('should trigger sync job via MCP', async () => {
      const syncResponse = await mcpClient.triggerSync({
        integrationType: 'netsuite',
        entityTypes: ['journalEntry'],
        syncMode: 'incremental'
      });
      
      expect(syncResponse).toHaveProperty('syncId');
      expect(syncResponse).toHaveProperty('status');
      expect(syncResponse.syncId).toBeTruthy();
    });
    
    it('should check sync job status', async () => {
      // First trigger a sync
      const syncResponse = await mcpClient.triggerSync({
        integrationType: 'adp',
        entityTypes: ['employee'],
        syncMode: 'incremental'
      });
      
      const syncId = syncResponse.syncId;
      
      // Then check status
      const statusResponse = await mcpClient.getSyncStatus(syncId);
      
      expect(statusResponse.syncId).toBe(syncId);
      expect(statusResponse).toHaveProperty('status');
      expect(['pending', 'running', 'completed', 'failed']).toContain(statusResponse.status);
    });
  });
  
  describe('Forecasting', () => {
    it('should get revenue forecast from MCP', async () => {
      const forecast = await mcpClient.getForecast('downtown', 'revenue');
      
      expect(forecast).toHaveProperty('locationId');
      expect(forecast).toHaveProperty('metric', 'revenue');
      expect(forecast).toHaveProperty('predicted');
      expect(forecast).toHaveProperty('confidence');
      
      // Verify confidence is between 0 and 1
      expect(forecast.confidence).toBeGreaterThanOrEqual(0);
      expect(forecast.confidence).toBeLessThanOrEqual(1);
    });
  });
  
  describe('Alerts', () => {
    it('should fetch alerts from MCP', async () => {
      const alerts = await mcpClient.getAlerts();
      
      expect(Array.isArray(alerts)).toBe(true);
      
      if (alerts.length > 0) {
        const alert = alerts[0];
        expect(alert).toHaveProperty('id');
        expect(alert).toHaveProperty('severity');
        expect(alert).toHaveProperty('message');
        expect(['info', 'warning', 'critical']).toContain(alert.severity);
      }
    });
    
    it('should filter alerts by severity', async () => {
      const criticalAlerts = await mcpClient.getAlerts(undefined, 'critical');
      
      if (criticalAlerts.length > 0) {
        expect(criticalAlerts.every(a => a.severity === 'critical')).toBe(true);
      }
    });
  });
  
  describe('Error Handling', () => {
    it('should handle MCP Server unavailable gracefully', async () => {
      // Temporarily break the connection
      const originalUrl = process.env.MCP_API_URL;
      process.env.MCP_API_URL = 'http://invalid-mcp-server:9999';
      
      const brokenClient = getMCPClient();
      
      // Should handle error gracefully
      await expect(brokenClient.testConnection()).resolves.toBe(false);
      
      // Restore
      process.env.MCP_API_URL = originalUrl;
    });
    
    it('should handle invalid API key', async () => {
      const response = await axios.get(
        `${MCP_URL}/api/v1/integrations/status`,
        {
          headers: { Authorization: 'Bearer invalid-key' },
          validateStatus: () => true // Don't throw on error status
        }
      );
      
      expect(response.status).toBe(401);
    });
  });
  
  describe('Response Time SLAs', () => {
    it('should respond to health check in < 100ms', async () => {
      const start = Date.now();
      await mcpClient.testConnection();
      const duration = Date.now() - start;
      
      expect(duration).toBeLessThan(100);
    });
    
    it('should respond to data queries in < 500ms', async () => {
      const start = Date.now();
      await mcpClient.getFinancialSummary('downtown');
      const duration = Date.now() - start;
      
      expect(duration).toBeLessThan(500);
    });
  });
});

