# NetSuite Integration Implementation Plan

**Date**: 2025-01-07
**Author**: Claude Code
**Status**: Ready for Implementation
**Estimated Time**: 6-8 hours

## Overview

Integrate NetSuite ERP with DentalERP MCP Server to sync financial and operational data to Snowflake for AI-powered business intelligence.

## Architecture

```
NetSuite API (OAuth 1.0a TBA)
    ↓
MCP Server (FastAPI)
    ↓
Snowflake Bronze Layer (raw JSON)
    ↓
dbt Transformations
    ↓
Snowflake Silver Layer (cleaned, SCD Type 2)
    ↓
Snowflake Gold Layer (analytics + AI features)
    ↓
Analytics APIs + AI Insights
```

## Implementation Tasks

### Task 1: Add NetSuite Credentials to Environment

**File**: `mcp-server/.env`

**Action**: Add the following lines to the existing `.env` file:

```bash
# NetSuite Integration Credentials
NETSUITE_ACCOUNT_ID=7048582
NETSUITE_CONSUMER_KEY=827945f2ee3aabc5a5388059ad117a6ab21ee46dcb54c8ce59d0448c42bca07f
NETSUITE_CONSUMER_SECRET=6c832dc6dcb4138337f7c9474f9903fe2fb29cee38890599f2a94db4d245075a
NETSUITE_TOKEN_ID=72d6982da7d037b56c219489e8436dcf09da3f3d07d1af2dd0a0d8e5333f2754
NETSUITE_TOKEN_SECRET=bdf84b3943895f0ce6560b58b6dc7df0957abefef2718b8e1ca7720cf232a116
```

**Verification**:
```bash
cd mcp-server
grep NETSUITE .env
# Should show all 5 NetSuite variables
```

**GCP Production**:
```bash
# SSH to GCP VM
ssh root@34.69.75.118

# Add same credentials
cd /opt/dental-erp/mcp-server
nano .env
# Paste NetSuite credentials
# Save and exit (Ctrl+X, Y, Enter)

# Verify
grep NETSUITE .env
```

---

### Task 2: Create PostgreSQL Migration for Sync State

**File**: `mcp-server/migrations/003_netsuite_sync_state.sql`

**Action**: Create new migration file with this exact content:

```sql
-- Track sync state for each NetSuite record type per tenant
CREATE TABLE IF NOT EXISTS netsuite_sync_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    record_type VARCHAR(50) NOT NULL,
    last_sync_timestamp TIMESTAMP,
    last_sync_status VARCHAR(20) DEFAULT 'pending',
    records_synced INTEGER DEFAULT 0,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    next_retry_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, record_type)
);

CREATE INDEX idx_netsuite_sync_tenant ON netsuite_sync_state(tenant_id);
CREATE INDEX idx_netsuite_sync_next_retry ON netsuite_sync_state(next_retry_at)
    WHERE last_sync_status = 'failed';
CREATE INDEX idx_netsuite_sync_record_type ON netsuite_sync_state(record_type);

COMMENT ON TABLE netsuite_sync_state IS 'Tracks NetSuite sync state for incremental syncs';
```

**Verification**:
```bash
# Local: Run migration
docker exec dentalerp-postgres-1 psql -U postgres -d mcp -f /path/to/migrations/003_netsuite_sync_state.sql

# Or apply via Docker
docker cp mcp-server/migrations/003_netsuite_sync_state.sql dentalerp-postgres-1:/tmp/
docker exec dentalerp-postgres-1 psql -U postgres -d mcp -f /tmp/003_netsuite_sync_state.sql

# Verify table exists
docker exec dentalerp-postgres-1 psql -U postgres -d mcp -c "\d netsuite_sync_state"
```

---

### Task 3: Create Snowflake Schema Setup

**File**: `snowflake-netsuite-setup.sql` (in project root)

**Action**: Create new file with complete Snowflake schema:

