# Operations KPI Dashboard - Data Source Mapping

**Date:** November 17, 2025
**Status:** Implementation in Progress

---

## 🎯 Client KPI Requirements

Based on Brad Starkweather's preliminary list (Nov 16, 2025):

1. Production & Collections (8 metrics)
2. Patient Visits (5 metrics)
3. Production Per Visit (6 metrics)
4. Case Acceptance (6 metrics per provider)
5. New Patient Acquisition (2 metrics)
6. Hygiene Efficiency (5 metrics)
7. Provider Gross Production (detailed per provider)

---

## 📊 Data Source Strategy: Hybrid Approach

### Philosophy
**Maximize NetSuite Integration + Fill Gaps with CSV Upload**

✅ Use NetSuite/PMS API when available (real-time, automated)
⚠️ Fall back to CSV upload when integration not yet built
🔄 Migrate from CSV to API integration over time

---

## 🗺️ KPI Data Source Mapping

### 1. PRODUCTION & COLLECTIONS (8 Metrics)

| Metric | Primary Source | Secondary Source | Status |
|--------|---------------|------------------|--------|
| **Gross Production - Doctor** | ✅ **NetSuite** (Transaction Detail) | CSV Upload | ✅ Available |
| **Gross Production - Specialty** | ✅ **NetSuite** (Transaction Detail) | CSV Upload | ✅ Available |
| **Gross Production - Hygiene** | ✅ **NetSuite** (Transaction Detail) | CSV Upload | ✅ Available |
| **Net Production** | ✅ **NetSuite** (Gross - Adjustments) | CSV Upload | ✅ Available |
| **Collections** | ✅ **NetSuite** (Invoice Payments) | CSV Upload | ✅ Available |
| **Collection Rate %** | ✅ **Calculated** (Collections / Net Production) | - | ✅ Auto-calculated |
| **LTM Production** | ✅ **Calculated** (12-month rolling sum) | - | ✅ Auto-calculated |
| **LTM Collections** | ✅ **Calculated** (12-month rolling sum) | - | ✅ Auto-calculated |

**Integration Details:**
```sql
-- NetSuite provides this data already!
SELECT
    subsidiary_name AS practice_location,
    DATE_TRUNC('MONTH', transaction_date) AS report_month,
    SUM(CASE WHEN account_type = 'Income' AND department = 'Doctor' THEN credit_amount ELSE 0 END) AS doctor_production,
    SUM(CASE WHEN account_type = 'Income' AND department = 'Specialty' THEN credit_amount ELSE 0 END) AS specialty_production,
    SUM(CASE WHEN account_type = 'Income' AND department = 'Hygiene' THEN credit_amount ELSE 0 END) AS hygiene_production,
    SUM(amount_paid) AS collections
FROM silver.fact_journal_entries je
LEFT JOIN silver.fact_invoices inv ON je.transaction_date = inv.invoice_date
WHERE je.status = 'Posted'
GROUP BY subsidiary_name, DATE_TRUNC('MONTH', transaction_date)
```

**Status:** ✅ NetSuite integration already live, just need to add aggregation query

---

### 2. PATIENT VISITS (5 Metrics)

| Metric | Primary Source | Secondary Source | Status |
|--------|---------------|------------------|--------|
| **Doctor Visits** | ⚠️ **PMS** (Dentrix/Eaglesoft Appointments) | CSV Upload | 🔄 CSV for now |
| **Specialist Visits** | ⚠️ **PMS** (Appointments) | CSV Upload | 🔄 CSV for now |
| **Hygiene Visits** | ⚠️ **PMS** (Appointments) | CSV Upload | 🔄 CSV for now |
| **Total Visits** | ⚠️ **PMS** (Appointments) | CSV Upload | 🔄 CSV for now |
| **LTM Visits** | ✅ **Calculated** (12-month rolling) | - | ✅ Auto-calculated |

**Integration Needed:**
- Dentrix/Eaglesoft API integration for appointment data
- Alternative: Daily PMS day sheet upload (already have this for production!)

