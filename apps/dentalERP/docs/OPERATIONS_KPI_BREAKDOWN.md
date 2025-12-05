# Operations KPI Dashboard - Metrics Breakdown

**Date:** November 14, 2025

---

## 📊 PHASE 1: Automate Existing Operations Report (3-4 Weeks)

### Objective
Replace manual Excel tracking with automated real-time dashboard. **Zero new metrics** - just automate what they already track.

---

### 1. PRODUCTION & COLLECTIONS (8 Metrics)

| Metric | Current (Excel) | Phase 1 (Automated) |
|--------|----------------|---------------------|
| **Gross Production - Doctor** | Manual entry | ✅ Auto-calculated from PMS/NetSuite |
| **Gross Production - Specialty** | Manual entry | ✅ Auto-calculated |
| **Gross Production - Hygiene** | Manual entry | ✅ Auto-calculated |
| **Total Gross Production** | Excel SUM formula | ✅ Auto-calculated |
| **Net Production (Revenue)** | Manual entry | ✅ Auto-calculated (Gross - Adjustments) |
| **Total Collections** | Manual entry | ✅ Auto-calculated from NetSuite |
| **Collection Rate %** | Excel formula | ✅ Auto-calculated (Collections / Net Production) |
| **Last Twelve Months (LTM)** | Excel rolling sum | ✅ Auto-calculated with SQL window functions |

**Enhancement:** Real-time updates vs monthly manual entry

---

### 2. PATIENT VISITS (5 Metrics)

| Metric | Current (Excel) | Phase 1 (Automated) |
|--------|----------------|---------------------|
| **Doctor Visits - Provider #1** | Manual count | ✅ Auto-counted from PMS |
| **Doctor Visits - Provider #2** | Manual count | ✅ Auto-counted from PMS |
| **Specialist Visits** | Manual count | ✅ Auto-counted from PMS |
| **Hygiene Visits** | Manual count | ✅ Auto-counted from PMS |
| **Total Patient Visits** | Excel SUM | ✅ Auto-calculated |
| **Last Twelve Months (LTM)** | Excel rolling sum | ✅ Auto-calculated |

**Enhancement:** Daily updates vs monthly aggregation

---

### 3. PRODUCTION PER VISIT (6 Metrics)

| Metric | Current (Excel) | Phase 1 (Automated) |
|--------|----------------|---------------------|
| **Doctor #1 Production/Visit** | Excel formula | ✅ Auto-calculated (Production / Visits) |
| **Doctor #2 Production/Visit** | Excel formula | ✅ Auto-calculated |
| **Specialist Production/Visit** | Excel formula | ✅ Auto-calculated |
| **Hygiene Production/Visit** | Excel formula | ✅ Auto-calculated |
| **Overall Production/Visit** | Excel formula | ✅ Auto-calculated |
| **Last Twelve Months (LTM)** | Excel rolling avg | ✅ Auto-calculated |

**Enhancement:** Visual trend charts, practice comparisons

---

### 4. CASE ACCEPTANCE (6 Metrics per Provider)

| Metric | Current (Excel) | Phase 1 (Automated) |
|--------|----------------|---------------------|
| **Treatment Presented** | Manual entry | ✅ Auto-tracked from PMS |
| **Treatment Presented/Visit** | Excel formula | ✅ Auto-calculated |
| **Treatment Accepted** | Manual entry | ✅ Auto-tracked from PMS |
| **Acceptance Rate %** | Excel formula | ✅ Auto-calculated (Accepted / Presented) |
| **Last Twelve Months (LTM)** | Excel rolling totals | ✅ Auto-calculated |