```sql
-- ============================================================================
-- NetSuite Integration - Snowflake Schema Setup
-- Run this in Snowflake UI after connecting to DENTAL_ERP_DW database
-- ============================================================================

USE DATABASE DENTAL_ERP_DW;
USE WAREHOUSE COMPUTE_WH;
USE ROLE ACCOUNTADMIN;

-- ============================================================================
-- BRONZE LAYER: Raw NetSuite Data
-- ============================================================================

CREATE TABLE IF NOT EXISTS bronze.netsuite_journal_entries (
    id VARCHAR(50),
    sync_id VARCHAR(36),
    tenant_id VARCHAR(50),
    raw_data VARIANT,
    last_modified_date TIMESTAMP,
    extracted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    _ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS bronze.netsuite_accounts (
    id VARCHAR(50),
    sync_id VARCHAR(36),
    tenant_id VARCHAR(50),
    raw_data VARIANT,
    last_modified_date TIMESTAMP,
    extracted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    _ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS bronze.netsuite_invoices (
    id VARCHAR(50),
    sync_id VARCHAR(36),
    tenant_id VARCHAR(50),
    raw_data VARIANT,
    last_modified_date TIMESTAMP,
    extracted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    _ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS bronze.netsuite_payments (
    id VARCHAR(50),
    sync_id VARCHAR(36),
    tenant_id VARCHAR(50),
    raw_data VARIANT,
    last_modified_date TIMESTAMP,
    extracted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    _ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS bronze.netsuite_vendor_bills (
    id VARCHAR(50),
    sync_id VARCHAR(36),
    tenant_id VARCHAR(50),
    raw_data VARIANT,
    last_modified_date TIMESTAMP,
    extracted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    _ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS bronze.netsuite_customers (
    id VARCHAR(50),
    sync_id VARCHAR(36),
    tenant_id VARCHAR(50),
    raw_data VARIANT,
    last_modified_date TIMESTAMP,
    extracted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    _ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS bronze.netsuite_vendors (
    id VARCHAR(50),
    sync_id VARCHAR(36),
    tenant_id VARCHAR(50),
    raw_data VARIANT,
    last_modified_date TIMESTAMP,
    extracted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    _ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS bronze.netsuite_items (
    id VARCHAR(50),
    sync_id VARCHAR(36),
    tenant_id VARCHAR(50),
    raw_data VARIANT,
    last_modified_date TIMESTAMP,
    extracted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    _ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS bronze.netsuite_subsidiaries (
    id VARCHAR(50),
    sync_id VARCHAR(36),
    tenant_id VARCHAR(50),
    raw_data VARIANT,
    last_modified_date TIMESTAMP,
    extracted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    _ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- ============================================================================
-- SILVER LAYER: Cleaned & Typed
-- ============================================================================

CREATE TABLE IF NOT EXISTS silver.dim_netsuite_accounts (
    account_key BIGINT AUTOINCREMENT PRIMARY KEY,
    account_id VARCHAR(50),
    account_number VARCHAR(50),
    account_name VARCHAR(255),
    account_type VARCHAR(50),
    account_category VARCHAR(100),
    parent_account_id VARCHAR(50),
    parent_account_name VARCHAR(255),
    is_summary_account BOOLEAN,
    is_inactive BOOLEAN,
    description TEXT,
    valid_from TIMESTAMP,
    valid_to TIMESTAMP,
    is_current BOOLEAN,
    tenant_id VARCHAR(50),
    _dbt_updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS silver.dim_netsuite_customers (
    customer_key BIGINT AUTOINCREMENT PRIMARY KEY,
    customer_id VARCHAR(50),
    entity_id VARCHAR(100),
    company_name VARCHAR(255),
    customer_type VARCHAR(50),
    email VARCHAR(255),
    phone VARCHAR(50),
    billing_address VARIANT,
    subsidiary_id VARCHAR(50),
    subsidiary_name VARCHAR(255),
    is_inactive BOOLEAN,
    valid_from TIMESTAMP,
    valid_to TIMESTAMP,
    is_current BOOLEAN,
    tenant_id VARCHAR(50),
    _dbt_updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS silver.dim_netsuite_vendors (
    vendor_key BIGINT AUTOINCREMENT PRIMARY KEY,
    vendor_id VARCHAR(50),
    entity_id VARCHAR(100),
    company_name VARCHAR(255),
    vendor_type VARCHAR(50),
    email VARCHAR(255),
    phone VARCHAR(50),
    billing_address VARIANT,
    subsidiary_id VARCHAR(50),
    subsidiary_name VARCHAR(255),
    is_inactive BOOLEAN,
    valid_from TIMESTAMP,
    valid_to TIMESTAMP,
    is_current BOOLEAN,
    tenant_id VARCHAR(50),
    _dbt_updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS silver.fact_netsuite_transactions (
    transaction_key BIGINT AUTOINCREMENT PRIMARY KEY,
    transaction_id VARCHAR(50),
    internal_id VARCHAR(50),
    transaction_type VARCHAR(50),
    transaction_date DATE,
    posting_period VARCHAR(20),
    amount DECIMAL(18,2),
    debit_amount DECIMAL(18,2),
    credit_amount DECIMAL(18,2),
    currency VARCHAR(3),
    exchange_rate DECIMAL(10,4),
    account_key BIGINT,
    customer_key BIGINT,
    vendor_key BIGINT,
    subsidiary_id VARCHAR(50),
    department_id VARCHAR(50),
    class_id VARCHAR(50),
    location_id VARCHAR(50),
    status VARCHAR(20),
    memo TEXT,
    created_date TIMESTAMP,
    last_modified_date TIMESTAMP,
    tenant_id VARCHAR(50),
    _dbt_updated_at TIMESTAMP
);

-- ============================================================================
-- GOLD LAYER: Analytics + AI
-- ============================================================================

CREATE TABLE IF NOT EXISTS gold.daily_financial_metrics (
    metric_date DATE,
    tenant_id VARCHAR(50),
    subsidiary VARCHAR(100),
    total_revenue DECIMAL(18,2),
    total_expenses DECIMAL(18,2),
    net_income DECIMAL(18,2),
    gross_profit DECIMAL(18,2),
    gross_margin_pct DECIMAL(5,2),
    cash_receipts DECIMAL(18,2),
    cash_disbursements DECIMAL(18,2),
    net_cash_flow DECIMAL(18,2),
    accounts_receivable DECIMAL(18,2),
    accounts_payable DECIMAL(18,2),
    pms_production DECIMAL(18,2),
    netsuite_revenue DECIMAL(18,2),
    variance DECIMAL(18,2),
    variance_pct DECIMAL(5,2),
    is_anomaly BOOLEAN,
    anomaly_score FLOAT,
    anomaly_reason TEXT,
    day_of_week INTEGER,
    revenue_7d_avg DECIMAL(18,2),
    revenue_30d_avg DECIMAL(18,2),
    revenue_trend VARCHAR(20),
    daily_summary TEXT,
    data_quality_score FLOAT,
    _dbt_updated_at TIMESTAMP,
    PRIMARY KEY (metric_date, tenant_id, subsidiary)
);

CREATE TABLE IF NOT EXISTS gold.ai_financial_insights (
    insight_id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(50),
    insight_date DATE,
    insight_type VARCHAR(50),
    title VARCHAR(255),
    description TEXT,
    severity VARCHAR(20),
    confidence_score FLOAT,
    affected_metrics VARIANT,
    reasoning TEXT,
    recommended_actions VARIANT,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    _dbt_updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gold.financial_forecasts (
    forecast_id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(50),
    metric_name VARCHAR(100),
    forecast_date DATE,
    forecast_horizon_days INTEGER,
    forecast_value DECIMAL(18,2),
    forecast_lower_bound DECIMAL(18,2),
    forecast_upper_bound DECIMAL(18,2),
    model_type VARCHAR(50),
    actual_value DECIMAL(18,2),
    forecast_error DECIMAL(18,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    _dbt_updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gold.revenue_reconciliation (
    reconciliation_date DATE,
    tenant_id VARCHAR(50),
    practice_location VARCHAR(100),
    pms_production DECIMAL(18,2),
    pms_collections DECIMAL(18,2),
    netsuite_revenue DECIMAL(18,2),
    netsuite_cash_received DECIMAL(18,2),
    production_vs_revenue_variance DECIMAL(18,2),
    variance_reason TEXT,
    reconciliation_status VARCHAR(20),
    _dbt_updated_at TIMESTAMP,
    PRIMARY KEY (reconciliation_date, tenant_id, practice_location)
);

SELECT 'NetSuite Snowflake schema created successfully!' as status;
```

