import axios, { AxiosInstance, AxiosResponse } from 'axios';
import config from '../config/environment';
import { logger } from '../utils/logger';

/**
 * MCP Client - Centralized client for all MCP (Mapping & Control Plane) Server interactions
 * Replaces direct integrations with ADP, NetSuite, DentalIntel, Eaglesoft, etc.
 */

export interface MCPMapping {
  entity: string;
  sourceSystem: string;
  targetSystem: string;
  mappingRules: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface MCPFinancialSummary {
  locationId: string;
  revenue: number;
  expenses: number;
  netIncome: number;
  payrollCosts: number;
  dateRange: {
    from: string;
    to: string;
  };
  breakdown: {
    category: string;
    amount: number;
  }[];
}

export interface MCPSyncRequest {
  integrationType: string;
  entityTypes: string[];
  locationIds?: string[];
  syncMode?: 'full' | 'incremental';
}

export interface MCPSyncResponse {
  syncId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startedAt: string;
  completedAt?: string;
  recordsProcessed?: number;
  errors?: string[];
}

export interface MCPForecast {
  locationId: string;
  metric: string;
  predicted: number;
  confidence: number;
  period: string;
  factors: Record<string, any>;
}

export interface MCPAlert {
  id: string;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  source: string;
  locationId?: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface MCPProductionMetrics {
  locationId: string;
  dateRange: {
    from: string;
    to: string;
  };
  totalProduction: number;
  totalCollections: number;
  newPatients: number;
  activePatients: number;
  appointmentsScheduled: number;
  appointmentsCompleted: number;
  cancellationRate: number;
  noShowRate: number;
}

export interface MCPIntegrationStatus {
  integrationType: string;
  status: 'connected' | 'disconnected' | 'error' | 'pending';
  lastSyncAt?: string;
  nextSyncAt?: string;
  errorMessage?: string;
  metadata?: Record<string, any>;
}

/**
 * MCP Client Service
 * Handles all communication with the MCP Server
 */
export class MCPClient {
  private client: AxiosInstance;
  private baseURL: string;
  private apiKey: string;