**Workaround:**
- PMS day sheets contain visit counts
- Already extracting from PDF uploads
- Can reuse `bronze.pms_day_sheets` table

```sql
-- Get visit counts from existing PMS day sheets
SELECT
    practice_location,
    DATE_TRUNC('MONTH', report_date) AS report_month,
    SUM(extracted_data:patient_visits::INT) AS total_visits
FROM bronze.pms_day_sheets
GROUP BY practice_location, DATE_TRUNC('MONTH', report_date)
```

**Status:** ⚠️ Can leverage existing PMS day sheet data, or use CSV upload

---

### 3. PRODUCTION PER VISIT (6 Metrics)

| Metric | Primary Source | Calculation | Status |
|--------|---------------|-------------|--------|
| **Doctor PPV** | ✅ Calculated | Doctor Production / Doctor Visits | ✅ Auto-calculated |
| **Specialist PPV** | ✅ Calculated | Specialist Production / Specialist Visits | ✅ Auto-calculated |
| **Hygiene PPV** | ✅ Calculated | Hygiene Production / Hygiene Visits | ✅ Auto-calculated |
| **Total PPV** | ✅ Calculated | Total Production / Total Visits | ✅ Auto-calculated |
| **LTM Provider PPV** | ✅ Calculated | LTM Production / LTM Visits | ✅ Auto-calculated |
| **LTM Total PPV** | ✅ Calculated | Rolling average | ✅ Auto-calculated |

**Status:** ✅ All calculated in Gold dynamic table (no source needed)

---

### 4. CASE ACCEPTANCE (6 Metrics per Provider)

| Metric | Primary Source | Secondary Source | Status |
|--------|---------------|------------------|--------|
| **Treatment Presented** | ⚠️ **PMS** (Treatment Plans) | CSV Upload | 🔄 CSV for now |
| **Treatment Accepted** | ⚠️ **PMS** (Treatment Plans) | CSV Upload | 🔄 CSV for now |
| **Case Acceptance Rate %** | ✅ Calculated | Accepted / Presented | ✅ Auto-calculated |
| **Provider-Level Tracking** | ⚠️ **PMS** (by provider) | CSV Upload | 🔄 CSV for now |
| **Monthly Trends** | ✅ Calculated | Historical comparison | ✅ Auto-calculated |
| **LTM Case Acceptance** | ✅ Calculated | 12-month rolling | ✅ Auto-calculated |

**Integration Needed:**
- Dentrix/Eaglesoft Treatment Plan module
- Track: Plan created date, presented date, accepted date, provider

**Workaround:**
- Manual entry in Operations Report Excel → CSV upload
- OR: Extract from PMS export reports

**Status:** 🔄 CSV upload for Phase 1, PMS integration for Phase 2

---

### 5. NEW PATIENT ACQUISITION (2 Metrics)

| Metric | Primary Source | Secondary Source | Status |
|--------|---------------|------------------|--------|
| **New Patients per Month** | ⚠️ **PMS** (New Patient flag) | CSV Upload | 🔄 CSV for now |
| **Reappointment Rate** | ⚠️ **PMS** (Follow-up appointments) | CSV Upload | 🔄 CSV for now |

**Integration Options:**
1. Dentrix: Query `patient` table WHERE `first_visit_date` in month
2. Eaglesoft: Similar patient master table query
3. NetSuite: IF patients tracked as customers, can use `customer.first_order_date`

**Best Approach:**
- PMS is source of truth for patient data
- NetSuite has financial data, not patient demographics

**Status:** 🔄 CSV upload for Phase 1, PMS API integration for Phase 2

---

### 6. HYGIENE EFFICIENCY (5 Metrics)

| Metric | Primary Source | Secondary Source | Status |
|--------|---------------|------------------|--------|
| **Hygiene Capacity Utilization** | ⚠️ **PMS** (Schedule capacity) | CSV Upload | 🔄 CSV for now |
| **Hygiene Productivity Ratio** | ✅ **Hybrid** | Production ÷ Compensation | ✅ Partial |
| **Revenue per Hygiene Hour** | ⚠️ **PMS + Payroll** | CSV Upload | 🔄 CSV for now |
| **Patients per Hygiene Hour** | ⚠️ **PMS** (Schedule + visits) | CSV Upload | 🔄 CSV for now |
| **Hygiene Reappointment %** | ⚠️ **PMS** (Follow-up scheduling) | CSV Upload | 🔄 CSV for now |

