# Operations KPI Dashboard - LEAN Implementation (Reuse-First Approach)

**Date:** November 14, 2025
**Status:** Planning
**Priority:** High
**Estimated Time:** 2-3 weeks (vs 8 weeks in original plan)

---

## 🎯 Strategy: Maximum Reuse

This plan **reuses 80% of existing infrastructure** to deliver operations KPIs quickly:

✅ **Reuse:** Existing Snowflake connector
✅ **Reuse:** Existing analytics API pattern
✅ **Reuse:** Existing React Query hooks
✅ **Reuse:** Existing ProductionAnalyticsPage as template
✅ **Reuse:** Existing Bronze→Silver→Gold dbt pattern
✅ **Reuse:** Existing PDF/Excel upload infrastructure

🆕 **New:** Operations-specific SQL tables
🆕 **New:** Operations-specific API endpoints (copy/paste from analytics.py)
🆕 **New:** Operations dashboard page (copy/paste ProductionAnalyticsPage.tsx)

---

## 📊 What We're Building

### Operations Metrics Tracked
Based on `Operations Report(28).xlsx` analysis:

1. **Production & Collections** (we already have this!)
2. **Patient Visits** (NEW - by provider type)
3. **Production Per Visit** (calculation: production/visits)
4. **Case Acceptance** (NEW - treatment presented vs accepted)
5. **New Patients** (NEW - acquisition & conversion)
6. **Hygiene Recare** (NEW - capacity utilization)
7. **Labor Efficiency** (NEW - hygiene productivity ratio)
8. **Provider Performance** (NEW - individual provider tracking)

---

## 🗄️ Database Schema (SIMPLIFIED - Reuse Gold Pattern)

### Bronze → Silver → Gold with Dynamic Tables (AUTO-REFRESH!)

#### Bronze Layer: Raw Operations Data (Regular Table)

```sql
-- Raw operations metrics from Excel upload
CREATE TABLE bronze.operations_metrics_raw (
    id VARCHAR(50) PRIMARY KEY,
    practice_code VARCHAR(50) NOT NULL,
    practice_name VARCHAR(100),
    report_month DATE NOT NULL,
    tenant_id VARCHAR(50) NOT NULL,

    -- Raw metric values from Excel
    raw_data VARIANT,  -- Store all metrics as JSON

    -- Metadata
    source_file VARCHAR(200),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),

    CONSTRAINT unique_practice_month UNIQUE (practice_code, report_month, tenant_id)
);
```

#### Silver Layer: Cleaned Operations Metrics (DYNAMIC TABLE - AUTO-REFRESH!)

```sql
-- dbt model: models/silver/operations/stg_operations_metrics.sql
-- Snowflake creates this as a DYNAMIC TABLE with auto-refresh

{{
  config(
    materialized='dynamic_table',
    target_lag='1 hour',
    snowflake_warehouse='COMPUTE_WH'
  )
}}

SELECT
    practice_code,
    practice_name,
    report_month,
    tenant_id,

    -- Extract from raw_data VARIANT column
    raw_data:total_production::DECIMAL(18,2) AS total_production,
    raw_data:net_production::DECIMAL(18,2) AS net_production,
    raw_data:collections::DECIMAL(18,2) AS collections,
    raw_data:visits_total::INT AS visits_total,
    raw_data:visits_doctor::INT AS visits_doctor,
    raw_data:visits_hygiene::INT AS visits_hygiene,
    raw_data:new_patients::INT AS new_patients_count,
    raw_data:treatment_presented::DECIMAL(18,2) AS treatment_presented,
    raw_data:treatment_accepted::DECIMAL(18,2) AS treatment_accepted,
    raw_data:hygiene_capacity::INT AS hygiene_capacity_slots,
    raw_data:hygiene_production::DECIMAL(18,2) AS hygiene_net_production,
    raw_data:hygiene_compensation::DECIMAL(18,2) AS hygiene_compensation,

    uploaded_at,
    CURRENT_TIMESTAMP() AS transformed_at

FROM {{ source('bronze', 'operations_metrics_raw') }}
WHERE raw_data IS NOT NULL
```

#### Gold Layer: Operations KPIs (DYNAMIC TABLE - AUTO-REFRESH!)

