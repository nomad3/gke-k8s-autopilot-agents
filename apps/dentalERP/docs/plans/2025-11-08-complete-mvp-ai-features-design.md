# Complete MVP: AI Features & Critical Gaps - Design

**Date:** 2025-11-08
**Status:** Validated
**Approach:** Snowflake-native computation, thin MCP API layer

---

## Overview

**Goal:** Complete the Silvercreek MVP by fixing critical gaps and implementing AI features using existing NetSuite data while waiting for ADP/Dentrix credentials.

**Strategy:** Leverage Snowflake's full ML and analytical capabilities instead of reimplementing in Python. Build complete financial analytics with NetSuite data, create ready-to-activate placeholders for clinical/payroll features.

**Timeline:** 6-7 days for AI features MVP

---

## Architecture

### Snowflake-Native AI Pattern

```
┌─────────────────────────────────────────────────────────┐
│ Snowflake (All Heavy Computation)                       │
│ ├─ ML.FORECAST() - Time series forecasting              │
│ ├─ STDDEV/AVG/Window functions - Anomaly detection     │
│ ├─ dbt models - Pre-compute everything                  │
│ └─ Materialized tables - Query-ready results            │
└──────────────────┬────────────────────────────────────┘
                   ↓ (Simple SELECT queries)
┌──────────────────┴────────────────────────────────────┐
│ MCP Server (Thin API + GPT-4 Only)                     │
│ ├─ Query forecasts: SELECT * FROM gold.revenue_forecast│
│ ├─ Query anomalies: SELECT * FROM gold.production_anomalies│
│ ├─ Query alerts: SELECT * FROM gold.kpi_alerts         │
│ └─ GPT-4 text generation (can't delegate to Snowflake) │
└──────────────────┬────────────────────────────────────┘
                   ↓
┌──────────────────┴────────────────────────────────────┐
│ Frontend (Display Only)                                 │
│ └─ Charts, tables, widgets from Snowflake results     │
└───────────────────────────────────────────────────────┘
```

**Benefits:**
- Snowflake's columnar optimization (faster than Python)
- No computation in MCP (stays lightweight)
- Easier testing (SQL only)
- dbt handles dependencies and scheduling
- Cost-effective (Snowflake warehouse auto-suspends)

---

## Task Breakdown

### Task 1: Fix NetSuite Data Duplication

**Problem:** 25,052 duplicate records (5x inflation) from multiple test syncs

**Current Code:**
```python
# snowflake_netsuite_loader.py line 227
INSERT INTO bronze.netsuite_accounts (...)
SELECT column1, PARSE_JSON(column2), ...
FROM VALUES(%s, %s, ...)
```

**New Code:**
```python
MERGE INTO bronze.netsuite_accounts t
USING (
    SELECT column1 as id, PARSE_JSON(column2) as raw_data, ...
    FROM VALUES(%s, %s, ...)
) s
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET
    raw_data = s.raw_data,
    last_modified_date = s.last_modified_date,
    extracted_at = s.extracted_at
WHEN NOT MATCHED THEN INSERT (...)
    VALUES (...)
```

**Cleanup Script:**
```sql
-- Delete duplicates, keep most recent
DELETE FROM bronze.netsuite_accounts
WHERE id IN (
    SELECT id FROM (
        SELECT id, extracted_at,
               ROW_NUMBER() OVER (PARTITION BY id ORDER BY extracted_at DESC) as rn
        FROM bronze.netsuite_accounts
    ) WHERE rn > 1
)
```

**Files Changed:**
- `mcp-server/src/services/snowflake_netsuite_loader.py` (method: _bulk_insert_snowflake)
- `scripts/cleanup_netsuite_duplicates.sql` (new file)

**Testing:**
- Trigger sync twice for same data
- Verify: COUNT(*) = COUNT(DISTINCT id)
- Verify: Total records ~6,263 (not 31,315)

---

### Task 2: Add APScheduler for Automated Syncs

