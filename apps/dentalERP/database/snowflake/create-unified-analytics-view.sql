USE DATABASE DENTAL_ERP_DW;
USE SCHEMA GOLD;
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE DYNAMIC TABLE gold.practice_analytics_unified
TARGET_LAG = '1 hour'
WAREHOUSE = COMPUTE_WH
AS
SELECT
    pm.practice_id,
    pm.practice_display_name,
    COALESCE(ops.report_month, pms.month, fin.report_month) AS report_month,
    pm.tenant_id,

    -- Operations Metrics (ALL from Operations Report)
    ops.total_production,
    ops.gross_production_doctor,
    ops.gross_production_specialty,
    ops.gross_production_hygiene,
    ops.net_production,
    ops.collections,
    ops.collection_rate_pct,
    ops.adjustment_rate_pct,
    ops.visits_doctor_1,
    ops.visits_doctor_2,
    ops.visits_doctor_total,
    ops.visits_specialist,
    ops.visits_hygiene,
    ops.visits_total,
    ops.ppv_doctor_1,
    ops.ppv_doctor_2,
    ops.ppv_doctor_avg,
    ops.ppv_specialist,
    ops.ppv_hygiene,
    ops.ppv_overall,
    ops.doc1_treatment_presented,
    ops.doc1_treatment_accepted,
    ops.doc1_acceptance_rate_pct,
    ops.doc2_treatment_presented,
    ops.doc2_treatment_accepted,
    ops.doc2_acceptance_rate_pct,
    ops.case_acceptance_rate_pct,
    ops.new_patients_total,
    ops.new_patients_reappt_rate,
    ops.hygiene_capacity_slots,
    ops.hygiene_capacity_utilization_pct,
    ops.hygiene_net_production,
    ops.hygiene_compensation,
    ops.hygiene_productivity_ratio,
    ops.hygiene_reappt_rate,
    ops.doctor_1_production,
    ops.doctor_2_production,
    ops.specialist_production,
    ops.ltm_production,
    ops.ltm_collections,
    ops.ltm_visits,
    ops.ltm_new_patients,

    -- Financial Metrics (from NetSuite)
    fin.monthly_revenue AS netsuite_revenue,
    fin.monthly_expenses AS netsuite_expenses,
    fin.monthly_net_income AS netsuite_net_income,
    fin.profit_margin_pct AS netsuite_profit_margin,
    0 AS netsuite_revenue_growth,  -- Placeholder for growth calculation

    -- PMS Production (from day sheets, aggregated monthly)
    pms.total_production AS pms_production,
    pms.collections AS pms_collections,
    pms.patient_visits AS pms_visits,
    pms.production_per_visit AS pms_ppv,
    pms.data_quality_score AS pms_quality,

    -- Cross-System Validations
    ops.total_production - COALESCE(pms.total_production, 0) AS production_variance,
    ops.collections - COALESCE(pms.collections, 0) AS collections_variance,

    -- Metadata
    ops.extraction_method,
    ops.data_quality_score,
    CURRENT_TIMESTAMP() AS calculated_at

FROM gold.practice_master pm

LEFT JOIN bronze_gold.operations_kpis_monthly ops
    ON LOWER(REPLACE(pm.operations_code, ' ', '_')) = ops.practice_location
    AND pm.tenant_id = ops.tenant_id

LEFT JOIN bronze_gold.netsuite_monthly_financials fin
    ON pm.practice_id = fin.practice_id
    AND pm.tenant_id = fin.tenant_id

LEFT JOIN (
    SELECT
        practice_location,
        DATE_TRUNC('MONTH', report_date) AS month,
        SUM(total_production) AS total_production,
        SUM(collections) AS collections,
        SUM(patient_visits) AS patient_visits,
        AVG(production_per_visit) AS production_per_visit,
        AVG(data_quality_score) AS data_quality_score
    FROM bronze_gold.daily_production_metrics
    GROUP BY practice_location, DATE_TRUNC('MONTH', report_date)
) pms
    ON pm.pms_location_code = pms.practice_location
    AND DATE_TRUNC('MONTH', ops.report_month) = pms.month

WHERE pm.is_active = TRUE;

COMMENT ON DYNAMIC TABLE gold.practice_analytics_unified IS
'Unified practice analytics joining Operations Report + NetSuite + PMS + ADP (future)';

SELECT 'Unified analytics view created' AS status;