  constructor() {
    this.baseURL = config.mcp.apiUrl;
    this.apiKey = config.mcp.apiKey;

    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.apiKey}`,
        'X-Tenant-ID': 'silvercreek', // Multi-tenant support - Silver Creek Dental Partners
      },
    });

    // Request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        logger.debug('MCP API Request', {
          method: config.method,
          url: config.url,
          params: config.params,
        });
        return config;
      },
      (error) => {
        logger.error('MCP API Request Error', { error });
        return Promise.reject(error);
      }
    );

    // Response interceptor for logging and error handling
    this.client.interceptors.response.use(
      (response) => {
        logger.debug('MCP API Response', {
          status: response.status,
          url: response.config.url,
        });
        return response;
      },
      (error) => {
        logger.error('MCP API Response Error', {
          status: error.response?.status,
          url: error.config?.url,
          message: error.response?.data?.message || error.message,
        });
        return Promise.reject(error);
      }
    );
  }

  /**
   * Get entity mappings from MCP
   */
  async getMappings(entity: string): Promise<MCPMapping[]> {
    try {
      const response: AxiosResponse<MCPMapping[]> = await this.client.get(`/api/v1/mappings/${entity}`);
      return response.data;
    } catch (error) {
      logger.error('Failed to fetch mappings from MCP', { entity, error });
      throw error;
    }
  }

  /**
   * Get financial summary for a location
   */
  async getFinancialSummary(locationId: string, from?: string, to?: string): Promise<MCPFinancialSummary> {
    try {
      const params: any = { location: locationId };
      if (from) params.from = from;
      if (to) params.to = to;

      const response: AxiosResponse<MCPFinancialSummary> = await this.client.get('/api/v1/finance/summary', {
        params,
      });
      return response.data;
    } catch (error) {
      logger.error('Failed to fetch financial summary from MCP', { locationId, error });
      throw error;
    }
  }

  /**
   * Get production metrics for a location
   */
  async getProductionMetrics(locationId: string, from?: string, to?: string): Promise<MCPProductionMetrics> {
    try {
      const params: any = { location: locationId };
      if (from) params.from = from;
      if (to) params.to = to;

      const response: AxiosResponse<MCPProductionMetrics> = await this.client.get('/api/v1/production/metrics', {
        params,
      });
      return response.data;
    } catch (error) {
      logger.error('Failed to fetch production metrics from MCP', { locationId, error });
      throw error;
    }
  }

  /**
   * Trigger a data sync job
   */
  async triggerSync(request: MCPSyncRequest): Promise<MCPSyncResponse> {
    try {
      const response: AxiosResponse<MCPSyncResponse> = await this.client.post('/api/v1/sync/run', request);
      return response.data;
    } catch (error) {
      logger.error('Failed to trigger sync via MCP', { request, error });
      throw error;
    }
  }

  /**
   * Get sync job status
   */
  async getSyncStatus(syncId: string): Promise<MCPSyncResponse> {
    try {
      const response: AxiosResponse<MCPSyncResponse> = await this.client.get(`/api/v1/sync/${syncId}`);
      return response.data;
    } catch (error) {
      logger.error('Failed to fetch sync status from MCP', { syncId, error });
      throw error;
    }
  }

  /**
   * Get forecast data for a location
   */
  async getForecast(locationId: string, metric: string): Promise<MCPForecast> {
    try {
      const response: AxiosResponse<MCPForecast> = await this.client.get(`/api/v1/forecast/${locationId}`, {
        params: { metric },
      });
      return response.data;
    } catch (error) {
      logger.error('Failed to fetch forecast from MCP', { locationId, metric, error });
      throw error;
    }
  }

  /**
   * Get alerts from MCP
   */
  async getAlerts(locationId?: string, severity?: string): Promise<MCPAlert[]> {
    try {
      const params: any = {};
      if (locationId) params.location = locationId;
      if (severity) params.severity = severity;

      const response: AxiosResponse<MCPAlert[]> = await this.client.get('/api/v1/alerts', { params });
      return response.data;
    } catch (error) {
      logger.error('Failed to fetch alerts from MCP', { locationId, severity, error });
      throw error;
    }
  }

  /**
   * Get integration status
   */
  async getIntegrationStatus(integrationType?: string): Promise<MCPIntegrationStatus[]> {
    try {
      const params: any = {};
      if (integrationType) params.type = integrationType;

      const response: AxiosResponse<MCPIntegrationStatus[]> = await this.client.get('/api/v1/integrations/status', {
        params,
      });
      return response.data;
    } catch (error) {
      logger.error('Failed to fetch integration status from MCP', { integrationType, error });
      throw error;
    }
  }

  /**
   * Test connection to MCP Server
   */
  async testConnection(): Promise<boolean> {
    try {
      const response = await this.client.get('/api/v1/health');
      return response.status === 200;
    } catch (error) {
      logger.error('MCP connection test failed', { error });
      return false;
    }
  }

  /**
   * Generic GET request to MCP Server
   * For use when no specific method exists
   */
  async get(path: string, config?: any): Promise<AxiosResponse> {
    try {
      return await this.client.get(path, config);
    } catch (error) {
      logger.error('MCP GET request failed', { path, error });
      throw error;
    }
  }

  /**
   * Generic POST request to MCP Server
   * For use when no specific method exists
   */
  async post(path: string, data?: any, config?: any): Promise<AxiosResponse> {
    try {
      return await this.client.post(path, data, config);
    } catch (error) {
      logger.error('MCP POST request failed', { path, error });
      throw error;
    }
  }

  /**
   * Generic PUT request to MCP Server
   */
  async put(path: string, data?: any, config?: any): Promise<AxiosResponse> {
    try {
      return await this.client.put(path, data, config);
    } catch (error) {
      logger.error('MCP PUT request failed', { path, error });
      throw error;
    }
  }

  /**
   * Generic DELETE request to MCP Server
   */
  async delete(path: string, config?: any): Promise<AxiosResponse> {
    try {
      return await this.client.delete(path, config);
    } catch (error) {
      logger.error('MCP DELETE request failed', { path, error });
      throw error;
    }
  }

  /**
   * Get raw data from data lake for custom queries
   */
  async queryDataLake(query: string, params?: Record<string, any>): Promise<any[]> {
    try {
      const response: AxiosResponse<any[]> = await this.client.post('/api/v1/datalake/query', {
        query,
        params,
      });
      return response.data;
    } catch (error) {
      logger.error('Failed to query data lake via MCP', { query, error });
      throw error;
    }
  }
}

// Singleton instance
let mcpClientInstance: MCPClient | null = null;

export function getMCPClient(): MCPClient {
  if (!mcpClientInstance) {
    mcpClientInstance = new MCPClient();
  }
  return mcpClientInstance;
}

export default MCPClient;
