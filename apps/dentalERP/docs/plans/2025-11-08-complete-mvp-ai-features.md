# Complete MVP AI Features Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete Silvercreek MVP by fixing duplication, enabling automated syncs, and implementing all AI features using Snowflake-native architecture

**Architecture:** Snowflake handles all heavy computation (ML.FORECAST, Z-scores, aggregations), MCP provides thin API layer with GPT-4 text generation only

**Tech Stack:** Snowflake ML, dbt, FastAPI, APScheduler, OpenAI GPT-4, Slack webhooks, SMTP

---

## Task 1: Fix NetSuite Data Duplication

**Files:**
- Modify: `mcp-server/src/services/snowflake_netsuite_loader.py:206-236`
- Create: `scripts/cleanup_netsuite_duplicates.sql`
- Test: `mcp-server/tests/test_snowflake_netsuite_loader.py`

### Step 1: Write test for MERGE upsert behavior

Add to `mcp-server/tests/test_snowflake_netsuite_loader.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

def test_bulk_insert_uses_merge_for_deduplication():
    """Verify bulk insert uses MERGE (upsert) instead of INSERT"""
    from src.services.snowflake_netsuite_loader import NetSuiteToSnowflakeLoader

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
    assert "ON t.id = s.id" in actual_sql.lower(), "MERGE should match on ID column"
    assert "WHEN MATCHED THEN UPDATE" in actual_sql, "MERGE should update existing"
    assert "WHEN NOT MATCHED THEN INSERT" in actual_sql, "MERGE should insert new"
```

### Step 2: Run test to verify it fails

Run:
```bash
cd mcp-server
pytest tests/test_snowflake_netsuite_loader.py::test_bulk_insert_uses_merge_for_deduplication -v
```

Expected output:
```
FAILED - AssertionError: SQL should use MERGE, not INSERT
```

### Step 3: Implement MERGE upsert in _bulk_insert_snowflake

Modify `mcp-server/src/services/snowflake_netsuite_loader.py` lines 206-236:

```python
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
            {update_set},
            updated_at = CURRENT_TIMESTAMP()
        WHEN NOT MATCHED THEN INSERT
            ({column_list})
        VALUES ({', '.join(['s.' + col.lower() for col in columns])})
    """

    # Convert records to tuples
    record_tuples = [tuple(rec[col] for col in columns) for rec in records]

    # Execute bulk merge
    await self.snowflake.execute_many(merge_sql, record_tuples)
```

### Step 4: Run test to verify it passes

Run:
```bash
pytest tests/test_snowflake_netsuite_loader.py::test_bulk_insert_uses_merge_for_deduplication -v
```

Expected output:
```
PASSED
```

### Step 5: Create cleanup script for existing duplicates

Create `scripts/cleanup_netsuite_duplicates.sql`:

```sql
-- Cleanup existing NetSuite duplicate records
-- Keeps most recent record (by extracted_at), deletes older duplicates

-- Journal Entries
DELETE FROM bronze.netsuite_journal_entries
WHERE (id, extracted_at) NOT IN (
    SELECT id, MAX(extracted_at)
    FROM bronze.netsuite_journal_entries
    GROUP BY id
);

-- Accounts
DELETE FROM bronze.netsuite_accounts
WHERE (id, extracted_at) NOT IN (
    SELECT id, MAX(extracted_at)
    FROM bronze.netsuite_accounts
    GROUP BY id
);

-- Vendor Bills
DELETE FROM bronze.netsuite_vendor_bills
WHERE (id, extracted_at) NOT IN (
    SELECT id, MAX(extracted_at)
    FROM bronze.netsuite_vendor_bills
    GROUP BY id
);

-- Customers
DELETE FROM bronze.netsuite_customers
WHERE (id, extracted_at) NOT IN (
    SELECT id, MAX(extracted_at)
    FROM bronze.netsuite_customers
    GROUP BY id
);

-- Vendors
DELETE FROM bronze.netsuite_vendors
WHERE (id, extracted_at) NOT IN (
    SELECT id, MAX(extracted_at)
    FROM bronze.netsuite_vendors
    GROUP BY id
);

-- Subsidiaries
DELETE FROM bronze.netsuite_subsidiaries
WHERE (id, extracted_at) NOT IN (
    SELECT id, MAX(extracted_at)
    FROM bronze.netsuite_subsidiaries
    GROUP BY id
);

-- Verify cleanup
SELECT 'netsuite_journal_entries' as table_name, COUNT(*) as total, COUNT(DISTINCT id) as distinct_ids FROM bronze.netsuite_journal_entries
UNION ALL
SELECT 'netsuite_accounts', COUNT(*), COUNT(DISTINCT id) FROM bronze.netsuite_accounts
UNION ALL
SELECT 'netsuite_vendor_bills', COUNT(*), COUNT(DISTINCT id) FROM bronze.netsuite_vendor_bills
UNION ALL
SELECT 'netsuite_customers', COUNT(*), COUNT(DISTINCT id) FROM bronze.netsuite_customers
UNION ALL
SELECT 'netsuite_vendors', COUNT(*), COUNT(DISTINCT id) FROM bronze.netsuite_vendors
UNION ALL
SELECT 'netsuite_subsidiaries', COUNT(*), COUNT(DISTINCT id) FROM bronze.netsuite_subsidiaries;
```

### Step 6: Commit MERGE upsert implementation

```bash
git add mcp-server/src/services/snowflake_netsuite_loader.py \
        mcp-server/tests/test_snowflake_netsuite_loader.py \
        scripts/cleanup_netsuite_duplicates.sql

git commit -m "fix(netsuite): implement MERGE upsert to prevent duplicate records

- Replace INSERT with MERGE pattern in _bulk_insert_snowflake()
- Match on ID column, update if exists, insert if new
- Add test to verify MERGE usage
- Add cleanup script to remove existing duplicates

Fixes: 25,052 duplicate records (5x inflation from test syncs)
Expected result: ~6,263 unique records after cleanup"
```

---

## Task 2: Add APScheduler for Automated Syncs

**Files:**
- Modify: `mcp-server/src/main.py:1-50`
- Modify: `mcp-server/requirements.txt`
- Create: `mcp-server/src/scheduler/jobs.py`

### Step 1: Add APScheduler to requirements.txt

