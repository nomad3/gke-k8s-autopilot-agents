# NetSuite Financial Integration - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate NetSuite financial data (Revenue, Expenses, Net Income) into unified analytics view to overlay financial performance with operational metrics.

**Architecture:** Extract subsidiary names from existing NetSuite transaction data, update practice_master mappings, create monthly financial aggregations, and join into gold.practice_analytics_unified.

**Tech Stack:** Snowflake (SQL aggregations), Python (data analysis), FastAPI (API updates)

---

## Current State Analysis

**NetSuite Data Available:**
- ✅ bronze.netsuite_transaction_details (3,868 records)
- ✅ bronze.netsuite_accounts (chart of accounts)
- ✅ bronze.netsuite_customers, vendors, invoices
- ❌ No structured subsidiary_name column
- ❌ CSV format without proper subsidiary identification

**Operations Data:**
- ✅ 341 records, 14 practices, 85% complete
- ✅ Production, collections, visits all tracking
- ✅ Primary data source (complete)

**Gap:**
- Need to extract subsidiary/practice from NetSuite transactions
- Map to practice_master
- Aggregate financial metrics by practice/month

---

## Task 1: Analyze NetSuite Transaction Data Structure

**Files:**
- Create: `scripts/python/analyze_netsuite_data.py`

**Step 1: Inspect NetSuite transaction data**

```python
#!/usr/bin/env python3
"""Analyze NetSuite data to find how practices are identified"""

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

print("=" * 80)
print("NETSUITE DATA STRUCTURE ANALYSIS")
print("=" * 80)

# Get all columns
cursor.execute("DESCRIBE TABLE bronze.netsuite_transaction_details")
columns = [c[0] for c in cursor.fetchall()]

print(f"\nColumns in netsuite_transaction_details ({len(columns)}):")
for col in columns:
    print(f"  • {col}")

# Get sample records (skip header row)
cursor.execute("SELECT * FROM bronze.netsuite_transaction_details WHERE TYPE != 'Type' LIMIT 10")
results = cursor.fetchall()

if results:
    print(f"\nSample Transactions ({len(results)}):")
    for i, r in enumerate(results[:3], 1):
        print(f"\n  Transaction {i}:")
        for col, val in zip(columns, r):
            if val and str(val).strip() not in ['', 'Type', 'Date']:
                print(f"     {col}: {val}")

# Check if there's a location/subsidiary indicator
print("\n" + "=" * 80)
print("LOOKING FOR PRACTICE/LOCATION INDICATORS:")
print("=" * 80)

# Check for patterns in NAME, MEMO, or ACCOUNT columns
for col in ['NAME', 'MEMO', 'ACCOUNT', 'SPLIT']:
    try:
        cursor.execute(f"SELECT DISTINCT {col} FROM bronze.netsuite_transaction_details WHERE {col} IS NOT NULL AND {col} != '{col}' LIMIT 20")
        values = cursor.fetchall()
        if values:
            unique_values = [v[0] for v in values if v[0]][:10]
            if unique_values:
                print(f"\n{col} column samples:")
                for v in unique_values:
                    print(f"  • {v}")
    except:
        pass

cursor.close()
conn.close()

print()
print("=" * 80)
print("💡 Look for practice names (Eastlake, Torrey Pines, etc.) in the output")
EOF
```

**Step 2: Run analysis**

Run: `python3 scripts/python/analyze_netsuite_data.py > /tmp/netsuite_analysis.txt`

**Step 3: Review output**

Check: `/tmp/netsuite_analysis.txt` for:
- Which column contains practice/subsidiary identifier
- How practices are named (exact strings)
- Whether we can map to our 14 practices

**Step 4: Document findings**

Create: `docs/NETSUITE_DATA_MAPPING.md` with:
- Column that identifies practice
- Actual practice/subsidiary names found
- Mapping to practice_master

**Step 5: Commit**

```bash
git add scripts/python/analyze_netsuite_data.py docs/NETSUITE_DATA_MAPPING.md
git commit -m "docs: analyze NetSuite data structure for practice mapping"
```

---

## Task 2: Create NetSuite Practice Identifier Extraction

**Files:**
- Create: `database/snowflake/add-netsuite-practice-identifier.sql`

**Step 1: Add practice identifier extraction logic**

Based on findings from Task 1, create SQL to extract practice from NetSuite data:

