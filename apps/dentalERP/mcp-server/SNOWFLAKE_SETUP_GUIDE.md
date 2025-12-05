# ❄️ Snowflake Setup & Testing Guide

Complete guide to setting up Snowflake for the MCP Server and testing the integration.

---

## 📋 Prerequisites

1. **Snowflake Account**: You need a Snowflake account (trial or paid)
2. **Snowflake User**: User with appropriate permissions
3. **Python Environment**: MCP Server with dependencies installed

---

## 🚀 Step 1: Get a Snowflake Account

### Option A: Free Trial (Recommended for Testing)

1. Visit https://signup.snowflake.com/
2. Sign up for a **30-day free trial**
3. Choose your cloud provider:
   - **AWS** (most common)
   - Azure
   - Google Cloud
4. Choose your region (e.g., `US East (Ohio)`)
5. Complete registration

You'll receive:
- **Account Identifier**: e.g., `xyz12345.us-east-1`
- **Username**: e.g., `ADMIN` or your email
- **Password**: Set during registration

### Option B: Existing Snowflake Account

If you already have access:
1. Get your **Account Identifier** from your admin
2. Get your **Username** and **Password**
3. Ensure you have permissions to create databases, schemas, and tables

---

## 🔑 Step 2: Find Your Snowflake Connection Details

### Important Note on Authentication

**Snowflake Authentication Methods**:
- ✅ **Username/Password**: Simplest (we use this for getting started)
- ✅ **Key-Pair Authentication**: Most secure for production (recommended)
- ✅ **OAuth**: Enterprise SSO integration
- ✅ **Programmatic Access Tokens (PAT)**: Newer method

**Our implementation uses `snowflake-connector-python`** (the official Python library), which is the **recommended approach** by Snowflake. We do NOT use the REST API directly as the Python connector provides better performance, connection pooling, and native integration.

For detailed authentication options, see: `SNOWFLAKE_AUTHENTICATION.md`

### 2.1 Account Identifier

Your Snowflake account identifier has the format: `<account_locator>.<region>.<cloud>`

**Example**: `xy12345.us-east-1.aws` or `organization-account_name`

**How to find it**:

1. **From Snowflake Web UI**:
   - Log in to https://app.snowflake.com/
   - Look at the URL: `https://app.snowflake.com/<account_identifier>/...`
   - Example: `https://app.snowflake.com/xy12345.us-east-1.aws/`

2. **From Snowflake SQL**:
   ```sql
   SELECT CURRENT_ACCOUNT();
   -- Returns: XY12345

   SELECT CURRENT_REGION();
   -- Returns: AWS_US_EAST_1
   ```

3. **Full format**:
   - **Legacy format**: `<account_locator>.<region>`
   - **New format**: `<organization>-<account_name>`
   - Both work with the connector

### 2.2 Warehouse Name

Warehouses provide compute power. You need at least one.

**Default**: Most accounts come with `COMPUTE_WH`

**How to check**:
```sql
SHOW WAREHOUSES;
```

**Create if needed**:
```sql
CREATE WAREHOUSE IF NOT EXISTS DENTAL_ERP_WH
WITH
  WAREHOUSE_SIZE = 'X-SMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;
```

**Size Guide**:
- `X-SMALL`: Development/testing (2 credits/hour)
- `SMALL`: Light production (4 credits/hour)
- `MEDIUM`: Moderate production (8 credits/hour)
- `LARGE`: Heavy production (16 credits/hour)

### 2.3 Database & Schema

**Create database**:
```sql
CREATE DATABASE IF NOT EXISTS DENTAL_ERP_DW;
USE DATABASE DENTAL_ERP_DW;
```

**Create schemas for Bronze/Silver/Gold**:
```sql
CREATE SCHEMA IF NOT EXISTS BRONZE;
CREATE SCHEMA IF NOT EXISTS SILVER;
CREATE SCHEMA IF NOT EXISTS GOLD;
```

### 2.4 User & Role

**Default**: Your account comes with `ACCOUNTADMIN` role

