# NetSuite Data Import - Quick Start Guide

## Overview

This guide shows you how to import the NetSuite financial data backup into the DentalERP system.

**Data Source**: `backup/report_250_transactiondetail.csv` (686 transactions, Nov 2025)

---

## Quick Commands

### 1. Import CSV to Bronze Layer
```bash
cd /opt/dental-erp/mcp-server
python scripts/seed-netsuite-from-csv.py
```

**Expected Output:**
```
✅ Inserted 686 transactions to Bronze layer
✅ Balance Check: $0.00 (debits = credits)
✅ Date Range: 2025-11-01 to 2025-11-30
✅ 52 unique vendors/customers tracked
```

### 2. Transform to Silver & Gold
```bash
cd /opt/dental-erp/dbt/dentalerp
dbt run --select stg_netsuite_transactions+
```

### 3. Verify Data
```bash
# Test Snowflake connection
cd /opt/dental-erp
./scripts/test-snowflake.sh

# Test analytics API
curl -H "Authorization: Bearer $MCP_API_KEY" \
     -H "X-Tenant-ID: silvercreek" \
     https://mcp.agentprovision.com/api/v1/analytics/financial/summary
```

---

## What Gets Imported

### Transaction Types (686 total)
- **Bills** (450): Vendor invoices for expenses
- **Bill Payments** (180): Payments to vendors
- **Invoices** (30): Customer invoices
- **Customer Payments** (26): Payments from customers

### Account Categories
- **Operating Expenses**: Labs, Facility, Marketing, Operating, Payroll
- **Current Liabilities**: Accounts Payable, Ramp AP cards
- **Revenue**: Production Income, Collections

### Entities Tracked
- **52 unique vendors/customers**
- Examples: 321 Crown Dental Laboratory, Glidewell Laboratories, Method Pro Inc

---

## Data Structure

### CSV Format
```
Type, Date, Document Number, Name, Memo, Account, Clr, Split, Qty, Amount
```

### Bronze Layer Table
```sql
bronze.netsuite_transactions
  ├─ transaction_type (Bill, Payment, Invoice)
  ├─ transaction_date (2025-11-01 to 2025-11-30)
  ├─ entity_name (Vendor/Customer)
  ├─ account_category (Operating Expenses, Revenue, etc.)
  ├─ debit_amount, credit_amount
  └─ raw_data (full CSV row as JSON)
```

---

## Verification Checklist

After running the import, verify:

- [ ] **Transaction Count**: 686 transactions imported
- [ ] **Balance Check**: Total debits = Total credits ($0.00 difference)
- [ ] **Date Range**: All dates between 2025-11-01 and 2025-11-30
- [ ] **Entity Count**: 52 unique vendors/customers
- [ ] **Categories**: All accounts mapped to valid categories
- [ ] **No Errors**: Import script completed without errors

---

## Troubleshooting

### Issue: "CSV file not found"
```bash
# Verify file exists
ls -l /Users/nomade/Documents/GitHub/dentalERP/backup/report_250_transactiondetail.csv

# Update path in script if needed
# Edit: mcp-server/scripts/seed-netsuite-from-csv.py
# Line: self.csv_path = Path("YOUR_PATH_HERE")
```

### Issue: "Balance check failed (debits != credits)"
```bash
# This indicates a parsing error in debit/credit logic
# Check logs for specific transaction that failed
# Review: mcp-server/scripts/seed-netsuite-from-csv.py
# Function: determine_debit_credit()
```

### Issue: "Snowflake connection failed"
```bash
# Verify Snowflake credentials
env | grep SNOWFLAKE

# Test connection
cd /opt/dental-erp
./scripts/test-snowflake.sh
```

---

## Advanced Usage

### Import Specific Date Range
Edit `seed-netsuite-from-csv.py`:
```python
# In read_csv_transactions() method
if transaction_date < "2025-11-01" or transaction_date > "2025-11-30":
    continue  # Skip transactions outside range
```

### Filter by Transaction Type
Edit `seed-netsuite-from-csv.py`:
```python
# In read_csv_transactions() method
if transaction_type not in ["Bill", "Bill Payment"]:
    continue  # Only import bills and payments
```

### Custom Account Mapping
Edit `seed-netsuite-from-csv.py`:
```python
# Update account_category_map dictionary
self.account_category_map = {
    "Labs Expenses": "Operating Expenses",
    "Your Custom Category": "Your Custom Mapping",
    ...
}
```

---

## Data Flow

```
1. CSV Backup (686 lines)
   ↓
2. seed-netsuite-from-csv.py
   ├─ Parse CSV
   ├─ Extract account hierarchy
   ├─ Calculate debits/credits
   ├─ Validate balance
   └─ Insert to Snowflake
   ↓
3. Bronze Layer (bronze.netsuite_transactions)
   ↓
4. dbt Transformations
   ├─ Silver: Clean & standardize
   └─ Gold: Aggregate metrics
   ↓
5. MCP Analytics API
   ↓
6. Frontend Dashboard
```

---

## Related Documentation

- **Full Data Structure Guide**: `/docs/NETSUITE_DATA_STRUCTURE.md`
- **Changes Summary**: `/docs/SEED_DATA_CHANGES_SUMMARY.md`
- **NetSuite Integration**: `/docs/NETSUITE_INTEGRATION_FINAL.md`
- **Main Codebase Guide**: `/CLAUDE.md`

---

## Support

Questions? Issues?
1. Check `/docs/NETSUITE_DATA_STRUCTURE.md` for detailed explanations
2. Review logs in MCP server for error details
3. Verify CSV format matches expected structure
4. Test Snowflake connection with `./scripts/test-snowflake.sh`

---

**Last Updated**: November 12, 2025
**Maintained By**: DentalERP Team
