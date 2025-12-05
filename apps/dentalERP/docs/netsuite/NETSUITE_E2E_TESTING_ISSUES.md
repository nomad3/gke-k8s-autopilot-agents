# NetSuite End-to-End Testing Issues
**Date**: November 12, 2025
**Status**: 🔴 BLOCKED - Critical Issues Identified
**Impact**: Cannot test complete data flow from NetSuite → Snowflake → Backend → Frontend

---

## Executive Summary

The NetSuite integration has **multiple critical blocking issues** that prevent end-to-end testing of the complete data pipeline. While individual components work in isolation, the full flow from NetSuite → Snowflake → Backend API → Frontend is broken.

### Current Status by Component:

| Component | Status | Issue |
|-----------|--------|-------|
| NetSuite Connector | ⚠️ PARTIAL | Missing `import os` causing credential fallback to fail |
| NetSuite API Auth | ✅ WORKING | OAuth 1.0a TBA with HMAC-SHA256 functional |
| Data Extraction | 🔴 BLOCKED | User Event Script crashes on detail fetches |
| Bronze Layer | ⚠️ PARTIAL | 1,975 incomplete records (ID-only), 174 complete (CSV) |
| Silver Layer | ⚠️ PARTIAL | Only processes 174/2,149 records (CSV imports) |
| Gold Layer | ⚠️ LIMITED | Shows November 2025 only ($126K expenses) |
| Backend API | ✅ WORKING | `/analytics/financial/*` endpoints functional |
| Frontend | ✅ WORKING | Financial dashboard displays data correctly |

**Bottom Line**: System works end-to-end with CSV imports, but NetSuite API sync is fundamentally broken due to incomplete data extraction.

---

## Critical Issues

### 1. 🔴 CRITICAL: Missing Python Import in NetSuite Connector

**File**: `mcp-server/src/connectors/netsuite.py:61`

**Problem**: Code uses `os.environ.get()` but never imports `os` module

```python
# Line 61-66 in netsuite.py
env_account = os.environ.get('NETSUITE_ACCOUNT_ID')  # ❌ NameError: name 'os' is not defined
env_consumer_key = os.environ.get('NETSUITE_CONSUMER_KEY')
# ... etc
```

**Impact**:
- Connector crashes when trying to use environment variables
- Fallback to env credentials fails
- Integration router cannot initialize NetSuite connector

**Fix**:
```python
# Add to imports at top of file (after line 16)
import os
```

**Priority**: 🔴 CRITICAL - Must fix before any NetSuite testing

---

### 2. 🔴 CRITICAL: NetSuite REST API Returns Incomplete Data

**Root Cause**: NetSuite REST API list endpoints only return record IDs and links, not actual transaction data

**Documentation Reference**: `NETSUITE_API_DATA_ISSUE_EXPLAINED.md`

**Problem Flow**:
```
1. Call: GET /journalEntry?limit=100
   Returns: {"id": "7605", "links": [...]}  ← No financial data!

2. Need: {"id": "7605", "line": [{account, debit, credit}]}  ← Required for analytics

3. Must call: GET /journalEntry/7605?expandSubResources=true
   Returns: 400 ERROR - Script crash (see issue #3)
```

**Impact**:
- 1,975 Bronze records have NO financial information
- Only CSV imports (174 records) work correctly
- Cannot generate historical trends or multi-month analytics

**Evidence in Snowflake**:
```sql
-- Bronze: 2,149 total records
SELECT COUNT(*) FROM bronze.netsuite_journal_entries;  -- 2,149

-- Only 174 have usable data (line items)
SELECT COUNT(*) FROM bronze.netsuite_journal_entries
WHERE raw_data:line IS NOT NULL;  -- 174

-- Silver processes only records with line items
SELECT COUNT(*) FROM silver.stg_financials;  -- 479 rows (174 transactions × 2.75 lines avg)
```

---