**Check current user**:
```sql
SELECT CURRENT_USER();
SELECT CURRENT_ROLE();
```

**Create dedicated role for MCP (recommended)**:
```sql
-- Create role
CREATE ROLE IF NOT EXISTS MCP_ROLE;

-- Grant permissions
GRANT USAGE ON WAREHOUSE DENTAL_ERP_WH TO ROLE MCP_ROLE;
GRANT USAGE ON DATABASE DENTAL_ERP_DW TO ROLE MCP_ROLE;
GRANT USAGE ON SCHEMA DENTAL_ERP_DW.BRONZE TO ROLE MCP_ROLE;
GRANT USAGE ON SCHEMA DENTAL_ERP_DW.SILVER TO ROLE MCP_ROLE;
GRANT USAGE ON SCHEMA DENTAL_ERP_DW.GOLD TO ROLE MCP_ROLE;

-- Grant table permissions
GRANT CREATE TABLE ON SCHEMA DENTAL_ERP_DW.BRONZE TO ROLE MCP_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA DENTAL_ERP_DW.BRONZE TO ROLE MCP_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA DENTAL_ERP_DW.BRONZE TO ROLE MCP_ROLE;

GRANT SELECT ON ALL TABLES IN SCHEMA DENTAL_ERP_DW.SILVER TO ROLE MCP_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA DENTAL_ERP_DW.SILVER TO ROLE MCP_ROLE;

GRANT SELECT ON ALL TABLES IN SCHEMA DENTAL_ERP_DW.GOLD TO ROLE MCP_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA DENTAL_ERP_DW.GOLD TO ROLE MCP_ROLE;

-- Create user for MCP Server
CREATE USER IF NOT EXISTS MCP_USER
  PASSWORD = 'YourSecurePassword123!'
  DEFAULT_ROLE = MCP_ROLE
  DEFAULT_WAREHOUSE = DENTAL_ERP_WH;

-- Assign role to user
GRANT ROLE MCP_ROLE TO USER MCP_USER;
```

---

## ⚙️ Step 3: Configure MCP Server

### 3.1 Environment Variables

Create or update `mcp-server/.env`:

```bash
# Snowflake Connection (REQUIRED)
SNOWFLAKE_ACCOUNT=xy12345.us-east-1.aws
SNOWFLAKE_USER=MCP_USER
SNOWFLAKE_PASSWORD=YourSecurePassword123!
SNOWFLAKE_WAREHOUSE=DENTAL_ERP_WH
SNOWFLAKE_DATABASE=DENTAL_ERP_DW
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=MCP_ROLE

# MCP Server (must be set for API authentication)
MCP_API_KEY=dev-mcp-api-key-change-in-production-min-32-chars
SECRET_KEY=your-secret-key-for-jwt

# Database
POSTGRES_HOST=postgres
POSTGRES_DB=mcp
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
```

### 3.2 Docker Compose (if using Docker)

Update `docker-compose.yml` to include Snowflake env vars:

```yaml
mcp-server:
  environment:
    # ... existing vars ...
    SNOWFLAKE_ACCOUNT: ${SNOWFLAKE_ACCOUNT}
    SNOWFLAKE_USER: ${SNOWFLAKE_USER}
    SNOWFLAKE_PASSWORD: ${SNOWFLAKE_PASSWORD}
    SNOWFLAKE_WAREHOUSE: ${SNOWFLAKE_WAREHOUSE:-COMPUTE_WH}
    SNOWFLAKE_DATABASE: ${SNOWFLAKE_DATABASE:-DENTAL_ERP_DW}
    SNOWFLAKE_SCHEMA: ${SNOWFLAKE_SCHEMA:-PUBLIC}
    SNOWFLAKE_ROLE: ${SNOWFLAKE_ROLE}
```

---

## 🧪 Step 4: Test the Connection

### 4.1 Quick Connection Test (Python)

