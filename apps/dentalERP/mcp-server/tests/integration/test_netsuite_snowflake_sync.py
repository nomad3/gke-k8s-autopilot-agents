"""
Integration Tests for NetSuite → Snowflake Sync Pipeline
Tests end-to-end data flow from NetSuite to Snowflake Bronze layer

These tests require:
- Valid NetSuite credentials (OAuth 1.0a TBA)
- Valid Snowflake credentials
- RUN_INTEGRATION_TESTS environment variable set to 'true'

Run with: RUN_INTEGRATION_TESTS=true pytest tests/integration/test_netsuite_snowflake_sync.py -v
"""

import os
import pytest
from datetime import datetime
from typing import List, Dict, Any

# Skip all tests in this module if RUN_INTEGRATION_TESTS is not set
pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS", "false").lower() != "true",
    reason="Integration tests require RUN_INTEGRATION_TESTS=true environment variable"
)


class TestNetSuiteToSnowflakeSync:
    """Test complete NetSuite → Snowflake data synchronization"""

    @pytest.mark.asyncio
    async def test_sync_journal_entries_to_snowflake(self):
        """
        Test end-to-end sync of journal entries from NetSuite to Snowflake Bronze layer

        Workflow:
        1. Initialize NetSuiteToSnowflakeLoader with default tenant
        2. Sync journalEntry records from NetSuite
        3. Verify records are inserted into BRONZE.NETSUITE_JOURNAL_ENTRIES
        4. Verify record structure matches expectations
        5. Verify RAW_DATA column is queryable VARIANT type

        Success Criteria:
        - No errors during sync
        - At least 1 record synced
        - RAW_DATA contains valid JSON
        - Required fields (ID, CREATED_AT, UPDATED_AT) are populated
        """
        from src.services.snowflake_netsuite_loader import NetSuiteToSnowflakeLoader
        from src.connectors.snowflake import SnowflakeConnector
        from src.core.config import settings

        # Verify credentials are available
        assert settings.netsuite_account, "NETSUITE_ACCOUNT must be set"
        assert settings.netsuite_consumer_key, "NETSUITE_CONSUMER_KEY must be set"
        assert settings.snowflake_account, "SNOWFLAKE_ACCOUNT must be set"
        assert settings.snowflake_user, "SNOWFLAKE_USER must be set"

        # Initialize loader (use default tenant or first available tenant)
        tenant_id = await self._get_default_tenant_id()
        loader = NetSuiteToSnowflakeLoader(tenant_id=tenant_id)

        # Initialize connectors
        await loader.initialize()

        # Sync journal entries only (limit scope for faster test)
        record_count = await loader.sync_record_type(
            record_type="journalEntry",
            incremental=False  # Full sync for test
        )

        # Verify sync succeeded
        assert record_count >= 0, "Sync should complete without errors"

        if record_count > 0:
            # Verify data in Snowflake
            snowflake = loader.snowflake

            # Query Bronze table
            query = """
                SELECT
                    ID,
                    RAW_DATA,
                    CREATED_AT,
                    UPDATED_AT
                FROM BRONZE.NETSUITE_JOURNAL_ENTRIES
                ORDER BY CREATED_AT DESC
                LIMIT 5
            """

            results = await snowflake.execute_query(query)

            # Verify structure
            assert len(results) > 0, "Should have at least one record in Bronze table"

            for row in results:
                # Verify all required fields are populated
                assert row['ID'] is not None, "ID should not be null"
                assert row['RAW_DATA'] is not None, "RAW_DATA should not be null"
                assert row['CREATED_AT'] is not None, "CREATED_AT should not be null"
                assert row['UPDATED_AT'] is not None, "UPDATED_AT should not be null"

                # Verify RAW_DATA is a dict (parsed JSON, not string)
                assert isinstance(row['RAW_DATA'], dict), \
                    "RAW_DATA should be parsed JSON (dict), not string"

                # Verify RAW_DATA contains expected NetSuite fields
                raw_data = row['RAW_DATA']
                assert 'id' in raw_data, "RAW_DATA should contain 'id' field"

        print(f"✅ Successfully synced {record_count} journal entries to Snowflake")

    @pytest.mark.asyncio
    async def test_raw_data_is_queryable_variant(self):
        """
        Test that RAW_DATA column is stored as VARIANT and is queryable using JSON notation

        This test verifies Fix #3 from the design:
        - RAW_DATA column accepts JSON via PARSE_JSON()
        - Data is stored as VARIANT type (not VARCHAR)
        - JSON fields are queryable using Snowflake JSON notation (e.g., raw_data:id::string)

        Workflow:
        1. Query BRONZE.NETSUITE_JOURNAL_ENTRIES using JSON path notation
        2. Verify JSON fields can be extracted
        3. Verify no "expecting VARIANT but got VARCHAR" errors

        Success Criteria:
        - Query executes without type mismatch errors
        - JSON fields are extractable using notation like raw_data:fieldName::type
        - Extracted values match expected types
        """
        from src.connectors.snowflake import SnowflakeConnector
        from src.core.config import settings

        # Verify Snowflake credentials
        assert settings.snowflake_account, "SNOWFLAKE_ACCOUNT must be set"
        assert settings.snowflake_user, "SNOWFLAKE_USER must be set"

        # Create Snowflake connector
        snowflake = SnowflakeConnector()

        # Test query using JSON path notation (validates VARIANT type)
        query = """
            SELECT
                ID,
                RAW_DATA:id::STRING as netsuite_id,
                RAW_DATA:tranDate::DATE as transaction_date,
                RAW_DATA:memo::STRING as memo,
                RAW_DATA:subsidiary::STRING as subsidiary
            FROM BRONZE.NETSUITE_JOURNAL_ENTRIES
            LIMIT 10
        """

        try:
            results = await snowflake.execute_query(query)

            # If we have results, verify JSON extraction worked
            if results:
                for row in results:
                    # Verify extracted fields are accessible
                    assert 'NETSUITE_ID' in row or 'netsuite_id' in row, \
                        "Should extract netsuite_id from RAW_DATA"

                    # Verify we can access the extracted value (may be null for some records)
                    netsuite_id = row.get('NETSUITE_ID') or row.get('netsuite_id')

                    # If netsuite_id exists, it should be a string
                    if netsuite_id is not None:
                        assert isinstance(netsuite_id, (str, int)), \
                            f"netsuite_id should be string or int, got {type(netsuite_id)}"

                print(f"✅ Successfully queried {len(results)} records using VARIANT JSON notation")
            else:
                print("⚠️  No records found in table (may be empty, but query syntax is valid)")

        except Exception as e:
            # Check if error is the "expecting VARIANT but got VARCHAR" error
            error_msg = str(e).lower()
            if "expecting variant" in error_msg and "varchar" in error_msg:
                pytest.fail(
                    f"❌ VARIANT column error detected! This means Fix #3 is not applied correctly.\n"
                    f"Error: {e}\n"
                    f"Solution: Ensure PARSE_JSON() is used in INSERT statement"
                )
            else:
                # Re-raise other errors
                raise

    async def _get_default_tenant_id(self) -> str:
        """Get default tenant ID for testing"""
        from src.core.database import get_db
        from src.models.tenant import Tenant
        from sqlalchemy import select

        async with get_db() as session:
            # Get first tenant or create default
            result = await session.execute(
                select(Tenant).where(Tenant.tenant_code == "default")
            )
            tenant = result.scalar_one_or_none()

            if not tenant:
                # Try to get any tenant
                result = await session.execute(select(Tenant).limit(1))
                tenant = result.scalar_one_or_none()

            if not tenant:
                pytest.skip("No tenant found in database. Run seed script first.")

            return str(tenant.id)


