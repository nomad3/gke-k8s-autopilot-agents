-- ============================================================================
-- Fast CSV Load to Snowflake using COPY INTO
-- Run this in Snowflake UI or via snowsql CLI
-- ============================================================================

USE DATABASE DENTAL_ERP_DW;
USE WAREHOUSE COMPUTE_WH;
USE SCHEMA BRONZE;

-- ============================================================================
-- STEP 1: Create file format for the CSV files
-- ============================================================================

CREATE OR REPLACE FILE FORMAT csv_transaction_format
  TYPE = 'CSV'
  FIELD_DELIMITER = ','
  SKIP_HEADER = 6  -- Skip the header metadata rows
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  TRIM_SPACE = TRUE
  ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
  EMPTY_FIELD_AS_NULL = TRUE
  NULL_IF = ('', 'NULL');

-- ============================================================================
-- STEP 2: Create temporary staging table to load raw CSV
-- ============================================================================

CREATE OR REPLACE TEMPORARY TABLE temp_csv_transactions (
  Type STRING,
  Date STRING,
  Document_Number STRING,
  Name STRING,
  Memo STRING,
  Account STRING,
  Clr STRING,
  Split STRING,
  Qty STRING,
  Amount STRING
);

-- ============================================================================
-- STEP 3: Upload files from GCP VM
-- Run these commands on the GCP VM terminal:
-- ============================================================================

/*
# On GCP VM, connect to Snowflake and upload files:
snowsql -a HKTPGHW-ES87244 -u NOMADSIMON -d DENTAL_ERP_DW -s BRONZE -w COMPUTE_WH

-- Then in snowsql:
PUT file:///opt/dental-erp/backup/TransactionDetail_eastlake_mapped.csv @~/staged;
PUT file:///opt/dental-erp/backup/TransactionDetail_torrey_pines_mapped.csv @~/staged;
PUT file:///opt/dental-erp/backup/TransactionDetail_ads_mapped.csv @~/staged;
*/

-- ============================================================================
-- STEP 4: Load into temporary table from staged files
-- ============================================================================

COPY INTO temp_csv_transactions
FROM @~/staged
FILE_FORMAT = csv_transaction_format
PATTERN = '.*TransactionDetail.*mapped.csv.gz'
ON_ERROR = 'CONTINUE';

-- Check how many loaded
SELECT COUNT(*) FROM temp_csv_transactions;
-- Expected: 37,759

-- ============================================================================
-- STEP 5: Transform and insert into Bronze layer
-- ============================================================================

-- Eastlake transactions
INSERT INTO bronze.netsuite_journal_entries
  (id, sync_id, tenant_id, raw_data, last_modified_date, extracted_at, is_deleted)
SELECT
  'eastlake_' || Document_Number || '_' || ROW_NUMBER() OVER (ORDER BY Date) as id,
  'csv_load_20251113' as sync_id,
  'eastlake' as tenant_id,
  OBJECT_CONSTRUCT(
    'Type', Type,
    'Date', Date,
    'Document_Number', Document_Number,
    'Name', Name,
    'Memo', Memo,
    'Account', Account,
    'Clr', Clr,
    'Split', Split,
    'Qty', Qty,
    'Amount', Amount
  ) as raw_data,
  CURRENT_TIMESTAMP() as last_modified_date,
  CURRENT_TIMESTAMP() as extracted_at,
  FALSE as is_deleted
FROM temp_csv_transactions
WHERE Account LIKE '%Eastlake%'
   OR Account LIKE '%SCDP Eastlake%';

-- Torrey Pines transactions
INSERT INTO bronze.netsuite_journal_entries
  (id, sync_id, tenant_id, raw_data, last_modified_date, extracted_at, is_deleted)
SELECT
  'torrey_pines_' || Document_Number || '_' || ROW_NUMBER() OVER (ORDER BY Date) as id,
  'csv_load_20251113' as sync_id,
  'torrey_pines' as tenant_id,
  OBJECT_CONSTRUCT(
    'Type', Type,
    'Date', Date,
    'Document_Number', Document_Number,
    'Name', Name,
    'Memo', Memo,
    'Account', Account,
    'Clr', Clr,
    'Split', Split,
    'Qty', Qty,
    'Amount', Amount
  ) as raw_data,
  CURRENT_TIMESTAMP() as last_modified_date,
  CURRENT_TIMESTAMP() as extracted_at,
  FALSE as is_deleted
FROM temp_csv_transactions
WHERE (Account LIKE '%Torrey%' OR Account LIKE '%Torrey Pines%')
  AND Account NOT LIKE '%Eastlake%';

-- ADS transactions
INSERT INTO bronze.netsuite_journal_entries
  (id, sync_id, tenant_id, raw_data, last_modified_date, extracted_at, is_deleted)
SELECT
  'ads_' || Document_Number || '_' || ROW_NUMBER() OVER (ORDER BY Date) as id,
  'csv_load_20251113' as sync_id,
  'ads' as tenant_id,
  OBJECT_CONSTRUCT(
    'Type', Type,
    'Date', Date,
    'Document_Number', Document_Number,
    'Name', Name,
    'Memo', Memo,
    'Account', Account,
    'Clr', Clr,
    'Split', Split,
    'Qty', Qty,
    'Amount', Amount
  ) as raw_data,
  CURRENT_TIMESTAMP() as last_modified_date,
  CURRENT_TIMESTAMP() as extracted_at,
  FALSE as is_deleted
FROM temp_csv_transactions
WHERE (Account LIKE '%San Marcos%' OR Account LIKE '%ADS%' OR Account LIKE '%Mission Hills%')
  AND Account NOT LIKE '%Eastlake%'
  AND Account NOT LIKE '%Torrey%';

-- ============================================================================
-- STEP 6: Verify data loaded
-- ============================================================================

SELECT
  tenant_id,
  COUNT(*) as transaction_count
FROM bronze.netsuite_journal_entries
WHERE sync_id = 'csv_load_20251113'
GROUP BY tenant_id
ORDER BY tenant_id;

-- Check total
SELECT COUNT(*) as total FROM bronze.netsuite_journal_entries;

-- ============================================================================
-- STEP 7: Refresh dynamic tables (if needed)
-- ============================================================================

-- Silver tables will auto-refresh within 10 minutes
-- Gold tables will auto-refresh within 30 minutes
-- To force immediate refresh:

ALTER DYNAMIC TABLE silver.fact_journal_entries REFRESH;
ALTER DYNAMIC TABLE gold.daily_financial_summary REFRESH;

SELECT * FROM gold.daily_financial_summary LIMIT 10;

-- ============================================================================
-- Complete! Dashboard will now show all transaction data
-- ============================================================================