**Verification**:
```bash
# Log into Snowflake UI (https://app.snowflake.com)
# Run the SQL file
# Verify tables exist:

USE DATABASE DENTAL_ERP_DW;
SHOW TABLES IN SCHEMA BRONZE LIKE '%netsuite%';
SHOW TABLES IN SCHEMA SILVER LIKE '%netsuite%';
SHOW TABLES IN SCHEMA GOLD;
```

---

### Task 4: Create NetSuiteToSnowflakeLoader Service

**File**: `mcp-server/src/services/snowflake_netsuite_loader.py`

**Action**: Create new Python service file:

```python
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
from ..core.database import get_session
from ..utils.logger import logger
from sqlalchemy import text


class NetSuiteToSnowflakeLoader:
    """Load NetSuite data directly into Snowflake Bronze layer"""

    RECORD_TYPES = [
        "journalEntry",
        "account",
        "invoice",
        "payment",
        "vendorBill",
        "customer",
        "vendor",
        "item",
        "subsidiary"
    ]

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.netsuite: Optional[NetSuiteConnector] = None
        self.snowflake: Optional[SnowflakeConnector] = None

    async def initialize(self):
        """Initialize connectors"""
        # Get NetSuite connector via integration router
        integration_router = IntegrationRouter()
        self.netsuite = await integration_router.get_connector(
            tenant_id=self.tenant_id,
            integration_type="netsuite"
        )

        # Get Snowflake connector via warehouse router
        warehouse_router = WarehouseRouter()
        self.snowflake = await warehouse_router.get_connector(
            tenant_id=self.tenant_id,
            warehouse_type="snowflake"
        )

        if not self.netsuite:
            raise Exception(f"NetSuite connector not found for tenant {self.tenant_id}")

        if not self.snowflake:
            raise Exception(f"Snowflake connector not found for tenant {self.tenant_id}")

    async def sync_all_record_types(self, incremental: bool = True) -> Dict[str, int]:
        """
        Sync all NetSuite record types to Snowflake

        Args:
            incremental: If True, only fetch records changed since last sync

        Returns:
            Dict with record counts per type
        """
        await self.initialize()

        results = {}

        for record_type in self.RECORD_TYPES:
            try:
                count = await self.sync_record_type(record_type, incremental)
                results[record_type] = count
                logger.info(f"Synced {count} {record_type} records")
            except Exception as e:
                logger.error(f"Failed to sync {record_type}: {e}")
                results[record_type] = -1  # Indicates error

                # Update sync state with error
                await self._update_sync_state(
                    record_type=record_type,
                    status='failed',
                    error_message=str(e)
                )

        return results

    async def sync_record_type(
        self,
        record_type: str,
        incremental: bool = True
    ) -> int:
        """
        Fetch from NetSuite and load to Snowflake Bronze

        Args:
            record_type: 'journalEntry', 'account', 'invoice', etc.
            incremental: Use lastModifiedDate filter

        Returns:
            Number of records synced
        """
        sync_id = str(uuid.uuid4())

        # Get last sync time for incremental
        last_sync = None
        if incremental:
            last_sync = await self._get_last_sync_time(record_type)

        logger.info(
            f"Starting {record_type} sync (incremental={incremental}, "
            f"last_sync={last_sync})"
        )

        # Fetch from NetSuite with pagination
        all_records = []
        offset = 0
        page_size = 100  # NetSuite recommended

        while True:
            filters = {"limit": page_size, "offset": offset}

            if last_sync:
                # Incremental: only fetch changed records
                filters["q"] = f'lastModifiedDate > "{last_sync.isoformat()}"'

            # Fetch page
            response = await self.netsuite.fetch_data(record_type, filters)

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
            logger.info(f"No new {record_type} records to sync")
            return 0

        # Prepare for Snowflake insert
        bronze_records = []
        for record in all_records:
            bronze_records.append({
                "ID": record.get("id") or record.get("internalId"),
                "SYNC_ID": sync_id,
                "TENANT_ID": self.tenant_id,
                "RAW_DATA": json.dumps(record),
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
        """Bulk insert records into Snowflake"""
        if not records:
            return

        # Build INSERT statement
        columns = list(records[0].keys())
        placeholders = ", ".join([f":{col}" for col in columns])
        column_list = ", ".join(columns)

        insert_sql = f"""
            INSERT INTO {table} ({column_list})
            VALUES ({placeholders})
        """

        # Execute bulk insert
        await self.snowflake.execute_many(insert_sql, records)

    async def _get_last_sync_time(self, record_type: str) -> Optional[datetime]:
        """Get last successful sync timestamp for record type"""
        async with get_session() as session:
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
        async with get_session() as session:
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
            await session.commit()

    def _pluralize(self, word: str) -> str:
        """Simple pluralize (good enough for NetSuite record types)"""
        mappings = {
            "journalEntry": "journal_entries",
            "account": "accounts",
            "invoice": "invoices",
            "payment": "payments",
            "vendorBill": "vendor_bills",
            "customer": "customers",
            "vendor": "vendors",
            "item": "items",
            "subsidiary": "subsidiaries"
        }
        return mappings.get(word, f"{word}s")
```

