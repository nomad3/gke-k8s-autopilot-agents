# Production Critical Fixes Design

**Date:** 2025-11-09
**Status:** Validated
**Scope:** Fix verified production issues blocking end-to-end functionality

---

## Verified Issues (Evidence-Based)

### Issue 1: Missing Snowflake subsidiary_id Columns
**Evidence:** Multi-subsidiary sync logs show:
```
SQL compilation error: invalid identifier 'SUBSIDIARY_ID'
```
**Impact:** MERGE upsert fails, multi-subsidiary sync cannot write data

### Issue 2: Snowflake Gold Tables Don't Exist
**Evidence:** Financial API returns:
```
{"detail":"invalid identifier 'SUBSIDIARY_ID'"}
```
**Impact:** All analytics APIs fail, no KPIs, no insights

### Issue 3: Frontend CORS Errors
**Evidence:** Browser console shows:
```
Cross-Origin Request Blocked: CORS header 'Access-Control-Allow-Origin' missing
GET https://mcp.agentprovision.com/api/v1/tenants/ - Status: 500
```
**Impact:** Frontend cannot load tenant data, app breaks on startup

### Issue 4: MCP Tenant Endpoint Crashes
**Evidence:** MCP logs show:
```
AttributeError: '_AsyncGeneratorContextManager' object has no attribute 'execute'
File: tenant_service.py, line 46
```
**Impact:** Tenant API returns 500, frontend cannot initialize

### Issue 5: Multi-Subsidiary Sync Schema Mismatch
**Evidence:** Sync attempts fail with subsidiary filter but Bronze tables reject data
**Impact:** Cannot get data from all 24 practices

---

## Solution Design

### Part 1: Fix Snowflake Data Pipeline (Priority 1)

**Task 1.1: Add subsidiary_id Columns**
```sql
-- Execute on Snowflake
ALTER TABLE bronze.netsuite_journal_entries ADD COLUMN subsidiary_id VARCHAR(50);
ALTER TABLE bronze.netsuite_accounts ADD COLUMN subsidiary_id VARCHAR(50);
ALTER TABLE bronze.netsuite_vendor_bills ADD COLUMN subsidiary_id VARCHAR(50);
ALTER TABLE bronze.netsuite_customers ADD COLUMN subsidiary_id VARCHAR(50);
ALTER TABLE bronze.netsuite_vendors ADD COLUMN subsidiary_id VARCHAR(50);
ALTER TABLE bronze.netsuite_subsidiaries ADD COLUMN subsidiary_id VARCHAR(50);
ALTER TABLE bronze.netsuite_invoices ADD COLUMN subsidiary_id VARCHAR(50);
ALTER TABLE bronze.netsuite_payments ADD COLUMN subsidiary_id VARCHAR(50);
ALTER TABLE bronze.netsuite_items ADD COLUMN subsidiary_id VARCHAR(50);
```

**Task 1.2: Create Snowflake Dynamic Tables**
```sql
-- Execute snowflake-mvp-ai-setup.sql (764 lines)
-- Creates:
CREATE DYNAMIC TABLE silver.stg_financials...
CREATE DYNAMIC TABLE gold.fact_financials...
CREATE DYNAMIC TABLE gold.monthly_production_kpis...
CREATE DYNAMIC TABLE gold.production_anomalies...
CREATE TABLE gold.kpi_alerts...
CREATE TASK refresh_kpi_alerts...
```

**Task 1.3: Verify Tables Created**
```sql
SHOW DYNAMIC TABLES IN gold;
SHOW TASKS IN gold;

SELECT COUNT(*) FROM gold.monthly_production_kpis;
-- Should return rows (monthly KPIs by practice)
```

**Automation:** Use Python script on GCP VM to execute SQL:
```python
# On dental-erp-vm
docker exec mcp-server-prod python3 << EOF
import snowflake.connector
# Execute schema migration
# Execute Dynamic Tables SQL
# Verify creation
EOF
```

---

### Part 2: Fix Frontend CORS & API Issues (Priority 2)

**Task 2.1: Add CORS Origins**

File: `mcp-server/src/main.py`

```python
# Current:
allow_origins=["http://localhost:3000"],

# Fix to:
allow_origins=[
    "http://localhost:3000",
    "https://dentalerp.agentprovision.com",  # Production frontend
    "https://mcp.agentprovision.com"
],
```

**Task 2.2: Fix Tenant Service Database Context**

File: `mcp-server/src/services/tenant_service.py` line 46

```python
# Current (BROKEN):
result = await db.execute(query)

# Fix to:
async with db as session:
    result = await session.execute(query)
    return result.scalars().all()
```

**OR** (if get_db already returns session):
```python
# Just use db directly (verify get_db implementation)
result = await db.execute(query)
```

**Task 2.3: Verify CORS Fix**
```bash
# Test 1: Tenant API works
curl https://mcp.agentprovision.com/api/v1/tenants/ \
  -H "Authorization: Bearer $MCP_API_KEY"
# Expected: JSON array of tenants, no 500 error

# Test 2: Browser console shows no CORS errors
# Open https://dentalerp.agentprovision.com
# Check console: No "Cross-Origin Request Blocked" errors
```

---

### Part 3: Trigger Multi-Subsidiary Sync (Priority 3)

**After schema fixes, trigger full sync:**

```bash
curl -X POST https://mcp.agentprovision.com/api/v1/netsuite/sync/trigger \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: default" \
  -d '{"full_sync": true}'
```

**Expected:**
- Loops through all 24 subsidiaries
- MERGE upsert succeeds (schema has subsidiary_id)
- 6,263 records → 150,000+ records (24x coverage)

---

## Implementation Order

**Step 1:** Execute Snowflake schema migration (2 min)
**Step 2:** Execute Snowflake Dynamic Tables SQL (5 min)
**Step 3:** Fix CORS in main.py (1 min)
**Step 4:** Fix tenant_service.py database context (2 min)
**Step 5:** Deploy MCP server with fixes (3 min)
**Step 6:** Trigger multi-subsidiary sync (5 min)
**Step 7:** Verify end-to-end with curl (5 min)
**Step 8:** Open frontend and verify data displays (2 min)

**Total:** 25 minutes

---

## Success Criteria (Verification Commands)

### Must Pass All:

```bash
# 1. Snowflake schema has subsidiary_id
SELECT subsidiary_id FROM bronze.netsuite_accounts LIMIT 1;
# Expected: Returns a value (not error)

# 2. Gold tables exist
SELECT COUNT(*) FROM gold.monthly_production_kpis;
# Expected: Returns count > 0

# 3. Tenant API works
curl https://mcp.agentprovision.com/api/v1/tenants/ -H "Authorization: Bearer $KEY"
# Expected: HTTP 200, JSON array

# 4. Frontend loads without CORS errors
curl -I https://dentalerp.agentprovision.com
# Expected: HTTP 200

# 5. Browser console clean
# Open https://dentalerp.agentprovision.com
# Expected: No CORS errors, app loads

# 6. Financial API returns data
curl https://mcp.agentprovision.com/api/v1/analytics/financial/summary \
  -H "Authorization: Bearer $KEY" -H "X-Tenant-ID: default"
# Expected: JSON with practice financial data

# 7. Multi-subsidiary data visible
SELECT COUNT(DISTINCT subsidiary_id) FROM bronze.netsuite_journal_entries;
# Expected: > 1 (multiple subsidiaries)
```

---

**Design validated:** 2025-11-09
**Estimated time:** 25 minutes
**Approach:** Sequential fixes with verification after each step
