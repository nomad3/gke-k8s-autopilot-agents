# Operations KPI Dashboard - Production Deployment Guide

**Date:** November 17, 2025
**Status:** Ready for Deployment
**Commits:** `33cdbd8` + `e22f959`

---

## ✅ What's Been Completed Locally

### Backend Implementation
- ✅ Snowflake tables created (Bronze, Silver Dynamic, Gold Dynamic)
- ✅ Operations API endpoints (`/api/v1/operations/*`)
- ✅ Excel/CSV parser service
- ✅ End-to-end testing complete
- ✅ 21 months of LHD data loaded and verified
- ✅ Code committed and pushed to GitHub

### Test Results
```
✅ 24 records in Snowflake (21 LHD months + 3 test records)
✅ Dynamic tables auto-refreshing correctly
✅ KPIs calculating accurately:
   - Collection Rate: 97.1%
   - Production/Visit: $95.55
   - Case Acceptance: 25.2%
   - Hygiene Ratio: 2.55
   - LTM rollups working
```

---

## 🚀 Production Deployment Steps

### Step 1: SSH to GCP VM

```bash
gcloud compute ssh dental-erp-vm --zone=us-central1-a
```

### Step 2: Navigate to Project and Pull Code

```bash
cd /opt/dental-erp

# Pull latest code from GitHub
# Note: If git pull fails due to SSH keys, try HTTPS:
sudo git remote set-url origin https://github.com/nomad3/dentalERP.git
sudo git pull origin main

# Verify commits
git log -2 --oneline
# Should show:
# e22f959 feat: add operations report parser and end-to-end testing
# 33cdbd8 feat: implement Operations KPI Dashboard backend with NetSuite integration
```

### Step 3: Create Operations KPI Tables in Production Snowflake

```bash
# Set Snowflake credentials (already in .env)
cd /opt/dental-erp
source .env

# Run table creation script
python3 scripts/create-operations-kpi-tables.py
```

**Expected Output:**
```
✅ Connected to Snowflake: HKTPGHW-ES87244
✓ Created Bronze table: operations_metrics_raw
✓ Created Silver dynamic table: stg_operations_metrics
✓ Created Gold dynamic table: operations_kpis_monthly
✅ All tables verified successfully
```

### Step 4: Deploy MCP Server with Operations Endpoints

```bash
cd /opt/dental-erp

# Rebuild and restart MCP server with new operations module
sudo docker-compose build --no-cache mcp-server-prod
sudo docker-compose up -d mcp-server-prod

# Wait for startup
sleep 10

# Check MCP server logs
sudo docker logs --tail 50 dentalerp-mcp-server-prod-1

# Should see:
# "✅ Scheduler started: 4 jobs registered"
# "INFO: Application startup complete"
```

### Step 5: Verify Operations API Endpoints

```bash
# Set MCP API key
export MCP_API_KEY="your-production-mcp-api-key"

# Test health endpoint
curl https://mcp.agentprovision.com/health

# Test operations endpoints (should return empty array initially)
curl https://mcp.agentprovision.com/api/v1/operations/kpis/monthly \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: silvercreek"

# Should return: [] (empty - no data uploaded yet)
# Or if test data exists: JSON array with KPI records
```

### Step 6: Upload Operations Data to Production

```bash
cd /opt/dental-erp

# Parse and upload Operations Report
python3 scripts/python/parse_operations_report.py

# Should output:
# ✅ Extracted 21 monthly records
# ✅ Upload complete: 21 successful, 0 errors
# ✅ Dynamic tables refreshed
```

### Step 7: Verify Production API with Real Data

```bash
# Query monthly KPIs
curl https://mcp.agentprovision.com/api/v1/operations/kpis/monthly?limit=5 \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: silvercreek" | jq '.'

# Query summary
curl https://mcp.agentprovision.com/api/v1/operations/kpis/summary \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: silvercreek" | jq '.'

# Query by-practice comparison
curl https://mcp.agentprovision.com/api/v1/operations/kpis/by-practice \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: silvercreek" | jq '.'
```