**Goal:** Automate NetSuite syncs so data stays fresh while building AI features

**Implementation in main.py:**

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler = AsyncIOScheduler()

    # Daily full sync at 2am
    scheduler.add_job(
        run_netsuite_sync,
        CronTrigger(hour=2, minute=0),
        args=[True],  # full_sync=True
        id='netsuite_daily_full_sync'
    )

    # Incremental sync every 4 hours
    scheduler.add_job(
        run_netsuite_sync,
        'interval',
        hours=4,
        args=[False],  # full_sync=False
        id='netsuite_incremental_sync'
    )

    scheduler.start()
    logger.info("Scheduler started: NetSuite syncs automated")

    yield

    # Shutdown
    scheduler.shutdown()

async def run_netsuite_sync(full_sync: bool):
    """Background job for NetSuite sync"""
    from src.services.netsuite_sync_orchestrator import sync_all_tenants
    try:
        result = await sync_all_tenants(full_sync=full_sync)
        logger.info(f"Scheduled NetSuite sync completed: {result}")
    except Exception as e:
        logger.error(f"Scheduled NetSuite sync failed: {e}")
```

**Environment Variables:**
```bash
# Add to mcp-server/.env
NETSUITE_SYNC_SCHEDULE_FULL=0 2 * * *    # 2am daily
NETSUITE_SYNC_SCHEDULE_INCREMENTAL=0 */4 * * *  # Every 4 hours
```

**Files Changed:**
- `mcp-server/src/main.py` (add scheduler to lifespan)
- `mcp-server/requirements.txt` (add APScheduler==3.10.4)

**Testing:**
- Verify scheduler starts without errors
- Mock time to trigger job
- Verify sync runs automatically

---

### Task 3: Activate dbt Models

**Problem:** `monthly_production_kpis` references non-existent `fact_financials` table

**Solution:** Create fact_financials from NetSuite stg_financials

**New File:** `dbt/dentalerp/models/gold/facts/fact_financials.sql`

```sql
{{ config(materialized='table') }}

/*
Gold Layer - Financial Transactions Fact Table
Combines NetSuite journal entries with standardized dimensions
*/

SELECT
    je.id as transaction_id,
    je.practice_name,
    je.transaction_date,
    DATE_TRUNC('month', je.transaction_date) as month_date,
    je.account_type,
    je.amount,
    CASE
        WHEN je.account_type IN ('Expense', 'Cost of Goods Sold') THEN 'expense'
        WHEN je.account_type IN ('Income', 'Revenue') THEN 'revenue'
        ELSE 'other'
    END as transaction_type,
    je.description,
    je.created_at
FROM {{ ref('stg_financials') }} je
WHERE je.transaction_date >= DATEADD(MONTH, -24, CURRENT_DATE())  -- 2 years history
```

**Activation Steps:**
1. Create fact_financials.sql
2. Run `dbt run --select fact_financials`
3. Rename `monthly_production_kpis.sql.disabled` → `.sql`
4. Rename `kpi_alerts.sql.disabled` → `.sql`
5. Run `dbt run --select monthly_production_kpis kpi_alerts`
6. Verify: `SELECT COUNT(*) FROM gold.monthly_production_kpis`
7. Verify: `SELECT COUNT(*) FROM gold.kpi_alerts`

**Files Changed:**
- `dbt/dentalerp/models/gold/facts/fact_financials.sql` (new)
- `dbt/dentalerp/models/gold/metrics/monthly_production_kpis.sql` (renamed)
- `dbt/dentalerp/models/gold/metrics/kpi_alerts.sql` (renamed)

---

### Task 4: Implement Forecasting (Snowflake-Native)

**Create dbt Forecast Model:** `dbt/dentalerp/models/gold/forecasts/revenue_forecast.sql`

```sql
{{ config(materialized='table') }}

/*
Gold Layer - Revenue Forecasting using Snowflake ML
Generates 3-6 month revenue projections with confidence intervals
*/

