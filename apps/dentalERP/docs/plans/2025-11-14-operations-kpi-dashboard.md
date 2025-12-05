# Operations KPI Dashboard - Implementation Plan

**Date:** November 14, 2025
**Status:** Planning
**Priority:** High (Post-Stakeholder Demo Success)

---

## 📋 Executive Summary

Following successful stakeholder demo, the team has requested integration of their comprehensive **Monthly Operations Report** KPIs into the DentalERP analytics platform. This will eliminate manual Excel tracking and provide real-time operational insights across all 14+ practice locations.

**Current State:**
- Manual Excel report (`Operations Report(28).xlsx`) tracked monthly
- 14 practice locations monitored individually
- 21+ months of historical data (Jan 2021 - Sep 2022)
- ~60 distinct KPI metrics tracked per practice
- Time-consuming manual data entry and consolidation

**Desired State:**
- Automated KPI tracking integrated into DentalERP platform
- Real-time dashboard with drill-down capabilities
- Historical trend analysis and forecasting
- Practice-level and portfolio-level views
- Automated alerts for metrics outside target ranges

---

## 🎯 Metrics Catalog

### Analysis Source
**File:** `examples/ingestion/Operations Report(28).xlsx`
**Sheet Structure:**
- Main Sheet: "Operating Metrics" (consolidated view)
- Individual Practice Sheets: LHD, EFD I, CVFD, DSR, ADS, IPD, EFD II, RD, LSD, UCFD, LCD, EAWD, SED, DD

**Time Dimension:**
- Monthly data points
- Last Twelve Months (LTM) rolling calculations
- Date range: 2021-01 through 2022-09

---

## 📊 Complete KPI Breakdown

### 1. PRODUCTION & COLLECTIONS

#### Gross Production
- **Doctor Production** (monthly + LTM)
- **Specialty Production** (monthly + LTM)
- **Hygiene Production** (monthly + LTM)
- **Total Production** (monthly + LTM)

**Formula:** Sum of all billable services before adjustments

#### Net Production (Revenue)
- **Net Production** (monthly + LTM)
- **% of Gross Production** (adjustment rate)

**Formula:** Gross Production - Adjustments - Write-offs

#### Collections
- **Total Collections** (monthly + LTM)
- **% of Net Production** (collection rate)

**Formula:** Actual cash collected / Net Production

**🎯 Target Ranges:**
- Collection Rate: 95-100%
- Adjustment Rate: <5%

---

### 2. PATIENT VISITS

#### Doctor Visits
- **Doctor #1 Visits** (monthly + LTM)
- **Doctor #2 Visits** (monthly + LTM)
- **Total Doctor Visits** (monthly + LTM)

#### Specialist Visits
- **Specialist Visits** (monthly + LTM)

#### Hygienist Visits
- **Hygiene Visits** (monthly + LTM)

#### Total Visits
- **Combined Total** (monthly + LTM)

**🎯 Target Ranges:**
- Doctor: 300-400 visits/month per provider
- Hygiene: 80-120 visits/month per hygienist

---

### 3. GROSS PRODUCTION BY PROVIDER

#### Individual Provider Tracking
- **Doctor #1 Production** (monthly + LTM)
- **Doctor #2 Production** (monthly + LTM)
- **Specialist Production** (monthly + LTM)
- **Hygienist Production** (monthly + LTM)

**Use Case:** Provider productivity analysis, compensation planning

---

### 4. PRODUCTION PER VISIT

#### By Provider Type
- **Doctor #1 Production/Visit** (monthly + LTM)
- **Doctor #2 Production/Visit** (monthly + LTM)
- **Specialist Production/Visit** (monthly + LTM)
- **Hygienist Production/Visit** (monthly + LTM)
- **Total Production/Visit** (monthly + LTM)

**Formula:** Total Production / Total Visits

**🎯 Target Ranges:**
- Doctor: $300-$500 per visit
- Hygiene: $400-$600 per visit
- Overall: $250-$400 per visit

---

### 5. CASE ACCEPTANCE

#### Doctor #1 Metrics
- **Treatment Presented** (monthly + LTM)
- **Treatment Presented per Visit** (LTM)
- **Treatment Accepted** (monthly + LTM)
- **Acceptance Rate %** (monthly + LTM)

#### Doctor #2 Metrics
- **Treatment Presented** (monthly + LTM)
- **Treatment Presented per Visit** (LTM)
- **Treatment Accepted** (monthly + LTM)
- **Acceptance Rate %** (monthly + LTM)

**Formula:** Treatment Accepted / Treatment Presented

**🎯 Target:** 80-90% acceptance rate

**Business Impact:** Key indicator of case presentation effectiveness, treatment planning quality, patient education

---

### 6. NEW PATIENTS

- **Total New Patients** (monthly + LTM)
- **Reappointment Rate %** (patients who schedule follow-up)

**🎯 Target:**
- New patients: 30-50/month per practice
- Reappointment rate: >85%

---

