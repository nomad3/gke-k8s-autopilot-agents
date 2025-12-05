# NetSuite API Integration - Next Steps

**Date:** November 20, 2025
**Status:** Framework Ready, API Call Needed
**Priority:** Complete automation of financial metrics

---

## 🎯 Goal

Automate Operations Report financial metrics by connecting to NetSuite API to fetch all subsidiary data and transactions, replacing manual CSV uploads.

---

## ✅ What's Already Done

### **Infrastructure:**
- ✅ NetSuite connector with OAuth 1.0a TBA (`mcp-server/src/connectors/netsuite.py`)
- ✅ Credentials configured in `.env`
- ✅ MCP API endpoint: `/api/v1/netsuite/sync/trigger`
- ✅ Practice identifier extraction logic created
- ✅ Monthly financial aggregations dynamic table created
- ✅ Unified view ready to join NetSuite data

### **Credentials (in mcp-server/.env):**
```
NETSUITE_ACCOUNT_ID=7048582
NETSUITE_CONSUMER_KEY=b1e7d9f7e7aacb40dfb8c867798438576c2dba1d80f53d325773622b5f4639a5
NETSUITE_CONSUMER_SECRET=d61f0cc714b4eba1edd3ba7db4278fec2507ac4249d07e557db8f995163b122e
NETSUITE_TOKEN_ID=535c55951e2a885077e33f72f412e7c35a7e5b937d760f768f00b4a95a83fd39
NETSUITE_TOKEN_SECRET=7f64f7395fe2b49a369f9776ebf4d3fb094717e2f40907a4246abff0a4e7aeb6
```

### **What CSV Analysis Showed:**
From `backup/TransactionDetail-*.csv` files (15 files):
- SCDP Eastlake, LLC
- SCDP Laguna Hills, LLC
- SCDP Torrey Pines, LLC
- SCDP Del Sur Ranch, LLC
- SCDP Coronado, LLC
- SCDP Temecula, LLC
- SCDP Torrey Highlands, LLC
- SCDP Kearny Mesa, LLC
- SCDP Vista, LLC
- SCDP Carlsbad, LLC
- SCDP UTC, LLC
- SCDP Laguna Hills II, LLC
- Steve P. Theodosis Dental Corporation, PC

**Total: 13 unique NetSuite subsidiaries**

---

## 📋 Steps to Complete NetSuite API Integration

### **Step 1: Fetch All Subsidiaries from NetSuite API**

**Option A: Via MCP API Endpoint**
```bash
curl -X POST https://mcp.agentprovision.com/api/v1/netsuite/sync/trigger \
  -H "Authorization: Bearer d876e6163089364d96a45a80ed576e99fc55b306133e258d9f861007e824b456" \
  -H "X-Tenant-ID: silvercreek" \
  -H "Content-Type: application/json" \
  -d '{"entity_types": ["subsidiary"], "full_sync": true}'
```

**Option B: Direct Python Script**
```python
# Create: scripts/python/fetch_all_netsuite_subsidiaries.py
import asyncio
import os
from dotenv import load_dotenv

load_dotenv('mcp-server/.env')

# Import NetSuite connector
from mcp_server.src.connectors.netsuite import NetSuiteConnector

async def fetch_subsidiaries():
    connector = NetSuiteConnector(
        account=os.getenv('NETSUITE_ACCOUNT_ID'),
        consumer_key=os.getenv('NETSUITE_CONSUMER_KEY'),
        consumer_secret=os.getenv('NETSUITE_CONSUMER_SECRET'),
        token_key=os.getenv('NETSUITE_TOKEN_ID'),
        token_secret=os.getenv('NETSUITE_TOKEN_SECRET')
    )

    subsidiaries = await connector.get_subsidiaries()

    print(f"Found {len(subsidiaries)} subsidiaries:")
    for sub in subsidiaries:
        print(f"  ID: {sub.get('id'):5s} | Name: {sub.get('name')}")

asyncio.run(fetch_subsidiaries())
```

Run: `python3 scripts/python/fetch_all_netsuite_subsidiaries.py`

---

### **Step 2: Update practice_master with Correct Subsidiary Names**

Once we have the actual names from Step 1, update the mapping:

