# NetSuite Backup Data Field Mapping - Comprehensive Guide

**Date**: November 10, 2025
**Purpose**: Map NetSuite backup CSV fields to current DentalERP schema across all components
**Target**: Complete end-to-end data flow from NetSuite → Snowflake → Backend API → Frontend

## 📊 NetSuite Backup Data Structure

### 1. Transaction Details (`report_250_transactiondetail.csv`)
**Key Financial Records - Includes Journal Entries, Bills, Invoices**

| NetSuite Field | Sample Data | Data Type | Description |
|----------------|-------------|-----------|-------------|
| Type | "Journal", "Bill", "Invoice" | VARCHAR(50) | Transaction type |
| Date | "11/1/2025" | DATE | Transaction date |
| Document Number | "JE1298", "10339" | VARCHAR(50) | Unique document identifier |
| Name | "321 Crown Dental Laboratory" | VARCHAR(255) | Customer/Vendor name |
| Memo | "Cheryl Cady", "IPS OBJECT FIX FLOW" | TEXT | Transaction description |
| Account | "Labs Expenses : Laboratory Fees" | VARCHAR(255) | Account name with hierarchy |
| Clr | "F" | VARCHAR(1) | Cleared status flag |
| Split | "2000 - Accounts Payable (A/P)" | VARCHAR(255) | Split account or summary |
| Qty | "" (empty) | INTEGER | Quantity (mostly empty) |
| Amount | "$640.54", "($345.83)" | DECIMAL(18,2) | Transaction amount (negative for credits) |

### 2. Customer/Job List (`custjoblist.csv`)
**Customer and Subsidiary Information**

| NetSuite Field | Sample Data | Data Type | Description |
|----------------|-------------|-----------|-------------|
| Inactive | "No" | BOOLEAN | Active status flag |
| ID | "1", "IC Parent Company" | VARCHAR(50) | Internal NetSuite ID |
| Name | "Uncategorized", "IC SCDP San Marcos, LLC" | VARCHAR(255) | Customer/Subsidiary name |
| Duplicate | "" (empty) | VARCHAR(50) | Duplicate check field |
| Primary Contact | "" (empty) | VARCHAR(255) | Primary contact name |
| Category | "" (empty) | VARCHAR(100) | Customer category |
| Primary Subsidiary | "Parent Company : Silver Creek Dental Partners, LLC" | VARCHAR(255) | Subsidiary hierarchy |
| Sales Rep | "" (empty) | VARCHAR(100) | Sales representative |
| Partner | "" (empty) | VARCHAR(100) | Partner assignment |
| Status | "CUSTOMER-Closed Won" | VARCHAR(50) | Customer status |
| Phone | "" (empty) | VARCHAR(50) | Phone number |
| Email | "" (empty) | VARCHAR(255) | Email address |
| Login Access | "No" | VARCHAR(10) | Portal access flag |

### 3. Employee List (`employeelist.csv`)
**Employee/User Information**

| NetSuite Field | Sample Data | Data Type | Description |
|----------------|-------------|-----------|-------------|
| Inactive | "No" | BOOLEAN | Active status flag |
| Picture | "" (empty) | TEXT | Profile picture reference |
| Name | "Barbara Marra", "Brad Starkweather" | VARCHAR(255) | Employee full name |
| Title | "" (empty) | VARCHAR(100) | Job title |
| Location | "" (empty) | VARCHAR(255) | Office location |
| Department | "" (empty) | VARCHAR(100) | Department assignment |
| Supervisor | "" (empty) | VARCHAR(255) | Supervisor name |
| Subsidiary | "Parent Company" | VARCHAR(255) | Subsidiary assignment |
| Contact Info | HTML with email links | TEXT | Contact information |

### 4. Vendor List (`vendorlist.csv`)
**Vendor/Supplier Information**

