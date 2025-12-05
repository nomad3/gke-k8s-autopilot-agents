# NetSuite Subsidiary to Operations Practice Mapping - Confirmation Needed

**To:** Accounting Team
**From:** Development Team
**Date:** November 20, 2025
**Subject:** Confirm NetSuite Subsidiary Mappings for Unified Analytics Dashboard

---

## Background

We're integrating NetSuite ERP financial data with our Operations Report data in the unified analytics dashboard. We have **20 NetSuite Transaction Detail CSV files** representing **17 unique subsidiaries**, and **12 practices in the Operations Report**.

We need to confirm the correct mappings between NetSuite subsidiary names and Operations Report practice codes to ensure accurate cross-validation and financial reporting.

---

## ✅ CONFIRMED MAPPINGS (6 practices with matching data)

| NetSuite Subsidiary | Operations Code | Practice Name | Status |
|---------------------|-----------------|---------------|---------|
| SCDP San Marcos, LLC | ads | Advanced Dental Solutions | ✅ Confirmed |
| SCDP Del Sur Ranch, LLC | dsr | Del Sur Dental | ✅ Confirmed |
| SCDP Torrey Pines, LLC | efd_i | Encinitas Family Dental I | ✅ Confirmed |
| SCDP Eastlake, LLC | sed | Scripps Eastlake Dental | ✅ Confirmed |
| SCDP UTC, LLC | ucfd | University City Family Dental | ✅ Confirmed |
| SCDP Rancho ??? | rd | Rancho Dental | ✅ Confirmed (need exact NetSuite name) |

---

## ❓ NEED CONFIRMATION - Operations Practices Missing NetSuite Mapping

The following 6 practices appear in the Operations Report but we haven't identified their NetSuite subsidiaries yet:

| Operations Code | Full Practice Name | Best Guess NetSuite Subsidiary | CSV File |
|-----------------|-------------------|--------------------------------|----------|
| **dd** | Downtown Dental | SCDP Coronado, LLC? | TransactionDetail-199.csv |
| **eawd** | East Avenue Dental | ??? | Not found in CSV files |
| **efd_ii** | Encinitas Family Dental II | SCDP Laguna Hills II, LLC? | TransactionDetail-355.csv |
| **ipd** | Imperial Point Dental | ??? | Not found in CSV files |
| **lcd** | La Costa Dental | ??? | Not found in CSV files |
| **lsd** | La Senda Dental | ??? | Not found in CSV files |

**Questions:**
1. Is "SCDP Coronado, LLC" actually Downtown Dental (dd)?
2. Is "SCDP Laguna Hills II, LLC" actually Encinitas Family Dental II (efd_ii)?
3. Do East Avenue (eawd), Imperial Point (ipd), La Costa (lcd), and La Senda (lsd) have NetSuite subsidiaries? If so, what are their exact LLC names?

---

## ❓ NEED CONFIRMATION - NetSuite Subsidiaries Missing Operations Mapping

The following 11 NetSuite subsidiaries have financial data but no Operations Report data:

| NetSuite Subsidiary | Revenue | Our Guess | CSV Files |
|---------------------|---------|-----------|-----------|
| **SCDP Laguna Hills, LLC** | $3.0M | lhd? | TransactionDetail-232.csv |
| **SCDP Laguna Hills II, LLC** | - | efd_ii? OR lcd? | TransactionDetail-355.csv |
| **SCDP Torrey Highlands, LLC** | $1.9M | ipd? | TransactionDetail-40.csv |
| **SCDP Coronado, LLC** | - | dd? | TransactionDetail-199.csv |
| **SCDP Temecula, LLC** | $2.7M | - | TransactionDetail-248.csv |
| **SCDP Temecula II, LLC** | $0.6M | - | TransactionDetail557.csv |
| **SCDP Kearny Mesa, LLC** | $1.4M | - | TransactionDetail-407.csv |
| **SCDP Vista, LLC** | $2.1M | eawd? | TransactionDetail-868.csv |
| **SCDP Carlsbad, LLC** | $2.2M | lcd? | TransactionDetail-942.csv |
| **SCDP Otay Lakes, LLC** | $1.5M | lsd? | TransactionDetail599.csv |
| **SCDP San Marcos II, LLC** | - | ads (2nd location)? | TransactionDetail819.csv |
| **Steve P. Theodosis Dental Corporation, PC** | $20.9M | - | TransactionDetail-218.csv |