**Verification**: Run type check and syntax validation:
```bash
cd mcp-server
python -m py_compile src/services/snowflake_netsuite_loader.py
```

---

### Task 5: Create NetSuiteSyncOrchestrator Service

**File**: `mcp-server/src/services/netsuite_sync_orchestrator.py`

**Content**: See full implementation in design document above (Part 6).

**Verification**:
```bash
cd mcp-server
python -m py_compile src/services/netsuite_sync_orchestrator.py
```

---

### Task 6: Create NetSuite Sync API Endpoints

**File**: `mcp-server/src/api/netsuite_sync.py`

**Action**: Create new API endpoint file:

```python
"""
NetSuite Sync API Endpoints
Manual trigger and status endpoints
"""

from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

from ..services.netsuite_sync_orchestrator import NetSuiteSyncOrchestrator
from ..services.snowflake_netsuite_loader import NetSuiteToSnowflakeLoader
from ..core.tenant import TenantContext
from ..core.security import verify_api_key
from ..utils.logger import logger


router = APIRouter(prefix="/api/v1/netsuite", tags=["netsuite"])


class SyncRequest(BaseModel):
    full_sync: bool = False
    record_types: Optional[list[str]] = None


class SyncResponse(BaseModel):
    sync_id: str
    status: str
    message: str
    started_at: datetime


@router.post("/sync/trigger", response_model=SyncResponse)
async def trigger_sync(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    authorization: str = Header(...),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """
    Manually trigger NetSuite sync

    Args:
        full_sync: If True, ignore last sync time (full refresh)
        record_types: Optional list of specific record types to sync
    """
    # Verify API key
    await verify_api_key(authorization)

    # Get tenant
    tenant = TenantContext.get_tenant()
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant not found")

    tenant_id = str(tenant.id)

    # Start sync in background
    orchestrator = NetSuiteSyncOrchestrator()

    sync_id = f"manual_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    async def run_sync():
        try:
            await orchestrator.sync_tenant(
                tenant_id=tenant_id,
                incremental=not request.full_sync
            )
        except Exception as e:
            logger.error(f"Sync failed: {e}")

    background_tasks.add_task(run_sync)

    return SyncResponse(
        sync_id=sync_id,
        status="started",
        message=f"Sync started for tenant {tenant.tenant_code}",
        started_at=datetime.utcnow()
    )


@router.get("/sync/status")
async def get_sync_status(
    authorization: str = Header(...),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """Get current sync status for tenant"""
    await verify_api_key(authorization)

    tenant = TenantContext.get_tenant()
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant not found")

    # Query sync state from database
    from ..core.database import get_session
    from sqlalchemy import text

    async with get_session() as session:
        result = await session.execute(
            text("""
                SELECT record_type, last_sync_timestamp, last_sync_status,
                       records_synced, error_message, retry_count
                FROM netsuite_sync_state
                WHERE tenant_id = :tenant_id
                ORDER BY last_sync_timestamp DESC NULLS LAST
            """),
            {"tenant_id": str(tenant.id)}
        )

        rows = result.fetchall()

        sync_statuses = []
        for row in rows:
            sync_statuses.append({
                "record_type": row[0],
                "last_sync": row[1].isoformat() if row[1] else None,
                "status": row[2],
                "records_synced": row[3],
                "error": row[4],
                "retry_count": row[5]
            })

        return {
            "tenant_code": tenant.tenant_code,
            "sync_statuses": sync_statuses
        }


@router.post("/sync/test-connection")
async def test_netsuite_connection(
    authorization: str = Header(...),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """Test NetSuite connection for tenant"""
    await verify_api_key(authorization)

    tenant = TenantContext.get_tenant()
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant not found")

    loader = NetSuiteToSnowflakeLoader(str(tenant.id))

    try:
        await loader.initialize()

        # Test connection by fetching 1 subsidiary
        response = await loader.netsuite.fetch_data("subsidiary", {"limit": 1})

        if response.success:
            return {
                "status": "success",
                "message": "NetSuite connection successful",
                "sample_data": response.data[0] if response.data else None
            }
        else:
            return {
                "status": "failed",
                "message": response.error
            }
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Verification**:
```bash
cd mcp-server
python -m py_compile src/api/netsuite_sync.py
```

---

### Task 7: Register NetSuite API Router

**File**: `mcp-server/src/main.py`

**Action**: Add NetSuite router registration to the main FastAPI app.

Find the section where routers are registered (likely around line 30-50) and add:

```python
from .api import netsuite_sync

