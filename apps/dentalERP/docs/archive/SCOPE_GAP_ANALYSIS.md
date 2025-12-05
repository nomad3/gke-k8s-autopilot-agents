# DentalERP: Scope Gap Analysis
**Project:** AI-Accelerated Dental ERP MVP for Silvercreek (15 Locations)
**Date:** November 8, 2025
**Current Status:** 17% Complete

---

## Executive Summary

### Current State
The DentalERP platform has **solid infrastructure** but is missing **critical integrations and AI features** required for the Silvercreek MVP scope.

**What's Working:**
- ✅ Multi-tenant architecture (production-ready)
- ✅ NetSuite integration (31,315 records synced)
- ✅ PDF AI extraction (GPT-4 Vision)
- ✅ Snowflake warehouse (Bronze-Silver-Gold)
- ✅ Production analytics dashboard
- ✅ Authentication & role-based access

**What's Missing:**
- ❌ 3 critical integrations (ADP, DentalIntel, Dentrix/Eaglesoft)
- ❌ AI features (forecasting, text-to-insights, anomaly detection)
- ❌ Advanced dashboards (financial, clinical, patient analytics)
- ❌ 80% of dbt transformations
- ⚠️ Data duplication not prevented (5x duplicates found)

### Timeline Impact
**Original Scope:** 8 weeks
**Estimated Remaining:** 10-12 weeks (60-83 days of work)

---

## Detailed Gap Analysis

### 1. Data Integrations (20% Complete)

#### ✅ NetSuite (100% Complete)
- **Status:** PRODUCTION READY
- **Synced Data:** 31,315 records (journal entries, accounts, vendors, bills)
- **Features:** OAuth 1.0a, automatic sync, error retry
- **Verified:** All 3 bug fixes working, VARIANT columns functional
- **File:** `mcp-server/src/connectors/netsuite.py` (510 lines)

#### ⚠️ ADP Payroll (70% Complete - NOT PRODUCTION)
- **Status:** Built but not activated
- **File:** `mcp-server/src/connectors/adp.py` (240 lines)
- **Features Built:**
  - OAuth 2.0 client credentials flow
  - Employee, payroll, timecard endpoints
  - Token caching & refresh
- **Missing:**
  - Not registered in ConnectorRegistry
  - No sync orchestrator
  - No dbt models
  - Not tested with production data
- **Effort to Complete:** 2-3 days

#### ❌ DentalIntel (0% Complete)
- **Status:** NOT STARTED
- **Required:** Analytics and production metrics integration
- **Scope:**
  - API connector (OAuth 2.0 or API key)
  - Production, patient volume, appointment data
  - Bronze → Silver → Gold transformation
- **Effort:** 3-4 days

#### ❌ Dentrix PMS (0% Complete)
- **Status:** NOT STARTED
- **Scope:** Practice management system data
- **Required:**
  - API connector or CSV export parser
  - Patient, appointment, production, treatment data
  - Multi-location consolidation
- **Effort:** 5-7 days (depends on API availability)

#### ❌ Eaglesoft PMS (0% Complete)
- **Status:** NOT STARTED
- **Current Workaround:** Manual PDF uploads
- **Scope:** Practice management system data
- **Required:**
  - API connector or CSV export parser
  - Integration with existing PDF ingestion
- **Effort:** 5-7 days

**Integration Gap Total:** 17-24 days of work remaining

---

### 2. dbt Transformations (15% Complete)

#### ✅ PMS Day Sheets (Complete)
- **Silver:** `stg_pms_day_sheets.sql` - Type casting, null handling, quality scoring
- **Gold:** `daily_production_metrics.sql` - Daily aggregations, KPIs
- **Status:** WORKING with PDF ingestion data

#### ❌ NetSuite Financials (0% Complete)
**Required Silver Models:**
- `silver/netsuite/stg_journal_entries.sql` - Clean GL transactions
- `silver/netsuite/stg_accounts.sql` - Chart of accounts standardization
- `silver/netsuite/stg_invoices.sql` - Customer invoicing
- `silver/netsuite/stg_payments.sql` - Cash receipts
- `silver/netsuite/stg_vendor_bills.sql` - AP transactions