**Questions:**
1. Which Operations practice codes correspond to these NetSuite subsidiaries?
2. Are Temecula, Temecula II, Kearny Mesa, Vista, Carlsbad, Otay Lakes, and Torrey Highlands newer practices not yet in Operations Report?
3. Is Theodosis Dental a separate entity not tracked in Operations Report?

---

## 📋 COMPLETE LIST - All CSV Files We Have

| File | Subsidiary | Transactions |
|------|------------|--------------|
| TransactionDetail-40.csv | SCDP Torrey Highlands, LLC | ~1,100 |
| TransactionDetail-83.csv | SCDP Eastlake, LLC | ~800 |
| TransactionDetail-165.csv | SCDP Del Sur Ranch, LLC | 1,776 |
| TransactionDetail-199.csv | SCDP Coronado, LLC | ~900 |
| TransactionDetail-218.csv | Steve P. Theodosis Dental Corporation, PC | ~600 |
| TransactionDetail-232.csv | SCDP Laguna Hills, LLC | ~1,200 |
| TransactionDetail-248.csv | SCDP Temecula, LLC | ~1,100 |
| TransactionDetail-263.csv | SCDP Torrey Pines, LLC | ~1,000 |
| TransactionDetail-355.csv | SCDP Laguna Hills II, LLC | ~800 |
| TransactionDetail-381.csv | SCDP Eastlake, LLC | ~900 |
| TransactionDetail-407.csv | SCDP Kearny Mesa, LLC | ~1,000 |
| TransactionDetail-658.csv | SCDP Torrey Pines, LLC | ~850 |
| TransactionDetail-868.csv | SCDP Vista, LLC | ~1,000 |
| TransactionDetail-942.csv | SCDP Carlsbad, LLC | ~950 |
| TransactionDetail-951.csv | SCDP UTC, LLC | ~900 |
| TransactionDetail72.csv | SCDP San Marcos, LLC | ~800 |
| TransactionDetail88.csv | SCDP San Marcos, LLC | ~850 |
| TransactionDetail557.csv | SCDP Temecula II, LLC | ~700 |
| TransactionDetail599.csv | SCDP Otay Lakes, LLC | ~800 |
| TransactionDetail819.csv | SCDP San Marcos II, LLC | ~750 |

---

## 🎯 REQUESTED ACTION

Please provide the complete mapping table:

| NetSuite Subsidiary LLC Name | Operations Practice Code | Operations Full Name |
|------------------------------|--------------------------|----------------------|
| SCDP Eastlake, LLC | sed | Scripps Eastlake Dental |
| SCDP Torrey Pines, LLC | efd_i | Encinitas Family Dental I |
| SCDP Del Sur Ranch, LLC | dsr | Del Sur Dental |
| SCDP San Marcos, LLC | ads | Advanced Dental Solutions |
| SCDP San Marcos II, LLC | ads | Advanced Dental Solutions |
| SCDP UTC, LLC | ucfd | University City Family Dental |
| SCDP Coronado, LLC | **???** | **???** |
| SCDP Laguna Hills, LLC | **???** | **???** |
| SCDP Laguna Hills II, LLC | **???** | **???** |
| SCDP Torrey Highlands, LLC | **???** | **???** |
| SCDP Kearny Mesa, LLC | **???** | **???** |
| SCDP Vista, LLC | **???** | **???** |
| SCDP Carlsbad, LLC | **???** | **???** |
| SCDP Temecula, LLC | **???** | **???** |
| SCDP Temecula II, LLC | **???** | **???** |
| SCDP Otay Lakes, LLC | **???** | **???** |
| Steve P. Theodosis Dental Corporation, PC | **???** | **???** |

Please fill in the "???" entries with the correct Operations practice codes and full names.

---

## Why This Matters

1. **Data Accuracy:** Ensures financial metrics match between NetSuite and Operations
2. **Cross-Validation:** Allows us to compare ERP data vs manual reporting
3. **Dashboard Accuracy:** Users will see complete, validated financial data
4. **Audit Trail:** Proper mappings enable reconciliation and variance analysis

---

## Timeline

**Urgent:** Need this by end of week to complete the unified analytics dashboard integration.

Once we have the mappings, we'll update the system configuration and ensure all 12 Operations practices show matching NetSuite financial data.

Thank you!
