# Analytics Dashboard Fix - Completed 2025-11-22

## Problem Summary
Analytics dashboard was showing "Network Error" and 500 Internal Server Error when trying to load production data for Silver Creek tenant.

## Root Causes Identified

### 1. Tenant Warehouse Configuration Had PLACEHOLDER Credentials
**Location**: `mcp` PostgreSQL database, `tenant_warehouses` table
**Issue**: The table had `"account": "PLACEHOLDER", "user": "PLACEHOLDER"` instead of real Snowflake credentials
**Impact**: MCP server couldn't connect to Snowflake (error 250001)

### 2. Deploy Script Wasn't Exporting Snowflake Variables
**Location**: `deploy.sh` line 65
**Issue**: Script only exported `API_PORT WEB_PORT MCP_API_KEY MCP_SECRET_KEY` but not `SNOWFLAKE_*` variables
**Impact**: Docker containers didn't receive Snowflake credentials even when set in shell

### 3. .env File Had Escaped Password Characters
**Location**: `mcp-server/.env` on GCP VM
**Issue**: Password stored as `@SebaSofi.2k25\!\!` (with backslashes) instead of `@SebaSofi.2k25!!`
**Impact**: Snowflake connection attempts failed with authentication error

### 4. gold.practice_analytics_unified Dynamic Table Was Broken
**Location**: Snowflake `DENTAL_ERP_DW.gold.practice_analytics_unified`
**Issue**: Circular reference - VIEW reading FROM dynamic table, dynamic table reading FROM view
**Impact**: Dynamic table couldn't refresh, returned NULL values for all operations metrics

## Fixes Applied

### Fix 1: Update deploy.sh to Export Snowflake Variables
```bash
# Added after line 65 in deploy.sh:
if [ -n "${SNOWFLAKE_ACCOUNT:-}" ]; then
  export SNOWFLAKE_ACCOUNT SNOWFLAKE_USER SNOWFLAKE_PASSWORD
  export SNOWFLAKE_WAREHOUSE SNOWFLAKE_DATABASE SNOWFLAKE_SCHEMA SNOWFLAKE_ROLE
fi
```

**Status**: ✅ Committed to git (commit 99a00c9)

### Fix 2: Update tenant_warehouses Table
```sql
UPDATE tenant_warehouses
SET warehouse_config = jsonb_build_object(
  'account', 'HKTPGHW-ES87244',
  'user', 'NOMADSIMON',
  'password', '@SebaSofi.2k25!!',
  'warehouse', 'COMPUTE_WH',
  'database', 'DENTAL_ERP_DW',
  'schema', 'BRONZE',
  'role', 'ACCOUNTADMIN'
)
WHERE warehouse_type = 'snowflake';
```

**Status**: ✅ Applied directly to `mcp` database on production

### Fix 3: Fix .env File Password
```bash
# On GCP VM: /opt/dental-erp/mcp-server/.env
# Changed: SNOWFLAKE_PASSWORD=@SebaSofi.2k25\!\!
# To:      SNOWFLAKE_PASSWORD=@SebaSofi.2k25!!
```

**Status**: ✅ Updated via gcloud scp

### Fix 4: Recreate gold.practice_analytics_unified
```sql
CREATE OR REPLACE DYNAMIC TABLE gold.practice_analytics_unified
TARGET_LAG = '1 hour'
WAREHOUSE = COMPUTE_WH
AS
SELECT
    PRACTICE_LOCATION AS practice_id,
    PRACTICE_NAME AS practice_display_name,
    REPORT_MONTH AS report_month,
    TENANT_ID AS tenant_id,
    -- All operations metrics from operations_kpis_monthly
    TOTAL_PRODUCTION, NET_PRODUCTION, COLLECTIONS, etc.
    -- NetSuite columns as NULL for now
    CAST(NULL AS NUMBER(20,2)) AS netsuite_revenue,
    ...
FROM bronze_gold.operations_kpis_monthly;
```

**Status**: ✅ Executed in Snowflake

## Verification Results

### MCP Analytics Endpoints - ALL WORKING
```bash
# Production summary
curl "https://mcp.agentprovision.com/api/v1/analytics/production/summary" \
  -H "Authorization: Bearer d876..." \
  -H "X-Tenant-ID: silvercreek"

Response: {
  "PRACTICE_COUNT": 12,
  "TOTAL_PRODUCTION": "48674575.71",
  "TOTAL_VISITS": 54807
}

# Daily production
✅ Returns 339 records with daily metrics

# By practice
✅ Returns 12 practices with aggregated metrics
```

