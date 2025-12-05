# Demo Data Integrity Report

**Date:** November 25, 2025
**Purpose:** Pre-demo verification of production data consistency

---

## Executive Summary

Production data has **data integrity issues that need resolution**:
- **Operations data**: 12 practices - REAL data ✅
- **NetSuite CSV data**: 17 subsidiaries - REAL data ✅
- **Backend seed.ts**: Contains **14 FAKE subsidiary names** ❌
- **Mapping needed**: Operations practice codes ↔ NetSuite subsidiaries
- **Financial summary endpoint**: Has a code bug (avoid in demo)

---

## Production Endpoints Status

### Working Endpoints

| Endpoint | Tenant | Status | Notes |
|----------|--------|--------|-------|
| `/api/v1/operations/kpis/summary` | silvercreek | Working | 12 practices, $1.94M July production |
| `/api/v1/operations/kpis/monthly` | silvercreek | Working | All 12 practices with correct names |
| `/api/v1/analytics/unified/summary` | silvercreek | Working | 12 practices, LTM ~$18M |
| `/api/v1/analytics/unified/by-practice` | silvercreek | Working | All 12 practices ranked |
| Backend `/api/analytics/production/*` | - | Working | 304 cached responses |

### Problematic Endpoints

| Endpoint | Issue | Workaround |
|----------|-------|------------|
| `/api/v1/analytics/financial/summary` | Python error: "format requires a mapping" | Use unified or operations endpoints |
| Tenant `default` | "Tenant not found" | Always use `silvercreek` |

---

## Real NetSuite Subsidiaries (Source of Truth)

**These 17 subsidiaries from the CSV files are the ONLY real NetSuite data:**

| # | NetSuite Subsidiary | CSV Files |
|---|---------------------|-----------|
| 1 | SCDP San Marcos, LLC | 72, 88 |
| 2 | SCDP Del Sur Ranch, LLC | 165 |
| 3 | SCDP Torrey Pines, LLC | 263, 658 |
| 4 | SCDP Eastlake, LLC | 83, 381 |
| 5 | SCDP UTC, LLC | 951 |
| 6 | SCDP Coronado, LLC | 199 |
| 7 | SCDP Vista, LLC | 868 |
| 8 | SCDP Laguna Hills II, LLC | 355 |
| 9 | SCDP Torrey Highlands, LLC | 40 |
| 10 | SCDP Carlsbad, LLC | 942 |
| 11 | SCDP Otay Lakes, LLC | 599 |
| 12 | SCDP Laguna Hills, LLC | 232 |
| 13 | SCDP Kearny Mesa, LLC | 407 |
| 14 | SCDP Temecula, LLC | 248 |
| 15 | SCDP Temecula II, LLC | 557 |
| 16 | SCDP San Marcos II, LLC | 819 |
| 17 | Steve P. Theodosis Dental Corp | 218 |

---

## Operations Report Practices (12 practices)

**These practice codes and names come from real operations report data:**

| # | Code | Practice Name |
|---|------|---------------|
| 1 | `ads` | Advanced Dental Solutions |
| 2 | `dd` | Downtown Dental |
| 3 | `dsr` | Del Sur Dental |
| 4 | `eawd` | East Avenue Dental |
| 5 | `efd_i` | Encinitas Family Dental I |
| 6 | `efd_ii` | Encinitas Family Dental II |
| 7 | `ipd` | Imperial Point Dental |
| 8 | `lcd` | La Costa Dental |
| 9 | `lsd` | La Senda Dental |
| 10 | `rd` | Rancho Dental |
| 11 | `sed` | Scripps Eastlake Dental |
| 12 | `ucfd` | University City Family Dental |

---

## ⚠️ FAKE Data in Backend Database (LOW RISK for Demo)

### Production Database State (Checked Nov 24, 2025)

**Practices Table (45 rows - has duplicates!):**
- ADS (12 duplicates) - REAL ✅
- Eastlake (12 duplicates) - REAL ✅
- Torrey Pines (12 duplicates) - REAL ✅
- Silver Creek (9 duplicates) - **FAKE** ❌

**Locations Table (186 rows - has duplicates!):**

