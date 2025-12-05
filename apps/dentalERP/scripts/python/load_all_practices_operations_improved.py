#!/usr/bin/env python3
"""
Load ALL 14 Practices from Operations Report - IMPROVED PARSER
Uses flexible label search instead of fixed row numbers
"""

import pandas as pd
import json
import os
from datetime import datetime
import snowflake.connector
from dotenv import load_dotenv

load_dotenv('mcp-server/.env')

# Practice code mapping
PRACTICE_MAPPING = {
    'LHD': 'Laguna Hills Dental',
    'EFD I': 'Encinitas Family Dental I',
    'CVFD': 'Carmel Valley Family Dental',
    'DSR': 'Del Sur Dental',
    'ADS': 'Advanced Dental Solutions',
    'IPD': 'Imperial Point Dental',
    'EFD II': 'Encinitas Family Dental II',
    'RD': 'Rancho Dental',
    'LSD': 'La Senda Dental',
    'UCFD': 'University City Family Dental',
    'LCD': 'La Costa Dental',
    'EAWD': 'East Avenue Dental',
    'SED': 'Scripps Eastlake Dental',
    'DD': 'Downtown Dental'
}


def find_metric_row(df, search_terms, start_row=0, end_row=120, column=1):
    """
    Find row containing metric label by searching for terms

    Args:
        df: DataFrame
        search_terms: List of terms that should ALL be present (case-insensitive)
        start_row: Start searching from this row
        end_row: Stop at this row
        column: Which column to search (default 1 for metric names)

    Returns:
        Row index or None
    """
    for idx in range(start_row, min(end_row, len(df))):
        cell_value = str(df.iloc[idx, column]).strip() if pd.notna(df.iloc[idx, column]) else ''

        # Check if all search terms are in the cell (case-insensitive)
        if cell_value and all(term.upper() in cell_value.upper() for term in search_terms):
            return idx

    return None


def extract_value_at_row(df, row_idx, col_idx):
    """Safely extract numeric value from cell"""
    if row_idx is None or row_idx >= len(df):
        return None

    value = df.iloc[row_idx, col_idx]
    if pd.notna(value) and value != '':
        try:
            if isinstance(value, (int, float)):
                return float(value)
            else:
                return float(str(value).replace(',', ''))
        except:
            return None
    return None