**Tracked for:** Each individual provider (Doctor #1, Doctor #2, etc.)

**Enhancement:** Provider ranking, trend alerts

---

### 5. NEW PATIENT ACQUISITION (2 Metrics)

| Metric | Current (Excel) | Phase 1 (Automated) |
|--------|----------------|---------------------|
| **Total New Patients** | Manual count | ✅ Auto-counted from PMS |
| **Reappointment Rate %** | Manual tracking | ✅ Auto-calculated (scheduled follow-up / total new) |

**Enhancement:** New patient trend graphs, month-over-month comparison

---

### 6. HYGIENE EFFICIENCY (5 Metrics)

| Metric | Current (Excel) | Phase 1 (Automated) |
|--------|----------------|---------------------|
| **Hygiene Visits** | Manual count | ✅ Auto-counted from PMS |
| **Hygiene Capacity (slots)** | Manual entry | ✅ Auto-calculated from schedule |
| **Capacity Utilization %** | Excel formula | ✅ Auto-calculated (Visits / Capacity) |
| **Hygiene Reappointment Rate** | Manual tracking | ✅ Auto-calculated |
| **Hygiene Productivity Ratio** | Excel formula | ✅ Auto-calculated (Production / Compensation) |

**Enhancement:** Visual capacity charts, utilization alerts

---

### 7. PROVIDER GROSS PRODUCTION (Individual Tracking)

| Metric | Current (Excel) | Phase 1 (Automated) |
|--------|----------------|---------------------|
| **Doctor #1 Monthly Production** | Manual entry | ✅ Auto-calculated from PMS |
| **Doctor #2 Monthly Production** | Manual entry | ✅ Auto-calculated from PMS |
| **Specialist Monthly Production** | Manual entry | ✅ Auto-calculated from PMS |
| **Hygienist Monthly Production** | Manual entry | ✅ Auto-calculated from PMS |
| **Last Twelve Months (LTM)** | Excel rolling totals | ✅ Auto-calculated |

**Enhancement:** Provider performance rankings, peer comparison

---

## 📊 PHASE 1 DASHBOARD FEATURES (Included)

### What You'll See (Beyond Excel)

✅ **Interactive Charts**
- Production trends over time (line charts)
- Practice comparison bar charts
- KPI cards with trend indicators (↑ 8% vs last month)

✅ **Filters & Drill-Down**
- Select date range (month, quarter, YTD, custom)
- Filter by practice location
- Filter by provider
- Export to Excel/PDF

✅ **Practice Comparison Table**
- Rank all 14 practices by any metric
- Sort by production, visits, efficiency, etc.
- Color-coded performance indicators

✅ **Real-Time Updates**
- Daily refresh vs monthly manual
- Auto-refresh when new data uploaded
- Mobile-responsive (view on phone/tablet)

✅ **Historical Data**
- 21+ months loaded (Jan 2021 - present)
- Trend analysis vs same month last year
- LTM calculations for all metrics

---

## 🎯 PHASE 1 SUMMARY

**Total Metrics Automated:** 60+ KPIs across all categories

**Time to Implement:** 3-4 weeks

**Business Value:**
- ✅ Eliminate 8-10 hours/month manual Excel work
- ✅ Real-time visibility vs monthly lag
- ✅ Multi-practice comparison in one view
- ✅ Mobile access anytime, anywhere
- ✅ Automated calculations (no formula errors)
- ✅ Visual dashboards (easier to spot trends)

**Cost:** Included in existing DentalERP platform

**Risk:** Low (reusing 80% existing code)

---

## 🤖 PHASE 2: AI-POWERED ENHANCEMENTS (Future Project)

### Objective
Add **predictive, prescriptive, and competitive intelligence** beyond current manual tracking.

---

### NEW AI Metrics (Not in Current Report)

#### 1. PREDICTIVE ANALYTICS

| New Metric | Description | Business Value |
|------------|-------------|----------------|
| **Production Forecast** | Predict next 3-6 months production | Proactive staffing & budgeting |
| **Confidence Intervals** | ±$15K confidence range | Risk assessment |
| **Trend Direction** | Improving/declining/stable | Early warning system |
| **Budget Risk Score** | Probability of missing targets | Financial planning |

**Implementation:** Snowflake ML.FORECAST (4-6 weeks)

---

#### 2. PATIENT LIFETIME VALUE (LTV)

| New Metric | Description | Business Value |
|------------|-------------|----------------|
| **Patient LTV Score** | Predicted lifetime revenue per patient | Focus marketing on high-value demographics |
| **High-Value Patient %** | Patients with LTV >$10K | Prioritize retention |
| **Churn Risk Score** | Likelihood patient will leave (0-100) | Prevent loss of valuable patients |
| **New Patient ROI** | Acquisition cost vs predicted LTV | Justify marketing spend |

**Data Required:** Patient demographics, treatment history, visit patterns
**Implementation:** 6-8 weeks

---

#### 3. ANOMALY DETECTION & ALERTS

| New Feature | Description | Business Value |
|-------------|-------------|----------------|
| **Automated Alerts** | "Eastlake production down 18% - investigate" | Catch problems in real-time |
| **Root Cause Analysis** | "Drop correlates with Dr. Smith vacation" | Faster problem diagnosis |
| **Pattern Matching** | "Similar drop occurred last December" | Distinguish systemic vs one-time issues |
| **Threshold Alerts** | Auto-alert when metrics fall below targets | Proactive management |

**Implementation:** 2-3 weeks (Quick Win)

---

#### 4. COMPETITIVE BENCHMARKING

| New Metric | Description | Business Value |
|------------|-------------|----------------|
| **Percentile Ranking** | "Your production/visit: 78th percentile" | Understand competitive position |
| **Market Share Estimate** | Based on zip code demographics | Growth opportunity sizing |
| **Pricing Competitiveness** | Vs local competitors | Pricing strategy |
| **Service Gap Analysis** | Services offered vs market demand | Expansion opportunities |

**Data Sources:** ADA benchmarks, Dental Intelligence network, public data
**Implementation:** 4-6 weeks

---

#### 5. HYGIENE REVENUE RECOVERY

| New Feature | Description | Business Value |
|-------------|-------------|----------------|
| **Recare Gap List** | "547 patients overdue = $82K opportunity" | Actionable revenue recovery list |
| **Patient Prioritization** | Ranked by value (high-LTV patients first) | Maximize ROI of outreach |
| **Revenue Leakage $** | Total missed revenue from overdue patients | Quantify opportunity |
| **Predicted Response** | Likelihood patient will schedule | Focus on high-probability conversions |

**Implementation:** 3-4 weeks

---

#### 6. CASE ACCEPTANCE OPTIMIZATION

| New Insight | Description | Business Value |
|-------------|-------------|----------------|
| **Optimal Value Range** | "$3K-$5K cases have 85% acceptance" | Price presentations optimally |
| **Time-of-Day Pattern** | "Tuesday AM = 12% higher acceptance" | Schedule presentations strategically |
| **Demographic Profiles** | "Age 35-50 + PPO = 85% acceptance" | Target ideal patients |
| **Treatment Type Trends** | "Cosmetic down 15%, restorative up 8%" | Adjust service mix |

**Implementation:** 6-8 weeks

---

#### 7. PROVIDER EFFICIENCY (AI-ADJUSTED)

| New Metric | Description | Business Value |
|------------|-------------|----------------|
| **Complexity-Adjusted Score** | Accounts for case difficulty | Fair performance evaluation |
| **Patient Mix Adjustment** | Accounts for insurance mix impact | Identify systemic vs individual issues |
| **No-Show Impact $** | Lost production from cancellations | Quantify scheduling issues |
| **Optimal Schedule Score** | Actual vs ideal patient mix | Improve scheduling |

**Implementation:** 4-6 weeks

---

#### 8. TREATMENT CONVERSION FUNNEL

| New Metric | Description | Business Value |
|------------|-------------|----------------|
| **Diagnosis → Presentation %** | % diagnosed issues presented | Identify presentation gaps |
| **Presentation → Acceptance %** | Current metric (enhanced) | Existing |
| **Acceptance → Scheduling %** | % accepted cases scheduled | Find scheduling bottleneck |
| **Scheduling → Completion %** | % scheduled cases completed | Track follow-through |
| **Overall Conversion Rate** | End-to-end funnel | Identify biggest revenue leaks |

**Implementation:** 3-4 weeks

---

#### 9. MARKETING ROI ATTRIBUTION

| New Metric | Description | Business Value |
|------------|-------------|----------------|
| **Acquisition Cost by Channel** | Cost per patient (Google, referrals, etc.) | Optimize budget allocation |
| **Marketing ROI by Channel** | LTV / Acquisition Cost | Know which channels work |
| **Referral Source Value** | Which patients refer high-value patients | Incentivize best referrers |
| **Campaign Effectiveness** | Conversions per $ spent | Measure campaign performance |

**Data Required:** Marketing source tracking, campaign spend data
**Implementation:** 4-6 weeks

---

#### 10. SEASONAL CAPACITY PLANNING

| New Feature | Description | Business Value |
|------------|-------------|----------------|
| **Seasonal Index** | Predicted demand by month | Proactive staffing |
| **Capacity Forecast** | Utilization next 90 days | Optimize scheduling |
| **Staffing Recommendations** | "Reduce hours by 10% in December" | Cost optimization |
| **Inventory Predictions** | Supplies needed based on forecasts | Reduce waste |

**Implementation:** 3-4 weeks

---

#### 11. PATIENT SATISFACTION & NPS

| New Metric | Description | Business Value |
|------------|-------------|----------------|
| **Net Promoter Score** | Industry standard satisfaction metric | Benchmark patient experience |
| **Review Sentiment Score** | AI analysis of online reviews | Identify service issues |
| **Complaint Rate** | Tracked complaints per 100 visits | Quality monitoring |
| **Satisfaction → Retention** | Correlation to patient retention | Link experience to revenue |

**Data Required:** Post-visit surveys, online review integration
**Implementation:** 4-6 weeks

---

#### 12. AI INSIGHTS DASHBOARD

| New Feature | Description | Business Value |
|-------------|-------------|----------------|
| **Daily Opportunities** | "127 overdue hygiene = $19K revenue" | Automated insight generation |
| **Risk Alerts** | "New patients down 3 months - investigate" | Early warning system |
| **Predictions** | "Next month forecast: $285K ±$15K" | Forward-looking planning |
| **Recommendations** | "Focus on marketing (+15% recommended)" | Prescriptive actions |
| **Practice Health Score** | Overall score 0-100 | Single performance metric |

**Implementation:** 6-8 weeks (full platform)

---

## 📅 IMPLEMENTATION ROADMAP

### **PHASE 1: Foundation** (3-4 weeks) - **RECOMMENDED TO START**
✅ Automate all 60+ existing metrics
✅ Real-time dashboard with charts
✅ Practice comparison & ranking
✅ Historical data (21+ months)
✅ Export functionality
✅ Mobile-responsive design

**Cost:** Included in DentalERP platform
**ROI:** Eliminate 96-120 hours/year manual work = $4,800-$6,000 savings

---

### **PHASE 2A: Quick Win AI Features** (2-4 weeks) - **HIGH ROI**
✅ Anomaly detection & automated alerts
✅ Production forecasting (3-6 months)
✅ Hygiene revenue recovery tool
✅ Treatment conversion funnel

**Cost:** Included (uses Snowflake ML)
**ROI:** $82K+ revenue recovery per practice

---

### **PHASE 2B: Advanced Analytics** (2-3 months) - **STRATEGIC**
- Patient LTV prediction
- Provider efficiency scoring (AI-adjusted)
- Competitive benchmarking
- Marketing ROI attribution
- Case acceptance optimization

**Cost:** Additional development
**ROI:** $150K+ annual revenue impact

---

### **PHASE 2C: Predictive Platform** (3-4 months) - **TRANSFORMATIONAL**
- Optimal scheduling recommendations
- Seasonal capacity planning
- Patient satisfaction & NPS
- Full AI insights dashboard
- Churn prediction & prevention

**Cost:** Full AI platform investment
**ROI:** $487K+ potential annual impact

---

## 💡 RECOMMENDATION

### Start with Phase 1 (3-4 weeks)
**Why:**
- ✅ Low risk (proven technology)
- ✅ Immediate value (eliminate manual work)
- ✅ Fast delivery (2-3 weeks)
- ✅ Foundation for all future AI features
- ✅ Get team comfortable with dashboards

**Then evaluate Phase 2 based on:**
- Phase 1 adoption and feedback
- Specific pain points identified
- ROI priorities (revenue recovery vs efficiency vs growth)
- Data availability (PMS integration, marketing tracking, etc.)

---

## 📊 SUMMARY TABLE

| Category | Phase 1 (Automate) | Phase 2A (Quick AI) | Phase 2B (Advanced) | Phase 2C (Full AI) |
|----------|-------------------|---------------------|---------------------|-------------------|
| **Timeline** | 3-4 weeks | +2-4 weeks | +2-3 months | +3-4 months |
| **Metrics** | 60+ existing KPIs | +4 predictive features | +5 strategic insights | +3 AI platforms |
| **Effort** | Low (code reuse) | Low (Snowflake ML) | Medium | High |
| **Risk** | Low | Low | Medium | Medium |
| **ROI** | $5K/year savings | $82K+ revenue | $150K+ revenue | $487K+ revenue |
| **Decision** | ✅ **Start Here** | Add after Phase 1 | Evaluate need | Future investment |

---

**Document Owner:** Development Team
**Last Updated:** November 14, 2025

**Questions?** See detailed implementation plans:
- Phase 1: `docs/plans/2025-11-14-operations-kpis-LEAN-APPROACH.md`
- Phase 2: `docs/plans/2025-11-14-operations-kpi-dashboard.md` (AI section)
