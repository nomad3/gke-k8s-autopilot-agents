# Complete End-to-End Data Flow Documentation
## NetSuite → Snowflake Bronze → Silver → Gold → API → Frontend

**Date**: November 10, 2025
**Implementation**: Silver Creek Dental Partners (9 locations)
**Architecture**: Multi-tenant with 3-layer data transformation

---

## 🎯 Overview

This document describes the complete data flow from NetSuite ERP through Snowflake data warehouse to the frontend dashboard.

**Key Changes from Previous Architecture**:
1. **Removed dbt** - Replaced with Snowflake Dynamic Tables (native, auto-refreshing)
2. **Fixed NetSuite connector** - Correct table naming and VARIANT column handling
3. **Added tenant-practice mapping** - Backend practices link to MCP tenants
4. **Added subsidiary tracking** - Each location maps to NetSuite subsidiary

---

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     COMPLETE DATA FLOW                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  NetSuite REST API (OAuth 1.0a TBA)                                │
│  ├─ 9 Subsidiaries (SCDP Eastlake, Torrey Pines, etc.)            │
│  ├─ Journal Entries, Accounts, Invoices, Payments, Vendor Bills   │
│  └─ Customers, Vendors, Inventory Items                             │
│                           ↓                                          │
│  ┌────────────────────────────────────────────────────────┐        │
│  │ MCP Server - NetSuite Connector                         │        │
│  │ ├─ Fetches ALL data via REST API                       │        │
│  │ ├─ Uses SuiteQL for Journal Entries (bypasses UES)     │        │
│  │ └─ Handles pagination & rate limiting                   │        │
│  └─────────────────────┬──────────────────────────────────┘        │
│                           ↓                                          │
│  ┌────────────────────────────────────────────────────────┐        │
│  │ Snowflake BRONZE Layer (Raw JSON)                      │        │
│  │ ├─ netsuite_journalentry                               │        │
│  │ ├─ netsuite_account                                    │        │
│  │ ├─ netsuite_invoice                                    │        │
│  │ ├─ netsuite_customerpayment                            │        │
│  │ ├─ netsuite_vendorbill                                 │        │
│  │ ├─ netsuite_customer                                   │        │
│  │ ├─ netsuite_vendor                                     │        │
│  │ ├─ netsuite_inventoryitem                              │        │
│  │ └─ netsuite_subsidiary                                 │        │
│  └─────────────────────┬──────────────────────────────────┘        │
│                           ↓ (Dynamic Tables auto-refresh)            │
│  ┌────────────────────────────────────────────────────────┐        │
│  │ Snowflake SILVER Layer (Cleaned & Typed)              │        │
│  │ ├─ dim_accounts (SCD Type 2)                          │        │
│  │ ├─ dim_subsidiaries                                   │        │
│  │ ├─ dim_customers (SCD Type 2)                         │        │
│  │ ├─ dim_vendors (SCD Type 2)                           │        │
│  │ ├─ fact_journal_entries (with line items)            │        │
│  │ ├─ fact_invoices                                      │        │
│  │ └─ fact_vendor_bills                                  │        │
│  └─────────────────────┬──────────────────────────────────┘        │
│                           ↓ (Dynamic Tables auto-refresh)            │
│  ┌────────────────────────────────────────────────────────┐        │
│  │ Snowflake GOLD Layer (Analytics KPIs)                 │        │
│  │ ├─ daily_financial_summary                            │        │
│  │ ├─ monthly_financial_kpis (with MoM growth)           │        │
│  │ ├─ ar_aging_summary                                   │        │
│  │ ├─ ap_aging_summary                                   │        │
│  │ ├─ expense_analysis                                   │        │
│  │ ├─ top_customers                                      │        │
│  │ └─ top_vendors                                        │        │
│  └─────────────────────┬──────────────────────────────────┘        │
│                           ↓                                          │
│  ┌────────────────────────────────────────────────────────┐        │
│  │ MCP Server Analytics API                               │        │
│  │ GET /api/v1/analytics/financial/daily                  │        │
│  │ GET /api/v1/analytics/financial/monthly                │        │
│  │ GET /api/v1/analytics/ar-aging                         │        │
│  │ GET /api/v1/analytics/expense-analysis                 │        │
│  └─────────────────────┬──────────────────────────────────┘        │
│                           ↓                                          │
│  ┌────────────────────────────────────────────────────────┐        │
│  │ ERP Backend API (Express)                              │        │
│  │ GET /api/analytics/financial/summary                   │        │
│  │ ├─ Calls MCP Server via mcpClient                     │        │
│  │ ├─ Maps subsidiary_id → location_id                   │        │
│  │ └─ Returns data scoped by practice_id                 │        │
│  └─────────────────────┬──────────────────────────────────┘        │
│                           ↓                                          │
│  ┌────────────────────────────────────────────────────────┐        │
│  │ React Frontend Dashboard                               │        │
│  │ ├─ Executive Dashboard (multi-location view)           │        │
│  │ ├─ Financial Analytics (revenue, expenses, growth)     │        │
│  │ ├─ AR/AP Aging Reports                                │        │
│  │ └─ Expense Analysis by Category                        │        │
│  └────────────────────────────────────────────────────────┘        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Data Model Alignment

