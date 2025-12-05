# Multi-Subsidiary NetSuite & Frontend Enhancement Design

**Date:** 2025-11-08
**Status:** Validated
**Scope:** Fix multi-practice data ingestion + display real financial data on frontend

---

## Problem Statement

**Critical Issue:** NetSuite connector pulling data from ONLY 1 subsidiary (out of 24)
- Impact: Missing data for 23 dental practices
- Silvercreek needs 15 locations - we're only getting 1
- Journal entries, vendor bills have NO subsidiary tracking

**Secondary Issue:** Frontend showing mock/placeholder data
- Financial Analytics dashboard has placeholders
- No display of real NetSuite financial metrics
- AI insights not visible to users

---

## Solution Overview

**Part 1: Multi-Subsidiary NetSuite Sync**
- Loop through all 24 subsidiaries
- Fetch data for each subsidiary separately
- Tag records with subsidiary_id
- Aggregate in Snowflake by practice/subsidiary

**Part 2: Frontend Real Data Display**
- Remove ALL mock data (except ADP)
- Display real NetSuite financial metrics
- Match operations report format (revenue, expenses, margins, etc.)
- Add AI insights widget (GPT-4 summaries)
- Practice comparison table

---

## Architecture

### Multi-Subsidiary Data Flow

```
NetSuite API
  ↓
1. Fetch subsidiaries (24 practices)
  ↓
2. Loop: For each subsidiary
   └─ For each record type (journalEntry, vendorBill, etc.)
      └─ Fetch with filter: {"subsidiary": subsidiary_id}
         └─ MERGE to Snowflake Bronze (includes subsidiary_id)
  ↓
Snowflake Dynamic Tables
  ↓ GROUP BY subsidiary/practice
Gold Layer: monthly_production_kpis (per practice)
  ↓
MCP API: /api/v1/analytics/financial/summary
  ↓
Frontend: FinancialAnalyticsPage.tsx
  └─ Display by practice with MoM comparisons
```

### Frontend Data Architecture

```
┌─────────────────────────────────────────┐
│ Executive Dashboard                     │
│ ├─ AI Insights Widget (GPT-4)          │
│ ├─ Financial Summary Cards             │
│ └─ Practice Comparison Table            │
├─────────────────────────────────────────┤
│ Financial Analytics Page                │
│ ├─ Revenue by Practice (real data)     │
│ ├─ Expense Breakdown (real data)       │
│ ├─ Profit Margins Chart (real data)    │
│ └─ MoM Growth Trends (real data)       │
├─────────────────────────────────────────┤
│ Data Sources: All Real                 │
│ ├─ gold.monthly_production_kpis        │
│ ├─ gold.production_anomalies           │
│ └─ gold.kpi_alerts                      │
└─────────────────────────────────────────┘
```

---

## Task Breakdown

### Task 1: Fix Multi-Subsidiary NetSuite Sync

**Files:**
- Modify: `mcp-server/src/services/netsuite_sync_orchestrator.py`
- Modify: `mcp-server/src/connectors/netsuite.py` (add subsidiary support)
- Modify: `mcp-server/src/services/snowflake_netsuite_loader.py` (ensure subsidiary_id tracked)

**Changes:**

1. **Fetch subsidiaries first:**
```python
async def get_all_subsidiaries(self) -> List[Dict]:
    """Get list of all subsidiaries"""
    response = await self.netsuite.fetch_data("subsidiary", {"limit": 100})
    return response.data if response.success else []
```

2. **Loop through subsidiaries:**
```python
async def sync_all_record_types(self, full_sync: bool = False):
    # Get all subsidiaries
    subsidiaries = await self.get_all_subsidiaries()

    for record_type in RECORD_TYPES:
        for subsidiary in subsidiaries:
            # Fetch with subsidiary filter
            filters = {"subsidiary": subsidiary['id']}
            await self.sync_record_type_for_subsidiary(
                record_type,
                subsidiary['id'],
                full_sync
            )
```

3. **Track subsidiary in records:**
```python
bronze_records.append({
    "ID": record.get("id"),
    "SUBSIDIARY_ID": subsidiary_id,  # NEW
    "RAW_DATA": json.dumps(record),
    ...
})
```

**Expected Result:** 395 journal entries → 9,480 entries (24x coverage)

---

### Task 2: Update Snowflake Dynamic Tables for Subsidiary

**Files:**
- Modify: `snowflake-mvp-ai-setup.sql`

**Changes:**

Update `stg_financials` to extract subsidiary:
```sql
CREATE OR REPLACE DYNAMIC TABLE silver.stg_financials
AS
SELECT
    id,
    raw_data:subsidiary.id::string as subsidiary_id,
    raw_data:subsidiary.name::string as practice_name,  -- Use subsidiary name as practice
    raw_data:tranDate::date as transaction_date,
    raw_data:debit::number - raw_data:credit::number as amount,
    ...
FROM bronze.netsuite_journal_entries
```

Update `monthly_production_kpis` to group by subsidiary:
```sql
GROUP BY practice_name, month_date  -- practice_name now from subsidiary
```

**Expected Result:** KPIs calculated per practice (all 24)

---

### Task 3: Create Financial Summary API Endpoint

**Files:**
- Create: `mcp-server/src/api/financial.py` (new router)
- Modify: `mcp-server/src/main.py` (register router)

