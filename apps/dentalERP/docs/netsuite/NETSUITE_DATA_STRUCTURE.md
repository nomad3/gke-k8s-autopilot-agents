# NetSuite Data Structure Mapping

## Overview

This document describes how NetSuite financial data flows from the backup CSV through the Bronze → Silver → Gold transformation pipeline.

**Last Updated**: November 12, 2025

---

## Source Data: CSV Backup

### File Location
```
backup/report_250_transactiondetail.csv
```

### CSV Structure

**Report Header:**
- Line 1: Company Name: "Silver Creek Dental Partners, LLC"
- Line 2: Report Type: "Parent Company (Consolidated)"
- Line 3: Report Name: "Transaction Detail"
- Line 4: Date Range: "November 1, 2025 - November 30, 2025"
- Line 5-6: Blank lines
- Line 7: Column headers

**Column Headers:**
```
Type, Date, Document Number, Name, Memo, Account, Clr, Split, Qty, Amount
```

### Data Fields

| Field | Description | Example |
|-------|-------------|---------|
| **Type** | Transaction type | Bill, Bill Payment, Invoice, Customer Payment, Journal Entry |
| **Date** | Transaction date (MM/DD/YYYY) | 11/1/2025 |
| **Document Number** | Transaction reference number | 10339, INV-0004805 |
| **Name** | Entity name (vendor/customer) | 321 Crown Dental Laboratory, Glidewell Laboratories |
| **Memo** | Transaction description | Cheryl Cady, Monthly rental fees |
| **Account** | Account name with hierarchy | Labs Expenses : Laboratory Fees, 2000 - Accounts Payable (A/P) |
| **Clr** | Cleared flag | F (cleared), blank (uncleared) |
| **Split** | Split account or "- Split -" | 2000 - Accounts Payable (A/P), - Split - |
| **Qty** | Quantity (usually blank) | (blank) |
| **Amount** | Transaction amount | $640.54, ($12,206.75) |

### Account Naming Patterns

**Pattern 1: Category : Subcategory**
```
Labs Expenses : Laboratory Fees
Facility Expenses : Rent Payments
Facility Expenses : Other Lease (Prop Taxes,Ins,CAM)
Marketing : Digital Marketing
Operating Expenses : Telephone, Computer & Internet
Payroll Expenses : Salaries & Wages
```

**Pattern 2: Number - Account Name**
```
2000 - Accounts Payable (A/P)
1076 - Eastlake Ramp AP
1088 - San Marcos II Ramp AP
2025 - SCDP Torrey Pines Ramp Card
6103 - Facility Expenses : Other Lease (Prop Taxes,Ins,CAM)
6302 - Marketing : Digital Marketing
6425 - Operating Expenses : Telephone, Computer & Internet
```

### Transaction Types

1. **Bill** - Vendor invoices for goods/services
2. **Bill Payment** - Payments made to vendors
3. **Invoice** - Customer invoices for services rendered
4. **Customer Payment** - Payments received from customers
5. **Journal Entry** - Manual accounting entries
6. **Deposit** - Bank deposits
7. **Check** - Check payments
8. **Credit Memo** - Customer credits
9. **Vendor Credit** - Vendor credits

### Amount Format

- **Positive amounts**: Standard expenses or credits (e.g., $640.54)
- **Negative amounts (in parentheses)**: Contra entries or reversals (e.g., ($12,206.75))
- **Currency formatting**: Includes $ symbol and thousands separators (,)

### Example Transactions

**Bill Transaction (Expense):**
```csv
Bill,11/1/2025,10339,321 Crown Dental Laboratory,Cheryl Cady,Labs Expenses : Laboratory Fees,F,2000 - Accounts Payable (A/P),,$640.54
```
- **Debit**: Labs Expenses : Laboratory Fees = $640.54
- **Credit**: Accounts Payable (A/P) = $640.54

**Bill with Split Entry:**
```csv
Bill,11/1/2025,4,"Laguna Crown, LLC",Rent,Facility Expenses : Rent Payments,F,2000 - Accounts Payable (A/P),,"$10,046.75"
Bill,11/1/2025,4,"Laguna Crown, LLC",Rent,Accounts Payable (A/P),F,- Split -,,"($12,206.75)"
```
- Multiple line items for single bill
- Negative amount shows contra entry (total A/P liability)

