# Unified Analytics Consolidation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Consolidate Operations + Financial + Production analytics into single unified view with practice master mapping and clean up all legacy/placeholder pages.

**Architecture:** Create gold.practice_master mapping table and gold.practice_analytics_unified dynamic table that JOINs all data sources. Consolidate frontend into single Analytics page with 4 tabs (Overview, Operations, Financial, Production). Remove 10 placeholder pages and clean navigation.

**Tech Stack:** Snowflake Dynamic Tables, FastAPI (MCP), Express (Backend), React + TypeScript

---

## Task 1: Create Practice Master Mapping Table

**Files:**
- Create: `database/snowflake/create-practice-master.sql`

**Step 1: Create SQL for practice master table**

```sql
-- Practice Master Mapping Table
-- Single source of truth for practice identifiers across all systems

USE DATABASE DENTAL_ERP_DW;
USE SCHEMA GOLD;
USE ROLE ACCOUNTADMIN;

CREATE TABLE IF NOT EXISTS gold.practice_master (
    practice_id VARCHAR(50) PRIMARY KEY,
    practice_display_name VARCHAR(100) NOT NULL,

    -- System-specific identifiers
    operations_code VARCHAR(20),           -- LHD, EFD I, ADS (from Ops Report)
    netsuite_subsidiary_id VARCHAR(50),
    netsuite_subsidiary_name VARCHAR(100), -- SCDP Eastlake, etc.
    pms_location_code VARCHAR(50),         -- eastlake, torrey_pines (from day sheets)
    adp_location_code VARCHAR(50),         -- For future ADP integration
    eaglesoft_practice_id VARCHAR(50),     -- For future Eaglesoft API

    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    tenant_id VARCHAR(50) DEFAULT 'silvercreek',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Master practice mapping across all integrated systems (Operations, NetSuite, PMS, ADP)';

-- Insert all 14 practice mappings
INSERT INTO gold.practice_master
(practice_id, practice_display_name, operations_code, netsuite_subsidiary_name, pms_location_code, tenant_id)
VALUES
('lhd', 'Laguna Hills Dental', 'LHD', 'SCDP Laguna Hills', 'laguna_hills', 'silvercreek'),
('efd_i', 'Encinitas Family Dental I', 'EFD I', 'SCDP Encinitas I', 'encinitas_1', 'silvercreek'),
('cvfd', 'Carmel Valley Family Dental', 'CVFD', 'SCDP Carmel Valley', 'carmel_valley', 'silvercreek'),
('dsr', 'Del Sur Dental', 'DSR', 'SCDP Del Sur', 'del_sur', 'silvercreek'),
('ads', 'Advanced Dental Solutions', 'ADS', 'SCDP San Marcos', 'ads', 'silvercreek'),
('ipd', 'Imperial Point Dental', 'IPD', 'SCDP Imperial Point', 'imperial_point', 'silvercreek'),
('efd_ii', 'Encinitas Family Dental II', 'EFD II', 'SCDP Encinitas II', 'encinitas_2', 'silvercreek'),
('rd', 'Rancho Dental', 'RD', 'SCDP Rancho', 'rancho', 'silvercreek'),
('lsd', 'La Senda Dental', 'LSD', 'SCDP La Senda', 'la_senda', 'silvercreek'),
('ucfd', 'University City Family Dental', 'UCFD', 'SCDP University City', 'university_city', 'silvercreek'),
('lcd', 'La Costa Dental', 'LCD', 'SCDP La Costa', 'la_costa', 'silvercreek'),
('eawd', 'East Avenue Dental', 'EAWD', 'SCDP East Avenue', 'east_avenue', 'silvercreek'),
('sed', 'Scripps Eastlake Dental', 'SED', 'SCDP Eastlake', 'eastlake', 'silvercreek'),
('dd', 'Downtown Dental', 'DD', 'SCDP Downtown', 'downtown', 'silvercreek');

SELECT 'Practice master table created with 14 practices' AS status;
```

**Step 2: Create Python script to execute SQL**

Create: `scripts/create-practice-master.py`

```python
#!/usr/bin/env python3
import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv('mcp-server/.env')

conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    role=os.getenv('SNOWFLAKE_ROLE'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
    database=os.getenv('SNOWFLAKE_DATABASE')
)

cursor = conn.cursor()

# Read and execute SQL
with open('database/snowflake/create-practice-master.sql') as f:
    sql = f.read()

for statement in sql.split(';'):
    if statement.strip():
        cursor.execute(statement)

conn.commit()

# Verify
cursor.execute("SELECT COUNT(*) FROM gold.practice_master")
count = cursor.fetchone()[0]
print(f"✅ Practice master created with {count} practices")

cursor.close()
conn.close()
```

**Step 3: Execute locally**

Run: `python3 scripts/create-practice-master.py`
Expected: "✅ Practice master created with 14 practices"

**Step 4: Verify mapping**

```bash
python3 << 'EOF'
import os, snowflake.connector
from dotenv import load_dotenv
load_dotenv('mcp-server/.env')
conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    role=os.getenv('SNOWFLAKE_ROLE'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
    database=os.getenv('SNOWFLAKE_DATABASE')
)
cursor = conn.cursor()
cursor.execute("SELECT practice_id, practice_display_name, operations_code FROM gold.practice_master ORDER BY practice_id")
for row in cursor.fetchall():
    print(f"  {row[0]:15s} {row[1]:40s} ({row[2]})")
cursor.close()
conn.close()
EOF
```

Expected: List of 14 practices with all codes

