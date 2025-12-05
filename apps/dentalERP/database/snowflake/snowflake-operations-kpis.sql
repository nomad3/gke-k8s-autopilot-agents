-- ============================================================================
-- Snowflake Operations KPI Tables - Monthly Practice Operations Tracking
-- Replaces manual Excel Operations Report with automated tracking
-- ============================================================================
-- Pattern: Bronze (raw) → Silver Dynamic Table → Gold Dynamic Table
-- Auto-refresh: Dynamic tables update automatically when source data changes
-- ============================================================================

USE DATABASE DENTAL_ERP_DW;
USE WAREHOUSE COMPUTE_WH;
USE ROLE ACCOUNTADMIN;

-- ============================================================================
-- BRONZE LAYER: Raw Operations Metrics from Excel Upload
-- ============================================================================

USE SCHEMA BRONZE;

CREATE TABLE IF NOT EXISTS bronze.operations_metrics_raw (
    id VARCHAR(255) PRIMARY KEY,
    practice_code VARCHAR(50) NOT NULL,
    practice_name VARCHAR(100),
    report_month DATE NOT NULL,
    tenant_id VARCHAR(50) NOT NULL DEFAULT 'silvercreek',

    -- Raw metric values stored as JSON (VARIANT column)
    raw_data VARIANT NOT NULL,

    -- Metadata
    source_file VARCHAR(200),
    uploaded_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
    loaded_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),

    CONSTRAINT unique_practice_month UNIQUE (practice_code, report_month, tenant_id)
) CLUSTER BY (practice_code, report_month)
COMMENT = 'Bronze layer - Raw operations metrics from Excel monthly reports';

SELECT 'Bronze table created: bronze.operations_metrics_raw' AS status;

-- ============================================================================
-- SILVER LAYER: Cleaned Operations Metrics (DYNAMIC TABLE)
-- Auto-refreshes when Bronze layer changes
-- ============================================================================

USE SCHEMA BRONZE_SILVER;