### 7. RECARE (RECALL/HYGIENE EFFICIENCY)

#### Capacity Metrics
- **Hygiene Visits** (actual)
- **Hygiene Capacity** (available slots)
- **% Capacity Utilization**

**Formula:** Actual Hygiene Visits / Total Available Hygiene Slots

#### Reappointment Rate
- **% of hygiene patients who schedule next visit**

**🎯 Target:**
- Capacity Utilization: 85-95%
- Reappointment Rate: >90%

---

### 8. LABOR EFFICIENCY

#### Hygiene Productivity Ratio
- **Hygiene Net Production** (monthly)
- **Hygiene Compensation** (monthly)
- **Productivity Ratio** (production / compensation)

**Formula:** Hygiene Net Production / Hygiene Compensation

**🎯 Target:** Ratio of 2.5-3.5 (i.e., $2.50-$3.50 in production per $1 in comp)

**Business Impact:** Critical for profitability analysis, compensation structure planning

---

## 🗄️ Data Architecture

### Proposed Snowflake Schema

```sql
-- Bronze Layer: Raw Operations Data
CREATE TABLE bronze.operations_metrics_raw (
    id VARCHAR(50) PRIMARY KEY,
    practice_code VARCHAR(50) NOT NULL,
    practice_name VARCHAR(100),
    report_month DATE NOT NULL,
    metric_category VARCHAR(100),
    metric_name VARCHAR(100),
    metric_value DECIMAL(18,2),
    metric_type VARCHAR(20), -- 'monthly', 'ltm', 'ratio', 'percent'
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    source_file VARCHAR(200),
    CONSTRAINT unique_metric_month UNIQUE (practice_code, report_month, metric_category, metric_name)
);

-- Silver Layer: Cleaned & Typed Metrics
CREATE TABLE silver.operations_metrics (
    id VARCHAR(50) PRIMARY KEY,
    practice_code VARCHAR(50) NOT NULL,
    practice_name VARCHAR(100),
    report_month DATE NOT NULL,

    -- Production & Collections
    gross_production_doctor DECIMAL(18,2),
    gross_production_specialty DECIMAL(18,2),
    gross_production_hygiene DECIMAL(18,2),
    gross_production_total DECIMAL(18,2),
    net_production DECIMAL(18,2),
    collections DECIMAL(18,2),
    collection_rate_pct DECIMAL(5,2),
    adjustment_rate_pct DECIMAL(5,2),

    -- Patient Visits
    visits_doctor_1 INT,
    visits_doctor_2 INT,
    visits_doctors_total INT,
    visits_specialists INT,
    visits_hygiene INT,
    visits_total INT,

    -- Production Per Visit
    ppv_doctor_1 DECIMAL(10,2),
    ppv_doctor_2 DECIMAL(10,2),
    ppv_doctors_avg DECIMAL(10,2),
    ppv_specialists DECIMAL(10,2),
    ppv_hygiene DECIMAL(10,2),
    ppv_overall DECIMAL(10,2),

    -- Case Acceptance (Doctor #1)
    doc1_treatment_presented DECIMAL(18,2),
    doc1_treatment_accepted DECIMAL(18,2),
    doc1_acceptance_rate_pct DECIMAL(5,2),

    -- Case Acceptance (Doctor #2)
    doc2_treatment_presented DECIMAL(18,2),
    doc2_treatment_accepted DECIMAL(18,2),
    doc2_acceptance_rate_pct DECIMAL(5,2),

    -- New Patients
    new_patients_total INT,
    new_patients_reappointment_rate_pct DECIMAL(5,2),

    -- Recare
    hygiene_capacity_slots INT,
    hygiene_capacity_utilization_pct DECIMAL(5,2),
    hygiene_reappointment_rate_pct DECIMAL(5,2),

    -- Labor Efficiency
    hygiene_net_production DECIMAL(18,2),
    hygiene_compensation DECIMAL(18,2),
    hygiene_productivity_ratio DECIMAL(5,2),

    -- LTM (Last Twelve Months) Aggregates
    ltm_gross_production DECIMAL(18,2),
    ltm_net_production DECIMAL(18,2),
    ltm_collections DECIMAL(18,2),
    ltm_visits_total INT,

    -- Metadata
    data_quality_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Gold Layer: Analytics-Ready KPIs
CREATE TABLE gold.operations_kpis_monthly (
    id VARCHAR(50) PRIMARY KEY,
    practice_code VARCHAR(50) NOT NULL,
    practice_name VARCHAR(100),
    report_month DATE NOT NULL,

    -- Core Financial KPIs
    total_production DECIMAL(18,2),
    total_collections DECIMAL(18,2),
    collection_efficiency_score DECIMAL(5,2), -- Composite score 0-100

    -- Productivity KPIs
    total_patient_visits INT,
    avg_production_per_visit DECIMAL(10,2),
    provider_productivity_score DECIMAL(5,2), -- Composite score 0-100

    -- Growth KPIs
    new_patient_count INT,
    new_patient_conversion_rate DECIMAL(5,2),
    patient_retention_score DECIMAL(5,2), -- Based on reappointment rates

    -- Operational Efficiency KPIs
    capacity_utilization_pct DECIMAL(5,2),
    labor_efficiency_ratio DECIMAL(5,2),
    operational_efficiency_score DECIMAL(5,2), -- Composite score 0-100

    -- Clinical Quality KPIs
    case_acceptance_rate_avg DECIMAL(5,2),
    treatment_planning_effectiveness DECIMAL(5,2),

    -- Benchmarking Flags
    is_above_target_production BOOLEAN,
    is_above_target_collections BOOLEAN,
    is_above_target_efficiency BOOLEAN,

    -- Trends (vs previous month)
    production_trend_pct DECIMAL(6,2),
    collections_trend_pct DECIMAL(6,2),
    visits_trend_pct DECIMAL(6,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Create indexes for performance
CREATE INDEX idx_ops_metrics_practice_month ON silver.operations_metrics(practice_code, report_month);
CREATE INDEX idx_ops_kpis_practice_month ON gold.operations_kpis_monthly(practice_code, report_month);
```