-- Use Snowflake's time series forecasting
SELECT *
FROM TABLE(
    FORECAST(
        input_data => SYSTEM$QUERY_REFERENCE('
            SELECT
                month_date as timestamp,
                total_production as target
            FROM gold.monthly_production_kpis
            ORDER BY month_date
        '),
        series_colname => 'timestamp',
        value_colname => 'target',
        config_object => {'prediction_interval': 3}
    )
)
```

**Update forecasting.py to query results:**

```python
async def forecast_revenue(self, practice_name: str, periods: int = 3, confidence_level: float = 0.95):
    """Query pre-computed Snowflake ML forecasts"""

    # Snowflake does all computation, we just query
    result = await warehouse_router.execute_query("""
        SELECT
            ts as forecast_month,
            forecast as predicted_value,
            lower_bound,
            upper_bound
        FROM gold.revenue_forecast
        WHERE practice_name = %s
        ORDER BY ts
        LIMIT %s
    """, parameters=(practice_name, periods))

    return {
        "practice_name": practice_name,
        "forecasts": result,
        "model": "snowflake_ml_forecast",
        "confidence_level": confidence_level,
        "generated_at": datetime.utcnow().isoformat()
    }
```

**Files Changed:**
- `dbt/dentalerp/models/gold/forecasts/revenue_forecast.sql` (new)
- `mcp-server/src/services/forecasting.py` (fill TODO line 57-74)

---

### Task 5: Implement Anomaly Detection (Snowflake-Native)

**Create dbt Anomaly Model:** `dbt/dentalerp/models/gold/monitoring/production_anomalies.sql`

```sql
{{ config(materialized='table') }}

/*
Gold Layer - Production Anomaly Detection
Z-score based anomaly detection with 12-month rolling baseline
*/

WITH stats AS (
    SELECT
        practice_name,
        month_date,
        total_production,

        -- 12-month rolling statistics
        AVG(total_production) OVER (
            PARTITION BY practice_name
            ORDER BY month_date
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) as avg_12m,

        STDDEV(total_production) OVER (
            PARTITION BY practice_name
            ORDER BY month_date
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) as stddev_12m

    FROM {{ ref('monthly_production_kpis') }}
),

anomalies AS (
    SELECT
        practice_name,
        month_date,
        total_production as actual_value,
        avg_12m as expected_value,

        -- Calculate Z-score
        (total_production - avg_12m) / NULLIF(stddev_12m, 0) as z_score,

        -- Classify severity
        CASE
            WHEN ABS((total_production - avg_12m) / NULLIF(stddev_12m, 0)) > 3.0 THEN 'critical'
            WHEN ABS((total_production - avg_12m) / NULLIF(stddev_12m, 0)) > 2.0 THEN 'warning'
            ELSE 'info'
        END as severity,

        -- Generate message
        CASE
            WHEN (total_production - avg_12m) / NULLIF(stddev_12m, 0) > 2.0 THEN
                'Production anomaly: ' || ROUND(total_production) || ' is ' || ROUND(ABS(z_score), 1) || ' std deviations above normal'
            WHEN (total_production - avg_12m) / NULLIF(stddev_12m, 0) < -2.0 THEN
                'Production anomaly: ' || ROUND(total_production) || ' is ' || ROUND(ABS(z_score), 1) || ' std deviations below normal'
            ELSE 'Normal variance'
        END as alert_message

    FROM stats
    WHERE stddev_12m > 0  -- Need enough history
)

SELECT *
FROM anomalies
WHERE severity IN ('warning', 'critical')
ORDER BY month_date DESC, ABS(z_score) DESC
```

**Update forecasting.py:**

```python
async def detect_anomalies(self, practice_name: str, metric: str = "revenue", sensitivity: float = 2.0):
    """Query pre-computed anomalies from Snowflake"""

    result = await warehouse_router.execute_query("""
        SELECT
            month_date,
            actual_value,
            expected_value,
            z_score,
            severity,
            alert_message
        FROM gold.production_anomalies
        WHERE practice_name = %s
        AND ABS(z_score) >= %s
        ORDER BY month_date DESC
    """, parameters=(practice_name, sensitivity))

    return result
```

**Files Changed:**
- `dbt/dentalerp/models/gold/monitoring/production_anomalies.sql` (new)
- `mcp-server/src/services/forecasting.py` (fill TODO line 125-148)

---

### Task 6: Implement Text-to-Insights (GPT-4)

**Add new method to forecasting.py:**

```python
async def generate_insights(
    self,
    practice_name: Optional[str] = None,
    period: str = "month"
) -> str:
    """
    Generate natural language insights using GPT-4

    Queries Snowflake KPIs and uses GPT-4 to create executive summary
    """

    # Query top practices
    top_practices = await warehouse_router.execute_query("""
        SELECT
            practice_name,
            total_production,
            mom_production_growth_pct,
            profit_margin_pct
        FROM gold.monthly_production_kpis
        WHERE month_date = DATE_TRUNC('month', CURRENT_DATE())
        ORDER BY total_production DESC
        LIMIT 5
    """)

    # Query recent alerts
    alerts = await warehouse_router.execute_query("""
        SELECT practice_name, alert_message, severity
        FROM gold.kpi_alerts
        WHERE month_date >= DATEADD(MONTH, -1, CURRENT_DATE())
        ORDER BY severity DESC, month_date DESC
        LIMIT 10
    """)

    # Build GPT-4 prompt
    prompt = f"""
You are analyzing dental practice financial data. Provide a concise 2-3 sentence executive summary.

Top Practices by Production:
{self._format_kpis_for_prompt(top_practices)}

Recent Alerts:
{self._format_alerts_for_prompt(alerts)}

Format:
"Production [up/down] X% MoM, driven by [location]. Top gains: [list]. Cost changes: [summary]."

Focus on actionable insights, not just numbers.
"""

    # Call GPT-4
    import openai
    openai.api_key = os.getenv('OPENAI_API_KEY')

    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0.7
    )

    insight = response.choices[0].message.content

    # Cache for 1 hour
    return insight
