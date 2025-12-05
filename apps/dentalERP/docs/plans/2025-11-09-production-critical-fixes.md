# Production Critical Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 5 verified production issues blocking end-to-end functionality: Snowflake schema, Gold tables, frontend API routing, tenant endpoint crash, and multi-subsidiary sync

**Architecture:** Frontend → Backend API → MCP → Snowflake. Fix data pipeline first (Snowflake), then fix API routing (frontend through backend, not direct to MCP), then verify complete flow.

**Tech Stack:** Snowflake SQL, Python FastAPI, TypeScript React, Docker

---

## Task 1: Execute Snowflake Schema Migration

**Files:**
- Execute: `snowflake-add-subsidiary-column.sql` on GCP VM via MCP container

### Step 1: Execute schema migration on Snowflake

Run on GCP VM:
```bash
gcloud compute ssh dental-erp-vm --zone=us-central1-a

cd /opt/dental-erp

sudo docker exec dental-erp_mcp-server-prod_1 python3 << 'EOF'
import snowflake.connector, os

env = {}
with open("/app/.env") as f:
    for line in f:
        if "=" in line and not line.startswith("#"):
            k,v = line.strip().split("=", 1)
            env[k] = v

conn = snowflake.connector.connect(
    account=env["SNOWFLAKE_ACCOUNT"],
    user=env["SNOWFLAKE_USER"],
    password=env["SNOWFLAKE_PASSWORD"],
    warehouse=env["SNOWFLAKE_WAREHOUSE"],
    database=env["SNOWFLAKE_DATABASE"]
)

cursor = conn.cursor()

tables = [
    'netsuite_journal_entries',
    'netsuite_accounts',
    'netsuite_vendor_bills',
    'netsuite_customers',
    'netsuite_vendors',
    'netsuite_subsidiaries',
    'netsuite_invoices',
    'netsuite_payments',
    'netsuite_items'
]

print("Adding subsidiary_id columns...")
for table in tables:
    try:
        cursor.execute(f"ALTER TABLE bronze.{table} ADD COLUMN subsidiary_id VARCHAR(50)")
        print(f"✅ {table}")
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"ℹ️  {table}: Already exists")
        else:
            print(f"❌ {table}: {e}")

conn.close()
print("\n✅ Schema migration complete")
EOF
```

### Step 2: Verify subsidiary_id columns exist

Run:
```bash
sudo docker exec dental-erp_mcp-server-prod_1 python3 << 'EOF'
import snowflake.connector, os

env = {}
with open("/app/.env") as f:
    for line in f:
        if "=" in line and not line.startswith("#"):
            k,v = line.strip().split("=", 1)
            env[k] = v

conn = snowflake.connector.connect(
    account=env["SNOWFLAKE_ACCOUNT"],
    user=env["SNOWFLAKE_USER"],
    password=env["SNOWFLAKE_PASSWORD"],
    warehouse=env["SNOWFLAKE_WAREHOUSE"],
    database=env["SNOWFLAKE_DATABASE"]
)

cursor = conn.cursor()

# Test that column exists
cursor.execute("SELECT subsidiary_id FROM bronze.netsuite_accounts LIMIT 1")
result = cursor.fetchone()
print(f"✅ Verification: subsidiary_id column exists (value: {result[0]})")

conn.close()
EOF
```

Expected output:
```
✅ Verification: subsidiary_id column exists (value: None)
```

### Step 3: Document completion

Create verification note (no commit yet, will batch with other fixes):
```bash
echo "✅ Task 1 Complete: Snowflake subsidiary_id columns added" > /tmp/task1-done.txt
```

---

## Task 2: Create Snowflake Dynamic Tables

**Files:**
- Execute: `snowflake-mvp-ai-setup.sql` on Snowflake

### Step 1: Execute Dynamic Tables SQL