**Required Gold Models:**
- `gold/financial/monthly_pnl.sql` - P&L by location
- `gold/financial/cash_flow.sql` - Cash flow analysis
- `gold/financial/ar_aging.sql` - Accounts receivable aging
- `gold/financial/ap_aging.sql` - Accounts payable aging
- `gold/financial/balance_sheet.sql` - Balance sheet by location

**Effort:** 5-7 days

#### ❌ ADP Payroll (0% Complete)
**Required Silver Models:**
- `silver/adp/stg_employees.sql` - Employee master with locations
- `silver/adp/stg_payroll.sql` - Payroll runs standardized
- `silver/adp/stg_timecards.sql` - Hours worked by location

**Required Gold Models:**
- `gold/payroll/monthly_labor_costs.sql` - Cost by location/dept
- `gold/payroll/overtime_analysis.sql` - OT tracking
- `gold/payroll/headcount_metrics.sql` - FTE analysis

**Effort:** 4-5 days

#### ❌ PMS Clinical Data (0% Complete)
**Required Silver Models:**
- `silver/pms/stg_patients.sql` - Patient master
- `silver/pms/stg_appointments.sql` - Appointment history
- `silver/pms/stg_treatments.sql` - Procedures performed

**Required Gold Models:**
- `gold/clinical/patient_acquisition.sql` - New patient trends
- `gold/clinical/retention_cohorts.sql` - Patient retention
- `gold/clinical/treatment_mix.sql` - Procedure distribution
- `gold/clinical/provider_productivity.sql` - Provider metrics

**Effort:** 6-8 days

#### ⚠️ Monthly KPIs (90% Complete - DISABLED)
- **File:** `monthly_production_kpis.sql.disabled`
- **Status:** COMPLETE but disabled
- **Features:**
  - Monthly aggregation
  - MoM growth calculation
  - Target variance
  - Profit margins
- **Action:** Remove .disabled extension, test, activate
- **Effort:** 0.5-1 day

#### ⚠️ KPI Alerts (90% Complete - DISABLED)
- **File:** `kpi_alerts.sql.disabled`
- **Status:** COMPLETE but disabled
- **Features:**
  - >10% variance detection
  - Alert severity classification
  - Message generation
- **Action:** Activate and connect to Alert service
- **Effort:** 1-2 days

**dbt Gap Total:** 16-22 days of work remaining

---

### 3. AI Features (5% Complete)

#### ✅ PDF AI Extraction (100% Complete)
- **Model:** GPT-4 Vision (gpt-4o)
- **Service:** `PDFIngestionService`
- **Capabilities:** Extract production, collections, visits from day sheets
- **Quality:** 0.95 average extraction score
- **Status:** PRODUCTION READY

#### ❌ Text-to-Insights Engine (0% Complete)
- **Scope:** GPT-4 natural language summaries of KPIs
- **File:** `forecasting.py` lines 57-74 (TODO marker)
- **Required:**
  ```python
  # Example output needed:
  "Production up 12% MoM at Eastlake location, driven by increased patient visits.
   Top 3 gains: Eastlake (+$45K), Torrey Pines (+$30K), ADS (+$12K).
   Cost increases: Payroll +8% (hired 2 hygienists), Supplies +3%."
  ```
- **Implementation:**
  - Query monthly_production_kpis from Gold layer
  - Send to GPT-4 with prompt template
  - Cache results (hourly refresh)
  - Display in executive dashboard widget
- **Effort:** 2-3 days

#### ❌ Forecasting Module (5% Complete)
- **Scope:** Revenue & cost projections with confidence intervals
- **File:** `forecasting.py` lines 98-99 (TODO marker)
- **Frontend:** `ForecastingPage.tsx` (single-line placeholder)
- **Required:**
  - Snowflake ML.FORECAST() integration
  - Historical data preparation (12+ months)
  - 3-6 month revenue projection
  - Cost forecasting with seasonality
  - Confidence intervals (95%)
  - Chart visualization
