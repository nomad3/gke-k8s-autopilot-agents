# Deployment Checklist - NetSuite to Snowflake Data Flow
## Silver Creek Dental Partners

**Date**: November 10, 2025
**Deployment Target**: GCP VM (dental-erp-vm)
**Status**: ✅ Code Ready - Awaiting Manual Execution

---

## ✅ Completed (Pre-Deployment)

- [x] Backend schema updated (tenant_id, external_system_id fields)
- [x] Drizzle migration created (0007_add_tenant_external_system_mapping.sql)
- [x] NetSuite connector fixed (table naming, VARIANT columns)
- [x] Snowflake dynamic tables created (Bronze → Silver → Gold)
- [x] dbt project removed (replaced with native Snowflake)
- [x] Seed scripts created (Backend + MCP + Snowflake)
- [x] Documentation written (COMPLETE_DATA_FLOW_DOCUMENTATION.md)
- [x] All changes committed and pushed to GitHub

---

## 🚀 Deployment Steps (Manual Execution Required)

### Step 1: Deploy Code to GCP VM

```bash
# Run from local machine
cd /Users/nomade/Documents/GitHub/dentalERP
./deploy.sh

# This will:
# - SSH into GCP VM
# - Pull latest code from GitHub
# - Rebuild and restart Docker containers
```

### Step 2: Run Database Migrations

```bash
# SSH into GCP VM
gcloud compute ssh dental-erp-vm --project=aremko-e51ae

# Once inside VM:
cd /opt/dentalERP

# Apply backend migration
docker-compose exec backend npm run db:migrate

# Verify migration applied
docker-compose exec backend npm run db:status
```

### Step 3: Seed Backend Database

```bash
# Still on GCP VM:
docker-compose exec backend node scripts/backend-seed-silvercreek.ts

# This creates:
# - Silver Creek practice with tenant_id="silvercreek"
# - 9 subsidiary locations with external_system_id mapping
# - 3 users (Brad CFO, Barbara Manager, Lindsey Accountant)

# Verify seed
docker-compose exec backend psql $DATABASE_URL -c "SELECT name, tenant_id FROM practices;"
docker-compose exec backend psql $DATABASE_URL -c "SELECT name, subsidiary_name, external_system_id FROM locations;"
```

### Step 4: Seed MCP Database

```bash
# Still on GCP VM:
docker-compose exec mcp-server python scripts/mcp-seed-silvercreek.py

# This creates:
# - Tenant: silvercreek
# - Snowflake warehouse configuration
# - NetSuite integration configuration

# Verify seed
docker-compose exec mcp-server psql $MCP_DATABASE_URL -c "SELECT tenant_code, tenant_name FROM tenants;"
docker-compose exec mcp-server psql $MCP_DATABASE_URL -c "SELECT warehouse_type, is_primary FROM tenant_warehouses WHERE tenant_id=(SELECT id FROM tenants WHERE tenant_code='silvercreek');"
```

### Step 5: Setup Snowflake Tables