### 3. 🔴 BLOCKING: NetSuite User Event Script Crashes on Detail Fetches

**NetSuite Script**: "TD UE VendorBillForm" (Deployment: `CUSTOMDEPLOY_VID_UE_JOURNAL_VBF`)

**Error**:
```
SSS_SEARCH_ERROR_OCCURRED: Record 'CUSTOMRECORD_VID_TEMPLATE' was not found
at VID_DistributionTemplateGateway.runQuery(BaseGateway.js:305)
```

**Problem**:
- Script runs on EVERY journal entry detail fetch
- Script searches for custom record that doesn't exist properly
- 100% of detail fetches fail with this error
- Tested with 395 different journal entry IDs - ALL failed

**Impact**:
- Cannot fetch transaction line items via API
- Blocks two-phase sync implementation
- Forces reliance on CSV exports

**Workarounds**:
1. **CSV Export** (Current): Works perfectly, bypasses scripts
2. **SuiteQL API** (Implemented): Bypasses User Event Scripts
3. **Disable Script** (Risky): Requires NetSuite admin approval
4. **Fix Script** (Best): Contact NetSuite support

**Code Reference**:
- `netsuite.py:628-656` - `fetch_journal_entry_detail()` method
- `netsuite.py:471-586` - `fetch_journal_entries_via_suiteql()` alternative

---

### 4. ⚠️ MEDIUM: Incomplete Test Coverage

**Missing Tests**:
- ❌ No automated E2E test for NetSuite → Snowflake → Frontend flow
- ❌ No test script for NetSuite sync status validation
- ❌ No test for SuiteQL fallback mechanism
- ❌ No integration test for financial analytics endpoints with NetSuite data

**Existing Tests** (PDF/PMS focused):
- ✅ `test-complete-system.sh` - Tests PDF ingestion pipeline
- ✅ `test-snowflake.sh` - Tests Snowflake connectivity
- ✅ `test-production.sh` - Tests production endpoints
- ❌ None specifically test NetSuite integration

**What's Needed**:
```bash
# Create: scripts/test-netsuite-e2e.sh
1. Test connection to NetSuite API
2. Trigger sync (both list and detail fetches)
3. Verify Bronze layer has complete data (with line items)
4. Verify Silver layer processes records correctly
5. Verify Gold layer shows financial metrics
6. Test backend /analytics/financial/summary endpoint
7. Verify frontend can display NetSuite data
```

---

### 5. ⚠️ MEDIUM: Snowflake Table Name Inconsistency

**File**: `mcp-server/src/services/snowflake_netsuite_loader.py`

**Problem**: Code expects table names that don't match Snowflake schema

**Mismatch Table**:
| Code Expects | Snowflake Has | Status |
|--------------|---------------|--------|
| `netsuite_journal_entries` | ✅ Matches | OK |
| `netsuite_accounts` | ✅ Matches | OK |
| `netsuite_invoices` | ✅ Matches | OK |
| `netsuite_payments` | `netsuite_customerPayment` | ⚠️ Mismatch |
| `netsuite_items` | `netsuite_inventoryItem` | ⚠️ Mismatch |

**Fix**: Update `_pluralize()` method in loader (documented in `NETSUITE_INTEGRATION_FINAL.md:217-230`)

---

## Data Flow Analysis

### What WORKS (CSV Import Path):

```
CSV Export from NetSuite
  ↓ (Transaction Detail Report)
  ↓ Complete data: line items, debits, credits
Bronze: 174 transactions with full data
  ↓ LATERAL FLATTEN(raw_data:line)
Silver: 479 rows (line-level detail)
  ↓ GROUP BY month, practice
Gold: 1 row (Nov 2025: $126,441 expenses)
  ↓ MCP /api/v1/analytics/financial/summary
Backend: /analytics/financial/summary
  ↓
Frontend: FinancialAnalyticsPage.tsx
  ↓
✅ Dashboard shows November 2025 metrics
```