```sql
-- dbt model: models/gold/operations/operations_kpis_monthly.sql
-- Snowflake auto-refreshes when silver layer changes!

{{
  config(
    materialized='dynamic_table',
    target_lag='1 hour',
    snowflake_warehouse='COMPUTE_WH'
  )
}}

WITH current_month AS (
    SELECT * FROM {{ ref('stg_operations_metrics') }}
),

ltm_aggregates AS (
    -- Last Twelve Months rolling calculations
    SELECT
        practice_code,
        report_month,
        SUM(total_production) OVER (
            PARTITION BY practice_code
            ORDER BY report_month
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) AS ltm_production,
        SUM(collections) OVER (
            PARTITION BY practice_code
            ORDER BY report_month
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) AS ltm_collections,
        SUM(visits_total) OVER (
            PARTITION BY practice_code
            ORDER BY report_month
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) AS ltm_visits
    FROM current_month
)

SELECT
    cm.practice_code AS practice_location,  -- Alias for compatibility
    cm.practice_name,
    cm.report_month,
    cm.tenant_id,

    -- Production & Collections
    cm.total_production,
    cm.net_production,
    cm.collections,
    CASE
        WHEN cm.net_production > 0
        THEN (cm.collections / cm.net_production * 100)
        ELSE 0
    END AS collection_rate_pct,

    -- Patient Visits
    cm.visits_doctor AS visits_doctor_total,
    cm.visits_hygiene AS visits_hygiene,
    cm.visits_total,

    -- Production Per Visit (CALCULATED)
    CASE
        WHEN cm.visits_doctor > 0
        THEN (cm.total_production / cm.visits_doctor)
        ELSE 0
    END AS production_per_visit_doctor,
    CASE
        WHEN cm.visits_hygiene > 0
        THEN (cm.hygiene_net_production / cm.visits_hygiene)
        ELSE 0
    END AS production_per_visit_hygiene,
    CASE
        WHEN cm.visits_total > 0
        THEN (cm.total_production / cm.visits_total)
        ELSE 0
    END AS production_per_visit_overall,

    -- Case Acceptance (CALCULATED)
    cm.treatment_presented,
    cm.treatment_accepted,
    CASE
        WHEN cm.treatment_presented > 0
        THEN (cm.treatment_accepted / cm.treatment_presented * 100)
        ELSE 0
    END AS case_acceptance_rate_pct,

    -- New Patients
    cm.new_patients_count,
    -- Note: reappointment rate needs additional data source

    -- Hygiene Efficiency (CALCULATED)
    cm.hygiene_capacity_slots,
    CASE
        WHEN cm.hygiene_capacity_slots > 0
        THEN (cm.visits_hygiene / cm.hygiene_capacity_slots * 100)
        ELSE 0
    END AS hygiene_capacity_utilization_pct,
    CASE
        WHEN cm.hygiene_compensation > 0
        THEN (cm.hygiene_net_production / cm.hygiene_compensation)
        ELSE 0
    END AS hygiene_productivity_ratio,

    -- Last Twelve Months (LTM) Rollups
    ltm.ltm_production,
    ltm.ltm_collections,
    ltm.ltm_visits,

    -- Metadata
    'excel_upload' AS extraction_method,
    1.0 AS data_quality_score,  -- Excel = perfect
    cm.uploaded_at,
    CURRENT_TIMESTAMP() AS calculated_at

FROM current_month cm
LEFT JOIN ltm_aggregates ltm
    ON cm.practice_code = ltm.practice_code
    AND cm.report_month = ltm.report_month
```

**Key Benefit:** Changes to Bronze automatically flow to Silver → Gold with 1-hour lag!

#### Gold Table: Operations KPIs (DYNAMIC TABLE)
    -- Use EXACT same pattern as daily_production_metrics
    practice_location VARCHAR(100) NOT NULL,
    report_month DATE NOT NULL,
    tenant_id VARCHAR(50) NOT NULL,

    -- Production & Collections (ALREADY HAVE THIS DATA!)
    total_production DECIMAL(18,2),
    net_production DECIMAL(18,2),
    collections DECIMAL(18,2),
    collection_rate_pct DECIMAL(5,2),

    -- Patient Visits (NEW)
    visits_doctor_total INT,
    visits_specialist INT,
    visits_hygiene INT,
    visits_total INT,

    -- Production Per Visit (CALCULATED)
    production_per_visit_doctor DECIMAL(10,2),
    production_per_visit_hygiene DECIMAL(10,2),
    production_per_visit_overall DECIMAL(10,2),

    -- Case Acceptance (NEW)
    treatment_presented DECIMAL(18,2),
    treatment_accepted DECIMAL(18,2),
    case_acceptance_rate_pct DECIMAL(5,2),

    -- New Patients (NEW)
    new_patients_count INT,
    new_patients_reappt_rate_pct DECIMAL(5,2),

    -- Hygiene Efficiency (NEW)
    hygiene_capacity_slots INT,
    hygiene_capacity_utilization_pct DECIMAL(5,2),
    hygiene_productivity_ratio DECIMAL(5,2),

    -- Last Twelve Months (LTM) Rollups
    ltm_production DECIMAL(18,2),
    ltm_collections DECIMAL(18,2),
    ltm_visits INT,

    -- Metadata (REUSE PATTERN)
    extraction_method VARCHAR(20),
    data_quality_score DECIMAL(3,2),
    uploaded_at TIMESTAMP,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),

    PRIMARY KEY (practice_location, report_month, tenant_id)
);