**Step 5: Commit**

```bash
git add database/snowflake/create-practice-master.sql scripts/create-practice-master.py
git commit -m "feat: add practice master mapping table for all 14 practices"
```

---

## Task 2: Create Unified Analytics View

**Files:**
- Create: `database/snowflake/create-unified-analytics-view.sql`

**Step 1: Write SQL for unified dynamic table**

```sql
USE DATABASE DENTAL_ERP_DW;
USE SCHEMA GOLD;
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE DYNAMIC TABLE gold.practice_analytics_unified
TARGET_LAG = '1 hour'
WAREHOUSE = COMPUTE_WH
AS
SELECT
    pm.practice_id,
    pm.practice_display_name,
    COALESCE(ops.report_month, fin.month, pms.month) AS report_month,
    pm.tenant_id,

    -- Operations Metrics (ALL from Operations Report)
    ops.total_production,
    ops.gross_production_doctor,
    ops.gross_production_specialty,
    ops.gross_production_hygiene,
    ops.net_production,
    ops.collections,
    ops.collection_rate_pct,
    ops.adjustment_rate_pct,
    ops.visits_doctor_1,
    ops.visits_doctor_2,
    ops.visits_doctor_total,
    ops.visits_specialist,
    ops.visits_hygiene,
    ops.visits_total,
    ops.ppv_doctor_1,
    ops.ppv_doctor_2,
    ops.ppv_doctor_avg,
    ops.ppv_specialist,
    ops.ppv_hygiene,
    ops.ppv_overall,
    ops.doc1_treatment_presented,
    ops.doc1_treatment_accepted,
    ops.doc1_acceptance_rate_pct,
    ops.doc2_treatment_presented,
    ops.doc2_treatment_accepted,
    ops.doc2_acceptance_rate_pct,
    ops.case_acceptance_rate_pct,
    ops.new_patients_total,
    ops.new_patients_reappt_rate,
    ops.hygiene_capacity_slots,
    ops.hygiene_capacity_utilization_pct,
    ops.hygiene_net_production,
    ops.hygiene_compensation,
    ops.hygiene_productivity_ratio,
    ops.hygiene_reappt_rate,
    ops.doctor_1_production,
    ops.doctor_2_production,
    ops.specialist_production,
    ops.ltm_production,
    ops.ltm_collections,
    ops.ltm_visits,
    ops.ltm_new_patients,

    -- Financial Metrics (from NetSuite)
    fin.monthly_revenue AS netsuite_revenue,
    fin.monthly_expenses AS netsuite_expenses,
    fin.monthly_net_income AS netsuite_net_income,
    fin.profit_margin_pct AS netsuite_profit_margin,
    fin.revenue_growth_pct AS netsuite_revenue_growth,

    -- PMS Production (from day sheets, aggregated monthly)
    pms.total_production AS pms_production,
    pms.collections AS pms_collections,
    pms.patient_visits AS pms_visits,
    pms.production_per_visit AS pms_ppv,
    pms.data_quality_score AS pms_quality,

    -- Cross-System Validations
    ops.total_production - COALESCE(pms.total_production, 0) AS production_variance,
    ops.collections - COALESCE(pms.collections, 0) AS collections_variance,

    -- Metadata
    ops.extraction_method,
    ops.data_quality_score,
    CURRENT_TIMESTAMP() AS calculated_at

FROM gold.practice_master pm

LEFT JOIN bronze_gold.operations_kpis_monthly ops
    ON LOWER(REPLACE(pm.operations_code, ' ', '_')) = ops.practice_location
    AND pm.tenant_id = ops.tenant_id

LEFT JOIN gold.monthly_financial_kpis fin
    ON pm.netsuite_subsidiary_name = fin.subsidiary_name
    AND DATE_TRUNC('MONTH', ops.report_month) = fin.month
    AND pm.tenant_id = fin.tenant_id

LEFT JOIN (
    SELECT
        practice_location,
        DATE_TRUNC('MONTH', report_date) AS month,
        SUM(total_production) AS total_production,
        SUM(collections) AS collections,
        SUM(patient_visits) AS patient_visits,
        AVG(production_per_visit) AS production_per_visit,
        AVG(data_quality_score) AS data_quality_score
    FROM bronze_gold.daily_production_metrics
    GROUP BY practice_location, DATE_TRUNC('MONTH', report_date)
) pms
    ON pm.pms_location_code = pms.practice_location
    AND DATE_TRUNC('MONTH', ops.report_month) = pms.month

WHERE pm.is_active = TRUE;

COMMENT ON DYNAMIC TABLE gold.practice_analytics_unified IS
'Unified practice analytics joining Operations Report + NetSuite + PMS + ADP (future)';

SELECT 'Unified analytics view created' AS status;
```

**Step 2: Create execution script**

Create: `scripts/create-unified-analytics-view.py`

```python
#!/usr/bin/env python3
import os
import snowflake.connector
from dotenv import load_dotenv
from pathlib import Path

load_dotenv('mcp-server/.env')

conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    role=os.getenv('SNOWFLAKE_ROLE'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
    database=os.getenv('SNOWFLAKE_DATABASE')
)

cursor = conn.cursor()

# Read and execute
sql_path = Path('database/snowflake/create-unified-analytics-view.sql')
with open(sql_path) as f:
    sql = f.read()

for statement in sql.split(';'):
    statement = statement.strip()
    if statement and not statement.startswith('--'):
        cursor.execute(statement)
        if 'SELECT' in statement and 'AS status' in statement:
            result = cursor.fetchone()
            if result:
                print(f"  {result[0]}")

conn.commit()

# Verify row count
cursor.execute("SELECT COUNT(*), COUNT(DISTINCT practice_id) FROM gold.practice_analytics_unified")
result = cursor.fetchone()
print(f"✅ Unified view created: {result[0]} records, {result[1]} practices")

cursor.close()
conn.close()
```

