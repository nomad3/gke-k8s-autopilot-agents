# Fix Analytics Dashboard Data Display Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix analytics dashboard to display $309M production data from Snowflake for Silver Creek and 17 subsidiary practices.

**Architecture:** MCP server has Snowflake credentials but connection is failing. Fix Snowflake connection, verify analytics endpoints query correct tables (bronze_gold.daily_production_metrics VIEW pointing to gold.practice_analytics_unified), ensure data flows to frontend.

**Tech Stack:** Python FastAPI (MCP), Snowflake, PostgreSQL, React (Frontend)

---

## Current State

**Working:**
- ✅ Login via "Admin Access" button
- ✅ Frontend loading at https://dentalerp.agentprovision.com
- ✅ Backend and MCP containers running
- ✅ Snowflake credentials in MCP container environment
- ✅ Snowflake data exists: $309M production, 12 practices

**Broken:**
- ❌ Analytics endpoints return 500 errors
- ❌ MCP can't connect to Snowflake (error 250001)
- ❌ Dashboard shows "No practice data available"

---

## Task 1: Debug MCP Snowflake Connection

**Files:**
- Check: `mcp-server/src/connectors/snowflake.py`
- Check: MCP container logs

**Step 1: Check MCP Snowflake connection error**

Run:
```bash
gcloud compute ssh root@dental-erp-vm --zone=us-central1-a --command "docker logs dental-erp_mcp-server-prod_1 2>&1" | grep -A20 "Snowflake"
```

Expected: See detailed error about why Snowflake connection fails

**Step 2: Verify Snowflake credentials format**

Check if password has special characters that need escaping:
- Password: `@SebaSofi.2k25!!`
- Issue: `!!` might be interpreted by shell/docker

Run inside MCP container:
```bash
docker exec dental-erp_mcp-server-prod_1 python3 -c "
import os
print('SNOWFLAKE_ACCOUNT:', os.getenv('SNOWFLAKE_ACCOUNT'))
print('SNOWFLAKE_USER:', os.getenv('SNOWFLAKE_USER'))
print('SNOWFLAKE_PASSWORD:', os.getenv('SNOWFLAKE_PASSWORD'))
"
```

Expected: All values print correctly

**Step 3: Test Snowflake connection directly from MCP container**

Run:
```bash
docker exec dental-erp_mcp-server-prod_1 python3 << 'EOF'
import snowflake.connector
import os

conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    role=os.getenv('SNOWFLAKE_ROLE'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
    database=os.getenv('SNOWFLAKE_DATABASE')
)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM bronze_gold.daily_production_metrics")
print(f"✅ Connected! Records: {cursor.fetchone()[0]}")
cursor.close()
conn.close()
EOF
```

Expected: "✅ Connected! Records: 2173" or error showing exact connection issue

**Step 4: Fix based on error found**

If password escaping issue:
- Update docker-compose.yml to escape `!` characters
- Or use docker secrets instead of env vars

If network issue:
- Check if MCP container can resolve Snowflake hostname
- Check firewall rules

If credentials issue:
- Verify credentials work from local machine
- Check if account is locked or password expired

**Step 5: Commit fix**

```bash
git add [files changed]
git commit -m "fix: resolve MCP Snowflake connection issue

[Description of what was fixed]"
git push origin main
```

---

## Task 2: Verify Analytics Endpoints Query Correct Tables

**Files:**
- Check: `mcp-server/src/api/analytics.py`
- Check: `mcp-server/src/api/analytics_unified.py`

**Step 1: Identify which endpoints are being called**

From browser console errors:
- `/api/analytics-unified/summary`
- `/api/analytics-unified/by-practice`
- `/api/analytics-unified/monthly?category=operations`

Find these in MCP server code:
```bash
grep -r "analytics-unified" mcp-server/src/
```

Expected: Find route handlers in `analytics_unified.py` or `analytics.py`

**Step 2: Check SQL queries in those endpoints**

Look for SQL queries that might be:
- Querying wrong table names
- Using wrong column names
- Missing tenant_id filter

Example issue: Query uses `practice_financials` but table is `daily_production_metrics`

**Step 3: Update queries to use correct table**

Queries should use:
```sql
SELECT * FROM bronze_gold.daily_production_metrics
WHERE tenant_id = 'silvercreek'
```

The `daily_production_metrics` is a VIEW created earlier that points to `gold.practice_analytics_unified`

**Step 4: Test endpoint locally**

Run:
```bash
cd mcp-server
# Start MCP server locally
uvicorn src.main:app --reload --port 8085
```

Test in another terminal:
```bash
curl "http://localhost:8085/api/v1/analytics/unified/summary" \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  -H "X-Tenant-ID: silvercreek"
```

Expected: JSON with practice counts and production totals

**Step 5: Commit**

```bash
git add mcp-server/src/api/analytics_unified.py
git commit -m "fix: update analytics endpoints to query correct Snowflake tables"
git push origin main
```

---

## Task 3: Deploy with Snowflake Credentials

**Files:**
- Modify: None (deployment task)

**Step 1: Pull latest code on VM**

Run:
```bash
gcloud compute ssh root@dental-erp-vm --zone=us-central1-a
cd /opt/dental-erp
git pull origin main
```

Expected: "Fast-forward" with latest commits

**Step 2: Set environment variables and deploy**

