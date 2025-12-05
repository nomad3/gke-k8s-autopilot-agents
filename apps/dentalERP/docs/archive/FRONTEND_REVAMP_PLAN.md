# Frontend UX/UI Revamp Plan
**Multi-Tenant BI Dashboard with Branch Comparison**
**Date**: 2025-10-30

---

## 🎯 Goals

1. **Multi-Tenant Support**: Global tenant selector with context propagation
2. **Executive Overview**: Bird's eye view of all practices/branches
3. **Branch Comparison**: Side-by-side practice performance analysis
4. **Modern BI Design**: Data-dense, scannable, action-oriented
5. **Mobile-First**: Responsive design for tablets and mobile
6. **Real-Time Updates**: Live data with WebSocket integration

---

## 📐 Architecture Overview

```
frontend/src/
├── contexts/
│   └── TenantContext.tsx          # NEW: Global tenant selection
├── components/
│   ├── tenant/
│   │   ├── TenantSwitcher.tsx     # NEW: Dropdown tenant selector
│   │   └── TenantBadge.tsx        # NEW: Current tenant indicator
│   ├── dashboard/
│   │   ├── ExecutiveOverview.tsx  # NEW: All-branches KPI grid
│   │   ├── BranchComparison.tsx   # NEW: Side-by-side comparison
│   │   ├── KPICard.tsx            # ENHANCED: Modern metric card
│   │   └── TrendChart.tsx         # NEW: Sparkline/trend charts
│   └── analytics/
│       ├── ProductionHeatmap.tsx  # NEW: Calendar heatmap
│       ├── PracticeLeaderboard.tsx # NEW: Ranked practice list
│       └── PerformanceRadar.tsx   # NEW: Multi-metric radar chart
├── pages/
│   ├── dashboard/
│   │   ├── ExecutiveDashboard.tsx # NEW: C-suite view
│   │   └── ManagerDashboard.tsx   # ENHANCED: Operations view
│   └── analytics/
│       ├── BranchAnalyticsPage.tsx # NEW: Branch comparison page
│       └── ProductionAnalyticsPage.tsx # ENHANCED: With comparisons
└── services/
    ├── tenantApi.ts               # NEW: Tenant management APIs
    └── analyticsApi.ts            # ENHANCED: Multi-tenant analytics
```

---

## 🎨 Design System

### Color Palette
```
Primary (Sky Blue):   #0ea5e9 - Data/Analytics
Success (Green):      #10b981 - Positive metrics
Warning (Orange):     #f59e0b - Attention needed
Danger (Red):         #ef4444 - Critical issues
Purple:               #8b5cf6 - Special/Premium features
Gray Scale:           #1f2937 → #f9fafb (9 shades)
```

### Typography
```
Font: Inter (system-ui fallback)
Sizes:
  - Display: 36px/44px (font-bold)
  - H1: 30px/36px (font-bold)
  - H2: 24px/32px (font-semibold)
  - H3: 20px/28px (font-semibold)
  - Body: 14px/20px (font-normal)
  - Small: 12px/16px (font-normal)
  - Tiny: 10px/14px (font-medium)
```

### Spacing
```
xs: 4px, sm: 8px, md: 16px, lg: 24px, xl: 32px, 2xl: 48px
```

---

## 🧩 Component Specifications

### 1. TenantContext Provider

**Purpose**: Global tenant selection state
**Features**:
- Persist selected tenant to localStorage
- Auto-select if single tenant
- Inject X-Tenant-ID header in all API calls
- Expose `selectedTenant`, `setSelectedTenant`, `tenants`, `isLoading`

**API Integration**:
```typescript
GET /api/v1/tenants → List all tenants user has access to
```