**Step 3: Execute locally**

Run: `chmod +x scripts/create-unified-analytics-view.py && python3 scripts/create-unified-analytics-view.py`
Expected: "✅ Unified view created: 327 records, 13 practices"

**Step 4: Verify unified view has all metrics**

```bash
python3 << 'EOF'
import os, snowflake.connector
from dotenv import load_dotenv
load_dotenv('mcp-server/.env')
conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    role=os.getenv('SNOWFLAKE_ROLE'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
    database=os.getenv('SNOWFLAKE_DATABASE')
)
cursor = conn.cursor()
cursor.execute("SELECT * FROM gold.practice_analytics_unified LIMIT 1")
columns = [desc[0] for desc in cursor.description]
print(f"Total columns: {len(columns)}")
print("Sample columns:")
for col in columns[:20]:
    print(f"  • {col}")
cursor.close()
conn.close()
EOF
```

Expected: ~70+ columns including all operations metrics

**Step 5: Commit**

```bash
git add database/snowflake/create-unified-analytics-view.sql scripts/create-unified-analytics-view.py
git commit -m "feat: create unified practice analytics view joining all data sources"
```

---

## Task 3: Create Unified API Endpoints

**Files:**
- Create: `mcp-server/src/api/analytics_unified.py`
- Modify: `mcp-server/src/main.py` (add router)

**Step 1: Create unified analytics API**

Create: `mcp-server/src/api/analytics_unified.py`

```python
"""
Unified Analytics API - Single source for all practice metrics
Queries gold.practice_analytics_unified (Operations + Financial + PMS + ADP)
"""

from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..core.security import get_api_key_header
from ..core.tenant import TenantContext
from ..services.warehouse_router import get_tenant_warehouse
from ..utils.logger import logger

router = APIRouter(prefix="/api/v1/analytics/unified", tags=["analytics-unified"])


@router.get("/monthly")
async def get_unified_monthly_analytics(
    practice_id: Optional[str] = Query(None, description="Filter by practice ID"),
    start_month: Optional[str] = Query(None, description="Start month (YYYY-MM-DD)"),
    end_month: Optional[str] = Query(None, description="End month (YYYY-MM-DD)"),
    category: Optional[str] = Query('all', description="all|operations|financial|production"),
    limit: int = Query(100, ge=1, le=1000),
    api_key: str = Depends(get_api_key_header)
):
    """
    Get unified monthly analytics from all data sources

    Returns all metrics from Operations Report + NetSuite + PMS
    """
    warehouse = await get_tenant_warehouse()
    tenant = TenantContext.get_tenant()

    # Build WHERE clause
    where_clauses = [f"tenant_id = '{tenant.tenant_code}'"]
    if practice_id:
        where_clauses.append(f"practice_id = '{practice_id}'")
    if start_month:
        where_clauses.append(f"report_month >= '{start_month}'")
    if end_month:
        where_clauses.append(f"report_month <= '{end_month}'")

    where_sql = f"WHERE {' AND '.join(where_clauses)}"

    # Select columns based on category
    if category == 'operations':
        select_cols = """
            practice_id, practice_display_name, report_month,
            total_production, collections, collection_rate_pct,
            visits_total, ppv_overall, case_acceptance_rate_pct,
            hygiene_productivity_ratio, new_patients_total,
            ltm_production, ltm_collections
        """
    elif category == 'financial':
        select_cols = """
            practice_id, practice_display_name, report_month,
            netsuite_revenue, netsuite_expenses, netsuite_net_income,
            netsuite_profit_margin, netsuite_revenue_growth
        """
    elif category == 'production':
        select_cols = """
            practice_id, practice_display_name, report_month,
            pms_production, pms_collections, pms_visits, pms_ppv, pms_quality
        """
    else:  # 'all'
        select_cols = "*"

    query = f"""
        SELECT {select_cols}
        FROM gold.practice_analytics_unified
        {where_sql}
        ORDER BY report_month DESC, practice_id
        LIMIT {limit}
    """

    logger.info(f"Unified analytics query: {category}, practice: {practice_id}")

    try:
        results = await warehouse.execute_query(query)
        return results
    except Exception as e:
        logger.error(f"Unified analytics query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query unified analytics: {str(e)}"
        )


@router.get("/summary")
async def get_unified_summary(
    practice_id: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    api_key: str = Depends(get_api_key_header)
):
    """Get aggregated summary from unified view"""

    warehouse = await get_tenant_warehouse()
    tenant = TenantContext.get_tenant()

    where_clauses = [f"tenant_id = '{tenant.tenant_code}'"]
    if practice_id:
        where_clauses.append(f"practice_id = '{practice_id}'")
    if month:
        where_clauses.append(f"report_month = '{month}'")
    else:
        where_clauses.append(f"report_month = (SELECT MAX(report_month) FROM gold.practice_analytics_unified WHERE tenant_id = '{tenant.tenant_code}')")

    where_sql = f"WHERE {' AND '.join(where_clauses)}"

    query = f"""
        SELECT
            COUNT(DISTINCT practice_id) AS practice_count,
            MAX(report_month) AS latest_month,
            SUM(total_production) AS total_production,
            SUM(collections) AS total_collections,
            AVG(collection_rate_pct) AS avg_collection_rate,
            SUM(visits_total) AS total_visits,
            AVG(ppv_overall) AS avg_ppv,
            AVG(case_acceptance_rate_pct) AS avg_case_acceptance,
            AVG(hygiene_productivity_ratio) AS avg_hygiene_ratio,
            SUM(netsuite_revenue) AS total_revenue,
            SUM(netsuite_expenses) AS total_expenses,
            SUM(netsuite_net_income) AS total_net_income,
            SUM(ltm_production) AS ltm_production
        FROM gold.practice_analytics_unified
        {where_sql}
    """

    try:
        results = await warehouse.execute_query(query)
        return results[0] if results else {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-practice")
async def get_unified_by_practice(
    start_month: Optional[str] = Query(None),
    end_month: Optional[str] = Query(None),
    api_key: str = Depends(get_api_key_header)
):
    """Get metrics aggregated by practice"""

    warehouse = await get_tenant_warehouse()
    tenant = TenantContext.get_tenant()

    where_clauses = [f"tenant_id = '{tenant.tenant_code}'"]
    if start_month:
        where_clauses.append(f"report_month >= '{start_month}'")
    if end_month:
        where_clauses.append(f"report_month <= '{end_month}'")

    where_sql = f"WHERE {' AND '.join(where_clauses)}"

    query = f"""
        SELECT
            practice_id,
            practice_display_name,
            COUNT(DISTINCT report_month) AS months_tracked,
            SUM(total_production) AS total_production,
            SUM(collections) AS total_collections,
            AVG(collection_rate_pct) AS avg_collection_rate,
            SUM(visits_total) AS total_visits,
            AVG(ppv_overall) AS avg_ppv,
            AVG(case_acceptance_rate_pct) AS avg_case_acceptance,
            AVG(hygiene_productivity_ratio) AS avg_hygiene_ratio,
            SUM(netsuite_revenue) AS total_revenue,
            SUM(netsuite_net_income) AS total_net_income,
            MIN(report_month) AS first_month,
            MAX(report_month) AS last_month
        FROM gold.practice_analytics_unified
        {where_sql}
        GROUP BY practice_id, practice_display_name
        ORDER BY total_production DESC
    """

    try:
        results = await warehouse.execute_query(query)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 2: Register router in main.py**

Modify: `mcp-server/src/main.py`

Find line: `from .api import data, health, integrations, mappings, warehouse, pdf_ingestion, dbt_runner, analytics, tenants, products, netsuite_sync, financial, bulk_load, operations`

Change to: `from .api import data, health, integrations, mappings, warehouse, pdf_ingestion, dbt_runner, analytics, tenants, products, netsuite_sync, financial, bulk_load, operations, analytics_unified`

Find line: `app.include_router(operations.router)  # Operations KPI tracking`

