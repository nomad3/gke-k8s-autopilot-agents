# NetSuite Data Sync Gap - Investigation Findings

## 🔴 CRITICAL ISSUE

**Expected**: 7,326 journal entries (Eastlake Jan-Nov 2025)
**Actual**: 0-22 journal entries syncing from NetSuite API
**Gap**: 99.7% of data missing!

## 📊 Evidence

### CSV Data (Source of Truth from NetSuite UI Export)

**Eastlake CSV Analysis**:
- File: `backup/TransactionDetail_eastlake_mapped.csv`
- Total line items: 37,180 rows
- **Unique journal entries: 7,326** (by Document Number)
- Date range: 2025-01-31 to 2025-11-08
- Sample doc numbers: JE23, JE270, JE375, JE648, etc.

**Transaction Types in CSV**:
- All rows show Type: "Journal"
- Each row is a line item (debit/credit line)
- Multiple rows per journal entry

### NetSuite API Results

**Current Sync Results**:
- Status: "success"
- Records synced: 0-22 journal entries
- No errors reported
- Multiple subsidiaries queried (24 total)

**What the API is doing**:
```python
# Query:
SELECT t.id, t.tranid, t.trandate, t.subsidiary, status, memo
FROM transaction t
WHERE t.type = 'Journal'
  AND t.subsidiary = '{subsidiary_id}'
  AND t.trandate >= TO_DATE('2025-01-01', 'YYYY-MM-DD')
ORDER BY t.trandate DESC
```

## 🔍 Hypotheses

### Hypothesis 1: Subsidiary ID Mismatch
**Theory**: Eastlake data is under a different subsidiary ID than we're querying

**Evidence**:
- We query 24 subsidiaries
- Only get 0-22 total records across ALL
- CSV has 7,326 from one location (Eastlake)

**Test**: Check which subsidiary IDs actually have data

### Hypothesis 2: Date Filter Too Restrictive
**Theory**: Date filter `>= 2025-01-01` is excluding data

**Evidence**:
- CSV starts 2025-01-31
- But this shouldn't exclude Nov data
- Query orders by DESC so should get recent first

**Test**: Remove date filter entirely

### Hypothesis 3: CSV vs API Data Discrepancy
**Theory**: CSV was exported with different filters or manually created

**Evidence**:
- API returns almost nothing
- CSV has thousands of entries
- Possible the CSV includes deleted/draft entries

**Test**: Query NetSuite for total count without filters

### Hypothesis 4: Transaction Type Filtering
**Theory**: These aren't actually type='Journal' in NetSuite API

**Evidence**:
- CSV shows "Journal" but that's export format
- NetSuite internal type might be different
- Could be "GeneralJournal" or other variant

**Test**: Query transaction table without type filter

## 📝 What We Know Works

1. **NetSuite OAuth** - ✅ Authenticated successfully
2. **SuiteQL Syntax** - ✅ Queries execute without errors
3. **Auto-Batching** - ✅ Batches correctly when data exists
4. **Snowflake Insert** - ✅ MERGE works, prevents duplicates
5. **APScheduler** - ✅ Jobs registered and will run daily

## 🎯 What Needs Debugging

1. **Why only 22 out of 7,326 records?**
2. **What subsidiary IDs actually have the Eastlake data?**
3. **Are the date filters correct?**
4. **What's the total count in NetSuite API vs CSV?**

## 🔧 Next Steps for Debugging

### Step 1: Query NetSuite Without Filters
```sql
SELECT COUNT(*)
FROM transaction
WHERE type = 'Journal'
-- No date filter, no subsidiary filter
```

### Step 2: Check Which Subsidiaries Have Data
```sql
SELECT subsidiary, COUNT(*) as count
FROM transaction
WHERE type = 'Journal'
GROUP BY subsidiary
ORDER BY count DESC
```

### Step 3: Verify Transaction Types
```sql
SELECT type, COUNT(*) as count
FROM transaction
GROUP BY type
```

### Step 4: Compare Document Numbers
- Check if CSV doc numbers (JE270, etc.) exist in NetSuite API
- Query by tranId to find matching records

---

**Current State**: Automation works, but data sync is incomplete.
**Priority**: Debug and fix the 99.7% missing data issue.