---

## 🔄 Data Ingestion Strategy

### Phase 1: Historical Data Load (Excel Import)

**Input:** `Operations Report(28).xlsx` (and subsequent monthly reports)

**Process:**
```python
# MCP Server: /src/services/operations_excel_parser.py

class OperationsReportParser:
    """Parse SCDP Monthly Operations Report Excel files"""

    def parse_operations_report(self, file_path: str) -> List[Dict]:
        """
        Extract all metrics from Excel file

        Returns:
            List of metric dictionaries with:
            - practice_code
            - practice_name
            - report_month
            - metric_category
            - metric_name
            - metric_value
            - metric_type
        """

    def load_to_snowflake(self, metrics: List[Dict]):
        """Bulk insert to bronze.operations_metrics_raw"""

    def trigger_dbt_transformations(self):
        """Run silver and gold layer transformations"""
```

**Endpoint:**
```
POST /api/v1/operations/upload
Content-Type: multipart/form-data

Body:
- file: operations_report.xlsx
- report_month: 2024-11-01
```

### Phase 2: Automated Data Collection

**Sources (in priority order):**

1. **PMS Day Sheet Integration** (Primary)
   - Production data from Dentrix/Eaglesoft
   - Patient visit counts
   - Provider-level detail

2. **NetSuite ERP** (Financial)
   - Collections (already integrated)
   - Revenue recognition
   - Compensation data

3. **Practice Management Reports** (Operational)
   - Case acceptance from PMS
   - New patient tracking
   - Appointment scheduling data

4. **HR/Payroll Systems** (Labor)
   - Provider compensation (ADP integration)
   - Hours worked
   - Productivity calculations

**Automation Schedule:**
- Daily: Production & collections sync
- Weekly: Operational metrics refresh
- Monthly: Full KPI calculation and LTM roll-up

---

## 📈 Frontend Dashboard Design

### Operations KPI Dashboard Page

**Route:** `/analytics/operations`

**Layout:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  OPERATIONS OVERVIEW                           [Month Selector ▼]   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  📊 KEY METRICS (Current Month vs Target vs LTM)                    │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐      │
│  │ Production   │ Collections  │ Patient      │ Efficiency   │      │
│  │ $1.2M        │ $1.15M       │ Visits       │ Score        │      │
│  │ ↑ 8% vs LTM  │ ↑ 5% vs LTM  │ 1,234        │ 87/100       │      │
│  │ Target: 95%  │ Target: 98%  │ ↑ 3% vs LTM  │ ↑ 2 pts      │      │
│  └──────────────┴──────────────┴──────────────┴──────────────┘      │
│                                                                      │
│  📈 PRODUCTION TRENDS (12-month chart)                              │
│  [Line chart: Gross Production vs Net Production vs Collections]    │
│                                                                      │
│  👥 PROVIDER PRODUCTIVITY                                            │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ Provider     │ Visits │ Production │ Prod/Visit │ vs Target│     │
│  ├────────────────────────────────────────────────────────────┤     │
│  │ Dr. Smith    │   342  │  $425,000  │   $1,243   │ ✅ +8%   │     │
│  │ Dr. Jones    │   298  │  $398,000  │   $1,336   │ ✅ +12%  │     │
│  │ Dr. Wilson   │   156  │  $198,000  │   $1,269   │ ⚠️ -2%   │     │
│  │ Hygiene Team │   890  │  $445,000  │     $500   │ ✅ +5%   │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  💼 CASE ACCEPTANCE                                                  │
│  [Funnel chart: Presented → Accepted]                               │
│  - Treatment Presented: $1.8M                                        │
│  - Treatment Accepted: $1.5M                                         │
│  - Acceptance Rate: 83% (Target: 85%)                                │
│                                                                      │
│  🆕 NEW PATIENT ACQUISITION                                          │
│  [Bar chart: Monthly new patients + reappointment rate]             │
│                                                                      │
│  🔄 HYGIENE RECARE EFFICIENCY                                        │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ Capacity Utilization: 91% (Target: 85-95%)                 │     │
│  │ Reappointment Rate: 94% (Target: >90%)                     │     │
│  │ Productivity Ratio: 2.8 (Target: 2.5-3.5)                  │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  🏥 PRACTICE COMPARISON                                              │
│  [Table with all 14 practices, sortable by any metric]              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Filters:**
- Practice selector (single or multi-select)
- Date range (month, quarter, YTD, custom)
- Provider filter
- Metric category tabs

