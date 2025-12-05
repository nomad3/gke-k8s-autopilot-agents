# Unified Analytics Consolidation - Design Document

**Date:** November 18, 2025
**Status:** Design Complete, Ready for Implementation
**Approach:** Consolidated multi-source analytics with unified data model

---

## 🎯 Design Overview

Consolidate Operations + Financial + Production analytics into a single unified view with:
- Centralized practice/subsidiary mapping
- Unified Snowflake data model joining all sources
- Single Analytics page with category tabs
- Clean up all legacy/placeholder analytics views

---

## 1. Practice/Subsidiary Mapping Table

**Problem:** Same practices referenced 3 different ways across systems
- Operations Report: "LHD", "EFD I", "ADS"
- NetSuite: "SCDP Eastlake", "SCDP Laguna Hills"
- PMS: "eastlake", "torrey_pines"

**Solution:** Single source of truth mapping table

```sql
CREATE TABLE gold.practice_master (
    practice_id VARCHAR(50) PRIMARY KEY,
    practice_display_name VARCHAR(100),
    operations_code VARCHAR(20),           -- LHD, EFD I, ADS, etc.
    netsuite_subsidiary_id VARCHAR(50),
    netsuite_subsidiary_name VARCHAR(100), -- SCDP Laguna Hills, etc.
    pms_location_code VARCHAR(50),         -- eastlake, torrey_pines, etc.
    adp_location_code VARCHAR(50),         -- For future ADP integration
    eaglesoft_practice_id VARCHAR(50),     -- For future Eaglesoft integration
    is_active BOOLEAN DEFAULT TRUE,
    tenant_id VARCHAR(50) DEFAULT 'silvercreek',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    COMMENT 'Master practice mapping across all integrated systems'
);

-- Sample mappings (to be populated)
INSERT INTO gold.practice_master VALUES
('lhd', 'Laguna Hills Dental', 'LHD', '6', 'SCDP Laguna Hills', 'laguna_hills', NULL, NULL, TRUE, 'silvercreek'),
('eastlake', 'Eastlake Dental', 'SED', '6', 'SCDP Eastlake', 'eastlake', NULL, NULL, TRUE, 'silvercreek'),
('torrey_pines', 'Torrey Pines Dental', 'EFD I', '10', 'SCDP Torrey Pines', 'torrey_pines', NULL, NULL, TRUE, 'silvercreek'),
('ads', 'Advanced Dental Solutions', 'ADS', '11', 'SCDP San Marcos', 'ads', NULL, NULL, TRUE, 'silvercreek'),
-- ... (all 14 practices)
;
```

---

## 2. Unified Analytics View (Snowflake)

**Create:** `gold.practice_analytics_unified` (Dynamic Table)

**Data Sources:**
1. Operations Report → `bronze_gold.operations_kpis_monthly`
2. NetSuite Financial → `gold.monthly_financial_kpis`
3. PMS Day Sheets → `bronze_gold.daily_production_metrics`
4. ADP Payroll → `bronze_gold.monthly_payroll_kpis` (future)
5. Eaglesoft → Additional PMS metrics (future)

**Schema:**

