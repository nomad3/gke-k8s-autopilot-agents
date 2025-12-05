# NetSuite Complete Data Flow Mapping
## Silver/Gold Layers → MCP Server → Backend API → Frontend

This document provides comprehensive field mapping for the entire NetSuite data flow in our BI platform, from the Silver/Gold data warehouse layers through the MCP server to the backend API and frontend components.

## Data Architecture Overview

```
NetSuite (Source) → Bronze Layer → Silver Layer → Gold Layer → MCP Server → Backend API → Frontend
```

## 1. Snowflake Data Warehouse Schema

### Bronze Layer (Raw Data)
```sql
-- Raw NetSuite data as ingested
CREATE TABLE bronze.netsuite_journalentry (
    id VARCHAR,
    tenant_id VARCHAR,
    subsidiary_id VARCHAR,
    raw_data VARIANT,
    ingested_at TIMESTAMP
);

CREATE TABLE bronze.netsuite_account (
    id VARCHAR,
    tenant_id VARCHAR,
    subsidiary_id VARCHAR,
    raw_data VARIANT,
    ingested_at TIMESTAMP
);
```

### Silver Layer (Cleaned & Standardized)
```sql
-- Standardized financial data
CREATE TABLE silver.stg_netsuite_journal_entries (
    journal_entry_id VARCHAR,
    subsidiary_id VARCHAR,
    transaction_date DATE,
    account_id VARCHAR,
    account_name VARCHAR,
    debit_amount DECIMAL(15,2),
    credit_amount DECIMAL(15,2),
    description VARCHAR,
    reference_entity VARCHAR,
    currency VARCHAR,
    exchange_rate DECIMAL(10,4)
);

CREATE TABLE silver.stg_netsuite_accounts (
    account_id VARCHAR,
    account_number VARCHAR,
    account_name VARCHAR,
    account_type VARCHAR,
    account_category VARCHAR,
    parent_account VARCHAR,
    subsidiary_id VARCHAR,
    is_active BOOLEAN,
    balance DECIMAL(15,2)
);
```

### Gold Layer (Analytics-Ready)
```sql
-- Aggregated metrics for BI
CREATE TABLE gold.daily_financial_metrics (
    subsidiary_id VARCHAR,
    report_date DATE,
    total_production DECIMAL(15,2),
    total_collections DECIMAL(15,2),
    total_expenses DECIMAL(15,2),
    net_income DECIMAL(15,2),
    profit_margin DECIMAL(5,2),
    patient_visits INTEGER,
    production_per_visit DECIMAL(10,2),
    collection_rate DECIMAL(5,2)
);

CREATE TABLE gold.subsidiary_performance (
    subsidiary_id VARCHAR,
    subsidiary_name VARCHAR,
    ranking_period VARCHAR,
    revenue_rank INTEGER,
    profit_rank INTEGER,
    growth_rate DECIMAL(5,2),
    efficiency_score DECIMAL(5,2)
);
```

## 2. MCP Server Data Models

### Tenant Context
```python
class TenantContext:
    tenant_id: str  # "silvercreek"
    tenant_code: str  # "silvercreek"
    subsidiaries: List[Dict]  # All 11 Silver Creek locations
```

### NetSuite Connector Response
```python
{
    "subsidiary_id": "1",
    "subsidiary_name": "Silver Creek Dental Partners, LLC",
    "financial_metrics": {
        "total_revenue": 1250000.00,
        "total_expenses": 980000.00,
        "net_income": 270000.00,
        "profit_margin": 21.60,
        "journal_entry_count": 45,
        "account_count": 25,
        "customer_count": 8,
        "vendor_count": 12
    },
    "journal_entries": [
        {
            "journal_entry_id": "JE202511001",
            "transaction_date": "2025-11-01",
            "account_name": "Production Income",
            "debit_amount": 0,
            "credit_amount": 15000.00,
            "description": "Monthly production revenue",
            "reference_entity": "Patient Services"
        }
    ],
    "chart_of_accounts": [
        {
            "account_number": "4000",
            "account_name": "Production Income",
            "account_category": "Revenue",
            "account_type": "Income",
            "balance": 1250000.00
        }
    ],
    "customers": [...],
    "vendors": [...]
}
```