**Export Options:**
- PDF Executive Summary
- Excel detailed report
- CSV raw data
- Scheduled email reports

---

## 🔧 Implementation Phases

### Phase 1: Data Foundation (Week 1-2)
**Priority: CRITICAL**

- [ ] Create Snowflake tables (bronze, silver, gold)
- [ ] Build Excel parser for Operations Report
- [ ] Load historical data (21 months: Jan 2021 - Sep 2022)
- [ ] Create dbt transformations (bronze → silver → gold)
- [ ] Validate data accuracy against source Excel

**Deliverables:**
- `bronze.operations_metrics_raw` populated
- `silver.operations_metrics` with clean data
- `gold.operations_kpis_monthly` with calculated KPIs
- Data quality report

---

### Phase 2: API Development (Week 3)
**Priority: HIGH**

- [ ] Create operations analytics API endpoints
  - `GET /api/v1/operations/kpis/summary`
  - `GET /api/v1/operations/kpis/monthly`
  - `GET /api/v1/operations/providers/productivity`
  - `GET /api/v1/operations/practices/comparison`
- [ ] Build Excel upload endpoint
- [ ] Implement caching strategy
- [ ] Add API documentation

**Deliverables:**
- 4-6 RESTful API endpoints
- Swagger/OpenAPI docs
- Integration tests

---

### Phase 3: Frontend Dashboard (Week 4-5)
**Priority: HIGH**

- [ ] Create `/analytics/operations` page
- [ ] Build KPI summary cards
- [ ] Implement production trends chart
- [ ] Add provider productivity table
- [ ] Build case acceptance funnel
- [ ] Create practice comparison table
- [ ] Add export functionality (PDF, Excel, CSV)

**Deliverables:**
- Fully functional Operations Dashboard
- Mobile-responsive design
- Interactive charts and filters

---

### Phase 4: Automation & Integration (Week 6-8)
**Priority: MEDIUM**

- [ ] Integrate with PMS for automated production data
- [ ] Connect to NetSuite for collections data
- [ ] Build ADP integration for compensation data
- [ ] Create automated monthly report generation
- [ ] Implement alerting for metrics outside target range
- [ ] Add forecasting models (ML-based predictions)

**Deliverables:**
- Automated data pipeline
- Email alerts for anomalies
- Predictive analytics

---

### Phase 5: Advanced Analytics (Future)
**Priority: LOW**

- [ ] Benchmark data integration (industry standards)
- [ ] Cohort analysis (patient lifetime value)
- [ ] Predictive modeling (revenue forecasting)
- [ ] Automated insights (AI-generated summaries)
- [ ] Mobile app (iOS/Android)

---

## 🎯 Success Metrics

### Technical KPIs
- **Data Accuracy:** 99.9% match with source Excel
- **API Response Time:** <500ms for dashboard queries
- **Dashboard Load Time:** <2 seconds
- **Data Freshness:** Daily automated updates

### Business KPIs
- **Time Savings:** Eliminate 8-10 hours/month manual reporting
- **Adoption Rate:** 80%+ of executives use dashboard weekly
- **Insight Quality:** 5+ actionable insights surfaced per month
- **Decision Speed:** 50% faster operational decision-making

---

## 📊 Sample API Responses

### GET /api/v1/operations/kpis/summary

```json
{
  "practice_code": "eastlake",
  "practice_name": "Eastlake Dental",
  "report_month": "2024-11-01",
  "kpis": {
    "financial": {
      "total_production": 1250000.00,
      "total_collections": 1187500.00,
      "collection_rate": 95.0,
      "vs_target": {
        "production": 8.5,
        "collections": 5.2
      },
      "vs_ltm": {
        "production": 12.3,
        "collections": 9.8
      }
    },
    "productivity": {
      "total_visits": 1234,
      "avg_production_per_visit": 1012.95,
      "provider_productivity_score": 87,
      "vs_ltm": {
        "visits": 5.3,
        "ppv": 6.7
      }
    },
    "growth": {
      "new_patients": 45,
      "new_patient_conversion_rate": 88.5,
      "patient_retention_score": 92,
      "vs_ltm": {
        "new_patients": 12.5
      }
    },
    "efficiency": {
      "capacity_utilization": 91.2,
      "labor_efficiency_ratio": 2.8,
      "operational_efficiency_score": 89,
      "hygiene_productivity_ratio": 2.75
    },
    "clinical": {
      "case_acceptance_rate": 83.5,
      "treatment_planning_effectiveness": 85.2
    }
  },
  "alerts": [
    {
      "severity": "warning",
      "metric": "case_acceptance_rate",
      "message": "Below target of 85% (currently 83.5%)",
      "recommendation": "Review case presentation training"
    }
  ],
  "trends": {
    "production_trend_pct": 8.5,
    "collections_trend_pct": 5.2,
    "visits_trend_pct": 3.1
  },
  "generated_at": "2024-11-14T10:30:00Z"
}
```