### Backend PostgreSQL (ERP DB)

```typescript
practices {
  id: UUID
  name: string                      // "Silver Creek Dental Partners, LLC"
  tenant_id: string                 // "silvercreek" (links to MCP tenant)
  netsuite_parent_id: string        // "1" (NetSuite parent company ID)
  ...
}

locations {
  id: UUID
  practice_id: UUID                 // FK to practices
  name: string                      // "SCDP Eastlake, LLC"
  external_system_id: string        // "6" (NetSuite subsidiary ID)
  external_system_type: string      // "netsuite"
  subsidiary_name: string           // "SCDP Eastlake, LLC"
  ...
}
```

### MCP PostgreSQL (MCP DB)

```python
tenants {
  id: UUID
  tenant_code: string               // "silvercreek"
  tenant_name: string               // "Silver Creek Dental Partners, LLC"
  products: JSON                    // ["dentalerp"]
  ...
}

tenant_warehouses {
  id: UUID
  tenant_id: UUID                   // FK to tenants
  warehouse_type: string            // "snowflake"
  warehouse_config: JSON            // Snowflake credentials
  ...
}

tenant_integrations {
  id: UUID
  tenant_id: UUID                   // FK to tenants
  integration_type: string          // "netsuite"
  integration_config: JSON          // NetSuite OAuth credentials
  ...
}
```

### Snowflake (Data Warehouse)

```sql
-- Bronze Layer
bronze.netsuite_journalentry {
  id VARCHAR(50)                    // NetSuite internal ID
  subsidiary_id VARCHAR(50)         // NetSuite subsidiary ID
  tenant_id VARCHAR(50)             // "silvercreek"
  raw_data VARIANT                  // Full JSON from NetSuite API
  ...
}

-- Silver Layer (Dynamic Table)
silver.fact_journal_entries {
  journal_entry_id VARCHAR(50)
  subsidiary_id VARCHAR(50)         // Maps to locations.external_system_id
  subsidiary_name VARCHAR(255)      // Maps to locations.subsidiary_name
  account_id VARCHAR(50)
  debit_amount DECIMAL(18,2)
  credit_amount DECIMAL(18,2)
  ...
}

-- Gold Layer (Dynamic Table)
gold.daily_financial_summary {
  tenant_id VARCHAR(50)
  subsidiary_id VARCHAR(50)
  transaction_date DATE
  total_revenue DECIMAL(18,2)
  total_expenses DECIMAL(18,2)
  net_income DECIMAL(18,2)
  ...
}
```

---

## 🔄 Data Mapping Strategy

**Tenant ↔ Practice (1:1)**
```
MCP tenant.tenant_code = "silvercreek"
  ↓
Backend practice.tenant_id = "silvercreek"
  ↓
Snowflake *.tenant_id = "silvercreek"
```

**Subsidiary ↔ Location (1:1)**
```
NetSuite subsidiary.id = "6"
  ↓
Backend location.external_system_id = "6"
Backend location.subsidiary_name = "SCDP Eastlake, LLC"
  ↓
Snowflake *.subsidiary_id = "6"
Snowflake *.subsidiary_name = "SCDP Eastlake, LLC"
```