### Analytics API Response
```python
{
    "status": "success",
    "data": {
        "consolidated_metrics": {
            "total_subsidiaries": 11,
            "consolidated_revenue": 9670000.00,
            "consolidated_expenses": 7780000.00,
            "consolidated_net_income": 1890000.00,
            "consolidated_profit_margin": 19.54
        },
        "subsidiary_performance": [
            {
                "subsidiary_id": "1",
                "subsidiary_name": "Silver Creek Dental Partners, LLC",
                "total_revenue": 1250000.00,
                "profit_margin": 21.60,
                "revenue_rank": 1,
                "profit_rank": 1
            }
        ],
        "kpi_metrics": [
            {
                "kpi_name": "Daily Production",
                "current_value": 15000.00,
                "target_value": 16000.00,
                "trend_direction": "up",
                "trend_percentage": 3.45,
                "is_healthy": true
            }
        ]
    },
    "metadata": {
        "calculation_date": "2025-11-10",
        "data_quality_score": 94.5,
        "last_sync": "2025-11-10T15:30:00Z"
    }
}
```

## 3. Backend API Schema (PostgreSQL)

### Core Tables
```sql
-- Enhanced practices table with financial data
CREATE TABLE practices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(50) NOT NULL,
    netsuite_parent_id VARCHAR(50),
    settings JSONB,
    financial_metrics JSONB,
    is_active BOOLEAN DEFAULT true
);

-- Locations with subsidiary mapping
CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    practice_id UUID REFERENCES practices(id),
    name VARCHAR(255) NOT NULL,
    subsidiary_name VARCHAR(255),
    external_system_id VARCHAR(100),
    external_system_type VARCHAR(50),
    settings JSONB,
    financial_metrics JSONB,
    is_active BOOLEAN DEFAULT true
);

-- NetSuite-specific financial tables
CREATE TABLE netsuite_financial_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subsidiary_id VARCHAR(50) NOT NULL,
    total_revenue DECIMAL(15,2),
    total_expenses DECIMAL(15,2),
    net_income DECIMAL(15,2),
    profit_margin DECIMAL(5,2),
    calculation_date DATE
);
```

### BI-Extended Tables
```sql
-- Daily time-series metrics
CREATE TABLE netsuite_daily_metrics (
    subsidiary_id VARCHAR(50) NOT NULL,
    metric_date DATE NOT NULL,
    daily_revenue DECIMAL(15,2),
    daily_expenses DECIMAL(15,2),
    patient_visits INTEGER,
    production_per_visit DECIMAL(10,2),
    collection_rate DECIMAL(5,2),
    new_patients INTEGER,
    cancellation_rate DECIMAL(5,2)
);

-- KPI tracking for dashboards
CREATE TABLE netsuite_kpi_metrics (
    subsidiary_id VARCHAR(50) NOT NULL,
    kpi_name VARCHAR(100) NOT NULL,
    kpi_category VARCHAR(50), -- 'financial', 'operational', 'clinical'
    current_value DECIMAL(15,2),
    target_value DECIMAL(15,2),
    trend_direction VARCHAR(20),
    trend_percentage DECIMAL(5,2),
    is_healthy BOOLEAN,
    period_type VARCHAR(20)
);

-- Comparative analysis
CREATE TABLE netsuite_comparative_analysis (
    subsidiary_id VARCHAR(50) NOT NULL,
    comparison_period VARCHAR(20),
    current_period_revenue DECIMAL(15,2),
    previous_period_revenue DECIMAL(15,2),
    revenue_growth_rate DECIMAL(5,2),
    current_period_profit_margin DECIMAL(5,2),
    margin_improvement DECIMAL(5,2)
);
```

## 4. Backend API Endpoints

### Financial Analytics Endpoints
```typescript
// GET /api/analytics/netsuite/consolidated
interface ConsolidatedMetricsResponse {
  totalSubsidiaries: number;
  consolidatedRevenue: number;
  consolidatedExpenses: number;
  consolidatedNetIncome: number;
  consolidatedProfitMargin: number;
  totalJournalEntries: number;
  totalAccounts: number;
  dataQualityScore: number;
}

// GET /api/analytics/netsuite/subsidiaries
interface SubsidiaryPerformanceResponse {
  subsidiaries: Array<{
    subsidiaryId: string;
    subsidiaryName: string;
    totalRevenue: number;
    totalExpenses: number;
    netIncome: number;
    profitMargin: number;
    revenueRank: number;
    profitRank: number;
    journalEntryCount: number;
    accountCount: number;
  }>;
}

// GET /api/analytics/netsuite/daily-metrics
interface DailyMetricsResponse {
  dailyMetrics: Array<{
    subsidiaryId: string;
    metricDate: string;
    dailyRevenue: number;
    dailyExpenses: number;
    dailyNetIncome: number;
    patientVisits: number;
    productionPerVisit: number;
    collectionRate: number;
    newPatients: number;
    cancellationRate: number;
  }>;
}

// GET /api/analytics/netsuite/kpi-dashboard
interface KPIDashboardResponse {
  kpis: Array<{
    subsidiaryId: string;
    kpiName: string;
    kpiCategory: string;
    currentValue: number;
    targetValue: number;
    trendDirection: string;
    trendPercentage: number;
    isHealthy: boolean;
    healthIndicator: string;
  }>;
}
```

