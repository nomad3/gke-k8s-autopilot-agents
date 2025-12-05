# Fix Data Quality and Complete Integration - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix Excel parser to extract all 60+ metrics correctly, verify/update NetSuite subsidiary mappings, and update Operations/Production tabs to use unified API for consistency.

**Architecture:** Improve Operations Report Excel parser to handle all 14 practice sheet layouts, validate NetSuite subsidiary name mappings, consolidate all analytics tabs to use gold.practice_analytics_unified.

**Tech Stack:** Python (pandas for Excel parsing), Snowflake, React + TypeScript

---

## Current State Analysis

**Data Quality Issues:**
- 62.8% of records missing visit counts
- 100% missing case acceptance metrics
- 100% missing new patient metrics
- 93.6% missing hygiene capacity metrics
- 0% NetSuite financial data joined (mapping issue)

**Root Causes:**
1. Excel parser uses fixed row numbers (doesn't work for all sheet layouts)
2. NetSuite subsidiary names are assumptions (not verified against actual data)
3. Operations/Production tabs still use old APIs (not unified data)

---

## Task 1: Analyze Excel Sheet Structures

**Files:**
- Create: `scripts/python/analyze_operations_sheet_layouts.py`

**Step 1: Create sheet analysis script**

```python
#!/usr/bin/env python3
"""Analyze all 14 practice sheets to understand layout variations"""

import pandas as pd

excel_file = 'examples/ingestion/Operations Report(28).xlsx'
xl_file = pd.ExcelFile(excel_file)

practice_sheets = [s for s in xl_file.sheet_names if s != 'Operating Metrics']

print("=" * 80)
print("OPERATIONS REPORT SHEET LAYOUT ANALYSIS")
print("=" * 80)
print()

for sheet_name in practice_sheets:
    print(f"\n📄 {sheet_name}")
    print("-" * 80)

    df = pd.read_excel(excel_file, sheet_name=sheet_name)

    # Find where metrics start (look for common labels in column 1)
    metric_labels = []
    for idx in range(100):
        if idx >= len(df):
            break
        val = str(df.iloc[idx, 1]).strip() if pd.notna(df.iloc[idx, 1]) else ''
        if val and val not in ['nan', '']:
            if any(keyword in val.upper() for keyword in ['PRODUCTION', 'VISITS', 'PATIENTS', 'HYGIENE', 'COLLECTION']):
                metric_labels.append((idx, val))

    print(f"   Key metric rows found: {len(metric_labels)}")
    for row_idx, label in metric_labels[:10]:
        print(f"      Row {row_idx:3d}: {label}")

    # Check date row (usually row 4)
    date_row = df.iloc[4]
    dates_found = sum(1 for val in date_row if pd.notna(val))
    print(f"   Date columns (row 4): {dates_found}")

print()
print("=" * 80)
print("💡 INSIGHT: Each sheet has metrics at different row positions")
print("   Need flexible parser that searches for metric labels, not fixed rows")
EOF
```

**Step 2: Run analysis**

Run: `python3 scripts/python/analyze_operations_sheet_layouts.py`
Expected: Shows which rows contain which metrics for each practice

**Step 3: Document findings**

Create: `docs/EXCEL_PARSER_ANALYSIS.md` with:
- Which metrics are at which rows for each practice
- Common patterns across sheets
- Variations to handle

**Step 4: Commit**

```bash
git add scripts/python/analyze_operations_sheet_layouts.py docs/EXCEL_PARSER_ANALYSIS.md
git commit -m "docs: analyze Operations Report sheet layout variations"
```

---

## Task 2: Create Improved Excel Parser

**Files:**
- Modify: `scripts/python/load_all_practices_operations.py`

**Step 1: Add flexible metric extraction function**

Add this function to the file:

```python
def find_metric_row(df, search_terms, start_row=0, end_row=120):
    """
    Find row containing metric label

    Args:
        df: DataFrame
        search_terms: List of terms to search for (e.g., ['Gross Production', 'Total'])
        start_row: Start searching from this row
        end_row: Stop searching at this row

    Returns:
        Row index or None
    """
    for idx in range(start_row, min(end_row, len(df))):
        cell_value = str(df.iloc[idx, 1]).strip() if pd.notna(df.iloc[idx, 1]) else ''

        # Check if all search terms are in the cell
        if all(term.upper() in cell_value.upper() for term in search_terms):
            return idx

    return None


def extract_value_at_row(df, row_idx, col_idx):
    """Safely extract numeric value from cell"""
    if row_idx is None or row_idx >= len(df):
        return 0

    value = df.iloc[row_idx, col_idx]
    if pd.notna(value) and value != '':
        try:
            if isinstance(value, (int, float)):
                return float(value)
            else:
                return float(str(value).replace(',', ''))
        except:
            return 0
    return 0
```

**Step 2: Update metric extraction to use flexible search**

Replace the fixed row extraction with:

```python
# Instead of:
metrics['total_production'] = float(df.iloc[11, col_idx])

# Use:
row_total_prod = find_metric_row(df, ['Gross Production', 'Total'])
metrics['total_production'] = extract_value_at_row(df, row_total_prod, col_idx)

row_net_prod = find_metric_row(df, ['Net Production'])
metrics['net_production'] = extract_value_at_row(df, row_net_prod, col_idx)

row_collections = find_metric_row(df, ['Collections'])
metrics['collections'] = extract_value_at_row(df, row_collections, col_idx)

row_doctor_visits = find_metric_row(df, ['Doctor', 'Total'])  # "Total" under Doctors section
metrics['visits_doctor_total'] = extract_value_at_row(df, row_doctor_visits, col_idx)

row_hygiene_visits = find_metric_row(df, ['Hygienists'])
metrics['visits_hygiene'] = extract_value_at_row(df, row_hygiene_visits, col_idx)

row_total_visits = find_metric_row(df, ['Total'], start_row=row_hygiene_visits or 40)
metrics['visits_total'] = extract_value_at_row(df, row_total_visits, col_idx)

row_new_patients = find_metric_row(df, ['New Patients', 'Total'])
metrics['new_patients_total'] = extract_value_at_row(df, row_new_patients, col_idx)

row_treatment_presented = find_metric_row(df, ['Treatment Presented'])
metrics['treatment_presented'] = extract_value_at_row(df, row_treatment_presented, col_idx)

row_treatment_accepted = find_metric_row(df, ['Treatment Accepted'])
metrics['treatment_accepted'] = extract_value_at_row(df, row_treatment_accepted, col_idx)

row_hygiene_capacity = find_metric_row(df, ['Hygiene Capacity'])
metrics['hygiene_capacity_slots'] = extract_value_at_row(df, row_hygiene_capacity, col_idx)

row_hygiene_prod = find_metric_row(df, ['Hygiene Net Production'])
metrics['hygiene_net_production'] = extract_value_at_row(df, row_hygiene_prod, col_idx)

row_hygiene_comp = find_metric_row(df, ['Hygiene Compensation'])
metrics['hygiene_compensation'] = extract_value_at_row(df, row_hygiene_comp, col_idx)
```

**Step 3: Test improved parser on one practice**

Run: `python3 scripts/python/load_all_practices_operations.py` (with just LHD for testing)
Expected: See more metrics extracted (visits, case acceptance, new patients)

**Step 4: Clear existing data and reload all practices**

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
cursor.execute("DELETE FROM bronze.operations_metrics_raw")
cursor.execute("ALTER DYNAMIC TABLE bronze_silver.stg_operations_metrics REFRESH")
cursor.execute("ALTER DYNAMIC TABLE bronze_gold.operations_kpis_monthly REFRESH")
cursor.execute("ALTER DYNAMIC TABLE gold.practice_analytics_unified REFRESH")
conn.commit()
print("✅ Cleared old data, ready for reload")
cursor.close()
conn.close()
EOF

python3 scripts/python/load_all_practices_operations.py
```

Expected: All 14 practices with improved metric extraction

**Step 5: Commit**

```bash
git add scripts/python/load_all_practices_operations.py
git commit -m "feat: improve Excel parser with flexible metric detection"
```

---

## Task 3: Verify and Fix NetSuite Subsidiary Mappings

**Files:**
- Create: `scripts/python/verify_netsuite_subsidiary_mappings.py`

**Step 1: Check what NetSuite subsidiary data we actually have**

```python
#!/usr/bin/env python3
import os, snowflake.connector, json
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
print("NETSUITE SUBSIDIARY NAME EXTRACTION")
print("=" * 80)

# Try to find subsidiary names from transaction data
cursor.execute("""
    SELECT DISTINCT
        raw_data:subsidiary.id::STRING as sub_id,
        raw_data:subsidiary.refName::STRING as sub_name
    FROM bronze.netsuite_journal_entries
    WHERE raw_data:subsidiary.refName IS NOT NULL
    LIMIT 20
""")

print("\nSubsidiaries found in Journal Entries:")
results = cursor.fetchall()
if results:
    for r in results:
        print(f"  ID: {r[0]:5s} | Name: {r[1]}")
else:
    print("  (No data)")

# Check transaction details too
try:
    cursor.execute("""
        SELECT DISTINCT subsidiary_name
        FROM bronze.netsuite_transaction_details
        LIMIT 20
    """)
    results = cursor.fetchall()
    if results:
        print("\nSubsidiaries from Transaction Details:")
        for r in results:
            print(f"  • {r[0]}")
except:
    pass

cursor.close()
conn.close()

print()
print("=" * 80)
print("💡 Use these ACTUAL names to update practice_master")
EOF
```

**Step 2: Run verification**

Run: `python3 scripts/python/verify_netsuite_subsidiary_mappings.py`
Expected: Shows actual NetSuite subsidiary names

**Step 3: Update practice_master with correct names**

Based on output from Step 2, update:

```sql
UPDATE gold.practice_master
SET netsuite_subsidiary_name = 'ACTUAL_NAME_FROM_NETSUITE'
WHERE practice_id = 'lhd';

-- Repeat for all 14 practices with correct names
```

**Step 4: Refresh unified view**

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
cursor.execute("ALTER DYNAMIC TABLE gold.practice_analytics_unified REFRESH")
conn.commit()
print("✅ Unified view refreshed with corrected mappings")
cursor.close()
conn.close()
EOF
```

**Step 5: Commit**

```bash
git add scripts/python/verify_netsuite_subsidiary_mappings.py
git commit -m "feat: verify and correct NetSuite subsidiary mappings"
```

---

## Task 4: Update Operations Tab to Use Unified API

**Files:**
- Modify: `frontend/src/pages/analytics/OperationsAnalyticsPage.tsx`

**Step 1: Change imports**

Find:
```typescript
import { useOperationsMonthly, useOperationsSummary, useOperationsByPractice } from '../../hooks/useOperations';
```

Replace with:
```typescript
import { useUnifiedMonthly, useUnifiedSummary, useUnifiedByPractice } from '../../hooks/useUnifiedAnalytics';
```

**Step 2: Update hook calls**

Find:
```typescript
const { data: monthlyData, isLoading: monthlyLoading, error: monthlyError } = useOperationsMonthly({
```

Replace with:
```typescript
const { data: monthlyData, isLoading: monthlyLoading, error: monthlyError } = useUnifiedMonthly({
  category: 'operations',  // Filter to operations metrics only
```

**Step 3: Update field names to match unified view**

Change:
- `practice_location` → `practice_id`
- `PRACTICE_LOCATION` → `PRACTICE_ID`
- Add practice name display from `PRACTICE_DISPLAY_NAME`

**Step 4: Test compiles**

Run: `cd frontend && npm run type-check`
Expected: No errors

**Step 5: Commit**

```bash
git add frontend/src/pages/analytics/OperationsAnalyticsPage.tsx
git commit -m "feat: update Operations tab to use unified analytics API"
```

---

## Task 5: Update Production Tab to Use Unified API

**Files:**
- Modify: `frontend/src/pages/analytics/ProductionAnalyticsPage.tsx`

**Step 1: Change imports**

Find:
```typescript
import { useProductionDaily, useProductionSummary, useProductionByPractice } from '../../hooks/useAnalytics';
```

Replace with:
```typescript
import { useUnifiedMonthly, useUnifiedSummary, useUnifiedByPractice } from '../../hooks/useUnifiedAnalytics';
```

**Step 2: Update hook calls**

Replace hooks with unified versions:
```typescript
const { data: monthlyData } = useUnifiedMonthly({
  category: 'production',  // Filter to PMS production metrics only
  practice_id: selectedPractice || undefined,
  start_month: startDate || undefined,
  end_month: endDate || undefined,
  limit: 100,
});
```

**Step 3: Update field names**

Change to use unified view field names:
- `pms_production` instead of `total_production`
- `pms_visits` instead of `patient_visits`
- `pms_ppv` instead of `production_per_visit`

**Step 4: Test compiles**

Run: `cd frontend && npm run type-check`
Expected: No errors

**Step 5: Commit**

```bash
git add frontend/src/pages/analytics/ProductionAnalyticsPage.tsx
git commit -m "feat: update Production tab to use unified analytics API"
```

---

## Task 6: Deploy and Test

**Step 1: Push to GitHub**

```bash
git push origin main
```

**Step 2: Deploy to GCP**

```bash
gcloud compute ssh dental-erp-vm --zone=us-central1-a --command="cd /opt/dental-erp && git pull && sudo docker-compose build backend-prod frontend-prod mcp-server-prod && sudo docker-compose stop backend-prod frontend-prod mcp-server-prod && sudo docker-compose rm -f backend-prod frontend-prod mcp-server-prod && sudo docker-compose --profile production up -d backend-prod frontend-prod mcp-server-prod"
```

**Step 3: Verify all tabs show same practice list**

Test each tab:
1. Overview - Should show all 14 practices in dropdown
2. Operations - Should show all 14 practices in dropdown
3. Financial - Should show all 14 practices in dropdown
4. Production - Should show all 14 practices in dropdown

Expected: ALL tabs show consistent practice list

**Step 4: Verify data quality improved**

Check Operations tab:
- More visit counts visible (target: >80% of records)
- Case acceptance showing (target: >50% of records)
- New patients showing (target: >50% of records)

---

## Task 7: Final Data Quality Validation

**Step 1: Run data quality check**

```bash
python3 /tmp/check-whats-missing.py
```

Expected after fixes:
- Missing Visits: <20% (down from 62.8%)
- Missing Case Acceptance: <50% (down from 100%)
- Missing New Patients: <50% (down from 100%)
- Missing Hygiene Capacity: <50% (down from 93.6%)

**Step 2: Document remaining gaps**

Create: `docs/DATA_QUALITY_REPORT.md` with:
- Which practices have complete data
- Which metrics still need work
- Recommendations for manual data entry or client validation

**Step 3: Commit**

```bash
git add docs/DATA_QUALITY_REPORT.md
git commit -m "docs: data quality assessment after parser improvements"
```

---

## Success Criteria

**Data Quality:**
- [ ] >80% of records have visit counts
- [ ] >50% of records have case acceptance
- [ ] >50% of records have new patient counts
- [ ] All 14 practices have data

**Consistency:**
- [ ] Operations tab uses unified API
- [ ] Production tab uses unified API
- [ ] All tabs show same 14 practices in filter
- [ ] No "N/A" for metrics that should have data

**Integration:**
- [ ] NetSuite subsidiary mappings verified
- [ ] Financial data joining (even if just for 3 main practices)

---

## Estimated Timeline

- Task 1: Sheet analysis (30 min)
- Task 2: Improved parser (60 min)
- Task 3: NetSuite mapping (45 min)
- Task 4: Update Operations tab (20 min)
- Task 5: Update Production tab (20 min)
- Task 6: Deploy & test (30 min)
- Task 7: Validation (30 min)

**Total: ~4 hours**

---

**Plan Status:** ✅ COMPLETE
**Ready for:** Execution via superpowers:executing-plans
**Created:** November 19, 2025
