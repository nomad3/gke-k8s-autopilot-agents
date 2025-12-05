# Root Cause Analysis - 99.7% Data Missing

## 🎯 ROOT CAUSE IDENTIFIED

### The Bug
**SuiteQL Query Filter**: `WHERE t.trandate >= TO_DATE('2025-11-13', 'YYYY-MM-DD')`

**Impact**: Excludes ALL historical data (CSV covers Jan 31 - Nov 8, 2025)

**Result**: 0 records synced when 7,326 expected

## 📍 Source Location

**File**: `mcp-server/src/services/snowflake_netsuite_loader.py`
**Lines**: 146-155

```python
# Use explicit from_date if provided, otherwise use incremental logic
if from_date:
    filters["from_date"] = from_date
elif incremental:
    last_sync = await self._get_last_sync_time(record_type, sub_id)
    if last_sync:
        filters["from_date"] = last_sync.isoformat()[:10]  # YYYY-MM-DD format
```

**Problem**: When calling without `from_date` parameter and `incremental=True` (default), it uses `last_sync_time` from database, which is TODAY (2025-11-13).

## 🔍 Data Flow Trace

```
1. API Call: POST /api/v1/netsuite/sync/trigger
   - No from_date parameter
   - incremental defaults to True

2. Orchestrator → sync_all_record_types(incremental=True)

3. Loader checks: if incremental:
   - Gets last_sync_time from database
   - Returns: 2025-11-13 (TODAY)

4. Sets filter: from_date = '2025-11-13'

5. SuiteQL query: WHERE t.trandate >= '2025-11-13'

6. NetSuite returns: 0 records (no journal entries from today)

7. Result: 0 records synced
```

## ✅ Evidence

**Layer 1 - Subsidiaries Queried**: 24 subsidiaries (IDs 1-27)
**Layer 2 - NetSuite Response**: 0 records for EVERY subsidiary
**Layer 3 - SuiteQL Query**: Date filter = TODAY (2025-11-13)
**Layer 4 - CSV Data**: 7,326 entries from Jan 31 - Nov 8, 2025

## 🔧 The Fix

**For Full Sync (get ALL historical data)**:
- When `full_sync=True`, do NOT set any date filter
- Or set `from_date = None` to remove restriction
- This allows fetching ALL records regardless of date

**For Incremental Sync (only new data)**:
- Keep using last_sync_time
- But initialize it to a reasonable past date (e.g., 1 year ago)
- Not TODAY

## 📊 Expected Behavior After Fix

**Before**: >= 2025-11-13 → 0 records
**After**: No date filter → 7,326 records

Then subsequent incremental syncs will use actual last_sync_time.

---

**Root cause found through systematic debugging.**
**Next: Implement fix and test.**