| NetSuite Field | Sample Data | Data Type | Description |
|----------------|-------------|-----------|-------------|
| Inactive | "No" | BOOLEAN | Active status flag |
| Name | "321 Crown Dental Laboratory", "303 Accounting" | VARCHAR(255) | Vendor company name |
| Duplicate | "" (empty) | VARCHAR(50) | Duplicate check field |
| Category | "" (empty) | VARCHAR(100) | Vendor category/type |
| Primary Subsidiary | "Parent Company : Silver Creek Dental Partners, LLC" | VARCHAR(255) | Subsidiary hierarchy |
| Primary Contact | "" (empty) | VARCHAR(255) | Primary contact name |
| Phone | "(951) 254-9623", "(303) 877-7685" | VARCHAR(50) | Phone number |
| Email | "321crowndentallab@gmail.com", "lschmidt@303accounting.com" | VARCHAR(255) | Email address |
| Login Access | "No" | VARCHAR(10) | Portal access flag |
| Vendor Bank Fees | "No" | VARCHAR(10) | Bank fees flag |

---

## 🔄 Complete Field Mapping Across All Components

### Backend API Schema Mapping

#### 1. Practices Table (PostgreSQL)
```sql
-- From NetSuite Customer/Subsidiary data
practices {
  id: UUID (generated)
  name: "Silver Creek Dental Partners, LLC" ← custjoblist.Name
  description: "Multi-location dental practice group" ← derived
  address: JSON ← parse from subsidiary data
  phone: "(858) 555-0100" ← custjoblist.Phone
  email: "info@silvercreekdp.com" ← custjoblist.Email
  tenantId: "silvercreek" ← hardcoded for Silver Creek
  netsuiteParentId: "1" ← custjoblist.ID (where Name = "Parent Company")
  isActive: true ← !custjoblist.Inactive
}
```

#### 2. Locations Table (PostgreSQL)
```sql
-- From NetSuite Subsidiary data
locations {
  id: UUID (generated)
  practiceId: FK → practices.id
  name: "SCDP Eastlake, LLC" ← custjoblist.Name (IC subsidiaries)
  address: JSON ← parse from subsidiary data
  phone: "(858) 555-0006" ← derived from subsidiary ID
  email: "eastlake@silvercreekdp.com" ← derived
  externalSystemId: "6" ← custjoblist.ID
  externalSystemType: "netsuite" ← hardcoded
  subsidiaryName: "SCDP Eastlake, LLC" ← custjoblist.Name
  isActive: true ← !custjoblist.Inactive
}
```

#### 3. Users Table (PostgreSQL)
```sql
-- From NetSuite Employee data
users {
  id: UUID (generated)
  email: "bmarra@silvercreekdp.com" ← parse from employeelist.Contact Info
  passwordHash: bcrypt hash ← generated
  firstName: "Barbara" ← split employeelist.Name
  lastName: "Marra" ← split employeelist.Name
  role: "manager" ← derived from title/position
  phone: "(858) 555-1001" ← parse from Contact Info
  active: true ← !employeelist.Inactive
}
```

### MCP Server Schema Mapping

#### 1. Tenants Table (PostgreSQL)
```python
# From practice data
tenants {
  id: UUID (generated)
  tenant_code: "silvercreek" ← hardcoded
  tenant_name: "Silver Creek Dental Partners, LLC" ← practices.name
  industry: "dental" ← hardcoded
  products: ["dentalerp"] ← hardcoded
  status: "active" ← practices.isActive
  settings: {timezone, currency, fiscal_year} ← derived
}
```

#### 2. TenantIntegration Table (PostgreSQL)
```python
# NetSuite integration config
tenant_integrations {
  id: UUID (generated)
  tenant_id: FK → tenants.id
  integration_type: "netsuite" ← hardcoded
  integration_config: {
    "account": "7048582" ← NetSuite account ID
    "consumer_key": env var ← from environment
    "consumer_secret": env var ← from environment
    "token_key": env var ← from environment
    "token_secret": env var ← from environment
    "api_url": "https://7048582.suitetalk.api.netsuite.com/services/rest/record/v1" ← derived
  }
  status: "active" ← hardcoded
  sync_config: {
    "incremental": true,
    "sync_frequency": "15m",
    "record_types": [
      "journalEntry", "account", "invoice",
      "customerPayment", "vendorBill",
      "customer", "vendor", "inventoryItem", "subsidiary"
    ]
  }
}
```

### Snowflake Schema Mapping