Modify `mcp-server/requirements.txt`, add line:

```
APScheduler==3.10.4
```

### Step 2: Install dependency

Run:
```bash
cd mcp-server
pip install APScheduler==3.10.4
```

Expected: Package installed successfully

### Step 3: Create scheduler jobs module

Create `mcp-server/src/scheduler/jobs.py`:

```python
"""
Scheduled background jobs for data synchronization and alerting
"""

from ..utils.logger import logger
from ..services.netsuite_sync_orchestrator import sync_all_tenants
from ..services.alerts import get_alert_service
from ..services.forecasting import get_forecasting_service


async def sync_netsuite_full():
    """Daily full NetSuite sync (scheduled 2am)"""
    logger.info("Starting scheduled NetSuite full sync")
    try:
        result = await sync_all_tenants(full_sync=True)
        logger.info(f"Scheduled full sync completed: {result}")
    except Exception as e:
        logger.error(f"Scheduled full sync failed: {e}", exc_info=True)


async def sync_netsuite_incremental():
    """Incremental NetSuite sync (every 4 hours)"""
    logger.info("Starting scheduled NetSuite incremental sync")
    try:
        result = await sync_all_tenants(full_sync=False)
        logger.info(f"Scheduled incremental sync completed: {result}")
    except Exception as e:
        logger.error(f"Scheduled incremental sync failed: {e}", exc_info=True)


async def check_and_send_alerts():
    """Check for KPI alerts and send notifications (hourly)"""
    logger.info("Starting scheduled alert check")
    try:
        from ..services.alerts import AlertChannel

        alert_service = get_alert_service()
        alerts = await alert_service.check_kpi_alerts()

        for alert in alerts:
            # Check deduplication
            if not alert_service.should_deduplicate(alert, window_hours=24):
                # Send to Slack and Email
                await alert_service.send_alert(
                    alert,
                    channels=[AlertChannel.SLACK, AlertChannel.EMAIL]
                )

        logger.info(f"Alert check completed: {len(alerts)} alerts processed")

    except Exception as e:
        logger.error(f"Alert check failed: {e}", exc_info=True)


async def send_weekly_insights():
    """Generate and email weekly AI insights (Monday 9am)"""
    logger.info("Starting weekly insights generation")
    try:
        forecasting = get_forecasting_service()
        insights = await forecasting.generate_insights()

        # Send via email
        alert_service = get_alert_service()
        await alert_service.send_alert(
            alert={
                "severity": "info",
                "alert_message": f"Weekly Insights:\n\n{insights}",
                "practice_name": "All Practices"
            },
            channels=[AlertChannel.EMAIL]
        )

        logger.info("Weekly insights sent successfully")

    except Exception as e:
        logger.error(f"Weekly insights failed: {e}", exc_info=True)
```

### Step 4: Add scheduler to main.py lifespan

Modify `mcp-server/src/main.py`, update lifespan function:

```python
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from .scheduler import jobs


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown logic"""

    # Startup
    logger.info("Starting MCP Server...")

    # Initialize scheduler
    scheduler = AsyncIOScheduler()

    # Job 1: Daily NetSuite full sync at 2am
    scheduler.add_job(
        jobs.sync_netsuite_full,
        CronTrigger(hour=2, minute=0),
        id='netsuite_daily_full_sync',
        name='NetSuite Daily Full Sync',
        replace_existing=True
    )

    # Job 2: Incremental NetSuite sync every 4 hours
    scheduler.add_job(
        jobs.sync_netsuite_incremental,
        'interval',
        hours=4,
        id='netsuite_incremental_sync',
        name='NetSuite Incremental Sync',
        replace_existing=True
    )

    # Job 3: Hourly alert check
    scheduler.add_job(
        jobs.check_and_send_alerts,
        'interval',
        hours=1,
        id='hourly_alert_check',
        name='Hourly Alert Check',
        replace_existing=True
    )

    # Job 4: Weekly insights email (Monday 9am)
    scheduler.add_job(
        jobs.send_weekly_insights,
        CronTrigger(day_of_week='mon', hour=9, minute=0),
        id='weekly_insights_email',
        name='Weekly Insights Email',
        replace_existing=True
    )

    scheduler.start()
    logger.info("✅ Scheduler started: 4 jobs registered")
    logger.info("  - Daily NetSuite full sync: 2am")
    logger.info("  - Incremental NetSuite sync: Every 4 hours")
    logger.info("  - Hourly alert check")
    logger.info("  - Weekly insights: Monday 9am")

    yield

    # Shutdown
    logger.info("Shutting down scheduler...")
    scheduler.shutdown(wait=True)
    logger.info("Scheduler stopped")
```

### Step 5: Test scheduler initialization

Run:
```bash
cd mcp-server
python -c "from src.main import app; print('Scheduler test: OK')"
```

Expected: No import errors

### Step 6: Commit scheduler implementation

```bash
git add mcp-server/src/main.py \
        mcp-server/src/scheduler/jobs.py \
        mcp-server/requirements.txt

git commit -m "feat(scheduler): add APScheduler for automated NetSuite syncs and alerts

- Add APScheduler dependency
- Create jobs module with 4 background jobs:
  1. Daily NetSuite full sync (2am)
  2. Incremental NetSuite sync (every 4 hours)
  3. Hourly alert check
  4. Weekly insights email (Monday 9am)
- Integrate scheduler into FastAPI lifespan
- Add graceful shutdown handling

Ensures NetSuite data stays fresh automatically"
```

---

## Task 3: Activate Disabled dbt Models

**Files:**
- Create: `dbt/dentalerp/models/gold/facts/fact_financials.sql`
- Rename: `dbt/dentalerp/models/gold/metrics/monthly_production_kpis.sql.disabled` → `.sql`
- Rename: `dbt/dentalerp/models/gold/metrics/kpi_alerts.sql.disabled` → `.sql`

### Step 1: Create fact_financials from NetSuite data

Create `dbt/dentalerp/models/gold/facts/fact_financials.sql`:

```sql
{{
  config(
    materialized='table',
    tags=['gold', 'financial']
  )
}}

/*
Gold Layer - Financial Transactions Fact Table
Source: NetSuite journal entries via stg_financials
*/

SELECT
    -- Transaction identification
    CAST(id AS VARCHAR) as transaction_id,
    transaction_date,
    DATE_TRUNC('month', transaction_date) as month_date,

    -- Practice dimension (TODO: Replace with actual practice from NetSuite when available)
    'Default Practice' as practice_name,

    -- Financial metrics
    amount as total_production,

    -- Expense classification (TODO: Enhance when NetSuite account mapping complete)
    CASE
        WHEN amount < 0 THEN ABS(amount)
        ELSE 0
    END as total_expenses,

    -- Net income
    amount as net_income,

    -- Transaction metadata
    1 as transaction_count,
    'netsuite' as data_source,
    created_at

FROM {{ ref('stg_financials') }}
WHERE transaction_date >= DATEADD(MONTH, -24, CURRENT_DATE())  -- 2 years history
```

### Step 2: Run dbt to create fact_financials

Run:
```bash
cd dbt/dentalerp
dbt run --select fact_financials
```

Expected output:
```
1 of 1 START sql table model gold.fact_financials ............... [RUN]
1 of 1 OK created sql table model gold.fact_financials .......... [SUCCESS 1]
```

### Step 3: Activate monthly_production_kpis

Run:
```bash
cd dbt/dentalerp/models/gold/metrics
mv monthly_production_kpis.sql.disabled monthly_production_kpis.sql
```

### Step 4: Run monthly_production_kpis model

Run:
```bash
dbt run --select monthly_production_kpis
```

Expected output:
```
1 of 1 START sql view model gold.monthly_production_kpis ........ [RUN]
1 of 1 OK created sql view model gold.monthly_production_kpis ... [SUCCESS 1]
```

### Step 5: Activate kpi_alerts

Run:
```bash
cd dbt/dentalerp/models/gold/metrics
mv kpi_alerts.sql.disabled kpi_alerts.sql
```

### Step 6: Run kpi_alerts model

Run:
```bash
dbt run --select kpi_alerts
```

Expected output:
```
1 of 1 START sql table model gold.kpi_alerts .................... [RUN]
1 of 1 OK created sql table model gold.kpi_alerts ............... [SUCCESS 1]
```

### Step 7: Verify models created and populated

Run in Snowflake:
```sql
SELECT COUNT(*) FROM gold.fact_financials;
SELECT COUNT(*) FROM gold.monthly_production_kpis;
SELECT COUNT(*) FROM gold.kpi_alerts;
```

Expected: All queries return count > 0

### Step 8: Commit model activation

```bash
git add dbt/dentalerp/models/gold/facts/fact_financials.sql \
        dbt/dentalerp/models/gold/metrics/monthly_production_kpis.sql \
        dbt/dentalerp/models/gold/metrics/kpi_alerts.sql

git commit -m "feat(dbt): activate MoM KPIs and variance alert models

- Create fact_financials from NetSuite stg_financials
- Activate monthly_production_kpis.sql (was disabled)
- Activate kpi_alerts.sql (was disabled)

Enables:
- Month-over-month growth tracking
- Target variance detection
- Automated alert generation
- Foundation for forecasting and anomaly detection"
```

---

## Task 4: Implement Snowflake-Native Forecasting

**Files:**
- Create: `dbt/dentalerp/models/gold/forecasts/revenue_forecast.sql`
- Create: `dbt/dentalerp/models/gold/forecasts/cost_forecast.sql`
- Modify: `mcp-server/src/services/forecasting.py:57-99`
- Create: `mcp-server/src/api/forecasting.py`

### Step 1: Create revenue forecast dbt model

Create `dbt/dentalerp/models/gold/forecasts/revenue_forecast.sql`:

```sql
{{
  config(
    materialized='table',
    tags=['gold', 'forecasting', 'ml']
  )
}}

/*
Gold Layer - Revenue Forecasting using Snowflake ML
3-month revenue projections with confidence intervals
*/

-- Note: Snowflake FORECAST() requires Snowflake Enterprise Edition
-- For MVP, use simple linear regression

WITH historical_data AS (
    SELECT
        practice_name,
        month_date,
        total_production
    FROM {{ ref('monthly_production_kpis') }}
    WHERE total_production IS NOT NULL
    ORDER BY month_date
),

-- Calculate linear trend
trend_stats AS (
    SELECT
        practice_name,
        REGR_SLOPE(total_production, DATEDIFF(MONTH, '2020-01-01', month_date)) as slope,
        REGR_INTERCEPT(total_production, DATEDIFF(MONTH, '2020-01-01', month_date)) as intercept,
        STDDEV(total_production) as stddev
    FROM historical_data
    GROUP BY practice_name
),

-- Generate forecast for next 3 months
forecast_periods AS (
    SELECT
        ROW_NUMBER() OVER (ORDER BY SEQ4()) as period_offset
    FROM TABLE(GENERATOR(ROWCOUNT => 3))
),

forecasts AS (
    SELECT
        t.practice_name,
        DATEADD(MONTH, f.period_offset, CURRENT_DATE()) as forecast_month,

        -- Linear projection: y = mx + b
        (t.slope * (DATEDIFF(MONTH, '2020-01-01', DATEADD(MONTH, f.period_offset, CURRENT_DATE())))) + t.intercept as predicted_value,

        -- Confidence intervals (±1.96 * stddev for 95% confidence)
        ((t.slope * (DATEDIFF(MONTH, '2020-01-01', DATEADD(MONTH, f.period_offset, CURRENT_DATE())))) + t.intercept) - (1.96 * t.stddev) as lower_bound,

        ((t.slope * (DATEDIFF(MONTH, '2020-01-01', DATEADD(MONTH, f.period_offset, CURRENT_DATE())))) + t.intercept) + (1.96 * t.stddev) as upper_bound,

        0.95 as confidence_level,
        'linear_regression' as model_type,
        CURRENT_TIMESTAMP() as generated_at

    FROM trend_stats t
    CROSS JOIN forecast_periods f
)

SELECT * FROM forecasts
ORDER BY practice_name, forecast_month
```

### Step 2: Run revenue forecast model

Run:
```bash
cd dbt/dentalerp
dbt run --select revenue_forecast
```

Expected: Model creates successfully

### Step 3: Update forecasting.py to query Snowflake forecasts

