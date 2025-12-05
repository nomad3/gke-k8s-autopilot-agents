# Frontend Analytics Pages - Mock/Hardcoded Data Analysis
**Date**: November 14, 2025
**Scope**: All analytics pages in `/frontend/src/pages/analytics/`

---

## Executive Summary

Found **11 files** with mock/hardcoded data across the analytics section:
- **3 files**: Placeholder UI elements (no API hooks)
- **2 files**: Mock benchmark data with hardcoded defaults
- **6 files**: Blank state fallback data (appropriate for API failures)
- **Multiple locations**: Default fallback values when API data missing

**Total Issues Found**: ~18 hardcoded values requiring attention

---

## Detailed Findings by File

### 1. **EnhancedAnalyticsPage.tsx** (CRITICAL - MOCK DATA)
**Status**: Uses mock benchmark data for industry comparisons
**Lines**: 64-102

#### Mock Benchmark Metrics (6 hardcoded values):
```typescript
// Line 68-69: Mock production benchmark
industryAvg: totalProduction * 0.85,    // Mock: 85% of your value
topPerformer: totalProduction * 1.15,   // Mock: 115% of your value

// Line 75-76: Hardcoded industry averages
industryAvg: 425,                       // Mock industry average
topPerformer: 550,                      // Mock top performer

// Line 82-83: Mock visit benchmarks
industryAvg: totalVisits * 0.9,         // Mock: 90% of your value
topPerformer: totalVisits * 1.2,        // Mock: 120% of your value

// Line 89-98: Completely hardcoded mock metrics
{
  name: 'Collection Rate',
  yourValue: 95.5,                      // Mock
  industryAvg: 92.0,                    // Mock industry average
  topPerformer: 98.0,                   // Mock top performer
}

{
  name: 'Quality Score',
  yourValue: 88.0,                      // Mock
  industryAvg: 85.0,                    // Mock industry average
  topPerformer: 95.0,                   // Mock top performer
}
```

**Purpose**: BenchmarkOverlay component displays "Industry Benchmarks" comparison

**Issue**: 
- Industry averages are completely made up (not from real data source)
- Collection Rate and Quality Score are hardcoded (95.5%, 88.0%) instead of calculated
- Mock data doesn't represent actual industry standards

**Recommendation**: 
- REMOVE hardcoded benchmark data
- Create API endpoint for real industry/peer benchmarks
- Or fetch from external benchmark database (DentalIntel)
- Update component to show "Data unavailable" if real benchmarks not available

**Impact Level**: HIGH - Misleads users about performance vs. industry

---

### 2. **BranchComparisonPage.tsx** (CRITICAL - HARDCODED DEFAULTS)
**Status**: Uses hardcoded fallback values when data missing
**Lines**: 58-59

#### Hardcoded Default Values:
```typescript
// Line 58-59: Default to hardcoded values if API doesn't return field
collection_rate: Number(practice.COLLECTION_RATE || 95),     // Default to 95% if not available
quality_score: Number(practice.QUALITY_SCORE || 90),         // Default to 90 if not available
```

**Purpose**: ComparisonTable component needs these fields for ranking

**Issue**:
- If API doesn't return `COLLECTION_RATE`, it defaults to 95% (misleading)
- If API doesn't return `QUALITY_SCORE`, it defaults to 90 (false confidence)
- These defaults are used in rankings and comparisons without clear indication

**Recommendation**:
- Remove hardcoded defaults
- Make fields optional/nullable
- Show "N/A" or "Data pending" in UI when missing
- Or ensure backend always returns these fields (preferred)

**Impact Level**: MEDIUM - Could rank practices incorrectly if data missing

---

### 3. **RevenueChart.tsx** (APPROPRIATE - BLANK STATE)
**Status**: Uses blank state data when API fails
**Lines**: 10-17

#### Blank State Data:
```typescript
const blankData: RevenuePoint[] = [
  { month: 'Jan', revenue: 0, target: 0 },
  { month: 'Feb', revenue: 0, target: 0 },
  // ... 6 months
];

const chartData: RevenuePoint[] = isBlank ? blankData : actualData;
```

**Purpose**: Show empty chart when API unavailable