# ... existing router registrations ...

app.include_router(netsuite_sync.router)
```

**Verification**:
```bash
cd mcp-server
python -m py_compile src/main.py
```

---

### Task 8: Update Tenant Integration with NetSuite

**Action**: Add NetSuite integration to the default tenant in the database.

```bash
# Local development
docker exec dentalerp-postgres-1 psql -U postgres -d mcp << 'EOSQL'
INSERT INTO tenant_integrations (
    id, tenant_id, integration_type, integration_config, status, created_at
)
SELECT
    gen_random_uuid(),
    id,
    'netsuite',
    jsonb_build_object(
        'account_id', '7048582',
        'consumer_key', '827945f2ee3aabc5a5388059ad117a6ab21ee46dcb54c8ce59d0448c42bca07f',
        'consumer_secret', '6c832dc6dcb4138337f7c9474f9903fe2fb29cee38890599f2a94db4d245075a',
        'token_id', '72d6982da7d037b56c219489e8436dcf09da3f3d07d1af2dd0a0d8e5333f2754',
        'token_secret', 'bdf84b3943895f0ce6560b58b6dc7df0957abefef2718b8e1ca7720cf232a116'
    ),
    'active',
    NOW()
FROM tenants
WHERE tenant_code = 'default'
ON CONFLICT DO NOTHING;
EOSQL