**New Endpoint:**
```python
@router.get("/api/v1/analytics/financial/summary")
async def get_financial_summary(
    practice_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get financial summary by practice

    Returns operations report metrics:
    - Total Revenue
    - Total Expenses
    - Net Income
    - Gross Margin %
    - Payroll Expense
    - Cash Balance
    - AR, AP balances
    - MoM growth %
    """

    query = """
        SELECT
            practice_name,
            month_date,
            total_production as revenue,
            total_expenses,
            net_income,
            profit_margin_pct as gross_margin,
            mom_growth_pct,
            -- TODO: Add payroll, cash, AR, AP from other tables
        FROM gold.monthly_production_kpis
        WHERE 1=1
    """

    if practice_name:
        query += f" AND practice_name = '{practice_name}'"

    if start_date:
        query += f" AND month_date >= '{start_date}'"

    if end_date:
        query += f" AND month_date <= '{end_date}'"

    query += " ORDER BY month_date DESC, practice_name"

    return await snowflake.execute_query(query)
```

---

### Task 4: Remove Mock Data

**Files to Clean:**

**MCP Server:**
- `mcp-server/src/services/forecasting.py`:
  - Delete `_generate_mock_forecast()`
  - Delete `_generate_mock_anomalies()`
  - Delete `_generate_mock_insight()`
  - Update methods to return empty list if no Snowflake data

**Frontend:**
- `frontend/src/pages/analytics/FinancialAnalyticsPage.tsx`:
  - Remove placeholder text
  - Remove mock chart data
- `frontend/src/components/analytics/*`:
  - Check for hardcoded sample data
  - Remove demo datasets

**Search Pattern:**
```bash
grep -r "mock" frontend/src/
grep -r "sample.*data" frontend/src/
grep -r "placeholder" frontend/src/
grep -r "TODO.*demo" frontend/src/
```

---

### Task 5: Build Financial Analytics Dashboard

**File:** `frontend/src/pages/analytics/FinancialAnalyticsPage.tsx`

**Components to Build:**

1. **KPI Cards (Top Row)**
```typescript
<div className="grid grid-cols-5 gap-4">
  <KPICard
    title="Total Revenue"
    value={formatCurrency(data.total_revenue)}
    change={data.mom_revenue_growth}
    trend={data.mom_revenue_growth > 0 ? 'up' : 'down'}
  />
  <KPICard title="Total Expenses" value={...} />
  <KPICard title="Net Income" value={...} />
  <KPICard title="Gross Margin" value={...} />
  <KPICard title="EBITDA" value={...} />
</div>
```

2. **Practice Comparison Table**
```typescript
<DataTable
  columns={['Practice', 'Revenue', 'Expenses', 'Net Income', 'Margin %', 'MoM Growth']}
  data={practiceData}  // From API
  sortable
  exportable
/>
```

3. **MoM Trend Chart**
```typescript
<LineChart
  data={monthlyTrends}  // From API
  xAxis="month"
  yAxis="revenue"
  groupBy="practice_name"
/>
```

**API Integration:**
```typescript
// Hook: frontend/src/hooks/useFinancialAnalytics.ts
export function useFinancialSummary(params) {
  return useQuery({
    queryKey: ['financial-summary', params],
    queryFn: () => api.get('/api/v1/analytics/financial/summary', { params }),
    staleTime: 5 * 60 * 1000  // 5 minutes
  })
}
```

---

### Task 6: Add AI Insights Widget to Dashboard

**File:** `frontend/src/components/dashboard/AIInsightsWidget.tsx` (new)

**Component:**
```typescript
export function AIInsightsWidget() {
  const { data: insights } = useQuery({
    queryKey: ['ai-insights'],
    queryFn: () => mcpAPI.get('/api/v1/analytics/insights'),
    staleTime: 60 * 60 * 1000  // 1 hour (matches backend cache)
  })

  return (
    <Card className="ai-insights">
      <CardHeader>
        <Brain className="icon" />
        <h3>AI Insights</h3>
      </CardHeader>
      <CardContent>
        <p className="insight-text">{insights?.insight}</p>
        <span className="meta">Generated by GPT-4 • Updated hourly</span>
      </CardContent>
    </Card>
  )
}
```

**Add to:** Executive Dashboard and Financial Analytics pages

---

## Success Criteria

**Multi-Subsidiary Sync:**
- ✅ All 24 subsidiaries synced
- ✅ Journal entries tagged with subsidiary
- ✅ Each practice appears in monthly_production_kpis
- ✅ No data from single practice only

**Frontend Real Data:**
- ✅ No mock data visible (except ADP placeholder)
- ✅ Financial metrics from real NetSuite data
- ✅ Practice comparison showing all locations
- ✅ MoM growth calculated from actual data
- ✅ AI insights displayed on dashboard
- ✅ Anomaly alerts visible

**Data Quality:**
- ✅ Revenue matches operations report format
- ✅ All 24 practices represented
- ✅ MoM calculations accurate
- ✅ No duplicates (MERGE working)

---

## Estimated Timeline

- Task 1: Multi-subsidiary sync (1-2 days)
- Task 2: Update Snowflake models (0.5 day)
- Task 3: Financial API endpoint (0.5 day)
- Task 4: Remove mocks (1 day)
- Task 5: Build financial dashboard (1-2 days)
- Task 6: AI insights widget (0.5 day)

**Total: 4.5-6.5 days**

---

**Design validated:** 2025-11-08
**Ready for implementation:** Yes
