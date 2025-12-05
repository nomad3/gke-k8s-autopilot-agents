-- Extract practice identifiers from NetSuite transaction data
-- Practice names appear in ACCOUNT and SPLIT columns

USE DATABASE DENTAL_ERP_DW;
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE VIEW bronze.netsuite_transactions_with_practice AS
SELECT
    *,
    CASE
        -- Eastlake patterns
        WHEN ACCOUNT LIKE '%Eastlake%' OR SPLIT LIKE '%Eastlake%' OR MEMO LIKE '%EASTLAKE%' THEN 'sed'

        -- Laguna Hills patterns
        WHEN ACCOUNT LIKE '%Laguna Hills%' OR SPLIT LIKE '%Laguna Hills%' OR MEMO LIKE '%LAGUNA%' THEN 'lhd'

        -- Torrey Pines / Encinitas patterns
        WHEN ACCOUNT LIKE '%Torrey Pines%' OR SPLIT LIKE '%Torrey Pines%' OR ACCOUNT LIKE '%Encinitas%' OR SPLIT LIKE '%Encinitas%' THEN 'efd_i'

        -- San Marcos / ADS patterns
        WHEN ACCOUNT LIKE '%San Marcos%' OR SPLIT LIKE '%San Marcos%' OR ACCOUNT LIKE '%ADS%' OR NAME LIKE '%Advanced Dental%' THEN 'ads'

        -- Del Sur patterns
        WHEN ACCOUNT LIKE '%Del Sur%' OR SPLIT LIKE '%Del Sur%' THEN 'dsr'

        -- Rancho patterns
        WHEN ACCOUNT LIKE '%Rancho%' OR SPLIT LIKE '%Rancho%' THEN 'rd'

        -- La Senda patterns
        WHEN ACCOUNT LIKE '%La Senda%' OR SPLIT LIKE '%La Senda%' THEN 'lsd'

        -- La Costa patterns
        WHEN ACCOUNT LIKE '%La Costa%' OR SPLIT LIKE '%La Costa%' THEN 'lcd'

        -- University City patterns
        WHEN ACCOUNT LIKE '%University City%' OR SPLIT LIKE '%University City%' THEN 'ucfd'

        -- Imperial Point patterns
        WHEN ACCOUNT LIKE '%Imperial Point%' OR SPLIT LIKE '%Imperial Point%' THEN 'ipd'

        -- East Avenue patterns
        WHEN ACCOUNT LIKE '%East Avenue%' OR SPLIT LIKE '%East Avenue%' THEN 'eawd'

        -- Downtown patterns
        WHEN ACCOUNT LIKE '%Downtown%' OR SPLIT LIKE '%Downtown%' THEN 'dd'

        -- Carmel Valley patterns
        WHEN ACCOUNT LIKE '%Carmel Valley%' OR SPLIT LIKE '%Carmel Valley%' THEN 'cvfd'

        -- UTC patterns (additional UTC patterns beyond University City)
        WHEN ACCOUNT LIKE '%UTC%' OR SPLIT LIKE '%UTC%' OR ACCOUNT LIKE '% 0733%' THEN 'ucfd'

        -- Torrey Highlands patterns
        WHEN ACCOUNT LIKE '%Torrey Highlands%' OR SPLIT LIKE '%Torrey Highlands%' THEN 'th'

        -- Kearny Mesa patterns
        WHEN ACCOUNT LIKE '%Kearny Mesa%' OR SPLIT LIKE '%Kearny Mesa%' OR ACCOUNT LIKE '% 0527%' THEN 'km'

        -- Vista patterns
        WHEN ACCOUNT LIKE '%Vista%' OR SPLIT LIKE '%Vista%' THEN 'vista'

        -- Carlsbad patterns
        WHEN ACCOUNT LIKE '%Carlsbad%' OR SPLIT LIKE '%Carlsbad%' OR ACCOUNT LIKE '% 9529%' THEN 'carlsbad'

        -- Temecula patterns
        WHEN ACCOUNT LIKE '%Temecula%' OR SPLIT LIKE '%Temecula%' THEN 'temecula'

        -- Otay Lakes patterns
        WHEN ACCOUNT LIKE '%Otay Lakes%' OR SPLIT LIKE '%Otay Lakes%' OR ACCOUNT LIKE '% 1675%' THEN 'olk'

        -- Theodosis patterns
        WHEN ACCOUNT LIKE '%Theodosis%' OR SPLIT LIKE '%Theodosis%' OR NAME LIKE '%Theodosis%' THEN 'theodosis'

        -- If generic "SCDP" without specific location, try to infer from other fields
        WHEN ACCOUNT LIKE '%SCDP%' AND MEMO LIKE '%Eastlake%' THEN 'sed'

        ELSE NULL
    END AS practice_id
FROM bronze.netsuite_transaction_details
WHERE TYPE != 'Type';  -- Skip CSV header row

SELECT 'NetSuite practice identifier view created' AS status;