```sql
-- Option A: If practice is in NAME column
CREATE OR REPLACE VIEW bronze.netsuite_transactions_with_practice AS
SELECT
    *,
    CASE
        WHEN NAME LIKE '%Eastlake%' THEN 'sed'
        WHEN NAME LIKE '%Laguna Hills%' THEN 'lhd'
        WHEN NAME LIKE '%Torrey Pines%' THEN 'efd_i'
        WHEN NAME LIKE '%San Marcos%' OR NAME LIKE '%ADS%' THEN 'ads'
        -- Add all 14 practices
        ELSE NULL
    END AS practice_id
FROM bronze.netsuite_transaction_details
WHERE TYPE != 'Type';  -- Skip header row

-- Option B: If practice is in separate column
-- CREATE VIEW extracting from that column

-- Option C: If no clear practice identifier
-- May need to load from CSV with practice column added
```

**Step 2: Test extraction**

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
cursor.execute("""
    SELECT practice_id, COUNT(*)
    FROM bronze.netsuite_transactions_with_practice
    WHERE practice_id IS NOT NULL
    GROUP BY practice_id
""")
for r in cursor.fetchall():
    print(f"  {r[0]}: {r[1]} transactions")
cursor.close()
conn.close()
EOF
```

Expected: Shows transaction counts per practice

**Step 3: Commit**

```bash
git add database/snowflake/add-netsuite-practice-identifier.sql
git commit -m "feat: add practice identifier extraction for NetSuite data"
```

---

## Task 3: Create Monthly Financial Aggregations

**Files:**
- Create: `database/snowflake/create-netsuite-monthly-financials.sql`

**Step 1: Aggregate NetSuite transactions to monthly financials**

```sql
CREATE OR REPLACE DYNAMIC TABLE bronze_gold.netsuite_monthly_financials
TARGET_LAG = '1 hour'
WAREHOUSE = COMPUTE_WH
AS
SELECT
    nt.practice_id,
    DATE_TRUNC('MONTH', TO_DATE(nt.DATE, 'MM/DD/YYYY')) AS report_month,
    'silvercreek' AS tenant_id,

    -- Revenue (credits to income accounts)
    SUM(CASE
        WHEN TRY_CAST(nt.AMOUNT AS DECIMAL(18,2)) < 0
        THEN ABS(TRY_CAST(nt.AMOUNT AS DECIMAL(18,2)))
        ELSE 0
    END) AS monthly_revenue,

    -- Expenses (debits to expense accounts)
    SUM(CASE
        WHEN TRY_CAST(nt.AMOUNT AS DECIMAL(18,2)) > 0
        THEN TRY_CAST(nt.AMOUNT AS DECIMAL(18,2))
        ELSE 0
    END) AS monthly_expenses,

    -- Net Income
    SUM(CASE
        WHEN TRY_CAST(nt.AMOUNT AS DECIMAL(18,2)) < 0
        THEN ABS(TRY_CAST(nt.AMOUNT AS DECIMAL(18,2)))
        ELSE 0
    END) - SUM(CASE
        WHEN TRY_CAST(nt.AMOUNT AS DECIMAL(18,2)) > 0
        THEN TRY_CAST(nt.AMOUNT AS DECIMAL(18,2))
        ELSE 0
    END) AS monthly_net_income,

    -- Transaction count
    COUNT(*) AS transaction_count,

    CURRENT_TIMESTAMP() AS calculated_at

FROM bronze.netsuite_transactions_with_practice nt
WHERE nt.practice_id IS NOT NULL
  AND TRY_CAST(nt.DATE AS DATE) IS NOT NULL
GROUP BY nt.practice_id, DATE_TRUNC('MONTH', TO_DATE(nt.DATE, 'MM/DD/YYYY'));
```

**Step 2: Execute creation**

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

with open('database/snowflake/create-netsuite-monthly-financials.sql') as f:
    cursor.execute(f.read())
conn.commit()

# Verify
cursor.execute("SELECT COUNT(*), COUNT(DISTINCT practice_id) FROM bronze_gold.netsuite_monthly_financials")
r = cursor.fetchone()
print(f"✅ NetSuite monthly financials: {r[0]} records, {r[1]} practices")

cursor.close()
conn.close()
EOF
```

Expected: Shows monthly financial records per practice

**Step 3: Commit**

```bash
git add database/snowflake/create-netsuite-monthly-financials.sql
git commit -m "feat: create NetSuite monthly financial aggregations"
```

---

## Task 4: Update Unified View to Include NetSuite Financials

**Files:**
- Modify: `database/snowflake/create-unified-analytics-view.sql`

**Step 1: Update unified view SQL**

Replace the NetSuite NULL placeholders with actual JOIN:

Find:
```sql
    -- Financial Metrics (from NetSuite) - Placeholder for when tables exist
    CAST(NULL AS DECIMAL(18,2)) AS netsuite_revenue,
    CAST(NULL AS DECIMAL(18,2)) AS netsuite_expenses,
    CAST(NULL AS DECIMAL(18,2)) AS netsuite_net_income,
    CAST(NULL AS DECIMAL(5,2)) AS netsuite_profit_margin,
    CAST(NULL AS DECIMAL(5,2)) AS netsuite_revenue_growth,
```