### Data Summary
- **Practices**: 12 (rd, ads, dsr, efd_i, ucfd, ipd, sed, efd_ii, lcd, lsd, eawd, dd)
- **Records**: 339 monthly aggregated records
- **Production**: $48.6M from operations_kpis_monthly
- **Date Range**: 2021-01-01 to 2025-07-01

## Architecture Flow (Post-Fix)

```
Snowflake:
  bronze_gold.operations_kpis_monthly (SOURCE: Excel Operations Report)
    ↓ (Dynamic Table with 1 hour lag)
  gold.practice_analytics_unified (MAIN ANALYTICS TABLE)
    ↓ (VIEW for backward compatibility)
  bronze_gold.daily_production_metrics (VIEW pointing to gold table)
    ↓
MCP Server:
  /api/v1/analytics/production/* endpoints
  /api/v1/analytics/unified/* endpoints
    ↓
Backend API:
  /api/analytics/* (proxies to MCP)
  /api/analytics-unified/* (proxies to MCP)
    ↓
Frontend:
  Analytics Dashboard Components
```

## Outstanding Issues

### 1. NetSuite Financial Data Not Joined
- `netsuite_revenue`, `netsuite_expenses` columns are NULL
- Need to add FULL OUTER JOIN with `silver.stg_financials`
- This will bring back the $309M total when combined with operations

### 2. Socket.IO Connection Failing
- Frontend shows: "Firefox can't establish a connection to wss://dentalerp.agentprovision.com/socket.io/"
- Not critical for analytics display, but affects real-time updates

### 3. Missing dental-icon.svg
- 404 error for /dental-icon.svg
- Cosmetic issue only

## Next Steps

1. Test frontend dashboard to confirm data loads
2. Add NetSuite financial data join if needed
3. Update CLAUDE.md with this troubleshooting process
4. Clean up documentation files in root directory

## Deployment Workflow for Future

**To deploy fixes to production:**

```bash
# 1. Make changes locally
git add [files]
git commit -m "fix: description"
git push origin main

# 2. On GCP VM - pull and deploy
gcloud compute ssh root@dental-erp-vm --zone=us-central1-a
cd /opt/dental-erp
git pull origin main

# 3. Export Snowflake credentials and deploy
export SNOWFLAKE_ACCOUNT='HKTPGHW-ES87244'
export SNOWFLAKE_USER='NOMADSIMON'
export SNOWFLAKE_PASSWORD='@SebaSofi.2k25!!'
export SNOWFLAKE_WAREHOUSE='COMPUTE_WH'
export SNOWFLAKE_DATABASE='DENTAL_ERP_DW'
export SNOWFLAKE_SCHEMA='BRONZE'
export SNOWFLAKE_ROLE='ACCOUNTADMIN'
export MCP_API_KEY='d876e6163089364d96a45a80ed576e99fc55b306133e258d9f861007e824b456'
export MCP_SECRET_KEY='production-secret-key-for-jwt-signing-min-32-characters-secure'

sudo -E bash deploy.sh
```

**For Snowflake-only fixes:**
- Connect directly to Snowflake and run SQL
- No deployment needed (changes take effect immediately)
- Update via Python script or SnowSQL

## Key Learnings

1. **Check database tables first** - The `tenant_warehouses` table had placeholder values that weren't obvious from logs
2. **Pydantic reads .env files** - Even when env vars are set, if .env file exists it takes precedence
3. **Dynamic Tables have lag dependencies** - Child table lag must be >= parent table lag
4. **Avoid circular references** - VIEWs and Dynamic Tables can't reference each other circularly

## Files Modified

- `/deploy.sh` - Added Snowflake env var exports
- `/opt/dental-erp/mcp-server/.env` - Fixed password escaping (on VM only, not in git)
- Snowflake: `gold.practice_analytics_unified` - Recreated as DYNAMIC TABLE

## Database Changes

**PostgreSQL `mcp` database:**
```sql
-- tenant_warehouses table updated with real Snowflake credentials
UPDATE tenant_warehouses SET warehouse_config = {...real credentials...}
```

**Snowflake `DENTAL_ERP_DW`:**
```sql
-- Recreated dynamic table
DROP DYNAMIC TABLE IF EXISTS gold.practice_analytics_unified;
CREATE DYNAMIC TABLE gold.practice_analytics_unified TARGET_LAG = '1 hour' ...
```

---

**Fixed by**: Claude Code
**Date**: 2025-11-22
**Time spent**: ~2 hours
**Status**: Analytics endpoints working, frontend needs verification