CREATE OR REPLACE DYNAMIC TABLE bronze_silver.stg_operations_metrics
TARGET_LAG = '1 hour'
WAREHOUSE = COMPUTE_WH
AS
SELECT
    practice_code,
    practice_name,
    report_month,
    tenant_id,

    -- Production & Collections (extract from VARIANT)
    raw_data:total_production::DECIMAL(18,2) AS total_production,
    raw_data:gross_production_doctor::DECIMAL(18,2) AS gross_production_doctor,
    raw_data:gross_production_specialty::DECIMAL(18,2) AS gross_production_specialty,
    raw_data:gross_production_hygiene::DECIMAL(18,2) AS gross_production_hygiene,
    raw_data:net_production::DECIMAL(18,2) AS net_production,
    raw_data:collections::DECIMAL(18,2) AS collections,
    raw_data:adjustments::DECIMAL(18,2) AS adjustments,

    -- Patient Visits
    raw_data:visits_doctor_1::INT AS visits_doctor_1,
    raw_data:visits_doctor_2::INT AS visits_doctor_2,
    raw_data:visits_doctor_total::INT AS visits_doctor_total,
    raw_data:visits_specialist::INT AS visits_specialist,
    raw_data:visits_hygiene::INT AS visits_hygiene,
    raw_data:visits_total::INT AS visits_total,

    -- Case Acceptance (Doctor #1)
    raw_data:doc1_treatment_presented::DECIMAL(18,2) AS doc1_treatment_presented,
    raw_data:doc1_treatment_accepted::DECIMAL(18,2) AS doc1_treatment_accepted,

    -- Case Acceptance (Doctor #2)
    raw_data:doc2_treatment_presented::DECIMAL(18,2) AS doc2_treatment_presented,
    raw_data:doc2_treatment_accepted::DECIMAL(18,2) AS doc2_treatment_accepted,

    -- New Patients
    raw_data:new_patients_total::INT AS new_patients_total,
    raw_data:new_patients_reappt_rate::DECIMAL(5,2) AS new_patients_reappt_rate,

    -- Hygiene Efficiency
    raw_data:hygiene_capacity_slots::INT AS hygiene_capacity_slots,
    raw_data:hygiene_net_production::DECIMAL(18,2) AS hygiene_net_production,
    raw_data:hygiene_compensation::DECIMAL(18,2) AS hygiene_compensation,
    raw_data:hygiene_reappt_rate::DECIMAL(5,2) AS hygiene_reappt_rate,

    -- Provider Production (Individual)
    raw_data:doctor_1_production::DECIMAL(18,2) AS doctor_1_production,
    raw_data:doctor_2_production::DECIMAL(18,2) AS doctor_2_production,
    raw_data:specialist_production::DECIMAL(18,2) AS specialist_production,

    -- Metadata
    uploaded_at,
    CURRENT_TIMESTAMP() AS transformed_at

FROM bronze.operations_metrics_raw
WHERE raw_data IS NOT NULL;

COMMENT ON DYNAMIC TABLE bronze_silver.stg_operations_metrics IS 'Silver layer - Cleaned operations metrics with typed columns, auto-refreshes from Bronze';

SELECT 'Silver dynamic table created: bronze_silver.stg_operations_metrics' AS status;

-- ============================================================================
-- GOLD LAYER: Operations KPIs with Calculations (DYNAMIC TABLE)
-- Auto-refreshes when Silver layer changes
-- Includes LTM (Last Twelve Months) rolling calculations
-- ============================================================================

USE SCHEMA BRONZE_GOLD;

CREATE OR REPLACE DYNAMIC TABLE bronze_gold.operations_kpis_monthly
TARGET_LAG = '1 hour'
WAREHOUSE = COMPUTE_WH
AS
WITH current_month AS (
    SELECT * FROM bronze_silver.stg_operations_metrics
),

ltm_aggregates AS (
    -- Last Twelve Months rolling calculations using window functions
    SELECT
        practice_code,
        report_month,
        SUM(total_production) OVER (
            PARTITION BY practice_code
            ORDER BY report_month
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) AS ltm_production,
        SUM(collections) OVER (
            PARTITION BY practice_code
            ORDER BY report_month
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) AS ltm_collections,
        SUM(visits_total) OVER (
            PARTITION BY practice_code
            ORDER BY report_month
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) AS ltm_visits,
        SUM(new_patients_total) OVER (
            PARTITION BY practice_code
            ORDER BY report_month
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ) AS ltm_new_patients
    FROM current_month
)

SELECT
    cm.practice_code AS practice_location,  -- Alias for compatibility with existing API
    cm.practice_name,
    cm.report_month,
    cm.tenant_id,

    -- Production & Collections
    cm.total_production,
    cm.gross_production_doctor,
    cm.gross_production_specialty,
    cm.gross_production_hygiene,
    cm.net_production,
    cm.collections,
    cm.adjustments,

    -- Calculated: Collection Rate %
    CASE
        WHEN cm.net_production > 0
        THEN (cm.collections / cm.net_production * 100)
        ELSE 0
    END AS collection_rate_pct,

    -- Calculated: Adjustment Rate %
    CASE
        WHEN cm.total_production > 0
        THEN (cm.adjustments / cm.total_production * 100)
        ELSE 0
    END AS adjustment_rate_pct,

    -- Patient Visits
    cm.visits_doctor_1,
    cm.visits_doctor_2,
    cm.visits_doctor_total,
    cm.visits_specialist,
    cm.visits_hygiene,
    cm.visits_total,

    -- Production Per Visit (CALCULATED)
    CASE
        WHEN cm.visits_doctor_1 > 0
        THEN (cm.doctor_1_production / cm.visits_doctor_1)
        ELSE 0
    END AS ppv_doctor_1,

    CASE
        WHEN cm.visits_doctor_2 > 0
        THEN (cm.doctor_2_production / cm.visits_doctor_2)
        ELSE 0
    END AS ppv_doctor_2,

    CASE
        WHEN cm.visits_doctor_total > 0
        THEN (cm.gross_production_doctor / cm.visits_doctor_total)
        ELSE 0
    END AS ppv_doctor_avg,

    CASE
        WHEN cm.visits_specialist > 0
        THEN (cm.specialist_production / cm.visits_specialist)
        ELSE 0
    END AS ppv_specialist,

    CASE
        WHEN cm.visits_hygiene > 0
        THEN (cm.hygiene_net_production / cm.visits_hygiene)
        ELSE 0
    END AS ppv_hygiene,

    CASE
        WHEN cm.visits_total > 0
        THEN (cm.total_production / cm.visits_total)
        ELSE 0
    END AS ppv_overall,

    -- Case Acceptance - Doctor #1 (CALCULATED)
    cm.doc1_treatment_presented,
    cm.doc1_treatment_accepted,
    CASE
        WHEN cm.doc1_treatment_presented > 0
        THEN (cm.doc1_treatment_accepted / cm.doc1_treatment_presented * 100)
        ELSE 0
    END AS doc1_acceptance_rate_pct,

    -- Case Acceptance - Doctor #2 (CALCULATED)
    cm.doc2_treatment_presented,
    cm.doc2_treatment_accepted,
    CASE
        WHEN cm.doc2_treatment_presented > 0
        THEN (cm.doc2_treatment_accepted / cm.doc2_treatment_presented * 100)
        ELSE 0
    END AS doc2_acceptance_rate_pct,

    -- Combined Case Acceptance Rate
    CASE
        WHEN (cm.doc1_treatment_presented + cm.doc2_treatment_presented) > 0
        THEN ((cm.doc1_treatment_accepted + cm.doc2_treatment_accepted) /
              (cm.doc1_treatment_presented + cm.doc2_treatment_presented) * 100)
        ELSE 0
    END AS case_acceptance_rate_pct,

    -- New Patients
    cm.new_patients_total,
    cm.new_patients_reappt_rate,

    -- Hygiene Efficiency (CALCULATED)
    cm.hygiene_capacity_slots,
    cm.hygiene_reappt_rate,
    CASE
        WHEN cm.hygiene_capacity_slots > 0
        THEN (cm.visits_hygiene / cm.hygiene_capacity_slots * 100)
        ELSE 0
    END AS hygiene_capacity_utilization_pct,

    cm.hygiene_net_production,
    cm.hygiene_compensation,
    CASE
        WHEN cm.hygiene_compensation > 0
        THEN (cm.hygiene_net_production / cm.hygiene_compensation)
        ELSE 0
    END AS hygiene_productivity_ratio,

    -- Provider Production (Individual)
    cm.doctor_1_production,
    cm.doctor_2_production,
    cm.specialist_production,

    -- Last Twelve Months (LTM) Rollups
    ltm.ltm_production,
    ltm.ltm_collections,
    ltm.ltm_visits,
    ltm.ltm_new_patients,

    -- Metadata
    'excel_upload' AS extraction_method,
    1.0 AS data_quality_score,  -- Excel data = perfect quality
    cm.uploaded_at,
    CURRENT_TIMESTAMP() AS calculated_at

FROM current_month cm
LEFT JOIN ltm_aggregates ltm
    ON cm.practice_code = ltm.practice_code
    AND cm.report_month = ltm.report_month;

COMMENT ON DYNAMIC TABLE bronze_gold.operations_kpis_monthly IS 'Gold layer - Monthly operations KPIs with LTM rollups and calculated metrics, auto-refreshes from Silver';

SELECT 'Gold dynamic table created: bronze_gold.operations_kpis_monthly' AS status;

-- ============================================================================
-- Indexes for Query Performance
-- ============================================================================

-- Note: Snowflake dynamic tables automatically maintain clustering
-- But we can add search optimization if needed for large datasets

-- ALTER DYNAMIC TABLE bronze_gold.operations_kpis_monthly
-- ADD SEARCH OPTIMIZATION ON EQUALITY(practice_location, tenant_id);

SELECT 'Operations KPI tables setup complete!' AS status;
SELECT 'Next steps: Upload Excel data to bronze.operations_metrics_raw' AS status;
SELECT 'Dynamic tables will auto-refresh within 1 hour' AS status;

-- ============================================================================
-- Sample Query to Test (after data loaded)
-- ============================================================================

/*
-- Test query after loading data:
SELECT
    practice_location,
    report_month,
    total_production,
    collection_rate_pct,
    ppv_overall,
    case_acceptance_rate_pct,
    hygiene_productivity_ratio,
    ltm_production
FROM bronze_gold.operations_kpis_monthly
WHERE tenant_id = 'silvercreek'
ORDER BY report_month DESC, practice_location
LIMIT 20;
*/