Replace with:
```sql
    -- Financial Metrics (from NetSuite)
    fin.monthly_revenue AS netsuite_revenue,
    fin.monthly_expenses AS netsuite_expenses,
    fin.monthly_net_income AS netsuite_net_income,
    CASE
        WHEN fin.monthly_revenue > 0
        THEN (fin.monthly_net_income / fin.monthly_revenue * 100)
        ELSE NULL
    END AS netsuite_profit_margin,
    0 AS netsuite_revenue_growth,  -- Calculate later with LAG function
```

Add JOIN:
```sql
LEFT JOIN bronze_gold.netsuite_monthly_financials fin
    ON pm.practice_id = fin.practice_id
    AND DATE_TRUNC('MONTH', ops.report_month) = fin.report_month
    AND pm.tenant_id = fin.tenant_id
```

**Step 2: Recreate unified view**

```bash
python3 scripts/create-unified-analytics-view.py
```

Expected: "✅ Unified view created with NetSuite data"

**Step 3: Verify NetSuite data appears**

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
cursor.execute("""
    SELECT COUNT(*), SUM(netsuite_revenue), SUM(netsuite_net_income)
    FROM gold.practice_analytics_unified
    WHERE netsuite_revenue IS NOT NULL
""")
r = cursor.fetchone()
print(f"✅ Records with NetSuite data: {r[0]}")
print(f"   Total Revenue: ${r[1]:,.2f}")
print(f"   Total Net Income: ${r[2]:,.2f}")
cursor.close()
conn.close()
EOF
```

Expected: Shows revenue and net income totals

**Step 4: Commit**

```bash
git add database/snowflake/create-unified-analytics-view.sql
git commit -m "feat: integrate NetSuite financial data into unified view"
```

---

## Task 5: Update Financial Tab to Display NetSuite Metrics

**Files:**
- Modify: `frontend/src/pages/analytics/FinancialAnalyticsPage.tsx`

**Step 1: Update to use unified API**

Change imports:
```typescript
import { useUnifiedMonthly, useUnifiedSummary, useUnifiedByPractice } from '../../hooks/useUnifiedAnalytics';
```

Update hooks:
```typescript
const { data: monthlyData } = useUnifiedMonthly({
  practice_id: selectedPractice || undefined,
  start_month: startMonth || undefined,
  end_month: endMonth || undefined,
  category: 'financial',  // Filter to financial metrics
  limit: 100,
});
```

**Step 2: Add financial KPI cards**

```typescript
{summaryData && (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow p-6 text-white">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium opacity-90">Total Revenue</span>
        <ChartBarIcon className="h-5 w-5 opacity-80" />
      </div>
      <div className="text-3xl font-bold">
        {formatCurrency(summaryData.total_revenue || summaryData.TOTAL_REVENUE)}
      </div>
      <div className="text-xs opacity-80 mt-1">
        From NetSuite
      </div>
    </div>

    <div className="bg-gradient-to-br from-red-500 to-red-600 rounded-lg shadow p-6 text-white">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium opacity-90">Total Expenses</span>
        <ChartBarIcon className="h-5 w-5 opacity-80" />
      </div>
      <div className="text-3xl font-bold">
        {formatCurrency(summaryData.total_expenses || summaryData.TOTAL_EXPENSES)}
      </div>
      <div className="text-xs opacity-80 mt-1">
        Operating costs
      </div>
    </div>

    <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow p-6 text-white">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium opacity-90">Net Income</span>
        <ChartBarIcon className="h-5 w-5 opacity-80" />
      </div>
      <div className="text-3xl font-bold">
        {formatCurrency(summaryData.total_net_income || summaryData.TOTAL_NET_INCOME)}
      </div>
      <div className="text-xs opacity-80 mt-1">
        Revenue - Expenses
      </div>
    </div>

    <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow p-6 text-white">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium opacity-90">Profit Margin</span>
        <ChartBarIcon className="h-5 w-5 opacity-80" />
      </div>
      <div className="text-3xl font-bold">
        {formatPercent(summaryData.avg_profit_margin || summaryData.AVG_PROFIT_MARGIN)}
      </div>
      <div className="text-xs opacity-80 mt-1">
        Net Income / Revenue
      </div>
    </div>
  </div>
)}
```

**Step 3: Test compiles**

Run: `cd frontend && npm run type-check`
Expected: No errors

**Step 4: Commit**

```bash
git add frontend/src/pages/analytics/FinancialAnalyticsPage.tsx
git commit -m "feat: update Financial tab to show NetSuite metrics from unified view"
```

---

## Task 6: Deploy and Test NetSuite Integration

**Step 1: Push to GitHub**

```bash
git push origin main
```

**Step 2: Deploy to GCP**

```bash
gcloud compute ssh dental-erp-vm --zone=us-central1-a --command="cd /opt/dental-erp && git pull && python3 scripts/create-unified-analytics-view.py && sudo docker-compose build frontend-prod && sudo docker-compose --profile production up -d frontend-prod"
```

**Step 3: Test Financial tab**

Open: https://dentalerp.agentprovision.com/analytics/financial

Expected:
- See Revenue, Expenses, Net Income cards
- Practice filter shows all 14 practices
- Financial data displays for practices with NetSuite data

**Step 4: Verify cross-system data**

Select a practice (e.g., "Eastlake" or "ADS"):
- Overview tab: Shows operational + financial KPIs
- Operations tab: Shows detailed operations metrics
- Financial tab: Shows detailed NetSuite financials
- Production tab: Shows PMS day sheet data

Expected: All tabs show data for the same practice

---

## Task 7: Validation and Documentation

**Step 1: Run final data integrity check**

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

cursor.execute("""
    SELECT
        practice_id,
        COUNT(*) as total_months,
        SUM(CASE WHEN total_production > 0 THEN 1 ELSE 0 END) as has_ops_data,
        SUM(CASE WHEN netsuite_revenue IS NOT NULL THEN 1 ELSE 0 END) as has_netsuite_data,
        SUM(CASE WHEN pms_production IS NOT NULL THEN 1 ELSE 0 END) as has_pms_data
    FROM gold.practice_analytics_unified
    GROUP BY practice_id
    ORDER BY total_months DESC
""")

print("Practice Data Source Coverage:")
print(f"{'Practice':<10s} {'Months':<8s} {'Operations':<12s} {'NetSuite':<10s} {'PMS':<10s}")
print("-" * 60)

for r in cursor.fetchall():
    print(f"{r[0]:<10s} {r[1]:<8d} {r[2]:<12d} {r[3]:<10d} {r[4]:<10d}")

cursor.close()
conn.close()
EOF
```