### What's BROKEN (API Sync Path):

```
NetSuite REST API Sync
  ↓ GET /journalEntry?limit=100
  ↓ Returns: {id, links} ONLY ❌
Bronze: 1,975 records with NO financial data
  ↓ LATERAL FLATTEN(raw_data:line)
  ↓ line field = NULL ❌
Silver: 0 rows (all records skipped)
  ↓
Gold: 0 rows
  ↓
Backend: Empty data array
  ↓
Frontend: "No data available"
  ↓
❌ Dashboard cannot show API-synced data
```

**Why the Gap?**
1. List API call gets IDs only (by design)
2. Need detail calls to get line items
3. Detail calls blocked by User Event Script crash
4. Result: Bronze has 1,975 useless records

---

## Component-by-Component Status

### NetSuite Connector (`mcp-server/src/connectors/netsuite.py`)

**Status**: ⚠️ PARTIAL - Auth works, data extraction incomplete

**Working**:
- ✅ OAuth 1.0a TBA authentication (HMAC-SHA256)
- ✅ REST Record API v1 connection
- ✅ List endpoint calls (`GET /journalEntry`)
- ✅ Pagination (100 records per page)
- ✅ SuiteQL implementation (bypass scripts)

**Broken**:
- ❌ Missing `import os` (line 61)
- ❌ Detail fetches fail (User Event Script crash)
- ❌ Returns incomplete data from list endpoints
- ❌ Two-phase sync never completes phase 2

**Evidence**: See `NETSUITE_INTEGRATION_FINAL.md` lines 146-191

---

### Snowflake Bronze Layer

**Status**: ⚠️ PARTIAL - Contains data but mostly useless

**Schema**: `bronze.netsuite_journal_entries` (created via `snowflake-netsuite-setup.sql:14-23`)

**Contents**:
```sql
-- Total records
SELECT COUNT(*) FROM bronze.netsuite_journal_entries;
-- Result: 2,149

-- Records with complete data (line items)
SELECT COUNT(*)
FROM bronze.netsuite_journal_entries
WHERE raw_data:line IS NOT NULL;
-- Result: 174 (8.1% of total)

-- Records with ONLY IDs (useless)
SELECT COUNT(*)
FROM bronze.netsuite_journal_entries
WHERE raw_data:line IS NULL;
-- Result: 1,975 (91.9% of total) ❌
```

**Problem**: 91.9% of Bronze records lack the financial data needed for analytics

---

### Snowflake Silver Layer

**Status**: ⚠️ PARTIAL - Works correctly but limited by Bronze data

**Schema**: Uses dynamic table `silver.stg_financials` (see `NETSUITE-COMPLETE-DATA-FLOW-MAPPING.md`)

**SQL Logic**:
```sql
CREATE DYNAMIC TABLE silver.stg_financials AS
SELECT
    je.id AS journal_entry_id,
    line.value:account.name::STRING AS account_name,
    line.value:debit::DECIMAL(18,2) AS debit_amount,
    line.value:credit::DECIMAL(18,2) AS credit_amount
FROM bronze.netsuite_journal_entries je,
    LATERAL FLATTEN(input => je.raw_data:line) line  ← REQUIRES line field
WHERE je.raw_data:line IS NOT NULL;  ← Filters out 1,975 records
```

**Result**:
- Processes 174 Bronze records → 479 Silver rows
- Correctly skips 1,975 incomplete records
- **Working as designed** - not a Silver layer bug

---

### Snowflake Gold Layer

**Status**: ⚠️ LIMITED - Works but only for November 2025

**Schema**: `gold.daily_financial_metrics` (aggregated KPIs)

**Current Data**:
```sql
SELECT * FROM gold.daily_financial_metrics;
-- Result: 1 row
-- practice_name: Silver Creek
-- period: 2025-11
-- total_revenue: $0
-- total_expenses: $126,441.07
-- net_income: -$126,441.07
-- transaction_count: 171
```