```sql
-- File: database/snowflake/update-practice-master-netsuite-names.sql

USE DATABASE DENTAL_ERP_DW;
USE SCHEMA GOLD;

UPDATE gold.practice_master
SET netsuite_subsidiary_name = CASE practice_id
    WHEN 'sed' THEN 'SCDP Eastlake, LLC'
    WHEN 'lhd' THEN 'SCDP Laguna Hills, LLC'
    WHEN 'efd_i' THEN 'SCDP Torrey Pines, LLC'
    WHEN 'dsr' THEN 'SCDP Del Sur Ranch, LLC'
    WHEN 'ads' THEN 'SCDP San Marcos, LLC'  -- Or whatever the actual name is
    -- Add all 14 mappings based on actual API results
    ELSE netsuite_subsidiary_name
END
WHERE practice_id IN ('sed', 'lhd', 'efd_i', 'dsr', 'ads'  /* ... */);
```

---

### **Step 3: Fetch Transaction Data for All Subsidiaries**

Use the NetSuite sync endpoint to fetch transactions for each subsidiary:

```python
# For each subsidiary ID found in Step 1:
for subsidiary_id in subsidiary_ids:
    response = await connector.fetch_journal_entries_via_suiteql(
        subsidiary_id=subsidiary_id,
        from_date='2024-01-01',  # Last year
        limit=None  # Get all
    )

    # Load to Snowflake bronze.netsuite_journal_entries
```

Or use the existing sync endpoint:
```bash
curl -X POST https://mcp.agentprovision.com/api/v1/netsuite/sync/trigger \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: silvercreek" \
  -H "Content-Type: application/json" \
  -d '{"entity_types": ["journalEntry", "invoice", "vendorBill"], "full_sync": true}'
```

---

### **Step 4: Verify All Practices Have NetSuite Data**

After loading:

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
        COUNT(*) as months,
        SUM(netsuite_revenue) as total_revenue
    FROM gold.practice_analytics_unified
    WHERE netsuite_revenue IS NOT NULL
    GROUP BY practice_id
    ORDER BY total_revenue DESC
""")

print("Practices with NetSuite financial data:")
for r in cursor.fetchall():
    print(f"  {r[0]:10s}: {r[1]:2d} months, ${r[2]:>12,.0f} revenue")

cursor.close()
conn.close()
EOF
```

Expected: Should show 10-14 practices (not just 3)

---

## 🔑 Key Files

**NetSuite Connector:**
- `mcp-server/src/connectors/netsuite.py` (OAuth connector)

**API Endpoints:**
- `/api/v1/netsuite/sync/trigger` - Trigger sync
- `/api/v1/netsuite/sync/status` - Check status

**Configuration:**
- `mcp-server/.env` - NetSuite credentials

**Snowflake Tables:**
- `bronze.netsuite_transactions_with_practice` (view with practice_id)
- `bronze_gold.netsuite_monthly_financials` (monthly aggregations)
- `gold.practice_analytics_unified` (unified view)

---

## 🎯 Expected Outcome

After completing NetSuite API integration:

**Automated Metrics from NetSuite (per practice/month):**
- ✅ Revenue
- ✅ Expenses
- ✅ Net Income
- ✅ Profit Margin %

**Combined with Operations Report:**
- ✅ Production (Doctor, Specialty, Hygiene)
- ✅ Collections & Collection Rates
- ✅ Patient Visits
- ✅ Case Acceptance
- ✅ New Patients
- ✅ Hygiene Efficiency

**Result:**
- **Complete automation** of Operations Report
- **No manual Excel entry** needed
- **Real-time updates** from NetSuite API
- **Cross-system validation** (NetSuite revenue vs Operations collections)

---

## ⏱️ Estimated Time

- Fetch subsidiaries via API: 15 min
- Update practice_master mappings: 15 min
- Sync all transaction data: 30-60 min (depending on volume)
- Verify integration: 15 min
- Deploy and test: 15 min

**Total: 1.5-2 hours**

---

## 🚨 Current Workaround

Until API integration is complete, the system works with:
- Operations Report Excel (85% complete, all 14 practices)
- NetSuite CSV data (3 practices: ADS, EFD I, SED)

**This provides immediate value while working toward full automation.**

---

## 📝 Recommended Approach

**Next Session:**
1. Call MCP API to fetch all subsidiaries
2. Update practice_master with actual subsidiary names
3. Trigger full NetSuite sync for all entity types
4. Verify data in unified view
5. Test dashboard shows financial data

**Tools:**
- Use production MCP server (already deployed with NetSuite connector)
- Credentials already configured
- Just need to trigger the syncs

---

**Status:** Ready to execute when you have 1-2 hours for NetSuite API work
**Blocker:** None - infrastructure complete, just need to run the syncs
**Value:** Complete Operations Report automation with real-time NetSuite data

---

**Document Created:** November 20, 2025
**Next Session:** NetSuite API sync execution
