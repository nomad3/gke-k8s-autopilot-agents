# Demo Setup Guide

## Overview

This guide will help you deploy the DentalERP demo with **37,759 real NetSuite transactions** from 3 practices.

## Data Ready

- **Eastlake**: 37,174 transactions
- **Torrey Pines**: 226 transactions
- **ADS**: 359 transactions
- **Total**: 37,759 transactions

All data is in `/backup` directory, already mapped to practice subsidiaries.

## Quick Start (GCP VM)

### 1. SSH into GCP VM

```bash
gcloud compute ssh dental-erp-vm --zone=us-central1-a
```

### 2. Navigate to Project

```bash
cd /opt/dental-erp
```

### 3. Pull Latest Code

```bash
sudo git pull origin main
```

### 4. Run Demo Deployment Script

```bash
sudo ./scripts/deploy-demo.sh
```

This script will:
1. ✓ Pull latest code
2. ✓ Check Docker containers
3. ✓ Fix frontend if needed (502 Bad Gateway)
4. ✓ Verify MCP Server health
5. ✓ Load 37,759 transactions to Snowflake Bronze
6. ✓ Verify dynamic tables transform to Silver & Gold
7. ✓ Test frontend accessibility

## Manual Steps (if needed)

### Load Data Only

```bash
cd /opt/dental-erp
source .env
sudo -E python3 scripts/ingest-netsuite-multi-practice.py
```

### Fix Frontend 502 Error

```bash
# Check logs
sudo docker logs --tail 100 dentalerp-frontend-prod-1

# Restart frontend
sudo docker restart dentalerp-frontend-prod-1

# Wait 10 seconds, then test
curl https://dentalerp.agentprovision.com
```

### Verify Snowflake Data

```sql
-- Check Bronze layer
SELECT COUNT(*) FROM bronze.netsuite_journal_entries;
-- Expected: 37,759 rows

-- Check Silver dynamic tables
SHOW DYNAMIC TABLES IN SCHEMA silver;
SELECT COUNT(*) FROM silver.fact_journal_entries;

-- Check Gold aggregations
SELECT * FROM gold.daily_financial_summary
WHERE transaction_date >= '2025-01-01'
ORDER BY transaction_date DESC
LIMIT 10;

-- By practice
SELECT
    subsidiary_name,
    COUNT(*) as transaction_count,
    SUM(total_revenue) as total_revenue,
    SUM(total_expenses) as total_expenses,
    SUM(net_income) as net_income
FROM gold.daily_financial_summary
GROUP BY subsidiary_name
ORDER BY total_revenue DESC;
```

## Architecture

### Data Flow

```
CSV Backups (37,759 rows)
    ↓
Bronze Layer (raw JSON in VARIANT columns)
    ↓ [Dynamic Tables - TARGET_LAG = 10 min]
Silver Layer (cleaned, typed, flattened)
    ↓ [Dynamic Tables - TARGET_LAG = 30 min]
Gold Layer (aggregated KPIs)
    ↓
Analytics Dashboard
```

### Dynamic Tables (No dbt needed!)

Snowflake dynamic tables **auto-refresh** when Bronze data changes:

- **Silver Layer**: Flattens JSON, types fields, joins dimensions
- **Gold Layer**: Aggregates daily/monthly KPIs, calculates metrics

**No manual dbt runs required** - data flows automatically!

## Frontend Access

- **URL**: https://dentalerp.agentprovision.com
- **Credentials**: admin@practice.com / Admin123!
- **Dashboard**: Navigate to Analytics → Financial Dashboard

## API Testing

### MCP Server Health

```bash
curl https://mcp.agentprovision.com/health
```

### Get Financial Summary

```bash
curl https://mcp.agentprovision.com/api/v1/analytics/financial/summary \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: eastlake"
```

## Troubleshooting

### Frontend returns 502 Bad Gateway

**Cause**: Frontend container not running or crashed
**Fix**: `sudo docker restart dentalerp-frontend-prod-1`

### No data in Silver/Gold tables

**Cause**: Dynamic tables not refreshed yet
**Check**: `SHOW DYNAMIC TABLES IN SCHEMA silver;`
**Fix**: Wait 10-30 minutes for TARGET_LAG, or manually refresh:

```sql
ALTER DYNAMIC TABLE silver.fact_journal_entries REFRESH;
ALTER DYNAMIC TABLE gold.daily_financial_summary REFRESH;
```

### Python script fails with Snowflake error

**Cause**: Missing environment variables
**Fix**: Check `.env` file has all SNOWFLAKE_* variables

```bash
cat .env | grep SNOWFLAKE
```

## Success Criteria

✓ Frontend loads at https://dentalerp.agentprovision.com
✓ Bronze has 37,759 journal entries
✓ Silver dynamic tables populated
✓ Gold shows daily_financial_summary with 3 subsidiaries
✓ Dashboard displays charts for Eastlake, Torrey Pines, ADS

## Support

- **Logs**: `sudo docker logs dentalerp-frontend-prod-1`
- **Containers**: `sudo docker ps`
- **Restart All**: `sudo ./deploy.sh`

---

**Last Updated**: November 13, 2025
**Data Source**: NetSuite CSV exports (Jan-Nov 2025)
