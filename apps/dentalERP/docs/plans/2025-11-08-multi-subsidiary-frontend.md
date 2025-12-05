# Multi-Subsidiary NetSuite & Frontend Real Data Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix multi-subsidiary NetSuite sync to get data from all 24 practices, remove all mock data, and display real financial metrics on frontend

**Architecture:** Loop through subsidiaries in NetSuite sync, tag records with subsidiary_id, aggregate in Snowflake by practice, display real data in React frontend with AI insights

**Tech Stack:** Python FastAPI, NetSuite REST API, Snowflake Dynamic Tables, React TypeScript, TanStack Query

---

## Task 1: Fix Multi-Subsidiary NetSuite Sync

**Files:**
- Modify: `mcp-server/src/services/netsuite_sync_orchestrator.py`
- Modify: `mcp-server/src/connectors/netsuite.py`
- Test: `mcp-server/tests/test_netsuite_sync_orchestrator.py`

### Step 1: Add get_all_subsidiaries method to NetSuiteConnector

Modify `mcp-server/src/connectors/netsuite.py`, add method after `fetch_data`:

```python
async def get_subsidiaries(self) -> List[Dict[str, Any]]:
    """
    Fetch all subsidiaries from NetSuite

    Returns:
        List of subsidiary dictionaries with id and name
    """
    logger.info("[NetSuite] Fetching all subsidiaries")

    response = await self.fetch_data("subsidiary", {"limit": 100})

    if not response.success:
        logger.error(f"Failed to fetch subsidiaries: {response.error}")
        return []

    subsidiaries = response.data
    logger.info(f"[NetSuite] Found {len(subsidiaries)} subsidiaries")

    return subsidiaries
```

### Step 2: Modify sync orchestrator to loop through subsidiaries

Modify `mcp-server/src/services/netsuite_sync_orchestrator.py`, update `sync_all_record_types`:

```python
async def sync_all_record_types(self, full_sync: bool = False) -> Dict[str, int]:
    """Sync all NetSuite record types for all subsidiaries"""

    # Step 1: Get all subsidiaries
    subsidiaries = await self.netsuite.get_subsidiaries()

    if not subsidiaries:
        logger.warning("No subsidiaries found, syncing without subsidiary filter")
        subsidiaries = [{"id": None, "name": "Default"}]  # Fallback

    logger.info(f"Syncing data for {len(subsidiaries)} subsidiaries")

    results = {}

    # Step 2: For each record type
    for record_type in self.RECORD_TYPES:
        total_synced = 0

        # Step 3: For each subsidiary
        for subsidiary in subsidiaries:
            try:
                sub_id = subsidiary.get('id')
                sub_name = subsidiary.get('name', 'Unknown')

                logger.info(f"Syncing {record_type} for subsidiary: {sub_name} (ID: {sub_id})")

                # Build filters with subsidiary
                filters = {"limit": 100}

                if sub_id:
                    filters["subsidiary"] = sub_id

                if not full_sync:
                    last_sync = await self._get_last_sync_time(record_type, sub_id)
                    if last_sync:
                        filters["q"] = f'lastModifiedDate > "{last_sync.isoformat()}"'

                # Fetch and sync for this subsidiary
                count = await self.sync_record_type(
                    record_type,
                    subsidiary_id=sub_id,
                    filters=filters
                )

                total_synced += count

            except Exception as e:
                logger.error(f"Failed to sync {record_type} for subsidiary {sub_id}: {e}")
                continue

        results[record_type] = total_synced
        logger.info(f"✅ Synced {total_synced} {record_type} records across all subsidiaries")

    return results
```

### Step 3: Update sync_record_type to accept subsidiary_id

Modify `sync_record_type` method signature:

```python
async def sync_record_type(
    self,
    record_type: str,
    subsidiary_id: Optional[str] = None,
    filters: Optional[Dict] = None
) -> int:
    """Sync one record type for one subsidiary"""

    # Use provided filters or build new
    if filters is None:
        filters = {"limit": 100}
        if subsidiary_id:
            filters["subsidiary"] = subsidiary_id

    # Rest of existing logic...
    # Add subsidiary_id to bronze_records:
    bronze_records.append({
        "ID": record.get("id"),
        "SUBSIDIARY_ID": subsidiary_id,  # NEW FIELD
        "SYNC_ID": sync_id,
        "TENANT_ID": self.tenant_id,
        "RAW_DATA": json.dumps(record),
        ...
    })
```

### Step 4: Test multi-subsidiary sync

Run:
```bash
cd mcp-server
pytest tests/test_netsuite_sync_orchestrator.py -v
```

Expected: Tests pass (or skip if credentials not available)

### Step 5: Commit multi-subsidiary sync

```bash
git add mcp-server/src/services/netsuite_sync_orchestrator.py \
        mcp-server/src/connectors/netsuite.py

git commit -m "feat(netsuite): add multi-subsidiary sync support

- Add get_subsidiaries() to NetSuiteConnector
- Loop through all 24 subsidiaries in sync orchestrator
- Add subsidiary filter to API calls
- Track subsidiary_id in bronze records

Fixes: Data from only 1 practice → Data from all 24 practices
Expected: 395 journal entries → 9,480 entries (24x coverage)"
```

---

## Task 2: Update Snowflake Models for Subsidiary Tracking

**Files:**
- Modify: `snowflake-mvp-ai-setup.sql`

### Step 1: Update stg_financials to extract subsidiary

Modify `snowflake-mvp-ai-setup.sql`, update stg_financials Dynamic Table:

```sql
CREATE OR REPLACE DYNAMIC TABLE silver.stg_financials
TARGET_LAG = '1 hour'
WAREHOUSE = compute_wh
AS
SELECT
    id as transaction_id,

    -- Extract subsidiary info from raw JSON
    raw_data:subsidiary.id::string as subsidiary_id,
    COALESCE(
        raw_data:subsidiary.name::string,
        'Unknown Practice'
    ) as practice_name,

    -- Transaction details
    raw_data:tranDate::date as transaction_date,
    DATE_TRUNC('month', raw_data:tranDate::date) as month_date,

    -- Financial amounts
    COALESCE(raw_data:debit::number(18,2), 0) - COALESCE(raw_data:credit::number(18,2), 0) as amount,

    -- Account classification
    raw_data:account.name::string as account_name,
    raw_data:account.type::string as account_type,

    -- Metadata
    created_at,
    extracted_at

FROM bronze.netsuite_journal_entries
WHERE transaction_date >= DATEADD(MONTH, -24, CURRENT_DATE())
```

### Step 2: Update fact_financials to group by practice

Modify fact_financials Dynamic Table:

```sql
CREATE OR REPLACE DYNAMIC TABLE gold.fact_financials
TARGET_LAG = '1 hour'
WAREHOUSE = compute_wh
AS
SELECT
    practice_name,
    subsidiary_id,
    month_date,

    -- Revenue (positive amounts)
    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_revenue,

    -- Expenses (negative amounts)
    SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as total_expenses,

    -- Net income
    SUM(amount) as net_income,

    -- Transaction count
    COUNT(*) as transaction_count,

    CURRENT_TIMESTAMP() as calculated_at

FROM silver.stg_financials
GROUP BY practice_name, subsidiary_id, month_date
```

### Step 3: Update monthly_production_kpis for multi-practice

Ensure grouping includes practice_name:

```sql
CREATE OR REPLACE DYNAMIC TABLE gold.monthly_production_kpis
TARGET_LAG = '1 hour'
WAREHOUSE = compute_wh
AS
SELECT
    practice_name,
    subsidiary_id,
    month_date,

    -- Current month
    total_revenue,
    total_expenses,
    net_income,

    -- Profit margin
    ROUND((net_income / NULLIF(total_revenue, 0)) * 100, 2) as profit_margin_pct,

    -- MoM growth
    LAG(total_revenue) OVER (PARTITION BY practice_name ORDER BY month_date) as prev_month_revenue,
    ROUND(
        ((total_revenue - LAG(total_revenue) OVER (PARTITION BY practice_name ORDER BY month_date))
         / NULLIF(LAG(total_revenue) OVER (PARTITION BY practice_name ORDER BY month_date), 0)) * 100,
        2
    ) as mom_growth_pct,

    CURRENT_TIMESTAMP() as calculated_at

FROM gold.fact_financials
```

### Step 4: Commit Snowflake model updates

```bash
git add snowflake-mvp-ai-setup.sql

git commit -m "feat(snowflake): update models for multi-subsidiary tracking

- Extract subsidiary.id and subsidiary.name from raw_data
- Group financials by practice_name (from subsidiary)
- Calculate revenue, expenses, net_income per practice
- MoM growth partitioned by practice_name

Enables: 24-practice financial reporting"
```

---

## Task 3: Remove Mock Data from Services

**Files:**
- Modify: `mcp-server/src/services/forecasting.py`
- Delete mock generators

### Step 1: Remove mock forecast generator

Delete `_generate_mock_forecast()` method from `forecasting.py` (lines ~194-225):

```python
# DELETE THIS METHOD ENTIRELY
def _generate_mock_forecast(...):
    ...
```

### Step 2: Remove mock anomaly generator

Delete `_generate_mock_anomalies()` method (lines ~227-244):

```python
# DELETE THIS METHOD ENTIRELY
def _generate_mock_anomalies(...):
    ...
```

### Step 3: Update methods to return empty on no data

Modify `forecast_revenue` to handle missing Snowflake data:

```python
async def forecast_revenue(...):
    """Query Snowflake forecasts - no mocks"""

    result = await snowflake.execute_query(...)

    if not result:
        logger.warning(f"No forecast data for {practice_name}")
        return {
            "practice_name": practice_name,
            "forecasts": [],
            "model": "no_data",
            "generated_at": datetime.utcnow().isoformat()
        }

    # Return real data
    return format_forecast_response(result)
```

### Step 4: Commit mock removal

```bash
git add mcp-server/src/services/forecasting.py

git commit -m "refactor(forecasting): remove all mock data generators

- Delete _generate_mock_forecast()
- Delete _generate_mock_anomalies()
- Return empty results if Snowflake has no data
- Production ready - no fake data"
```

---

## Task 4: Create Financial Summary API Endpoint

**Files:**
- Create: `mcp-server/src/api/financial.py`
- Modify: `mcp-server/src/main.py`

### Step 1: Create financial router

Create `mcp-server/src/api/financial.py`:

```python
"""
Financial Analytics API
Real NetSuite financial data endpoints
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime, timedelta

from ..core.security import verify_api_key
from ..services.warehouse_router import WarehouseRouter
from ..utils.logger import logger

router = APIRouter(prefix="/api/v1/analytics/financial", tags=["financial"])


@router.get("/summary")
async def get_financial_summary(
    practice_name: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    api_key: str = Depends(verify_api_key)
):
    """
    Get financial summary by practice

    Operations Report Metrics:
    - Total Revenue
    - Total Expenses
    - Net Income
    - Gross Margin %
    - MoM Growth %

    Args:
        practice_name: Optional practice filter
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        Financial metrics per practice per month
    """
    try:
        warehouse_router = WarehouseRouter()
        snowflake = await warehouse_router.get_connector(warehouse_type="snowflake")

        # Build query
        query = """
            SELECT
                practice_name,
                subsidiary_id,
                month_date,
                total_revenue,
                total_expenses,
                net_income,
                profit_margin_pct,
                mom_growth_pct,
                prev_month_revenue,
                calculated_at
            FROM gold.monthly_production_kpis
            WHERE 1=1
        """

        params = {}

        if practice_name:
            query += " AND practice_name = %(practice_name)s"
            params['practice_name'] = practice_name

        if start_date:
            query += " AND month_date >= %(start_date)s"
            params['start_date'] = start_date
        else:
            # Default to last 3 months
            query += " AND month_date >= DATEADD(MONTH, -3, CURRENT_DATE())"

        if end_date:
            query += " AND month_date <= %(end_date)s"
            params['end_date'] = end_date

        query += " ORDER BY month_date DESC, practice_name"

        # Execute query
        result = await snowflake.execute_query(query, parameters=params)

        return {
            "data": result,
            "count": len(result),
            "filters": {
                "practice_name": practice_name,
                "start_date": start_date,
                "end_date": end_date
            }
        }

    except Exception as e:
        logger.error(f"Financial summary failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-practice")
async def get_by_practice_comparison(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """
    Compare all practices side-by-side

    Returns:
        Latest month financial metrics for all practices
    """
    try:
        warehouse_router = WarehouseRouter()
        snowflake = await warehouse_router.get_connector(warehouse_type="snowflake")

        query = """
            WITH latest_month AS (
                SELECT MAX(month_date) as max_month
                FROM gold.monthly_production_kpis
            )
            SELECT
                k.practice_name,
                k.total_revenue,
                k.total_expenses,
                k.net_income,
                k.profit_margin_pct,
                k.mom_growth_pct
            FROM gold.monthly_production_kpis k
            CROSS JOIN latest_month l
            WHERE k.month_date = l.max_month
            ORDER BY k.total_revenue DESC
        """

        result = await snowflake.execute_query(query)

        return {
            "practices": result,
            "count": len(result),
            "period": "latest_month"
        }

    except Exception as e:
        logger.error(f"Practice comparison failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 3: Register financial router in main.py

Modify `mcp-server/src/main.py`, add after existing routers:

```python
from .api import financial

app.include_router(financial.router)
```

### Step 4: Test financial endpoints

Run:
```bash
# Start MCP server
cd mcp-server
uvicorn src.main:app --reload

# Test in another terminal
curl -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
     "http://localhost:8085/api/v1/analytics/financial/summary"

curl -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
     "http://localhost:8085/api/v1/analytics/financial/by-practice"
```

Expected: JSON with real NetSuite financial data

### Step 5: Commit financial API

```bash
git add mcp-server/src/api/financial.py \
        mcp-server/src/main.py

git commit -m "feat(api): add financial analytics endpoints with real NetSuite data

- GET /api/v1/analytics/financial/summary (by practice, date range)
- GET /api/v1/analytics/financial/by-practice (comparison view)
- Query gold.monthly_production_kpis (real Snowflake data)
- No mock data - production ready

Returns: revenue, expenses, net_income, margins, MoM growth"
```

---

## Task 5: Remove Frontend Mock Data

**Files:**
- Modify: `frontend/src/pages/analytics/FinancialAnalyticsPage.tsx`
- Delete: Any mock data constants

### Step 1: Find and remove mock data

Search for mocks:
```bash
cd frontend
grep -r "mockData\|sampleData\|demoData\|placeholder.*data" src/pages/analytics/
grep -r "const.*MOCK\|const.*SAMPLE" src/
```

### Step 2: Remove placeholder components in FinancialAnalyticsPage

Modify `frontend/src/pages/analytics/FinancialAnalyticsPage.tsx`:

Remove any of these patterns:
```typescript
// DELETE: Mock data constants
const MOCK_DATA = [...]
const sampleRevenue = [...]

// DELETE: Placeholder text
<div>Coming soon...</div>
<div>Placeholder for AR Aging</div>