```bash
cd mcp-server

# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Test connection
python -c "
from src.connectors.snowflake import get_snowflake_connector
import asyncio

async def test():
    connector = get_snowflake_connector()
    if connector.is_enabled:
        connected = await connector.test_connection()
        if connected:
            print('✅ Snowflake connection successful!')
        else:
            print('❌ Connection failed. Check credentials.')
    else:
        print('❌ Snowflake not configured. Check .env file.')

asyncio.run(test())
"
```

### 4.2 Test via MCP API (when server is running)

```bash
# Start MCP Server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8085

# In another terminal, test warehouse status
curl -X GET http://localhost:8085/api/v1/warehouse/status \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" | jq

# Expected response:
# {
#   "connected": true,
#   "warehouse": {
#     "warehouse": "DENTAL_ERP_WH",
#     "database": "DENTAL_ERP_DW",
#     "schema": "PUBLIC",
#     "version": "8.2.0"
#   },
#   "layers": {
#     "bronze": {"table_count": 0},
#     "silver": {"table_count": 0},
#     "gold": {"table_count": 0}
#   },
#   "timestamp": "2025-10-29T12:00:00.000Z"
# }
```

---

## 📊 Step 5: Create Sample Bronze Tables

### 5.1 Create Bronze Layer Table

```sql
-- Switch to Bronze schema
USE SCHEMA DENTAL_ERP_DW.BRONZE;

-- Create a sample Bronze table for NetSuite data
CREATE TABLE IF NOT EXISTS bronze.netsuite_journalentry (
    id VARCHAR(255) PRIMARY KEY,
    source_system VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    raw_data VARIANT NOT NULL,
    extracted_at TIMESTAMP_LTZ NOT NULL,
    loaded_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
    batch_id VARCHAR(255),
    correlation_id VARCHAR(255)
);

-- Add clustering for better query performance
ALTER TABLE bronze.netsuite_journalentry
CLUSTER BY (source_system, entity_type, extracted_at);
```

### 5.2 Insert Sample Data

```sql
-- Insert test record
INSERT INTO bronze.netsuite_journalentry
(id, source_system, entity_type, raw_data, extracted_at)
SELECT
    'test_' || UUID_STRING() AS id,
    'netsuite' AS source_system,
    'journalentry' AS entity_type,
    PARSE_JSON('{
        "internalId": "12345",
        "tranId": "JE-001",
        "tranDate": "2024-11-01",
        "amount": 1500.00,
        "currency": "USD",
        "status": "approved",
        "memo": "Test journal entry"
    }') AS raw_data,
    CURRENT_TIMESTAMP() AS extracted_at;

-- Verify insertion
SELECT * FROM bronze.netsuite_journalentry;
```

---

## 🔄 Step 6: Test Data Sync via MCP

### 6.1 Trigger Sync Job

```bash
# Trigger a sync to load data to Bronze layer
curl -X POST http://localhost:8085/api/v1/sync/run \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  -H "Content-Type: application/json" \
  -d '{
    "integration_type": "netsuite",
    "entity_types": ["journalentry"],
    "location_ids": ["downtown"],
    "sync_mode": "incremental"
  }' | jq

# Response:
# {
#   "sync_id": "sync_abc123xyz",
#   "status": "pending",
#   "message": "Sync job created successfully"
# }
```

### 6.2 Check Sync Status

```bash
# Check sync status
curl -X GET http://localhost:8085/api/v1/sync/sync_abc123xyz \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" | jq

# Response:
# {
#   "id": "sync_abc123xyz",
#   "status": "completed",
#   "records_processed": 150,
#   "started_at": "2025-10-29T12:00:00Z",
#   "completed_at": "2025-10-29T12:00:05Z"
# }
```

### 6.3 Verify Data in Bronze Layer

```sql
-- Check if data was loaded
SELECT
    source_system,
    entity_type,
    COUNT(*) as record_count,
    MAX(extracted_at) as latest_extraction
FROM bronze.netsuite_journalentry
GROUP BY 1, 2;
```

---

## 🏗️ Step 7: Create Gold Layer for Testing

### 7.1 Create Sample Gold Table