- **Effort:** 4-5 days

#### ❌ Anomaly Detection (0% Complete)
- **Scope:** Statistical variance detection for alerts
- **File:** `forecasting.py` lines 125-148 (TODO marker)
- **Required:**
  - Z-score calculation (standard deviations)
  - Moving average trend detection
  - Seasonal adjustment
  - Threshold configuration (default: 2.0 sigma)
  - Alert message generation
  - Integration with Alert service
- **Effort:** 2-3 days

#### ❌ Alert Delivery (20% Complete)
- **File:** `alerts.py` - 4 TODO markers
- **Status:** Deduplication logic exists, delivery not implemented
- **Missing:**
  - Email sending (SMTP integration) - TODO line 121
  - Slack webhooks - TODO line 127
  - Custom webhook delivery - TODO line 133
  - KPI alert checking - TODO line 61
- **Effort:** 2-3 days

#### ⚠️ Schema Mapping AI (50% Complete - DISABLED)
- **File:** `schema_mapper.py`
- **Status:** LLM integration disabled (`_llm_enabled = False`)
- **Missing:**
  - GPT-4 field similarity matching
  - User feedback learning loop
  - Automatic schema detection
- **Effort:** 2 days

**AI Features Gap Total:** 12-16 days of work remaining

---

### 4. Analytics Dashboards (40% Complete)

#### ✅ Production Dashboard (100%)
- **Page:** `ProductionAnalyticsPage.tsx`
- **Features:** Daily production metrics, filters, export
- **Status:** WORKING

#### ✅ Branch Comparison (100%)
- **Page:** `BranchComparisonPage.tsx`
- **Features:** Multi-location comparison, ranking, export
- **Status:** WORKING

#### ⚠️ Financial Analytics (20%)
- **Page:** `FinancialAnalyticsPage.tsx`
- **Status:** Placeholders for AR aging, profitability
- **Missing:** NetSuite data integration, P&L, cash flow
- **Effort:** 3-4 days

#### ❌ Forecasting Dashboard (5%)
- **Page:** `ForecastingPage.tsx`
- **Status:** One-line placeholder
- **Missing:** All forecasting visualizations
- **Effort:** 3-4 days

#### ❌ Clinical Analytics (10%)
- **Page:** `ClinicalAnalyticsPage.tsx`
- **Missing:** Treatment distribution, provider productivity
- **Effort:** 3-4 days

#### ❌ Patient Analytics (10%)
- **Page:** `PatientAnalyticsPage.tsx`
- **Missing:** Acquisition funnel, retention cohorts, LTV
- **Effort:** 2-3 days

#### ❌ Staff/Scheduling Analytics (10%)
- **Pages:** `StaffAnalyticsPage.tsx`, `SchedulingAnalyticsPage.tsx`
- **Missing:** Utilization, no-show rates, efficiency metrics
- **Effort:** 3-4 days

#### ❌ Benchmarking & Reports (0%)
- **Pages:** `BenchmarkingPage.tsx`, `ReportsPage.tsx`
- **Missing:** Cross-location benchmarks, PDF reports, scheduled delivery
- **Effort:** 4-5 days

**Dashboard Gap Total:** 18-24 days of work remaining

---

## Critical Issues

### Issue #1: Data Duplication (BLOCKING)

**Problem:** Every NetSuite record duplicated 5x in Snowflake Bronze

**Root Cause:** No duplicate detection at ingestion layer
- Multiple sync runs insert same ID repeatedly
- No UNIQUE constraint on ID column
- No ON CONFLICT IGNORE/UPDATE logic

**Current Workaround:** dbt Gold layer uses MAX_BY(quality_score) to pick one record

**Impact:**
- Bronze layer: 31,315 records (should be 6,263)
- Storage waste: 5x inflation
- Query performance degradation
- Risk of incorrect metrics if dedup fails