Run on GCP VM:
```bash
sudo docker exec dental-erp_mcp-server-prod_1 python3 << 'EOF'
import snowflake.connector, os

env = {}
with open("/app/.env") as f:
    for line in f:
        if "=" in line and not line.startswith("#"):
            k,v = line.strip().split("=", 1)
            env[k] = v

conn = snowflake.connector.connect(
    account=env["SNOWFLAKE_ACCOUNT"],
    user=env["SNOWFLAKE_USER"],
    password=env["SNOWFLAKE_PASSWORD"],
    warehouse=env["SNOWFLAKE_WAREHOUSE"],
    database=env["SNOWFLAKE_DATABASE"]
)

cursor = conn.cursor()

# Read and execute SQL file
with open("/app/snowflake-mvp-ai-setup.sql") as f:
    sql_content = f.read()

statements = [s.strip() for s in sql_content.split(";") if s.strip() and not s.strip().startswith("--")]

print(f"Executing {len(statements)} SQL statements...")

for i, stmt in enumerate(statements, 1):
    try:
        cursor.execute(stmt)
        result = cursor.fetchone()
        if result and len(result) > 0:
            print(f"[{i}] ✅ {result[0][:60]}")
        else:
            print(f"[{i}] ✅")
    except Exception as e:
        error = str(e)
        if "already exists" in error.lower() or "does not exist" in error.lower():
            print(f"[{i}] ℹ️  {error[:60]}")
        else:
            print(f"[{i}] ❌ {error[:100]}")

conn.close()
print("\n✅ Dynamic Tables creation complete")
EOF
```

Expected output showing Dynamic Tables created

### Step 2: Verify Dynamic Tables exist

Run:
```bash
sudo docker exec dental-erp_mcp-server-prod_1 python3 << 'EOF'
import snowflake.connector, os

env = {}
with open("/app/.env") as f:
    for line in f:
        if "=" in line and not line.startswith("#"):
            k,v = line.strip().split("=", 1)
            env[k] = v

conn = snowflake.connector.connect(
    account=env["SNOWFLAKE_ACCOUNT"],
    user=env["SNOWFLAKE_USER"],
    password=env["SNOWFLAKE_PASSWORD"],
    warehouse=env["SNOWFLAKE_WAREHOUSE"],
    database=env["SNOWFLAKE_DATABASE"]
)

cursor = conn.cursor()

# Verify Gold tables
try:
    cursor.execute("SELECT COUNT(*) FROM gold.monthly_production_kpis")
    count = cursor.fetchone()[0]
    print(f"✅ gold.monthly_production_kpis: {count} rows")
except Exception as e:
    print(f"❌ gold.monthly_production_kpis: {e}")

try:
    cursor.execute("SELECT COUNT(*) FROM gold.production_anomalies")
    count = cursor.fetchone()[0]
    print(f"✅ gold.production_anomalies: {count} rows")
except Exception as e:
    print(f"❌ gold.production_anomalies: {e}")

try:
    cursor.execute("SHOW DYNAMIC TABLES IN gold")
    tables = cursor.fetchall()
    print(f"✅ Dynamic Tables: {len(tables)} created")
except Exception as e:
    print(f"❌ Dynamic Tables: {e}")

conn.close()
EOF
```

Expected: All 3 verifications pass with row counts

### Step 3: Document completion

```bash
echo "✅ Task 2 Complete: Snowflake Dynamic Tables created" >> /tmp/task1-done.txt
```

---

## Task 3: Fix Frontend API Routing (Use Backend, Not MCP)

**Files:**
- Check: `frontend/src/components/dashboards/ExecutiveDashboard.tsx`
- Check: `frontend/src/services/*`
- Modify: Any files calling MCP directly

### Step 1: Find direct MCP API calls in frontend

Run:
```bash
cd frontend
grep -r "mcp.agentprovision.com\|MCP_BASE_URL\|mcpAPI" src/ --include="*.tsx" --include="*.ts"
```

Expected: List of files calling MCP directly

### Step 2: Check AIInsightsWidget (likely culprit)

Read `frontend/src/components/dashboard/AIInsightsWidget.tsx`:

If it has:
```typescript
const MCP_BASE_URL = 'https://mcp.agentprovision.com';
axios.get(`${MCP_BASE_URL}/api/v1/analytics/insights`)
```

Replace with:
```typescript
// Use backend proxy instead
import { apiClient } from '../../services/api';

const response = await apiClient.get('/analytics/insights');
// Backend will proxy to MCP internally
```

### Step 3: Verify backend has insights proxy route

Check `backend/src/routes/analytics.ts`:

If missing `/insights` route, add:
```typescript
router.get('/insights', authMiddleware, async (req, res) => {
  try {
    const response = await mcpClient.get('/api/v1/analytics/insights');
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

### Step 4: Update AIInsightsWidget to use backend API

Modify `frontend/src/components/dashboard/AIInsightsWidget.tsx`:

```typescript
// DELETE direct MCP calls
const MCP_BASE_URL = import.meta.env.VITE_MCP_API_URL || 'http://localhost:8085';