Add after: `app.include_router(analytics_unified.router)  # Unified analytics`

**Step 3: Test API locally**

Run MCP server: `cd mcp-server && uvicorn src.main:app --reload --port 8085`

Test:
```bash
curl http://localhost:8085/api/v1/analytics/unified/monthly?limit=5 \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  -H "X-Tenant-ID: silvercreek"
```

Expected: JSON array with unified metrics from all sources

**Step 4: Commit**

```bash
git add mcp-server/src/api/analytics_unified.py mcp-server/src/main.py
git commit -m "feat: add unified analytics API joining all data sources"
```

---

## Task 4: Update Backend Proxy Routes

**Files:**
- Create: `backend/src/routes/analyticsUnified.ts`
- Modify: `backend/src/server.ts`

**Step 1: Create backend proxy**

Create: `backend/src/routes/analyticsUnified.ts`

```typescript
import { Router } from 'express';
import { logger } from '../utils/logger';
import { getMCPClient } from '../services/mcpClient';

const router = Router();
const mcpClient = getMCPClient();

router.get('/monthly', async (req, res) => {
  try {
    const { practice_id, start_month, end_month, category, limit } = req.query;

    const response = await mcpClient.get('/api/v1/analytics/unified/monthly', {
      params: { practice_id, start_month, end_month, category, limit },
    });

    return res.json(response.data);
  } catch (error) {
    logger.error('Unified analytics monthly error:', error);
    return res.status(500).json({ error: 'Failed to fetch unified analytics' });
  }
});

router.get('/summary', async (req, res) => {
  try {
    const { practice_id, month } = req.query;

    const response = await mcpClient.get('/api/v1/analytics/unified/summary', {
      params: { practice_id, month },
    });

    return res.json(response.data);
  } catch (error) {
    logger.error('Unified analytics summary error:', error);
    return res.status(500).json({ error: 'Failed to fetch summary' });
  }
});

router.get('/by-practice', async (req, res) => {
  try {
    const { start_month, end_month } = req.query;

    const response = await mcpClient.get('/api/v1/analytics/unified/by-practice', {
      params: { start_month, end_month },
    });

    return res.json(response.data);
  } catch (error) {
    logger.error('Unified analytics by-practice error:', error);
    return res.status(500).json({ error: 'Failed to fetch by-practice' });
  }
});

export default router;
```

**Step 2: Register in server.ts**

Modify: `backend/src/server.ts`

Find: `import operationsRoutes from './routes/operations';`
Add: `import analyticsUnifiedRoutes from './routes/analyticsUnified';`

