# URGENT: Analytics Dashboard Data Flow Fix - Claude Handoff

## Current Situation (as of 2025-11-21 18:15 -03:00)

### What's Working ✅
- Login is successful (fixed `refresh_tokens.token` column to TEXT type)
- Silver Creek tenant is visible and selectable in the UI
- All 4 tenants (silvercreek, eastlake, torrey_pines, ads) are seeded in MCP database
- MCP database has `tenant_warehouses` and `tenant_integrations` configured for Silver Creek

### What's Broken ❌
- **CRITICAL**: Analytics dashboard shows "No practice data available" for ALL tenants
- The `bi_daily_metrics` table in `dental_erp_dev` database is EMPTY
- Analytics data ($309M that was previously visible) is gone
- The Snowflake/NetSuite integration refactor broke the data pipeline

## Root Cause Analysis

1. **Previous working state**: Analytics data was flowing from Snowflake → MCP Server → Backend API → Frontend
2. **What broke it**: Refactored Snowflake tables to integrate with NetSuite API, but NetSuite API integration failed
3. **Current state**: The analytics endpoints in `backend/src/routes/analytics.ts` proxy to MCP server, but MCP server can't return data because:
   - Snowflake tables are in wrong format or empty
   - MCP server queries are failing
   - No fallback data source

## Architecture Understanding

### Data Flow (Should Be)
```
Snowflake (BRONZE/SILVER/GOLD layers)
    ↓
MCP Server (queries Snowflake, returns JSON)
    ↓
Backend API (proxies to MCP, adds auth)
    ↓
Frontend (displays in dashboard)
```

### Key Endpoints
- Frontend calls: `/api/analytics/executive-kpis`, `/api/analytics/production/summary`, etc.
- Backend proxies to: MCP Server `/api/v1/analytics/*` endpoints
- MCP Server queries: Snowflake `DENTAL_ERP_DW.BRONZE_GOLD.*` tables

### Silver Creek Tenant Structure
- **Silver Creek** = Rollup/aggregate tenant showing combined metrics from 14 subsidiaries
- Each of the 14 subsidiaries should be individual selectable tenants:
  1. SCDP Silver Creek
  2. SCDP Mountain View
  3. SCDP Sunnyvale
  4. SCDP Santa Clara
  5. SCDP Milpitas
  6. SCDP Fremont
  7. SCDP Newark
  8. SCDP Union City
  9. SCDP Hayward
  10. SCDP San Leandro
  11. SCDP Oakland
  12. SCDP Berkeley
  13. SCDP Richmond
  14. (One more location)

## Your Mission

### Primary Goal
**Get the analytics dashboard showing data for Silver Creek tenant within 2 hours.**

### Constraints
1. ✅ **Use Git workflow**: All changes must be committed, pushed, pulled on GCP VM, and deployed via `deploy.sh`
2. ✅ **No manual docker cp/scp**: Everything through Git and proper deployment
3. ✅ **Fix forward, don't revert**: The Snowflake refactor is done, we need to make it work
4. ✅ **Test locally first**: Verify changes work locally before deploying to VM

### Step-by-Step Action Plan

#### Phase 1: Diagnose MCP Server Snowflake Connection (30 min)

1. **Check MCP Server logs** for Snowflake connection errors:
   ```bash
   gcloud compute ssh root@dental-erp-vm --zone=us-central1-a --command "docker logs --tail 100 dental-erp_mcp-server-prod_1"
   ```

2. **Verify Snowflake credentials** are set in MCP container:
   - Check if `.env` file has `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`
   - Verify `tenant_warehouses` table has correct Snowflake config for `silvercreek` tenant

3. **Test Snowflake connection** from MCP container:
   - Create a test script to query Snowflake directly
   - Verify tables exist: `DENTAL_ERP_DW.BRONZE_GOLD.practice_financials`, `daily_production_metrics`, etc.

#### Phase 2: Fix MCP Server Analytics Endpoints (45 min)

1. **Locate MCP analytics endpoints**:
   - File: `mcp-server/src/routes/analytics.ts` (or similar)
   - Endpoints: `/api/v1/analytics/production/summary`, `/api/v1/analytics/financial/summary`

2. **Update queries to match current Snowflake schema**:
   - If tables were renamed during refactor, update query table names
   - If columns changed, update SELECT statements
   - Add proper error handling and logging

3. **Add fallback/mock data** for demo if Snowflake is unavailable:
   - Return hardcoded $309M metrics if Snowflake query fails
   - Log warning but don't crash

4. **Test locally**:
   ```bash
   cd mcp-server
   npm run dev
   # Test endpoint: curl http://localhost:8085/api/v1/analytics/production/summary
   ```