Run:
```bash
export SNOWFLAKE_ACCOUNT='HKTPGHW-ES87244'
export SNOWFLAKE_USER='NOMADSIMON'
export SNOWFLAKE_PASSWORD='@SebaSofi.2k25!!'
export SNOWFLAKE_ROLE='ACCOUNTADMIN'
export SNOWFLAKE_WAREHOUSE='COMPUTE_WH'
export SNOWFLAKE_DATABASE='DENTAL_ERP_DW'
export MCP_API_KEY='d876e6163089364d96a45a80ed576e99fc55b306133e258d9f861007e824b456'
export MCP_SECRET_KEY='production-secret-key-for-jwt-signing-min-32-characters-secure'

sudo -E ./deploy.sh
```

Expected: "Deployment Complete! MCP Server is ready!"

**Step 3: Verify services are healthy**

Run:
```bash
docker-compose ps
```

Expected: All prod services show "Up" or "Up (healthy)"

**Step 4: Test MCP analytics endpoint**

Run:
```bash
curl "https://mcp.agentprovision.com/api/v1/analytics/production/summary" \
  -H "Authorization: Bearer d876e6163089364d96a45a80ed576e99fc55b306133e258d9f861007e824b456" \
  -H "X-Tenant-ID: silvercreek"
```

Expected: JSON response with practice_count and total_production

**Step 5: Test in browser**

1. Go to https://dentalerp.agentprovision.com
2. Click "Admin Access" to login
3. Navigate to Analytics → Overview
4. Verify data displays (not "No practice data available")

Expected: Dashboard shows production metrics

---

## Task 4: Fix Data Corruption in Snowflake View

**Files:**
- Modify: None (Snowflake SQL)

**Background:** The `daily_production_metrics` VIEW shows 2,173 records and $309M which is TOO MUCH. It's including all months/duplicates instead of unique monthly records.

**Step 1: Check current VIEW definition**

Run:
```python
import os, snowflake.connector
from dotenv import load_dotenv

load_dotenv('mcp-server/.env')
conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    role=os.getenv('SNOWFLAKE_ROLE'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
    database=os.getenv('SNOWFLAKE_DATABASE')
)

cursor = conn.cursor()
cursor.execute("SHOW VIEWS LIKE 'daily_production_metrics' IN SCHEMA bronze_gold")
# Check if it's a VIEW or TABLE

cursor.execute("""
    SELECT DISTINCT practice_id, report_month
    FROM bronze_gold.daily_production_metrics
    WHERE tenant_id = 'silvercreek'
    ORDER BY practice_id, report_month
    LIMIT 20
""")

for row in cursor.fetchall():
    print(row)

cursor.close()
conn.close()
```

Expected: See if there are duplicate months or if data looks correct

**Step 2: Recreate VIEW with proper aggregation**

The VIEW should show ONE record per practice per month, not all individual records.

Run:
```sql
CREATE OR REPLACE VIEW bronze_gold.daily_production_metrics AS
SELECT
    practice_id as practice_location,
    report_month as report_date,
    tenant_id,
    total_production,
    net_production,
    collections,
    visits_total as patient_visits,
    ppv_overall as production_per_visit,
    collection_rate_pct,
    extraction_method,
    data_quality_score,
    0 as duplicate_count,
    calculated_at as uploaded_at,
    calculated_at
FROM gold.practice_analytics_unified
WHERE total_production IS NOT NULL
```

**Step 3: Verify corrected data**

Run:
```sql
SELECT COUNT(DISTINCT practice_location) as practices,
       COUNT(*) as records,
       SUM(total_production) as total
FROM bronze_gold.daily_production_metrics
WHERE tenant_id = 'silvercreek'
```

Expected: ~12 practices, reasonable record count, $309M total

**Step 4: Document**

No commit needed (Snowflake change), but document in session notes

---

## Task 5: Verify Analytics Display in Dashboard

**Files:**
- None (verification task)

**Step 1: Clear browser cache**

In browser:
- Clear cache and cookies for https://dentalerp.agentprovision.com
- Hard refresh (Cmd+Shift+R or Ctrl+Shift+R)

**Step 2: Login and navigate**

1. Go to https://dentalerp.agentprovision.com
2. Click "Admin Access"
3. Navigate to Analytics → Overview

**Step 3: Verify data displays**

Check for:
- ✅ Total Production number (should be ~$309M or subset)
- ✅ Practice count (12 practices)
- ✅ Charts/graphs rendering
- ✅ No "500 Internal Server Error" messages
- ✅ No "No practice data available" messages

**Step 4: Check all analytics tabs**

- Overview tab
- Operations tab
- Financial tab (if exists)
- Production tab (if exists)

All should show data, not errors.

**Step 5: Document success**

Take screenshots and document what's displaying correctly

---

## Success Criteria

- [ ] MCP connects to Snowflake without errors
- [ ] Analytics endpoints return JSON (not 500 errors)
- [ ] Dashboard displays production metrics
- [ ] 12 practices visible in analytics
- [ ] Data totals are reasonable (~$309M, not corrupted)
- [ ] All changes committed and deployed via Git

---

## Troubleshooting

### If Snowflake connection still fails:
- Check if GCP VM can reach Snowflake (network/firewall)
- Verify credentials haven't expired
- Check Snowflake account status

### If data is still corrupted:
- Revert to using Operations Report Excel data only (known good)
- Disable NetSuite integration temporarily
- Focus on getting SOME data showing vs perfect data

### If MCP crashes:
- Check Python dependencies are installed
- Check for syntax errors in analytics.py
- Review MCP startup logs for import errors

---

**Estimated Time:** 2 hours
**Priority:** CRITICAL (dashboard must work)
**Complexity:** Medium (mostly config and SQL fixes)