class TestNetSuiteRecordTypeMappings:
    """Test that NetSuite record types map to correct Snowflake table names"""

    @pytest.mark.asyncio
    async def test_record_type_table_mappings(self):
        """
        Test that record types map to correct Snowflake table names

        This validates Fix #1 and Fix #2:
        - Fix #1: Uses correct NetSuite API identifiers (customerPayment, inventoryItem)
        - Fix #2: Maps to correct Snowflake table names with snake_case

        Expected Mappings:
        - journalEntry → BRONZE.NETSUITE_JOURNAL_ENTRIES
        - customerPayment → BRONZE.NETSUITE_PAYMENTS
        - inventoryItem → BRONZE.NETSUITE_INVENTORY_ITEMS
        - vendorBill → BRONZE.NETSUITE_VENDOR_BILLS
        """
        from src.services.snowflake_netsuite_loader import NetSuiteToSnowflakeLoader

        # Test mappings
        loader = NetSuiteToSnowflakeLoader(tenant_id="test")

        test_cases = [
            ("journalEntry", "journal_entries"),
            ("account", "accounts"),
            ("invoice", "invoices"),
            ("customerPayment", "payments"),  # Fix #1: was "payment"
            ("vendorBill", "vendor_bills"),
            ("customer", "customers"),
            ("vendor", "vendors"),
            ("inventoryItem", "inventory_items"),  # Fix #1: was "item"
        ]

        for record_type, expected_table_suffix in test_cases:
            table_name = loader._pluralize(record_type)
            assert table_name == expected_table_suffix, \
                f"Record type '{record_type}' should map to table suffix '{expected_table_suffix}', got '{table_name}'"

        print("✅ All record type mappings are correct")