Modify `mcp-server/src/services/forecasting.py` lines 57-74:

```python
@cached(ttl=3600, key_prefix="forecast:revenue")
async def forecast_revenue(
    self,
    practice_name: str,
    periods: int = 3,
    confidence_level: float = 0.95
) -> Dict[str, Any]:
    """
    Query pre-computed revenue forecasts from Snowflake

    Snowflake dbt model does all computation (linear regression)
    MCP just queries the results
    """
    from ..services.warehouse_router import WarehouseRouter

    logger.info(f"Fetching revenue forecast for {practice_name}, {periods} periods")

    warehouse_router = WarehouseRouter()
    snowflake = await warehouse_router.get_connector(warehouse_type="snowflake")

    # Query pre-computed forecasts
    result = await snowflake.execute_query("""
        SELECT
            forecast_month,
            predicted_value,
            lower_bound,
            upper_bound,
            confidence_level,
            model_type
        FROM gold.revenue_forecast
        WHERE practice_name = %s
        ORDER BY forecast_month
        LIMIT %s
    """, parameters={'practice_name': practice_name, 'periods': periods})

    # Format response
    forecasts = []
    for row in result:
        forecasts.append({
            "period": row['forecast_month'].strftime("%Y-%m"),
            "predicted": float(row['predicted_value']),
            "lower_bound": float(row['lower_bound']),
            "upper_bound": float(row['upper_bound']),
            "confidence": float(row['confidence_level'])
        })

    return {
        "practice_name": practice_name,
        "metric": "revenue",
        "forecasts": forecasts,
        "model": result[0]['model_type'] if result else "linear_regression",
        "generated_at": datetime.utcnow().isoformat()
    }
```

### Step 4: Create forecast API endpoint

Create `mcp-server/src/api/forecasting.py`:

```python
"""
Forecasting API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from ..core.security import verify_api_key
from ..services.forecasting import get_forecasting_service
from ..utils.logger import logger

router = APIRouter(prefix="/api/v1/forecasting", tags=["forecasting"])


@router.get("/revenue/{practice_name}")
async def get_revenue_forecast(
    practice_name: str,
    periods: int = 3,
    api_key: str = Depends(verify_api_key)
):
    """
    Get revenue forecast for practice

    Args:
        practice_name: Practice identifier
        periods: Number of months to forecast (default 3)

    Returns:
        Revenue projections with confidence intervals
    """
    try:
        forecasting = get_forecasting_service()
        forecast = await forecasting.forecast_revenue(practice_name, periods)
        return forecast

    except Exception as e:
        logger.error(f"Revenue forecast failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs/{practice_name}")
async def get_cost_forecast(
    practice_name: str,
    periods: int = 3,
    api_key: str = Depends(verify_api_key)
):
    """Get cost forecast for practice"""
    try:
        forecasting = get_forecasting_service()
        forecast = await forecasting.forecast_costs(practice_name, periods)
        return forecast

    except Exception as e:
        logger.error(f"Cost forecast failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 5: Register forecast router in main.py

Add to `mcp-server/src/main.py`:

```python
from .api import forecasting

app.include_router(forecasting.router)
```

### Step 6: Test forecast endpoint

Run:
```bash
curl -H "Authorization: Bearer $MCP_API_KEY" \
     -H "X-Tenant-ID: default" \
     "http://localhost:8085/api/v1/forecasting/revenue/Default%20Practice?periods=3"
```

Expected: JSON with 3-month forecast

### Step 7: Commit forecasting implementation

```bash
git add dbt/dentalerp/models/gold/forecasts/revenue_forecast.sql \
        mcp-server/src/services/forecasting.py \
        mcp-server/src/api/forecasting.py \
        mcp-server/src/main.py

git commit -m "feat(forecasting): implement Snowflake-native revenue forecasting

- Create revenue_forecast dbt model with linear regression
- Update forecasting.py to query Snowflake results (not compute)
- Add /api/v1/forecasting endpoints
- Generate 3-month projections with 95% confidence intervals

Follows Snowflake-native pattern: computation in SQL, API just queries"
```

---

## Task 5: Implement Snowflake-Native Anomaly Detection

**Files:**
- Create: `dbt/dentalerp/models/gold/monitoring/production_anomalies.sql`
- Modify: `mcp-server/src/services/forecasting.py:125-148`
- Modify: `mcp-server/src/api/forecasting.py`

### Step 1: Create anomaly detection dbt model

Create `dbt/dentalerp/models/gold/monitoring/production_anomalies.sql`:

```sql
{{
  config(
    materialized='table',
    tags=['gold', 'monitoring', 'anomalies']
  )
}}

/*
Gold Layer - Production Anomaly Detection
Z-score based statistical anomaly detection with 12-month rolling baseline
*/

WITH monthly_stats AS (
    SELECT
        practice_name,
        month_date,
        total_production,

        -- 12-month rolling average
        AVG(total_production) OVER (
            PARTITION BY practice_name
            ORDER BY month_date
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) as avg_12m,

        -- 12-month rolling standard deviation
        STDDEV(total_production) OVER (
            PARTITION BY practice_name
            ORDER BY month_date
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) as stddev_12m,

        -- Count of months for baseline
        COUNT(*) OVER (
            PARTITION BY practice_name
            ORDER BY month_date
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) as baseline_months

    FROM {{ ref('monthly_production_kpis') }}
),

z_scores AS (
    SELECT
        practice_name,
        month_date,
        total_production as actual_value,
        ROUND(avg_12m, 2) as expected_value,
        ROUND(stddev_12m, 2) as stddev,

        -- Calculate Z-score
        ROUND(
            (total_production - avg_12m) / NULLIF(stddev_12m, 0),
            2
        ) as z_score,

        baseline_months

    FROM monthly_stats
    WHERE baseline_months >= 6  -- Need at least 6 months of history
),