#### Phase 3: Seed 14 Silver Creek Subsidiary Tenants (30 min)

1. **Update `mcp-server/seed_data.py`** to include all 14 subsidiaries as separate tenants
2. **Each subsidiary tenant needs**:
   - Unique `tenant_code` (e.g., `silvercreek_mountainview`)
   - Unique `tenant_name` (e.g., "SCDP Mountain View")
   - Same Snowflake warehouse config as parent
   - NetSuite integration config

3. **Update `backend/src/database/seed.ts`** to create practices for each subsidiary

#### Phase 4: Deploy and Verify (15 min)

1. **Commit all changes**:
   ```bash
   git add -A
   git commit -m "Fix MCP analytics endpoints and add Silver Creek subsidiaries"
   git push origin main
   ```

2. **Deploy on GCP VM**:
   ```bash
   gcloud compute ssh root@dental-erp-vm --zone=us-central1-a
   cd /opt/dental-erp
   git pull

   # Set proper MCP API keys (generate secure 32+ char strings)
   export MCP_API_KEY="$(openssl rand -base64 32)"
   export MCP_SECRET_KEY="$(openssl rand -base64 32)"

   bash deploy.sh
   ```

3. **Verify in browser**:
   - Go to https://dentalerp.agentprovision.com/analytics/overview
   - Login with Admin Access
   - Select "Silver Creek Dental Partners, LLC"
   - Verify $309M metrics appear

## Key Files to Modify

### MCP Server
- `mcp-server/src/routes/analytics.ts` - Analytics API endpoints
- `mcp-server/src/services/snowflake.ts` - Snowflake query service
- `mcp-server/seed_data.py` - Tenant seeding script
- `mcp-server/scripts/mcp-seed-silvercreek.py` - Already updated, may need tweaks

### Backend
- `backend/src/routes/analytics.ts` - Already proxies to MCP (should be OK)
- `backend/src/database/seed.ts` - Add 14 subsidiary practices

### Deploy
- `deploy.sh` - Deployment script (already configured)

## Database Credentials

### PostgreSQL (dental_erp_dev)
- Host: `postgres` (in Docker network)
- User: `postgres`
- Password: `N6At7Nao7EnVPJ9euYhirIgwZI6m69poJEp/IqIw1xI=`
- Database: `dental_erp_dev`

### PostgreSQL (mcp)
- Host: `postgres` (in Docker network)
- User: `postgres`
- Password: `N6At7Nao7EnVPJ9euYhirIgwZI6m69poJEp/IqIw1xI=`
- Database: `mcp`

### Snowflake
- Check `.env` files in `mcp-server/` for credentials
- Account: Should be in `SNOWFLAKE_ACCOUNT` env var
- Database: `DENTAL_ERP_DW`
- Schemas: `BRONZE`, `BRONZE_SILVER`, `BRONZE_GOLD`

## Success Criteria

1. ✅ Analytics dashboard shows $309M total production for Silver Creek
2. ✅ All 14 subsidiary tenants are visible and selectable
3. ✅ Each subsidiary shows individual metrics
4. ✅ No "Network Error" or "No data available" messages
5. ✅ All changes deployed via Git + deploy.sh workflow

## Emergency Fallback

If Snowflake connection is completely broken and can't be fixed in time:

1. **Modify MCP analytics endpoints** to return hardcoded demo data
2. **Structure**: Match expected JSON format from Snowflake queries
3. **Values**: Use realistic numbers that sum to $309M for Silver Creek
4. **Deploy**: Same Git workflow

## Important Notes

- **Don't use `docker cp`** - everything through Git
- **Test locally first** - don't deploy broken code
- **MCP_API_KEY must be 32+ chars** and NOT start with "prod-mcp" (deploy.sh validation)
- **Silver Creek is special** - it's the aggregate view, subsidiaries are individual
- **Time is critical** - focus on getting data showing, perfect can come later

## Contact Info

- GCP VM: `root@dental-erp-vm` in zone `us-central1-a`
- App URL: https://dentalerp.agentprovision.com
- MCP URL: https://mcp.agentprovision.com (if configured)
- GitHub: nomad3/dentalERP

## Current Session Summary

We fixed:
- Login token size issue (refresh_tokens.token → TEXT)
- MCP tenant seeding (json.dumps instead of str())
- Silver Creek tenant + warehouse + integration in MCP

We still need:
- Analytics data flowing from Snowflake/MCP to frontend
- 14 subsidiary tenants created and seeded
- Proper deployment via deploy.sh with correct API keys

Good luck! The demo depends on this working. 🚀