| Location | Subsidiary | Status |
|----------|------------|--------|
| ADS - San Marcos Office | SCDP San Marcos, LLC | ✅ REAL |
| ADS - San Marcos II Office | SCDP San Marcos II, LLC | ✅ REAL |
| Eastlake - Main Office | SCDP Eastlake, LLC | ✅ REAL |
| Torrey Pines - Torrey Pines Office | SCDP Torrey Pines, LLC | ✅ REAL |
| Torrey Pines - Torrey Highlands Office | SCDP Torrey Highlands, LLC | ✅ REAL |
| Silver Creek - Berkeley Office | SCDP Berkeley, LLC | ❌ FAKE |
| Silver Creek - Fremont Office | SCDP Fremont, LLC | ❌ FAKE |
| Silver Creek - Hayward Office | SCDP Hayward, LLC | ❌ FAKE |
| Silver Creek - Milpitas Office | SCDP Milpitas, LLC | ❌ FAKE |
| Silver Creek - Mountain View Office | SCDP Mountain View, LLC | ❌ FAKE |
| Silver Creek - Newark Office | SCDP Newark, LLC | ❌ FAKE |
| Silver Creek - Oakland Office | SCDP Oakland, LLC | ❌ FAKE |
| Silver Creek - Richmond Office | SCDP Richmond, LLC | ❌ FAKE |
| Silver Creek - San Jose HQ | Silver Creek | ❌ FAKE |
| Silver Creek - San Leandro Office | SCDP San Leandro, LLC | ❌ FAKE |
| Silver Creek - Santa Clara Office | SCDP Santa Clara, LLC | ❌ FAKE |
| Silver Creek - Silver Creek Office | SCDP Silver Creek, LLC | ❌ FAKE |
| Silver Creek - Sunnyvale Office | SCDP Sunnyvale, LLC | ❌ FAKE |
| Silver Creek - Union City Office | SCDP Union City, LLC | ❌ FAKE |

### Demo Impact Assessment

| Component | Uses Backend DB? | Risk |
|-----------|------------------|------|
| Operations KPIs | NO (Snowflake) | ✅ Safe |
| Unified Analytics | NO (Snowflake) | ✅ Safe |
| Executive Dashboard | NO (MCP→Snowflake) | ✅ Safe |
| Practice Dropdown | YES | ⚠️ May show fake "Silver Creek" |
| Admin Settings | YES | ⚠️ Shows fake locations |

### Recommendation for Demo

**DO NOT FIX before demo** - Risk of breaking production outweighs benefit
- Analytics dashboards use Snowflake data (correct 12 practices)
- Only backend admin pages show the fake data
- **Avoid**: Practice management, Admin settings pages during demo

### Source of Fake Data

**File:** `backend/src/database/seed.ts` (lines 130-145)

---

## Mapping: Operations ↔ NetSuite (NEEDS CONFIRMATION)

### High Confidence Mappings

| Ops Code | Practice Name | NetSuite Subsidiary | Rationale |
|----------|---------------|---------------------|-----------|
| `ads` | Advanced Dental Solutions | SCDP San Marcos, LLC | San Marcos location |
| `dsr` | Del Sur Dental | SCDP Del Sur Ranch, LLC | Name match |
| `sed` | Scripps Eastlake Dental | SCDP Eastlake, LLC | Name match |
| `ucfd` | University City Family Dental | SCDP UTC, LLC | UTC = University City |
| `lcd` | La Costa Dental | SCDP Carlsbad, LLC | La Costa is in Carlsbad |

### Needs Confirmation

| Ops Code | Practice Name | Possible NetSuite Match | Confidence |
|----------|---------------|-------------------------|------------|
| `dd` | Downtown Dental | SCDP Coronado, LLC? | Medium |
| `eawd` | East Avenue Dental | SCDP Vista, LLC? | Low |
| `efd_i` | Encinitas Family Dental I | SCDP Torrey Pines, LLC? | Medium |
| `efd_ii` | Encinitas Family Dental II | SCDP Laguna Hills II, LLC? | Low |
| `ipd` | Imperial Point Dental | SCDP Torrey Highlands, LLC? | Low |
| `lsd` | La Senda Dental | SCDP Otay Lakes, LLC? | Low |
| `rd` | Rancho Dental | **??? (no match found)** | ❌ |

### NetSuite Subsidiaries Not Mapped to Operations

| NetSuite Subsidiary | Notes |
|---------------------|-------|
| SCDP Laguna Hills, LLC | Separate from "II" |
| SCDP Kearny Mesa, LLC | Not in ops report |
| SCDP Temecula, LLC | Not in ops report |
| SCDP Temecula II, LLC | Not in ops report |
| SCDP San Marcos II, LLC | Second location? |
| Steve P. Theodosis Dental Corp | Parent entity? |

---

## Demo Recommendations

### ✅ SAFE to Show

1. **Operations KPIs page** - 12 real practices, correct names
2. **Executive Dashboard** - Analytics from Snowflake (real data)
3. **Unified Analytics** - Aggregated metrics work correctly
4. **Date range 2024-2025** - Has data coverage
5. **Use tenant `silvercreek`** for all API calls

### ⚠️ AVOID Showing

1. **Practice Management page** - Shows fake "Silver Creek" practice
2. **Admin Settings** - Shows 186 duplicate locations with fake subsidiaries
3. **Financial Summary endpoint** - Has Python code bug
4. **Tenant `default`** - Not configured, returns error
5. **NetSuite-specific financial breakdown** - Mapping incomplete