Find: `app.use('/api/operations', authMiddleware, auditMiddleware, operationsRoutes);`
Add after: `app.use('/api/analytics-unified', authMiddleware, auditMiddleware, analyticsUnifiedRoutes);`

**Step 3: Test backend locally**

Run: `cd backend && npm run dev`

Test:
```bash
# Get token first
TOKEN=$(curl -s http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@practice.com","password":"Admin123!"}' | jq -r '.accessToken')

curl http://localhost:3001/api/analytics-unified/monthly?limit=3 \
  -H "Authorization: Bearer $TOKEN"
```

Expected: JSON with unified analytics data

**Step 4: Commit**

```bash
git add backend/src/routes/analyticsUnified.ts backend/src/server.ts
git commit -m "feat: add backend proxy for unified analytics API"
```

---

## Task 5: Create Frontend Unified Hooks

**Files:**
- Create: `frontend/src/hooks/useUnifiedAnalytics.ts`

**Step 1: Create React Query hooks**

```typescript
import { useQuery, UseQueryResult } from '@tanstack/react-query';
import api from '../services/api';
import { useAuthStore } from '../store/authStore';

/**
 * Unified Analytics Hooks
 * Single source for all practice metrics (Operations + Financial + PMS)
 */

export const useUnifiedMonthly = (params: {
  practice_id?: string;
  start_month?: string;
  end_month?: string;
  category?: 'all' | 'operations' | 'financial' | 'production';
  limit?: number;
} = {}): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);

  return useQuery({
    queryKey: ['unified-monthly', params],
    queryFn: async () => {
      const response = await api.get('/analytics-unified/monthly', { params });
      return response.data;
    },
    enabled: !!user,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 30 * 60 * 1000,
  });
};

export const useUnifiedSummary = (params: {
  practice_id?: string;
  month?: string;
} = {}): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);

  return useQuery({
    queryKey: ['unified-summary', params],
    queryFn: async () => {
      const response = await api.get('/analytics-unified/summary', { params });
      return response.data;
    },
    enabled: !!user,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 30 * 60 * 1000,
  });
};

export const useUnifiedByPractice = (params: {
  start_month?: string;
  end_month?: string;
} = {}): UseQueryResult<any> => {
  const user = useAuthStore(state => state.user);

  return useQuery({
    queryKey: ['unified-by-practice', params],
    queryFn: async () => {
      const response = await api.get('/analytics-unified/by-practice', { params });
      return response.data;
    },
    enabled: !!user,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 30 * 60 * 1000,
  });
};
```

**Step 2: Test hooks work**

Create a test component to verify hooks return data (optional for validation)

**Step 3: Commit**

```bash
git add frontend/src/hooks/useUnifiedAnalytics.ts
git commit -m "feat: add unified analytics React Query hooks"
```

---

## Task 6: Create Overview Tab Page

**Files:**
- Create: `frontend/src/pages/analytics/OverviewPage.tsx`

**Step 1: Create Overview page with unified KPIs**

Create: `frontend/src/pages/analytics/OverviewPage.tsx`