#### Bronze Layer (Raw NetSuite Data)
```sql
-- Direct from NetSuite API/CSV data
bronze.netsuite_journal_entries {
  id: VARCHAR(50) ← transaction_detail.Document Number (JE*)
  sync_id: VARCHAR(36) ← generated UUID
  tenant_id: VARCHAR(50) ← "silvercreek"
  raw_data: VARIANT ← full JSON from CSV row
  last_modified_date: TIMESTAMP ← transaction_detail.Date
  extracted_at: TIMESTAMP ← current timestamp
  is_deleted: BOOLEAN ← false (default)
}

bronze.netsuite_customers {
  id: VARCHAR(50) ← custjoblist.ID
  sync_id: VARCHAR(36) ← generated UUID
  tenant_id: VARCHAR(50) ← "silvercreek"
  raw_data: VARIANT ← full customer JSON
  last_modified_date: TIMESTAMP ← current timestamp
  extracted_at: TIMESTAMP ← current timestamp
  is_deleted: BOOLEAN ← custjoblist.Inactive = "Yes"
}

bronze.netsuite_vendors {
  id: VARCHAR(50) ← vendorlist row ID
  sync_id: VARCHAR(36) ← generated UUID
  tenant_id: VARCHAR(50) ← "silvercreek"
  raw_data: VARIANT ← full vendor JSON
  last_modified_date: TIMESTAMP ← current timestamp
  extracted_at: TIMESTAMP ← current timestamp
  is_deleted: BOOLEAN ← vendorlist.Inactive = "Yes"
}
```

#### Silver Layer (Cleaned & Typed)
```sql
-- From Bronze layer transformation
silver.fact_netsuite_transactions {
  transaction_key: BIGINT ← auto-increment
  transaction_id: VARCHAR(50) ← bronze.netsuite_journal_entries.id
  internal_id: VARCHAR(50) ← parsed from raw_data
  transaction_type: VARCHAR(50) ← "Journal", "Bill", "Invoice"
  transaction_date: DATE ← transaction_detail.Date
  posting_period: VARCHAR(20) ← derived from date
  amount: DECIMAL(18,2) ← ABS(transaction_detail.Amount)
  debit_amount: DECIMAL(18,2) ← MAX(transaction_detail.Amount, 0)
  credit_amount: DECIMAL(18,2) ← MAX(-transaction_detail.Amount, 0)
  currency: VARCHAR(3) ← "USD"
  exchange_rate: DECIMAL(10,4) ← 1.0000 (default)
  account_key: BIGINT ← FK to dim_netsuite_accounts
  customer_key: BIGINT ← FK to dim_netsuite_customers
  vendor_key: BIGINT ← FK to dim_netsuite_vendors
  subsidiary_id: VARCHAR(50) ← parsed from transaction
  department_id: VARCHAR(50) ← parsed from transaction
  class_id: VARCHAR(50) ← parsed from transaction
  location_id: VARCHAR(50) ← parsed from transaction
  status: VARCHAR(20) ← "Posted"
  memo: TEXT ← transaction_detail.Memo
  created_date: TIMESTAMP ← transaction_detail.Date
  last_modified_date: TIMESTAMP ← current timestamp
  tenant_id: VARCHAR(50) ← "silvercreek"
}
```

#### Gold Layer (Analytics KPIs)
```sql
-- From Silver layer aggregation
gold.daily_financial_metrics {
  metric_date: DATE ← transaction_date
  tenant_id: VARCHAR(50) ← "silvercreek"
  subsidiary: VARCHAR(100) ← subsidiary_name
  total_revenue: DECIMAL(18,2) ← SUM(CASE WHEN account_category = 'Revenue' THEN amount ELSE 0 END)
  total_expenses: DECIMAL(18,2) ← SUM(CASE WHEN account_category = 'Expense' THEN amount ELSE 0 END)
  net_income: DECIMAL(18,2) ← total_revenue - total_expenses
  gross_profit: DECIMAL(18,2) ← total_revenue - COGS
  gross_margin_pct: DECIMAL(5,2) ← (gross_profit / total_revenue) * 100
  cash_receipts: DECIMAL(18,2) ← SUM(customer payments)
  cash_disbursements: DECIMAL(18,2) ← SUM(vendor payments)
  net_cash_flow: DECIMAL(18,2) ← cash_receipts - cash_disbursements
  accounts_receivable: DECIMAL(18,2) ← SUM(AR balance)
  accounts_payable: DECIMAL(18,2) ← SUM(AP balance)
  pms_production: DECIMAL(18,2) ← from PMS integration
  netsuite_revenue: DECIMAL(18,2) ← total_revenue
  variance: DECIMAL(18,2) ← pms_production - netsuite_revenue
  variance_pct: DECIMAL(5,2) ← (variance / pms_production) * 100
  is_anomaly: BOOLEAN ← AI detection
  anomaly_score: FLOAT ← AI confidence
  anomaly_reason: TEXT ← AI explanation
  day_of_week: INTEGER ← EXTRACT(DOW FROM metric_date)
  revenue_7d_avg: DECIMAL(18,2) ← 7-day moving average
  revenue_30d_avg: DECIMAL(18,2) ← 30-day moving average
  revenue_trend: VARCHAR(20) ← "increasing", "decreasing", "stable"
  daily_summary: TEXT ← AI-generated summary
  data_quality_score: FLOAT ← completeness + accuracy score
}
```

