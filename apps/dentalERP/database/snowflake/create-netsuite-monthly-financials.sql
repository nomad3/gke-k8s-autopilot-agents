-- Create monthly financial aggregations from NetSuite transaction data

USE DATABASE DENTAL_ERP_DW;
USE SCHEMA BRONZE_GOLD;
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE DYNAMIC TABLE bronze_gold.netsuite_monthly_financials
TARGET_LAG = '1 hour'
WAREHOUSE = COMPUTE_WH
AS
SELECT
    nt.practice_id,
    DATE_TRUNC('MONTH', TO_DATE(nt.DATE)) AS report_month,
    'silvercreek' AS tenant_id,

    -- Revenue (negative amounts in NetSuite = credits = revenue)
    -- Parse AMOUNT: remove $, commas, handle parentheses as negatives
    SUM(CASE
        WHEN TRY_CAST(
            REPLACE(REPLACE(REPLACE(REPLACE(nt.AMOUNT, '$', ''), ',', ''), '(', '-'), ')', '')
            AS DECIMAL(18,2)) < 0
        THEN ABS(TRY_CAST(
            REPLACE(REPLACE(REPLACE(REPLACE(nt.AMOUNT, '$', ''), ',', ''), '(', '-'), ')', '')
            AS DECIMAL(18,2)))
        ELSE 0
    END) AS monthly_revenue,

    -- Expenses (positive amounts = debits = expenses)
    SUM(CASE
        WHEN TRY_CAST(
            REPLACE(REPLACE(REPLACE(REPLACE(nt.AMOUNT, '$', ''), ',', ''), '(', '-'), ')', '')
            AS DECIMAL(18,2)) > 0
        THEN TRY_CAST(
            REPLACE(REPLACE(REPLACE(REPLACE(nt.AMOUNT, '$', ''), ',', ''), '(', '-'), ')', '')
            AS DECIMAL(18,2))
        ELSE 0
    END) AS monthly_expenses,

    -- Net Income (revenue - expenses)
    SUM(CASE
        WHEN TRY_CAST(
            REPLACE(REPLACE(REPLACE(REPLACE(nt.AMOUNT, '$', ''), ',', ''), '(', '-'), ')', '')
            AS DECIMAL(18,2)) < 0
        THEN ABS(TRY_CAST(
            REPLACE(REPLACE(REPLACE(REPLACE(nt.AMOUNT, '$', ''), ',', ''), '(', '-'), ')', '')
            AS DECIMAL(18,2)))
        ELSE 0
    END) - SUM(CASE
        WHEN TRY_CAST(
            REPLACE(REPLACE(REPLACE(REPLACE(nt.AMOUNT, '$', ''), ',', ''), '(', '-'), ')', '')
            AS DECIMAL(18,2)) > 0
        THEN TRY_CAST(
            REPLACE(REPLACE(REPLACE(REPLACE(nt.AMOUNT, '$', ''), ',', ''), '(', '-'), ')', '')
            AS DECIMAL(18,2))
        ELSE 0
    END) AS monthly_net_income,

    -- Profit margin %
    CASE
        WHEN SUM(CASE WHEN TRY_CAST(REPLACE(REPLACE(REPLACE(REPLACE(nt.AMOUNT, '$', ''), ',', ''), '(', '-'), ')', '') AS DECIMAL(18,2)) < 0
            THEN ABS(TRY_CAST(REPLACE(REPLACE(REPLACE(REPLACE(nt.AMOUNT, '$', ''), ',', ''), '(', '-'), ')', '') AS DECIMAL(18,2))) ELSE 0 END) > 0
        THEN (
            (SUM(CASE WHEN TRY_CAST(REPLACE(REPLACE(REPLACE(REPLACE(nt.AMOUNT, '$', ''), ',', ''), '(', '-'), ')', '') AS DECIMAL(18,2)) < 0
                THEN ABS(TRY_CAST(REPLACE(REPLACE(REPLACE(REPLACE(nt.AMOUNT, '$', ''), ',', ''), '(', '-'), ')', '') AS DECIMAL(18,2))) ELSE 0 END) -
             SUM(CASE WHEN TRY_CAST(REPLACE(REPLACE(REPLACE(REPLACE(nt.AMOUNT, '$', ''), ',', ''), '(', '-'), ')', '') AS DECIMAL(18,2)) > 0
                THEN TRY_CAST(REPLACE(REPLACE(REPLACE(REPLACE(nt.AMOUNT, '$', ''), ',', ''), '(', '-'), ')', '') AS DECIMAL(18,2)) ELSE 0 END)) /
            SUM(CASE WHEN TRY_CAST(REPLACE(REPLACE(REPLACE(REPLACE(nt.AMOUNT, '$', ''), ',', ''), '(', '-'), ')', '') AS DECIMAL(18,2)) < 0
                THEN ABS(TRY_CAST(REPLACE(REPLACE(REPLACE(REPLACE(nt.AMOUNT, '$', ''), ',', ''), '(', '-'), ')', '') AS DECIMAL(18,2))) ELSE 0 END) * 100
        )
        ELSE 0
    END AS profit_margin_pct,

    -- Transaction count for reference
    COUNT(*) AS transaction_count,

    CURRENT_TIMESTAMP() AS calculated_at

FROM bronze.netsuite_transactions_with_practice nt
WHERE nt.practice_id IS NOT NULL
  AND nt.DATE IS NOT NULL
  AND nt.DATE != 'Date'  -- Skip header
  AND TRY_CAST(nt.DATE AS DATE) IS NOT NULL
GROUP BY nt.practice_id, DATE_TRUNC('MONTH', TO_DATE(nt.DATE)), tenant_id;

COMMENT ON DYNAMIC TABLE bronze_gold.netsuite_monthly_financials IS
'Monthly financial metrics from NetSuite aggregated by practice';

SELECT 'NetSuite monthly financials dynamic table created' AS status;