```typescript
import React, { useState } from 'react';
import { useUnifiedMonthly, useUnifiedSummary, useUnifiedByPractice } from '../../hooks/useUnifiedAnalytics';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { ChartBarIcon, BanknotesIcon, UsersIcon, TrendingUpIcon } from '@heroicons/react/24/outline';

const OverviewPage: React.FC = () => {
  const [selectedPractice, setSelectedPractice] = useState<string>('');
  const [startMonth, setStartMonth] = useState<string>('');
  const [endMonth, setEndMonth] = useState<string>('');

  const { data: summaryData, isLoading: summaryLoading } = useUnifiedSummary({
    practice_id: selectedPractice || undefined,
    month: endMonth || undefined,
  });

  const { data: byPracticeData, isLoading: byPracticeLoading } = useUnifiedByPractice({
    start_month: startMonth || undefined,
    end_month: endMonth || undefined,
  });

  const { data: monthlyData } = useUnifiedMonthly({
    practice_id: selectedPractice || undefined,
    start_month: startMonth || undefined,
    end_month: endMonth || undefined,
    category: 'all',
    limit: 100,
  });

  const isLoading = summaryLoading || byPracticeLoading;

  // Format helpers
  const formatCurrency = (value: any) => {
    if (!value || isNaN(parseFloat(value))) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(parseFloat(value));
  };

  const formatPercent = (value: any) => {
    if (!value || isNaN(parseFloat(value))) return 'N/A';
    return `${parseFloat(value).toFixed(1)}%`;
  };

  const formatNumber = (value: any) => {
    if (!value || isNaN(parseFloat(value))) return 'N/A';
    return new Intl.NumberFormat('en-US').format(parseFloat(value));
  };

  // Get unique practices for filter
  const practices = React.useMemo(() => {
    if (!byPracticeData) return [];
    return byPracticeData.map((p: any) => ({
      id: p.practice_id || p.PRACTICE_ID,
      name: p.practice_display_name || p.PRACTICE_DISPLAY_NAME,
    }));
  }, [byPracticeData]);

  if (isLoading && !summaryData) {
    return (
      <div className="flex items-center justify-center h-96">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Practice Analytics Overview</h1>
        <p className="text-sm text-gray-600 mt-1">
          Unified view combining Operations Report + NetSuite + PMS data
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow border p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Practice
            </label>
            <select
              value={selectedPractice}
              onChange={(e) => setSelectedPractice(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-500"
            >
              <option value="">All Practices</option>
              {practices.map((p: any) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Month
            </label>
            <input
              type="month"
              value={startMonth}
              onChange={(e) => setStartMonth(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Month
            </label>
            <input
              type="month"
              value={endMonth}
              onChange={(e) => setEndMonth(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={() => {
                setSelectedPractice('');
                setStartMonth('');
                setEndMonth('');
              }}
              className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid - 8 Key Metrics */}
      {summaryData && (
        <>
          {/* Row 1: Financial */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-sky-500 to-sky-600 rounded-lg shadow p-6 text-white">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium opacity-90">Total Production</span>
                <ChartBarIcon className="h-5 w-5 opacity-80" />
              </div>
              <div className="text-3xl font-bold">
                {formatCurrency(summaryData.total_production || summaryData.TOTAL_PRODUCTION)}
              </div>
              <div className="text-xs opacity-80 mt-1">
                Across {formatNumber(summaryData.practice_count || summaryData.PRACTICE_COUNT)} practices
              </div>
            </div>

            <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow p-6 text-white">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium opacity-90">Collections</span>
                <BanknotesIcon className="h-5 w-5 opacity-80" />
              </div>
              <div className="text-3xl font-bold">
                {formatCurrency(summaryData.total_collections || summaryData.TOTAL_COLLECTIONS)}
              </div>
              <div className="text-xs opacity-80 mt-1">
                Rate: {formatPercent(summaryData.avg_collection_rate || summaryData.AVG_COLLECTION_RATE)}
              </div>
            </div>

            <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow p-6 text-white">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium opacity-90">Patient Visits</span>
                <UsersIcon className="h-5 w-5 opacity-80" />
              </div>
              <div className="text-3xl font-bold">
                {formatNumber(summaryData.total_visits || summaryData.TOTAL_VISITS)}
              </div>
              <div className="text-xs opacity-80 mt-1">
                PPV: {formatCurrency(summaryData.avg_ppv || summaryData.AVG_PPV)}
              </div>
            </div>

            <div className="bg-gradient-to-br from-amber-500 to-amber-600 rounded-lg shadow p-6 text-white">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium opacity-90">Net Income</span>
                <TrendingUpIcon className="h-5 w-5 opacity-80" />
              </div>
              <div className="text-3xl font-bold">
                {formatCurrency(summaryData.total_net_income || summaryData.TOTAL_NET_INCOME)}
              </div>
              <div className="text-xs opacity-80 mt-1">
                From NetSuite
              </div>
            </div>
          </div>

          {/* Row 2: Operations Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow p-6 text-white">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium opacity-90">Case Acceptance</span>
                <ChartBarIcon className="h-5 w-5 opacity-80" />
              </div>
              <div className="text-3xl font-bold">
                {formatPercent(summaryData.avg_case_acceptance || summaryData.AVG_CASE_ACCEPTANCE)}
              </div>
              <div className="text-xs opacity-80 mt-1">
                Treatment acceptance rate
              </div>
            </div>

            <div className="bg-gradient-to-br from-teal-500 to-teal-600 rounded-lg shadow p-6 text-white">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium opacity-90">Hygiene Efficiency</span>
                <ChartBarIcon className="h-5 w-5 opacity-80" />
              </div>
              <div className="text-3xl font-bold">
                {(summaryData.avg_hygiene_ratio || summaryData.AVG_HYGIENE_RATIO)?.toFixed(2) || 'N/A'}
              </div>
              <div className="text-xs opacity-80 mt-1">
                Productivity ratio
              </div>
            </div>

            <div className="bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-lg shadow p-6 text-white">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium opacity-90">Revenue (NetSuite)</span>
                <BanknotesIcon className="h-5 w-5 opacity-80" />
              </div>
              <div className="text-3xl font-bold">
                {formatCurrency(summaryData.total_revenue || summaryData.TOTAL_REVENUE)}
              </div>
              <div className="text-xs opacity-80 mt-1">
                From financial system
              </div>
            </div>

            <div className="bg-gradient-to-br from-rose-500 to-rose-600 rounded-lg shadow p-6 text-white">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium opacity-90">LTM Production</span>
                <TrendingUpIcon className="h-5 w-5 opacity-80" />
              </div>
              <div className="text-3xl font-bold">
                {formatCurrency(summaryData.ltm_production || summaryData.LTM_PRODUCTION)}
              </div>
              <div className="text-xs opacity-80 mt-1">
                Rolling 12 months
              </div>
            </div>
          </div>
        </>
      )}

      {/* Practice Comparison Table */}
      {byPracticeData && byPracticeData.length > 0 && (
        <div className="bg-white rounded-lg shadow border">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-semibold">Practice Performance Comparison</h3>
            <p className="text-sm text-gray-600 mt-1">All practices ranked by total production</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Practice</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Months</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Production</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Collections</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Visits</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">PPV</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Collection %</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {byPracticeData.map((practice: any, idx: number) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      {practice.practice_display_name || practice.PRACTICE_DISPLAY_NAME}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 text-right">
                      {practice.months_tracked || practice.MONTHS_TRACKED}
                    </td>
                    <td className="px-6 py-4 text-sm font-semibold text-gray-900 text-right">
                      {formatCurrency(practice.total_production || practice.TOTAL_PRODUCTION)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 text-right">
                      {formatCurrency(practice.total_collections || practice.TOTAL_COLLECTIONS)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 text-right">
                      {formatNumber(practice.total_visits || practice.TOTAL_VISITS)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 text-right">
                      {formatCurrency(practice.avg_ppv || practice.AVG_PPV)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 text-right">
                      {formatPercent(practice.avg_collection_rate || practice.AVG_COLLECTION_RATE)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default OverviewPage;
```