**Expected Response:**
```json
[
  {
    "practice_location": "lhd",
    "practice_name": "Laguna Hills Dental",
    "report_month": "2022-09-01",
    "total_production": 160000.0,
    "collection_rate_pct": 98.06,
    "ppv_overall": 262.30,
    "case_acceptance_rate_pct": 80.0,
    "hygiene_productivity_ratio": 2.50,
    "ltm_production": 1920000.0
  }
]
```

---

## 🐛 Troubleshooting

### Issue: git pull fails with "Host key verification failed"

**Solution:**
```bash
# On GCP VM, set remote to HTTPS instead of SSH
cd /opt/dental-erp
sudo git remote set-url origin https://github.com/nomad3/dentalERP.git
sudo git pull origin main
```

### Issue: MCP Server won't start

**Check logs:**
```bash
sudo docker logs --tail 100 dentalerp-mcp-server-prod-1
```

**Common fixes:**
```bash
# Rebuild container
sudo docker-compose build --no-cache mcp-server-prod

# Restart
sudo docker-compose up -d mcp-server-prod
```

### Issue: Operations endpoints return 404

**Verify router is registered:**
```bash
# Check if operations.py is in the image
sudo docker exec dentalerp-mcp-server-prod-1 ls -la /app/src/api/operations.py

# Check API docs
curl https://mcp.agentprovision.com/docs
# Should list /api/v1/operations/* endpoints
```

### Issue: Snowflake tables not found

**Run table creation:**
```bash
cd /opt/dental-erp
source .env
python3 scripts/create-operations-kpi-tables.py
```

---

## ✅ Post-Deployment Verification Checklist

- [ ] MCP server running: `sudo docker ps | grep mcp-server-prod`
- [ ] Operations API responds: `curl https://mcp.agentprovision.com/api/v1/operations/kpis/monthly`
- [ ] Snowflake tables exist: Run table creation script
- [ ] Data uploaded: Run parse_operations_report.py
- [ ] Dynamic tables refreshing: Check Snowflake UI
- [ ] API returns data: Query endpoints with curl

---

## 📊 Current Deployment Status

**Code Status:**
- ✅ Committed: 2 commits (33cdbd8 + e22f959)
- ✅ Pushed to GitHub: origin/main
- ⏳ **Needs deployment to GCP VM**

**Production URLs:**
- Frontend: https://dentalerp.agentprovision.com
- MCP Server: https://mcp.agentprovision.com
- API Docs: https://mcp.agentprovision.com/docs

**What's Working:**
- ✅ Tested locally with local Snowflake
- ✅ All 3 Snowflake layers verified
- ✅ API endpoints tested
- ⏳ **Pending:** Deploy to GCP and verify production

---

## 📋 Manual Deployment Checklist

Run these commands on GCP VM (`gcloud compute ssh dental-erp-vm --zone=us-central1-a`):

```bash
# 1. Pull code
cd /opt/dental-erp
sudo git pull origin main

# 2. Create Snowflake tables
python3 scripts/create-operations-kpi-tables.py

# 3. Rebuild and restart MCP server
sudo docker-compose build --no-cache mcp-server-prod
sudo docker-compose up -d mcp-server-prod

# 4. Verify deployment
curl https://mcp.agentprovision.com/health
curl https://mcp.agentprovision.com/docs | grep operations

# 5. Upload data
python3 scripts/python/parse_operations_report.py

# 6. Test API
export MCP_API_KEY="your-prod-key"
curl https://mcp.agentprovision.com/api/v1/operations/kpis/monthly \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: silvercreek"
```

---

**Next Step:** SSH to GCP VM and run the commands above

**Alternative:** If you have access to GCP console, you can run these in Cloud Shell

---

**Document Owner:** Development Team
**Last Updated:** November 17, 2025