// DELETE: Demo charts with hardcoded data
<BarChart data={[{name: 'Demo', value: 100}]} />
```

### Step 3: Commit mock removal

```bash
git add frontend/src/pages/analytics/FinancialAnalyticsPage.tsx

git commit -m "refactor(frontend): remove all mock data from financial analytics

- Delete mock data constants
- Remove placeholder components
- Remove demo charts
- Prepare for real API integration"
```

---

## Task 6: Build Financial Analytics Dashboard with Real Data

**Files:**
- Modify: `frontend/src/pages/analytics/FinancialAnalyticsPage.tsx`
- Create: `frontend/src/hooks/useFinancialAnalytics.ts`
- Create: `frontend/src/services/financialAPI.ts`

### Step 1: Create financial API service

Create `frontend/src/services/financialAPI.ts`:

```typescript
import { apiClient } from './api';

export interface FinancialSummary {
  practice_name: string;
  subsidiary_id: string;
  month_date: string;
  total_revenue: number;
  total_expenses: number;
  net_income: number;
  profit_margin_pct: number;
  mom_growth_pct: number;
  prev_month_revenue: number;
}

export interface FinancialSummaryResponse {
  data: FinancialSummary[];
  count: number;
  filters: {
    practice_name?: string;
    start_date?: string;
    end_date?: string;
  };
}