---

## 🔐 Security & Compliance

- **Data Access:** Role-based (Executive, Regional Manager, Practice Manager)
- **PHI Protection:** No patient-identifiable information in operations metrics
- **Audit Trail:** All data access logged
- **Data Retention:** 7 years minimum for financial compliance

---

## 📝 Notes & Considerations

1. **Practice Name Mapping:**
   - Need to map Excel sheet names (LHD, EFD I, etc.) to our practice codes
   - Create `practices_mapping` table for reference

2. **Provider Identification:**
   - "Doctor #1", "Doctor #2" are placeholders
   - Need actual provider names from HR system
   - Consider anonymization for benchmarking

3. **LTM Calculations:**
   - Rolling 12-month window
   - Handle partial months for current period
   - Ensure consistency with manual Excel calculations

4. **Target Setting:**
   - Initial targets from industry benchmarks
   - Allow practice-specific target customization
   - Implement target escalation over time

5. **Data Gaps:**
   - Plan for missing data handling
   - Imputation strategies for incomplete months
   - Quality scoring for reliability indicators

---

## 📅 Timeline Summary

| Phase | Duration | Start | End | Status |
|-------|----------|-------|-----|--------|
| Phase 1: Data Foundation | 2 weeks | Week 1 | Week 2 | 🟡 Planning |
| Phase 2: API Development | 1 week | Week 3 | Week 3 | ⚪ Not Started |
| Phase 3: Frontend Dashboard | 2 weeks | Week 4 | Week 5 | ⚪ Not Started |
| Phase 4: Automation | 3 weeks | Week 6 | Week 8 | ⚪ Not Started |
| Phase 5: Advanced Analytics | TBD | Future | Future | ⚪ Not Started |

**Total Estimated Time:** 8 weeks for full implementation (Phases 1-4)

---

## ✅ Next Steps

1. **Immediate (This Week):**
   - Get approval for plan from stakeholders
   - Map practice codes (LHD → eastlake, etc.)
   - Obtain provider names for Doctor #1, Doctor #2 mappings
   - Validate target ranges with clinical leadership

2. **Week 1:**
   - Create Snowflake tables
   - Build Excel parser
   - Begin historical data load

3. **Ongoing:**
   - Weekly sync with operations team
   - Monthly review of KPI accuracy
   - Quarterly target review and adjustment

---

## 🤖 AI-POWERED & ADVANCED METRICS (Beyond Current Report)

### Executive Summary

The current Operations Report tracks **lagging indicators** (what already happened). With DentalERP's AI capabilities, we can add **leading indicators** (predict what will happen) and **prescriptive analytics** (what to do about it).

---

### 🎯 New KPIs Enabled by AI/ML

#### 1. PREDICTIVE PRODUCTION FORECASTING

**Current Report:** Shows last month's production
**AI Enhancement:** Predicts next 3-6 months production with confidence intervals

```sql
-- Leverage Snowflake ML.FORECAST
CREATE OR REPLACE MODEL gold.production_forecast_model
FROM gold.operations_kpis_monthly
PREDICT total_production
USING (
    type = 'SEASONAL_ARIMA',
    seasonal_periods = 12,
    exogenous_variables = ['new_patients_count', 'case_acceptance_rate_pct']
);
```

**New Metrics:**
- **Forecasted Production** (next month, quarter, year)
- **Production Trend Direction** (improving/declining/stable)
- **Confidence Score** (how reliable is the forecast)
- **Risk Score** (probability of missing budget targets)

**Business Value:**
- Proactive staffing decisions
- Early identification of revenue shortfalls
- Better cash flow planning
- Informed marketing spend decisions

---

#### 2. PATIENT LIFETIME VALUE (LTV) PREDICTION

**Current Report:** Counts new patients, tracks reappointment rate
**AI Enhancement:** Predicts total revenue per patient over their lifetime

**Calculation:**
```python
Patient LTV = (Avg Treatment Value) × (Visit Frequency) × (Patient Lifespan) × (Referral Factor)

With AI:
- Predict visit frequency based on patient profile
- Predict churn probability by demographics
- Predict treatment acceptance likelihood
- Predict referral probability
```

**New Metrics:**
- **Patient LTV Score** (predicted lifetime value per patient)
- **High-Value Patient Percentage** (LTV > $10K)
- **Patient Churn Risk Score** (0-100, likelihood of leaving)
- **New Patient ROI** (acquisition cost vs predicted LTV)