### Frontend Dashboard Mapping

#### Executive Dashboard Components
```typescript
// From Gold layer analytics data
interface ExecutiveDashboardData {
  // Financial Summary Card
  totalRevenue: number ← gold.daily_financial_metrics.total_revenue
  totalExpenses: number ← gold.daily_financial_metrics.total_expenses
  netIncome: number ← gold.daily_financial_metrics.net_income
  profitMargin: number ← gold.daily_financial_metrics.gross_margin_pct

  // Cash Flow Card
  cashReceipts: number ← gold.daily_financial_metrics.cash_receipts
  cashDisbursements: number ← gold.daily_financial_metrics.cash_disbursements
  netCashFlow: number ← gold.daily_financial_metrics.net_cash_flow

  // AR/AP Aging Card
  accountsReceivable: number ← gold.daily_financial_metrics.accounts_receivable
  accountsPayable: number ← gold.daily_financial_metrics.accounts_payable

  // Revenue Trend Chart
  dailyRevenue: Array<{
    date: string ← gold.daily_financial_metrics.metric_date
    revenue: number ← gold.daily_financial_metrics.total_revenue
    trend: string ← gold.daily_financial_metrics.revenue_trend
  }>

  // PMS vs NetSuite Reconciliation Card
  pmsProduction: number ← gold.daily_financial_metrics.pms_production
  netsuiteRevenue: number ← gold.daily_financial_metrics.netsuite_revenue
  variance: number ← gold.daily_financial_metrics.variance
  variancePercent: number ← gold.daily_financial_metrics.variance_pct

  // AI Insights Card
  insights: Array<{
    type: string ← gold.ai_financial_insights.insight_type
    title: string ← gold.ai_financial_insights.title
    description: string ← gold.ai_financial_insights.description
    severity: string ← gold.ai_financial_insights.severity
    confidence: number ← gold.ai_financial_insights.confidence_score
  }>

  // Location Performance Table
  locationMetrics: Array<{
    location: string ← gold.daily_financial_metrics.subsidiary
    revenue: number ← gold.daily_financial_metrics.total_revenue
    expenses: number ← gold.daily_financial_metrics.total_expenses
    netIncome: number ← gold.daily_financial_metrics.net_income
    margin: number ← gold.daily_financial_metrics.gross_margin_pct
  }>
}
```

---

## 🎯 Key Financial Records to Extract

### Journal Entries (Priority 1)
```sql
-- From transaction_detail.csv where Type = Journal
SELECT
  Document_Number as journal_entry_id,
  Date as transaction_date,
  Account as account_name,
  Memo as description,
  Amount as amount,
  Name as reference_entity
FROM report_250_transactiondetail.csv
WHERE Type = Journal
ORDER BY Date DESC;
```

### Bills/Invoices (Priority 2)
```sql
-- From transaction_detail.csv where Type IN (Bill, Invoice)
SELECT
  Document_Number as invoice_bill_id,
  Date as transaction_date,
  Name as vendor_customer_name,
  Account as expense_revenue_account,
  Amount as total_amount,
  Memo as description
FROM report_250_transactiondetail.csv
WHERE Type IN (Bill, Invoice)
ORDER BY Date DESC;
```

