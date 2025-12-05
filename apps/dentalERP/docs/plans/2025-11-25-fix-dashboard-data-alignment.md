# Plan: Fix Dashboard Data Alignment

**Date:** November 25, 2025
**Status:** Ready for Implementation
**Priority:** High (affects demo/production)

---

## Problem Summary

The Practice Analytics Overview dashboard shows incorrect or missing data:

| Card/Column | Current Value | Issue |
|-------------|---------------|-------|
| Net Income | N/A | NetSuite data not joined |
| Revenue (NetSuite) | N/A | NetSuite data not joined |
| Encinitas FD I PPV | $5,650 | Should be ~$1,100 |
| Encinitas FD II Collection % | 154.5% | Over 100% is invalid |
| Downtown Dental Collection % | 55.6% | Suspiciously low |

---

## Root Causes

### 1. NetSuite Data Missing from Gold Layer
- `gold.practice_analytics_unified` has NULL values for `netsuite_revenue`, `netsuite_net_income`
- NetSuite CSV files exist in `backup/` but not uploaded to Snowflake Bronze layer
- Need to re-upload all 20 TransactionDetail CSVs

### 2. Operations Data Quality Issues
- **Encinitas Family Dental I**: Source data shows 1-6 visits/month instead of ~100+
  - This causes PPV to be inflated ($50K production / 1 visit = $50K PPV)
  - The AVG_PPV of $5,650 is average of these inflated monthly values
- **Encinitas Family Dental II**: Collections > Production for some months
- These are source data issues in the uploaded Operations Reports

### 3. PPV Calculation Logic
- Current: Simple average of monthly PPV values
- Should be: Weighted average (Total Production / Total Visits)

---

## Implementation Tasks

### Phase 1: Upload NetSuite CSV Data (30 min)

**Task 1.1: Bulk upload NetSuite TransactionDetail CSVs**
```bash
# Use the bulk upload endpoint to process all CSVs
curl -X POST https://mcp.agentprovision.com/api/v1/netsuite/upload/bulk-transactions \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: silvercreek"
```

**Task 1.2: Verify NetSuite data in Bronze layer**
```bash
curl -s 'https://mcp.agentprovision.com/api/v1/analytics/unified/monthly?category=financial&limit=5' \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: silvercreek"
```

**Files involved:**
- `mcp-server/src/api/netsuite_upload.py` - Upload endpoint
- `mcp-server/src/services/netsuite_csv_parser.py` - CSV parser
- `backup/TransactionDetail-*.csv` - 20 source files

---

### Phase 2: Create Operations ↔ NetSuite Mapping (15 min)

**Problem:** Operations practices (ads, dsr, efd_i) need to be mapped to NetSuite subsidiaries (SCDP San Marcos, LLC, etc.)

**Task 2.1: Create/update mapping table in Snowflake**

Based on docs/DEMO_DATA_INTEGRITY_REPORT.md, high-confidence mappings:

| Ops Code | Practice Name | NetSuite Subsidiary |
|----------|---------------|---------------------|
| ads | Advanced Dental Solutions | SCDP San Marcos, LLC |
| dsr | Del Sur Dental | SCDP Del Sur Ranch, LLC |
| sed | Scripps Eastlake Dental | SCDP Eastlake, LLC |
| ucfd | University City Family Dental | SCDP UTC, LLC |
| lcd | La Costa Dental | SCDP Carlsbad, LLC |

**Task 2.2: Update gold.practice_analytics_unified dynamic table**
- Ensure JOIN between operations and netsuite data uses mapping table
- Currently the JOIN may be failing due to mismatched practice IDs

---

### Phase 3: Fix PPV Calculation (20 min)

**Task 3.1: Update the by-practice aggregation to use weighted average**

Current (incorrect):
```sql
AVG(ppv_overall) AS avg_ppv
```

Should be:
```sql
SUM(total_production) / NULLIF(SUM(visits_total), 0) AS avg_ppv
```

**Files to modify:**
- `mcp-server/src/api/analytics_unified.py` - Line 168

---

### Phase 4: Flag/Fix Bad Source Data (15 min)

**Task 4.1: Add data quality validation**

Add constraints/flags for:
- Visits < 10 per month → Flag as "DATA_QUALITY_WARNING"
- Collection rate > 120% → Flag as suspicious
- Collection rate < 50% → Flag as suspicious
- PPV > $3,000 → Flag as outlier

**Task 4.2: Review/re-upload Encinitas FD I Operations data**

The source Excel files have incorrect visit counts:
- 2025-06: 1 visit (should be ~100)
- 2025-05: 2 visits (should be ~100)
- 2025-04: 1 visit (should be ~100)

Either:
- Get corrected source files from client
- Manually correct in Snowflake Bronze layer

---

## Verification Steps

After each phase, verify:

1. **NetSuite cards show values:**
   ```bash
   curl 'https://mcp.agentprovision.com/api/v1/analytics/unified/summary' ...
   # Should show total_revenue and total_net_income != null
   ```

2. **PPV values are reasonable:**
   - All practices should have PPV between $200-$2,000
   - Encinitas FD I should show ~$1,100 PPV

3. **Collection rates are valid:**
   - All should be between 50%-120%
   - Encinitas FD II should be ~100%

---

## Rollback Plan

If issues occur:
1. NetSuite data: DELETE FROM bronze.netsuite_transactions WHERE uploaded_at > 'timestamp'
2. Operations data: Has MERGE/upsert, can re-upload original files
3. Gold layer: ALTER DYNAMIC TABLE gold.practice_analytics_unified REFRESH

---

## Dependencies

- SSH access to production VM ✅ (restored after reset)
- NetSuite CSV files in backup/ ✅ (20 files available)
- MCP Server API key ✅

---

## Timeline

| Phase | Task | Duration |
|-------|------|----------|
| 1 | Upload NetSuite CSVs | 30 min |
| 2 | Create practice mapping | 15 min |
| 3 | Fix PPV calculation | 20 min |
| 4 | Data quality fixes | 15 min |
| - | **Total** | **~80 min** |

---

## Notes

- Dynamic tables auto-refresh within 1 hour after Bronze data changes
- Force immediate refresh: `ALTER DYNAMIC TABLE ... REFRESH`
- Production backup exists at `/tmp/dental_erp_backup_20251125_025707.sql`