**State Shape**:
```typescript
interface TenantContextState {
  selectedTenant: Tenant | null;
  tenants: Tenant[];
  isLoading: boolean;
  error: Error | null;
  selectTenant: (tenantId: string) => void;
  refreshTenants: () => Promise<void>;
}

interface Tenant {
  id: string;
  tenant_code: string;
  tenant_name: string;
  products: string[];
  status: 'active' | 'inactive';
}
```

---

### 2. TenantSwitcher Component

**Purpose**: Dropdown for changing active tenant
**Location**: Top header (next to user menu)

**Features**:
- Show current tenant with badge
- List all accessible tenants
- Search/filter for 10+ tenants
- Show tenant product access
- Highlight current selection

**UI Mockup**:
```
┌─────────────────────────────────┐
│ 🏢 Silvercreek Dental      [▼] │
├─────────────────────────────────┤
│ 🔍 Search tenants...            │
├─────────────────────────────────┤
│ ✓ Silvercreek Dental            │
│   [dentalerp]                   │
│ ○ ACME Dental Practice          │
│   [dentalerp, agentprovision]   │
│ ○ Default Tenant                │
│   [dentalerp]                   │
└─────────────────────────────────┘
```

---

### 3. Executive Overview Dashboard

**Purpose**: C-suite bird's eye view across all branches
**Route**: `/dashboard/executive`
**Role Access**: `admin`, `executive`

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Executive Overview - All Practices                          │
│ Tenant: Silvercreek Dental | 15 Locations | Oct 2025       │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│ │ $2.4M   │ │ 12,450  │ │ $193    │ │ 94.2%   │           │
│ │ Total   │ │ Visits  │ │ Avg/    │ │ Collec  │           │
│ │ Prod    │ │         │ │ Visit   │ │ Rate    │           │
│ │ +12%    │ │ +5%     │ │ +7%     │ │ -1%     │           │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
├─────────────────────────────────────────────────────────────┤
│ Top Performing Practices     │ Needs Attention              │
│ 1. Downtown      $185K  ▲    │ • Westside: -15% MoM        │
│ 2. Eastside      $172K  ▲    │ • Northgate: Low quality    │
│ 3. Southside     $168K  ▲    │ • Midtown: Missing data     │
├─────────────────────────────────────────────────────────────┤
│ [Production Heatmap - 30 days]                              │
│ Mon Tue Wed Thu Fri Sat Sun                                 │
│  ██  ██  ██  ██  ██  ▓▓  ░░  Week 1                        │
│  ██  ██  ▓▓  ██  ██  ▓▓  ░░  Week 2                        │
│  ██  ██  ██  ██  ▓▓  ▓▓  ░░  Week 3                        │
│  ██  ██  ██  ██  ██  ▓▓  ░░  Week 4                        │
│ ██ = >$8K  ▓▓ = $5-8K  ░░ = <$5K                            │
└─────────────────────────────────────────────────────────────┘
```

**Data Sources**:
- `GET /api/v1/analytics/production/summary` (tenant-wide)
- `GET /api/v1/analytics/production/by-practice` (all practices)
- `GET /api/v1/analytics/production/daily` (heatmap data)

---

### 4. Branch Comparison View

**Purpose**: Side-by-side practice performance analysis
**Route**: `/analytics/branch-comparison`
**Role Access**: `admin`, `executive`, `manager`

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Branch Comparison                                           │
│ Select Practices: [Downtown ▼] [Eastside ▼] [Southside ▼]  │
│ Date Range: [Last 30 Days ▼]                               │
├───────────────┬───────────────┬───────────────┬─────────────┤
│ Metric        │ Downtown      │ Eastside      │ Southside   │
├───────────────┼───────────────┼───────────────┼─────────────┤
│ Total Prod    │ $185,420      │ $172,310      │ $168,905    │
│               │ 🥇 1st        │ 2nd           │ 3rd         │
├───────────────┼───────────────┼───────────────┼─────────────┤
│ Patient Visits│ 982           │ 1,045         │ 1,105       │
│               │ 3rd           │ 2nd           │ 🥇 1st      │
├───────────────┼───────────────┼───────────────┼─────────────┤
│ $/Visit       │ $189          │ $165          │ $153        │
│               │ 🥇 1st        │ 2nd           │ 3rd         │
├───────────────┼───────────────┼───────────────┼─────────────┤
│ Collection %  │ 95.2%         │ 93.8%         │ 92.1%       │
│               │ 🥇 1st        │ 2nd           │ 3rd         │
├───────────────┼───────────────┼───────────────┼─────────────┤
│ Trend (30d)   │ ──────▲       │ ────▲▲        │ ▲▲▲▲▲▲      │
│               │ +3%           │ +8%           │ +12%        │
└───────────────┴───────────────┴───────────────┴─────────────┘
```