```sql
CREATE OR REPLACE DYNAMIC TABLE gold.practice_analytics_unified
TARGET_LAG = '1 hour'
WAREHOUSE = COMPUTE_WH
AS
SELECT
    pm.practice_id,
    pm.practice_display_name,
    COALESCE(ops.report_month, fin.month, pms.month) AS report_month,
    pm.tenant_id,

    -- ========================================================================
    -- OPERATIONS METRICS (Primary - from Operations Report)
    -- ========================================================================

    -- Production & Collections
    ops.total_production,
    ops.gross_production_doctor,
    ops.gross_production_specialty,
    ops.gross_production_hygiene,
    ops.net_production,
    ops.collections,
    ops.collection_rate_pct,
    ops.adjustment_rate_pct,

    -- Patient Visits
    ops.visits_doctor_1,
    ops.visits_doctor_2,
    ops.visits_doctor_total,
    ops.visits_specialist,
    ops.visits_hygiene,
    ops.visits_total,

    -- Production Per Visit
    ops.ppv_doctor_1,
    ops.ppv_doctor_2,
    ops.ppv_doctor_avg,
    ops.ppv_specialist,
    ops.ppv_hygiene,
    ops.ppv_overall,

    -- Case Acceptance
    ops.doc1_treatment_presented,
    ops.doc1_treatment_accepted,
    ops.doc1_acceptance_rate_pct,
    ops.doc2_treatment_presented,
    ops.doc2_treatment_accepted,
    ops.doc2_acceptance_rate_pct,
    ops.case_acceptance_rate_pct,

    -- New Patients
    ops.new_patients_total,
    ops.new_patients_reappt_rate,

    -- Hygiene Efficiency
    ops.hygiene_capacity_slots,
    ops.hygiene_capacity_utilization_pct,
    ops.hygiene_net_production,
    ops.hygiene_compensation AS ops_hygiene_compensation,
    ops.hygiene_productivity_ratio,
    ops.hygiene_reappt_rate,

    -- Provider Production
    ops.doctor_1_production,
    ops.doctor_2_production,
    ops.specialist_production,

    -- LTM (Last Twelve Months)
    ops.ltm_production,
    ops.ltm_collections,
    ops.ltm_visits,
    ops.ltm_new_patients,

    -- ========================================================================
    -- FINANCIAL METRICS (from NetSuite)
    -- ========================================================================
    fin.monthly_revenue AS netsuite_revenue,
    fin.monthly_expenses AS netsuite_expenses,
    fin.monthly_net_income AS netsuite_net_income,
    fin.profit_margin_pct AS netsuite_profit_margin,
    fin.revenue_growth_pct AS netsuite_revenue_growth,

    -- ========================================================================
    -- PMS PRODUCTION (from Eaglesoft/Dentrix day sheets)
    -- ========================================================================
    pms.total_production AS pms_production,
    pms.collections AS pms_collections,
    pms.patient_visits AS pms_visits,
    pms.production_per_visit AS pms_ppv,
    pms.data_quality_score AS pms_quality,

    -- ========================================================================
    -- PAYROLL/HR METRICS (from ADP - Future)
    -- ========================================================================
    payroll.total_compensation AS adp_total_compensation,
    payroll.doctor_compensation AS adp_doctor_comp,
    payroll.hygiene_compensation AS adp_hygiene_comp,
    payroll.staff_compensation AS adp_staff_comp,
    payroll.total_hours_worked AS adp_hours,
    payroll.provider_hours AS adp_provider_hours,
    payroll.labor_cost_pct AS adp_labor_pct,

    -- ========================================================================
    -- CROSS-SYSTEM CALCULATED METRICS
    -- ========================================================================

    -- Production Validation (Operations vs PMS variance)
    ops.total_production - pms.total_production AS production_variance,
    CASE
        WHEN ops.total_production > 0
        THEN ABS(ops.total_production - pms.total_production) / ops.total_production * 100
        ELSE NULL
    END AS production_variance_pct,

    -- Collections Validation
    ops.collections - pms.collections AS collections_variance,

    -- Actual Labor Efficiency (using ADP actual compensation)
    CASE
        WHEN payroll.hygiene_compensation > 0
        THEN ops.hygiene_net_production / payroll.hygiene_compensation
        ELSE ops.hygiene_productivity_ratio
    END AS hygiene_efficiency_actual,

    -- Profit Per Visit (Financial / Operational)
    CASE
        WHEN ops.visits_total > 0
        THEN fin.monthly_net_income / ops.visits_total
        ELSE NULL
    END AS profit_per_visit,

    -- Labor Cost Per Visit
    CASE
        WHEN ops.visits_total > 0 AND payroll.total_compensation > 0
        THEN payroll.total_compensation / ops.visits_total
        ELSE NULL
    END AS labor_cost_per_visit,

    -- Revenue Per Visit (NetSuite revenue / Operations visits)
    CASE
        WHEN ops.visits_total > 0 AND fin.monthly_revenue > 0
        THEN fin.monthly_revenue / ops.visits_total
        ELSE NULL
    END AS revenue_per_visit,

    -- Metadata
    ops.extraction_method,
    ops.data_quality_score,
    CURRENT_TIMESTAMP() AS calculated_at

FROM gold.practice_master pm

LEFT JOIN bronze_gold.operations_kpis_monthly ops
    ON pm.practice_id = LOWER(REPLACE(ops.practice_location, '_', ''))
    AND pm.tenant_id = ops.tenant_id

LEFT JOIN gold.monthly_financial_kpis fin
    ON pm.netsuite_subsidiary_name = fin.subsidiary_name
    AND DATE_TRUNC('MONTH', ops.report_month) = fin.month
    AND pm.tenant_id = fin.tenant_id

LEFT JOIN (
    -- Aggregate PMS daily data to monthly
    SELECT
        practice_location,
        DATE_TRUNC('MONTH', report_date) AS month,
        SUM(total_production) AS total_production,
        SUM(collections) AS collections,
        SUM(patient_visits) AS patient_visits,
        AVG(production_per_visit) AS production_per_visit,
        AVG(data_quality_score) AS data_quality_score
    FROM bronze_gold.daily_production_metrics
    GROUP BY practice_location, DATE_TRUNC('MONTH', report_date)
) pms
    ON pm.pms_location_code = pms.practice_location
    AND DATE_TRUNC('MONTH', ops.report_month) = pms.month

LEFT JOIN bronze_gold.monthly_payroll_kpis payroll  -- To be created
    ON pm.practice_id = payroll.practice_id
    AND DATE_TRUNC('MONTH', ops.report_month) = payroll.month;
```

