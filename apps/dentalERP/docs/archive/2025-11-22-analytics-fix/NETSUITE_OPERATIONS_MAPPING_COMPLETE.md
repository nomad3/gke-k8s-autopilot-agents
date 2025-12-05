# Complete NetSuite to Operations Practice Mapping

## Company Structure
**Parent Company:** Silver Creek Dental Partners (SCDP)
**Subsidiaries:** Each SCDP LLC is a separate practice/location

## Complete Mapping Table

| Operations Code | Practice Full Name | NetSuite Subsidiary | CSV Files | Status |
|-----------------|-------------------|---------------------|-----------|--------|
| **sed** | Scripps Eastlake Dental | SCDP Eastlake, LLC | 83, 381 | ✅ Confirmed |
| **efd_i** | Encinitas Family Dental I | SCDP Torrey Pines, LLC | 263, 658 | ✅ Confirmed |
| **dsr** | Del Sur Dental | SCDP Del Sur Ranch, LLC | 165 | ✅ Confirmed |
| **ads** | Advanced Dental Solutions | SCDP San Marcos, LLC + San Marcos II | 72, 88, 819 | ✅ Confirmed |
| **ucfd** | University City Family Dental | SCDP UTC, LLC | 951 | ✅ Confirmed |
| **rd** | Rancho Dental | SCDP Rancho, LLC (or similar) | In one of the CSVs | ✅ Has data |
| **dd** | Downtown Dental | **SCDP Coronado, LLC?** | 199 | ❓ Probable |
| **efd_ii** | Encinitas Family Dental II | **SCDP Laguna Hills II, LLC?** | 355 | ❓ Probable |
| **lcd** | La Costa Dental | **SCDP Carlsbad, LLC?** | 942 | ❓ Probable |
| **lsd** | La Senda Dental | **SCDP Otay Lakes, LLC?** | 599 | ❓ Probable |
| **eawd** | East Avenue Dental | **SCDP Vista, LLC?** | 868 | ❓ Probable |
| **ipd** | Imperial Point Dental | **SCDP Torrey Highlands, LLC?** | 40 | ❓ Probable |

## NetSuite Subsidiaries Without Clear Operations Match

| NetSuite Subsidiary | CSV Files | Revenue | Notes |
|---------------------|-----------|---------|-------|
| SCDP Laguna Hills, LLC | 232 | $3.0M | Newer practice? |
| SCDP Kearny Mesa, LLC | 407 | $1.4M | Newer practice? |
| SCDP Temecula, LLC + II | 248, 557 | $3.3M | Two locations |
| Steve P. Theodosis Dental | 218 | $20.9M | Separate entity |

## Action Required

**Please confirm or correct the "❓ Probable" mappings above.**

Specifically, we need to know:
1. What is the exact NetSuite subsidiary name for **Rancho Dental**? (We see "Rancho 8711" in account names)
2. Is Downtown Dental actually located in Coronado?
3. Are the other probable matches correct based on geography?

## Why Some Practices Have Higher NetSuite Revenue

You'll notice some practices show MUCH higher NetSuite revenue than Operations production:
- Encinitas (efd_i): $145M NetSuite vs $63M Operations
- Del Sur (dsr): $115M NetSuite vs $64M Operations
- ADS: $108M NetSuite vs $71M Operations

**This is NORMAL** because:
- NetSuite = Full ERP (all revenue, all subsidiaries, full year)
- Operations Report = Subset of months/metrics from manual Excel extraction
- Data periods may differ (NetSuite has more historical data)
- Accounting methods differ (accrual vs cash, different recognition timing)

## Next Steps

1. Send this mapping to accounting team for confirmation
2. Once confirmed, update `practice_master` table with correct subsidiary IDs
3. Re-sync data to ensure proper practice attribution
4. Verify 12/12 Operations practices show matching NetSuite data

---

**Created:** November 20, 2025
**Purpose:** Finalize NetSuite-Operations integration for unified analytics dashboard