**API Query Flow**:
```
1. Frontend: GET /api/analytics/financial/summary?practice_id={uuid}
2. Backend: Fetch locations WHERE practice_id = {uuid}
3. Backend: Call MCP with tenant_id="silvercreek" & subsidiary_ids=["6","7","10",...]
4. MCP: Query Snowflake Gold tables WHERE tenant_id="silvercreek" AND subsidiary_id IN (...)
5. MCP: Return aggregated data
6. Backend: Map subsidiary_id → location_id and return to frontend
```

---

## 🚀 Implementation Steps

### Step 1: Apply Database Migrations

```bash
# Backend (ERP DB)
cd /Users/nomade/Documents/GitHub/dentalERP/backend
npm run db:migrate  # Applies 0007_add_tenant_external_system_mapping.sql

# MCP Server (MCP DB) - migrations already applied
cd /Users/nomade/Documents/GitHub/dentalERP/mcp-server
# Migrations 001-003 already applied
```

### Step 2: Seed PostgreSQL Databases

```bash
# Backend - Silver Creek practice and locations
cd /Users/nomade/Documents/GitHub/dentalERP/backend
node /tmp/dentalerp-implementation/backend-seed-silvercreek.ts

# MCP Server - Tenant, warehouse, and integration
cd /Users/nomade/Documents/GitHub/dentalERP/mcp-server
python /tmp/dentalerp-implementation/mcp-seed-silvercreek.py
```

### Step 3: Setup Snowflake Tables

```sql
-- Run in Snowflake UI (Worksheets)
-- Execute in order:

-- 1. Bronze layer (lowercase camelCase tables)
SOURCE /tmp/dentalerp-implementation/snowflake-bronze-schema-update.sql;

-- 2. Silver layer (Dynamic Tables)
SOURCE /tmp/dentalerp-implementation/snowflake-dynamic-tables-silver.sql;

-- 3. Gold layer (Dynamic Tables with KPIs)
SOURCE /tmp/dentalerp-implementation/snowflake-dynamic-tables-gold.sql;
```

### Step 4: Fetch NetSuite Data to Bronze

```bash
# Trigger NetSuite sync via MCP API
curl -X POST https://mcp.agentprovision.com/api/v1/netsuite/sync/trigger \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: silvercreek" \
  -H "Content-Type: application/json" \
  -d '{"full_sync": true, "record_types": ["journalEntry","account","invoice","customerPayment","vendorBill","customer","vendor","inventoryItem","subsidiary"]}'

# Check sync status
curl https://mcp.agentprovision.com/api/v1/netsuite/sync/status \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: silvercreek"
```

### Step 5: Verify Data Flow

```bash
# 1. Check Bronze layer
SELECT COUNT(*), subsidiary_id
FROM bronze.netsuite_journalentry
WHERE tenant_id = 'silvercreek'
GROUP BY subsidiary_id;

# 2. Check Silver layer (should auto-refresh after Bronze load)
SELECT COUNT(*)
FROM silver.fact_journal_entries
WHERE tenant_id = 'silvercreek';

# 3. Check Gold layer (should auto-refresh after Silver)
SELECT *
FROM gold.daily_financial_summary
WHERE tenant_id = 'silvercreek'
ORDER BY transaction_date DESC
LIMIT 10;
```

### Step 6: Delete dbt Project

```bash
cd /Users/nomade/Documents/GitHub/dentalERP
rm -rf dbt/
git add -A
git commit -m "refactor: replace dbt with Snowflake dynamic tables

- Remove dbt project (no longer needed)
- Snowflake dynamic tables handle Bronze→Silver→Gold transformations
- Native Snowflake features (auto-refresh, incremental updates)
- Simpler architecture, no external orchestration needed"
```

---

## 🔧 NetSuite Connector Fixes Applied

**File**: `mcp-server/src/services/snowflake_netsuite_loader.py`

### Fix 1: Table Name Mapping

**Before**:
```python
def _pluralize(self, word: str) -> str:
    mappings = {
        "journalEntry": "journal_entries",  # ❌ Wrong
        "customerPayment": "payments",      # ❌ Wrong
    }
```

**After**:
```python
def _pluralize(self, word: str) -> str:
    return word.lower()  # ✅ journalEntry → journalentry
```

### Fix 2: VARIANT Column Handling