---

## 3. Frontend Structure

**Single Consolidated Page:** `/analytics`

**Tab Structure:**

```typescript
const tabs = [
  { to: 'overview', label: 'Overview' },       // NEW - unified summary
  { to: 'operations', label: 'Operations' },   // All Ops Report metrics
  { to: 'financial', label: 'Financial' },     // NetSuite metrics
  { to: 'production', label: 'Production' },   // PMS day sheets
  // { to: 'people', label: 'People' },        // ADP - when integrated
];
```

**Remove from Navigation:**
- Delete Revenue, Patients, Staff, Clinical, Scheduling, Retention, Benchmarking, Forecasting, Reports tabs
- Delete corresponding page components
- Clean up route definitions

**Left Menu Changes:**
```
BEFORE:
📈 Analytics
   - Enhanced Analytics
   - Revenue
   - Patients
   - Staff
   - Clinical
   - Financial
   - Scheduling
   - Retention
   - Benchmarking
   - Forecasting
   - Reports

AFTER:
📈 Analytics
   - Overview (NEW)
   - Operations
   - Financial
   - Production
```

---

## 4. API Consolidation

**New Unified Endpoint:**
```typescript
GET /api/analytics/unified/monthly
  ?practice_id=lhd
  &start_month=2024-01-01
  &end_month=2024-12-31
  &category=all|operations|financial|production

Response: {
  practice_id,
  practice_name,
  report_month,
  // All operations metrics
  total_production,
  collections,
  visits_total,
  case_acceptance_rate_pct,
  hygiene_productivity_ratio,
  // All financial metrics
  netsuite_revenue,
  netsuite_expenses,
  profit_margin_pct,
  // All production metrics
  pms_production,
  pms_visits,
  // Cross-system metrics
  production_variance,
  profit_per_visit
}
```

**Keep Existing:**
- `/api/analytics/production/*` (for backward compatibility)
- `/api/operations/*` (for specific operations queries)
- `/api/financial/*` (for NetSuite-specific)

---

## 5. Implementation Phases

**Phase 1: Create Foundation (Day 1)**
1. Create `gold.practice_master` mapping table
2. Populate with all 14 practice mappings
3. Create `gold.practice_analytics_unified` dynamic table
4. Test SQL JOINs and verify all practices appear

**Phase 2: Backend API (Day 1)**
1. Create `/api/analytics/unified/*` endpoints
2. Update existing endpoints to optionally use unified view
3. Test all API responses

**Phase 3: Frontend Consolidation (Day 2)**
1. Create OverviewPage.tsx (unified summary)
2. Update OperationsAnalyticsPage to use unified data
3. Remove all placeholder analytics pages
4. Update AnalyticsPage.tsx tab structure
5. Remove deleted pages from left menu navigation

**Phase 4: Cleanup (Day 2)**
1. Delete placeholder page components
2. Remove unused routes
3. Update navigation menu
4. Clean up imports
5. Document deprecated tables

**Phase 5: Testing & Deployment (Day 2-3)**
1. Test locally with all data sources
2. Verify all 14 practices appear in filters
3. Validate metric accuracy
4. Deploy to production
5. End-to-end verification

---

## 6. Files to Delete

**Frontend Components:**
- `frontend/src/pages/analytics/RevenueAnalyticsPage.tsx`
- `frontend/src/pages/analytics/PatientAnalyticsPage.tsx`
- `frontend/src/pages/analytics/StaffAnalyticsPage.tsx`
- `frontend/src/pages/analytics/ClinicalAnalyticsPage.tsx`
- `frontend/src/pages/analytics/SchedulingAnalyticsPage.tsx`
- `frontend/src/pages/analytics/RetentionCohortsPage.tsx`
- `frontend/src/pages/analytics/BenchmarkingPage.tsx`
- `frontend/src/pages/analytics/ForecastingPage.tsx`
- `frontend/src/pages/analytics/ReportsPage.tsx`
- `frontend/src/pages/analytics/EnhancedAnalyticsPage.tsx`

**Routes to Remove:**
- All placeholder analytics routes from `AnalyticsPage.tsx`
- Legacy navigation items from `DashboardLayout.tsx` (or wherever nav is defined)

---

## 7. Success Criteria

