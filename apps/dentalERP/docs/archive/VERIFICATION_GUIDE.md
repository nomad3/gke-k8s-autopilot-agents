# NetSuite to Snowflake Bug Fixes - Verification Guide

## Summary of Fixes

All 3 critical bugs have been fixed:

1. ✅ **Bug #1:** Corrected NetSuite record type names
   - `payment` → `customerPayment`
   - `item` → `inventoryItem`

2. ✅ **Bug #2:** Fixed table name mappings
   - `journalEntry` → `journal_entries` (was `journalentry`)
   - `customerPayment` → `payments` (was `customer_payments`)
   - `inventoryItem` → `items` (was `inventory_items`)

3. ✅ **Bug #3:** Added PARSE_JSON() wrapper for VARIANT columns
   - RAW_DATA column now properly parsed from JSON string to VARIANT type

## Verification Steps

### Prerequisites

1. **Environment Variables Set:**
   ```bash
   export MCP_API_KEY="your-mcp-api-key"
   export SNOWFLAKE_ACCOUNT="your-account"
   export SNOWFLAKE_USER="your-user"
   export SNOWFLAKE_PASSWORD="your-password"
   export SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
   export SNOWFLAKE_DATABASE="DENTAL_ERP_DW"
   ```

2. **Docker Compose Running:**
   ```bash
   cd /Users/nomade/Documents/GitHub/dentalERP
   docker-compose up -d
   ```

3. **Services Health Check:**
   ```bash
   curl http://localhost:8085/health  # MCP Server
   docker-compose logs -f mcp-server  # Check for errors
   ```

---

### Step 1: Trigger NetSuite Sync

Trigger a sync for journal entries and accounts (small datasets):

```bash
curl -X POST http://localhost:8085/api/v1/netsuite/sync/trigger \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: default" \
  -H "Content-Type: application/json" \
  -d '{
    "record_types": ["journalEntry", "account"],
    "full_sync": false
  }'
```

**Expected Response:**
```json
{
  "sync_id": "<uuid>",
  "status": "in_progress",
  "record_types": ["journalEntry", "account"]
}
```

---

### Step 2: Check Sync Status

Wait 30-60 seconds, then check status:

```bash
curl http://localhost:8085/api/v1/netsuite/sync/status \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: default"
```

**Expected Response:**
```json
{
  "status": "completed",
  "records_synced": {
    "journalEntry": 145,
    "account": 87
  },
  "errors": []
}
```

**Success Criteria:**
- ✅ Status is "completed" (not "failed")
- ✅ No errors in response
- ✅ Record counts > 0

**If Failed:**
- Check MCP server logs: `docker-compose logs mcp-server | tail -100`
- Look for NetSuite API errors or Snowflake errors
- Verify credentials are correct

---

### Step 3: Verify Data in Snowflake Bronze

Connect to Snowflake and run:

```sql
-- Check record counts
SELECT COUNT(*) as journal_entry_count
FROM BRONZE.NETSUITE_JOURNAL_ENTRIES;

SELECT COUNT(*) as account_count
FROM BRONZE.NETSUITE_ACCOUNTS;
```

**Expected:**
- Both queries return count > 0
- No "table not found" errors

---

### Step 4: Verify VARIANT Column Works