### Chart of Accounts (Priority 3)
```sql
-- From transaction_detail.csv - unique accounts
SELECT DISTINCT
  Account as account_name,
  CASE
    WHEN Account LIKE '%Revenue%' THEN 'Revenue'
    WHEN Account LIKE '%Expense%' THEN 'Expense'
    WHEN Account LIKE '%Assets%' THEN 'Asset'
    WHEN Account LIKE '%Liabilities%' THEN 'Liability'
    WHEN Account LIKE '%Equity%' THEN 'Equity'
    ELSE 'Other'
  END as account_category
FROM report_250_transactiondetail.csv
WHERE Account IS NOT NULL
ORDER BY Account;
```

---

## 🚀 Implementation Steps

### 1. Data Extraction Script
```python
#!/usr/bin/env python3
"""
Extract NetSuite backup data and map to current schema
"""

import pandas as pd
import json
from datetime import datetime

def extract_netsuite_backup_data():
    """Extract and transform NetSuite backup CSV files"""

    # Load CSV files
    transactions = pd.read_csv('/opt/dental-erp/backup/report_250_transactiondetail.csv', skiprows=5)
    customers = pd.read_csv('/opt/dental-erp/backup/custjoblist.csv', skiprows=3)
    employees = pd.read_csv('/opt/dental-erp/backup/employeelist.csv', skiprows=3)
    vendors = pd.read_csv('/opt/dental-erp/backup/vendorlist.csv', skiprows=3)

    # Clean and standardize data
    # ... transformation logic ...

    return {
        'journal_entries': journal_entries,
        'customers': customers_clean,
        'vendors': vendors_clean,
        'accounts': chart_of_accounts,
        'transactions': transactions_clean
    }

if __name__ == "__main__":
    data = extract_netsuite_backup_data()
    print("NetSuite backup data extracted successfully!")
```

### 2. Backend Seeding Script
```typescript
/**
 * Seed backend database with NetSuite backup data
 */
import { db } from '../src/database';
import { practices, locations, users, userPractices } from '../src/database/schema';

async function seedNetSuiteBackupData() {
  // 1. Seed practices from NetSuite customers
  // 2. Seed locations from NetSuite subsidiaries
  // 3. Seed users from NetSuite employees
  // 4. Create relationships
}
```

### 3. MCP Server Seeding Script
```python
"""
Seed MCP server with NetSuite integration data
"""
from src.models.tenant import Tenant, TenantIntegration, TenantWarehouse
from src.core.database import get_db

async def seed_mcp_netsuite_data():
    """Seed MCP server with tenant and integration data"""
    # Create Silver Creek tenant
    # Create NetSuite integration
    # Create Snowflake warehouse
    pass
```

### 4. Snowflake Data Loading
```sql
-- Load transformed data into Snowflake Bronze tables
COPY INTO bronze.netsuite_journal_entries
FROM @netsuite_backup_stage/journal_entries.csv
FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1);

COPY INTO bronze.netsuite_customers
FROM @netsuite_backup_stage/customers.csv
FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1);

-- Trigger dynamic table refresh
ALTER DYNAMIC TABLE silver.fact_netsuite_transactions REFRESH;
ALTER DYNAMIC TABLE gold.daily_financial_metrics REFRESH;
```

---

## ✅ Verification Checklist

- [ ] All journal entries extracted from transaction details
- [ ] Customer/subsidiary data mapped to practices/locations
- [ ] Employee data mapped to users with proper roles
- [ ] Vendor data mapped to vendor records
- [ ] Chart of accounts extracted and categorized
- [ ] Backend database seeded with mapped data
- [ ] MCP server tenant and integration configured
- [ ] Snowflake Bronze tables loaded with backup data
- [ ] Silver dynamic tables refreshed successfully
- [ ] Gold KPI tables calculated correctly
- [ ] Frontend dashboard displays financial metrics
- [ ] Multi-location view shows all 9 subsidiaries
- [ ] PMS vs NetSuite reconciliation variance calculated
- [ ] AI insights generated from financial patterns

---

**Status**: ✅ Field mapping complete - Ready for implementation
**Next Steps**: Execute data extraction and seeding scripts
**Files Created**: docs/NETSUITE-BACKUP-FIELD-MAPPING.md