**Limitations**:
- Only November 2025 (CSV import month)
- No revenue data (CSV only had expenses)
- No historical trends (need 6-12 months)
- Cannot compare months or calculate growth

**Fix**: Need more CSV exports or working API sync

---

### MCP Server API (`mcp-server/src/api/analytics.py`)

**Status**: ✅ WORKING - Endpoints functional

**Financial Analytics Endpoints**:
```python
GET /api/v1/analytics/financial/summary
    ?practice_name=Silver Creek
    &start_date=2025-11-01
    &end_date=2025-11-30

# Response (working with CSV data):
{
  "practice_name": "Silver Creek",
  "period": "2025-11",
  "total_revenue": 0,
  "total_expenses": 126441.07,
  "net_income": -126441.07,
  "profit_margin_pct": null
}
```

**Status**: All endpoints query Gold layer correctly and return data

---

### Backend API (`backend/src/routes/analytics.ts`)

**Status**: ✅ WORKING - Proxies to MCP correctly

**Relevant Endpoints**:
```typescript
// Line 337-356: Financial Summary
GET /api/analytics/financial/summary
  → Proxies to MCP Server
  → Returns Gold layer data

// Line 358-372: Financial by Practice
GET /api/analytics/financial/by-practice
  → Proxies to MCP Server
  → Returns practice comparison
```

**Test Result**: Both endpoints return data successfully (tested with CSV imports)

---

### Frontend (`frontend/src/pages/analytics/FinancialAnalyticsPage.tsx`)

**Status**: ✅ WORKING - Displays available data correctly

**Hooks Used**:
- `useFinancialSummary()` - Fetches from `/api/analytics/financial/summary`
- `usePracticeComparison()` - Fetches from `/api/analytics/financial/by-practice`

**Current Display**:
- ✅ Shows November 2025 metrics
- ✅ Formats currency correctly ($126,441)
- ✅ Displays KPI cards
- ✅ Renders practice comparison table
- ⚠️ Cannot show trends (only 1 month of data)

---

## Root Cause Summary

The NetSuite end-to-end testing failure has THREE root causes:

### 1. Code Bug (CRITICAL)
**Issue**: Missing `import os` in NetSuite connector
**File**: `mcp-server/src/connectors/netsuite.py:61`
**Fix**: Add one line: `import os`
**Time**: 30 seconds

### 2. NetSuite API Design (ARCHITECTURAL)
**Issue**: List endpoints don't return transaction details
**Workaround**: Two-phase sync (list → details)
**Blocker**: See root cause #3

### 3. NetSuite Custom Script (EXTERNAL)
**Issue**: User Event Script crashes on detail fetches
**Script**: TD UE VendorBillForm
**Fix Options**:
  - Use SuiteQL API (implemented but not tested)
  - Disable script (requires admin approval)
  - Fix script (requires NetSuite support)
  - Continue using CSV exports (working now)

---

## Recommended Actions

### Immediate (Next Session):

1. **Fix import bug** (5 min)
   ```bash
   # mcp-server/src/connectors/netsuite.py
   # Add after line 15:
   import os
   ```

2. **Test SuiteQL approach** (30 min)
   - Method already implemented: `fetch_journal_entries_via_suiteql()`
   - Bypasses User Event Scripts
   - Should return complete data with line items
   - Create test script: `scripts/test-netsuite-suiteql.sh`

3. **Create E2E test script** (1 hour)
   ```bash
   scripts/test-netsuite-e2e.sh
   - Test NetSuite connection
   - Trigger SuiteQL sync
   - Verify Bronze has complete data
   - Check Silver processing
   - Validate Gold metrics
   - Test backend API
   - Confirm frontend display
   ```

### Short Term (This Week):

4. **Export more CSV data** (15 min)
   - Get 6-12 months of Transaction Detail Report
   - Import to Bronze layer
   - Generate historical trends for dashboard