**Step 2: Test page compiles**

Run: `cd frontend && npm run type-check`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/pages/analytics/OverviewPage.tsx
git commit -m "feat: add unified analytics overview page"
```

---

## Task 7: Update Analytics Page with New Tab Structure

**Files:**
- Modify: `frontend/src/pages/analytics/AnalyticsPage.tsx`

**Step 1: Update tabs array**

Find:
```typescript
const tabs = [
  { to: 'production', label: 'Production' },
  { to: 'operations', label: 'Operations' },
  // ... lots of commented out tabs
];
```

Replace with:
```typescript
const tabs = [
  { to: 'overview', label: 'Overview' },
  { to: 'operations', label: 'Operations' },
  { to: 'financial', label: 'Financial' },
  { to: 'production', label: 'Production' },
];
```

**Step 2: Update imports**

Add: `import OverviewPage from './OverviewPage';`

Remove all placeholder page imports:
```typescript
// DELETE THESE:
import RevenueAnalyticsPage from './RevenueAnalyticsPage';
import PatientAnalyticsPage from './PatientAnalyticsPage';
import StaffAnalyticsPage from './StaffAnalyticsPage';
import ClinicalAnalyticsPage from './ClinicalAnalyticsPage';
import SchedulingAnalyticsPage from './SchedulingAnalyticsPage';
import RetentionCohortsPage from './RetentionCohortsPage';
import BenchmarkingPage from './BenchmarkingPage';
import ForecastingPage from './ForecastingPage';
import ReportsPage from './ReportsPage';
```

**Step 3: Update routes**

Find:
```typescript
<Routes>
  <Route index element={<Navigate to="production" replace />} />
  <Route path="production" element={<ProductionAnalyticsPage />} />
  <Route path="operations" element={<OperationsAnalyticsPage />} />
  // ... lots of placeholder routes
</Routes>
```

Replace with:
```typescript
<Routes>
  <Route index element={<Navigate to="overview" replace />} />
  <Route path="overview" element={<OverviewPage />} />
  <Route path="operations" element={<OperationsAnalyticsPage />} />
  <Route path="financial" element={<FinancialAnalyticsPage />} />
  <Route path="production" element={<ProductionAnalyticsPage />} />
  <Route path="*" element={<Navigate to="overview" replace />} />
</Routes>
```

**Step 4: Test page compiles**

Run: `cd frontend && npm run type-check`
Expected: No errors

**Step 5: Commit**

```bash
git add frontend/src/pages/analytics/AnalyticsPage.tsx
git commit -m "feat: consolidate analytics tabs to 4 main views (Overview, Operations, Financial, Production)"
```

---

## Task 8: Delete Legacy Placeholder Pages

**Files:**
- Delete: `frontend/src/pages/analytics/RevenueAnalyticsPage.tsx`
- Delete: `frontend/src/pages/analytics/PatientAnalyticsPage.tsx`
- Delete: `frontend/src/pages/analytics/StaffAnalyticsPage.tsx`
- Delete: `frontend/src/pages/analytics/ClinicalAnalyticsPage.tsx`
- Delete: `frontend/src/pages/analytics/SchedulingAnalyticsPage.tsx`
- Delete: `frontend/src/pages/analytics/RetentionCohortsPage.tsx`
- Delete: `frontend/src/pages/analytics/BenchmarkingPage.tsx`
- Delete: `frontend/src/pages/analytics/ForecastingPage.tsx`
- Delete: `frontend/src/pages/analytics/ReportsPage.tsx`
- Delete: `frontend/src/pages/analytics/EnhancedAnalyticsPage.tsx`

**Step 1: Delete all placeholder page files**

```bash
cd frontend/src/pages/analytics
rm RevenueAnalyticsPage.tsx \
   PatientAnalyticsPage.tsx \
   StaffAnalyticsPage.tsx \
   ClinicalAnalyticsPage.tsx \
   SchedulingAnalyticsPage.tsx \
   RetentionCohortsPage.tsx \
   BenchmarkingPage.tsx \
   ForecastingPage.tsx \
   ReportsPage.tsx \
   EnhancedAnalyticsPage.tsx