```sql
USE SCHEMA DENTAL_ERP_DW.GOLD;

-- Create monthly production KPIs table
CREATE TABLE IF NOT EXISTS gold.monthly_production_kpis (
    practice_name VARCHAR(100),
    month_date DATE,
    year_month VARCHAR(7),
    total_production DECIMAL(18,2),
    total_expenses DECIMAL(18,2),
    net_income DECIMAL(18,2),
    profit_margin_pct DECIMAL(5,2),
    mom_production_growth_pct DECIMAL(5,2),
    PRIMARY KEY (practice_name, month_date)
);

-- Insert sample data for testing
INSERT INTO gold.monthly_production_kpis VALUES
('downtown', '2024-10-01', '2024-10', 250000.00, 180000.00, 70000.00, 28.0, 5.2),
('downtown', '2024-11-01', '2024-11', 262500.00, 185000.00, 77500.00, 29.5, 5.0),
('eastside', '2024-10-01', '2024-10', 180000.00, 135000.00, 45000.00, 25.0, 3.8),
('eastside', '2024-11-01', '2024-11', 189000.00, 138000.00, 51000.00, 27.0, 5.0);

-- Verify data
SELECT * FROM gold.monthly_production_kpis ORDER BY practice_name, month_date DESC;
```

### 7.2 Test Gold Layer Queries via MCP

```bash
# Query financial summary (should return data from Gold layer)
curl -X GET "http://localhost:8085/api/v1/finance/summary?location=downtown&from=2024-01-01&to=2024-12-31" \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" | jq

# Expected response:
# {
#   "location_id": "downtown",
#   "revenue": 512500.00,
#   "expenses": 365000.00,
#   "net_income": 147500.00,
#   "payroll_costs": 164250.00,
#   "date_range": {
#     "from": "2024-01-01",
#     "to": "2024-12-31"
#   },
#   "breakdown": [
#     {
#       "month": "2024-11",
#       "revenue": 262500.00,
#       "growth_rate": 5.0
#     },
#     {
#       "month": "2024-10",
#       "revenue": 250000.00,
#       "growth_rate": 5.2
#     }
#   ]
# }
```

---

## 🧪 Step 8: Advanced Testing

### 8.1 Test Bronze Layer Status

```bash
curl -X GET http://localhost:8085/api/v1/warehouse/bronze/status \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" | jq
```

### 8.2 Test Data Freshness Check

```bash
curl -X GET "http://localhost:8085/api/v1/warehouse/freshness?threshold_hours=24" \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" | jq
```

### 8.3 Test Custom Query

```bash
curl -X GET "http://localhost:8085/api/v1/warehouse/query?sql=SELECT%20*%20FROM%20gold.monthly_production_kpis%20LIMIT%205" \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" | jq
```

---

## 🔧 Troubleshooting

### Issue: "Connection refused" or "Authentication failed"

**Check credentials**:
```bash
# Verify env vars are loaded
cd mcp-server
python -c "from src.core.config import settings; print(f'Account: {settings.snowflake_account}'); print(f'User: {settings.snowflake_user}')"
```

**Test with snowsql CLI** (optional):
```bash
# Install snowsql
# https://docs.snowflake.com/en/user-guide/snowsql-install-config.html

# Test connection
snowsql -a xy12345.us-east-1.aws -u MCP_USER
# Enter password when prompted

# If successful, run:
SELECT CURRENT_VERSION();
```

### Issue: "Database does not exist"

```sql
-- Create database
CREATE DATABASE IF NOT EXISTS DENTAL_ERP_DW;

-- Create schemas
USE DATABASE DENTAL_ERP_DW;
CREATE SCHEMA IF NOT EXISTS BRONZE;
CREATE SCHEMA IF NOT EXISTS SILVER;
CREATE SCHEMA IF NOT EXISTS GOLD;
```

### Issue: "Insufficient privileges"

```sql
-- Grant permissions (as ACCOUNTADMIN)
USE ROLE ACCOUNTADMIN;

GRANT USAGE ON WAREHOUSE DENTAL_ERP_WH TO ROLE MCP_ROLE;
GRANT USAGE ON DATABASE DENTAL_ERP_DW TO ROLE MCP_ROLE;
GRANT ALL ON SCHEMA DENTAL_ERP_DW.BRONZE TO ROLE MCP_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA DENTAL_ERP_DW.GOLD TO ROLE MCP_ROLE;
```