```

**Files Changed:**
- `mcp-server/src/services/forecasting.py` (add generate_insights method)
- `mcp-server/src/api/analytics.py` (add GET /api/v1/analytics/insights endpoint)

---

### Task 7: Complete Alert Delivery

**Slack Webhook Implementation (alerts.py line 127):**

```python
async def _send_slack_alert(self, alert: Dict[str, Any]) -> bool:
    """Send alert to Slack via webhook"""
    import httpx

    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL not configured, skipping")
        return False

    # Format Slack message with blocks
    severity_emoji = {
        'info': 'ℹ️',
        'warning': '⚠️',
        'critical': '🚨'
    }

    message = {
        "text": f"{severity_emoji.get(alert['severity'], '📊')} {alert['alert_message']}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{severity_emoji.get(alert['severity'])} DentalERP Alert"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Practice:* {alert['practice_name']}"},
                    {"type": "mrkdwn", "text": f"*Severity:* {alert['severity'].upper()}"},
                    {"type": "mrkdwn", "text": f"*Metric:* {alert['metric_name']}"},
                    {"type": "mrkdwn", "text": f"*Variance:* {alert['variance_pct']}%"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": alert['alert_message']
                }
            }
        ]
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(webhook_url, json=message)
        return response.status_code == 200
```

**Email SMTP Implementation (alerts.py line 121):**

```python
async def _send_email_alert(self, alert: Dict[str, Any]) -> bool:
    """Send alert via email using SMTP"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('SMTP_FROM', smtp_user)
    to_email = os.getenv('ALERT_EMAIL')

    if not all([smtp_host, smtp_user, smtp_password, to_email]):
        logger.warning("SMTP not fully configured, skipping email")
        return False

    # Create email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"DentalERP Alert: {alert['severity'].upper()} - {alert['practice_name']}"
    msg['From'] = from_email
    msg['To'] = to_email

    # HTML body
    html = f"""
    <html>
      <body>
        <h2>DentalERP Alert</h2>
        <p><strong>Severity:</strong> {alert['severity'].upper()}</p>
        <p><strong>Practice:</strong> {alert['practice_name']}</p>
        <p><strong>Date:</strong> {alert['month_date']}</p>
        <p><strong>Message:</strong> {alert['alert_message']}</p>
        <hr>
        <p><strong>Details:</strong></p>
        <ul>
          <li>Metric: {alert['metric_name']}</li>
          <li>Actual: {alert['actual_value']}</li>
          <li>Expected: {alert['expected_value']}</li>
          <li>Variance: {alert['variance_pct']}%</li>
        </ul>
      </body>
    </html>
    """

    msg.attach(MIMEText(html, 'html'))

    # Send via SMTP
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)

    return True
```

**Add Scheduled Alert Checks (main.py):**

```python
# Hourly alert check
scheduler.add_job(
    check_and_send_alerts,
    'interval',
    hours=1,
    id='hourly_alert_check'
)

# Weekly insights email (Monday 9am)
scheduler.add_job(
    send_weekly_insights,
    CronTrigger(day_of_week='mon', hour=9),
    id='weekly_insights_email'
)

async def check_and_send_alerts():
    """Check for new alerts and send notifications"""
    from src.services.alerts import get_alert_service

    alert_service = get_alert_service()
    alerts = await alert_service.check_kpi_alerts()

    for alert in alerts:
        if not alert_service.should_deduplicate(alert):
            await alert_service.send_alert(alert, [AlertChannel.SLACK, AlertChannel.EMAIL])

async def send_weekly_insights():
    """Send weekly AI insights summary"""
    from src.services.forecasting import get_forecasting_service

    forecasting = get_forecasting_service()
    insights = await forecasting.generate_insights()

    # Send insights via email
    # (Use alert service with custom format)
```

**Files Changed:**
- `mcp-server/src/services/alerts.py` (fill TODOs)
- `mcp-server/src/main.py` (add alert scheduling)
- `mcp-server/.env` (add SMTP/Slack config)

---

## Testing Strategy

### Unit Tests
- Test MERGE upsert logic (insert new, update existing)
- Test dbt models compile
- Test forecasting queries return data
- Test anomaly detection identifies outliers
- Test GPT-4 prompt formatting

### Integration Tests
- End-to-end: NetSuite sync → dbt run → forecast generation
- Alert flow: Anomaly detected → Slack sent → Email sent
- Scheduler: Jobs run on schedule

### Production Verification
- Verify no duplicates after automated sync
- Verify monthly_production_kpis populates
- Verify forecasts generate
- Verify alerts deliver to Slack/email

---

## Environment Variables Required

```bash
# Slack (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alerts@dentalerp.com
SMTP_PASSWORD=...
SMTP_FROM=DentalERP Alerts <alerts@dentalerp.com>
ALERT_EMAIL=executives@silvercreek.com

# Scheduling
NETSUITE_SYNC_SCHEDULE_FULL=0 2 * * *
NETSUITE_SYNC_SCHEDULE_INCREMENTAL=0 */4 * * *
```

---

## Success Criteria

- ✅ NetSuite sync runs automatically (daily full, 4-hour incremental)
- ✅ Zero duplicate records in Bronze layer
- ✅ monthly_production_kpis shows MoM growth
- ✅ kpi_alerts table has variance alerts
- ✅ Forecasting API returns 3-month projections
- ✅ Anomaly detection identifies outliers
- ✅ GPT-4 generates natural language insights
- ✅ Slack receives alerts
- ✅ Email receives weekly insights

---

**Design validated:** 2025-11-08
**Ready for implementation:** Yes
**Estimated time:** 6-7 days
**Approach:** Snowflake-native computation, thin MCP API layer
