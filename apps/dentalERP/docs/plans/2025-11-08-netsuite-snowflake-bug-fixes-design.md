# NetSuite to Snowflake Bug Fixes Design

**Date:** 2025-11-08
**Status:** Validated
**Author:** Claude Code with superpowers:brainstorming

## Overview

Fix 3 critical bugs in `snowflake_netsuite_loader.py` that prevent NetSuite data from reaching Snowflake Bronze layer. Once fixed, the complete pipeline (NetSuite → Snowflake → dbt → Analytics) will be operational.

**Current Status:** 95% complete - authentication and API connectivity working in production

**Goal:** Enable end-to-end data flow from NetSuite to analytics dashboards

## Problem Statement

The NetSuite integration has three bugs in `/mcp-server/src/services/snowflake_netsuite_loader.py` that block data ingestion:

1. **Bug #1 (Lines 25-35):** Invalid NetSuite record type names
2. **Bug #2 (Lines 281-294):** Table name mapping mismatches
3. **Bug #3 (Line ~215):** VARIANT column type mismatch

All bugs prevent successful bulk inserts to Snowflake Bronze tables.

## Design

### Fix #1: Correct NetSuite Record Type Names

**Location:** Lines 25-35 in `NETSUITE_RECORD_TYPES` constant

**Problem:** Code uses "payment" and "item" which don't exist in NetSuite REST API v1

**Solution:** Use correct NetSuite record type identifiers

**Change:**
```python
# BEFORE
NETSUITE_RECORD_TYPES = [
    "journalEntry",
    "account",
    "customer",
    "vendor",
    "invoice",
    "payment",      # ❌ Invalid - NetSuite doesn't recognize this
    "vendorBill",
    "item",         # ❌ Invalid - too generic
    "employee"
]

# AFTER
NETSUITE_RECORD_TYPES = [
    "journalEntry",
    "account",
    "customer",
    "vendor",
    "invoice",
    "customerPayment",  # ✅ Correct REST API identifier
    "vendorBill",
    "inventoryItem",    # ✅ Correct REST API identifier
    "employee"
]
```

**Impact:** NetSuite API will successfully return payment and inventory item records

### Fix #2: Table Name Mapping

**Location:** Lines 281-294 in `_pluralize()` method

**Problem:** Simple `.lower() + "s"` doesn't match Snowflake table naming conventions
- "journalEntry" → "journalentry**s**" but table is "journal_**entries**"
- No snake_case conversion (camelCase → snake_case)

**Solution:** Explicit mapping dictionary with correct Snowflake table names

**Change:**
```python
# BEFORE
def _pluralize(record_type: str) -> str:
    """Convert record type to plural table name."""
    return record_type.lower() + "s"  # ❌ Too naive

# AFTER
def _pluralize(record_type: str) -> str:
    """Map NetSuite record types to Snowflake table names."""
    mapping = {
        "journalEntry": "journal_entries",
        "account": "accounts",
        "customer": "customers",
        "vendor": "vendors",
        "invoice": "invoices",
        "customerPayment": "customer_payments",
        "vendorBill": "vendor_bills",
        "inventoryItem": "inventory_items",
        "employee": "employees"
    }
    return mapping.get(record_type, record_type.lower() + "s")
```

**Impact:** INSERT statements will target correct Snowflake table names

### Fix #3: VARIANT Column Format

**Location:** Line ~215 in `bulk_insert_to_snowflake()` method

**Problem:** Code inserts JSON string directly to VARIANT column without parsing
- Snowflake error: "expecting VARIANT but got VARCHAR for column RAW_DATA"

**Solution:** Wrap JSON placeholder with `PARSE_JSON()` SQL function

**Change:**
```python
# BEFORE
INSERT INTO bronze.{table_name} (
    id,
    raw_data,           # ❌ Inserting string to VARIANT column
    created_at,
    updated_at
) VALUES (%s, %s, %s, %s)

# AFTER
INSERT INTO bronze.{table_name} (
    id,
    raw_data,           # ✅ Parse JSON string to VARIANT
    created_at,
    updated_at
) VALUES (%s, PARSE_JSON(%s), %s, %s)
```

**Impact:** Snowflake will accept JSON data and store it as queryable VARIANT type

## Testing Strategy

### Test Environment
- Local development: `http://localhost:8085`
- Production: `https://mcp.agentprovision.com`

### Test Flow

**1. Trigger Sync**
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

**2. Monitor Status**
```bash
curl http://localhost:8085/api/v1/netsuite/sync/status \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: default"
```

Expected: `{"status": "completed", "records_synced": {...}}`

**3. Verify Bronze Layer**
```sql
-- Check record counts
SELECT COUNT(*) FROM bronze.journal_entries;
SELECT COUNT(*) FROM bronze.accounts;
SELECT COUNT(*) FROM bronze.customer_payments;
SELECT COUNT(*) FROM bronze.inventory_items;

-- Verify VARIANT data is queryable
SELECT
    id,
    raw_data:id::string as netsuite_id,
    raw_data:tranDate::date as transaction_date,
    raw_data:amount::number as amount
FROM bronze.journal_entries
LIMIT 5;
```

**4. Run dbt Transformations**
```bash
cd dbt/dentalerp
dbt run --select stg_financials
```

**5. Verify Silver Layer**
```sql
SELECT
    COUNT(*) as total_records,
    MIN(transaction_date) as earliest,
    MAX(transaction_date) as latest
FROM bronze_silver.stg_financials;
```

## Success Criteria

- ✅ NetSuite sync completes without errors
- ✅ Data appears in all 9 Bronze tables
- ✅ RAW_DATA column is queryable as VARIANT (not VARCHAR error)
- ✅ Table names match Snowflake schema
- ✅ dbt transformations run successfully
- ✅ Data flows to Silver layer (stg_financials)
- ✅ No type mismatch errors in Snowflake

## Rollback Plan

If bugs cause issues:
1. Revert `snowflake_netsuite_loader.py` to previous version
2. Check MCP server logs: `docker-compose logs mcp-server`
3. Verify NetSuite API connectivity still works: `POST /api/v1/netsuite/sync/test-connection`

## Implementation Notes

- All fixes are in one file: `mcp-server/src/services/snowflake_netsuite_loader.py`
- No database schema changes required
- No API contract changes
- Estimated fix time: 15 minutes
- Estimated test time: 15-30 minutes

## References

- NetSuite Connector: `mcp-server/src/connectors/netsuite.py` (510 lines, working)
- Sync Orchestrator: `mcp-server/src/services/netsuite_sync_orchestrator.py` (110 lines, working)
- Integration Guide: `docs/NETSUITE_INTEGRATION_FINAL.md`
- Snowflake Schema: `snowflake-setup-updated.sql`

## Future Enhancements (Out of Scope)

- Scheduled automatic syncs (APScheduler)
- Additional dbt models beyond stg_financials
- Data quality tests in dbt
- Error recovery UI
- Monitoring and alerting

---

**Design validated:** 2025-11-08
**Ready for implementation:** Yes