**Assessment**: APPROPRIATE
- Only used when `error` or no data returned
- Clearly fallback for error states
- Shows "$0" values in UI (transparent that data missing)
- No misleading information

**Recommendation**: Keep as-is, properly handles error states

---

### 4. **LocationPerformance.tsx** (APPROPRIATE - BLANK STATE)
**Status**: Uses blank placeholder data when API fails
**Lines**: 19-25

#### Blank State Data:
```typescript
const locations: LocationData[] = isBlank
  ? [
      { name: '—', revenue: 0, revenueChange: 0, patients: 0, patientChange: 0, efficiency: 0, status: 'neutral' },
      // ... 3 blank rows
    ]
  : (data!.data.locations as any[]);
```

**Purpose**: Show placeholder rows when API unavailable

**Assessment**: APPROPRIATE
- Only used when `error` or no data
- Shows dashes "—" in UI to indicate empty
- Status marked as 'neutral' (not confident)
- Clear visual indication that data is missing

**Recommendation**: Keep as-is

---

### 5. **PatientAcquisition.tsx** (APPROPRIATE - BLANK STATE + MOCK PERFORMERS)
**Status**: Uses blank data + mock top performers
**Lines**: 7-17

#### Blank State Data:
```typescript
const totals = isBlank 
  ? { total: 0, referrals: 0, marketing: 0, walkIns: 0, trend: 'flat' }
  : data!.data;
```

#### Mock Top Performers (LINE 13-17):
```typescript
const topPerformers = isBlank
  ? []
  : [
      { name: 'Team A', revenue: '$—', utilization: `${totals.utilization}%`, rating: 4.8 },
    ];

// Comment on line 12:
// "Placeholder top performers for demo; when API adds performers, this can be replaced"
```

**Purpose**: Show top performers list (future feature)

**Assessment**: PARTIALLY APPROPRIATE
- Blank state (empty array) when no data is GOOD
- Hardcoded "Team A" with mock rating (4.8) is PROBLEMATIC
- Comment indicates developer awareness this is placeholder
- But mock data will never be shown (empty array fallback takes precedence)

**Recommendation**: Remove mock top performers entry, keep empty array fallback

---

### 6. **StaffProductivity.tsx** (APPROPRIATE - BLANK STATE + COMMENT)
**Status**: Uses blank state with clear placeholder comment
**Lines**: 8-17

#### Blank State Data:
```typescript
const totals = isBlank
  ? { utilization: 0, avgAppointmentsPerProvider: 0, overtimeHours: 0, remoteStaff: 0 }
  : data!.data;

// Comment explicitly marks as placeholder:
// "Placeholder top performers for demo; when API adds performers, this can be replaced"
const topPerformers = isBlank
  ? []
  : [
      { name: 'Team A', revenue: '$—', utilization: `${totals.utilization}%`, rating: 4.8 },
    ];
```

**Assessment**: APPROPRIATE
- Blank state when no data (shows "—" or "0")
- Mock performers array explicitly marked as placeholder
- Comment shows developer intent
- Empty array fallback prevents rendering misleading data

**Recommendation**: Keep as-is, eventually replace with real API data

---

### 7. **ForecastingPage.tsx** (PLACEHOLDER UI - NO API)
**Status**: Entire page is placeholder with no API integration
**Line**: 9

#### Placeholder UI:
```typescript
<span className="text-gray-500 text-sm">
  Projected revenue, patient volume, staffing (placeholder)
</span>
```

**Purpose**: Forecasting features not yet implemented

**Assessment**: APPROPRIATE
- Clearly marked "(placeholder)" to users
- No mock data being displayed as real
- Shows empty gray box
- No misleading calculations

**Recommendation**: Keep placeholder until forecasting module built

---

### 8. **PatientAnalyticsPage.tsx** (PLACEHOLDER UI - NO API)
**Status**: "Recall & Retention" section is placeholder
**Line**: 12

#### Placeholder UI:
```typescript
<span className="text-gray-500 text-sm">
  Recall rates, returning patient cohorts (placeholder)
</span>
```

**Assessment**: APPROPRIATE
- Clearly marked as placeholder
- Not showing any mock data to users

**Recommendation**: Keep placeholder

---