**Required Fix:**
1. Add UNIQUE constraint to Snowflake Bronze tables:
   ```sql
   ALTER TABLE bronze.netsuite_accounts ADD CONSTRAINT unique_id UNIQUE (id);
   ```

2. Modify bulk_insert to use MERGE (upsert) instead of INSERT:
   ```sql
   MERGE INTO bronze.netsuite_accounts t
   USING (SELECT ... FROM VALUES(...)) s
   ON t.id = s.id
   WHEN MATCHED THEN UPDATE SET ...
   WHEN NOT MATCHED THEN INSERT ...
   ```

3. Add incremental sync tracking to prevent full re-syncs

**Effort:** 1-2 days

---

### Issue #2: Disabled Critical dbt Models (BLOCKING)

**Problem:** MoM growth and variance alerts models exist but are disabled

**Files:**
- `monthly_production_kpis.sql.disabled` (100% complete, just disabled)
- `kpi_alerts.sql.disabled` (100% complete, just disabled)

**Impact:**
- No month-over-month growth tracking
- No variance detection
- Forecasting can't work without historical monthly data
- Anomaly detection has no baseline

**Required Fix:**
1. Rename files (remove .disabled)
2. Run `dbt run --select monthly_production_kpis kpi_alerts`
3. Test with production data
4. Verify Gold tables populated

**Effort:** 0.5-1 day

---

### Issue #3: Missing Core Integrations (BLOCKING)

**Problem:** 3 out of 5 core integrations not implemented

**Missing:**
- DentalIntel (analytics source)
- Dentrix PMS (clinical data)
- Eaglesoft PMS (clinical data)

**Impact:**
- Can't automate data sync for 15 locations
- Requires manual PDF uploads daily
- No patient/appointment analytics
- No clinical treatment data
- Financial data incomplete (NetSuite only, no PMS reconciliation)

**Effort:** 13-18 days total

---

## Scope Alignment Matrix

| Requirement | Spec | Status | Gap |
|-------------|------|--------|-----|
| **1. Data Integration (AI-Powered)** | | | |
| ADP connector | Required | 70% Built | Not registered |
| NetSuite connector | Required | ✅ 100% | None |
| DentalIntel connector | Required | ❌ 0% | Not started |
| Dentrix PMS connector | Required | ❌ 0% | Not started |
| Eaglesoft PMS connector | Required | ❌ 0% | Not started |
| AI schema mapping | Required | ⚠️ 50% | LLM disabled |
| Automated data cleaning | Required | ⚠️ 60% | Partial in dbt |
| | | | |
| **2. Data Warehouse & Modeling** | | | |
| Bronze-Silver-Gold architecture | Required | ✅ 100% | None |
| dbt KPI models | Required | ⚠️ 50% | MoM disabled |
| Variance analysis | Required | ❌ 0% | Disabled |
| MoM trends | Required | ❌ 0% | Disabled |
| 15-location consolidation | Required | ✅ 100% | None |
| | | | |
| **3. Analytics Dashboards** | | | |
| Real-time MoM production | Required | ⚠️ 50% | MoM data missing |
| Collections dashboard | Required | ✅ 80% | Minor gaps |
| AI text-to-insights | Required | ❌ 0% | Not implemented |
| Forecasting module | Required | ❌ 5% | Stub only |
| Top gains/costs summary | Required | ❌ 0% | Not implemented |
| | | | |
| **4. Privacy-First Design** | | | |
| Aggregate reporting default | Required | ⚠️ 30% | Not enforced |
| No PHI on dashboards | Required | ⚠️ 50% | No masking |
| Role-based access | Required | ✅ 80% | Need PHI controls |
| Row-level security | Required | ⚠️ 90% | Not activated |
| | | | |
| **5. AI Automation Add-Ons** | | | |
| Weekly insights email/Slack | Required | ❌ 0% | Not implemented |
| Variance detection | Required | ❌ 0% | Model disabled |
| Anomaly alerts | Required | ❌ 0% | Not implemented |

**Overall Scope Coverage:** ~17%

---

## Prioritized Implementation Roadmap

### IMMEDIATE (P0) - Block Everything Else