-- Index for fast queries (REUSE PATTERN)
CREATE INDEX idx_ops_kpis_practice_month ON gold.operations_kpis_monthly(practice_location, report_month);
CREATE INDEX idx_ops_kpis_tenant ON gold.operations_kpis_monthly(tenant_id);
```

**That's it!** One table, mirrors existing pattern.

---

## 🔄 Data Ingestion (REUSE Existing PDF Upload)

### Reuse: `mcp-server/src/api/pdf_ingestion.py`

**Current:** Uploads PMS day sheets
**Extend:** Support Operations Report Excel

```python
# File: mcp-server/src/services/operations_excel_parser.py
# NEW FILE - but follows pdf_ingestion.py pattern exactly

from typing import List, Dict
import pandas as pd
from datetime import datetime

class OperationsReportParser:
    """Parse SCDP Monthly Operations Report Excel - follows PDFIngestionService pattern"""

    def parse_excel(self, file_path: str, practice_code: str, report_month: str) -> Dict:
        """
        Parse Operations Report Excel

        Returns data in SAME format as PDF day sheets:
        {
            'practice_location': 'Eastlake',
            'report_date': '2024-11-01',
            'raw_data': { ... all metrics ... }
        }
        """
        df = pd.read_excel(file_path, sheet_name='Operating Metrics')

        # Extract metrics (simplified example)
        metrics = {
            'total_production': self._extract_value(df, 'Gross Production', 'Total'),
            'visits_total': self._extract_value(df, 'Total', 'Patient Visits'),
            'new_patients_count': self._extract_value(df, 'NEW PATIENTS', 'Total'),
            # ... extract all metrics ...
        }

        return {
            'practice_location': practice_code,
            'report_month': report_month,
            'raw_data': metrics,
            'extraction_method': 'excel_parser',
            'data_quality_score': 1.0  # Excel = perfect quality
        }

    def insert_to_bronze(self, data: Dict):
        """
        Insert to bronze.operations_metrics_raw
        Dynamic tables automatically propagate to Silver → Gold!
        """
        # REUSE: Existing Snowflake connector from warehouse_router
        warehouse = get_tenant_warehouse()

        # Store all metrics as JSON in raw_data column
        query = """
            INSERT INTO bronze.operations_metrics_raw
            (id, practice_code, practice_name, report_month, tenant_id, raw_data, source_file, uploaded_at)
            VALUES (?, ?, ?, ?, ?, PARSE_JSON(?), ?, CURRENT_TIMESTAMP())
        """

        params = (
            f"{data['practice_code']}_{data['report_month']}",
            data['practice_code'],
            data['practice_name'],
            data['report_month'],
            data['tenant_id'],
            json.dumps(data['raw_data']),  # Convert dict to JSON string
            data['source_file']
        )

        warehouse.execute(query, params)

        # Dynamic tables auto-refresh within 1 hour - no manual dbt run needed!
        # But can trigger immediate refresh if needed:
        # warehouse.execute("ALTER DYNAMIC TABLE silver.stg_operations_metrics REFRESH")
```

### Reuse API Endpoint Pattern

```python
# File: mcp-server/src/api/operations.py
# COPY mcp-server/src/api/pdf_ingestion.py and modify

from fastapi import APIRouter, File, UploadFile, Form
from ..services.operations_excel_parser import OperationsReportParser

router = APIRouter(prefix="/api/v1/operations", tags=["operations"])