**Bill Payment Transaction:**
```csv
Bill Payment,11/7/2025,78,Glidewell Laboratories,Indah Jackson,Eastlake Ramp AP,F,2000 - Accounts Payable (A/P),,($113.67)
Bill Payment,11/7/2025,78,Glidewell Laboratories,,Accounts Payable (A/P),F,1076 - Eastlake Ramp AP,,$113.67
```
- **Debit**: Accounts Payable (A/P) = $113.67 (reduces liability)
- **Credit**: Eastlake Ramp AP = $113.67 (payment from Ramp card)

---

## Bronze Layer: Raw Ingestion

### Table: `bronze.netsuite_transactions`

**Purpose**: Store raw transaction data from CSV with minimal transformation

**Schema:**
```sql
CREATE TABLE bronze.netsuite_transactions (
    id VARCHAR(50) PRIMARY KEY,
    sync_id VARCHAR(36),
    tenant_id VARCHAR(50),
    transaction_type VARCHAR(50),              -- Normalized type (vendor_bill, bill_payment, etc.)
    transaction_date DATE,
    document_number VARCHAR(100),
    entity_name VARCHAR(255),                  -- Vendor or customer name
    memo TEXT,
    account_number VARCHAR(50),                -- Extracted from account string
    account_name VARCHAR(255),                 -- Full account name
    account_category VARCHAR(100),             -- Top-level category
    account_subcategory VARCHAR(255),          -- Subcategory if applicable
    split_account VARCHAR(255),                -- Split account name
    debit_amount DECIMAL(15,2),                -- Debit amount (positive)
    credit_amount DECIMAL(15,2),               -- Credit amount (positive)
    amount DECIMAL(15,2),                      -- Original signed amount
    raw_data VARIANT,                          -- Full CSV row as JSON
    extracted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    _ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

### Transformation Logic

**Transaction Type Mapping:**
```python
{
    "Bill": "vendor_bill",
    "Bill Payment": "bill_payment",
    "Invoice": "invoice",
    "Customer Payment": "customer_payment",
    "Journal Entry": "journal_entry",
    "Deposit": "deposit",
    "Check": "check",
    "Credit Memo": "credit_memo",
    "Vendor Credit": "vendor_credit"
}
```

**Account Category Mapping:**
```python
{
    "Labs Expenses": "Operating Expenses",
    "Facility Expenses": "Operating Expenses",
    "Marketing": "Operating Expenses",
    "Operating Expenses": "Operating Expenses",
    "Payroll Expenses": "Operating Expenses",
    "Accounts Payable (A/P)": "Current Liabilities",
    "Production Income": "Revenue",
    "Collections": "Revenue",
    "Ramp AP": "Current Assets",
    "Ramp Card": "Current Assets"
}
```

**Debit/Credit Rules:**
```python
# Negative amounts (in parentheses)
if amount < 0:
    if "Accounts Payable" in account_name or "Split" in account_name:
        debit = abs(amount), credit = 0
    else:
        debit = 0, credit = abs(amount)

# Positive amounts
else:
    if "Income" or "Revenue" or "Collections" in account_name:
        debit = 0, credit = amount  # Revenue accounts
    elif "Expense" or "Labs" or "Payroll" in account_name:
        debit = amount, credit = 0  # Expense accounts
    elif "Accounts Payable" in account_name:
        debit = 0, credit = amount  # A/P liability
    else:
        debit = amount, credit = 0  # Default to debit