Expected: Shows which practices have which data sources

**Step 2: Document NetSuite integration status**

Create: `docs/NETSUITE_INTEGRATION_STATUS.md` with:
- Which practices have NetSuite data
- Date ranges for financial data
- Data completeness metrics
- Known gaps or issues

**Step 3: Commit**

```bash
git add docs/NETSUITE_INTEGRATION_STATUS.md
git commit -m "docs: NetSuite financial integration status and validation"
```

---

## Success Criteria

**NetSuite Data:**
- [ ] Subsidiary/practice identifiers extracted
- [ ] Monthly financial aggregations created
- [ ] Revenue, Expenses, Net Income calculating
- [ ] At least 3 main practices have financial data

**Unified View:**
- [ ] NetSuite columns populated (not NULL)
- [ ] Financial data joining correctly by practice + month
- [ ] No duplicates or data corruption

**Frontend:**
- [ ] Financial tab shows NetSuite metrics
- [ ] All practices show in Financial tab filter
- [ ] KPI cards display revenue/expenses/net income
- [ ] Cross-system validation visible

---

## Alternative Approach (If NetSuite Data Unclear)

If Task 1 shows NetSuite data doesn't have clear practice identifiers:

**Option A: Use Existing CSV Files**
- Load NetSuite CSVs from `backup/TransactionDetail-*.csv`
- Add practice_id column during load
- Aggregate to monthly financials
- Join into unified view

**Option B: Manual Mapping Table**
- Create mapping: NetSuite account → Practice
- Use account patterns to identify practice
- Aggregate by identified practice

**Option C: Skip for Now**
- Operations Report has 85% of needed metrics
- Focus on operational analytics first
- Add NetSuite later when data is clearer

---

## Estimated Timeline

- Task 1: NetSuite data analysis (45 min)
- Task 2: Practice identifier extraction (30 min)
- Task 3: Monthly aggregations (45 min)
- Task 4: Update unified view (20 min)
- Task 5: Update Financial tab (30 min)
- Task 6: Deploy & test (30 min)
- Task 7: Validation (30 min)

**Total: ~4 hours** (or less if using CSV approach)

---

## Rollback Plan

If NetSuite integration causes issues:

```sql
-- Revert unified view to Operations-only
DROP DYNAMIC TABLE gold.practice_analytics_unified;
-- Recreate without NetSuite JOIN
-- (Original version without fin.monthly_revenue, etc.)
```

Frontend changes can be reverted via git.

---

**Plan Status:** ✅ COMPLETE
**Ready for:** Execution (if NetSuite integration desired)
**Alternative:** Operations Report data alone is production-ready

**Created:** November 20, 2025