@router.post("/upload")
async def upload_operations_report(
    file: UploadFile = File(...),
    practice_code: str = Form(...),
    report_month: str = Form(...),
    api_key: str = Depends(get_api_key_header)
):
    """
    Upload monthly operations report Excel

    REUSES: Exact same pattern as PDF upload
    """
    parser = OperationsReportParser()

    # Save temp file (REUSE from pdf_ingestion.py)
    temp_path = save_upload_file(file)

    try:
        # Parse Excel
        data = parser.parse_excel(temp_path, practice_code, report_month)

        # Insert to Snowflake
        parser.insert_to_snowflake(data)

        return {
            "status": "success",
            "practice": practice_code,
            "month": report_month,
            "metrics_loaded": len(data['raw_data'])
        }
    finally:
        os.unlink(temp_path)
```

---

## 📊 API Endpoints (REUSE analytics.py Pattern)

### Copy/Paste from analytics.py, Change Table Name

```python
# File: mcp-server/src/api/operations.py (continued)

@router.get("/kpis/monthly")
async def get_monthly_operations_kpis(
    practice_location: Optional[str] = Query(None),
    start_month: Optional[str] = Query(None),
    end_month: Optional[str] = Query(None),
    limit: int = Query(100),
    api_key: str = Depends(get_api_key_header)
):
    """
    Get monthly operations KPIs

    COPY from analytics.py /production/daily and change:
    - Table: gold.operations_kpis_monthly (instead of daily_production_metrics)
    - Date field: report_month (instead of report_date)
    - That's it!
    """
    warehouse = await get_tenant_warehouse()
    tenant = TenantContext.get_tenant()

    # Build WHERE clause (EXACT SAME PATTERN)
    where_clauses = [f"tenant_id = '{tenant.tenant_code}'"]
    if practice_location:
        where_clauses.append(f"practice_location = '{practice_location}'")
    if start_month:
        where_clauses.append(f"report_month >= '{start_month}'")
    if end_month:
        where_clauses.append(f"report_month <= '{end_month}'")

    where_sql = f"WHERE {' AND '.join(where_clauses)}"

    # Simple query (EXACT SAME PATTERN)
    query = f"""
        SELECT
            practice_location,
            report_month,
            total_production,
            net_production,
            collections,
            collection_rate_pct,
            visits_total,
            production_per_visit_overall,
            case_acceptance_rate_pct,
            new_patients_count,
            hygiene_capacity_utilization_pct,
            hygiene_productivity_ratio,
            ltm_production,
            ltm_collections
        FROM gold.operations_kpis_monthly
        {where_sql}
        ORDER BY report_month DESC, practice_location
        LIMIT {limit}
    """

    results = await warehouse.execute(query)
    return results


@router.get("/kpis/summary")
async def get_operations_summary(
    practice_location: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    api_key: str = Depends(get_api_key_header)
):
    """
    Get aggregated operations summary

    COPY from analytics.py /production/summary pattern
    """
    # Implementation - same pattern, different table
    pass
```

**That's ALL the backend code needed!**

---

## 🎨 Frontend Dashboard (REUSE ProductionAnalyticsPage.tsx)

### Step 1: Copy Existing Page

```bash
# Copy the production analytics page as template
cp frontend/src/pages/analytics/ProductionAnalyticsPage.tsx \
   frontend/src/pages/analytics/OperationsAnalyticsPage.tsx
```

### Step 2: Modify Hooks (REUSE useAnalytics.ts Pattern)

```typescript
// File: frontend/src/hooks/useOperations.ts
// COPY frontend/src/hooks/useAnalytics.ts and modify

import { useQuery } from '@tanstack/react-query';
import { mcpAPI } from '../services/mcpAPI';

export function useOperationsMonthly(params: {
  practice_location?: string;
  start_month?: string;
  end_month?: string;
  limit?: number;
}) {
  return useQuery({
    queryKey: ['operations', 'monthly', params],
    queryFn: () =>
      mcpAPI.get('/api/v1/operations/kpis/monthly', { params }),
    staleTime: 5 * 60 * 1000, // 5 minutes (REUSE same caching strategy)
  });
}

export function useOperationsSummary(params: {
  practice_location?: string;
  month?: string;
}) {
  return useQuery({
    queryKey: ['operations', 'summary', params],
    queryFn: () =>
      mcpAPI.get('/api/v1/operations/kpis/summary', { params }),
    staleTime: 5 * 60 * 1000,
  });
}
```

### Step 3: Update Page Component

```typescript
// File: frontend/src/pages/analytics/OperationsAnalyticsPage.tsx
// MODIFY the copied ProductionAnalyticsPage.tsx