def extract_practice_data_improved(df, practice_code, practice_name):
    """
    Extract metrics using flexible label search instead of fixed rows
    """
    metrics_list = []

    # Find date columns (row 4)
    date_row = df.iloc[4]
    dates = []
    date_col_indices = []

    for col_idx, cell_value in enumerate(date_row):
        if pd.notna(cell_value):
            try:
                cell_date = pd.to_datetime(cell_value)
                dates.append(cell_date)
                date_col_indices.append(col_idx)
            except:
                pass

    print(f"   Found {len(dates)} months of data")

    # For each month, extract metrics
    for date, col_idx in zip(dates, date_col_indices):
        report_month = date.strftime('%Y-%m-01')
        metrics = {}

        # PRODUCTION & COLLECTIONS
        row = find_metric_row(df, ['Doctor'], start_row=5, end_row=15)
        val = extract_value_at_row(df, row, col_idx)
        if val: metrics['gross_production_doctor'] = val

        row = find_metric_row(df, ['Specialty'], start_row=5, end_row=15)
        val = extract_value_at_row(df, row, col_idx)
        if val: metrics['gross_production_specialty'] = val

        row = find_metric_row(df, ['Hygiene'], start_row=5, end_row=15)
        val = extract_value_at_row(df, row, col_idx)
        if val: metrics['gross_production_hygiene'] = val

        row = find_metric_row(df, ['Total'], start_row=5, end_row=15)
        val = extract_value_at_row(df, row, col_idx)
        if val: metrics['total_production'] = val

        row = find_metric_row(df, ['Net Production'])
        val = extract_value_at_row(df, row, col_idx)
        if val: metrics['net_production'] = val

        row = find_metric_row(df, ['Collections'], start_row=19, end_row=25)
        val = extract_value_at_row(df, row, col_idx)
        if val: metrics['collections'] = val

        # PATIENT VISITS
        # Find "PATIENT VISITS" section header first
        visits_section_start = find_metric_row(df, ['PATIENT VISITS'])
        if visits_section_start:
            # Doctor #1
            row = find_metric_row(df, ['Doctor #1'], start_row=visits_section_start, end_row=visits_section_start+15)
            val = extract_value_at_row(df, row, col_idx)
            if val: metrics['visits_doctor_1'] = int(val)

            # Doctor #2
            row = find_metric_row(df, ['Doctor #2'], start_row=visits_section_start, end_row=visits_section_start+15)
            val = extract_value_at_row(df, row, col_idx)
            if val: metrics['visits_doctor_2'] = int(val)

            # Specialists
            row = find_metric_row(df, ['Specialists'], start_row=visits_section_start, end_row=visits_section_start+15)
            val = extract_value_at_row(df, row, col_idx)
            if val: metrics['visits_specialist'] = int(val)

            # Hygienists
            row = find_metric_row(df, ['Hygienists'], start_row=visits_section_start, end_row=visits_section_start+15)
            val = extract_value_at_row(df, row, col_idx)
            if val: metrics['visits_hygiene'] = int(val)

            # Total Visits (look after hygienists)
            row = find_metric_row(df, ['Total'], start_row=visits_section_start+10, end_row=visits_section_start+20)
            val = extract_value_at_row(df, row, col_idx)
            if val: metrics['visits_total'] = int(val)

        # CASE ACCEPTANCE
        case_section_start = find_metric_row(df, ['CASE ACCEPTANCE'])
        if case_section_start:
            # Doctor #1 Treatment Presented
            row = find_metric_row(df, ['Treatment Presented'], start_row=case_section_start, end_row=case_section_start+10)
            val = extract_value_at_row(df, row, col_idx)
            if val: metrics['doc1_treatment_presented'] = val

            # Doctor #1 Treatment Accepted
            row = find_metric_row(df, ['Treatment Accepted'], start_row=case_section_start, end_row=case_section_start+15)
            val = extract_value_at_row(df, row, col_idx)
            if val: metrics['doc1_treatment_accepted'] = val

            # Doctor #2 Treatment Presented (search after first doctor section)
            row = find_metric_row(df, ['Treatment Presented'], start_row=case_section_start+10, end_row=case_section_start+25)
            val = extract_value_at_row(df, row, col_idx)
            if val: metrics['doc2_treatment_presented'] = val

            # Doctor #2 Treatment Accepted
            row = find_metric_row(df, ['Treatment Accepted'], start_row=case_section_start+15, end_row=case_section_start+30)
            val = extract_value_at_row(df, row, col_idx)
            if val: metrics['doc2_treatment_accepted'] = val

        # NEW PATIENTS
        new_patients_section = find_metric_row(df, ['NEW PATIENTS'])
        if new_patients_section:
            row = find_metric_row(df, ['Total'], start_row=new_patients_section, end_row=new_patients_section+5)
            val = extract_value_at_row(df, row, col_idx)
            if val: metrics['new_patients_total'] = int(val)

            row = find_metric_row(df, ['Reappointment Rate'], start_row=new_patients_section, end_row=new_patients_section+5)
            val = extract_value_at_row(df, row, col_idx)
            if val: metrics['new_patients_reappt_rate'] = val

        # RECARE / HYGIENE EFFICIENCY
        recare_section = find_metric_row(df, ['RECARE'])
        if recare_section:
            row = find_metric_row(df, ['Hygiene Capacity'], start_row=recare_section, end_row=recare_section+10)
            val = extract_value_at_row(df, row, col_idx)
            if val: metrics['hygiene_capacity_slots'] = int(val)

            row = find_metric_row(df, ['Reappointment Rate'], start_row=recare_section, end_row=recare_section+10)
            val = extract_value_at_row(df, row, col_idx)
            if val: metrics['hygiene_reappt_rate'] = val

        # LABOR EFFICIENCY
        labor_section = find_metric_row(df, ['Labor Efficiency'])
        if labor_section:
            row = find_metric_row(df, ['Hygiene Net Production'], start_row=labor_section, end_row=labor_section+5)
            val = extract_value_at_row(df, row, col_idx)
            if val: metrics['hygiene_net_production'] = val

            row = find_metric_row(df, ['Hygiene Compensation'], start_row=labor_section, end_row=labor_section+5)
            val = extract_value_at_row(df, row, col_idx)
            if val: metrics['hygiene_compensation'] = val

        # Only add record if we have meaningful data
        if metrics.get('total_production', 0) > 0 or metrics.get('visits_total', 0) > 0:
            metrics_list.append({
                'practice_code': practice_code.lower().replace(' ', '_'),
                'practice_name': practice_name,
                'report_month': report_month,
                'raw_data': metrics,
                'tenant_id': 'silvercreek'
            })

    return metrics_list