Test that RAW_DATA is queryable as VARIANT (Bug #3 fix):

```sql
-- Extract fields from JSON using VARIANT syntax
SELECT
    ID,
    RAW_DATA:id::string as netsuite_id,
    RAW_DATA:tranDate::date as transaction_date,
    RAW_DATA:amount::number(18,2) as amount
FROM BRONZE.NETSUITE_JOURNAL_ENTRIES
LIMIT 5;
```

**Expected:**
- Query executes successfully
- All 4 columns return data (not NULL)
- **NO ERROR:** "expecting VARIANT but got VARCHAR"

**Success Criteria:**
- ✅ Query returns 5 rows
- ✅ `netsuite_id` column is populated
- ✅ No type mismatch errors
- ✅ JSON fields are extractable

---

### Step 5: Test All Record Types

Trigger sync for all record types to verify all table name mappings:

```bash
curl -X POST http://localhost:8085/api/v1/netsuite/sync/trigger \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: default" \
  -H "Content-Type: application/json" \
  -d '{
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
    ],
    "full_sync": false
  }'
```

**Check sync status after ~2 minutes:**
```bash
curl http://localhost:8085/api/v1/netsuite/sync/status \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: default"
```

**Expected:**
- All 9 record types show `records_synced > 0`
- No errors for any record type

---

### Step 6: Verify Table Names (Bug #2 Fix)

Confirm data landed in correct tables:

```sql
-- Check that data is in the CORRECT tables
SELECT COUNT(*) FROM BRONZE.NETSUITE_PAYMENTS;        -- NOT customer_payments
SELECT COUNT(*) FROM BRONZE.NETSUITE_ITEMS;           -- NOT inventory_items
SELECT COUNT(*) FROM BRONZE.NETSUITE_JOURNAL_ENTRIES; -- NOT journalentry

-- These tables should NOT exist (old incorrect names)
SELECT COUNT(*) FROM BRONZE.NETSUITE_CUSTOMER_PAYMENTS; -- Should ERROR
SELECT COUNT(*) FROM BRONZE.NETSUITE_INVENTORY_ITEMS;   -- Should ERROR
SELECT COUNT(*) FROM BRONZE.NETSUITE_JOURNALENTRY;      -- Should ERROR
```

**Expected:**
- First 3 queries return count > 0 ✅
- Last 3 queries return "table does not exist" error ✅

---

### Step 7: Run dbt Transformations

Trigger dbt to transform Bronze → Silver:

```bash
# Option 1: Via API
curl -X POST http://localhost:8085/api/v1/dbt/run/stg_financials \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: default"

# Option 2: Direct dbt command
cd dbt/dentalerp
dbt run --select stg_financials
```

**Expected Output:**
```
Completed successfully

1 of 1 START sql table model bronze_silver.stg_financials ......... [RUN]
1 of 1 OK created sql table model bronze_silver.stg_financials .... [SUCCESS 1 in 3.45s]
```

**Success Criteria:**
- ✅ dbt runs without errors
- ✅ Model completes successfully
- ✅ No table not found errors

---

### Step 8: Verify Silver Layer

Confirm data transformed to Silver layer:

```sql
SELECT
    COUNT(*) as total_records,
    MIN(transaction_date) as earliest_date,
    MAX(transaction_date) as latest_date,
    SUM(amount) as total_amount
FROM BRONZE_SILVER.STG_FINANCIALS;
```

**Expected:**
- Query returns data (total_records > 0)
- Date range makes sense
- No NULLs in aggregates

---

## Integration Test (Optional)

If you have pytest and credentials configured:

```bash
cd mcp-server

# Set environment variables
export RUN_INTEGRATION_TESTS=true
export TEST_TENANT_ID=default

# Run integration tests
pytest tests/integration/test_netsuite_snowflake_sync.py -v
```

**Expected:**
- ✅ `test_sync_journal_entries_to_snowflake` PASSED
- ✅ `test_raw_data_is_queryable_variant` PASSED
- ✅ `test_record_type_table_mappings` PASSED

---

## Success Checklist

Complete this checklist to verify all fixes:

- [ ] NetSuite sync triggered successfully (Step 1)
- [ ] Sync completed without errors (Step 2)
- [ ] Data appears in Bronze tables (Step 3)
- [ ] RAW_DATA is queryable as VARIANT - no type errors (Step 4)
- [ ] All 9 record types sync successfully (Step 5)
- [ ] Data in correct tables (payments, items, journal_entries) (Step 6)
- [ ] dbt transformations run successfully (Step 7)
- [ ] Data flows to Silver layer (Step 8)
- [ ] Integration tests pass (optional)

---

## Troubleshooting

### Issue: "Table not found" error

**Cause:** Table name mapping incorrect

**Fix:** Verify Snowflake schema:
```sql
SHOW TABLES IN BRONZE LIKE 'NETSUITE_%';
```

Compare with mappings in `_pluralize()` method.

---

### Issue: "expecting VARIANT but got VARCHAR"

**Cause:** PARSE_JSON() wrapper not applied

**Fix:** Verify commit `0a5685c` is included:
```bash
git log --oneline | grep "PARSE_JSON"
```

Should show: `0a5685c fix: wrap RAW_DATA with PARSE_JSON()`

---

### Issue: NetSuite API error "Invalid record type"

**Cause:** Incorrect record type name

**Fix:** Verify commit `9eb5730` is included:
```bash
git log --oneline | grep "correct record type names"
```

Should show: `9eb5730 fix(netsuite): correct record type names`

---

### Issue: No data in Bronze tables

**Check:**
1. NetSuite credentials valid
2. Snowflake credentials valid
3. MCP server logs for errors
4. Network connectivity to NetSuite API

---

## Summary

All 3 bug fixes are complete and tested:

| Bug | Fix | Commit | Verified |
|-----|-----|--------|----------|
| #1 | Record type names | 9eb5730 | Unit test ✅ |
| #2 | Table name mappings | 1fdf0d1 | Unit test ✅ |
| #3 | VARIANT column format | 0a5685c | Unit test ✅ |

**Next Step:** Deploy to GCP VM and run verification steps in production environment.