### Key Metrics to Highlight

| Metric | Value | Period |
|--------|-------|--------|
| Practice Count | 12 | - |
| Total Production | $1.94M | July 2025 |
| LTM Production | ~$18M | Rolling 12 months |
| Collection Rate | ~92% | Average |
| Total Visits | 1,900 | July 2025 |

---

## Post-Demo Action Plan

### Priority 1: Fix Fake Data in Backend

**Task:** Update `backend/src/database/seed.ts` to remove fake subsidiaries

**Steps:**
1. Remove all 14 fake "Silver Creek" subsidiaries (lines 130-145)
2. Replace with real NetSuite subsidiary mapping
3. Re-run database seed on production
4. Verify backend API returns correct subsidiary names

### Priority 2: Confirm Operations ↔ NetSuite Mapping

**Questions to resolve with client:**

| # | Question |
|---|----------|
| 1 | **Rancho Dental (`rd`)**: What is the NetSuite subsidiary name? |
| 2 | **Downtown Dental (`dd`)**: Is this SCDP Coronado, LLC? |
| 3 | **Encinitas Family Dental I (`efd_i`)**: Is this SCDP Torrey Pines, LLC? |
| 4 | **Encinitas Family Dental II (`efd_ii`)**: Is this SCDP Laguna Hills II, LLC? |
| 5 | **Imperial Point Dental (`ipd`)**: Is this SCDP Torrey Highlands, LLC? |
| 6 | **East Avenue Dental (`eawd`)**: Is this SCDP Vista, LLC? |
| 7 | **La Senda Dental (`lsd`)**: Is this SCDP Otay Lakes, LLC? |

### Priority 3: Explain Unmapped Subsidiaries

**Why are these NetSuite subsidiaries not in operations reports?**

| Subsidiary | Question |
|------------|----------|
| SCDP Laguna Hills, LLC | New practice? Separate from "II"? |
| SCDP Kearny Mesa, LLC | New acquisition? |
| SCDP Temecula, LLC | Different region? |
| SCDP Temecula II, LLC | Different region? |
| SCDP San Marcos II, LLC | Second ADS location? |
| Steve P. Theodosis Dental Corp | Parent/holding entity? |

### Priority 4: Update Code After Mapping Confirmed

**Files to update:**
- `backend/src/database/seed.ts` - Practice/subsidiary mapping
- `mcp-server/src/services/netsuite_csv_parser.py` - Subsidiary name normalization
- `docs/DEMO_DATA_INTEGRITY_REPORT.md` - Final confirmed mapping

---

## API Test Commands

```bash
# Set API key
export MCP_KEY="d876e6163089364d96a45a80ed576e99fc55b306133e258d9f861007e824b456"

# Operations Summary (WORKS)
curl -s "https://mcp.agentprovision.com/api/v1/operations/kpis/summary?start_date=2024-01-01&end_date=2025-12-31" \
  -H "Authorization: Bearer ${MCP_KEY}" \
  -H "X-Tenant-ID: silvercreek"

# Operations Monthly by Practice (WORKS)
curl -s "https://mcp.agentprovision.com/api/v1/operations/kpis/monthly?start_date=2025-07-01&end_date=2025-07-31" \
  -H "Authorization: Bearer ${MCP_KEY}" \
  -H "X-Tenant-ID: silvercreek"

# Unified Summary (WORKS)
curl -s "https://mcp.agentprovision.com/api/v1/analytics/unified/summary?start_date=2025-07-01&end_date=2025-07-31" \
  -H "Authorization: Bearer ${MCP_KEY}" \
  -H "X-Tenant-ID: silvercreek"

# Unified By Practice (WORKS)
curl -s "https://mcp.agentprovision.com/api/v1/analytics/unified/by-practice?start_date=2025-01-01&end_date=2025-12-31" \
  -H "Authorization: Bearer ${MCP_KEY}" \
  -H "X-Tenant-ID: silvercreek"
```

---

## Production Services Status

| Service | Status | Notes |
|---------|--------|-------|
| MCP Server | Healthy | https://mcp.agentprovision.com |
| Backend | Running | Port 3001 |
| Frontend | Running | https://dentalerp.agentprovision.com |
| PostgreSQL | Healthy | Port 5432 |
| Redis | Healthy | Port 6379 |

---

## Related Documentation

- `docs/archive/2025-11-22-analytics-fix/NETSUITE_SUBSIDIARY_MAPPING_CONFIRMATION.md` - Full mapping request
- `docs/archive/2025-11-22-analytics-fix/NETSUITE_OPERATIONS_MAPPING_COMPLETE.md` - Mapping table
- `docs/plans/2025-11-18-unified-analytics-consolidation.md` - Implementation plan

---

**Last Updated:** November 24, 2025
**Author:** Claude Code
**Status:** Data integrity issues identified - see Post-Demo Action Plan