def load_all_practices():
    """Load all 14 practices with improved parser"""

    excel_file = 'examples/ingestion/Operations Report(28).xlsx'

    print("=" * 80)
    print("LOADING ALL 14 PRACTICES - IMPROVED PARSER")
    print("=" * 80)
    print()

    all_records = []

    for practice_code, practice_name in PRACTICE_MAPPING.items():
        print(f"📊 Parsing: {practice_name} ({practice_code})")

        try:
            df = pd.read_excel(excel_file, sheet_name=practice_code)
            records = extract_practice_data_improved(df, practice_code, practice_name)
            all_records.extend(records)
            print(f"   ✅ Extracted {len(records)} monthly records")

            # Show sample metrics for first record
            if records:
                sample = records[0]['raw_data']
                metric_count = len([k for k, v in sample.items() if v is not None and v != 0])
                print(f"   📊 Sample month has {metric_count} non-zero metrics")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        print()

    print(f"📦 Total records to upload: {len(all_records)}")

    # Show summary of what was extracted
    if all_records:
        sample = all_records[0]['raw_data']
        print(f"\n✅ Metrics extracted successfully:")
        for key in sorted(sample.keys()):
            print(f"   • {key}")
    print()

    # Upload to Snowflake
    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        role=os.getenv('SNOWFLAKE_ROLE'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE')
    )

    cursor = conn.cursor()

    print("=" * 80)
    print("UPLOADING TO SNOWFLAKE")
    print("=" * 80)
    print()

    success = 0
    errors = 0

    for i, record in enumerate(all_records, 1):
        record_id = f"{record['practice_code']}_{record['report_month']}"
        raw_data_json = json.dumps(record['raw_data'])

        query = f"""
            MERGE INTO bronze.operations_metrics_raw AS target
            USING (
                SELECT
                    '{record_id}' AS id,
                    '{record['practice_code']}' AS practice_code,
                    '{record['practice_name']}' AS practice_name,
                    '{record['report_month']}' AS report_month,
                    '{record['tenant_id']}' AS tenant_id,
                    PARSE_JSON('{raw_data_json}') AS raw_data,
                    'Operations Report(28).xlsx' AS source_file,
                    CURRENT_TIMESTAMP() AS uploaded_at,
                    CURRENT_TIMESTAMP() AS loaded_at
            ) AS source
            ON target.id = source.id
            WHEN MATCHED THEN
                UPDATE SET raw_data = source.raw_data, loaded_at = source.loaded_at
            WHEN NOT MATCHED THEN
                INSERT (id, practice_code, practice_name, report_month, tenant_id, raw_data, source_file, uploaded_at, loaded_at)
                VALUES (source.id, source.practice_code, source.practice_name, source.report_month,
                        source.tenant_id, source.raw_data, source.source_file, source.uploaded_at, source.loaded_at)
        """

        try:
            cursor.execute(query)
            conn.commit()
            success += 1
            if i % 50 == 0 or i == len(all_records):
                print(f"   [{i:3d}/{len(all_records)}] ✅ {success} successful, {errors} errors")
        except Exception as e:
            errors += 1
            print(f"   [{i:3d}/{len(all_records)}] ❌ {record_id}: {str(e)[:80]}")

    print()
    print(f"✅ Upload complete: {success} successful, {errors} errors")
    print()

    # Refresh dynamic tables
    print("🔄 Refreshing dynamic tables...")
    cursor.execute("ALTER DYNAMIC TABLE bronze_silver.stg_operations_metrics REFRESH")
    print("   ✅ Silver refreshed")

    cursor.execute("ALTER DYNAMIC TABLE bronze_gold.operations_kpis_monthly REFRESH")
    print("   ✅ Gold refreshed")

    cursor.execute("ALTER DYNAMIC TABLE gold.practice_analytics_unified REFRESH")
    print("   ✅ Unified view refreshed")
    print()

    # Verify final data quality
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN visits_total > 0 THEN 1 ELSE 0 END) as has_visits,
            SUM(CASE WHEN case_acceptance_rate_pct > 0 THEN 1 ELSE 0 END) as has_case_acceptance,
            SUM(CASE WHEN new_patients_total > 0 THEN 1 ELSE 0 END) as has_new_patients,
            SUM(CASE WHEN hygiene_capacity_slots > 0 THEN 1 ELSE 0 END) as has_hygiene_capacity
        FROM gold.practice_analytics_unified
    """)
    result = cursor.fetchone()

    print("📊 DATA QUALITY AFTER IMPROVED PARSING:")
    print("=" * 80)
    print(f"   Total Records: {result[0]}")
    print(f"   Has Visits: {result[1]} ({result[1]/result[0]*100:.1f}%)")
    print(f"   Has Case Acceptance: {result[2]} ({result[2]/result[0]*100:.1f}%)")
    print(f"   Has New Patients: {result[3]} ({result[3]/result[0]*100:.1f}%)")
    print(f"   Has Hygiene Capacity: {result[4]} ({result[4]/result[0]*100:.1f}%)")

    cursor.close()
    conn.close()

    print()
    print("=" * 80)
    print("✅ ALL 14 PRACTICES LOADED WITH IMPROVED PARSER!")
    print("=" * 80)


if __name__ == '__main__':
    load_all_practices()