### Issue: "Warehouse suspended"

```sql
-- Resume warehouse
ALTER WAREHOUSE DENTAL_ERP_WH RESUME;

-- Check warehouse status
SHOW WAREHOUSES LIKE 'DENTAL_ERP_WH';
```

### Issue: Python connector import error

```bash
# Reinstall Snowflake connector
pip install --upgrade snowflake-connector-python

# Verify installation
python -c "import snowflake.connector; print(snowflake.connector.__version__)"
```

---

## 📊 Performance Monitoring

### Check Warehouse Usage

```sql
-- Query history (last 24 hours)
SELECT
    query_text,
    execution_status,
    total_elapsed_time / 1000 as execution_time_seconds,
    warehouse_name
FROM TABLE(information_schema.query_history())
WHERE start_time >= DATEADD(day, -1, CURRENT_TIMESTAMP())
ORDER BY start_time DESC
LIMIT 100;
```

### Check Credit Usage

```sql
-- Warehouse credit usage
SELECT
    warehouse_name,
    SUM(credits_used) as total_credits
FROM TABLE(information_schema.warehouse_metering_history(
    dateadd('days', -7, current_date())
))
GROUP BY warehouse_name;
```

---

## ✅ Success Checklist

- [ ] Snowflake account created and accessible
- [ ] Account identifier identified
- [ ] Database `DENTAL_ERP_DW` created
- [ ] Schemas `BRONZE`, `SILVER`, `GOLD` created
- [ ] Warehouse created and running
- [ ] User with appropriate permissions created
- [ ] MCP `.env` file configured with Snowflake credentials
- [ ] Python connection test passes
- [ ] MCP API warehouse status returns success
- [ ] Sample Bronze table created
- [ ] Sample Gold table created with test data
- [ ] MCP can query Gold layer successfully
- [ ] Data sync job completes successfully

---

## 📚 Additional Resources

- **Snowflake Documentation**: https://docs.snowflake.com/
- **Snowflake Connector Python**: https://docs.snowflake.com/en/user-guide/python-connector.html
- **MCP Snowflake Orchestration Guide**: `/mcp-server/SNOWFLAKE_ORCHESTRATION.md`
- **Snowflake Free Trial**: https://signup.snowflake.com/
- **Snowflake University** (free training): https://learn.snowflake.com/

---

## 💡 Quick Start Summary

```bash
# 1. Sign up for Snowflake free trial
https://signup.snowflake.com/

# 2. Get your credentials:
#    - Account: xy12345.us-east-1.aws
#    - Username: ADMIN (or your email)
#    - Password: (set during signup)

# 3. Create database & schemas (in Snowflake Web UI):
CREATE DATABASE DENTAL_ERP_DW;
CREATE SCHEMA DENTAL_ERP_DW.BRONZE;
CREATE SCHEMA DENTAL_ERP_DW.SILVER;
CREATE SCHEMA DENTAL_ERP_DW.GOLD;

# 4. Configure MCP Server:
cd mcp-server
cat > .env.snowflake << EOF
SNOWFLAKE_ACCOUNT=xy12345.us-east-1.aws
SNOWFLAKE_USER=ADMIN
SNOWFLAKE_PASSWORD=YourPassword123!
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=DENTAL_ERP_DW
SNOWFLAKE_SCHEMA=PUBLIC
EOF

# 5. Test connection:
python -c "from src.connectors.snowflake import get_snowflake_connector; import asyncio; connector = get_snowflake_connector(); print('✅ Connected' if asyncio.run(connector.test_connection()) else '❌ Failed')"

# 6. Start MCP Server:
uvicorn src.main:app --reload --host 0.0.0.0 --port 8085

# 7. Test API:
curl http://localhost:8085/api/v1/warehouse/status \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars"
```

---

**Last Updated**: October 29, 2025
**Status**: ✅ Production Ready