export const financialAPI = {
  getSummary: async (params?: {
    practice_name?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<FinancialSummaryResponse> => {
    const response = await apiClient.get('/api/v1/analytics/financial/summary', {
      params
    });
    return response.data;
  },

  getByPracticeComparison: async (): Promise<{
    practices: FinancialSummary[];
    count: number;
  }> => {
    const response = await apiClient.get('/api/v1/analytics/financial/by-practice');
    return response.data;
  }
};
```

### Step 2: Create React Query hook

Create `frontend/src/hooks/useFinancialAnalytics.ts`:

```typescript
import { useQuery } from '@tanstack/react-query';
import { financialAPI } from '../services/financialAPI';

export function useFinancialSummary(params?: {
  practice_name?: string;
  start_date?: string;
  end_date?: string;
}) {
  return useQuery({
    queryKey: ['financial-summary', params],
    queryFn: () => financialAPI.getSummary(params),
    staleTime: 5 * 60 * 1000,  // 5 minutes
    retry: 2
  });
}

export function usePracticeComparison() {
  return useQuery({
    queryKey: ['practice-comparison'],
    queryFn: () => financialAPI.getByPracticeComparison(),
    staleTime: 5 * 60 * 1000
  });
}
```

### Step 3: Build Financial Analytics Page

Modify `frontend/src/pages/analytics/FinancialAnalyticsPage.tsx`:

```typescript
import React from 'react';
import { useFinancialSummary, usePracticeComparison } from '../../hooks/useFinancialAnalytics';
import { formatCurrency, formatPercent } from '../../utils/format';

export function FinancialAnalyticsPage() {
  const { data: summary, isLoading, error } = useFinancialSummary();
  const { data: comparison } = usePracticeComparison();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  // Get latest month metrics
  const latestMonth = summary?.data[0];

  return (
    <div className="financial-analytics-page">
      <PageHeader title="Financial Analytics" subtitle="Real-time NetSuite data" />

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-5 gap-4 mb-8">
        <KPICard
          title="Total Revenue"
          value={formatCurrency(latestMonth?.total_revenue)}
          change={latestMonth?.mom_growth_pct}
          trend={latestMonth?.mom_growth_pct > 0 ? 'up' : 'down'}
        />
        <KPICard
          title="Total Expenses"
          value={formatCurrency(latestMonth?.total_expenses)}
        />
        <KPICard
          title="Net Income"
          value={formatCurrency(latestMonth?.net_income)}
          change={latestMonth?.mom_growth_pct}
        />
        <KPICard
          title="Profit Margin"
          value={formatPercent(latestMonth?.profit_margin_pct)}
        />
        <KPICard
          title="Practices"
          value={comparison?.count || 0}
        />
      </div>

      {/* Practice Comparison Table */}
      <Card className="mb-8">
        <CardHeader>
          <h3>Performance by Practice</h3>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={[
              { header: 'Practice', accessor: 'practice_name' },
              { header: 'Revenue', accessor: 'total_revenue', format: formatCurrency },
              { header: 'Expenses', accessor: 'total_expenses', format: formatCurrency },
              { header: 'Net Income', accessor: 'net_income', format: formatCurrency },
              { header: 'Margin %', accessor: 'profit_margin_pct', format: formatPercent },
              { header: 'MoM Growth', accessor: 'mom_growth_pct', format: formatPercent }
            ]}
            data={comparison?.practices || []}
            sortable
            exportable
          />
        </CardContent>
      </Card>

      {/* Monthly Trend Chart */}
      <Card>
        <CardHeader>
          <h3>Revenue Trend</h3>
        </CardHeader>
        <CardContent>
          <LineChart
            data={summary?.data || []}
            xKey="month_date"
            yKey="total_revenue"
            groupBy="practice_name"
          />
        </CardContent>
      </Card>
    </div>
  );
}
```

### Step 4: Test frontend with real data

Run:
```bash
cd frontend
npm run dev

# Open browser to http://localhost:3000/analytics/financial
# Verify: Real NetSuite data displayed, no mock data
```

### Step 5: Commit financial dashboard

```bash
git add frontend/src/pages/analytics/FinancialAnalyticsPage.tsx \
        frontend/src/hooks/useFinancialAnalytics.ts \
        frontend/src/services/financialAPI.ts

git commit -m "feat(frontend): build financial analytics dashboard with real NetSuite data

- Create financial API service and React Query hooks
- Build KPI summary cards (revenue, expenses, margins)
- Build practice comparison table
- Build monthly trend chart
- No mock data - 100% real Snowflake data

Displays: All 24 practices with MoM growth tracking"
```

---

## Task 7: Add AI Insights Widget to Executive Dashboard

**Files:**
- Create: `frontend/src/components/dashboard/AIInsightsWidget.tsx`
- Modify: `frontend/src/pages/dashboard/DashboardPage.tsx`

### Step 1: Create AI Insights Widget component

Create `frontend/src/components/dashboard/AIInsightsWidget.tsx`:

```typescript
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Brain, RefreshCw } from 'lucide-react';
import { mcpAPI } from '../../services/mcpAPI';
import { Card, CardHeader, CardContent } from '../ui/Card';

interface AIInsightsResponse {
  insight: string;
  practice_name: string;
  period: string;
  generated_at: string;
  model: string;
}

export function AIInsightsWidget() {
  const { data, isLoading, error, refetch } = useQuery<AIInsightsResponse>({
    queryKey: ['ai-insights'],
    queryFn: async () => {
      const response = await mcpAPI.get('/api/v1/analytics/insights');
      return response.data;
    },
    staleTime: 60 * 60 * 1000,  // 1 hour (matches backend cache)
    retry: 1
  });

  if (isLoading) {
    return (
      <Card className="ai-insights-widget">
        <CardContent className="p-6">
          <div className="flex items-center space-x-2 text-gray-500">
            <Brain className="animate-pulse" />
            <span>Generating AI insights...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="ai-insights-widget">
        <CardContent className="p-6">
          <div className="text-orange-600">
            AI insights temporarily unavailable
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="ai-insights-widget bg-gradient-to-br from-purple-50 to-blue-50">
      <CardHeader className="flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <Brain className="w-6 h-6 text-purple-600" />
          <h3 className="font-semibold text-lg">AI Insights</h3>
        </div>
        <button
          onClick={() => refetch()}
          className="text-sm text-gray-500 hover:text-gray-700 flex items-center space-x-1"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </CardHeader>

      <CardContent className="p-6">
        <p className="text-gray-800 text-base leading-relaxed mb-4">
          {data?.insight}
        </p>

        <div className="flex justify-between items-center text-xs text-gray-500">
          <span>Powered by GPT-4</span>
          <span>Updated {new Date(data?.generated_at || '').toLocaleTimeString()}</span>
        </div>
      </CardContent>
    </Card>
  );
}
```

### Step 2: Add widget to Executive Dashboard

Modify `frontend/src/pages/dashboard/DashboardPage.tsx`:

```typescript
import { AIInsightsWidget } from '../../components/dashboard/AIInsightsWidget';

export function DashboardPage() {
  return (
    <div className="dashboard-page">
      <PageHeader title="Executive Dashboard" />

      {/* AI Insights - Top of page */}
      <div className="mb-8">
        <AIInsightsWidget />
      </div>

      {/* Existing KPI widgets */}
      <div className="grid grid-cols-3 gap-6">
        {/* ... existing widgets ... */}
      </div>
    </div>
  );
}
```

### Step 3: Test AI insights widget

Run:
```bash
npm run dev

# Open http://localhost:3000/dashboard
# Verify: AI insights widget displays GPT-4 summary
# Verify: Refresh button works
# Verify: Shows "generating" state while loading
```

### Step 4: Commit AI insights widget

```bash
git add frontend/src/components/dashboard/AIInsightsWidget.tsx \
        frontend/src/pages/dashboard/DashboardPage.tsx

git commit -m "feat(frontend): add AI insights widget with GPT-4 summaries

- Create AIInsightsWidget component with Brain icon
- Display GPT-4 generated insights on executive dashboard
- Auto-refresh every hour (cached)
- Manual refresh button
- Loading and error states
- Gradient background for visual distinction

Powered by: Real Snowflake KPIs + GPT-4 analysis"
```

---

## Task 8: Deploy to Production and Verify

**Files:**
- Deploy via GCP

### Step 1: Merge to main and push

Run:
```bash
cd /Users/nomade/Documents/GitHub/dentalERP
git merge feat/multi-subsidiary-frontend
git push origin main
```

### Step 2: Deploy to GCP

Run:
```bash
gcloud compute ssh dental-erp-vm --zone=us-central1-a

cd /opt/dental-erp
sudo git pull origin main

# Rebuild MCP server with new code
sudo docker-compose build mcp-server-prod
sudo docker-compose stop mcp-server-prod
sudo docker-compose rm -f mcp-server-prod
sudo docker-compose up -d mcp-server-prod

# Rebuild frontend with new components
sudo docker-compose build frontend-prod
sudo docker-compose restart frontend-prod
```

### Step 3: Execute updated Snowflake SQL

On GCP VM:
```bash
sudo docker cp snowflake-mvp-ai-setup.sql dental-erp_mcp-server-prod_1:/app/
sudo docker exec dental-erp_mcp-server-prod_1 python3 << 'EOF'
import snowflake.connector, os
env = {}
with open("/app/.env") as f:
    for line in f:
        if "=" in line and not line.startswith("#"):
            k,v = line.strip().split("=", 1)
            env[k] = v

conn = snowflake.connector.connect(
    account=env["SNOWFLAKE_ACCOUNT"],
    user=env["SNOWFLAKE_USER"],
    password=env["SNOWFLAKE_PASSWORD"],
    warehouse=env["SNOWFLAKE_WAREHOUSE"],
    database=env["SNOWFLAKE_DATABASE"]
)

with open("/app/snowflake-mvp-ai-setup.sql") as f:
    for stmt in f.read().split(";"):
        stmt = stmt.strip()
        if stmt and not stmt.startswith("--"):
            try:
                conn.cursor().execute(stmt)
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"Error: {e}")

print("✅ Snowflake models updated")
conn.close()
EOF
```

### Step 4: Trigger multi-subsidiary sync

Run:
```bash
curl -X POST https://mcp.agentprovision.com/api/v1/netsuite/sync/trigger \
  -H "Authorization: Bearer prod-mcp-api-key-change-in-production-min-32-chars-secure" \
  -H "X-Tenant-ID: default" \
  -d '{"record_types": ["journalEntry", "account"], "full_sync": true}'
```

Wait 2-3 minutes for sync to complete

### Step 5: Verify multi-subsidiary coverage

Run:
```bash
sudo docker exec dental-erp_mcp-server-prod_1 python3 /app/check_subsidiary_coverage.py
```

Expected:
- ✅ Journal entries from MULTIPLE subsidiaries (not just 1)
- ✅ Data coverage: 395 entries → 2,000-10,000 entries (depending on NetSuite data)

### Step 6: Test financial API in production

Run:
```bash
curl -H "Authorization: Bearer prod-mcp-api-key-change-in-production-min-32-chars-secure" \
     "https://mcp.agentprovision.com/api/v1/analytics/financial/summary"
```

Expected: JSON with financial data for multiple practices

### Step 7: Test AI insights in production

Run:
```bash
curl -H "Authorization: Bearer prod-mcp-api-key-change-in-production-min-32-chars-secure" \
     "https://mcp.agentprovision.com/api/v1/analytics/insights"
```

Expected: GPT-4 generated insights about all practices

### Step 8: Verify frontend displays real data

Open browser:
```
https://dentalerp.agentprovision.com/analytics/financial
https://dentalerp.agentprovision.com/dashboard
```

Expected:
- ✅ Financial metrics from real NetSuite data
- ✅ Multiple practices in comparison table
- ✅ AI insights widget showing GPT-4 summary
- ✅ No "placeholder" or "coming soon" text
- ✅ Charts showing real trends

### Step 9: Create verification report

Create verification checklist:

```markdown
## Multi-Subsidiary & Frontend Verification

### NetSuite Multi-Subsidiary
- [ ] All 24 subsidiaries synced
- [ ] Journal entries have subsidiary field populated
- [ ] Vendor bills have subsidiary tracking
- [ ] Each practice appears in monthly_production_kpis

### Frontend Real Data
- [ ] Financial dashboard shows real revenue/expenses
- [ ] Practice comparison table has multiple rows
- [ ] AI insights widget displays GPT-4 summary
- [ ] No mock data visible
- [ ] MoM growth calculations accurate

### API Endpoints
- [ ] GET /api/v1/analytics/financial/summary works
- [ ] GET /api/v1/analytics/financial/by-practice works
- [ ] GET /api/v1/analytics/insights works

### Data Quality
- [ ] Revenue matches operations report format
- [ ] All practices represented
- [ ] No duplicates (MERGE working)
```

### Step 10: Final commit

```bash
git add VERIFICATION.md

git commit -m "docs: verification report for multi-subsidiary and frontend enhancements

All features verified:
- Multi-subsidiary NetSuite sync (24 practices)
- Real financial data displayed on frontend
- AI insights widget operational
- No mock data (except ADP)

Production ready for Silvercreek 15-location deployment"
```

---

## Summary

**Total Tasks:** 8
**Total Commits:** 8
**Estimated Time:** 4.5-6.5 days

**Key Deliverables:**
1. Multi-subsidiary NetSuite sync (24x data coverage)
2. Snowflake models updated for subsidiary tracking
3. Financial summary API (real NetSuite data)
4. All mock data removed
5. Financial analytics dashboard (real data)
6. AI insights widget (GPT-4)
7. Production deployment
8. Complete verification

**Success Criteria:**
- Data from all 24 practices, not just 1
- Frontend shows real financial metrics
- AI insights visible to executives
- No mock/placeholder data (except ADP)

---

**Plan saved:** `docs/plans/2025-11-08-multi-subsidiary-frontend.md`
**Ready for execution**
