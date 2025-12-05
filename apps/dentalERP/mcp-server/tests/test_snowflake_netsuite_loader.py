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


def test_pluralize_maps_to_correct_snowflake_tables():
    """Verify _pluralize() maps NetSuite record types to correct Snowflake table names"""
    loader = NetSuiteToSnowflakeLoader(tenant_id="test-tenant")

    # Mappings based on actual Snowflake table schema
    # Tables are named: NETSUITE_JOURNAL_ENTRIES, NETSUITE_ACCOUNTS, etc.
    expected_mappings = {
        "journalEntry": "journal_entries",     # NOT "journalentrys" or "journalentry"
        "account": "accounts",
        "invoice": "invoices",
        "customerPayment": "payments",          # Table: NETSUITE_PAYMENTS
        "vendorBill": "vendor_bills",          # NOT "vendorbills"
        "customer": "customers",
        "vendor": "vendors",
        "inventoryItem": "items",               # Table: NETSUITE_ITEMS
        "subsidiary": "subsidiaries"           # NOT "subsidiarys"
    }

    for record_type, expected_table in expected_mappings.items():
        actual_table = loader._pluralize(record_type)
        assert actual_table == expected_table, \
            f"_pluralize('{record_type}') returned '{actual_table}', expected '{expected_table}'"


def test_bulk_insert_uses_parse_json_for_variant_column():
    """Verify _bulk_insert_snowflake() wraps RAW_DATA column with PARSE_JSON()"""
    from unittest.mock import AsyncMock, MagicMock

    loader = NetSuiteToSnowflakeLoader(tenant_id="test-tenant")

    # Mock the Snowflake connector's execute_many method
    loader.snowflake = MagicMock()
    loader.snowflake.execute_many = AsyncMock()

    # Sample records with RAW_DATA column
    test_records = [
        {
            "ID": "12345",
            "RAW_DATA": '{"id": "12345", "amount": 100}',
            "CREATED_AT": "2025-01-01",
            "UPDATED_AT": "2025-01-01"
        }
    ]

    # Execute the bulk insert
    import asyncio
    asyncio.run(loader._bulk_insert_snowflake(
        table="bronze.netsuite_journal_entries",
        records=test_records
    ))

    # Verify execute_many was called
    assert loader.snowflake.execute_many.called, "execute_many should have been called"

    # Get the actual SQL statement that was used
    actual_sql = loader.snowflake.execute_many.call_args[0][0]

    # Verify PARSE_JSON() wrapper is present for RAW_DATA column
    # With MERGE pattern, the SQL should look like:
    # SELECT column1 as id, PARSE_JSON(column2) as raw_data, ...
    # NOT: SELECT column1 as id, column2 as raw_data, ...

    assert "PARSE_JSON" in actual_sql, \
        f"SQL statement should wrap RAW_DATA with PARSE_JSON(), but got: {actual_sql}"

    # Verify that PARSE_JSON wraps the column reference for RAW_DATA
    # The pattern should be: PARSE_JSON(column2) as raw_data (where column2 is RAW_DATA)
    import re
    assert re.search(r'PARSE_JSON\s*\(\s*column\d+\s*\)\s+as\s+raw_data', actual_sql, re.IGNORECASE), \
        f"SQL should contain 'PARSE_JSON(columnN) as raw_data' for RAW_DATA column, but got: {actual_sql}"


def test_bulk_insert_uses_merge_for_deduplication():
    """Verify bulk insert uses MERGE (upsert) instead of INSERT"""
    from unittest.mock import AsyncMock, MagicMock

    loader = NetSuiteToSnowflakeLoader(tenant_id="test-tenant")

    # Mock Snowflake connector
    loader.snowflake = MagicMock()
    loader.snowflake.execute_many = AsyncMock()

    # Sample records
    test_records = [
        {
            "ID": "123",
            "SYNC_ID": "sync-456",
            "TENANT_ID": "tenant-789",
            "RAW_DATA": '{"field": "value"}',
            "LAST_MODIFIED_DATE": "2025-01-01",
            "EXTRACTED_AT": "2025-01-01T00:00:00",
            "IS_DELETED": False
        }
    ]

    # Call bulk insert
    import asyncio
    asyncio.run(loader._bulk_insert_snowflake(
        table="BRONZE.NETSUITE_TEST",
        records=test_records
    ))

    # Verify SQL uses MERGE pattern
    actual_sql = loader.snowflake.execute_many.call_args[0][0]

    assert "MERGE INTO" in actual_sql, f"SQL should use MERGE, not INSERT. Got: {actual_sql}"
    assert "on t.id = s.id" in actual_sql.lower(), "MERGE should match on ID column"
    assert "WHEN MATCHED THEN UPDATE" in actual_sql, "MERGE should update existing"
    assert "WHEN NOT MATCHED THEN INSERT" in actual_sql, "MERGE should insert new"