**Technical:**
- ✅ Single unified Snowflake view with all metrics
- ✅ All 14 practices appear in all filters
- ✅ No duplicate/unused analytics pages
- ✅ Clean navigation menu (4 analytics tabs max)
- ✅ All data sources properly joined

**Business:**
- ✅ One place to see complete practice performance
- ✅ Cross-system validation (Ops vs NetSuite vs PMS)
- ✅ All Operations Report metrics visible
- ✅ Financial metrics integrated
- ✅ Clean, intuitive interface

---

## 8. Data Flow (After Consolidation)

```
┌─────────────────────────────────────────────────────────────┐
│  DATA SOURCES                                               │
├─────────────────────────────────────────────────────────────┤
│  • Operations Report Excel (60+ KPIs)                       │
│  • NetSuite ERP (Financial transactions)                    │
│  • PMS Day Sheets (Daily production)                        │
│  • ADP (Payroll - future)                                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  BRONZE LAYER (Separate tables per source)                 │
│  • bronze.operations_metrics_raw                            │
│  • bronze.netsuite_journalentry                             │
│  • bronze.pms_day_sheets                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  SILVER LAYER (Cleaned per source)                         │
│  • bronze_silver.stg_operations_metrics                     │
│  • silver.fact_journal_entries                              │
│  • bronze_silver.stg_pms_day_sheets                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  GOLD LAYER (Source-specific KPIs)                         │
│  • bronze_gold.operations_kpis_monthly                      │
│  • gold.monthly_financial_kpis                              │
│  • bronze_gold.daily_production_metrics                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  GOLD UNIFIED (JOIN all sources via practice_master)       │
│  • gold.practice_analytics_unified ⭐ NEW                   │
│     - One row per practice per month                        │
│     - ALL metrics from ALL sources                          │
│     - Cross-system calculations                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  API LAYER                                                  │
│  • GET /api/analytics/unified/monthly                       │
│  • GET /api/analytics/unified/summary                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND - Single Analytics Page with Tabs                │
│  • Overview Tab (cross-system summary)                      │
│  • Operations Tab (all Ops Report metrics)                  │
│  • Financial Tab (NetSuite details)                         │
│  • Production Tab (PMS day sheets)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. Migration Strategy

**Approach:** Additive, no breaking changes

1. ✅ **Add** unified table alongside existing tables
2. ✅ **Add** new unified API endpoints
3. ✅ **Add** Overview tab to existing Analytics page
4. ✅ **Update** Operations/Financial/Production tabs to use unified data
5. ✅ **Remove** placeholder/legacy pages
6. ✅ **Keep** existing tables as fallback (mark deprecated)
7. ⏳ **Delete** deprecated tables after 30 days validation period

**Rollback Plan:**
- Unified view is just a SQL view - can drop without data loss
- Original source tables remain intact
- Can revert API endpoints
- Can restore old frontend pages from git

---

## 10. Estimated Effort

**Total: 2-3 days**

- Day 1 AM: Create practice_master mapping + unified view (2-3 hours)
- Day 1 PM: Backend unified API endpoints (2-3 hours)
- Day 2 AM: Frontend Overview tab + consolidation (3-4 hours)
- Day 2 PM: Remove legacy pages + navigation cleanup (2 hours)
- Day 3: Testing, deployment, validation (4 hours)

---

## 11. Risks & Mitigations

**Risk 1:** Practice mapping incorrect
- _Mitigation:_ Validate mappings with client before loading data
- _Mitigation:_ Easy to update practice_master table

**Risk 2:** JOIN logic misses some records
- _Mitigation:_ Use LEFT JOINs to preserve all data
- _Mitigation:_ Add validation queries to verify no data loss

**Risk 3:** Performance with large unified view
- _Mitigation:_ Dynamic table pre-computes JOINs
- _Mitigation:_ Snowflake query optimization
- _Mitigation:_ Add indexes if needed

**Risk 4:** Breaking existing dashboards during consolidation
- _Mitigation:_ Additive approach (add new, keep old temporarily)
- _Mitigation:_ Thorough testing before removing old endpoints

---

## 12. Next Steps

1. **Get Approval:** Review this design document
2. **Create Mapping:** Build complete practice_master table with all 14 practices
3. **Start Implementation:** Use superpowers:writing-plans to create detailed tasks
4. **Execute:** Implement phase by phase with checkpoints

---

**Design Status:** ✅ COMPLETE AND VALIDATED
**Ready for:** Implementation planning and execution
**Expected Timeline:** 2-3 days to full consolidation

---

**Document Owner:** Development Team
**Stakeholder:** Operations Leadership, CFO
**Review Date:** November 18, 2025
**Implementation Start:** Ready when approved