**Data Sources Breakdown:**
- **Hygiene Production:** ✅ NetSuite (already have)
- **Hygiene Compensation:** ✅ ADP Payroll OR NetSuite Expense accounts
- **Hygiene Hours:** ⚠️ ADP Time & Attendance OR PMS schedule
- **Hygiene Visit Counts:** ⚠️ PMS day sheets (already have!)
- **Capacity/Scheduling:** ⚠️ PMS appointment system

**NetSuite Query for Hygiene Compensation:**
```sql
SELECT
    subsidiary_name,
    DATE_TRUNC('MONTH', transaction_date) AS month,
    SUM(debit_amount) AS hygiene_compensation
FROM silver.fact_journal_entries
WHERE account_name LIKE '%Hygiene%Salary%'
   OR account_name LIKE '%Hygiene%Wages%'
GROUP BY subsidiary_name, month
```

**Status:** 🔄 Partial from NetSuite, rest from CSV upload

---

### 7. PROVIDER GROSS PRODUCTION (Detailed Per Provider)

| Metric | Primary Source | Secondary Source | Status |
|--------|---------------|------------------|--------|
| **Monthly Gross Production** | ✅ **NetSuite** (by provider/department) | CSV Upload | ✅ Partial |
| **LTM Gross Production** | ✅ Calculated | 12-month rolling | ✅ Auto-calculated |
| **Provider-by-Provider Breakdown** | ⚠️ **NetSuite + PMS** | CSV Upload | 🔄 CSV for now |

**NetSuite Approach:**
```sql
-- NetSuite tracks production by department/class/location
SELECT
    je.department,  -- Might be provider name or "Doctor 1", "Doctor 2"
    je.class,  -- Might have provider classification
    je.location,  -- Practice location
    SUM(credit_amount) AS production
FROM silver.fact_journal_entries je
WHERE account_type = 'Income'
GROUP BY department, class, location
```

**Challenge:**
- NetSuite might not have individual provider names
- Need to map NetSuite departments/classes to actual providers

**Best Approach:**
1. Check NetSuite custom fields for provider tracking
2. If not available, use CSV upload for provider detail
3. Later: Add provider mapping table (NetSuite dept → Provider name)

**Status:** 🔄 NetSuite for totals, CSV for provider detail

---

## 🔄 Hybrid Data Flow Architecture