**Business Value:**
- Focus marketing on high-LTV patient demographics
- Prioritize retention efforts on at-risk high-value patients
- Justify marketing spend with LTV data
- Personalize patient communication based on predicted behavior

---

#### 3. CASE ACCEPTANCE OPTIMIZATION

**Current Report:** Tracks acceptance rate %
**AI Enhancement:** Identifies WHY cases are accepted/rejected and predicts success factors

**New Metrics:**
- **Optimal Treatment Value Range** (sweet spot for acceptance)
- **Provider Acceptance Score** (adjusted for case complexity)
- **Time-of-Day Acceptance Pattern** (best time to present cases)
- **Patient Demographic Acceptance Profile** (age, income, insurance type)
- **Treatment Type Acceptance Trends** (cosmetic vs restorative)

**AI Insights:**
- "Dr. Smith's acceptance rate drops 15% for cases >$5K - recommend payment plans"
- "Tuesday morning presentations have 12% higher acceptance than Friday afternoon"
- "Patients aged 35-50 with PPO insurance have 85% acceptance for cosmetic work"

**Business Value:**
- Increase acceptance rate by 5-10% through data-driven presentation
- Optimize scheduling for case presentations
- Train providers on weak areas
- Tailor financing options to patient segments

---

#### 4. HYGIENE REVENUE OPTIMIZATION

**Current Report:** Tracks productivity ratio (production/compensation)
**AI Enhancement:** Predicts optimal scheduling and identifies revenue leakage

**New Metrics:**
- **Recare Gap Score** (patients overdue for hygiene, ranked by value)
- **Optimal Hygiene Utilization** (ML-predicted best capacity %)
- **Revenue Leakage** (missed hygiene opportunities $)
- **Hygiene Upsell Rate** (% hygiene visits leading to restorative work)
- **Ideal Hygiene Visit Duration** (maximize revenue per hour)

**AI Insights:**
- "547 patients overdue for hygiene = $82K revenue opportunity"
- "Reducing hygiene appointments from 60min to 50min increases daily revenue by $150"
- "Hygienist Sarah has 23% restorative referral rate vs 12% team average"

**Business Value:**
- Recover lost revenue from overdue patients
- Optimize hygiene scheduling for maximum revenue
- Identify top-performing hygienists for training others
- Reduce no-shows with predictive outreach

---

#### 5. PROVIDER EFFICIENCY SCORING (AI-ADJUSTED)

**Current Report:** Production per visit, visits per month
**AI Enhancement:** Adjusts for case complexity, patient mix, and external factors

**New Metrics:**
- **Complexity-Adjusted Production** (accounts for case difficulty)
- **Patient Mix Score** (impact of insurance mix on production)
- **Time-to-Treatment Score** (efficiency of chair time)
- **No-Show Impact** (lost production due to cancellations)
- **Optimal Schedule Score** (how well actual schedule matches ideal)

**Example:**
```
Dr. Jones: $125K production, 300 visits = $417/visit (seems low)
AI Adjustment:
- 65% Medicaid patients (-25% avg reimbursement)
- 18% complex cases requiring 2x time (+complexity factor)
- 12% no-show rate (-$15K lost production)
Adjusted Production/Visit: $523 (actually above target!)
```

**Business Value:**
- Fair performance evaluation accounting for patient mix
- Identify systemic issues (insurance mix, scheduling) vs provider issues
- Data-driven compensation models
- Optimize provider schedules by patient type

---

#### 6. ANOMALY DETECTION & AUTOMATED ALERTS

**Current Report:** Manual review of monthly numbers
**AI Enhancement:** Automatic detection of unusual patterns with root cause analysis

**New Alerts:**
- **Production Anomaly Alert:** "Eastlake production down 18% vs 90-day avg - investigate"
- **Case Acceptance Drop:** "Dr. Wilson acceptance rate dropped to 72% (usual 85%) - review last 20 cases"
- **Hygiene Utilization Warning:** "Hygiene capacity at 68% (target 85%) - schedule recall blitz"
- **New Patient Trend:** "New patient count declining 3 months straight - marketing issue?"
- **Collection Rate Issue:** "Collections at 88% (target 95%) - billing backlog detected"

**AI Root Cause Suggestions:**
- Correlation analysis: "Production drop correlates with Dr. Smith vacation week"
- Pattern matching: "Similar drop occurred last December - seasonal effect"
- Outlier detection: "3 large cases rescheduled - not a systemic issue"

**Business Value:**
- Catch problems before they become crises
- Automated monitoring vs manual review
- Faster response time to operational issues
- Data-driven problem diagnosis

---

#### 7. PATIENT FLOW OPTIMIZATION

**Current Report:** Total visit count
**AI Enhancement:** Identifies bottlenecks and optimizes patient flow

**New Metrics:**
- **Appointment Utilization Score** (actual vs optimal scheduling)
- **Provider Idle Time %** (revenue lost to gaps in schedule)
- **Patient Wait Time Impact** (effect on satisfaction and no-shows)
- **Optimal Appointment Mix** (new vs existing, procedure types)
- **Same-Day Opening Fill Rate** (ability to fill cancellations)