### 9. **StaffAnalyticsPage.tsx** (PLACEHOLDER UI - NO API)
**Status**: "Utilization & Payroll Efficiency" section is placeholder
**Line**: 12

#### Placeholder UI:
```typescript
<span className="text-gray-500 text-sm">
  ADP utilization, revenue per hour (placeholder)
</span>
```

**Assessment**: APPROPRIATE
- Clearly marked as placeholder
- Just shows empty box

**Recommendation**: Keep placeholder

---

### 10. **ClinicalAnalyticsPage.tsx** (PLACEHOLDER UI - NO API)
**Status**: Two sections are placeholders
**Lines**: 10, 18

#### Placeholder UIs:
```typescript
<span className="text-gray-500 text-sm">
  Procedures by type, completion rates (placeholder)
</span>

<span className="text-gray-500 text-sm">
  Chair utilization, on-time, throughput (placeholder)
</span>
```

**Assessment**: APPROPRIATE
- Both clearly marked as placeholders
- No mock data shown

**Recommendation**: Keep placeholders

---

### 11. **ProductionAnalyticsPage.tsx** (EXCELLENT - NO MOCK DATA)
**Status**: Uses real API data throughout
**Properties**: 
- No hardcoded defaults
- No mock benchmarks
- Proper error handling
- Format helpers (formatCurrency, formatNumber, formatPercent)

**Assessment**: GOOD
- Clean implementation
- All data from APIs
- Proper loading states

**Recommendation**: Use as template for other analytics pages

---

### 12. **FinancialAnalyticsPage.tsx** (EXCELLENT - NO MOCK DATA)
**Status**: Uses real API data from hooks
**Properties**:
- `useFinancialSummary()` hook
- `usePracticeComparison()` hook
- Proper error states

**Assessment**: GOOD
- Clean implementation
- All data from APIs
- Handles missing data gracefully

**Recommendation**: Keep as-is

---

### 13. **SchedulingAnalyticsPage.tsx** (GOOD - API-DRIVEN)
**Status**: Uses API data with proper fallbacks
**Properties**:
- Fetches from `analyticsAPI.getSchedulingOverview()`
- Shows "Loading…" while fetching
- Shows "0" or "0%" as fallback (not misleading)

**Assessment**: GOOD

**Recommendation**: Keep as-is

---

### 14. **BenchmarkingPage.tsx** (GOOD - API-DRIVEN)
**Status**: Uses API data with proper fallbacks
**Properties**:
- Fetches from `analyticsAPI.getBenchmarking()`
- Maps API response to UI

**Assessment**: GOOD

**Recommendation**: Keep as-is

---

### 15. **RetentionCohortsPage.tsx** (GOOD + COMMENT)
**Status**: Uses API data with explicit "synthetic cohorts" note
**Line**: 55

#### Note Comment:
```typescript
<p className="text-xs text-gray-500 mt-3">Synthetic cohorts for demo</p>
```

**Purpose**: Shows retention cohorts (potentially synthetic for demo)

**Assessment**: ACCEPTABLE
- Explicit note that cohorts are "synthetic for demo"
- User is informed they're not real data
- Data still comes from API (not hardcoded)

**Recommendation**: Keep comment, consider updating once real cohort logic implemented

---

### 16. **AnalyticsPage.tsx** (NAV ROUTER - NO DATA)
**Status**: Router page, no data logic
**Assessment**: N/A

---

### 17. **ReportsPage.tsx** (STATIC UI - NO DATA)
**Status**: Static UI with hardcoded examples
**Lines**: 24-26

#### Hardcoded Report Examples:
```typescript
<ul className="space-y-2 text-sm text-gray-700">
  <li>Executive Summary – Last 30 days <span className="text-xs text-gray-500">(PDF)</span></li>
  <li>Location Performance – QTD <span className="text-xs text-gray-500">(CSV)</span></li>
  <li>Clinical Outcomes – Last month <span className="text-xs text-gray-500">(PDF)</span></li>
</ul>
```

**Assessment**: APPROPRIATE
- These are just UI example labels
- Not data being presented as real
- Shows what reports users can generate
- Placeholder feature (reports not yet built)

**Recommendation**: Keep as placeholder examples

---

## Summary Table