### Current State (Recommended for Phase 1)

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ NetSuite ERP                    ⚠️ CSV Upload                │
│  (Already Integrated)               (Manual for Phase 1)         │
│  ├─ Production (by dept)            ├─ Provider detail           │
│  ├─ Collections                     ├─ Case acceptance           │
│  ├─ Expenses                        ├─ New patients              │
│  └─ Compensation                    ├─ Visit counts (detail)     │
│                                     └─ Reappointment rates       │
│                                                                  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │        BRONZE: operations_metrics_raw (VARIANT)            │  │
│  │  Stores: NetSuite aggregated + CSV uploaded data as JSON  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                         ↓ (Auto-refresh: 1 hour)                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │     SILVER: stg_operations_metrics (Dynamic Table)         │  │
│  │  Extracts: Typed columns from JSON                        │  │
│  └───────────────────────────────────────────────────────────┘  │
│                         ↓ (Auto-refresh: 1 hour)                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │     GOLD: operations_kpis_monthly (Dynamic Table)          │  │
│  │  Calculates: All KPIs, ratios, LTM rollups               │  │
│  └───────────────────────────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           API: /api/v1/operations/kpis/*                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │    FRONTEND: /analytics/operations Dashboard              │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Detailed Data Source Matrix

### Legend:
- ✅ = Already available from NetSuite integration
- 🟡 = Partially available, needs enhancement
- ⚠️ = Requires PMS integration or CSV upload
- 🔄 = CSV upload for Phase 1, automate in Phase 2

---

### **Category 1: Production & Collections**

| KPI | Source System | Table/API | Notes |
|-----|--------------|-----------|-------|
| Gross Production - Doctor | ✅ NetSuite | `silver.fact_journal_entries` | Filter by department/class |
| Gross Production - Specialty | ✅ NetSuite | `silver.fact_journal_entries` | Filter by specialty dept |
| Gross Production - Hygiene | ✅ NetSuite | `silver.fact_journal_entries` | Filter by hygiene dept |
| Net Production | ✅ NetSuite | Calculated (Gross - Adjustments) | Already in `gold.daily_financial_summary` |
| Collections | ✅ NetSuite | `silver.fact_invoice_payments` | Already tracked |
| Collection Rate % | ✅ Calculated | Collections / Net Production | In Gold layer |
| LTM Production | ✅ Calculated | Window function (12 months) | In Gold layer |
| LTM Collections | ✅ Calculated | Window function (12 months) | In Gold layer |

**Implementation:**
```sql
-- Add this to existing NetSuite data pipeline
CREATE OR REPLACE VIEW gold.operations_production_from_netsuite AS
SELECT
    subsidiary_name AS practice_location,
    DATE_TRUNC('MONTH', transaction_date) AS report_month,
    SUM(CASE WHEN line_memo LIKE '%Doctor%' OR department = 'Provider' THEN credit_amount ELSE 0 END) AS gross_production_doctor,
    SUM(CASE WHEN line_memo LIKE '%Specialty%' THEN credit_amount ELSE 0 END) AS gross_production_specialty,
    SUM(CASE WHEN line_memo LIKE '%Hygiene%' OR department = 'Hygiene' THEN credit_amount ELSE 0 END) AS gross_production_hygiene,
    SUM(credit_amount) AS total_production
FROM silver.fact_journal_entries
WHERE account_type = 'Income'
  AND status = 'Posted'
GROUP BY subsidiary_name, DATE_TRUNC('MONTH', transaction_date);
```

---

### **Category 2: Patient Visits**

| KPI | Source System | Table/API | Notes |
|-----|--------------|-----------|-------|
| Doctor Visits | 🟡 PMS Day Sheets | `bronze.pms_day_sheets` → `extracted_data:patient_visits` | Already extracting! |
| Specialist Visits | ⚠️ PMS or CSV | Manual upload | Not in day sheets |
| Hygiene Visits | ⚠️ PMS or CSV | Manual upload | Not in day sheets |
| Total Visits | 🟡 PMS Day Sheets | `bronze.pms_day_sheets` | Have total, not breakdown |
| LTM Visits | ✅ Calculated | Window function | Auto-calculated |

**Current PMS Day Sheet Data:**
```json
{
  "patient_visits": 464  // Total only, no breakdown
}
```

**Options:**
1. **Use existing day sheets** for total visits (already have!)
2. **CSV upload** for provider-level breakdown
3. **PMS API integration** for detailed appointment data (Phase 2)

**Recommendation:** Mix existing day sheet data (totals) + CSV upload (breakdown)

---

### **Category 3: Production Per Visit**

| KPI | Source System | Calculation | Status |
|-----|--------------|-------------|--------|
| Doctor PPV | ✅ Calculated | Doctor Production / Doctor Visits | ✅ Auto |
| Specialist PPV | ✅ Calculated | Specialist Production / Specialist Visits | ✅ Auto |
| Hygiene PPV | ✅ Calculated | Hygiene Production / Hygiene Visits | ✅ Auto |
| Total PPV | ✅ Calculated | Total Production / Total Visits | ✅ Auto |
| LTM Provider PPV | ✅ Calculated | LTM Production / LTM Visits | ✅ Auto |
| LTM Total PPV | ✅ Calculated | Rolling average | ✅ Auto |

**Dependency:** Needs Categories 1 (Production) + 2 (Visits)

**Status:** ✅ Fully automated once source data available

---

### **Category 4: Case Acceptance**

| KPI | Source System | Table/API | Notes |
|-----|--------------|-----------|-------|
| Treatment Presented | ⚠️ PMS Treatment Plans | Dentrix/Eaglesoft | Not in NetSuite |
| Treatment Accepted | ⚠️ PMS Treatment Plans | Dentrix/Eaglesoft | Not in NetSuite |
| Case Acceptance Rate % | ✅ Calculated | Accepted / Presented | Auto-calculated |
| Provider-Level Tracking | ⚠️ PMS | CSV Upload | Per-provider detail |
| Monthly Trends | ✅ Calculated | Historical comparison | Auto-calculated |
| LTM Case Acceptance | ✅ Calculated | 12-month rolling | Auto-calculated |

**Integration Path:**
1. **Phase 1:** CSV upload (from manual Operations Report)
2. **Phase 2:** PMS API integration
   - Dentrix: `treatment_plan` table
   - Eaglesoft: Treatment plan module API

**Status:** 🔄 CSV for Phase 1, PMS API for Phase 2

---

### **Category 5: New Patient Acquisition**

| KPI | Source System | Table/API | Notes |
|-----|--------------|-----------|-------|
| New Patients per Month | ⚠️ PMS Patient Master | `patient` table WHERE `is_new` | Not in NetSuite |
| Reappointment Rate | ⚠️ PMS Appointments | Next appointment scheduled? | Not in NetSuite |

**NetSuite Alternative:**
- IF practices track new patients as "new customers" in NetSuite
- Query: `SELECT COUNT(*) FROM netsuite_customer WHERE date_created = month`
- Unlikely to be accurate (NetSuite = billing, not patient mgmt)

**Best Source:** PMS system (source of truth for patient data)

**Status:** 🔄 CSV for Phase 1, PMS API for Phase 2

---

### **Category 6: Hygiene Efficiency**

| KPI | Source System | Calculation/Source | Status |
|-----|--------------|-------------------|--------|
| Hygiene Capacity Utilization | 🟡 PMS Schedule + CSV | Actual visits / Available slots | 🔄 Hybrid |
| Hygiene Productivity Ratio | ✅ NetSuite + NetSuite/ADP | Production / Compensation | ✅ Available |
| Revenue per Hygiene Hour | 🟡 NetSuite + ADP | Production / Hours worked | 🔄 Need ADP |
| Patients per Hygiene Hour | ⚠️ PMS + ADP | Visits / Hours | 🔄 CSV for now |
| Hygiene Reappointment % | ⚠️ PMS | Follow-up scheduling | 🔄 CSV for now |

**Data Source Breakdown:**
- **Hygiene Production:** ✅ NetSuite (already have)
- **Hygiene Compensation:** ✅ NetSuite expense accounts OR ADP payroll
- **Hygiene Hours:** ⚠️ ADP time & attendance (need integration)
- **Hygiene Visits:** 🟡 PMS day sheets (have total, not hygiene-specific)
- **Capacity/Schedule:** ⚠️ PMS scheduling system

**NetSuite for Compensation:**
```sql
-- Get hygiene compensation from expense accounts
SELECT
    subsidiary_name,
    DATE_TRUNC('MONTH', transaction_date) AS month,
    SUM(debit_amount) AS hygiene_compensation
FROM silver.fact_journal_entries
WHERE account_name LIKE '%Hygiene%Payroll%'
   OR account_name LIKE '%Hygiene%Salary%'
   OR account_name LIKE '%Hygiene%Wages%'
   OR (account_type = 'Expense' AND department = 'Hygiene')
GROUP BY subsidiary_name, month
```

**Status:** 🔄 Production from NetSuite, rest from CSV/ADP

---

### **Category 7: Provider Gross Production**

| KPI | Source System | Table/API | Notes |
|-----|--------------|-----------|-------|
| Monthly Gross Production | ✅ NetSuite | `silver.fact_journal_entries` | By department |
| LTM Gross Production | ✅ Calculated | Window function | Auto-calculated |
| Provider-by-Provider Breakdown | ⚠️ NetSuite Custom Fields? | CSV Upload | Need provider mapping |

**NetSuite Provider Tracking Options:**

**Option 1: NetSuite has provider custom field**
```sql
SELECT
    je.custom_field_provider_name AS provider,
    SUM(credit_amount) AS production
FROM silver.fact_journal_entries je
WHERE account_type = 'Income'
GROUP BY provider
```

**Option 2: NetSuite uses departments**
```sql
SELECT
    je.department AS provider,  -- "Dr. Smith", "Dr. Jones"
    SUM(credit_amount) AS production
FROM silver.fact_journal_entries je
WHERE account_type = 'Income'
GROUP BY department
```

**Option 3: CSV Upload (if NetSuite doesn't track)**
- Manual mapping in Operations Report Excel
- Upload provider detail via CSV

**Action Required:** Check NetSuite schema for provider tracking fields

**Status:** 🔄 Depends on NetSuite configuration, CSV backup

---

## 🚀 Implementation Phases

### **Phase 1: Quick Win (Current - Week 1)**
✅ Create Snowflake tables (Bronze, Silver, Gold dynamic)
✅ Build API endpoints
✅ CSV upload capability for all 7 categories
🔄 NetSuite integration for Production & Collections only

**Result:** Working dashboard with manual CSV upload + some NetSuite automation

---

### **Phase 2: NetSuite Deep Integration (Weeks 2-3)**
- [ ] Add NetSuite queries for hygiene compensation
- [ ] Map NetSuite departments/classes to providers
- [ ] Build automated monthly aggregation job
- [ ] Reduce CSV dependency to just PMS-specific metrics

**Result:** 50% of metrics automated from NetSuite

---

### **Phase 3: PMS Integration (Months 2-3)**
- [ ] Dentrix/Eaglesoft API integration
- [ ] Patient visit detail extraction
- [ ] Case acceptance tracking
- [ ] New patient identification
- [ ] Reappointment rate calculation

**Result:** 90% of metrics fully automated

---

### **Phase 4: ADP Payroll Integration (Month 3-4)**
- [ ] ADP API integration
- [ ] Time & attendance data
- [ ] Compensation by provider
- [ ] Hours worked tracking

**Result:** 100% automated, zero manual entry

---

## 💡 Recommendations

### Immediate (This Week):
1. ✅ **Use CSV upload for Phase 1** - Gets dashboard working immediately
2. ✅ **Leverage NetSuite for financials** - Production, collections, compensation
3. ⚠️ **Check NetSuite for provider fields** - Custom fields? Departments? Classes?

### Short-term (Weeks 2-4):
4. Build NetSuite aggregation queries for operations metrics
5. Create provider mapping table (NetSuite dept → Provider name)
6. Add scheduled job to sync NetSuite → operations Bronze daily

### Long-term (Months 2-4):
7. PMS API integration for patient/visit detail
8. ADP integration for time & payroll data
9. Fully automated pipeline, retire CSV uploads

---

## 📝 Action Items for Client

To maximize NetSuite integration, we need:

1. **NetSuite Schema Review**
   - [ ] How are providers tracked? (Custom field? Department? Class?)
   - [ ] Do journal entries have provider assignment?
   - [ ] Are there expense accounts per provider?

2. **Account Mapping**
   - [ ] Income accounts for Doctor/Specialty/Hygiene
   - [ ] Expense accounts for compensation by provider type
   - [ ] Any custom segments/dimensions?

3. **Data Availability**
   - [ ] Does NetSuite have patient count data? (Unlikely)
   - [ ] Treatment plan data in NetSuite? (Unlikely)
   - [ ] Appointment scheduling data? (No)

**Likely Outcome:**
- ✅ Production & Collections: 100% from NetSuite
- ⚠️ Visits & Patients: Need PMS integration OR CSV
- ⚠️ Case Acceptance: Need PMS integration OR CSV
- 🟡 Hygiene Efficiency: Partial from NetSuite, rest from CSV/ADP

---

**Document Owner:** Development Team
**Last Updated:** November 17, 2025
**Next Review:** After NetSuite schema review