anomalies AS (
    SELECT
        practice_name,
        month_date,
        actual_value,
        expected_value,
        stddev,
        z_score,

        -- Classify severity based on Z-score
        CASE
            WHEN ABS(z_score) > 3.0 THEN 'critical'
            WHEN ABS(z_score) > 2.0 THEN 'warning'
            ELSE 'info'
        END as severity,

        -- Generate alert message
        CASE
            WHEN z_score > 3.0 THEN
                'Extreme production spike: $' || ROUND(actual_value) || ' is ' || ROUND(ABS(z_score), 1) || ' std deviations above normal'
            WHEN z_score > 2.0 THEN
                'Production above normal: $' || ROUND(actual_value) || ' is ' || ROUND(ABS(z_score), 1) || ' std deviations high'
            WHEN z_score < -3.0 THEN
                'Extreme production drop: $' || ROUND(actual_value) || ' is ' || ROUND(ABS(z_score), 1) || ' std deviations below normal'
            WHEN z_score < -2.0 THEN
                'Production below normal: $' || ROUND(actual_value) || ' is ' || ROUND(ABS(z_score), 1) || ' std deviations low'
            ELSE
                'Normal variance'
        END as alert_message,

        CURRENT_TIMESTAMP() as detected_at

    FROM z_scores
    WHERE ABS(z_score) > 2.0  -- Only significant anomalies
)

SELECT * FROM anomalies
ORDER BY month_date DESC, ABS(z_score) DESC
```

### Step 2: Run anomaly detection model

Run:
```bash
dbt run --select production_anomalies
```

Expected: Model creates successfully

### Step 3: Update forecasting.py anomaly detection method

Modify `mcp-server/src/services/forecasting.py` lines 125-148:

```python
async def detect_anomalies(
    self,
    practice_name: str,
    metric: str = "revenue",
    sensitivity: float = 2.0
) -> List[Dict[str, Any]]:
    """
    Query pre-computed anomalies from Snowflake

    Snowflake computes Z-scores and identifies outliers
    MCP just queries the results

    Args:
        practice_name: Practice identifier
        metric: Metric to analyze (currently only 'revenue' supported)
        sensitivity: Z-score threshold (default 2.0)

    Returns:
        List of detected anomalies
    """
    from ..services.warehouse_router import WarehouseRouter

    logger.info(f"Fetching anomalies for {practice_name}, sensitivity: {sensitivity}")

    warehouse_router = WarehouseRouter()
    snowflake = await warehouse_router.get_connector(warehouse_type="snowflake")

    # Query pre-computed anomalies
    result = await snowflake.execute_query("""
        SELECT
            month_date,
            actual_value,
            expected_value,
            stddev,
            z_score,
            severity,
            alert_message,
            detected_at
        FROM gold.production_anomalies
        WHERE practice_name = %s
        AND ABS(z_score) >= %s
        ORDER BY month_date DESC
        LIMIT 20
    """, parameters={'practice_name': practice_name, 'sensitivity': sensitivity})

    # Format response
    anomalies = []
    for row in result:
        anomalies.append({
            "date": row['month_date'].strftime("%Y-%m-%d"),
            "metric": metric,
            "actual_value": float(row['actual_value']),
            "expected_value": float(row['expected_value']),
            "variance_pct": round(
                ((row['actual_value'] - row['expected_value']) / row['expected_value']) * 100,
                1
            ),
            "z_score": float(row['z_score']),
            "severity": row['severity'],
            "message": row['alert_message']
        })

    return anomalies
```

### Step 4: Add anomaly endpoint to forecasting API

Add to `mcp-server/src/api/forecasting.py`:

```python
@router.get("/anomalies/{practice_name}")
async def get_anomalies(
    practice_name: str,
    sensitivity: float = 2.0,
    api_key: str = Depends(verify_api_key)
):
    """
    Get detected anomalies for practice

    Args:
        practice_name: Practice identifier
        sensitivity: Z-score threshold (default 2.0 = 2 std deviations)

    Returns:
        List of anomalies with Z-scores
    """
    try:
        forecasting = get_forecasting_service()
        anomalies = await forecasting.detect_anomalies(practice_name, sensitivity=sensitivity)
        return {
            "practice_name": practice_name,
            "anomalies": anomalies,
            "sensitivity": sensitivity
        }

    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 5: Test anomaly detection

Run:
```bash
dbt run --select production_anomalies

curl -H "Authorization: Bearer $MCP_API_KEY" \
     "http://localhost:8085/api/v1/forecasting/anomalies/Default%20Practice"
```

Expected: JSON with detected anomalies

### Step 6: Commit anomaly detection

```bash
git add dbt/dentalerp/models/gold/monitoring/production_anomalies.sql \
        mcp-server/src/services/forecasting.py \
        mcp-server/src/api/forecasting.py

git commit -m "feat(anomaly): implement Snowflake-native anomaly detection

- Create production_anomalies dbt model with Z-score calculation
- 12-month rolling baseline for statistical analysis
- Severity classification (warning >2σ, critical >3σ)
- Update detect_anomalies() to query Snowflake results
- Add /api/v1/forecasting/anomalies endpoint

Follows Snowflake-native pattern: all statistics in SQL"
```

---

## Task 6: Implement GPT-4 Text-to-Insights

**Files:**
- Modify: `mcp-server/src/services/forecasting.py` (add generate_insights method)
- Modify: `mcp-server/src/api/forecasting.py` (add insights endpoint)

### Step 1: Add generate_insights method to forecasting.py

Add new method to `mcp-server/src/services/forecasting.py`:

```python
@cached(ttl=3600, key_prefix="insights:summary")
async def generate_insights(
    self,
    practice_name: Optional[str] = None,
    period: str = "month"
) -> str:
    """
    Generate natural language insights using GPT-4

    Queries Snowflake for KPIs and uses GPT-4 to create executive summary

    Args:
        practice_name: Optional practice filter (None = all practices)
        period: Time period ('month', 'quarter')

    Returns:
        Natural language summary (2-3 sentences)
    """
    from ..services.warehouse_router import WarehouseRouter
    import openai
    import os

    logger.info(f"Generating AI insights for {practice_name or 'all practices'}")

    warehouse_router = WarehouseRouter()
    snowflake = await warehouse_router.get_connector(warehouse_type="snowflake")

    # Query top practices by production
    top_practices_query = """
        SELECT
            practice_name,
            total_production,
            mom_production_growth_pct,
            profit_margin_pct,
            target_status
        FROM gold.monthly_production_kpis
        WHERE month_date = DATE_TRUNC('month', CURRENT_DATE())
        ORDER BY total_production DESC
        LIMIT 5
    """

    if practice_name:
        top_practices_query += f" AND practice_name = '{practice_name}'"

    top_practices = await snowflake.execute_query(top_practices_query)

    # Query recent alerts
    alerts = await snowflake.execute_query("""
        SELECT
            practice_name,
            alert_message,
            severity,
            variance_pct
        FROM gold.kpi_alerts
        WHERE month_date >= DATEADD(MONTH, -1, CURRENT_DATE())
        ORDER BY severity DESC, month_date DESC
        LIMIT 10
    """)

    # Format data for GPT-4
    kpi_summary = "\n".join([
        f"- {row['practice_name']}: ${row['total_production']:,.0f} "
        f"({row['mom_production_growth_pct']:+.1f}% MoM, "
        f"{row['profit_margin_pct']:.1f}% margin, {row['target_status']})"
        for row in top_practices
    ])

    alert_summary = "\n".join([
        f"- {row['practice_name']}: {row['alert_message']} ({row['severity']})"
        for row in alerts
    ]) if alerts else "No significant alerts"

    # Build GPT-4 prompt
    prompt = f"""You are analyzing dental practice financial performance.
Provide a concise 2-3 sentence executive summary focusing on actionable insights.

TOP PRACTICES BY PRODUCTION:
{kpi_summary}

RECENT ALERTS:
{alert_summary}

FORMAT:
"Production [trend] X% MoM, driven by [key driver]. Top performers: [list]. Notable changes: [insights]."

Focus on: MoM growth trends, top/bottom performers, cost changes, actionable insights.
Be specific with numbers and practice names. Keep it executive-level concise."""

    # Call GPT-4
    openai.api_key = os.getenv('OPENAI_API_KEY')

    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0.7
    )

    insights = response.choices[0].message.content

    logger.info(f"Generated insights: {insights[:100]}...")
    return insights
```

### Step 2: Add insights endpoint to forecasting API

Add to `mcp-server/src/api/forecasting.py`:

```python
@router.get("/insights")
async def get_ai_insights(
    practice_name: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """
    Get AI-generated natural language insights

    Args:
        practice_name: Optional practice filter

    Returns:
        GPT-4 generated executive summary of KPIs
    """
    try:
        forecasting = get_forecasting_service()
        insights = await forecasting.generate_insights(practice_name)

        return {
            "insights": insights,
            "practice_name": practice_name or "all",
            "generated_at": datetime.utcnow().isoformat(),
            "model": "gpt-4"
        }

    except Exception as e:
        logger.error(f"Insights generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 3: Test GPT-4 insights

Run:
```bash
curl -H "Authorization: Bearer $MCP_API_KEY" \
     "http://localhost:8085/api/v1/forecasting/insights"
```

Expected: Natural language summary of KPIs

### Step 4: Commit text-to-insights

```bash
git add mcp-server/src/services/forecasting.py \
        mcp-server/src/api/forecasting.py

git commit -m "feat(insights): implement GPT-4 text-to-insights engine

- Add generate_insights() method with GPT-4 integration
- Query Snowflake for top practices and recent alerts
- Generate 2-3 sentence executive summaries
- Add /api/v1/forecasting/insights endpoint
- Cache results for 1 hour to reduce OpenAI costs

