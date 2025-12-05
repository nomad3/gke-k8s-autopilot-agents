# Emergency Demo Fix - Dashboard Network Errors

**URGENT:** Client demo TODAY. Dashboard shows "Network Error" when trying to load data.

## Current Status

**Services Running:**
- ✅ Frontend: https://dentalerp.agentprovision.com (loads, login works)
- ✅ Backend: Port 3001 (processing logins successfully)
- ✅ MCP Server: Port 8085, healthy
- ✅ PostgreSQL & Redis: Healthy

**Data Exists in Snowflake:**
- ✅ gold.practice_analytics_unified: 20 practices, 2,245 records
- ✅ bronze_gold.operations_kpis_monthly: 12 practices, 339 records
- ✅ bronze_gold.daily_production_metrics: VIEW created pointing to unified data
- ✅ $309M production data available

**Problem:**
- ❌ Frontend shows "Network Error" when trying to load analytics data
- ❌ Browser console shows: ERR_CONNECTION_CLOSED, Failed to fetch
- ❌ Frontend error: "Failed to load tenants"

**Analytics API Test:**
```bash
curl "https://mcp.agentprovision.com/api/v1/analytics/production/summary" \
  -H "Authorization: Bearer d876e6163089364d96a45a80ed576e99fc55b306133e258d9f861007e824b456" \
  -H "X-Tenant-ID: silvercreek"
```
Returns: 12 practices, $309M (WORKING!)

## What Needs to be Fixed

1. **Frontend can't connect to backend** - Network errors, connection closed
2. **Likely causes:**
   - CORS configuration issue
   - Nginx proxy configuration broken
   - Backend routes not properly registered
   - Frontend API base URL misconfigured

## Quick Diagnostic Steps

```bash
# 1. Check nginx config
gcloud compute ssh root@dental-erp-vm --zone=us-central1-a --command "cat /etc/nginx/sites-enabled/dentalerp.agentprovision.com | grep -A10 location"

# 2. Check backend routes
gcloud compute ssh root@dental-erp-vm --zone=us-central1-a --command "cd /opt/dental-erp && docker-compose logs backend-prod" | grep -i "route\|endpoint\|error" | tail -30

# 3. Test backend directly
curl https://dentalerp.agentprovision.com/api/auth/login -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"test","password":"test"}'

# 4. Check what frontend is trying to call
gcloud compute ssh root@dental-erp-vm --zone=us-central1-a --command "cd /opt/dental-erp && docker-compose logs frontend-prod" | tail -50
```

## Most Likely Fix

**The frontend is calling `/api/tenants` which doesn't exist.**

Options:
1. Add `/api/tenants` endpoint to backend (if it's supposed to exist)
2. OR remove TenantContext from frontend (if not needed for single-tenant setup)
3. OR mock the endpoint to return a default tenant

## Emergency Bypass for Demo

If you can't fix in time, create a static data version:
- Export Snowflake data to JSON
- Serve static JSON files from frontend
- Bypass backend entirely for demo

## File Locations

**Key files:**
- Frontend: `/opt/dental-erp/frontend/src/`
- Backend: `/opt/dental-erp/backend/src/`
- MCP: `/opt/dental-erp/mcp-server/src/`
- Nginx: `/etc/nginx/sites-enabled/dentalerp.agentprovision.com`

**GCP VM:**
- IP: 34.69.75.118
- Zone: us-central1-a
- Name: dental-erp-vm

**Git:**
- SSH key added to GitHub deploy keys
- Can now use: `git pull origin main`

## Data Summary

**Snowflake has complete data:**
- 12 practices from Operations Report
- 14 practices from NetSuite CSV files
- 20 total practices in unified view
- $309M Operations production
- $492M NetSuite revenue

**The data is there - just need frontend to connect to backend properly!**

## Timeline

**Demo:** TODAY
**Fix needed:** ASAP (next 1-2 hours)

## Commands to Try

```bash
# Restart all services cleanly
gcloud compute ssh root@dental-erp-vm --zone=us-central1-a --command "
cd /opt/dental-erp
docker-compose down
docker-compose --profile production up -d
"

# Check if CORS is the issue
curl -I https://dentalerp.agentprovision.com/api/auth/login \
  -H "Origin: https://dentalerp.agentprovision.com"

# Test if backend API works directly
curl https://dentalerp.agentprovision.com/api/practices

# Check nginx error logs
gcloud compute ssh root@dental-erp-vm --zone=us-central1-a --command "tail -100 /var/log/nginx/error.log"
```

## Success Criteria

When fixed, you should be able to:
1. ✅ Login at https://dentalerp.agentprovision.com
2. ✅ See 12 practices in analytics dashboard
3. ✅ View production metrics ($309M total)
4. ✅ No "Network Error" messages

**All the data is there - this is just a connectivity/routing issue that can be fixed quickly!**
