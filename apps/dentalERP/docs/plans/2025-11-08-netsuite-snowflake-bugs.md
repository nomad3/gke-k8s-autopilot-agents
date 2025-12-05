# NetSuite to Snowflake Bug Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 3 critical bugs blocking NetSuite data from reaching Snowflake Bronze layer

**Architecture:** Update `snowflake_netsuite_loader.py` to use correct NetSuite API record type names, map to correct Snowflake table names, and format VARIANT columns properly

**Tech Stack:** Python 3.11, FastAPI, Snowflake, NetSuite REST API v1, pytest

---

## Task 1: Fix NetSuite Record Type Names (Bug #1)

**Files:**
- Modify: `mcp-server/src/services/snowflake_netsuite_loader.py:25-35`
- Test: `mcp-server/tests/test_snowflake_netsuite_loader.py`

**Step 1: Write failing test for correct record types**

Create test file to verify NetSuite API compatibility:

```python
# File: mcp-server/tests/test_snowflake_netsuite_loader.py
import pytest
from src.services.snowflake_netsuite_loader import NetSuiteToSnowflakeLoader


def test_record_types_match_netsuite_api():
    """Verify record types use correct NetSuite REST API identifiers"""
    loader = NetSuiteToSnowflakeLoader(tenant_id="test-tenant")

    # These are the CORRECT NetSuite REST API v1 record type names
    expected_record_types = [
        "journalEntry",
        "account",
        "invoice",
        "customerPayment",  # NOT "payment"
        "vendorBill",
        "customer",
        "vendor",
        "inventoryItem",    # NOT "item"
        "subsidiary"
    ]

    assert loader.RECORD_TYPES == expected_record_types, \
        f"Record types mismatch. Got: {loader.RECORD_TYPES}"
```

**Step 2: Run test to verify it fails**

Run:
```bash
cd mcp-server
pytest tests/test_snowflake_netsuite_loader.py::test_record_types_match_netsuite_api -v
```

Expected output:
```
FAILED - AssertionError: Record types mismatch. Got: ['journalEntry', 'account', 'invoice', 'payment', ...]
```

**Step 3: Fix record type names**

Update `mcp-server/src/services/snowflake_netsuite_loader.py` lines 25-35:

```python
    RECORD_TYPES = [
        "journalEntry",
        "account",
        "invoice",
        "customerPayment",  # ✅ Changed from "payment"
        "vendorBill",
        "customer",
        "vendor",
        "inventoryItem",    # ✅ Changed from "item"
        "subsidiary"
    ]
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_snowflake_netsuite_loader.py::test_record_types_match_netsuite_api -v
```

Expected output:
```
PASSED
```

**Step 5: Commit**

```bash
git add mcp-server/src/services/snowflake_netsuite_loader.py mcp-server/tests/test_snowflake_netsuite_loader.py
git commit -m "fix(netsuite): correct record type names for REST API compatibility

- Change 'payment' to 'customerPayment' (correct API identifier)
- Change 'item' to 'inventoryItem' (correct API identifier)
- Add test to verify record types match NetSuite REST API v1"
```

---

## Task 2: Fix Table Name Mappings (Bug #2)

**Files:**
- Modify: `mcp-server/src/services/snowflake_netsuite_loader.py:281-294`
- Test: `mcp-server/tests/test_snowflake_netsuite_loader.py`

**Step 1: Write failing test for table name mappings**

Add to `mcp-server/tests/test_snowflake_netsuite_loader.py`:

```python
def test_pluralize_maps_to_correct_snowflake_tables():
    """Verify _pluralize() returns correct Snowflake table names"""
    loader = NetSuiteToSnowflakeLoader(tenant_id="test-tenant")

    # Expected Snowflake table name mappings (snake_case with underscores)
    expected_mappings = {
        "journalEntry": "journal_entries",      # NOT "journalentry"
        "account": "accounts",
        "invoice": "invoices",
        "customerPayment": "customer_payments", # NOT "payments"
        "vendorBill": "vendor_bills",
        "customer": "customers",
        "vendor": "vendors",
        "inventoryItem": "inventory_items",     # NOT "items"
        "subsidiary": "subsidiaries"
    }

    for record_type, expected_table in expected_mappings.items():
        actual_table = loader._pluralize(record_type)
        assert actual_table == expected_table, \
            f"Wrong table name for {record_type}: got '{actual_table}', expected '{expected_table}'"
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_snowflake_netsuite_loader.py::test_pluralize_maps_to_correct_snowflake_tables -v
```

