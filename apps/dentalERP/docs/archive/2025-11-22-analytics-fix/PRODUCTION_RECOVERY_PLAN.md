# Production Recovery Plan - Dashboard Restoration

**Status:** Production completely broken due to docker-compose profile dependency issues
**Cause:** Changes made Nov 19-21 broke profile dependencies between dev/prod containers
**Data:** ✅ SAFE - All data intact in Snowflake ($309M production, 12 practices)

---

## Quick Summary

**What's Broken:**
- Docker-compose profiles have circular dependencies
- backend-prod depends on mcp-server (dev) which has dev profile
- mcp-server (dev) and mcp-server-prod conflict on port 8085
- Result: NO production containers can start

**What Works:**
- ✅ Code compiles successfully (tested locally)
- ✅ All data in Snowflake
- ✅ Git pull working with SSH deploy key
- ✅ Local build produces correct dist/routes/auth.js

---

## Root Cause Analysis

1. **Docker-Compose Profile Issue:**
   - `mcp-server` and `backend` services had NO profiles (always start)
   - We added `profiles: [dev]` to fix
   - BUT `backend-prod` depends on `mcp-server` which now requires dev profile
   - Creates: "Service mcp-server not enabled by active profiles" error

2. **Correct Fix:**
   - `backend-prod` should depend on `mcp-server-prod`, not `mcp-server`
   - OR remove the dependency entirely
   - OR add both dev and production profiles to dependencies

---

## Emergency Recovery Steps

### Option 1: Fix Docker-Compose Dependencies (2-3 hours)

**Step 1:** Update docker-compose.yml

Change backend-prod dependencies from:
```yaml
backend-prod:
  depends_on:
    mcp-server:  # WRONG - this is dev service
      condition: service_healthy
```

To:
```yaml
backend-prod:
  depends_on:
    mcp-server-prod:  # CORRECT - prod service
      condition: service_healthy
```

**Step 2:** Rebuild and deploy
```bash
git commit docker-compose.yml
git push
# On production:
git pull
docker-compose down
docker-compose --profile production up -d
```

### Option 2: Remove Health Check Dependencies (Faster - 30 min)

Remove `depends_on: mcp-server` from backend-prod entirely.
Backend will start without waiting for MCP, which is fine since they're independent.

### Option 3: Nuclear Option - Fresh Deployment (1 hour)

```bash
# On production VM:
cd /opt/dental-erp
docker-compose down -v  # Remove volumes too
docker system prune -af  # Clean everything
git pull origin main
./deploy.sh
```

---

## Test Plan After Fix

```bash
# 1. Verify services
docker-compose ps
# Should show ONLY: backend-prod, frontend-prod, mcp-server-prod, postgres, redis

# 2. Test frontend
curl https://dentalerp.agentprovision.com
# Should return HTML

# 3. Test backend login
curl -X POST https://dentalerp.agentprovision.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@practice.com","password":"Admin123!"}'
# Should return JWT token (200 OK)

# 4. Test MCP analytics
curl "https://mcp.agentprovision.com/api/v1/analytics/production/summary" \
  -H "Authorization: Bearer d876e6163089364d96a45a80ed576e99fc55b306133e258d9f861007e824b456" \
  -H "X-Tenant-ID: silvercreek"
# Should return 12 practices, $309M

# 5. Login to dashboard
# Go to https://dentalerp.agentprovision.com
# Email: admin@practice.com
# Password: Admin123!
# Should see analytics data
```

---

## Current Workarounds

**While dashboard is broken, you can:**

1. **Query Snowflake directly** to show data:
```sql
USE DATABASE DENTAL_ERP_DW;

-- Show all practices
SELECT practice_id, practice_display_name,
       SUM(total_production) as production,
       SUM(netsuite_revenue) as revenue
FROM gold.practice_analytics_unified
GROUP BY practice_id, practice_display_name
ORDER BY production DESC;

-- Returns 12-20 practices with $309M+ production
```

2. **Use MCP API directly** (works!):
```bash
curl "https://mcp.agentprovision.com/api/v1/analytics/production/summary" ...
# Returns JSON with 12 practices
```

3. **Export to Excel** for presentation

---

## Files to Check/Fix

1. **docker-compose.yml** - Fix profile dependencies
2. **deploy.sh** - May need updates for profile handling
3. **backend/src/routes/auth.ts** - ✅ Exists and compiles
4. **Snowflake views** - ✅ All working, daily_production_metrics VIEW created

---

## Data Status (GOOD NEWS)

**All data is SAFE and ACCESSIBLE:**
- bronze_gold.daily_production_metrics: VIEW to unified data (12 practices)
- gold.practice_analytics_unified: 20 practices, 2,245 records
- bronze_gold.operations_kpis_monthly: 12 practices, 339 records
- bronze_gold.netsuite_monthly_financials: 14 practices, 140 records

**Total:**
- $309M Operations production
- $492M NetSuite revenue
- 324K patient visits
- 2021-2025 date range

---

## Recommended Next Steps

1. **Immediate:** Fix docker-compose.yml backend-prod dependency
2. **Test locally** with docker-compose --profile production
3. **Deploy** when working locally
4. **Verify** login and data display
5. **Document** working deployment process

---

**Estimated Time to Fix:** 1-2 hours with focused work on docker-compose configuration

**Key Learning:** Always test docker-compose profile changes locally before deploying to production!