import React, { useState } from 'react';
import { useOperationsMonthly, useOperationsSummary } from '../../hooks/useOperations';
// ... rest of imports SAME as ProductionAnalyticsPage

const OperationsAnalyticsPage: React.FC = () => {
  const [startMonth, setStartMonth] = useState<string>('');
  const [endMonth, setEndMonth] = useState<string>('');
  const [selectedPractice, setSelectedPractice] = useState<string>('');

  // Fetch data - SAME PATTERN as production page
  const { data: monthlyData, isLoading } = useOperationsMonthly({
    practice_location: selectedPractice || undefined,
    start_month: startMonth || undefined,
    end_month: endMonth || undefined,
  });

  const { data: summaryData } = useOperationsSummary({
    practice_location: selectedPractice || undefined,
    month: endMonth || undefined,
  });

  // REUSE: Same KPI cards, charts, tables - just different data fields
  return (
    <div className="space-y-6">
      {/* KPI Summary Cards - COPY from ProductionAnalyticsPage */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KPICard
          title="Total Production"
          value={formatCurrency(summaryData?.total_production)}
          trend={summaryData?.production_trend_pct}
        />
        <KPICard
          title="Collection Rate"
          value={formatPercent(summaryData?.collection_rate_pct)}
          target={95}
        />
        <KPICard
          title="Case Acceptance"
          value={formatPercent(summaryData?.case_acceptance_rate_pct)}
          target={85}
        />
        <KPICard
          title="Hygiene Efficiency"
          value={summaryData?.hygiene_productivity_ratio?.toFixed(2)}
          target={2.5}
        />
      </div>

      {/* Production Trend Chart - REUSE from ProductionAnalyticsPage */}
      <ChartContainer title="Monthly Operations Trends">
        <LineChart data={monthlyData} ... />
      </ChartContainer>

      {/* Data Table - REUSE table component */}
      <DataTable
        data={monthlyData}
        columns={operationsColumns}
      />
    </div>
  );
};
```

### Step 4: Add Route

```typescript
// File: frontend/src/App.tsx
// ADD one line to existing routes

import OperationsAnalyticsPage from './pages/analytics/OperationsAnalyticsPage';

// In routes:
<Route path="/analytics/operations" element={<OperationsAnalyticsPage />} />
```

**That's ALL the frontend code needed!**

---

## ⏱️ Implementation Timeline (LEAN)

### Week 1: Database & Backend (3-4 days)

**Day 1: Snowflake & dbt Setup**
- [ ] Create `bronze.operations_metrics_raw` table in Snowflake (regular table)
- [ ] Create dbt model `models/silver/operations/stg_operations_metrics.sql` (dynamic table)
- [ ] Create dbt model `models/gold/operations/operations_kpis_monthly.sql` (dynamic table)
- [ ] Run `dbt run --select +operations_kpis_monthly` to create dynamic tables
- [ ] Test with sample JSON INSERT to bronze → verify auto-propagation to gold

**Day 2: Excel Parser**
- [ ] Build `OperationsReportParser` class (copy pdf_ingestion.py pattern)
- [ ] Test Excel parsing locally with one Operations Report file
- [ ] Validate extracted metrics match Excel values

**Day 3: API Development**
- [ ] Build `operations.py` API endpoints (copy analytics.py pattern)
  - POST /api/v1/operations/upload
  - GET /api/v1/operations/kpis/monthly
  - GET /api/v1/operations/kpis/summary
- [ ] Test endpoints with Postman/curl

**Day 4: Historical Data Load**
- [ ] Upload all 21 Operations Report Excel files via API
- [ ] Validate data in each layer:
  - Bronze: Raw JSON stored correctly
  - Silver: Metrics extracted and typed
  - Gold: KPIs calculated with LTM rollups
- [ ] Verify dynamic table refresh (wait 1 hour or force refresh)
- [ ] Buffer/testing day

**Deliverables:**
- ✅ 3 dbt models (Bronze table + 2 Dynamic Tables)
- ✅ Working API with 21 months historical data
- ✅ Auto-refreshing pipeline (Bronze → Silver → Gold)

---

### Week 2: Frontend Dashboard (3-4 days)

**Day 1:**
- [ ] Copy ProductionAnalyticsPage → OperationsAnalyticsPage
- [ ] Create useOperations.ts hooks
- [ ] Add route to App.tsx

**Day 2:**
- [ ] Update KPI cards with operations metrics
- [ ] Test data fetching and display

**Day 3:**
- [ ] Add operations-specific charts (case acceptance funnel, hygiene efficiency)
- [ ] Add practice comparison table

**Day 4:**
- [ ] Polish UI, add filters
- [ ] Add export functionality (reuse existing)
- [ ] Buffer/testing day

**Deliverables:** Fully functional Operations Dashboard

---

### Week 3: Polish & Automation (optional)

**Day 1-2:**
- [ ] Add automated alerts for metrics outside target
- [ ] Build email report (weekly operations summary)

**Day 3-4:**
- [ ] Documentation
- [ ] User training
- [ ] Demo to stakeholders

---

## 📝 What We're NOT Building (For Now)

To keep this LEAN, we're skipping:

❌ Complex Bronze→Silver→Gold pipeline (use direct Gold insert)
❌ dbt transformations (do calculations in parser)
❌ Real-time PMS integration (manual Excel upload for now)
❌ NetSuite/ADP integration (use Excel data)
❌ ML forecasting (use simple trend calculations)
❌ Mobile app

**We can add these later if needed!**

---

## 🎯 Success Criteria

### Technical
- ✅ API response time <500ms
- ✅ Dashboard load time <2s
- ✅ 100% data accuracy vs source Excel
- ✅ Works for all 14 practices

### Business
- ✅ Eliminate manual Excel reporting (save 8+ hrs/month)
- ✅ Real-time KPI visibility
- ✅ Historical trend analysis (21+ months)
- ✅ Practice comparison rankings

---

## 🚀 Phase 2 Ideas (Future)

Once dashboard is working:

1. **Automate Data Collection** - Pull from PMS, NetSuite, ADP directly
2. **Predictive Analytics** - Forecast production, case acceptance trends
3. **Automated Alerts** - Email when metrics fall below targets
4. **Provider Scorecards** - Individual provider performance tracking
5. **Industry Benchmarking** - Compare to national dental practice averages

---

## 💡 Key Insight: Reuse is Speed

By reusing existing infrastructure:

- **Database:** Same Snowflake setup, just add 1 table
- **Backend:** Copy analytics.py, change table name
- **Frontend:** Copy ProductionAnalyticsPage.tsx, change hooks
- **Deployment:** Already have CI/CD, just commit and push

**Result:** 2-3 weeks instead of 8 weeks, with proven patterns.

---

## 📋 Checklist - Ready to Start?

Before beginning implementation:

- [ ] Stakeholder approval on LEAN approach
- [ ] Access to all Operations Report Excel files
- [ ] Practice code mapping (LHD = ?, EFD I = ?, etc.)
- [ ] Provider name mapping (Doctor #1 = ?, Doctor #2 = ?)
- [ ] Target ranges validated with clinical team
- [ ] Snowflake access confirmed
- [ ] Development environment ready

---

## 🎉 Summary

**Original Plan:** 8 weeks, complex architecture, lots of new code, manual dbt runs
**LEAN Plan w/ Dynamic Tables:** 2-3 weeks, reuse 80% existing code, ZERO manual dbt runs!

**Key Advantages:**
- ✅ **Faster delivery** - 2-3 weeks vs 8 weeks
- ✅ **Lower risk** - Using proven code patterns
- ✅ **Easier maintenance** - Familiar codebase structure
- ✅ **Auto-refreshing pipeline** - Dynamic tables handle Bronze→Silver→Gold automatically!
- ✅ **No dbt orchestration** - Snowflake handles refresh scheduling
- ✅ **Real-time(ish) data** - 1-hour lag from upload to dashboard (configurable)

**Trade-offs:**
- ⚠️ Manual Excel upload initially (can automate PMS integration later)
- ⚠️ Simpler calculations in Phase 1 (can enhance with ML later)
- ⚠️ Dynamic table costs (small - only refresh when source changes)

**Why Dynamic Tables are Perfect for This:**
1. **Historical Data:** 21 months already loaded → no need for frequent refresh
2. **Monthly Updates:** New data only comes in monthly → minimal compute cost
3. **LTM Calculations:** Window functions in dynamic tables are super efficient
4. **Zero Maintenance:** Set it and forget it - Snowflake handles everything

**Recommendation:** Start with LEAN approach + dynamic tables, iterate based on feedback.

---

**Document Owner:** Development Team
**Next Step:** Get stakeholder approval and begin Week 1
**Last Updated:** November 14, 2025