# Verify
docker exec dentalerp-postgres-1 psql -U postgres -d mcp -c \
  "SELECT integration_type, status FROM tenant_integrations WHERE integration_type = 'netsuite';"
```

---

### Task 9: Test NetSuite Connection

**Action**: Test the NetSuite connection via API:

```bash
# Get MCP API key from environment
export MCP_API_KEY="dev-mcp-api-key-change-in-production-min-32-chars"

# Test connection
curl -X POST http://localhost:8085/api/v1/netsuite/sync/test-connection \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: default" \
  -H "Content-Type: application/json"

# Expected response:
# {
#   "status": "success",
#   "message": "NetSuite connection successful",
#   "sample_data": { ... subsidiary data ... }
# }
```

---

### Task 10: Run Initial Full Sync

**Action**: Trigger initial full sync to populate Snowflake:

```bash
# Trigger sync
curl -X POST http://localhost:8085/api/v1/netsuite/sync/trigger \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: default" \
  -H "Content-Type: application/json" \
  -d '{"full_sync": true}'

# Monitor sync status
curl http://localhost:8085/api/v1/netsuite/sync/status \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: default"

# Check MCP logs
docker-compose logs -f mcp-server
```

---

### Task 11: Verify Data in Snowflake

**Action**: Check that data landed in Bronze layer:

```sql
-- In Snowflake UI
USE DATABASE DENTAL_ERP_DW;