**Features**:
- Select 2-5 practices to compare
- Color-code best/worst performers
- Show rank badges (🥇🥈🥉)
- Sparkline trends
- Export to CSV/Excel

**Data Sources**:
- `GET /api/v1/analytics/production/by-practice?start_date=X&end_date=Y`
- `GET /api/v1/analytics/production/daily?practice_location=X&...`

---

### 5. Enhanced Dashboard Layout

**Changes to DashboardLayout.tsx**:
1. Add TenantSwitcher in header (right of logo)
2. Add "Executive View" toggle for admins
3. Add breadcrumb navigation
4. Add global date range picker
5. Add quick action buttons (Upload PDF, Run Report, etc.)
6. Sticky header on scroll
7. Collapsible sidebar with icons-only mode

**New Header Layout**:
```
┌────────────────────────────────────────────────────────────┐
│ [☰] DentalERP BI    🏢 Tenant [▼]  📅 Oct 2025  👤 User  │
│                                                             │
│ Home > Analytics > Production                              │
└────────────────────────────────────────────────────────────┘
```

---

### 6. Enhanced Production Analytics Page

**Changes to ProductionAnalyticsPage.tsx**:
1. Add practice selector with multi-select
2. Add comparison mode toggle
3. Add export button (CSV, Excel, PDF)
4. Add "Benchmark" overlay (compare to org average)
5. Add trend arrows (↑ +12%, ↓ -5%)
6. Add "Alerts" section (anomalies, missing data)
7. Add mini charts in table cells

**New Features**:
```typescript
// Comparison mode
<button onClick={() => setComparisonMode(!comparisonMode)}>
  {comparisonMode ? 'Single View' : 'Compare Practices'}
</button>

// Export
<button onClick={() => exportToExcel(dailyData)}>
  📊 Export to Excel
</button>

// Benchmark overlay
{showBenchmark && (
  <div className="benchmark-overlay">
    Org Average: $62.50/visit
    Your Performance: +8% above average
  </div>
)}
```

---

## 🔌 API Integration Plan

### New Endpoints Needed (Backend)
```python
# Tenant Management
GET    /api/v1/tenants                    # List tenants for current user
GET    /api/v1/tenants/{id}               # Get tenant details
GET    /api/v1/tenants/{id}/practices     # Get practices for tenant

# Multi-Practice Analytics
GET    /api/v1/analytics/production/compare  # Compare multiple practices
  ?practice_locations=A,B,C
  &start_date=2025-10-01
  &end_date=2025-10-31
  &metrics=production,visits,collection_rate

# Executive Rollup
GET    /api/v1/analytics/executive/summary  # Tenant-wide KPIs
  ?tenant_id=X
  &date_range=last_30_days

# Alerts & Anomalies
GET    /api/v1/analytics/alerts             # Data quality issues, anomalies
  ?tenant_id=X
  &severity=medium,high
```

### Enhanced Existing Endpoints
```python
# Add tenant_id filter (already implemented via middleware)
# Add comparison flag
# Add benchmark calculation
```

---

## 📊 Data Flow

