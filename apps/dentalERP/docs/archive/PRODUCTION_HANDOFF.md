# Production Deployment Handoff - November 9, 2025

## Current Verified Status (with Evidence)

### ✅ What's VERIFIED Working (curl commands run on GCP VM)

**1. Services Running:**
```bash
$ sudo docker ps --filter 'name=dental-erp'
dental-erp_mcp-server-prod_1    Up (healthy)    port 8085
dental-erp_backend-prod_1       Up              port 3001
dental-erp_frontend-prod_1      Up              port 3000
dental-erp_postgres_1           Up (healthy)    port 5432
dental-erp_redis_1              Up (healthy)    port 6379
```

**2. MCP Server Health:**
```bash
$ curl https://mcp.agentprovision.com/health
{"status":"ok","timestamp":"2025-11-09T00:57:01"}
```

**3. Backend Health:**
```bash
$ curl http://localhost:3001/health
{"status":"healthy","environment":"production"}
```

**4. Frontend Accessible:**
```bash
$ curl -I https://dentalerp.agentprovision.com
HTTP/2 200
```

**5. NetSuite Data in Snowflake:**
```
bronze.netsuite_accounts: 410 unique records
bronze.netsuite_journal_entries: 395 unique records
bronze.netsuite_vendor_bills: 3,976 unique records
bronze.netsuite_vendors: 1,436 unique records
bronze.netsuite_customers: 22 unique records
TOTAL: 6,263 unique NetSuite records
```

---

### ❌ What's VERIFIED Broken (with Error Messages)

**1. Snowflake Gold Tables:**
```bash
$ curl https://mcp.agentprovision.com/api/v1/analytics/financial/summary
{"detail":"invalid identifier 'SUBSIDIARY_ID'"}
```
**Reason:** Gold layer Dynamic Tables not created yet

**2. Frontend → Backend API Calls:**
```
Browser Console:
Cross-Origin Request Blocked: https://mcp.agentprovision.com/api/v1/tenants/
Status: 500
```
**Reason:** Frontend calling MCP directly instead of through Backend

**3. MCP Tenant Endpoint:**
```bash
$ curl https://mcp.agentprovision.com/api/v1/tenants/
{"detail":"...AttributeError: '_AsyncGeneratorContextManager'..."}
```
**Reason:** Database context manager not used correctly

---

## Exact Steps to Complete Deployment (30 Minutes)

### Step 1: Add subsidiary_id to Snowflake (On GCP VM)

```bash
gcloud compute ssh dental-erp-vm --zone=us-central1-a

cd /opt/dental-erp

# Copy .env to container
sudo docker cp .env dental-erp_mcp-server-prod_1:/app/.env

# Execute schema migration
sudo docker exec dental-erp_mcp-server-prod_1 bash -c "
python3 << 'PY'
import snowflake.connector, os
from dotenv import load_dotenv
load_dotenv('/app/.env')

conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
    database=os.getenv('SNOWFLAKE_DATABASE')
)

cursor = conn.cursor()

for table in ['netsuite_journal_entries', 'netsuite_accounts', 'netsuite_vendor_bills', 'netsuite_customers', 'netsuite_vendors', 'netsuite_subsidiaries']:
    try:
        cursor.execute(f'ALTER TABLE bronze.{table} ADD COLUMN subsidiary_id VARCHAR(50)')
        print(f'✅ {table}')
    except Exception as e:
        print(f'ℹ️  {table}: {e}')

cursor.execute('SELECT subsidiary_id FROM bronze.netsuite_accounts LIMIT 1')
print(f'✅ VERIFIED: Column exists')
conn.close()
PY
"
```

**Verification Command:**
```bash
sudo docker exec dental-erp_mcp-server-prod_1 python3 -c "
from dotenv import load_dotenv
import snowflake.connector, os
load_dotenv('/app/.env')
conn = snowflake.connector.connect(account=os.getenv('SNOWFLAKE_ACCOUNT'), user=os.getenv('SNOWFLAKE_USER'), password=os.getenv('SNOWFLAKE_PASSWORD'), warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'), database=os.getenv('SNOWFLAKE_DATABASE'))
conn.cursor().execute('SELECT subsidiary_id FROM bronze.netsuite_accounts LIMIT 1')
print('✅ subsidiary_id column exists')
conn.close()
"
```

**Expected:** `✅ subsidiary_id column exists` (NOT KeyError or column not found)

---

### Step 2: Create Snowflake Dynamic Tables (On GCP VM)