Expected output:
```
FAILED - AssertionError: Wrong table name for journalEntry: got 'journalentry', expected 'journal_entries'
```

**Step 3: Fix _pluralize() method**

Update `mcp-server/src/services/snowflake_netsuite_loader.py` lines 281-294:

```python
    def _pluralize(self, word: str) -> str:
        """Convert NetSuite record type to Snowflake table name"""
        # Explicit mapping to match actual Snowflake Bronze layer table names
        mappings = {
            "journalEntry": "journal_entries",      # ✅ Fixed from "journalentry"
            "account": "accounts",
            "invoice": "invoices",
            "customerPayment": "customer_payments", # ✅ Fixed from "payments"
            "vendorBill": "vendor_bills",
            "customer": "customers",
            "vendor": "vendors",
            "inventoryItem": "inventory_items",     # ✅ Fixed from "items"
            "subsidiary": "subsidiaries"
        }
        return mappings.get(word, f"{word}s")
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_snowflake_netsuite_loader.py::test_pluralize_maps_to_correct_snowflake_tables -v
```

Expected output:
```
PASSED
```

**Step 5: Commit**

```bash
git add mcp-server/src/services/snowflake_netsuite_loader.py mcp-server/tests/test_snowflake_netsuite_loader.py
git commit -m "fix(netsuite): correct table name mappings for Snowflake

- Fix journalEntry -> journal_entries (was journalentry)
- Fix customerPayment -> customer_payments (was payments)
- Fix inventoryItem -> inventory_items (was items)
- Add test to verify all table name mappings"
```

---

## Task 3: Fix VARIANT Column Format (Bug #3)

**Files:**
- Modify: `mcp-server/src/services/snowflake_netsuite_loader.py:206-225`
- Test: `mcp-server/tests/test_snowflake_netsuite_loader.py`

**Step 1: Write failing test for PARSE_JSON() wrapper**

Add to `mcp-server/tests/test_snowflake_netsuite_loader.py`:

```python
def test_bulk_insert_uses_parse_json_for_variant_column():
    """Verify SQL INSERT wraps RAW_DATA with PARSE_JSON() for VARIANT type"""
    loader = NetSuiteToSnowflakeLoader(tenant_id="test-tenant")

    # Sample record with RAW_DATA column
    sample_records = [{
        "ID": "123",
        "SYNC_ID": "sync-456",
        "TENANT_ID": "tenant-789",
        "RAW_DATA": '{"field": "value"}',  # JSON string
        "LAST_MODIFIED_DATE": "2025-01-01",
        "EXTRACTED_AT": "2025-01-01T00:00:00",
        "IS_DELETED": False
    }]

    # Mock Snowflake connector to capture SQL
    class MockSnowflake:
        def __init__(self):
            self.last_sql = None
            self.last_params = None

        async def execute_many(self, sql, params):
            self.last_sql = sql
            self.last_params = params

    loader.snowflake = MockSnowflake()

    # Run bulk insert
    import asyncio
    asyncio.run(loader._bulk_insert_snowflake(
        table="BRONZE.NETSUITE_TEST",
        records=sample_records
    ))

    # Verify SQL uses PARSE_JSON() for RAW_DATA column
    assert "PARSE_JSON(%s)" in loader.snowflake.last_sql, \
        f"SQL should wrap RAW_DATA with PARSE_JSON(). Got: {loader.snowflake.last_sql}"
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_snowflake_netsuite_loader.py::test_bulk_insert_uses_parse_json_for_variant_column -v
```

Expected output:
```
FAILED - AssertionError: SQL should wrap RAW_DATA with PARSE_JSON()
```

**Step 3: Fix bulk insert to use PARSE_JSON()**

Update `mcp-server/src/services/snowflake_netsuite_loader.py` lines 206-225:

```python
    async def _bulk_insert_snowflake(self, table: str, records: List[Dict[str, Any]]):
        """Bulk insert records into Snowflake"""
        if not records:
            return

        # Build INSERT statement with %s placeholders for Snowflake
        columns = list(records[0].keys())

        # Special handling for RAW_DATA column (VARIANT type needs PARSE_JSON)
        placeholders = []
        for col in columns:
            if col == "RAW_DATA":
                placeholders.append("PARSE_JSON(%s)")  # ✅ Wrap JSON string with PARSE_JSON()
            else:
                placeholders.append("%s")

        placeholders_str = ", ".join(placeholders)
        column_list = ", ".join(columns)

        insert_sql = f"""
            INSERT INTO {table} ({column_list})
            VALUES ({placeholders_str})
        """

        # Convert records from dicts to tuples in correct column order
        record_tuples = [tuple(rec[col] for col in columns) for rec in records]

        # Execute bulk insert
        await self.snowflake.execute_many(insert_sql, record_tuples)
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_snowflake_netsuite_loader.py::test_bulk_insert_uses_parse_json_for_variant_column -v
```

Expected output:
```
PASSED
```

**Step 5: Commit**

```bash
git add mcp-server/src/services/snowflake_netsuite_loader.py mcp-server/tests/test_snowflake_netsuite_loader.py
git commit -m "fix(netsuite): wrap RAW_DATA with PARSE_JSON() for VARIANT column

- Add PARSE_JSON(%s) wrapper for RAW_DATA in bulk insert
- Fixes Snowflake type mismatch error (VARCHAR vs VARIANT)
- Add test to verify PARSE_JSON() is used in SQL statement"
```

---

## Task 4: Integration Test - End-to-End Sync

**Files:**
- Test: `mcp-server/tests/integration/test_netsuite_snowflake_sync.py`

**Step 1: Write integration test**

Create integration test file:

```python
# File: mcp-server/tests/integration/test_netsuite_snowflake_sync.py
import pytest
import os
from src.services.snowflake_netsuite_loader import NetSuiteToSnowflakeLoader


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Integration tests require RUN_INTEGRATION_TESTS=1"
)
async def test_sync_journal_entries_to_snowflake():
    """
    Integration test: Sync NetSuite journal entries to Snowflake Bronze

    Prerequisites:
    - NetSuite credentials configured in .env
    - Snowflake credentials configured in .env
    - Tenant with integrations set up
    """
    # Use default tenant (should have NetSuite + Snowflake configured)
    loader = NetSuiteToSnowflakeLoader(tenant_id=os.getenv("TEST_TENANT_ID", "default"))

    # Sync journal entries only (small dataset for testing)
    count = await loader.sync_record_type("journalEntry", incremental=False)

    assert count >= 0, "Sync should return non-negative count"

    # Verify data landed in Snowflake
    if loader.snowflake:
        result = await loader.snowflake.execute_query(
            "SELECT COUNT(*) FROM BRONZE.NETSUITE_JOURNAL_ENTRIES"
        )
        assert result[0][0] > 0, "Bronze table should have records"


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Integration tests require RUN_INTEGRATION_TESTS=1"
)
async def test_raw_data_is_queryable_variant():
    """
    Integration test: Verify RAW_DATA is stored as VARIANT and queryable
    """
    loader = NetSuiteToSnowflakeLoader(tenant_id=os.getenv("TEST_TENANT_ID", "default"))
    await loader.initialize()

    # Query RAW_DATA as VARIANT (should be able to extract JSON fields)
    result = await loader.snowflake.execute_query("""
        SELECT
            ID,
            RAW_DATA:id::string as netsuite_id,
            RAW_DATA:tranDate::string as transaction_date
        FROM BRONZE.NETSUITE_JOURNAL_ENTRIES
        LIMIT 1
    """)

    assert result, "Should be able to query VARIANT fields"
    assert result[0][1] is not None, "RAW_DATA:id should be extractable"
```

**Step 2: Run integration test (optional, requires credentials)**