## 5. Frontend Components & Data Binding

### Dashboard Components
```typescript
// Executive Dashboard Component
interface ExecutiveDashboardProps {
  consolidatedMetrics: ConsolidatedMetricsResponse;
  subsidiaryPerformance: SubsidiaryPerformanceResponse;
  kpiDashboard: KPIDashboardResponse;
}

// Component data mapping
const ExecutiveDashboard: React.FC = () => {
  const { data: consolidated } = useAnalytics('netsuite/consolidated');
  const { data: performance } = useAnalytics('netsuite/subsidiaries');
  const { data: kpis } = useAnalytics('netsuite/kpi-dashboard');

  return (
    <div className="executive-dashboard">
      {/* Consolidated Metrics Cards */}
      <KPIWidget
        title="Consolidated Revenue"
        value={consolidated?.consolidatedRevenue}
        format="currency"
        trend={consolidated?.trend}
      />

      {/* Subsidiary Performance Table */}
      <DataTable
        data={performance?.subsidiaries}
        columns={[
          { field: 'subsidiaryName', header: 'Location' },
          { field: 'totalRevenue', header: 'Revenue', format: 'currency' },
          { field: 'profitMargin', header: 'Margin %', format: 'percentage' },
          { field: 'revenueRank', header: 'Revenue Rank' }
        ]}
      />

      {/* KPI Health Dashboard */}
      <KPIHealthGrid kpis={kpis?.kpis} />
    </div>
  );
};
```

### Chart Components
```typescript
// Financial Trend Chart
interface FinancialTrendChartProps {
  dailyMetrics: DailyMetricsResponse;
}

const FinancialTrendChart: React.FC = ({ dailyMetrics }) => {
  const chartData = dailyMetrics?.dailyMetrics.map(metric => ({
    date: metric.metricDate,
    revenue: metric.dailyRevenue,
    expenses: metric.dailyExpenses,
    netIncome: metric.dailyNetIncome,
    visits: metric.patientVisits
  }));

  return (
    <LineChart
      data={chartData}
      xAxis={{ dataKey: 'date' }}
      yAxis={{ tickFormatter: (value) => `$${value.toLocaleString()}` }}
      series={[
        { name: 'Revenue', dataKey: 'revenue', color: '#10b981' },
        { name: 'Expenses', dataKey: 'expenses', color: '#ef4444' },
        { name: 'Net Income', dataKey: 'netIncome', color: '#3b82f6' }
      ]}
    />
  );
};
```

## 6. Complete Field Mapping Reference

### Revenue Fields Mapping
```
NetSuite → Bronze → Silver → Gold → MCP → Backend → Frontend
─────────────────────────────────────────────────────────────────
Production → raw_data → total_production → daily_revenue → totalRevenue → total_revenue → Revenue
Collections → raw_data → total_collections → daily_collections → totalCollections → collection_amount → Collections
Income → calculated → net_income → daily_net_income → netIncome → net_income → Net Income
```

### Operational Fields Mapping
```
NetSuite → Bronze → Silver → Gold → MCP → Backend → Frontend
─────────────────────────────────────────────────────────────────
Patient Count → raw_data → patient_visits → patient_visits → patientVisits → patient_visits → Patient Visits
Visit Value → calculated → production_per_visit → production_per_visit → productionPerVisit → production_per_visit → $/Visit
Collection Rate → calculated → collection_rate → collection_rate → collectionRate → collection_rate → Collection %
```

### Ranking & Comparison Fields
```
NetSuite → Bronze → Silver → Gold → MCP → Backend → Frontend
─────────────────────────────────────────────────────────────────
Subsidiary → subsidiary_id → subsidiary_id → subsidiary_id → subsidiaryId → subsidiary_id → Location Name
Revenue Rank → calculated → revenue_rank → revenue_rank → revenueRank → revenue_rank → Revenue Rank
Profit Rank → calculated → profit_rank → profit_rank → profitRank → profit_rank → Profit Rank
```

## 7. Data Quality & Validation

### Quality Metrics
```typescript
interface DataQualityMetrics {
  completenessScore: number;      // 0-100%
  accuracyScore: number;          // 0-100%
  timelinessScore: number;        // 0-100%
  consistencyScore: number;       // 0-100%
  overallQualityScore: number;    // 0-100%
  dataFreshnessHours: number;     // Hours since last sync
  lastSyncTimestamp: string;      // ISO timestamp
}
```