```

### Data Quality Checks

1. **Balance Check**: Total debits should equal total credits
2. **Date Validation**: All dates should be valid and within expected range
3. **Entity Mapping**: All vendor/customer names should be non-null for relevant transactions
4. **Account Classification**: All accounts should map to valid categories
5. **Amount Parsing**: All amounts should parse to valid decimals

---

## Silver Layer: Cleaned & Standardized

### Table: `bronze_silver.stg_netsuite_transactions`

**Purpose**: Cleaned, typed, and enriched transaction data ready for analytics

**Expected Schema:**
```sql
CREATE TABLE bronze_silver.stg_netsuite_transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    transaction_date DATE NOT NULL,
    transaction_month VARCHAR(7),               -- YYYY-MM format
    document_number VARCHAR(100),
    entity_name VARCHAR(255),
    entity_type VARCHAR(50),                    -- vendor, customer, internal
    memo TEXT,
    account_number VARCHAR(50),
    account_name VARCHAR(255) NOT NULL,
    account_category VARCHAR(100) NOT NULL,
    account_subcategory VARCHAR(255),
    account_type VARCHAR(50),                   -- asset, liability, equity, revenue, expense
    split_account VARCHAR(255),
    debit_amount DECIMAL(15,2) NOT NULL DEFAULT 0,
    credit_amount DECIMAL(15,2) NOT NULL DEFAULT 0,
    net_amount DECIMAL(15,2),                   -- debit - credit
    is_split_entry BOOLEAN,
    location_code VARCHAR(50),                  -- Extracted from account or entity
    subsidiary_id VARCHAR(10),                  -- Mapped subsidiary ID
    is_valid BOOLEAN DEFAULT TRUE,
    validation_notes TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

### Silver Layer Transformations

1. **Type Casting**: Ensure all numeric fields are proper DECIMAL types
2. **Date Enrichment**: Add transaction_month for aggregation
3. **Entity Classification**: Determine if entity is vendor, customer, or internal
4. **Account Type Mapping**: Map categories to financial statement types (asset, liability, equity, revenue, expense)
5. **Location Extraction**: Extract location codes from account names or entity names
6. **Subsidiary Mapping**: Map location codes to subsidiary IDs
7. **Split Detection**: Flag split entries for proper handling
8. **Null Handling**: Replace nulls with appropriate defaults
9. **Validation**: Add validation flags and notes
10. **Outlier Detection**: Flag unusual amounts or patterns

---

## Gold Layer: Analytics-Ready

### Table: `bronze_gold.financial_metrics`

**Purpose**: Pre-aggregated financial metrics for dashboard consumption

**Schema:**
```sql
CREATE TABLE bronze_gold.financial_metrics (
    metric_id VARCHAR(50) PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    period_type VARCHAR(20),                    -- daily, monthly, quarterly, yearly
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    subsidiary_id VARCHAR(10),
    location_code VARCHAR(50),

    -- Revenue Metrics
    total_revenue DECIMAL(15,2) DEFAULT 0,
    production_income DECIMAL(15,2) DEFAULT 0,
    collections DECIMAL(15,2) DEFAULT 0,
    other_revenue DECIMAL(15,2) DEFAULT 0,

    -- Expense Metrics
    total_expenses DECIMAL(15,2) DEFAULT 0,
    lab_expenses DECIMAL(15,2) DEFAULT 0,
    facility_expenses DECIMAL(15,2) DEFAULT 0,
    marketing_expenses DECIMAL(15,2) DEFAULT 0,
    operating_expenses DECIMAL(15,2) DEFAULT 0,
    payroll_expenses DECIMAL(15,2) DEFAULT 0,

    -- Profitability Metrics
    gross_profit DECIMAL(15,2),
    net_income DECIMAL(15,2),
    profit_margin DECIMAL(5,2),

    -- Operational Metrics
    accounts_payable_balance DECIMAL(15,2),
    accounts_receivable_balance DECIMAL(15,2),
    working_capital DECIMAL(15,2),

    -- Transaction Volume
    transaction_count INTEGER DEFAULT 0,
    vendor_count INTEGER DEFAULT 0,
    customer_count INTEGER DEFAULT 0,

    -- KPIs
    revenue_per_transaction DECIMAL(15,2),
    expense_ratio DECIMAL(5,2),
    collection_rate DECIMAL(5,2),

    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

### Gold Layer Aggregations

1. **Revenue Aggregation**: Sum revenue by category and period
2. **Expense Aggregation**: Sum expenses by category and period
3. **Profitability Calculation**: Gross profit, net income, profit margin
4. **Balance Calculations**: A/P balance, A/R balance, working capital
5. **Volume Metrics**: Transaction counts, entity counts
6. **KPI Calculations**: Per-transaction metrics, ratios, rates
7. **Period Comparisons**: Month-over-month, year-over-year
8. **Subsidiary Rollups**: Location-specific and consolidated metrics

---

## Data Flow Summary

```
CSV Backup (report_250_transactiondetail.csv)
    │
    ├─ Header: Company, Report Type, Date Range
    ├─ Columns: Type, Date, Document Number, Name, Memo, Account, Amount
    ├─ 686 transaction lines (Nov 1-30, 2025)
    └─ Account patterns: "Category : Subcategory", "Number - Name"

    ▼ [seed-netsuite-from-csv.py]