**AI Insights:**
- "Mondays have 15% no-show rate - overbook by 2 appointments"
- "Hygiene openings at 2pm typically go unfilled - offer to existing patients first"
- "Spacing new patient exams at 9am and 2pm reduces wait times by 12 minutes"

**Business Value:**
- Maximize provider utilization
- Reduce patient wait times
- Fill last-minute cancellations
- Optimize daily schedule templates

---

#### 8. TREATMENT PLAN CONVERSION FUNNEL

**Current Report:** Treatment presented, treatment accepted
**AI Enhancement:** Track full conversion funnel with drop-off analysis

**New Metrics:**
- **Diagnosis to Presentation Rate** (% diagnosed issues presented)
- **Presentation to Acceptance Rate** (current metric)
- **Acceptance to Scheduling Rate** (% accepted cases scheduled)
- **Scheduling to Completion Rate** (% scheduled cases completed)
- **Overall Conversion Rate** (diagnosis → completed treatment)

**Funnel Example:**
```
100 Issues Diagnosed
 ↓ 85% → 85 Presented to Patient
 ↓ 80% → 68 Accepted by Patient
 ↓ 75% → 51 Scheduled
 ↓ 90% → 46 Completed

Overall Conversion: 46% (46/100)
Biggest Drop: Acceptance to Scheduling (25% loss = $XXK revenue)
```

**AI Insights:**
- "51% of accepted cases not scheduled within 30 days - implement auto-scheduling"
- "Patients who don't schedule within 7 days have 60% probability of never scheduling"

**Business Value:**
- Identify where revenue is being lost in the funnel
- Focus improvement efforts on biggest drop-off points
- Recover lost revenue with targeted interventions

---

#### 9. COMPETITIVE BENCHMARKING (EXTERNAL DATA)

**Current Report:** Internal metrics only
**AI Enhancement:** Compare to regional and national benchmarks

**New Metrics:**
- **Percentile Ranking** (vs similar practices nationally)
- **Market Share Estimate** (based on zip code demographics)
- **Pricing Competitiveness Score** (vs local competitors)
- **Service Gap Analysis** (services offered vs market demand)

**Data Sources:**
- ADA industry benchmarks
- Dental Intelligence network data
- Public insurance claim data
- Census demographic data

**Example Dashboard:**
```
Production/Visit: $425 (78th percentile - good!)
Case Acceptance: 83% (52nd percentile - opportunity)
Hygiene Utilization: 91% (89th percentile - excellent!)
New Patient Rate: 32/month (45th percentile - below average)
```

**Business Value:**
- Understand competitive position
- Identify improvement opportunities vs peers
- Set data-driven targets
- Validate performance ("good for our market" vs "good overall")

---

#### 10. REVENUE ATTRIBUTION & MARKETING ROI

**Current Report:** New patient count
**AI Enhancement:** Track patient source and lifetime value by marketing channel

**New Metrics:**
- **Patient Acquisition Cost by Channel** (Google Ads, Referrals, Insurance, etc.)
- **Marketing ROI by Channel** (LTV / Acquisition Cost)
- **Referral Source Value** (which patients refer high-value patients?)
- **Campaign Effectiveness Score** (conversions per $ spent)
- **Organic vs Paid Patient Value** (do paid patients stay longer?)

**Example Analysis:**
```
Channel          | New Patients | Avg LTV | Acq Cost | ROI
Google Ads       | 12           | $4,500  | $250     | 18x
Patient Referral | 8            | $6,200  | $50      | 124x
Insurance List   | 15           | $2,800  | $75      | 37x
Social Media     | 5            | $3,100  | $180     | 17x
```

**AI Insights:**
- "Patient referrals have 124x ROI - invest in referral program"
- "Google Ads patients have 30% higher churn rate than referrals"
- "Insurance list patients lowest LTV but highest volume - balance needed"

**Business Value:**
- Optimize marketing budget allocation
- Understand true patient acquisition costs
- Double down on highest-ROI channels
- Calculate breakeven for new marketing initiatives

---

#### 11. SEASONAL TREND & CAPACITY PLANNING

**Current Report:** Monthly snapshots, manual YoY comparison
**AI Enhancement:** Predict seasonal patterns and optimize capacity

**New Metrics:**
- **Seasonal Index by Month** (predicted vs actual demand)
- **Capacity Forecast** (predicted utilization next 90 days)
- **Staff Optimization Recommendation** (add/reduce hours when)
- **Inventory Prediction** (supplies needed based on forecasted procedures)

**AI Insights:**
- "December production typically drops 15% - reduce staff hours by 10%"
- "Back-to-school surge in September - add 2 hygiene days/week in August"
- "Cosmetic procedures spike Q1 (tax refunds) - pre-book now for 95% capacity"

**Business Value:**
- Proactive staffing adjustments
- Reduce excess inventory costs
- Maximize revenue during peak periods
- Minimize costs during slow periods

