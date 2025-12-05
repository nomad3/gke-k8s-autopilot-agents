"""
NetSuite to Snowflake Data Loader
Fetches data from NetSuite and loads into Snowflake Bronze layer
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from ..connectors.netsuite import NetSuiteConnector
from ..connectors.snowflake import SnowflakeConnector
from ..services.warehouse_router import WarehouseRouter
from ..services.integration_router import IntegrationRouter
from ..core.tenant import TenantContext
from ..core.database import get_db_context
from ..utils.logger import logger
from sqlalchemy import text


class NetSuiteToSnowflakeLoader:
    """Load NetSuite data directly into Snowflake Bronze layer"""

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

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.netsuite: Optional[NetSuiteConnector] = None
        self.snowflake: Optional[SnowflakeConnector] = None

    async def initialize(self):
        """Initialize connectors"""
        # Set tenant context for this operation
        from ..models.tenant import Tenant
        from uuid import UUID

        # Get tenant from database
        async with get_db_context() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Tenant).where(Tenant.id == UUID(self.tenant_id))
            )
            tenant = result.scalar_one_or_none()

            if not tenant:
                raise Exception(f"Tenant {self.tenant_id} not found")

            # Set tenant context
            TenantContext.set_tenant(tenant)

            # Get NetSuite connector via integration router
            integration_router = IntegrationRouter()
            self.netsuite = await integration_router.get_connector(
                integration_type="netsuite"
            )

            # Get Snowflake connector via warehouse router
            warehouse_router = WarehouseRouter()
            self.snowflake = await warehouse_router.get_connector(
                warehouse_type="snowflake"
            )

            if not self.netsuite:
                raise Exception(f"NetSuite connector not found for tenant {self.tenant_id}")

            if not self.snowflake:
                raise Exception(f"Snowflake connector not found for tenant {self.tenant_id}")

    async def sync_all_record_types(
        self,
        incremental: bool = True,
        record_types: Optional[List[str]] = None,
        from_date: Optional[str] = None,
        limit: Optional[int] = 100
    ) -> Dict[str, int]:
        """
        Sync NetSuite record types for all subsidiaries

        Args:
            incremental: If True, only fetch records changed since last sync
            record_types: List of specific record types to sync. If None, syncs all.
            from_date: Optional start date (YYYY-MM-DD). Overrides incremental last_sync.
            limit: Max records per subsidiary

        Returns:
            Dict with record counts per type
        """
        await self.initialize()

        # SIMPLIFIED APPROACH: For journal entries, query ALL transactions without subsidiary filter
        # NetSuite SuiteQL returns data for ALL subsidiaries in one query
        # We'll parse out the subsidiary from the raw data
        results = {}

        # Determine which record types to sync
        types_to_sync = record_types if record_types else self.RECORD_TYPES
        logger.info(f"Record types to sync: {types_to_sync}")

        # For journal entries, use simplified single-query approach
        for record_type in types_to_sync:
            try:
                # Build filters WITHOUT subsidiary (query ALL at once)
                filters = {
                    "limit": limit or 1000
                }

                # Date filter logic
                if from_date:
                    filters["from_date"] = from_date
                elif incremental:
                    # Get last sync time (without subsidiary_id - global last sync)
                    last_sync = await self._get_last_sync_time(record_type, None)
                    if last_sync:
                        filters["from_date"] = last_sync.isoformat()[:10]

                logger.info(f"Syncing {record_type} for ALL subsidiaries (filters={filters})")

                # Fetch and sync (subsidiary_id=None means query all)
                count = await self.sync_record_type(
                    record_type,
                    subsidiary_id=None,  # Query ALL subsidiaries at once
                    filters=filters
                )

                results[record_type] = count
                logger.info(f"✅ Synced {count} {record_type} records total")

            except Exception as e:
                logger.error(f"Failed to sync {record_type}: {e}")
                results[record_type] = 0
                continue

        # Cleanup: Close connector sessions to prevent leaks
        try:
            if self.netsuite:
                await self.netsuite.close()
            if self.snowflake:
                await self.snowflake.close()
            logger.info("[Cleanup] Closed all connector sessions")
        except Exception as e:
            logger.warning(f"[Cleanup] Error closing sessions: {e}")

        return results

    async def sync_record_type(
        self,
        record_type: str,
        subsidiary_id: Optional[str] = None,
        filters: Optional[Dict] = None
    ) -> int:
        """
        Fetch from NetSuite and load to Snowflake Bronze

        Args:
            record_type: 'journalEntry', 'account', 'invoice', etc.
            subsidiary_id: Optional subsidiary ID to filter by
            filters: Optional pre-built filters (with subsidiary, incremental, etc.)

        Returns:
            Number of records synced
        """
        sync_id = str(uuid.uuid4())

        # Use provided filters or build new
        if filters is None:
            filters = {"limit": 100}
            if subsidiary_id:
                filters["subsidiary"] = subsidiary_id

        # NOTE: NetSuite REST API does NOT support 'fields' parameter on list endpoints
        # List queries only return {id, links} regardless of parameters
        # Full details with line items must be fetched via detail endpoint (Phase 2 below)

        logger.info(
            f"Starting {record_type} sync for subsidiary {subsidiary_id} "
            f"(filters={filters})"
        )

        # Fetch from NetSuite with pagination
        all_records = []
        offset = 0
        page_size = filters.get("limit", 100)

        while True:
            # Build pagination filters
            page_filters = filters.copy()
            page_filters["limit"] = page_size
            page_filters["offset"] = offset

            # Fetch page
            response = await self.netsuite.fetch_data(record_type, page_filters)

            if not response.success:
                raise Exception(f"NetSuite fetch failed: {response.error}")

            all_records.extend(response.data)

            # Check if more pages
            if not response.metadata.get("has_more", False):
                break

            offset += page_size

            # Rate limit protection
            await asyncio.sleep(0.5)

        if not all_records:
            logger.info(f"No new {record_type} records to sync for subsidiary {subsidiary_id}")
            return 0

        # PHASE 2: For journalEntry, use SuiteQL to bypass broken User Event Scripts
        # SuiteQL queries Transaction/TransactionLine tables directly
        # Does NOT trigger User Event Scripts that block REST Record API
        if record_type == "journalEntry":
            logger.info(f"Fetching journal entries via SuiteQL (bypasses User Event Scripts)...")

            # Use SuiteQL instead of REST Record API
            # This avoids the broken VendorInvoiceDistribution script
            try:
                suiteql_entries = await self.netsuite.fetch_journal_entries_via_suiteql(
                    subsidiary_id=subsidiary_id,
                    from_date=filters.get("from_date"),  # Use the from_date field directly
                    limit=filters.get("limit", 100)
                )

                logger.info(f"✅ SuiteQL returned {len(suiteql_entries)} journal entries with line items")

                # Replace REST API records with SuiteQL records
                all_records = suiteql_entries

            except Exception as e:
                logger.error(f"SuiteQL fallback failed: {e}, trying REST API...")
                # Fall back to REST Record API if SuiteQL fails
                logger.info(f"Fetching full details for {len(all_records)} journal entries (with line items)...")

                detailed_records = []
                failed_count = 0

                for i, record in enumerate(all_records):
                    internal_id = record.get("id") or record.get("internalId")

                    if not internal_id:
                        logger.warning(f"Journal entry {i+1} has no ID, skipping")
                        continue

                    # Fetch full details including line items
                    detail = await self.netsuite.fetch_journal_entry_detail(internal_id)

                    if detail and "line" in detail:
                        detailed_records.append(detail)
                        if (i + 1) % 10 == 0:
                            logger.info(f"  Progress: {i+1}/{len(all_records)} journal entries fetched")
                    else:
                        failed_count += 1
                        logger.warning(f"  Journal entry {internal_id} missing line items")

                    # Rate limiting: 0.5s between detail fetches
                    await asyncio.sleep(0.5)

                logger.info(
                    f"Fetched details for {len(detailed_records)} journal entries "
                    f"({failed_count} failed or missing line items)"
                )

                # Replace summary records with detailed records
                all_records = detailed_records

        # Prepare for Snowflake insert
        bronze_records = []
        for record in all_records:
            bronze_records.append({
                "ID": record.get("id") or record.get("internalId"),
                "SUBSIDIARY_ID": subsidiary_id,  # NEW FIELD
                "SYNC_ID": sync_id,
                "TENANT_ID": self.tenant_id,
                "RAW_DATA": json.dumps(record),  # Keep as JSON string for SELECT PARSE_JSON pattern
                "LAST_MODIFIED_DATE": record.get("lastModifiedDate"),
                "EXTRACTED_AT": datetime.utcnow().isoformat(),
                "IS_DELETED": False
            })

        # Insert to Snowflake Bronze (bulk insert)
        table_name = f"BRONZE.NETSUITE_{self._pluralize(record_type).upper()}"

        await self._bulk_insert_snowflake(
            table=table_name,
            records=bronze_records
        )

        # Update sync state
        await self._update_sync_state(
            record_type=record_type,
            status='success',
            records_synced=len(bronze_records)
        )

        logger.info(
            f"✅ Synced {len(bronze_records)} {record_type} records to {table_name}"
        )

        return len(bronze_records)

    async def _bulk_insert_snowflake(self, table: str, records: List[Dict[str, Any]]):
        """Bulk insert/update records using MERGE to prevent duplicates"""
        if not records:
            return

        columns = list(records[0].keys())
        column_list = ", ".join(columns)

        # Build source SELECT with PARSE_JSON for RAW_DATA
        select_columns = []
        for i, col in enumerate(columns, 1):
            if col.upper() == "RAW_DATA":
                select_columns.append(f"PARSE_JSON(column{i}) as {col.lower()}")
            else:
                select_columns.append(f"column{i} as {col.lower()}")

        select_list = ", ".join(select_columns)
        placeholders = ", ".join(["%s" for _ in columns])

        # Build UPDATE SET clause (all columns except ID)
        update_columns = [col for col in columns if col.upper() != "ID"]
        update_set = ", ".join([f"{col} = s.{col.lower()}" for col in update_columns])

        # Use MERGE for upsert (prevents duplicates)
        merge_sql = f"""
            MERGE INTO {table} t
            USING (
                SELECT {select_list}
                FROM VALUES({placeholders})
            ) s
            ON t.ID = s.id
            WHEN MATCHED THEN UPDATE SET
                {update_set}
            WHEN NOT MATCHED THEN INSERT
                ({column_list})
            VALUES ({', '.join(['s.' + col.lower() for col in columns])})
        """

        # Convert records to tuples
        record_tuples = [tuple(rec[col] for col in columns) for rec in records]

        # Execute bulk merge
        await self.snowflake.execute_many(merge_sql, record_tuples)

    async def _get_last_sync_time(self, record_type: str, subsidiary_id: Optional[str] = None) -> Optional[datetime]:
        """Get last successful sync timestamp for record type and subsidiary"""
        async with get_db_context() as session:
            # Note: For now, we track sync state per record_type only (not per subsidiary)
            # This ensures we don't miss records if subsidiary config changes
            result = await session.execute(
                text("""
                    SELECT last_sync_timestamp
                    FROM netsuite_sync_state
                    WHERE tenant_id = :tenant_id
                      AND record_type = :record_type
                      AND last_sync_status = 'success'
                """),
                {"tenant_id": self.tenant_id, "record_type": record_type}
            )
            row = result.fetchone()
            return row[0] if row else None

    async def _update_sync_state(
        self,
        record_type: str,
        status: str,
        records_synced: int = 0,
        error_message: Optional[str] = None
    ):
        """Update sync state in PostgreSQL"""
        async with get_db_context() as session:
            await session.execute(
                text("""
                    INSERT INTO netsuite_sync_state (
                        tenant_id, record_type, last_sync_timestamp,
                        last_sync_status, records_synced, error_message, updated_at
                    )
                    VALUES (
                        :tenant_id, :record_type, :timestamp,
                        :status, :count, :error, NOW()
                    )
                    ON CONFLICT (tenant_id, record_type)
                    DO UPDATE SET
                        last_sync_timestamp = :timestamp,
                        last_sync_status = :status,
                        records_synced = :count,
                        error_message = :error,
                        retry_count = CASE WHEN :status = 'success' THEN 0 ELSE netsuite_sync_state.retry_count + 1 END,
                        updated_at = NOW()
                """),
                {
                    "tenant_id": self.tenant_id,
                    "record_type": record_type,
                    "timestamp": datetime.utcnow(),
                    "status": status,
                    "count": records_synced,
                    "error": error_message
                }
            )

    def _pluralize(self, word: str) -> str:
        """Convert record type to Snowflake table name"""
        # Map NetSuite record types to actual Snowflake table names
        # Tables use plural form with underscores: netsuite_journal_entries
        mapping = {
            "journalEntry": "journal_entries",
            "account": "accounts",
            "invoice": "invoices",
            "customerPayment": "customer_payments",
            "vendorBill": "vendor_bills",
            "customer": "customers",
            "vendor": "vendors",
            "inventoryItem": "inventory_items",
            "subsidiary": "subsidiaries"
        }
        return mapping.get(word, word.lower())