Delivers: 'Production up 12% MoM, driven by Eastlake...' style insights"
```

---

## Task 7: Complete Alert Delivery (Slack + Email)

**Files:**
- Modify: `mcp-server/src/services/alerts.py:61,121,127`
- Modify: `mcp-server/.env`

### Step 1: Implement check_kpi_alerts() to query Snowflake

Modify `mcp-server/src/services/alerts.py` line 61:

```python
async def check_kpi_alerts(
    self,
    practice_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Query pre-computed KPI alerts from Snowflake

    Args:
        practice_name: Optional practice filter

    Returns:
        List of active alerts
    """
    from ..services.warehouse_router import WarehouseRouter

    logger.info(f"Checking KPI alerts for {practice_name or 'all practices'}")

    warehouse_router = WarehouseRouter()
    snowflake = await warehouse_router.get_connector(warehouse_type="snowflake")

    # Build query
    query = """
        SELECT
            alert_id,
            practice_name,
            month_date,
            metric_name,
            actual_value,
            expected_value,
            variance_pct,
            severity,
            alert_message,
            generated_at
        FROM gold.kpi_alerts
        WHERE (%s IS NULL OR practice_name = %s)
        AND severity IN ('warning', 'critical')
        ORDER BY generated_at DESC, severity DESC
        LIMIT 50
    """

    result = await snowflake.execute_query(
        query,
        parameters={'practice_name': practice_name, 'practice_name_check': practice_name}
    )

    return result
```

### Step 2: Implement Slack webhook delivery

Modify `mcp-server/src/services/alerts.py` line 127:

```python
async def _send_slack_alert(self, alert: Dict[str, Any]) -> bool:
    """Send alert to Slack via webhook"""
    import httpx
    import os

    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL not configured, skipping Slack alert")
        return False

    # Severity emoji mapping
    severity_emoji = {
        'info': 'ℹ️',
        'warning': '⚠️',
        'critical': '🚨'
    }

    emoji = severity_emoji.get(alert.get('severity', 'info'), '📊')

    # Format Slack message with blocks
    message = {
        "text": f"{emoji} DentalERP Alert: {alert.get('alert_message', 'No message')}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} DentalERP Alert"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Practice:* {alert.get('practice_name', 'Unknown')}"},
                    {"type": "mrkdwn", "text": f"*Severity:* {alert.get('severity', 'info').upper()}"},
                    {"type": "mrkdwn", "text": f"*Metric:* {alert.get('metric_name', 'N/A')}"},
                    {"type": "mrkdwn", "text": f"*Variance:* {alert.get('variance_pct', 0):.1f}%"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Message:* {alert.get('alert_message', 'No details')}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Date: {alert.get('month_date', 'N/A')} | Generated: {alert.get('generated_at', 'N/A')}"
                    }
                ]
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=message)

            if response.status_code == 200:
                logger.info(f"Slack alert sent successfully: {alert.get('alert_message', '')[:50]}")
                return True
            else:
                logger.error(f"Slack webhook failed: {response.status_code} - {response.text}")
                return False

    except Exception as e:
        logger.error(f"Slack alert delivery failed: {e}", exc_info=True)
        return False
```

### Step 3: Implement email SMTP delivery

Modify `mcp-server/src/services/alerts.py` line 121:

```python
async def _send_email_alert(self, alert: Dict[str, Any]) -> bool:
    """Send alert via email using SMTP"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import os

    # Get SMTP configuration
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('SMTP_FROM', smtp_user)
    to_email = os.getenv('ALERT_EMAIL')

    if not all([smtp_host, smtp_user, smtp_password, to_email]):
        logger.warning("SMTP not fully configured, skipping email alert")
        return False

    # Build email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"DentalERP Alert: {alert.get('severity', 'INFO').upper()} - {alert.get('practice_name', 'Practice')}"
    msg['From'] = from_email
    msg['To'] = to_email

    # HTML body
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
          <h2 style="color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px;">DentalERP Alert</h2>

          <div style="margin: 20px 0;">
            <p><strong>Severity:</strong> <span style="color: {'#f44336' if alert.get('severity') == 'critical' else '#ff9800' if alert.get('severity') == 'warning' else '#2196F3'};">{alert.get('severity', 'info').upper()}</span></p>
            <p><strong>Practice:</strong> {alert.get('practice_name', 'Unknown')}</p>
            <p><strong>Date:</strong> {alert.get('month_date', 'N/A')}</p>
          </div>

          <div style="background-color: #f9f9f9; padding: 15px; border-radius: 4px; margin: 20px 0;">
            <p style="margin: 0; font-size: 16px;"><strong>Message:</strong></p>
            <p style="margin: 10px 0 0 0; font-size: 14px;">{alert.get('alert_message', 'No details available')}</p>
          </div>

          <div style="margin: 20px 0; padding: 15px; background-color: #e8f5e9; border-left: 4px solid #4CAF50;">
            <p style="margin: 0;"><strong>Details:</strong></p>
            <ul style="margin: 10px 0 0 0; padding-left: 20px;">
              <li>Metric: {alert.get('metric_name', 'N/A')}</li>
              <li>Actual Value: ${alert.get('actual_value', 0):,.2f}</li>
              <li>Expected Value: ${alert.get('expected_value', 0):,.2f}</li>
              <li>Variance: {alert.get('variance_pct', 0):.1f}%</li>
            </ul>
          </div>

          <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

          <p style="color: #999; font-size: 12px; text-align: center;">
            DentalERP Analytics Platform | Generated: {alert.get('generated_at', 'N/A')}
          </p>
        </div>
      </body>
    </html>
    """

    msg.attach(MIMEText(html, 'html'))

    try:
        # Send via SMTP
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        logger.info(f"Email alert sent successfully to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Email alert delivery failed: {e}", exc_info=True)
        return False
```

### Step 4: Add insights endpoint

Add to `mcp-server/src/api/forecasting.py`:

```python
@router.get("/insights")
async def get_ai_insights(
    practice_name: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """
    Get AI-generated insights summary

    Uses GPT-4 to analyze KPIs and generate natural language summary

    Args:
        practice_name: Optional practice filter

    Returns:
        Natural language insights (2-3 sentences)
    """
    try:
        forecasting = get_forecasting_service()
        insights = await forecasting.generate_insights(practice_name)

        return {
            "insights": insights,
            "practice_name": practice_name or "all",
            "generated_at": datetime.utcnow().isoformat(),
            "model": "gpt-4",
            "cached": True  # Cached for 1 hour
        }

    except Exception as e:
        logger.error(f"Insights generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 5: Add required environment variables

Add to `mcp-server/.env`:

```bash
# OpenAI (already exists, verify it's set)
OPENAI_API_KEY=sk-...

# Slack (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alerts@dentalerp.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=DentalERP Alerts <alerts@dentalerp.com>
ALERT_EMAIL=executives@silvercreek.com
```

### Step 6: Test GPT-4 insights

Run:
```bash
# Ensure OpenAI API key is set
echo $OPENAI_API_KEY

# Test insights endpoint
curl -H "Authorization: Bearer $MCP_API_KEY" \
     "http://localhost:8085/api/v1/forecasting/insights"
```

Expected: JSON with GPT-4 generated summary

### Step 7: Test alert delivery

Run:
```bash
# Test Slack webhook (if configured)
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text": "Test alert from DentalERP"}'

# Verify email configuration
python3 -c "
import smtplib
import os
from dotenv import load_dotenv
load_dotenv()

smtp = smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT', 587)))
smtp.starttls()
smtp.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
print('✅ SMTP connection successful')
smtp.quit()
"
```

Expected: Slack message received, SMTP connection successful

### Step 8: Commit alert delivery implementation

```bash
git add mcp-server/src/services/alerts.py \
        mcp-server/src/services/forecasting.py \
        mcp-server/src/api/forecasting.py \
        mcp-server/.env

git commit -m "feat(alerts): complete Slack and email alert delivery

- Implement check_kpi_alerts() to query Snowflake gold.kpi_alerts
- Implement Slack webhook with formatted blocks
- Implement SMTP email with HTML formatting
- Add GPT-4 text-to-insights generation
- Add insights API endpoint

Features:
- Hourly alert checks (via APScheduler)
- Slack notifications with severity colors
- HTML email alerts with variance details
- AI-generated weekly insights
- Alert deduplication (24-hour window)

Completes AI automation requirements from proposal"
```

---

## Task 8: Deploy and Verify All Features

**Files:**
- Run on GCP VM

### Step 1: Deploy to production

Run on local machine:
```bash
git push origin feat/complete-mvp-ai-features

# SSH to GCP
gcloud compute ssh dental-erp-vm --zone=us-central1-a
```

On GCP VM:
```bash
cd /opt/dental-erp
sudo git fetch origin
sudo git checkout feat/complete-mvp-ai-features
sudo git pull origin feat/complete-mvp-ai-features

# Rebuild MCP server
sudo docker-compose build mcp-server-prod
sudo docker-compose stop mcp-server-prod
sudo docker-compose rm -f mcp-server-prod
sudo docker-compose up -d mcp-server-prod
```

### Step 2: Run duplicate cleanup script

On GCP VM:
```bash
# Copy cleanup script to container
sudo docker cp scripts/cleanup_netsuite_duplicates.sql dental-erp_mcp-server-prod_1:/tmp/

# Execute cleanup
sudo docker exec dental-erp_mcp-server-prod_1 psql \
  -h $SNOWFLAKE_ACCOUNT \
  -U $SNOWFLAKE_USER \
  -d $SNOWFLAKE_DATABASE \
  -f /tmp/cleanup_netsuite_duplicates.sql
```

Or use Python script:
```bash
sudo docker exec dental-erp_mcp-server-prod_1 python3 /app/check_duplicates.py
```

Expected: Duplicates reduced from 25,052 → 0

### Step 3: Run dbt transformations

On GCP VM:
```bash
cd /opt/dental-erp/dbt/dentalerp

# Run all new models
dbt run --select fact_financials monthly_production_kpis kpi_alerts revenue_forecast production_anomalies
```

Expected: All 5 models create successfully

### Step 4: Verify automated sync scheduler

On GCP VM:
```bash
# Check scheduler logs
sudo docker-compose logs -f mcp-server-prod | grep -i "scheduler"
```

Expected: See "Scheduler started: 4 jobs registered"

### Step 5: Test forecasting API

Run:
```bash
curl -H "Authorization: Bearer prod-mcp-api-key-change-in-production-min-32-chars-secure" \
     "https://mcp.agentprovision.com/api/v1/forecasting/revenue/Default%20Practice?periods=3"
```

Expected: 3-month revenue projection with confidence intervals

### Step 6: Test anomaly detection API

Run:
```bash
curl -H "Authorization: Bearer prod-mcp-api-key-change-in-production-min-32-chars-secure" \
     "https://mcp.agentprovision.com/api/v1/forecasting/anomalies/Default%20Practice"
```

Expected: List of detected anomalies with Z-scores

### Step 7: Test GPT-4 insights API

Run:
```bash
curl -H "Authorization: Bearer prod-mcp-api-key-change-in-production-min-32-chars-secure" \
     "https://mcp.agentprovision.com/api/v1/forecasting/insights"
```

Expected: Natural language summary like "Production up 12% MoM..."

### Step 8: Verify alert delivery

Configure Slack webhook in `.env`, then wait 1 hour for scheduled alert check, or manually trigger:

```bash
# Manually trigger alert check
curl -X POST https://mcp.agentprovision.com/api/v1/alerts/check \
  -H "Authorization: Bearer prod-mcp-api-key-change-in-production-min-32-chars-secure"
```

Expected: Alert appears in Slack channel and email inbox

### Step 9: Create verification report

Create `IMPLEMENTATION_VERIFICATION.md`:

```markdown
# MVP AI Features Implementation Verification

**Date:** 2025-11-08
**Status:** Complete

## Verification Results

### ✅ Data Duplication Fixed
- Before: 31,315 records (5x duplicates)
- After: 6,263 unique records
- Method: MERGE upsert pattern
- Test: Re-run sync, verify COUNT(*) = COUNT(DISTINCT id)

### ✅ Automated Syncs Active
- Daily full sync: 2am ✅
- Incremental sync: Every 4 hours ✅
- Scheduler status: Running ✅
- Next sync: [timestamp]

### ✅ dbt Models Activated
- fact_financials: [N rows] ✅
- monthly_production_kpis: [N rows] ✅
- kpi_alerts: [N alerts] ✅
- revenue_forecast: [N forecasts] ✅
- production_anomalies: [N anomalies] ✅

### ✅ AI Features Working
- Revenue forecasting: 3-month projections ✅
- Anomaly detection: Z-score analysis ✅
- Text-to-insights: GPT-4 summaries ✅
- Alert delivery: Slack + Email ✅

### ✅ API Endpoints
- GET /api/v1/forecasting/revenue/{practice} ✅
- GET /api/v1/forecasting/costs/{practice} ✅
- GET /api/v1/forecasting/anomalies/{practice} ✅
- GET /api/v1/forecasting/insights ✅

## Success Criteria Met

- [x] No duplicate records in Bronze layer
- [x] NetSuite syncs run automatically
- [x] MoM growth tracking active
- [x] Variance alerts generated
- [x] Revenue forecasting working
- [x] Anomaly detection identifying outliers
- [x] GPT-4 generating insights
- [x] Alerts delivering to Slack/email

## Next Steps

- [ ] Build financial analytics dashboard
- [ ] Build forecasting dashboard
- [ ] Monitor automated syncs for 24 hours
- [ ] Collect user feedback on AI insights
- [ ] Fine-tune anomaly sensitivity thresholds
```

### Step 10: Final commit

```bash
git add IMPLEMENTATION_VERIFICATION.md

git commit -m "docs: verification report for MVP AI features

All features implemented and verified:
- Data duplication fixed (MERGE upsert)
- Automated syncs running (APScheduler)
- dbt models activated (5 new Gold tables)
- Forecasting working (Snowflake linear regression)
- Anomaly detection working (Z-score analysis)
- Text-to-insights working (GPT-4)
- Alert delivery working (Slack + Email)

Ready for production use"
```

---

## Summary

**Total Tasks:** 8
**Total Commits:** 8
**Estimated Time:** 6-7 days

**Task Breakdown:**
1. Fix duplication (1 day) - MERGE upsert + cleanup
2. Add APScheduler (0.5 day) - Automated syncs
3. Activate dbt models (0.5 day) - Enable MoM tracking
4. Implement forecasting (1-2 days) - Snowflake ML
5. Implement anomaly detection (1 day) - Z-score analysis
6. Implement text-to-insights (1 day) - GPT-4 summaries
7. Complete alert delivery (1 day) - Slack + Email
8. Deploy and verify (0.5 day) - Production testing

**Architecture Pattern:** Snowflake-native
- All heavy computation in Snowflake (SQL/dbt)
- MCP provides thin API layer
- GPT-4 only for natural language generation
- APScheduler for automation

**Success Criteria:**
- Zero duplicates in Bronze layer
- Automated syncs running on schedule
- 5 new Gold layer tables active
- 4 API endpoints returning real data
- Alerts delivering to Slack and email
- GPT-4 generating actionable insights

---

**Plan saved:** `docs/plans/2025-11-08-complete-mvp-ai-features.md`
**Ready for execution**