| File | Type | Issue | Severity | Status |
|------|------|-------|----------|--------|
| EnhancedAnalyticsPage.tsx | Mock Data | Hardcoded benchmarks (6 values) | HIGH | NEEDS FIX |
| BranchComparisonPage.tsx | Hardcoded Defaults | Default to 95% collection rate, 90% quality | MEDIUM | NEEDS FIX |
| RevenueChart.tsx | Blank State | Fallback zeros | LOW | GOOD |
| LocationPerformance.tsx | Blank State | Placeholder rows | LOW | GOOD |
| PatientAcquisition.tsx | Blank State + Mock | Empty array fallback, unused mock | LOW | ACCEPTABLE |
| StaffProductivity.tsx | Blank State + Mock | Empty array fallback, unused mock | LOW | ACCEPTABLE |
| ForecastingPage.tsx | Placeholder UI | No API integration | N/A | APPROPRIATE |
| PatientAnalyticsPage.tsx | Placeholder UI | No API integration | N/A | APPROPRIATE |
| StaffAnalyticsPage.tsx | Placeholder UI | No API integration | N/A | APPROPRIATE |
| ClinicalAnalyticsPage.tsx | Placeholder UI | No API integration | N/A | APPROPRIATE |
| ProductionAnalyticsPage.tsx | API-Driven | No mock data | N/A | EXCELLENT |
| FinancialAnalyticsPage.tsx | API-Driven | No mock data | N/A | EXCELLENT |
| SchedulingAnalyticsPage.tsx | API-Driven | No mock data | N/A | GOOD |
| BenchmarkingPage.tsx | API-Driven | No mock data | N/A | GOOD |
| RetentionCohortsPage.tsx | API-Driven | Synthetic note | LOW | ACCEPTABLE |
| AnalyticsPage.tsx | Router | N/A | N/A | N/A |
| ReportsPage.tsx | Static UI | Example labels only | N/A | APPROPRIATE |

---

## Priority Action Items

### CRITICAL (Must Fix)
1. **EnhancedAnalyticsPage.tsx** - Remove hardcoded benchmark data
   - Create real benchmark API endpoint
   - Or integrate with DentalIntel service for real industry data
   - Replace mock values with calculated or real data

2. **BranchComparisonPage.tsx** - Remove hardcoded defaults
   - Make collection_rate and quality_score optional
   - Show "N/A" in UI when missing
   - Ensure backend returns these fields always

### MEDIUM (Should Fix)
3. **PatientAcquisition.tsx & StaffProductivity.tsx** - Clean up unused mock performers
   - Remove hardcoded "Team A" entries
   - Keep empty array fallback only

### LOW (Nice to Have)
4. **RetentionCohortsPage.tsx** - Update "Synthetic cohorts" note
   - Either replace with real cohort logic
   - Or explain better what "synthetic for demo" means

---

## Recommendations

### For Analytics Components Going Forward:
1. **Use API data only** - Never hardcode business metrics
2. **Show clear fallbacks** - Use "—" or "N/A" when data missing, not zeros
3. **Explicit placeholders** - Mark unimplemented features clearly
4. **No default assumptions** - Don't assume 95% collection rate or 90% quality
5. **Error handling** - Show "Loading…" or error messages, not blanks

### For Benchmark Data:
1. Create backend endpoint: `GET /api/v1/benchmarks/{metric}`
2. Or integrate with DentalIntel API
3. Cache benchmark data (updated quarterly)
4. Allow practice to set custom benchmarks

### For Missing Fields:
1. Ensure backend returns all expected fields
2. Or make fields truly optional with nullable types
3. Never fallback to hardcoded "reasonable" defaults

---

## Code Examples

### Bad (Current):
```typescript
// EnhancedAnalyticsPage.tsx line 68
industryAvg: totalProduction * 0.85, // Mock: completely made up

// BranchComparisonPage.tsx line 58
collection_rate: Number(practice.COLLECTION_RATE || 95), // Unsafe default
```

### Good (Recommended):
```typescript
// Use calculated values only
industryAvg: undefined, // Show as "N/A" in UI

// Make fields optional
collection_rate: practice.COLLECTION_RATE ?? null, // null = show "N/A"

// Or ensure backend always provides data
collection_rate: Number(practice.COLLECTION_RATE), // Throw error if missing
```