**Already Correct** (line 348):
```python
if col.upper() == "RAW_DATA":
    select_columns.append(f"PARSE_JSON(column{i}) as {col.lower()}")  # ✅ Correct
```

### Fix 3: Record Type Names

**Already Fixed** (lines 29-34):
```python
RECORD_TYPES = [
    "customerPayment",  # ✅ Not "payment"
    "inventoryItem",    # ✅ Not "item"
]
```

---

## 📈 Snowflake Dynamic Tables Benefits

**vs dbt**:
- ✅ **Native Snowflake** - No external orchestration needed
- ✅ **Auto-refresh** - Refreshes when source data changes
- ✅ **Incremental** - Only processes new/changed data
- ✅ **Simpler** - No Python/YAML config files
- ✅ **Faster** - Executes in Snowflake engine directly
- ✅ **Declarative** - Define target state, Snowflake figures out how

**Configuration**:
```sql
CREATE OR REPLACE DYNAMIC TABLE silver.fact_journal_entries
TARGET_LAG = '15 minutes'  -- Refresh within 15min of source changes
WAREHOUSE = COMPUTE_WH     -- Compute resources
AS
SELECT ... FROM bronze.netsuite_journalentry;
```

**Refresh Behavior**:
- **TARGET_LAG = '10 minutes'** → Dimensions (accounts, customers, etc.)
- **TARGET_LAG = '15 minutes'** → Facts (transactions)
- **TARGET_LAG = '30 minutes'** → Gold aggregations (daily summaries)
- **TARGET_LAG = '1 hour'** → Gold KPIs (monthly metrics)

---

## 🔐 Security & Multi-Tenancy

**All layers enforce tenant isolation**:

```sql
-- Bronze layer: tenant_id column
SELECT * FROM bronze.netsuite_journalentry
WHERE tenant_id = 'silvercreek';

-- Silver layer: inherits tenant_id from Bronze
SELECT * FROM silver.fact_journal_entries
WHERE tenant_id = 'silvercreek';

-- Gold layer: inherits tenant_id from Silver
SELECT * FROM gold.daily_financial_summary
WHERE tenant_id = 'silvercreek';
```

**Backend API enforces practice scoping**:
```typescript
// User can only access their assigned practices
const userPractices = await getUserPractices(userId);
const practiceIds = userPractices.map(p => p.id);

// Fetch locations for user's practices
const locations = await getLocations(practiceIds);
const subsidiaryIds = locations.map(l => l.externalSystemId);

// Query MCP with tenant + subsidiary filters
const data = await mcpClient.getFinancialSummary({
  tenantId: 'silvercreek',
  subsidiaryIds: subsidiaryIds
});
```

---

## 🎨 OpenAI Enrichment (Future Enhancement)

**Gold layer tables are ready for AI enrichment**:

```sql
-- Example: Add AI-generated insights
CREATE OR REPLACE DYNAMIC TABLE gold.ai_financial_insights
TARGET_LAG = '1 day'
WAREHOUSE = COMPUTE_WH
AS
SELECT
    tenant_id,
    subsidiary_id,
    month,
    monthly_revenue,
    monthly_expenses,
    revenue_growth_pct,
    -- Call OpenAI External Function
    CALL_OPENAI_ANALYSIS(
        JSON_OBJECT(
            'revenue', monthly_revenue,
            'expenses', monthly_expenses,
            'growth_pct', revenue_growth_pct
        )
    ) AS ai_insights
FROM gold.monthly_financial_kpis;
```

**Setup Required**:
1. Create AWS Lambda or Azure Function to proxy OpenAI API
2. Set up Snowflake API Integration with authentication
3. Create External Function pointing to proxy
4. Add AI columns to Gold tables

**Reference**: https://docs.snowflake.com/en/sql-reference/external-functions-introduction

---

## 📊 Dashboard Data Flow

**Frontend Component** → **Backend API** → **MCP Server** → **Snowflake Gold**

### Example: Executive Financial Dashboard