**1. Fix Data Duplication (1-2 days)**
- [ ] Add UNIQUE constraints to Snowflake Bronze tables
- [ ] Implement MERGE (upsert) logic in bulk_insert
- [ ] Add incremental sync tracking
- [ ] Clean up existing duplicates

**2. Activate Disabled dbt Models (0.5-1 day)**
- [ ] Rename `monthly_production_kpis.sql.disabled` → `.sql`
- [ ] Rename `kpi_alerts.sql.disabled` → `.sql`
- [ ] Test with production data
- [ ] Verify Gold tables populated

**3. Activate Row-Level Security (0.5 day)**
- [ ] Execute `snowflake-multi-tenant-migration.sql`
- [ ] Test multi-tenant data isolation
- [ ] Document RLS setup

**Total P0 Effort:** 2-3.5 days

---

### PHASE 1: Core Integrations (P1) - Weeks 3-4

**4. Complete ADP Integration (2-3 days)**
- [ ] Register ADP in ConnectorRegistry
- [ ] Build ADP sync orchestrator
- [ ] Create dbt Silver models (employees, payroll)
- [ ] Test with production credentials
- [ ] Build Gold layer payroll metrics

**5. Build DentalIntel Integration (3-4 days)**
- [ ] Create DentalIntel connector
- [ ] Build authentication (OAuth 2.0 or API key)
- [ ] Implement data fetch endpoints
- [ ] Create Bronze/Silver dbt models
- [ ] Test with production data

**6. Build Dentrix Integration (5-7 days)**
- [ ] Investigate Dentrix API availability
- [ ] Build connector (API or CSV parser)
- [ ] Implement patient/appointment data fetch
- [ ] Create dbt Silver models
- [ ] Build Gold layer clinical metrics

**7. Build Eaglesoft Integration (5-7 days)**
- [ ] Investigate Eaglesoft API availability
- [ ] Build connector (API or CSV parser)
- [ ] Integrate with existing PDF ingestion
- [ ] Create dbt Silver models
- [ ] Consolidate with Dentrix data in Gold layer

**Total Phase 1 Effort:** 15-21 days

---

### PHASE 2: AI Features (P1) - Weeks 5-6

**8. Implement Forecasting Module (4-5 days)**
- [ ] Integrate Snowflake ML.FORECAST()
- [ ] Prepare 12+ months historical data
- [ ] Build revenue forecasting (3-6 months)
- [ ] Build cost forecasting with seasonality
- [ ] Create forecasting dashboard
- [ ] Add confidence intervals

**9. Implement Text-to-Insights (2-3 days)**
- [ ] Build GPT-4 KPI summary service
- [ ] Create natural language templates
- [ ] Implement caching (hourly refresh)
- [ ] Add dashboard widget
- [ ] Test with production KPIs

**10. Implement Anomaly Detection (2-3 days)**
- [ ] Build Z-score calculation service
- [ ] Add moving average trend detection
- [ ] Implement seasonal adjustment
- [ ] Configure thresholds (default 2.0 sigma)
- [ ] Connect to Alert service

**11. Complete Alert Delivery (2-3 days)**
- [ ] Implement SMTP email integration
- [ ] Implement Slack webhook delivery
- [ ] Build weekly insight scheduler
- [ ] Add custom webhook support
- [ ] Test alert deduplication

**Total Phase 2 Effort:** 10-14 days

---

### PHASE 3: Advanced Dashboards (P2) - Weeks 6-7

**12. Build Financial Analytics Dashboard (3-4 days)**
- [ ] Connect to NetSuite Gold layer
- [ ] P&L visualization
- [ ] Cash flow charts
- [ ] AR aging breakdown
- [ ] Budget vs actual variance

**13. Build Forecasting Dashboard (3-4 days)**
- [ ] Revenue projection charts
- [ ] Cost projection charts
- [ ] Confidence interval visualization
- [ ] Scenario planning (what-if analysis)

