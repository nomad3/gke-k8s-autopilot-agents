-- Create view that adds practice_id to netsuite_transaction_details
-- This view is used by netsuite_monthly_financials dynamic table

USE DATABASE DENTAL_ERP_DW;
USE SCHEMA BRONZE;
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE VIEW bronze.netsuite_transactions_with_practice AS
SELECT
    TYPE,
    DATE,
    DOCUMENT,
    NAME,
    MEMO,
    ACCOUNT,
    CLR,
    SPLIT,
    QTY,
    AMOUNT,
    -- Extract practice_id from ACCOUNT field based on subsidiary name
    CASE
        -- High-confidence mappings
        WHEN ACCOUNT LIKE '%San Marcos II%' THEN 'ads'
        WHEN ACCOUNT LIKE '%San Marcos%' THEN 'ads'
        WHEN ACCOUNT LIKE '%Del Sur Ranch%' THEN 'dsr'
        WHEN ACCOUNT LIKE '%Eastlake%' THEN 'sed'
        WHEN ACCOUNT LIKE '%UTC%' THEN 'ucfd'
        WHEN ACCOUNT LIKE '%Carlsbad%' THEN 'lcd'
        WHEN ACCOUNT LIKE '%Torrey Pines%' THEN 'efd_i'
        WHEN ACCOUNT LIKE '%Torrey Highlands%' THEN 'ipd'
        WHEN ACCOUNT LIKE '%Coronado%' THEN 'dd'
        WHEN ACCOUNT LIKE '%Vista%' THEN 'eawd'
        WHEN ACCOUNT LIKE '%Laguna Hills II%' THEN 'efd_ii'
        WHEN ACCOUNT LIKE '%Laguna Hills%' THEN 'efd_ii'
        WHEN ACCOUNT LIKE '%Otay Lakes%' THEN 'lsd'
        WHEN ACCOUNT LIKE '%Kearny Mesa%' THEN 'rd'
        -- Subsidiaries without Operations mapping
        WHEN ACCOUNT LIKE '%Temecula II%' THEN 'netsuite_temecula_ii'
        WHEN ACCOUNT LIKE '%Temecula%' THEN 'netsuite_temecula'
        WHEN ACCOUNT LIKE '%Theodosis%' THEN 'netsuite_theodosis'
        -- Default
        ELSE 'unknown'
    END AS practice_id,
    -- Extract subsidiary name from ACCOUNT for reference
    CASE
        WHEN ACCOUNT LIKE '%San Marcos II%' THEN 'SCDP San Marcos II, LLC'
        WHEN ACCOUNT LIKE '%San Marcos%' THEN 'SCDP San Marcos, LLC'
        WHEN ACCOUNT LIKE '%Del Sur Ranch%' THEN 'SCDP Del Sur Ranch, LLC'
        WHEN ACCOUNT LIKE '%Eastlake%' THEN 'SCDP Eastlake, LLC'
        WHEN ACCOUNT LIKE '%UTC%' THEN 'SCDP UTC, LLC'
        WHEN ACCOUNT LIKE '%Carlsbad%' THEN 'SCDP Carlsbad, LLC'
        WHEN ACCOUNT LIKE '%Torrey Pines%' THEN 'SCDP Torrey Pines, LLC'
        WHEN ACCOUNT LIKE '%Torrey Highlands%' THEN 'SCDP Torrey Highlands, LLC'
        WHEN ACCOUNT LIKE '%Coronado%' THEN 'SCDP Coronado, LLC'
        WHEN ACCOUNT LIKE '%Vista%' THEN 'SCDP Vista, LLC'
        WHEN ACCOUNT LIKE '%Laguna Hills II%' THEN 'SCDP Laguna Hills II, LLC'
        WHEN ACCOUNT LIKE '%Laguna Hills%' THEN 'SCDP Laguna Hills, LLC'
        WHEN ACCOUNT LIKE '%Otay Lakes%' THEN 'SCDP Otay Lakes, LLC'
        WHEN ACCOUNT LIKE '%Kearny Mesa%' THEN 'SCDP Kearny Mesa, LLC'
        WHEN ACCOUNT LIKE '%Temecula II%' THEN 'SCDP Temecula II, LLC'
        WHEN ACCOUNT LIKE '%Temecula%' THEN 'SCDP Temecula, LLC'
        WHEN ACCOUNT LIKE '%Theodosis%' THEN 'Steve P. Theodosis Dental Corporation, PC'
        ELSE 'Unknown'
    END AS subsidiary_name,
    'silvercreek' AS tenant_id
FROM bronze.netsuite_transaction_details
WHERE DATE IS NOT NULL
  AND DATE != 'Date';  -- Skip header rows

COMMENT ON VIEW bronze.netsuite_transactions_with_practice IS
'View that adds practice_id mapping to NetSuite transaction details based on subsidiary in ACCOUNT field';

SELECT 'View created: netsuite_transactions_with_practice' AS status;