Run:
```bash
# Set environment variables
export RUN_INTEGRATION_TESTS=1
export TEST_TENANT_ID=default
export SNOWFLAKE_ACCOUNT=your-account
export SNOWFLAKE_USER=your-user
export SNOWFLAKE_PASSWORD=your-password

# Run integration tests
pytest tests/integration/test_netsuite_snowflake_sync.py -v
```

Expected: Tests should pass if credentials are valid

**Step 3: Commit integration tests**

```bash
git add mcp-server/tests/integration/test_netsuite_snowflake_sync.py
git commit -m "test(netsuite): add end-to-end integration tests

- Test NetSuite to Snowflake sync flow
- Verify RAW_DATA is queryable as VARIANT
- Skip if RUN_INTEGRATION_TESTS not set"
```

---

## Task 5: Manual Verification

**Files:**
- None (manual testing only)

**Step 1: Start MCP server**

Run:
```bash
cd mcp-server
docker-compose up -d mcp-server
```

**Step 2: Trigger sync via API**

Run:
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

Expected output:
```json
{
  "sync_id": "...",
  "status": "in_progress",
  "record_types": ["journalEntry", "account"]
}
```

**Step 3: Check sync status**

Run:
```bash
curl http://localhost:8085/api/v1/netsuite/sync/status \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: default"
```

Expected output:
```json
{
  "status": "completed",
  "records_synced": {
    "journalEntry": 145,
    "account": 87
  }
}
```

**Step 4: Verify data in Snowflake Bronze**

Connect to Snowflake and run:

```sql
-- Check record counts
SELECT COUNT(*) FROM BRONZE.NETSUITE_JOURNAL_ENTRIES;
SELECT COUNT(*) FROM BRONZE.NETSUITE_ACCOUNTS;
SELECT COUNT(*) FROM BRONZE.NETSUITE_CUSTOMER_PAYMENTS;

-- Verify VARIANT data is queryable
SELECT
    ID,
    RAW_DATA:id::string as netsuite_id,
    RAW_DATA:tranDate::date as transaction_date,
    RAW_DATA:amount::number(18,2) as amount
FROM BRONZE.NETSUITE_JOURNAL_ENTRIES
LIMIT 5;
```

Expected: All queries should succeed without type errors

**Step 5: Run dbt transformations**

Run:
```bash
cd dbt/dentalerp
dbt run --select stg_financials
```

Expected output:
```
Completed successfully
```

**Step 6: Verify Silver layer**

Run in Snowflake:
```sql
SELECT
    COUNT(*) as total_records,
    MIN(transaction_date) as earliest,
    MAX(transaction_date) as latest
FROM BRONZE_SILVER.STG_FINANCIALS;
```

Expected: Data should flow from Bronze → Silver

**Step 7: Document results**

Create verification checklist:

```markdown
## Verification Results

- [ ] NetSuite sync triggered successfully
- [ ] Sync completed without errors
- [ ] Data appeared in Bronze tables (journal_entries, accounts, customer_payments, etc.)
- [ ] RAW_DATA queryable as VARIANT (no type mismatch errors)
- [ ] dbt transformations ran successfully
- [ ] Data flowed to Silver layer (stg_financials)

## Issues Found

(Document any issues encountered during testing)

## Next Steps

(List any follow-up tasks)
```

---

## Summary

**Total Commits:** 4
1. Fix record type names (Bug #1)
2. Fix table name mappings (Bug #2)
3. Fix VARIANT column format (Bug #3)
4. Add integration tests

**Testing Strategy:**
- Unit tests for each bug fix (TDD approach)
- Integration tests for end-to-end flow (optional, requires credentials)
- Manual verification via API and Snowflake queries

**Success Criteria:**
- All unit tests pass
- NetSuite sync completes without errors
- Data appears in Snowflake Bronze tables
- RAW_DATA is queryable as VARIANT
- dbt transformations run successfully
- Data flows to Silver layer

**Estimated Time:**
- Task 1: 10 minutes (fix + test)
- Task 2: 10 minutes (fix + test)
- Task 3: 15 minutes (fix + test)
- Task 4: 10 minutes (integration tests)
- Task 5: 15-30 minutes (manual verification)
- **Total: 60-75 minutes**

---

**Plan saved:** `docs/plans/2025-11-08-netsuite-snowflake-bugs.md`
**Ready for execution**
