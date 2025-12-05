# Pending Deployment - Manual Ingestion Features

## Current Status

### ✅ On GitHub (commits 99a00c9 → 359c37d)
- Fixed deploy.sh Snowflake exports
- Reverted Dockerfile changes
- Documentation cleanup (22 files archived)
- NetSuite CSV upload endpoint created
- NetSuite CSV parser service created
- Test script for manual ingestion

### ✅ On Local Machine
- All latest code (commit 359c37d)
- All commits pushed to GitHub

### ❌ On GCP VM
- **Still on OLD code** (commit 99a00c9)
- Cannot pull from GitHub due to SSH key issue
- Manually fixed database and .env file (not in git)

## What Needs to Deploy

### New Files to Deploy (from git)
1. `mcp-server/src/api/netsuite_upload.py` - NetSuite CSV upload endpoint
2. `mcp-server/src/services/netsuite_csv_parser.py` - Parser for NetSuite CSVs
3. `mcp-server/src/main.py` - Updated router registration
4. `scripts/test-manual-ingestion.sh` - Test script
5. `ANALYTICS_FIX_COMPLETED.md` - Documentation
6. `CLAUDE.md` - Updated troubleshooting
7. `docs/archive/2025-11-22-analytics-fix/` - Archived docs

### Manual Fixes on VM (NOT in git - need to document)
1. **PostgreSQL `mcp` database**:
   ```sql
   -- tenant_warehouses table has correct Snowflake credentials
   SELECT warehouse_config FROM tenant_warehouses WHERE warehouse_type='snowflake';
   -- Should show: account=HKTPGHW-ES87244, user=NOMADSIMON, password=@SebaSofi.2k25!!
   ```

2. **Snowflake DENTAL_ERP_DW**:
   ```sql
   -- gold.practice_analytics_unified recreated as DYNAMIC TABLE
   SHOW TABLES LIKE 'practice_analytics_unified' IN SCHEMA gold;
   -- Should show: DYNAMIC TABLE with TARGET_LAG='1 hour'
   ```

3. **MCP Server .env file** (`/opt/dental-erp/mcp-server/.env`):
   ```bash
   SNOWFLAKE_PASSWORD=@SebaSofi.2k25!!  # No backslashes
   ```

## Deployment Steps (Once Git Pull Works)

```bash
# 1. SSH to VM
gcloud compute ssh root@dental-erp-vm --zone=us-central1-a

# 2. Pull latest code
cd /opt/dental-erp
git pull origin main

# 3. Verify we have the new files
ls -la mcp-server/src/api/netsuite_upload.py
ls -la mcp-server/src/services/netsuite_csv_parser.py

# 4. Deploy with Snowflake credentials
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

## Testing After Deployment

### Test 1: NetSuite CSV Upload
```bash
curl -X POST "https://mcp.agentprovision.com/api/v1/netsuite/upload/transactions" \
  -H "Authorization: Bearer d876e6163089364d96a45a80ed576e99fc55b306133e258d9f861007e824b456" \
  -H "X-Tenant-ID: silvercreek" \
  -F "file=@backup/TransactionDetail-83.csv"
```

Expected: `{"status": "success", "data": {"transactions_count": 294, ...}}`

### Test 2: Operations Report Upload
```bash
curl -X POST "https://mcp.agentprovision.com/api/v1/operations/upload" \
  -H "Authorization: Bearer d876e6163089364d96a45a80ed576e99fc55b306133e258d9f861007e824b456" \
  -H "X-Tenant-ID: silvercreek" \
  -F "file=@examples/operations_report.xlsx" \
  -F "practice_code=test" \
  -F "practice_name=Test Practice" \
  -F "report_month=2025-11-01"
```

Expected: `{"status": "success", "data": {"records_inserted": ...}}`

### Test 3: Verify Data in Snowflake
```sql
-- Check NetSuite data loaded
SELECT COUNT(*), MIN(transaction_date), MAX(transaction_date)
FROM bronze.netsuite_transaction_details
WHERE tenant_id = 'silvercreek';

-- Check Operations data loaded
SELECT COUNT(*), MIN(report_month), MAX(report_month)
FROM bronze_gold.operations_kpis_monthly
WHERE tenant_id = 'silvercreek';

-- Check unified view has both
SELECT
    COUNT(DISTINCT practice_id) as practices,
    SUM(total_production) as ops_production,
    SUM(netsuite_revenue) as netsuite_revenue
FROM gold.practice_analytics_unified
WHERE tenant_id = 'silvercreek';
```

## Git SSH Key Issue

**Problem**: VM cannot pull from GitHub

**VM SSH Public Key** (needs to be in GitHub):
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDSX1Ak9wuY7ZoW9COmuriSOSD2wn54adVezqKXA2HYF saguilera1608@gmail.com
```

**Fingerprint**: `SHA256:m8ImsyshGTZeilBSb0kgQ9nlAuPtn4TgyNeQ2sg3rFI`

**Solution**: Add this key to https://github.com/settings/keys (your account) OR https://github.com/nomad3/dentalERP/settings/keys (deploy key for repo)

## Current State Summary

| Component | Status | Version |
|-----------|--------|---------|
| Local Machine | ✅ Up to date | 359c37d |
| GitHub | ✅ Up to date | 359c37d |
| GCP VM Code | ❌ OLD | 99a00c9 (missing 5 commits) |
| GCP VM Database | ✅ Fixed manually | tenant_warehouses updated |
| GCP VM Snowflake | ✅ Fixed manually | practice_analytics_unified recreated |
| Analytics Dashboard | ✅ Working | $48.6M showing |

## What's Working Right Now

- ✅ Analytics dashboard displays $48.6M operations data
- ✅ 12 practices visible
- ✅ MCP Server connected to Snowflake
- ✅ All analytics endpoints returning data

## What Will Work After Deployment

- ✅ NetSuite CSV upload via API
- ✅ Operations Report upload via API (already exists)
- ✅ Bulk NetSuite upload from backup/ directory
- ✅ Manual ingestion UI in frontend will work for both types
- ✅ Complete documentation

---

**Created**: 2025-11-23
**Blocker**: Git pull fails on VM due to SSH key
**Next Step**: Add VM SSH key to GitHub, then run deployment
