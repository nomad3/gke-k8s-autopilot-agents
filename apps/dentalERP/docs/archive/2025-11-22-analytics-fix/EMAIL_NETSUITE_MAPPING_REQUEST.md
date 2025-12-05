# Email Draft: NetSuite Subsidiary Mapping Confirmation

---

**Subject:** URGENT: Confirm NetSuite Subsidiary Mappings for Analytics Dashboard Integration

**To:** Accounting Team / Finance Manager

**Priority:** High

---

Hi Team,

We're completing the integration between NetSuite ERP and our Operations Report data for the unified analytics dashboard. To ensure accurate financial reporting and cross-validation, we need to confirm the correct mappings between NetSuite subsidiaries and our Operations practice codes.

## What We Have

We successfully imported **20 NetSuite Transaction Detail CSV files** that you extracted, representing **17 unique subsidiaries** with comprehensive financial transaction data (Jan-Nov 2025).

## What We Need

**Please complete this mapping table by filling in the NetSuite subsidiary names for each Operations practice:**

| Operations Code | Operations Practice Name | NetSuite Subsidiary LLC Name | CSV File(s) |
|-----------------|-------------------------|------------------------------|-------------|
| **sed** | Scripps Eastlake Dental | ✅ SCDP Eastlake, LLC | 83, 381 |
| **efd_i** | Encinitas Family Dental I | ✅ SCDP Torrey Pines, LLC | 263, 658 |
| **dsr** | Del Sur Dental | ✅ SCDP Del Sur Ranch, LLC | 165 |
| **ads** | Advanced Dental Solutions | ✅ SCDP San Marcos, LLC + SCDP San Marcos II, LLC | 72, 88, 819 |
| **ucfd** | University City Family Dental | ✅ SCDP UTC, LLC | 951 |
| **rd** | Rancho Dental | ✅ SCDP ??? (matches revenue ~$85M) | ??? |
| **dd** | Downtown Dental | SCDP Coronado, LLC ??? | 199 |
| **eawd** | East Avenue Dental | SCDP Vista, LLC ??? | 868 |
| **efd_ii** | Encinitas Family Dental II | SCDP Laguna Hills II, LLC ??? | 355 |
| **ipd** | Imperial Point Dental | SCDP Torrey Highlands, LLC ??? | 40 |
| **lcd** | La Costa Dental | SCDP Carlsbad, LLC ??? | 942 |
| **lsd** | La Senda Dental | SCDP Otay Lakes, LLC ??? | 599 |

**Specifically need confirmation on:**

1. **Rancho Dental (rd)** - Which NetSuite subsidiary is this? (Has ~$85M revenue, ~$72M operations production)

2. **Downtown Dental (dd)** - Is this SCDP Coronado, LLC? ($0.2M operations production)

3. **East Avenue Dental (eawd)** - Is this SCDP Vista, LLC? ($0.4M operations production)

4. **Encinitas Family Dental II (efd_ii)** - Is this SCDP Laguna Hills II, LLC? ($2.5M operations production)

5. **Imperial Point Dental (ipd)** - Is this SCDP Torrey Highlands, LLC? ($7.7M operations production)

6. **La Costa Dental (lcd)** - Is this SCDP Carlsbad, LLC? ($1.8M operations production)

7. **La Senda Dental (lsd)** - Is this SCDP Otay Lakes, LLC? ($1.7M operations production)

## Additional NetSuite Subsidiaries

We also found these NetSuite subsidiaries in the CSV files that **don't appear** in the Operations Report:
- SCDP Laguna Hills, LLC (232.csv) - $3.0M revenue
- SCDP Temecula, LLC (248.csv) - $2.7M revenue
- SCDP Temecula II, LLC (557.csv) - $0.6M revenue
- SCDP Kearny Mesa, LLC (407.csv) - $1.4M revenue
- Steve P. Theodosis Dental Corporation, PC (218.csv) - $20.9M revenue

**Are these:**
- Newer practices not yet in Operations Report?
- Different entities that should be tracked separately?
- Acquisitions or planned locations?

## Why This is Important

1. **Accuracy:** Dashboard will show unified Operations + NetSuite data for each practice
2. **Validation:** Cross-check manual Operations Report vs ERP financials
3. **Reconciliation:** Identify variances and data quality issues
4. **Completeness:** Ensure no practices are missing from either system

## Example of What We're Building

Once mapped correctly, dashboard will show:

```
Practice: Encinitas Family Dental I
  Operations Production: $63.2M  (from Excel Operations Report)
  NetSuite Revenue:      $145.2M (from ERP API)
  Variance:              $82.0M  (for investigation)
```

## Timeline

**Need by:** Friday, November 22, 2025
**Impact:** Blocks completion of unified analytics dashboard

## How to Respond

Please reply with the completed mapping table, or schedule a 15-minute call to go through the subsidiaries together.

Thank you!

---

**Technical Details (for reference):**
- NetSuite Account: 7048582
- Data Period: January 2025 - November 2025
- Total Transactions: 37,896 records across all entities
- Current Match Rate: 6 out of 12 practices (50%)
- Target: 12 out of 12 practices (100%)