**14. Build Clinical/Patient Dashboards (5-6 days)**
- [ ] Treatment distribution
- [ ] Provider productivity
- [ ] Patient acquisition funnel
- [ ] Retention cohort analysis
- [ ] Appointment utilization

**15. Build Staff/Scheduling Dashboards (3-4 days)**
- [ ] Provider utilization rates
- [ ] No-show tracking
- [ ] Staff efficiency metrics
- [ ] Schedule optimization

**Total Phase 3 Effort:** 14-18 days

---

### PHASE 4: Privacy & Compliance (P2) - Week 8

**16. Implement PHI Masking (2 days)**
- [ ] Patient name masking (initials only)
- [ ] DOB/SSN masking
- [ ] Audit logging for PHI access
- [ ] HIPAA documentation

**17. Implement Aggregate-by-Default (2-3 days)**
- [ ] Role-based query filtering
- [ ] Default to aggregated views
- [ ] Explicit detail access controls

**Total Phase 4 Effort:** 4-5 days

---

## Total Remaining Effort

| Phase | Days | Priority |
|-------|-----:|----------|
| P0 (Immediate) | 2-3.5 | 🔴 Critical |
| Phase 1 (Integrations) | 15-21 | 🔴 Critical |
| Phase 2 (AI Features) | 10-14 | 🔴 Critical |
| Phase 3 (Dashboards) | 14-18 | 🟠 High |
| Phase 4 (Compliance) | 4-5 | 🟡 Medium |
| **TOTAL** | **45-61.5 days** | |

**Add 20% buffer for testing/debugging:** 54-74 days
**Calendar Time (1 FTE):** 11-15 weeks
**Calendar Time (2 FTE):** 6-8 weeks

---

## Recommendations

### Option 1: Complete MVP for Silvercreek (Recommended)

**Approach:** Focus on P0 + Phase 1 + Phase 2 only
- Fix duplication
- Complete all 5 integrations
- Activate AI features
- Defer advanced dashboards to Phase 2 release

**Timeline:** 8-10 weeks (matches revised estimate)
**Deliverables:**
- All data integration automated
- Forecasting & anomaly detection working
- Core dashboards functional
- Weekly AI insights delivered

---

### Option 2: Faster MVP with Reduced Scope

**Approach:** Ship with current features + deduplication fix
- Fix duplication (P0)
- Complete ADP + DentalIntel only (skip Dentrix/Eaglesoft)
- Use manual PDF uploads for PMS data
- Activate existing dbt models
- Build forecasting only (skip text-to-insights)

**Timeline:** 4-5 weeks
**Trade-offs:**
- Manual PMS data entry required
- No clinical analytics
- No patient analytics
- Reduced AI features

---

### Option 3: Phased Rollout (Most Realistic)

**Phase 1 (Immediate):**
- Fix P0 issues (duplication, activate dbt models, RLS)
- Launch with 3-5 pilot locations
- Timeline: 2 weeks

**Phase 2 (Integrations):**
- Complete all 5 integrations
- Build all dbt models
- Timeline: 8-10 weeks

**Phase 3 (AI & Advanced Features):**
- Forecasting, anomaly detection, text-to-insights
- Advanced dashboards
- Timeline: 6-8 weeks

**Total Timeline:** 16-20 weeks (matches realistic estimate)

---

## Next Session Action Plan

If continuing immediately, prioritize in this exact order:

1. **Fix NetSuite data duplication** (1-2 days)
   - Add UNIQUE constraints
   - Implement MERGE upsert
   - Clean existing duplicates

2. **Activate disabled dbt models** (0.5-1 day)
   - Enable monthly_production_kpis.sql
   - Enable kpi_alerts.sql
   - Test with real data

3. **Complete ADP integration** (2-3 days)
   - Register connector
   - Build sync
   - Test production sync

4. **Activate Snowflake RLS** (0.5 day)
   - Execute migration SQL
   - Test isolation

**Total: 4-6.5 days to unblock major features**

---

**Generated:** November 8, 2025
**Analysis Method:** Superpowers codebase exploration + production testing
**Data Source:** Production Snowflake warehouse + GCP deployment verification
