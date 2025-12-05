# NetSuite Testing Quick Start Guide
**Date**: November 12, 2025
**Status**: ✅ Fixed and Ready for Testing

---

## What We Fixed

### 🔴 Critical Bug Fixed
**Issue**: Missing `import os` in NetSuite connector caused crashes
**File**: `mcp-server/src/connectors/netsuite.py`
**Fix**: Added `import os` on line 12
**Impact**: NetSuite connector can now initialize with environment variables

### 📋 New Test Scripts Created

1. **`scripts/test-netsuite-suiteql.sh`**
   - Quick test of SuiteQL approach
   - Triggers sync of 10 journal entries
   - Bypasses User Event Script crashes
   - Runtime: ~1 minute

2. **`scripts/test-netsuite-e2e.sh`**
   - Comprehensive 9-test suite
   - Tests complete data flow
   - Validates data quality
   - Runtime: ~2-3 minutes

### 📚 Documentation Added

**`docs/NETSUITE_E2E_TESTING_ISSUES.md`**
- Complete diagnostic report
- Root cause analysis
- Component-by-component status
- Troubleshooting guide

---

## Quick Testing (3 Steps)

### Prerequisites

```bash
# Required environment variables
export MCP_API_KEY="your-mcp-api-key"
export SNOWFLAKE_ACCOUNT="your-account.snowflakecomputing.com"
export SNOWFLAKE_USER="your-username"
export SNOWFLAKE_PASSWORD="your-password"
export SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
export SNOWFLAKE_DATABASE="DENTAL_ERP_DW"
```

### Step 1: Test SuiteQL Approach (1 min)

```bash
cd /Users/nomade/Documents/GitHub/dentalERP
./scripts/test-netsuite-suiteql.sh
```

**Expected Output**:
```
✓ Sync triggered successfully
Waiting 45 seconds for sync to complete...
✓ Test complete
```

### Step 2: Run Full E2E Test (3 min)

```bash
./scripts/test-netsuite-e2e.sh
```

**Expected Output**:
```
✓ PASS: NetSuite API connection successful
✓ PASS: Bronze layer accessible
✓ PASS: NetSuite sync triggered successfully
✓ PASS: Bronze layer has complete data (XX% with line items)
✓ PASS: Silver layer processed Bronze data successfully
✓ PASS: Gold layer has aggregated metrics
✓ PASS: Backend financial API returns data
✓ PASS: MCP financial API returns data
✓ PASS: Data quality checks passed

Passed: 9
Failed: 0
✓ All tests passed! NetSuite E2E flow is working.
```

### Step 3: Verify in Frontend

1. Open browser: http://localhost:3000
2. Navigate to: **Financial Analytics** page
3. Should see:
   - Total Revenue / Expenses / Net Income
   - Practice comparison table
   - Monthly trends (if multiple months synced)

---

## What the Tests Check

### Test Coverage Matrix

| # | Test | What It Validates | Component |
|---|------|-------------------|-----------|
| 1 | NetSuite Connection | OAuth 1.0a auth works | MCP Connector |
| 2 | Bronze Before Sync | Snowflake accessible | Snowflake |
| 3 | Sync Trigger | SuiteQL sync starts | MCP Server |
| 4 | Bronze After Sync | Data has line items | Bronze Layer |
| 5 | Silver Processing | Transformation works | Silver Layer |
| 6 | Gold Aggregation | Metrics calculated | Gold Layer |
| 7 | Backend API | Proxies to MCP | Backend |
| 8 | MCP API | Returns data | MCP Server |
| 9 | Data Quality | Structure valid | End-to-End |

---

## Troubleshooting

### Issue: "MCP_API_KEY environment variable not set"

**Solution**:
```bash
export MCP_API_KEY="your-actual-api-key-here"
```

Get the key from:
- Local: `cat /opt/dental-erp/.env | grep MCP_API_KEY`
- Production: Check secrets manager

---

### Issue: "Snowflake connection failed"

**Solution**:
```bash
# Test Snowflake connectivity
python3 << 'EOF'
import snowflake.connector
import os

conn = snowflake.connector.connect(
    account=os.environ['SNOWFLAKE_ACCOUNT'],
    user=os.environ['SNOWFLAKE_USER'],
    password=os.environ['SNOWFLAKE_PASSWORD']
)
print("✓ Connected to Snowflake!")
conn.close()
EOF
```

---

### Issue: "Bronze layer data incomplete (only X% with line items)"

**Meaning**: NetSuite sync returned records without transaction details

**Possible Causes**:
1. User Event Script still blocking detail fetches
2. SuiteQL not returning line items correctly
3. Database credentials issue

**Solutions**:

**Option A: Use CSV Import (Works 100%)**
```bash
# Export Transaction Detail Report from NetSuite
# Import via CSV (bypasses all API issues)
# See: docs/NETSUITE_API_DATA_ISSUE_EXPLAINED.md
```

**Option B: Test SuiteQL Directly**
```bash
# Check SuiteQL implementation
grep -A 50 "fetch_journal_entries_via_suiteql" \
  mcp-server/src/connectors/netsuite.py
```

**Option C: Check MCP Logs**
```bash
docker logs dental-erp_mcp-server-prod_1 | grep -i netsuite | tail -100
```

---

### Issue: "Silver/Gold layers have no data"