---

#### 12. PATIENT SATISFACTION & NET PROMOTER SCORE (NPS)

**Current Report:** Not tracked
**AI Enhancement:** Automated sentiment analysis and NPS tracking

**New Metrics:**
- **Net Promoter Score (NPS)** (-100 to +100, industry standard)
- **Patient Satisfaction Score** (1-10 scale, post-visit survey)
- **Review Sentiment Score** (AI analysis of online reviews)
- **Complaint Rate** (tracked complaints per 100 visits)
- **Response Time Score** (how quickly issues are addressed)

**AI Sentiment Analysis:**
```
Online Review: "Great dentist but waited 45 minutes"
AI Tags: [positive: dentist quality], [negative: wait time]
Action: Flag for operations team → improve scheduling

Correlation Analysis:
- Practices with NPS >50 have 15% higher patient retention
- 1-point NPS increase = 3.2% increase in referrals
```

**Business Value:**
- Early warning system for patient dissatisfaction
- Link satisfaction to financial outcomes
- Identify service issues before they spread
- Benchmark patient experience vs competitors

---

### 📊 Advanced Dashboard Concepts

#### Executive AI Insights Dashboard

**Daily AI-Generated Insights:**
```
🎯 TOP OPPORTUNITIES TODAY:
1. 127 overdue hygiene patients = $19K revenue opportunity
2. Dr. Smith's 2pm slot empty - suggest overbooking by 1
3. Case acceptance trending down 5% this week - investigate

⚠️ RISKS TO WATCH:
1. New patient count down 3 months - marketing review needed
2. Collections at 91% (target 95%) - billing backlog detected
3. Hygiene utilization 73% (target 85%) - schedule recall campaign

📈 PREDICTIONS:
1. Next month production forecast: $285K (±$15K confidence)
2. Year-end forecast: $3.2M (98% confidence of hitting $3M target)
3. Q1 2026 new patient forecast: 145 (seasonal increase expected)
```

#### AI-Powered Practice Scorecard

```
PRACTICE HEALTH SCORE: 87/100 (Good)

Financial Health:     92/100 ✅ (Production trending up)
Operational Health:   84/100 ✅ (Minor capacity issues)
Patient Health:       88/100 ✅ (High satisfaction, stable retention)
Growth Health:        81/100 ⚠️  (New patient acquisition slowing)

AI RECOMMENDATION:
Focus on new patient marketing (+15% investment recommended)
Projected Impact: +25 patients/month, +$112K annual revenue
```

---

### 🎯 Implementation Priority

**Phase 1: Quick Wins (Weeks 1-4)**
1. ✅ Anomaly detection & alerts
2. ✅ Production forecasting (Snowflake ML.FORECAST)
3. ✅ Recare gap analysis
4. ✅ Treatment funnel tracking

**Phase 2: Advanced Analytics (Months 2-3)**
5. Patient LTV prediction
6. Provider efficiency scoring (complexity-adjusted)
7. Competitive benchmarking
8. Marketing ROI attribution

**Phase 3: Predictive & Prescriptive (Months 4-6)**
9. Optimal scheduling recommendations
10. Churn risk prediction
11. Dynamic pricing optimization
12. Capacity planning automation

---

### 💡 Data Requirements for AI Metrics

**Already Have:**
- ✅ Production data (from PMS day sheets)
- ✅ Financial data (from NetSuite)
- ✅ Visit counts (from operations report)
- ✅ Case acceptance (from operations report)

**Need to Add:**
- 📊 Patient demographics (age, insurance type, zip code)
- 📊 Appointment scheduling data (scheduled vs completed, cancellations)
- 📊 Treatment plan details (procedure codes, values, dates)
- 📊 Patient feedback (surveys, NPS scores)
- 📊 Marketing source tracking (how patients found the practice)
- 📊 Online review data (Google, Yelp, Healthgrades)

**Can Integrate From:**
- PMS system (Dentrix, Eaglesoft) - patient data, appointments, treatment plans
- Survey tools (NiceJob, Solutionreach) - satisfaction scores
- Google My Business API - reviews and ratings
- Marketing platforms (Google Ads, Facebook Ads) - campaign data

---

### 🚀 Competitive Advantages

**Traditional Operations Report:**
- ❌ Backward-looking (shows what happened)
- ❌ Manual analysis required
- ❌ No predictions or recommendations
- ❌ Internal metrics only
- ❌ Monthly lag time

**AI-Powered DentalERP:**
- ✅ Forward-looking (predicts what will happen)
- ✅ Automated insights and alerts
- ✅ Prescriptive recommendations (what to do)
- ✅ Competitive benchmarking included
- ✅ Real-time or daily updates
- ✅ Mobile access anytime, anywhere

---

**Document Owner:** Development Team
**Stakeholder:** Operations Leadership, Practice Managers
**Review Cycle:** Bi-weekly during implementation

---

**Last Updated:** November 14, 2025
**Next Review:** November 21, 2025