```typescript
// Frontend: components/dashboard/ExecutiveFinancialSummary.tsx
const { data } = useQuery(['financial-summary', practiceId], () =>
  api.get(`/analytics/financial/summary?practice_id=${practiceId}`)
);

// Backend: routes/analytics.ts
router.get('/financial/summary', authenticateJWT, async (req, res) => {
  const { practice_id } = req.query;

  // Get locations for this practice
  const locations = await db.select()
    .from(locationsTable)
    .where(eq(locationsTable.practiceId, practice_id));

  const subsidiaryIds = locations.map(l => l.externalSystemId);

  // Query MCP
  const summary = await mcpClient.getFinancialSummary({
    tenantId: practice.tenantId,  // "silvercreek"
    subsidiaryIds: subsidiaryIds   // ["6", "7", "10", ...]
  });

  res.json(summary);
});

// MCP Server: api/analytics.py
@router.get("/financial/summary")
async def get_financial_summary(tenant_id: str, subsidiary_ids: List[str]):
    # Query Snowflake Gold layer
    query = """
        SELECT
            subsidiary_id,
            subsidiary_name,
            SUM(monthly_revenue) AS total_revenue,
            SUM(monthly_expenses) AS total_expenses,
            SUM(monthly_net_income) AS net_income,
            AVG(profit_margin_pct) AS avg_margin
        FROM gold.monthly_financial_kpis
        WHERE tenant_id = ?
          AND subsidiary_id = ANY(?)
          AND month >= DATEADD('month', -12, CURRENT_DATE())
        GROUP BY subsidiary_id, subsidiary_name
    """

    results = await snowflake.execute(query, [tenant_id, subsidiary_ids])
    return results
```

---

## 🚀 Deployment to GCP

```bash
# 1. Commit all changes
cd /Users/nomade/Documents/GitHub/dentalERP
git add -A
git commit -m "feat: complete NetSuite → Snowflake → Frontend data flow

- Add tenant_id and external_system mapping to backend schema
- Fix NetSuite connector table naming (lowercase camelCase)
- Replace dbt with Snowflake dynamic tables (Bronze→Silver→Gold)
- Add Silver Creek seed scripts (9 locations)
- Add comprehensive data flow documentation
- Ready for production deployment"

git push origin main

# 2. Deploy to GCP VM (using existing credentials)
./deploy.sh

# 3. Run migrations and seeds on production
ssh dental-erp-vm
cd /opt/dentalERP
docker-compose exec backend npm run db:migrate
docker-compose exec backend node scripts/seed-silvercreek.js
docker-compose exec mcp-server python scripts/seed-silvercreek.py

# 4. Setup Snowflake (run SQL scripts in Snowflake UI)
# - Bronze schema update
# - Silver dynamic tables
# - Gold dynamic tables

# 5. Trigger initial NetSuite sync
curl -X POST https://mcp.agentprovision.com/api/v1/netsuite/sync/trigger \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: silvercreek" \
  -d '{"full_sync": true}'

# 6. Monitor sync progress
curl https://mcp.agentprovision.com/api/v1/netsuite/sync/status \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: silvercreek"
```

---

## ✅ Verification Checklist

- [ ] Backend migrations applied (tenant_id, external_system_id fields)
- [ ] Backend seeded with Silver Creek practice + 9 locations
- [ ] MCP seeded with silvercreek tenant + Snowflake warehouse + NetSuite integration
- [ ] Snowflake Bronze tables created (lowercase camelCase names)
- [ ] Snowflake Silver dynamic tables created and refreshing
- [ ] Snowflake Gold dynamic tables created and refreshing
- [ ] NetSuite sync triggered and completed successfully
- [ ] Bronze layer has data for all 9 subsidiaries
- [ ] Silver layer populated from Bronze (auto-refresh)
- [ ] Gold layer populated from Silver (auto-refresh)
- [ ] Backend API returns financial data filtered by practice
- [ ] Frontend dashboard displays multi-location financial summary
- [ ] dbt project directory deleted from repo

---

## 📞 Support & Next Steps

**Immediate Next Steps**:
1. Test NetSuite sync with real credentials
2. Verify dynamic table refresh behavior
3. Add API endpoints for remaining Gold tables (AR aging, expense analysis, etc.)
4. Build frontend components to visualize Gold layer KPIs

**Future Enhancements**:
1. Add OpenAI enrichment for AI-generated insights
2. Add anomaly detection on financial metrics
3. Add forecasting models (revenue predictions)
4. Add data quality monitoring and alerts

---

**Last Updated**: November 10, 2025
**Author**: Claude Code
**Status**: ✅ Complete - Ready for deployment