**Check Bronze First**:
```sql
-- In Snowflake
SELECT COUNT(*) FROM bronze.netsuite_journal_entries;
SELECT COUNT(*) FROM bronze.netsuite_journal_entries WHERE raw_data:line IS NOT NULL;
```

If Bronze has data with line items but Silver is empty:
```sql
-- Check dynamic table status
SHOW DYNAMIC TABLES IN SCHEMA silver;

-- Manually refresh if needed
ALTER DYNAMIC TABLE silver.stg_financials REFRESH;
```

---

## Understanding the Results

### Good Results (Expected)

```
Bronze: 100+ records with 90%+ having line items
Silver: 200+ rows (2-3x Bronze due to line item expansion)
Gold: Multiple months of aggregated metrics
Backend API: Returns financial summary
Frontend: Displays charts and KPIs
```

### Problematic Results

```
Bronze: Many records but <10% have line items
  → NetSuite API returning incomplete data
  → Use SuiteQL or CSV import instead

Silver: 0 rows despite Bronze having data
  → Check if records have line items
  → Verify dynamic table refresh

Gold: 0 or 1 month only
  → Need more historical data
  → Export additional months via CSV
```

---

## Next Steps After Testing

### If All Tests Pass ✅

1. **Deploy to Production**
   ```bash
   git push origin main
   # Deploy via your CI/CD or manual deployment
   ```

2. **Schedule Regular Syncs**
   - Set up cron job for daily NetSuite sync
   - Monitor sync success rate
   - Alert on data quality drops

3. **Add More Data**
   - Export 6-12 months of historical data
   - Import via CSV for complete trends
   - Backfill missing months

### If Tests Fail ❌

1. **Check the Diagnostic Report**
   ```bash
   cat docs/NETSUITE_E2E_TESTING_ISSUES.md
   ```

2. **Review Component Status**
   - NetSuite Connector: Can it connect?
   - Bronze Layer: Does it have data?
   - Silver Layer: Is transformation working?
   - Gold Layer: Are metrics calculated?

3. **Get Help**
   - Check MCP Server logs
   - Review Snowflake query history
   - Consult NetSuite API documentation

---

## Production Deployment Checklist

Before deploying to production:

- [ ] All E2E tests pass locally
- [ ] NetSuite credentials verified in production `.env`
- [ ] Snowflake connection tested in production
- [ ] MCP Server can reach NetSuite API
- [ ] Backend can reach MCP Server
- [ ] Frontend can reach Backend API
- [ ] Test data flows end-to-end in production
- [ ] Monitoring/alerting configured
- [ ] Backup/rollback plan ready

---

## Performance Expectations

| Operation | Expected Time | Notes |
|-----------|---------------|-------|
| NetSuite Connection Test | <5 seconds | OAuth handshake |
| Sync 100 Journal Entries | 2-3 minutes | SuiteQL query + insert |
| Bronze → Silver Transformation | 5-10 seconds | Dynamic table refresh |
| Silver → Gold Aggregation | 2-5 seconds | Group by operations |
| Backend API Response | <1 second | Direct Snowflake query |
| Frontend Load | 1-2 seconds | React render + API call |

**Total E2E Latency**: Sync trigger to frontend display: **3-5 minutes**

---

## Monitoring Commands

### Check Sync Status
```bash
curl -s https://mcp.agentprovision.com/api/v1/netsuite/sync/status \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: default" | python3 -m json.tool
```

### Check Data Completeness
```sql
-- In Snowflake
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN raw_data:line IS NOT NULL THEN 1 ELSE 0 END) as complete,
    SUM(CASE WHEN raw_data:line IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as pct
FROM bronze.netsuite_journal_entries;
```

### Check Recent Syncs
```sql
SELECT
    DATE_TRUNC('hour', _ingestion_timestamp) as sync_hour,
    COUNT(*) as records_synced,
    AVG(CASE WHEN raw_data:line IS NOT NULL THEN 1 ELSE 0 END) * 100 as avg_completeness_pct
FROM bronze.netsuite_journal_entries
WHERE _ingestion_timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
GROUP BY 1
ORDER BY 1 DESC;
```

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `mcp-server/src/connectors/netsuite.py` | NetSuite API connector (OAuth + SuiteQL) |
| `mcp-server/src/services/snowflake_netsuite_loader.py` | Sync orchestration |
| `snowflake-netsuite-setup.sql` | Bronze/Silver/Gold schema |
| `docs/NETSUITE_E2E_TESTING_ISSUES.md` | Complete diagnostic guide |
| `scripts/test-netsuite-e2e.sh` | Comprehensive test suite |
| `scripts/test-netsuite-suiteql.sh` | Quick SuiteQL test |

---

## Success Criteria

Your NetSuite integration is working correctly when:

✅ NetSuite connection test passes
✅ Bronze layer receives records with line items (>90% completeness)
✅ Silver layer processes records into line-level detail
✅ Gold layer shows aggregated financial metrics
✅ Backend API returns financial summary data
✅ Frontend displays charts, KPIs, and trends
✅ E2E latency is <5 minutes from sync trigger to frontend
✅ Data quality score >0.9 for recent syncs

---

**Questions?** See `docs/NETSUITE_E2E_TESTING_ISSUES.md` for detailed troubleshooting.

**Last Updated**: November 12, 2025
**Status**: Ready for Testing ✅