```

**Step 2: Verify no import errors**

Run: `cd frontend && npm run type-check`
Expected: No errors (if errors, fix remaining imports in AnalyticsPage.tsx)

**Step 3: Commit**

```bash
git add -A frontend/src/pages/analytics/
git commit -m "chore: remove 10 placeholder analytics pages"
```

---

## Task 9: Update Navigation Menu

**Files:**
- Modify: `frontend/src/layouts/DashboardLayout.tsx` (or wherever nav is defined)

**Step 1: Find navigation definition**

Check: `frontend/src/layouts/DashboardLayout.tsx` or `frontend/src/components/Navigation.tsx`

**Step 2: Remove legacy analytics submenu items**

Find the Analytics submenu structure (looks like):
```typescript
{
  name: 'Analytics',
  items: [
    { name: 'Enhanced Analytics', ... },
    { name: 'Revenue', ... },
    { name: 'Patients', ... },
    // etc.
  ]
}
```

Replace with:
```typescript
{
  name: 'Analytics',
  href: '/analytics',
  // No submenu - tabs are within the page
}
```

Or if keeping submenu:
```typescript
{
  name: 'Analytics',
  items: [
    { name: 'Overview', href: '/analytics/overview' },
    { name: 'Operations', href: '/analytics/operations' },
    { name: 'Financial', href: '/analytics/financial' },
    { name: 'Production', href: '/analytics/production' },
  ]
}
```

**Step 3: Test navigation**

Run: `cd frontend && npm run dev`
Open: http://localhost:3000
Expected: Analytics menu shows only 4 items (or no submenu)

**Step 4: Commit**

```bash
git add frontend/src/layouts/DashboardLayout.tsx
git commit -m "feat: clean up analytics navigation menu"
```

---

## Task 10: Deploy to Production

**Files:**
- Execute on GCP VM

**Step 1: Push all changes to GitHub**

```bash
git push origin main
```

**Step 2: SSH to GCP and pull code**

```bash
gcloud compute ssh dental-erp-vm --zone=us-central1-a
cd /opt/dental-erp
git pull
```

**Step 3: Create Snowflake tables on production**

```bash
python3 scripts/create-practice-master.py
python3 scripts/create-unified-analytics-view.py
```

Expected: "✅ Practice master created" and "✅ Unified view created"

**Step 4: Rebuild and restart all services**

```bash
sudo docker-compose build backend-prod frontend-prod mcp-server-prod
sudo docker-compose stop backend-prod frontend-prod mcp-server-prod
sudo docker-compose rm -f backend-prod frontend-prod mcp-server-prod
sudo docker-compose --profile production up -d backend-prod frontend-prod mcp-server-prod
```

**Step 5: Wait for startup and verify**

```bash
sleep 20
sudo docker ps | grep prod
```

Expected: All 3 prod containers running

**Step 6: Test production API**

```bash
export MCP_API_KEY="d876e6163089364d96a45a80ed576e99fc55b306133e258d9f861007e824b456"

curl https://mcp.agentprovision.com/api/v1/analytics/unified/by-practice \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: silvercreek" | head -50
```

Expected: JSON with all 13 practices

**Step 7: Test production frontend**

Open browser: https://dentalerp.agentprovision.com/analytics/overview
Expected: See Overview tab with 8 KPI cards and all 13 practices

---

## Task 11: End-to-End Verification

**Step 1: Verify all practices in filter dropdown**

1. Open: https://dentalerp.agentprovision.com/analytics/overview
2. Click practice dropdown
3. Expected: See all 13 practices

**Step 2: Verify all tabs work**

1. Click "Overview" tab - Expected: 8 KPI cards, practice comparison
2. Click "Operations" tab - Expected: All Ops Report metrics
3. Click "Financial" tab - Expected: NetSuite metrics
4. Click "Production" tab - Expected: PMS day sheet data

**Step 3: Verify filtering works**

1. Select practice "ADS"
2. Set date range "2024-01 to 2024-12"
3. Expected: Data filters to show only ADS for 2024

**Step 4: Verify cross-system data appears**

1. Select a practice that has all 3 data sources
2. Check that Operations + Financial + Production metrics all show
3. Expected: No "N/A" for practices with complete data

**Step 5: Document any issues**

Create: `docs/UNIFIED_ANALYTICS_VALIDATION.md` with:
- Which practices have complete data
- Which metrics are missing
- Any data quality issues found

---

## Success Criteria Checklist

**Database:**
- [ ] gold.practice_master exists with 14 practice mappings
- [ ] gold.practice_analytics_unified exists and has 300+ records
- [ ] All 13 practices appear in unified view
- [ ] Operations metrics present (60+ fields)
- [ ] NetSuite metrics present where available
- [ ] PMS metrics present where available

**Backend:**
- [ ] /api/v1/analytics/unified/* endpoints working
- [ ] /api/analytics-unified/* proxy working
- [ ] All 13 practices returned from by-practice endpoint

**Frontend:**
- [ ] Analytics page has 4 tabs only (Overview, Operations, Financial, Production)
- [ ] Overview tab shows 8 KPI cards
- [ ] Practice filter shows all 13 practices
- [ ] All placeholder pages deleted
- [ ] Navigation menu cleaned up (no legacy items)
- [ ] TypeScript builds with no errors

**Production:**
- [ ] All services deployed and running
- [ ] Frontend accessible at /analytics/overview
- [ ] API returns unified data
- [ ] All 13 practices visible in dashboard

---

## Rollback Plan

If issues arise:

**Database:**
```sql
DROP DYNAMIC TABLE gold.practice_analytics_unified;
DROP TABLE gold.practice_master;
```
(Original tables remain intact)

**API:**
Revert commits, redeploy previous version

**Frontend:**
```bash
git revert HEAD~3..HEAD  # Revert last 3 commits
git push origin main
# Redeploy
```

---

## Estimated Timeline

- Task 1: Practice master (30 min)
- Task 2: Unified view (45 min)
- Task 3: MCP API (45 min)
- Task 4: Backend proxy (30 min)
- Task 5: Frontend hooks (20 min)
- Task 6: Overview page (60 min)
- Task 7: Update tabs (30 min)
- Task 8: Delete pages (15 min)
- Task 9: Navigation (30 min)
- Task 10: Deploy (60 min)
- Task 11: Validation (30 min)

**Total: ~7 hours**

---

## Notes

- All Snowflake tables are cloud-based - local execution affects production immediately
- Use MERGE instead of INSERT to avoid duplicates
- Dynamic tables refresh automatically - no manual dbt runs needed
- Keep original source tables as backup (mark deprecated, delete after 30 days)
- Test each task locally before deploying

---

**Plan Status:** ✅ COMPLETE
**Ready for:** Execution via superpowers:executing-plans
**Created:** November 18, 2025