**⚠️ Run in Snowflake UI (https://app.snowflake.com)**

```sql
-- 1. Connect to Snowflake and select database
USE DATABASE DENTAL_ERP_DW;
USE WAREHOUSE COMPUTE_WH;
USE ROLE ACCOUNTADMIN;

-- 2. Create Bronze tables (run script from /tmp)
-- Copy contents of: /tmp/dentalerp-implementation/snowflake-bronze-schema-update.sql
-- Execute in Snowflake worksheet

-- 3. Create Silver dynamic tables
-- Copy contents of: /tmp/dentalerp-implementation/snowflake-dynamic-tables-silver.sql
-- Execute in Snowflake worksheet

-- 4. Create Gold dynamic tables
-- Copy contents of: /tmp/dentalerp-implementation/snowflake-dynamic-tables-gold.sql
-- Execute in Snowflake worksheet

-- 5. Verify tables created
SHOW TABLES IN bronze LIKE 'netsuite_%';
SHOW DYNAMIC TABLES IN silver;
SHOW DYNAMIC TABLES IN gold;
```

### Step 6: Trigger NetSuite Data Sync

```bash
# From local machine or GCP VM:
curl -X POST https://mcp.agentprovision.com/api/v1/netsuite/sync/trigger \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: silvercreek" \
  -H "Content-Type: application/json" \
  -d '{
    "full_sync": true,
    "record_types": [
      "journalEntry",
      "account",
      "invoice",
      "customerPayment",
      "vendorBill",
      "customer",
      "vendor",
      "inventoryItem",
      "subsidiary"
    ]
  }'

# Expected response:
# {"sync_id": "...", "status": "started", "record_types": [...]}
```

### Step 7: Monitor Sync Progress

```bash
# Check sync status (run every 30 seconds)
curl https://mcp.agentprovision.com/api/v1/netsuite/sync/status \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: silvercreek"

# Expected response when complete:
# {
#   "journalEntry": {"status": "success", "records_synced": 686},
#   "account": {"status": "success", "records_synced": 57},
#   "subsidiary": {"status": "success", "records_synced": 9},
#   ...
# }
```

### Step 8: Verify Data Flow

```sql
-- Run in Snowflake UI

-- 1. Check Bronze layer has data
SELECT
  'bronze.netsuite_journalentry' AS table_name,
  COUNT(*) AS record_count,
  COUNT(DISTINCT subsidiary_id) AS subsidiary_count
FROM bronze.netsuite_journalentry
WHERE tenant_id = 'silvercreek'
UNION ALL
SELECT
  'bronze.netsuite_account',
  COUNT(*),
  COUNT(DISTINCT subsidiary_id)
FROM bronze.netsuite_account
WHERE tenant_id = 'silvercreek';

-- 2. Check Silver layer (should auto-refresh after Bronze)
-- Wait 15 minutes for dynamic tables to refresh
SELECT COUNT(*) AS journal_entry_lines
FROM silver.fact_journal_entries
WHERE tenant_id = 'silvercreek';

-- 3. Check Gold layer (should auto-refresh after Silver)
-- Wait 30 minutes for dynamic tables to refresh
SELECT
  subsidiary_id,
  subsidiary_name,
  transaction_date,
  total_revenue,
  total_expenses,
  net_income
FROM gold.daily_financial_summary
WHERE tenant_id = 'silvercreek'
ORDER BY transaction_date DESC
LIMIT 10;
```

### Step 9: Test Frontend Dashboard

```bash
# 1. Open frontend in browser
open https://dentalerp.agentprovision.com

# 2. Login with Silver Creek CFO account
# Email: bstarkweather@silvercreekhealthcare.com
# Password: dentalerp2025

# 3. Navigate to Financial Analytics
# - Should see multi-location financial summary
# - Should see data for all 9 subsidiaries
# - Should see revenue, expenses, net income metrics
```

---

## 🔍 Verification Checklist

### Backend Verification

```bash
# Check practice-tenant mapping
docker-compose exec backend psql $DATABASE_URL -c "
  SELECT
    p.name AS practice_name,
    p.tenant_id,
    COUNT(l.id) AS location_count
  FROM practices p
  LEFT JOIN locations l ON p.id = l.practice_id
  WHERE p.tenant_id = 'silvercreek'
  GROUP BY p.id, p.name, p.tenant_id;
"

# Expected: 1 practice with 9 locations
```

### MCP Verification

```bash
# Check tenant configuration
docker-compose exec mcp-server python -c "
from src.services.tenant_service import get_tenant_by_code
import asyncio
tenant = asyncio.run(get_tenant_by_code('silvercreek'))
print(f'Tenant: {tenant.tenant_name}')
print(f'Products: {tenant.products}')
print(f'Warehouses: {len(tenant.warehouses)}')
print(f'Integrations: {len(tenant.integrations)}')
"

# Expected: Tenant with 1 warehouse and 1 integration
```

### Snowflake Verification

```sql
-- Check data quality
SELECT
  'Bronze' AS layer,
  COUNT(*) AS total_records,
  COUNT(DISTINCT subsidiary_id) AS subsidiaries,
  MIN(extracted_at) AS first_sync,
  MAX(extracted_at) AS last_sync
FROM bronze.netsuite_journalentry
WHERE tenant_id = 'silvercreek'
UNION ALL
SELECT
  'Silver',
  COUNT(*),
  COUNT(DISTINCT subsidiary_id),
  MIN(extracted_at),
  MAX(extracted_at)
FROM silver.fact_journal_entries
WHERE tenant_id = 'silvercreek'
UNION ALL
SELECT
  'Gold',
  COUNT(*),
  COUNT(DISTINCT subsidiary_id),
  MIN(_calculated_at),
  MAX(_calculated_at)
FROM gold.daily_financial_summary
WHERE tenant_id = 'silvercreek';

-- Expected: Data in all 3 layers for 9 subsidiaries
```

### API Verification

```bash
# Test analytics API
curl -X GET 'https://mcp.agentprovision.com/api/v1/analytics/financial/daily?tenant_id=silvercreek&subsidiary_id=6' \
  -H "Authorization: Bearer $MCP_API_KEY"

# Expected: JSON with daily financial metrics for SCDP Eastlake
```

---

## 🐛 Troubleshooting

### NetSuite Sync Fails

```bash
# Check MCP logs
docker-compose logs -f mcp-server | grep NetSuite

# Common issues:
# - Invalid OAuth credentials → Check tenant_integrations table
# - User Event Scripts blocking → Loader uses SuiteQL to bypass
# - Rate limiting → Sync has built-in delays (0.5s between requests)
```

### Dynamic Tables Not Refreshing

```sql
-- Check dynamic table status
SELECT
  name,
  target_lag,
  refresh_mode,
  scheduling_state,
  last_refresh_start_time,
  last_refresh_finish_time,
  data_timestamp
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
  'silver.fact_journal_entries'
))
ORDER BY last_refresh_start_time DESC
LIMIT 5;

-- Force manual refresh if needed
ALTER DYNAMIC TABLE silver.fact_journal_entries REFRESH;
```

### Frontend Shows No Data

```bash
# 1. Check backend logs
docker-compose logs -f backend | grep analytics

# 2. Check MCP connectivity from backend
docker-compose exec backend curl http://mcp-server:8085/health

# 3. Check Snowflake connectivity from MCP
docker-compose exec mcp-server python -c "
from src.connectors.snowflake import SnowflakeConnector
import asyncio
conn = SnowflakeConnector(...)
print('Connected!' if asyncio.run(conn.test_connection()) else 'Failed')
"
```

---

## 📊 Expected Results

After successful deployment:

1. **Backend Database**:
   - 1 practice (Silver Creek Dental Partners)
   - 9 locations (SCDP subsidiaries)
   - 3 users (Brad, Barbara, Lindsey)

2. **MCP Database**:
   - 1 tenant (silvercreek)
   - 1 warehouse (Snowflake)
   - 1 integration (NetSuite)

3. **Snowflake Bronze**:
   - ~686 journal entries
   - ~57 accounts
   - 9 subsidiaries
   - Customers, vendors, invoices, bills

4. **Snowflake Silver**:
   - fact_journal_entries with line items
   - dim_accounts, dim_subsidiaries, dim_customers, dim_vendors

5. **Snowflake Gold**:
   - daily_financial_summary (686 rows, 1 per transaction date)
   - monthly_financial_kpis (aggregated by month)
   - AR/AP aging, expense analysis, top customers/vendors

6. **Frontend Dashboard**:
   - Login works with Brad's credentials
   - Financial analytics show multi-location data
   - Charts display revenue/expense trends
   - All 9 locations selectable in filters

---

## 🎯 Success Criteria

- [  ] All database migrations applied without errors
- [  ] Backend seed creates practice + 9 locations
- [  ] MCP seed creates tenant + warehouse + integration
- [  ] Snowflake Bronze tables created (9 tables)
- [  ] Snowflake Silver dynamic tables created (7 tables)
- [  ] Snowflake Gold dynamic tables created (7 tables)
- [  ] NetSuite sync completes for all 9 record types
- [  ] Bronze layer populated with real NetSuite data
- [  ] Silver layer auto-refreshes from Bronze (within 15 min)
- [  ] Gold layer auto-refreshes from Silver (within 30 min)
- [  ] Backend API returns financial data filtered by practice
- [  ] Frontend dashboard displays multi-location summary
- [  ] Data integrity verified (Bronze count = Silver count)

---

## 📞 Support

**Next Session Tasks**:
1. Add API endpoints for remaining Gold tables (AR aging, expense analysis)
2. Build frontend components to visualize new KPIs
3. Add OpenAI enrichment for AI-generated insights
4. Monitor Snowflake query performance and optimize

**Documentation**:
- See `docs/COMPLETE_DATA_FLOW_DOCUMENTATION.md` for architecture details
- See `docs/NETSUITE_INTEGRATION_FINAL.md` for NetSuite setup
- See `documentation/DEPLOYMENT_GCP_VM.md` for GCP deployment guide

---

**Last Updated**: November 10, 2025
**Status**: ✅ Ready for Deployment