Bronze Layer (bronze.netsuite_transactions)
    │
    ├─ Raw transaction data
    ├─ Parsed account structure
    ├─ Debit/credit calculation
    ├─ Entity extraction
    └─ Data quality validation

    ▼ [dbt: stg_netsuite_transactions.sql]

Silver Layer (bronze_silver.stg_netsuite_transactions)
    │
    ├─ Typed and cleaned data
    ├─ Enriched with period info
    ├─ Entity classification
    ├─ Location/subsidiary mapping
    └─ Validation flags

    ▼ [dbt: financial_metrics.sql]

Gold Layer (bronze_gold.financial_metrics)
    │
    ├─ Pre-aggregated metrics
    ├─ Revenue/expense by category
    ├─ Profitability calculations
    ├─ KPI calculations
    └─ Dashboard-ready data

    ▼ [MCP API: /api/v1/analytics/*]

Frontend Dashboard
    │
    ├─ Executive view
    ├─ Subsidiary comparison
    ├─ Vendor analysis
    ├─ Expense tracking
    └─ Financial reporting
```

---

## Seed Script Usage

### 1. Tenant & Integration Setup
```bash
cd mcp-server
python scripts/seed-netsuite-mcp-data.py
```

**What it does:**
- Creates `silvercreek` tenant
- Sets up Snowflake warehouse connection
- Configures NetSuite integration
- Maps subsidiary structure

### 2. CSV Data Import
```bash
cd mcp-server
python scripts/seed-netsuite-from-csv.py
```

**What it does:**
- Reads `backup/report_250_transactiondetail.csv`
- Parses 686 transaction lines
- Transforms to Bronze layer format
- Inserts into `bronze.netsuite_transactions`
- Validates debit/credit balance
- Generates summary statistics

**Expected Output:**
```
Transactions Parsed: 686
Transactions Inserted to Bronze: 686
Total Debits: $XXX,XXX.XX
Total Credits: $XXX,XXX.XX
Balance Check: $0.00 (should be zero)
Date Range: 2025-11-01 to 2025-11-30
Unique Entities: ~50 vendors/customers
```

### 3. dbt Transformation
```bash
cd dbt/dentalerp
dbt run --select stg_netsuite_transactions+
```

**What it does:**
- Transforms Bronze → Silver → Gold
- Runs data quality tests
- Generates analytics tables

---

## Next Steps

1. **Verify Bronze Layer**: Check that all 686 transactions loaded correctly
2. **Review Mappings**: Validate account category and subsidiary mappings
3. **Test Transformations**: Run dbt and verify Silver layer output
4. **Validate Metrics**: Check Gold layer calculations match expectations
5. **API Integration**: Test MCP analytics endpoints with new data
6. **Dashboard Testing**: Verify frontend displays metrics correctly

---

## References

- CSV Source: `/backup/report_250_transactiondetail.csv`
- Bronze Seed Script: `/mcp-server/scripts/seed-netsuite-from-csv.py`
- Tenant Setup Script: `/mcp-server/scripts/seed-netsuite-mcp-data.py`
- NetSuite Integration Guide: `/docs/NETSUITE_INTEGRATION_FINAL.md`
- Snowflake Setup: `/snowflake-netsuite-setup.sql`

---

**Maintained By**: DentalERP Team
**Last Updated**: November 12, 2025
