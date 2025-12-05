# MCP Architecture Migration - Completed

## Overview

The DentalERP backend has been successfully refactored to use the **MCP (Mapping & Control Plane) Server** architecture. All direct integrations with external systems (ADP, NetSuite, DentalIntel, Eaglesoft, Dentrix, Snowflake, etc.) have been removed and centralized in the MCP Server.

## Changes Made

### 1. **MCP Client Service** (`/src/services/mcpClient.ts`)
   - Created a centralized MCP client to communicate with the MCP Server API
   - Provides methods for:
     - `getMappings()` - Fetch entity mappings
     - `getFinancialSummary()` - Get financial data
     - `getProductionMetrics()` - Get production metrics
     - `triggerSync()` - Trigger data synchronization
     - `getSyncStatus()` - Check sync job status
     - `getForecast()` - Get forecasting data
     - `getAlerts()` - Fetch system alerts
     - `getIntegrationStatus()` - Get integration statuses
     - `testConnection()` - Test MCP Server connectivity
     - `queryDataLake()` - Execute custom data lake queries

### 2. **Environment Configuration** (`/src/config/environment.ts`)
   - **Removed** all integration-specific environment variables:
     - `DENTRIX_API_URL`, `DENTRIX_API_KEY`, `DENTRIX_API_SECRET`
     - `DENTALINTEL_API_URL`, `DENTALINTEL_API_KEY`, `DENTALINTEL_API_SECRET`
     - `ADP_API_URL`, `ADP_CLIENT_ID`, `ADP_CLIENT_SECRET`
     - `EAGLESOFT_API_URL`, `EAGLESOFT_API_KEY`, `EAGLESOFT_API_SECRET`
     - `NETSUITE_API_URL`, `NETSUITE_ACCOUNT`, `NETSUITE_CONSUMER_KEY`, etc.
     - `SNOWFLAKE_*` (all Snowflake configuration)
     - `INTEGRATION_CRYPTO_KEY`

   - **Added** MCP Server configuration:
     - `MCP_API_URL` - MCP Server base URL (default: `http://localhost:8000`)
     - `MCP_API_KEY` - API key for authenticating with MCP Server

### 3. **Analytics Service** (`/src/services/analytics.ts`)
   - Updated `getIntegrationStatus()` to fetch from MCP Server
   - Updated `getManagerMetrics()` to use MCP for production metrics and alerts
   - All integration status checks now proxy through MCP

### 4. **Integrations Routes** (`/src/routes/integrations.ts`)
   - **Removed** direct connector imports and usage
   - Updated `/status` endpoint to fetch from MCP Server
   - **Deprecated** credential management endpoints (now handled by MCP):
     - `GET /credentials`
     - `GET /credentials/:practiceId/:integrationType`
     - `PUT /credentials/:practiceId/:integrationType`
     - `DELETE /credentials/:practiceId/:integrationType`
   - Updated `POST /test-connection/:practiceId/:integrationType` to test via MCP
   - Removed Snowflake staging logic from file uploads (now handled by MCP)

### 5. **Removed Files and Services**

#### Connectors Removed:
   - `/services/integrationHub/connectors/adpConnector.ts`
   - `/services/integrationHub/connectors/dentalIntelConnector.ts`
   - `/services/integrationHub/connectors/dentrixConnector.ts`
   - `/services/integrationHub/connectors/eaglesoftConnector.ts`
   - `/services/integrationHub/connectors/netsuiteConnector.ts`
   - `/services/integrationHub/connectors/snowflakeConnector.ts`
   - `/services/integrationHub/connectors/baseConnector.ts`

#### Integration Hub Services Removed:
   - `/services/integrationHub/credentialsService.ts`
   - `/services/integrationHub/hub.ts`
   - `/services/integrationHub/index.ts`
   - `/services/integrationHub/netsuiteClient.ts`
   - `/services/integrationHub/netsuiteIngestion.ts`
   - `/services/integrationHub/registry.ts`
   - `/services/integrationHub/snowflakeIngestion.ts`
   - `/services/integrationHub/snowflakeService.ts`
   - `/services/integrationHub/types.ts`
   - `/services/snowflake.ts`
   - `/services/snowflakeIngestion.ts`

### 6. **Package Dependencies**
   - **Removed** `snowflake-sdk` dependency (no longer needed)
   - All other dependencies remain unchanged

### 7. **Environment Configuration File**
   - Created `.env.example` with MCP configuration
   - Documented deprecated environment variables

## Migration Guide

### For Developers

1. **Update your `.env` file**:
   ```bash
   # Remove all old integration configs
   # Add MCP Server configuration
   MCP_API_URL=http://localhost:8000
   MCP_API_KEY=your-secure-mcp-api-key-here
   ```

2. **Run database migrations** (if any schema changes):
   ```bash
   npm run db:migrate
   ```

3. **Install dependencies**:
   ```bash
   npm install
   ```

4. **Start the backend**:
   ```bash
   npm run dev
   ```

### For DevOps/Production

1. **Deploy MCP Server first** before deploying the updated ERP backend
2. **Update environment variables** in your deployment configuration
3. **Remove deprecated secrets** from secret managers (AWS Secrets Manager, etc.)
4. **Ensure MCP_API_KEY is securely stored** and accessible to the ERP backend

## API Changes

### Backward Compatibility

- Most endpoints remain the same
- Integration status responses now come from MCP Server
- Credential management endpoints return deprecation notices

### Breaking Changes

1. **Credential Management**:
   - Credential CRUD operations are now handled by MCP Server
   - Frontend should update to call MCP Server directly for credential management

2. **Direct Integration Access**:
   - No longer possible to directly query ADP, NetSuite, etc. from ERP
   - All data access must go through MCP Server APIs

## Testing

### Unit Tests
```bash
npm test
```

### Integration Tests
Ensure MCP Server is running:
```bash
# Test MCP connectivity
curl http://localhost:8000/api/v1/health

# Run integration tests
npm run test:integration
```

## Architecture Diagram

```
┌─────────────────┐
│   Frontend      │
│  (React/Vue)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐         ┌──────────────────┐
│   ERP Backend   │────────▶│   MCP Server     │
│   (Node.js)     │         │   (FastAPI)      │
└─────────────────┘         └────────┬─────────┘
         │                           │
         ▼                           ▼
┌─────────────────┐         ┌──────────────────┐
│   PostgreSQL    │         │  External APIs:  │
│  (ERP Database) │         │  - ADP           │
└─────────────────┘         │  - NetSuite      │
                            │  - DentalIntel   │
                            │  - Eaglesoft     │
                            │  - Dentrix       │
                            │  - Snowflake     │
                            └──────────────────┘
```

## Rollback Plan

If issues arise, you can rollback to the previous commit:

```bash
git log --oneline  # Find the commit before migration
git revert <commit-hash>
```

Or restore the old integration files from git history.

## Support

For questions or issues related to the MCP migration, contact the platform team or refer to:
- MCP Server documentation: `/documentation/prompt_mcp_server.md`
- MCP Server repository: (link to repo)

---

**Migration Date**: October 26, 2025
**Migration Status**: ✅ Complete
**MCP Server Version**: v1.0.0