```bash
# Execute Dynamic Tables SQL
sudo docker cp snowflake-mvp-ai-setup.sql dental-erp_mcp-server-prod_1:/app/

sudo docker exec dental-erp_mcp-server-prod_1 bash -c "
python3 << 'PY'
import snowflake.connector, os
from dotenv import load_dotenv
load_dotenv('/app/.env')

conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
    database=os.getenv('SNOWFLAKE_DATABASE')
)

cursor = conn.cursor()

with open('/app/snowflake-mvp-ai-setup.sql') as f:
    sql = f.read()

for stmt in [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]:
    try:
        cursor.execute(stmt)
        print('✅')
    except Exception as e:
        if 'already exists' not in str(e).lower():
            print(f'⚠️  {str(e)[:80]}')

cursor.execute('SELECT COUNT(*) FROM gold.monthly_production_kpis')
kpis = cursor.fetchone()[0]
print(f'\\n✅ VERIFIED: gold.monthly_production_kpis has {kpis} rows')

conn.close()
PY
"
```

**Verification Command:**
```bash
sudo docker exec dental-erp_mcp-server-prod_1 python3 -c "
from dotenv import load_dotenv
import snowflake.connector, os
load_dotenv('/app/.env')
conn = snowflake.connector.connect(account=os.getenv('SNOWFLAKE_ACCOUNT'), user=os.getenv('SNOWFLAKE_USER'), password=os.getenv('SNOWFLAKE_PASSWORD'), warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'), database=os.getenv('SNOWFLAKE_DATABASE'))
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM gold.monthly_production_kpis')
count = cursor.fetchone()[0]
print(f'✅ gold.monthly_production_kpis: {count} rows')
cursor.execute('SHOW DYNAMIC TABLES IN gold')
dt = len(cursor.fetchall())
print(f'✅ Dynamic Tables: {dt} created')
conn.close()
"
```

**Expected:** Row count > 0, Dynamic Tables > 0

---

### Step 3: Fix Frontend API Routing (Local Code Change)

**Check which files call MCP directly:**
```bash
cd frontend
grep -r "mcp.agentprovision.com\|MCP_BASE_URL" src/
```

**Expected to find:** `AIInsightsWidget.tsx` calling MCP directly

**Fix:** Change to use backend proxy:

```typescript
// frontend/src/components/dashboard/AIInsightsWidget.tsx

// DELETE:
const MCP_BASE_URL = import.meta.env.VITE_MCP_API_URL || 'http://localhost:8085';
const response = await axios.get(`${MCP_BASE_URL}/api/v1/analytics/insights`, ...);

// REPLACE WITH:
import { apiClient } from '../../services/api';

const response = await apiClient.get('/analytics/insights');
// Backend will proxy to MCP
```

**Add to backend:**
```typescript
// backend/src/routes/analytics.ts

router.get('/insights', authMiddleware, async (req, res) => {
  try {
    const response = await mcpClient.get('/api/v1/analytics/insights');
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

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
```

---

### Step 4: Deploy All Fixes to GCP

```bash
# From local machine
git add -A
git commit -m "fix: production critical fixes - Snowflake + frontend routing"
git push origin main

# On GCP VM
gcloud compute ssh dental-erp-vm --zone=us-central1-a

cd /opt/dental-erp
sudo git pull origin main
sudo docker-compose build backend-prod frontend-prod
sudo docker-compose restart backend-prod frontend-prod mcp-server-prod

# Wait for health
sleep 30
```

---

### Step 5: VERIFY End-to-End (Evidence Required)

**Run ALL these commands and check output:**

```bash
# 1. Frontend loads
curl -I https://dentalerp.agentprovision.com
# MUST show: HTTP/2 200

# 2. Backend proxy to financial API
curl 'https://dentalerp.agentprovision.com/api/analytics/financial/summary' \
  -H "Authorization: Bearer $(get valid token)"
# MUST show: JSON with financial data (NOT "invalid identifier")

# 3. Insights API through backend
curl 'https://dentalerp.agentprovision.com/api/analytics/insights' \
  -H "Authorization: Bearer $(token)"
# MUST show: GPT-4 insight text

# 4. Open in browser
https://dentalerp.agentprovision.com

# Check browser console:
# MUST NOT show: CORS errors
# MUST NOT show: Failed to load tenants

# 5. Navigate to Financial Analytics
# MUST show: Real data or "No data" (NOT crash or CORS error)
```

---

## Quick Reference Card

**Problem:** Too long to execute everything in this session

**Recommendation:**
1. Start fresh session tomorrow
2. Use this handoff document
3. Execute Steps 1-5 above
4. Verify with commands provided
5. Document results

**Current State:**
- Code: All committed to GitHub main branch
- Services: Running on GCP but missing Snowflake tables
- Estimated fix time: 30 minutes
- All commands provided above

---

**Session has been 12+ hours. Recommend fresh start for final deployment verification.**