5. **Document SuiteQL limitations** (30 min)
   - Test what data SuiteQL can access
   - Compare to REST API results
   - Update integration docs

6. **Add monitoring** (1 hour)
   - Alert when Bronze sync returns incomplete data
   - Track percentage of records with line items
   - Log API vs SuiteQL vs CSV import sources

### Long Term (Next Sprint):

7. **Resolve NetSuite Script Issue**
   - Option A: Work with NetSuite support to fix script
   - Option B: Get approval to disable script
   - Option C: Use SuiteQL exclusively (if complete)

8. **Implement hybrid approach**
   - Use SuiteQL for journal entries
   - Use REST API for other record types
   - Fall back to CSV for missing data

9. **Build reconciliation dashboard**
   - Show NetSuite sync status
   - Compare API vs CSV data completeness
   - Alert on data quality issues

---

## Testing Checklist

### Pre-Deployment Testing:

- [ ] Fix `import os` bug in NetSuite connector
- [ ] Deploy MCP server with fix
- [ ] Test NetSuite connection (`POST /api/v1/netsuite/sync/test-connection`)
- [ ] Trigger SuiteQL sync
- [ ] Verify Bronze layer receives complete records:
  ```sql
  SELECT
      COUNT(*) as total_records,
      SUM(CASE WHEN raw_data:line IS NOT NULL THEN 1 ELSE 0 END) as complete_records,
      SUM(CASE WHEN raw_data:line IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as pct_complete
  FROM bronze.netsuite_journal_entries
  WHERE _ingestion_timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour';
  ```
- [ ] Verify Silver layer processes new records
- [ ] Verify Gold layer updates with new metrics
- [ ] Test backend API returns new data
- [ ] Verify frontend displays updated metrics
- [ ] Check for errors in MCP logs
- [ ] Validate data quality scores

### Success Criteria:

- ✅ NetSuite connector initializes without errors
- ✅ Bronze records have `line` field populated (not null)
- ✅ Silver layer processes >90% of new Bronze records
- ✅ Gold layer shows multiple months of data
- ✅ Backend API returns complete financial summary
- ✅ Frontend shows trends and month-over-month comparisons
- ✅ End-to-end latency <5 minutes (sync trigger to frontend update)

---

## Related Documentation

- `docs/NETSUITE_INTEGRATION_FINAL.md` - Complete integration guide
- `docs/NETSUITE_API_DATA_ISSUE_EXPLAINED.md` - Why 1,975 records are useless
- `docs/NETSUITE-COMPLETE-DATA-FLOW-MAPPING.md` - Field-level mapping
- `docs/NETSUITE-BACKUP-FIELD-MAPPING.md` - NetSuite field reference
- `snowflake-netsuite-setup.sql` - Bronze/Silver/Gold schema
- `mcp-server/src/connectors/netsuite.py` - NetSuite connector implementation
- `mcp-server/src/services/snowflake_netsuite_loader.py` - Sync orchestration

---

## Appendix: Quick Wins

### Fix #1: Import Bug (30 seconds)
```python
# File: mcp-server/src/connectors/netsuite.py
# After line 15, add:
import os
```

### Fix #2: Test SuiteQL (5 min)
```bash
# Create: scripts/test-netsuite-suiteql.sh
curl -X POST https://mcp.agentprovision.com/api/v1/netsuite/sync/trigger \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: default" \
  -d '{"use_suiteql": true, "record_types": ["journalEntry"]}'
```

### Fix #3: Import More CSV Data (15 min)
1. Export Transaction Detail Report (Jan-Nov 2025)
2. Run CSV import script
3. Trigger dbt refresh
4. View multi-month trends in dashboard

---

**Status**: Ready for immediate action
**Next Session Priority**: Fix import bug, test SuiteQL, create E2E test
**ETA to Working E2E Test**: 2-3 hours