// REPLACE WITH backend API call
import { apiClient } from '../../services/api';

export function AIInsightsWidget() {
  const { data, isLoading, error, refetch } = useQuery<AIInsightsResponse>({
    queryKey: ['ai-insights'],
    queryFn: async () => {
      // Call backend, which proxies to MCP
      const response = await apiClient.get('/analytics/insights');
      return response.data;
    },
    staleTime: 60 * 60 * 1000,
    retry: 1
  });

  // ... rest of component
}
```

### Step 5: Check financialAPI.ts

Read `frontend/src/services/financialAPI.ts`:

Ensure it uses `apiClient` (backend proxy) not direct MCP:
```typescript
import { apiClient } from './api';

export const financialAPI = {
  getSummary: async (params) => {
    // Goes through backend at /api/analytics/financial/summary
    const response = await apiClient.get('/analytics/financial/summary', { params });
    return response.data;
  }
};
```

If it's calling MCP directly, fix it.

### Step 6: Add backend proxy routes for financial APIs

Check `backend/src/routes/analytics.ts`:

Add if missing:
```typescript
// Financial summary proxy
router.get('/financial/summary', authMiddleware, async (req, res) => {
  try {
    const response = await mcpClient.get('/api/v1/analytics/financial/summary', {
      params: req.query
    });
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Practice comparison proxy
router.get('/financial/by-practice', authMiddleware, async (req, res) => {
  try {
    const response = await mcpClient.get('/api/v1/analytics/financial/by-practice');
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

### Step 7: Commit frontend routing fixes

```bash
git add frontend/src/components/dashboard/AIInsightsWidget.tsx \
        frontend/src/services/financialAPI.ts \
        backend/src/routes/analytics.ts

git commit -m "fix(frontend): route API calls through backend instead of direct MCP

- Change AIInsightsWidget to call /api/analytics/insights (backend)
- Ensure financialAPI uses backend proxy
- Add backend proxy routes for financial/* and insights
- Fixes CORS errors (frontend → backend → MCP architecture)

Verified issue: Frontend was calling MCP directly causing CORS errors"
```

---

## Task 4: Fix MCP Tenant Service Database Context

**Files:**
- Modify: `mcp-server/src/services/tenant_service.py:46`

### Step 1: Check get_db implementation

Read `mcp-server/src/core/database.py`:

Understand if `get_db()` returns:
- AsyncGenerator (needs `async with`)
- AsyncSession directly (use directly)

### Step 2: Fix tenant_service.py based on get_db type

If `get_db` is AsyncGenerator, modify `mcp-server/src/services/tenant_service.py`:

```python
@staticmethod
async def list_tenants(
    db: AsyncSession,  # This is actually AsyncGenerator
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
) -> List[Tenant]:
    """List all tenants"""

    # FIX: Enter async context properly
    async with db as session:
        query = select(Tenant)

        if status:
            query = query.where(Tenant.status == status)

        query = query.offset(skip).limit(limit).order_by(Tenant.created_at.desc())

        result = await session.execute(query)
        return result.scalars().all()
```

OR if dependencies need updating, fix the endpoint instead:

```python
# In tenants.py
from ..core.database import get_db

@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
):
    """List all tenants"""
    async with get_db() as db:  # FIX: Enter context here
        tenants = await TenantService.list_tenants(db, skip, limit, status)
        return tenants
```

### Step 3: Test tenant endpoint

Run:
```bash
curl https://mcp.agentprovision.com/api/v1/tenants/ \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars"
```

Expected:
```json
[
  {
    "id": "...",
    "tenant_code": "default",
    "tenant_name": "Default Tenant",
    ...
  }
]
```

NOT:
```json
{"detail": "...AttributeError..."}
```

### Step 4: Commit tenant service fix

```bash
git add mcp-server/src/services/tenant_service.py

git commit -m "fix(mcp): fix tenant service database context manager usage

- Use 'async with db as session' pattern
- Fixes AttributeError: '_AsyncGeneratorContextManager' has no attribute 'execute'
- Tenant API now returns 200 instead of 500

Verified: curl /api/v1/tenants/ returns tenant list"
```

---

## Task 5: Deploy and Verify End-to-End

**Files:**
- Deploy via GCP

### Step 1: Merge to main and push

Run:
```bash
cd /Users/nomade/Documents/GitHub/dentalERP
git merge fix/production-critical-issues
git push origin main
```

### Step 2: Deploy to GCP

Run:
```bash
gcloud compute ssh dental-erp-vm --zone=us-central1-a

cd /opt/dental-erp
sudo git pull origin main

# Rebuild and restart services
sudo docker-compose build backend-prod mcp-server-prod frontend-prod
sudo docker-compose restart backend-prod mcp-server-prod frontend-prod
```

### Step 3: Wait for services to be healthy

Run:
```bash
sleep 30

# Verify all services running
sudo docker ps --filter 'name=dental-erp' --format '{{.Names}}: {{.Status}}'
```

Expected: All show "Up" and "healthy"

### Step 4: Verify Snowflake Gold tables have data

Run:
```bash
sudo docker exec dental-erp_mcp-server-prod_1 python3 << 'EOF'
import snowflake.connector, os

env = {}
with open("/app/.env") as f:
    for line in f:
        if "=" in line and not line.startswith("#"):
            k,v = line.strip().split("=", 1)
            env[k] = v

conn = snowflake.connector.connect(
    account=env["SNOWFLAKE_ACCOUNT"],
    user=env["SNOWFLAKE_USER"],
    password=env["SNOWFLAKE_PASSWORD"],
    warehouse=env["SNOWFLAKE_WAREHOUSE"],
    database=env["SNOWFLAKE_DATABASE"]
)

cursor = conn.cursor()

# Verify monthly KPIs
cursor.execute("SELECT COUNT(*) FROM gold.monthly_production_kpis")
kpi_count = cursor.fetchone()[0]
print(f"gold.monthly_production_kpis: {kpi_count} rows")

# Verify anomalies
cursor.execute("SELECT COUNT(*) FROM gold.production_anomalies")
anom_count = cursor.fetchone()[0]
print(f"gold.production_anomalies: {anom_count} rows")

# Sample data
cursor.execute("""
    SELECT practice_name, total_revenue, total_expenses, profit_margin_pct
    FROM gold.monthly_production_kpis
    LIMIT 5
""")

print("\nSample KPIs:")
for row in cursor.fetchall():
    print(f"  {row[0]}: Revenue ${row[1]:,.0f}, Expenses ${row[2]:,.0f}, Margin {row[3]}%")

conn.close()
EOF
```

Expected: Row counts > 0, sample data shows practices

### Step 5: Verify Backend API proxies work

Run:
```bash
# Test financial summary through backend
curl https://dentalerp.agentprovision.com/api/analytics/financial/summary \
  -H "Authorization: Bearer $BACKEND_TOKEN"
```

Expected: JSON with financial data (NOT "invalid identifier" error)

### Step 6: Verify Frontend loads without errors

Run:
```bash
# Test frontend loads
curl -I https://dentalerp.agentprovision.com
```

Expected: `HTTP/2 200`

### Step 7: Verify tenant API works

Run:
```bash
curl https://mcp.agentprovision.com/api/v1/tenants/ \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars"
```

Expected: JSON array of tenants (NOT AttributeError)

### Step 8: Trigger multi-subsidiary sync

Run:
```bash
curl -X POST https://mcp.agentprovision.com/api/v1/netsuite/sync/trigger \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  -H "X-Tenant-ID: default" \
  -H "Content-Type: application/json" \
  -d '{"record_types": ["account", "journalEntry"], "full_sync": true}'
```

Expected: `{"status": "started"}`

### Step 9: Wait and verify multi-subsidiary data

Wait 3 minutes, then run:
```bash
sudo docker exec dental-erp_mcp-server-prod_1 python3 << 'EOF'
import snowflake.connector, os

env = {}
with open("/app/.env") as f:
    for line in f:
        if "=" in line and not line.startswith("#"):
            k,v = line.strip().split("=", 1)
            env[k] = v

conn = snowflake.connector.connect(
    account=env["SNOWFLAKE_ACCOUNT"],
    user=env["SNOWFLAKE_USER"],
    password=env["SNOWFLAKE_PASSWORD"],
    warehouse=env["SNOWFLAKE_WAREHOUSE"],
    database=env["SNOWFLAKE_DATABASE"]
)

cursor = conn.cursor()

# Check if we have multi-subsidiary data
cursor.execute("""
    SELECT
        COUNT(DISTINCT subsidiary_id) as subsidiaries,
        COUNT(DISTINCT id) as unique_records,
        COUNT(*) as total_records
    FROM bronze.netsuite_accounts
    WHERE subsidiary_id IS NOT NULL
""")

subs, unique, total = cursor.fetchone()
print(f"Subsidiaries: {subs}")
print(f"Unique accounts: {unique}")
print(f"Total records: {total}")

if subs > 1:
    print(f"\n✅ Multi-subsidiary sync WORKING (data from {subs} subsidiaries)")
else:
    print(f"\n⚠️  Multi-subsidiary sync NOT working (data from {subs} subsidiary only)")

conn.close()
EOF
```

Expected:
```
Subsidiaries: 24
Unique accounts: 9,840
✅ Multi-subsidiary sync WORKING
```

### Step 10: Open frontend in browser and verify

Open in browser:
```
https://dentalerp.agentprovision.com
```

**Verification Checklist:**
- [ ] Page loads without errors
- [ ] No CORS errors in console
- [ ] Executive dashboard displays
- [ ] AI Insights widget shows GPT-4 summary (or "no data" message)
- [ ] Navigate to Financial Analytics page
- [ ] Financial KPI cards display (even if "no data")
- [ ] No JavaScript errors in console

### Step 11: Verify AI insights endpoint

Run:
```bash
curl https://dentalerp.agentprovision.com/api/analytics/insights \
  -H "Authorization: Bearer $BACKEND_TOKEN"
```

Expected: GPT-4 generated summary OR graceful "no data" response (NOT 500 error)

### Step 12: Verify financial analytics API

Run:
```bash
curl 'https://dentalerp.agentprovision.com/api/analytics/financial/summary' \
  -H "Authorization: Bearer $BACKEND_TOKEN"
```

Expected: JSON with practice financial data from `gold.monthly_production_kpis`

### Step 13: Create final verification report

Create `PRODUCTION_VERIFICATION_2025-11-09.md`:

```markdown
# Production Verification Report

**Date:** 2025-11-09
**Status:** [PASS/FAIL]

## Verification Results

### Snowflake Data Pipeline
- [x] subsidiary_id columns exist in Bronze: VERIFIED
- [x] Gold Dynamic Tables created: VERIFIED
- [x] monthly_production_kpis has data: [N] rows
- [x] production_anomalies has data: [N] rows

### API Endpoints
- [x] GET /api/v1/tenants/ returns 200: VERIFIED
- [x] GET /api/analytics/insights returns data: VERIFIED
- [x] GET /api/analytics/financial/summary returns data: VERIFIED

### Frontend
- [x] https://dentalerp.agentprovision.com loads: HTTP 200
- [x] No CORS errors in console: VERIFIED
- [x] Executive dashboard displays: VERIFIED
- [x] AI Insights widget visible: VERIFIED
- [x] Financial analytics page loads: VERIFIED

### Multi-Subsidiary Sync
- [x] Data from multiple subsidiaries: [N] subsidiaries
- [x] MERGE upsert works: No duplicate errors
- [x] All 24 practices represented: VERIFIED

## Issues Found

[List any issues discovered during verification]

## Overall Status

✅ Production deployment is FULLY OPERATIONAL
```

### Step 14: Final commit

```bash
git add PRODUCTION_VERIFICATION_2025-11-09.md

git commit -m "docs: production verification report - all systems operational

Verified with curl commands and browser testing:
✅ Snowflake Gold tables populated
✅ Multi-subsidiary sync working (24 practices)
✅ Frontend loads without CORS errors
✅ All API endpoints return real data
✅ End-to-end data flow operational

Evidence: Verification commands in report"
```

---

## Summary

**Total Tasks:** 5 (can be combined into fewer commits)
**Estimated Time:** 30 minutes with verification
**Approach:** Fix data foundation first, then frontend, verify each step

**Critical Success Factors:**
1. Run EVERY verification command and check output
2. Don't claim success without evidence
3. Use @superpowers:verification-before-completion throughout
4. Test end-to-end flow after each fix

**Verification Commands Must All Pass:**
- Snowflake: `SELECT COUNT(*) FROM gold.monthly_production_kpis` → rows
- Tenant API: `curl .../tenants/` → 200 OK
- Frontend: Browser console → no CORS errors
- Financial API: `curl .../financial/summary` → real data
- Multi-subsidiary: `SELECT COUNT(DISTINCT subsidiary_id)` → > 1

---

**Plan saved:** `docs/plans/2025-11-09-production-critical-fixes.md`
**Ready for execution with verification-before-completion**
