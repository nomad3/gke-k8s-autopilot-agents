# LIKELY ROOT CAUSE #2: Transaction Type Filter

## 🔴 The Issue

**Location**: `mcp-server/src/connectors/netsuite.py:496`

**Current Code**:
```python
where_clauses = ["t.type = 'Journal'"]
```

**Current Query**:
```sql
SELECT t.id, t.tranid, t.trandate, t.subsidiary, status, memo
FROM transaction t
WHERE t.type = 'Journal' AND t.subsidiary = 'X'
```

**Result**: 0 records from NetSuite

## 🔍 The Problem

**CSV Export shows**: Type = "Journal" (7,326 entries)
**SuiteQL field might use**: Different value or not exist

**Hypothesis**: The `type` field in NetSuite's transaction table doesn't use 'Journal' as the value, so our filter excludes ALL data.

## 🧪 Test to Confirm

Query WITHOUT type filter:

```sql
SELECT COUNT(*), type
FROM transaction t
WHERE t.subsidiary = '6'
GROUP BY type
```

If this returns thousands of records, then `type='Journal'` is filtering incorrectly.

## 🔧 The Fix

**Option 1**: Remove type filter entirely (sync ALL transaction types)
```python
# Instead of: where_clauses = ["t.type = 'Journal'"]
# Just use: where_clauses = []
```

**Option 2**: Find correct type value
- Query NetSuite to see what type values exist
- Update filter to match

**Option 3**: Use recordType field instead
- Transaction table might have `recordType` instead of `type`

## 📊 Session Progress

**Fixed**:
1. ✅ 4 SuiteQL syntax issues
2. ✅ Date filter bug (was using TODAY)

**Found But Not Yet Fixed**:
3. ⚠️ Transaction type filter (likely blocking ALL data)

## 🎯 Next Session Action

1. Test query WITHOUT `t.type = 'Journal'` filter
2. If returns data → Remove type filter or find correct value
3. Then re-test full sync
4. Should get 7,326+ records

---

**Summary**: Fixing date filter revealed the type filter issue.
**Status**: Code changes documented, ready to test/fix next session.