### Validation Rules
```sql
-- Data completeness validation
SELECT
    subsidiary_id,
    COUNT(CASE WHEN total_revenue IS NULL THEN 1 END) as missing_revenue,
    COUNT(CASE WHEN total_expenses IS NULL THEN 1 END) as missing_expenses,
    COUNT(*) as total_records,
    (COUNT(*) - COUNT(CASE WHEN total_revenue IS NULL OR total_expenses IS NULL THEN 1 END)) * 100.0 / COUNT(*) as completeness_pct
FROM netsuite_financial_metrics
WHERE calculation_date = CURRENT_DATE;

-- Financial calculation accuracy validation
SELECT
    subsidiary_id,
    CASE
        WHEN ABS(net_income - (total_revenue - total_expenses)) < 0.01 THEN 'ACCURATE'
        ELSE 'INACCURATE'
    END as calculation_status,
    COUNT(*) as record_count
FROM netsuite_financial_metrics
WHERE calculation_date = CURRENT_DATE
GROUP BY subsidiary_id, calculation_status;
```

## 8. API Response Examples

### Consolidated Metrics
```json
{
  "status": "success",
  "data": {
    "totalSubsidiaries": 11,
    "consolidatedRevenue": 9670000.00,
    "consolidatedExpenses": 7780000.00,
    "consolidatedNetIncome": 1890000.00,
    "consolidatedProfitMargin": 19.54,
    "totalJournalEntries": 385,
    "totalAccounts": 220,
    "dataQualityScore": 94.5
  },
  "metadata": {
    "calculationDate": "2025-11-10",
    "dataSource": "NetSuite",
    "lastSync": "2025-11-10T15:30:00Z"
  }
}
```

### Subsidiary Performance
```json
{
  "status": "success",
  "data": {
    "subsidiaries": [
      {
        "subsidiaryId": "1",
        "subsidiaryName": "Silver Creek Dental Partners, LLC",
        "totalRevenue": 1250000.00,
        "totalExpenses": 980000.00,
        "netIncome": 270000.00,
        "profitMargin": 21.60,
        "revenueRank": 1,
        "profitRank": 1,
        "journalEntryCount": 45,
        "accountCount": 25
      },
      {
        "subsidiaryId": "2",
        "subsidiaryName": "SCDP San Marcos, LLC",
        "totalRevenue": 890000.00,
        "totalExpenses": 720000.00,
        "netIncome": 170000.00,
        "profitMargin": 19.10,
        "revenueRank": 4,
        "profitRank": 5,
        "journalEntryCount": 38,
        "accountCount": 22
      }
    ]
  }
}
```

## 9. Error Handling & Status Codes

### Common Error Responses
```json
{
  "status": "error",
  "error": {
    "code": "NETSUITE_SYNC_FAILED",
    "message": "NetSuite synchronization failed due to authentication error",
    "details": {
      "subsidiary_id": "1",
      "error_type": "authentication",
      "retry_possible": true
    }
  }
}
```

### Status Codes
- `200` - Success with data
- `201` - Data created successfully
- `204` - Success with no content
- `400` - Bad request (invalid parameters)
- `401` - Unauthorized (invalid API key)
- `403` - Forbidden (insufficient permissions)
- `404` - Data not found
- `422` - Validation error
- `500` - Internal server error
- `503` - Service unavailable (NetSuite down)

## 10. Performance Optimization

### Database Indexes
```sql
-- Performance indexes
CREATE INDEX idx_netsuite_metrics_date ON netsuite_financial_metrics(calculation_date);
CREATE INDEX idx_journal_entries_date ON netsuite_journal_entries(transaction_date);
CREATE INDEX idx_daily_metrics_subsidiary ON netsuite_daily_metrics(subsidiary_id, metric_date);
CREATE INDEX idx_kpi_metrics_subsidiary ON netsuite_kpi_metrics(subsidiary_id, calculation_date);
```

### Caching Strategy
```typescript
// Redis caching for frequently accessed data
const cacheKeys = {
  consolidatedMetrics: 'netsuite:consolidated:metrics',
  subsidiaryPerformance: 'netsuite:subsidiaries:performance',
  kpiDashboard: 'netsuite:kpi:dashboard',
  dailyMetrics: 'netsuite:daily:metrics'
};

// Cache TTL: 15 minutes for real-time data, 1 hour for historical
const cacheTTL = {
  realTime: 900,    // 15 minutes
  historical: 3600  // 1 hour
};
```

This comprehensive mapping ensures data consistency and proper flow from NetSuite through all layers to the frontend dashboard, supporting our BI platform's analytics requirements. The structure is designed to handle multi-tenant scenarios and provide real-time financial insights across all Silver Creek subsidiaries.,