-- Check record counts
SELECT 'accounts' as table_name, COUNT(*) as records FROM bronze.netsuite_accounts
UNION ALL
SELECT 'customers', COUNT(*) FROM bronze.netsuite_customers
UNION ALL
SELECT 'vendors', COUNT(*) FROM bronze.netsuite_vendors
UNION ALL
SELECT 'invoices', COUNT(*) FROM bronze.netsuite_invoices
UNION ALL
SELECT 'payments', COUNT(*) FROM bronze.netsuite_payments
UNION ALL
SELECT 'journal_entries', COUNT(*) FROM bronze.netsuite_journal_entries;

-- Inspect sample data
SELECT * FROM bronze.netsuite_accounts LIMIT 5;
```

---

### Task 12: Deploy to Production (GCP VM)

**Action**: Deploy to GCP VM:

```bash
# SSH to GCP
ssh root@34.69.75.118

# Navigate to project
cd /opt/dental-erp

# Pull latest code
git pull origin main

# Rebuild MCP server
docker-compose --profile production build mcp-server-prod

# Restart services
docker-compose --profile production up -d mcp-server-prod

# Run migration
docker exec dental-erp_postgres_1 psql -U postgres -d mcp \
  -f /app/migrations/003_netsuite_sync_state.sql

# Add tenant integration (same SQL as Task 8)

# Check logs
docker-compose logs -f mcp-server-prod

# Test connection
curl -X POST https://mcp.agentprovision.com/api/v1/netsuite/sync/test-connection \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: default"
```

---

## Summary

**Deliverables**:
1. ✅ NetSuite credentials in `.env` files (local + GCP)
2. ✅ PostgreSQL `netsuite_sync_state` table
3. ✅ Snowflake Bronze/Silver/Gold schema
4. ✅ `NetSuiteToSnowflakeLoader` service
5. ✅ `NetSuiteSyncOrchestrator` service
6. ✅ NetSuite sync API endpoints
7. ✅ Tenant integration configuration
8. ✅ Initial data sync completed
9. ✅ Production deployment

**Next Steps** (Phase 2):
- Create dbt models for Silver/Gold transformations
- Set up scheduler for 15-min incremental syncs
- Build AI analytics endpoints
- Create frontend dashboards

**Estimated Time**: 6-8 hours