```
User Action (Select Tenant)
    ↓
TenantContext.selectTenant()
    ↓
localStorage.setItem('selected_tenant', id)
    ↓
API interceptor adds X-Tenant-ID header
    ↓
All subsequent API calls filtered by tenant
    ↓
Components react to tenant change
    ↓
Re-fetch analytics data for new tenant
```

---

## 🎯 Implementation Phases

### Phase 1: Foundation (Day 1)
- [x] TenantContext provider
- [x] TenantSwitcher component
- [x] Update API interceptor to inject tenant header
- [x] Test tenant switching

### Phase 2: Executive Dashboard (Day 2)
- [ ] Executive Overview page
- [ ] KPI summary cards
- [ ] Practice leaderboard
- [ ] Production heatmap

### Phase 3: Branch Comparison (Day 3)
- [ ] Branch comparison page
- [ ] Practice selector (multi-select)
- [ ] Comparison table with rankings
- [ ] Sparkline trend charts

### Phase 4: Enhanced Analytics (Day 4)
- [ ] Update ProductionAnalyticsPage
- [ ] Add comparison mode
- [ ] Add benchmark overlay
- [ ] Add export functionality

### Phase 5: Polish & Testing (Day 5)
- [ ] Mobile responsiveness
- [ ] Loading states
- [ ] Error handling
- [ ] E2E tests
- [ ] Performance optimization

---

## 🔧 Technical Decisions

### State Management
- **Tenant Selection**: React Context + localStorage
- **Analytics Data**: React Query (existing hooks)
- **UI State**: Local component state

### Data Fetching
- **React Query** for caching, deduplication, retry
- **Axios interceptors** for tenant headers
- **WebSocket** for real-time updates

### Styling
- **Tailwind CSS** for utility-first styling
- **Headless UI** for accessible components
- **Heroicons** for consistent iconography
- **Recharts** for data visualization

### Accessibility
- **ARIA labels** on all interactive elements
- **Keyboard navigation** fully supported
- **Screen reader** tested
- **Color contrast** WCAG AA compliant

---

## 📱 Mobile Considerations

### Responsive Breakpoints
```
sm: 640px   - Phone landscape
md: 768px   - Tablet portrait
lg: 1024px  - Tablet landscape
xl: 1280px  - Desktop
2xl: 1536px - Large desktop
```

### Mobile-Specific Features
- Swipeable cards
- Bottom sheet drawers
- Collapsible tables
- Touch-friendly hit targets (44x44px min)

---

## 🚀 Performance Targets

- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3.0s
- **API Response Time**: < 500ms (p95)
- **Bundle Size**: < 500KB gzipped
- **Lighthouse Score**: > 90/100

---

## 🧪 Testing Strategy

### Unit Tests
- TenantContext state management
- API interceptor tenant header injection
- Comparison calculations

### Integration Tests
- Tenant switching flow
- Branch comparison with real API
- Export functionality

### E2E Tests (Playwright)
- Login → Select Tenant → View Analytics
- Compare 3 branches → Export CSV
- Switch tenant → Verify data changes

---

## 📝 Documentation Needs

- [ ] **User Guide**: How to use multi-tenant features
- [ ] **Admin Guide**: How to manage tenants
- [ ] **API Docs**: New endpoints specification
- [ ] **Component Storybook**: Visual component library

---

## 🎉 Success Criteria

1. ✅ Users can switch tenants seamlessly
2. ✅ Executive dashboard shows org-wide KPIs
3. ✅ Branch comparison supports 2-5 practices
4. ✅ All analytics respect tenant filtering
5. ✅ Mobile experience is smooth
6. ✅ Load time < 3s on 3G connection
7. ✅ Zero cross-tenant data leakage
8. ✅ Positive user feedback from pilot

---

**Next Steps**: Implement Phase 1 (Foundation) components
**Estimated Effort**: 5 days (40 hours) for full implementation
**Priority**: HIGH - Enables multi-tenant SaaS launch
