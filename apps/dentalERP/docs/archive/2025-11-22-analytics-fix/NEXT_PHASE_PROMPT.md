# Next Phase Prompt - Complete Data Integration

Use this prompt to continue work in the next session:

---

## 📋 STARTING CONTEXT

I need to complete the NetSuite data integration for the Unified Analytics Dashboard.

**Current State:**
- ✅ Infrastructure 100% deployed (Snowflake tables, APIs, frontend)
- ✅ 14 practices with Operations Report data (85% complete)
- ✅ Unified analytics dashboard live at https://dentalerp.agentprovision.com/analytics/overview
- ⏳ NetSuite CSV data loading in progress (15 files in `backup/TransactionDetail-*.csv`)

**What Needs to be Done:**
1. Complete loading all NetSuite CSV files to Snowflake
2. Refresh `bronze_gold.netsuite_monthly_financials` dynamic table
3. Verify NetSuite financial data appears in `gold.practice_analytics_unified`
4. Test that Overview tab shows Revenue/Expenses/Net Income for all practices
5. Commit and deploy final changes

---

## 🎯 IMMEDIATE TASKS

### **Task 1: Check NetSuite CSV Loading Status**

The script `scripts/python/load_all_netsuite_csvs.py` was running in background.

Check status:
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
cursor.execute("SELECT COUNT(*) FROM bronze.netsuite_transaction_details WHERE TYPE != 'Type'")
count = cursor.fetchone()[0]
print(f"NetSuite transactions loaded: {count}")
cursor.close()
conn.close()
EOF
```

**Expected:** ~10,000+ transactions (if loading completed)

**If not complete:** Run `python3 scripts/python/load_all_netsuite_csvs.py` to finish

---

### **Task 2: Refresh Dynamic Tables**

After NetSuite data is loaded:

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
print("Refreshing dynamic tables...")
cursor.execute("ALTER DYNAMIC TABLE bronze_gold.netsuite_monthly_financials REFRESH")
print("✅ NetSuite monthly financials refreshed")
cursor.execute("ALTER DYNAMIC TABLE gold.practice_analytics_unified REFRESH")
print("✅ Unified view refreshed")
conn.commit()
cursor.close()
conn.close()
EOF
```

---

### **Task 3: Verify Financial Data Integration**

Check that NetSuite data now appears:

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

# Check how many practices now have financial data
cursor.execute("""
    SELECT
        practice_id,
        practice_display_name,
        COUNT(*) as months,
        SUM(netsuite_revenue) as revenue,
        SUM(netsuite_net_income) as net_income
    FROM gold.practice_analytics_unified
    WHERE netsuite_revenue IS NOT NULL
    GROUP BY practice_id, practice_display_name
    ORDER BY revenue DESC
""")

print("Practices with NetSuite Financial Data:")
for r in cursor.fetchall():
    print(f"  {r[0]:10s}: {r[2]:2d} months, ${r[3]:>12,.0f} revenue, ${r[4]:>10,.0f} net income")

cursor.close()
conn.close()
EOF
```

**Expected:** 10+ practices (not just 3)

---

### **Task 4: Test Production Dashboard**

1. Open: https://dentalerp.agentprovision.com/analytics/overview
2. Check "Net Income" KPI card - should show $X million (not N/A)
3. Check "Revenue (NetSuite)" KPI card - should show data
4. Select a practice (e.g., ADS or Eastlake) - should see both operations + financial metrics

---

## 📁 KEY FILES

**Completed Work:**
- `gold.practice_master` - 14 practice mappings
- `gold.practice_analytics_unified` - Unified view (341 records)
- `bronze_gold.operations_kpis_monthly` - Operations data
- `bronze_gold.netsuite_monthly_financials` - Financial data
- `frontend/src/pages/analytics/OverviewPage.tsx` - Overview tab with 8 KPIs

**Scripts:**
- `scripts/python/load_all_practices_operations_improved.py` - Improved Operations parser
- `scripts/python/load_all_netsuite_csvs.py` - NetSuite CSV loader (currently running)
- `scripts/create-unified-analytics-view.py` - Recreates unified view

**Plans:**
- `docs/plans/2025-11-18-unified-analytics-consolidation.md` - Full implementation plan
- `docs/plans/2025-11-20-netsuite-financial-integration.md` - NetSuite integration plan

---

## 🎯 SUCCESS CRITERIA

**Data:**
- [ ] All 15 NetSuite CSV files loaded (~10K+ transactions)
- [ ] 10+ practices with NetSuite financial data (revenue, expenses, net income)
- [ ] Unified view shows both Operations + NetSuite for each practice
- [ ] No data corruption or duplicates

**Dashboard:**
- [ ] Overview tab displays NetSuite revenue/expenses/net income
- [ ] Financial tab shows detailed NetSuite metrics
- [ ] All 14 practices appear in dropdowns
- [ ] Cross-system validation visible (Operations production vs NetSuite revenue)

---

## 🚀 NEXT SESSION APPROACH

**Use superpowers methodology:**

1. **Start:** Read NETSUITE_API_INTEGRATION_NEXT_STEPS.md
2. **Check:** NetSuite CSV loading status
3. **Execute:** Complete loading if needed, refresh tables, verify data
4. **Test:** Dashboard shows financial metrics
5. **Deploy:** If any frontend changes needed
6. **Verify:** End-to-end testing

**Estimated Time:** 1-2 hours to complete

---

## 📊 CURRENT STATUS SUMMARY

**Infrastructure:** ✅ 100% Complete
- Snowflake unified view (joins Operations + NetSuite + PMS)
- API endpoints (MCP + Backend)
- Frontend (4 tabs, Overview default)
- Navigation cleaned

**Data:**
- ✅ Operations: 341 records, 14 practices, 85% complete
- ⏳ NetSuite: Loading CSV files (15 practices worth of data)
- ✅ Practice mappings: Created for all subsidiaries

**Code:**
- 26+ commits deployed
- 55+ files changed
- 6,000+ lines of code

**Production:**
- Dashboard accessible and functional
- Shows operations data for all 14 practices
- NetSuite financial data will appear after loading completes

---

## 📝 RECOMMENDED PROMPT FOR NEXT SESSION

```
Continue the unified analytics work. I need to:

1. Check if the NetSuite CSV loading completed (scripts/python/load_all_netsuite_csvs.py)
2. Refresh the netsuite_monthly_financials and practice_analytics_unified dynamic tables
3. Verify all practices now have NetSuite financial data (revenue, expenses, net income)
4. Test the production dashboard shows the financial metrics
5. Fix any data quality issues found
6. Deploy and verify end-to-end

Background:
- Operations Report data is loaded (14 practices, 85% complete)
- NetSuite CSVs are in backup/ directory (15 files with transaction details)
- Unified view infrastructure is complete
- Just need to finish loading NetSuite data and verify integration

Goal: Complete automation of Operations Report by integrating all NetSuite financial data.

Use superpowers:executing-plans with the plan in:
docs/plans/2025-11-20-netsuite-financial-integration.md
```

---

**Session Complete - Ready for Final NetSuite Data Integration Phase**
**Estimated Next Session:** 1-2 hours
**Status:** Ready to execute when you are!

---

**Created:** November 20, 2025
