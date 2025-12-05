#!/usr/bin/env python3
"""
Parse Operations Report CSV and Upload to Snowflake
Extracts all practice data from SCDP Monthly Operations Report
"""

import pandas as pd
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import snowflake.connector
from dotenv import load_dotenv

load_dotenv('mcp-server/.env')


# Practice code mapping from sheet names
PRACTICE_MAPPING = {
    'LHD': 'Laguna Hills Dental',
    'EFD I': 'Encinitas Family Dental I',
    'CVFD': 'Carmel Valley Family Dental',
    'DSR': 'Del Sur',
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


def extract_metrics_from_operations_report(excel_file: str):
    """
    Extract all practice metrics from Operations Report Excel

    Returns:
        List of dictionaries, one per practice per month
    """
    print("=" * 80)
    print("PARSING OPERATIONS REPORT")
    print("=" * 80)
    print()

    print(f"📄 Reading file: {excel_file}")

    # Read the Operating Metrics sheet
    df = pd.read_excel(excel_file, sheet_name='Operating Metrics')

    print(f"   Dimensions: {df.shape[0]} rows × {df.shape[1]} columns")
    print()

    # Extract date headers from row 4 (index 4)
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

    print(f"📅 Found {len(dates)} month columns:")
    print(f"   First: {dates[0].strftime('%Y-%m-%d')}")
    print(f"   Last: {dates[-1].strftime('%Y-%m-%d')}")
    print()

    # Define metric mappings (row labels → JSON keys)
    metric_mappings = {
        # Production
        'Doctor': 'gross_production_doctor',
        'Specialty': 'gross_production_specialty',
        'Hygiene': 'gross_production_hygiene',
        'Total': 'total_production',
        'Net Production (Revenue)': 'net_production',
        'Collections': 'collections',

        # Visits
        'Doctor #1': 'visits_doctor_1',
        'Doctor #2': 'visits_doctor_2',
        'Specialists': 'visits_specialist',
        'Hygienists': 'visits_hygiene',

        # Case Acceptance
        'Treatment Presented': 'treatment_presented',
        'Treatment Accepted': 'treatment_accepted',

        # New Patients
        'New Patients': 'new_patients_total',
        'Reappointment Rate': 'new_patients_reappt_rate',

        # Hygiene Efficiency
        'Hygiene Capacity': 'hygiene_capacity_slots',
        'Hygiene Net Production': 'hygiene_net_production',
        'Hygiene Compensation': 'hygiene_compensation',
        'Ratio': 'hygiene_productivity_ratio',
    }

    # Extract metrics for one practice for all months
    all_records = []
    practice_code = 'LHD'  # Start with Laguna Hills
    practice_name = PRACTICE_MAPPING[practice_code]

    print(f"🏥 Extracting data for: {practice_name} ({practice_code})")
    print()

    # For each month column
    for date, col_idx in zip(dates, date_col_indices):
        report_month = date.strftime('%Y-%m-01')
        metrics = {}

        # Scan through rows to find metric values
        for row_idx in range(6, min(len(df), 110)):  # Rows 6-110 contain metrics
            row = df.iloc[row_idx]

            # Column 1 has the metric category/label
            label = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''

            if label in metric_mappings:
                metric_key = metric_mappings[label]
                value = row.iloc[col_idx]

                if pd.notna(value) and value != '':
                    try:
                        # Convert to float
                        if isinstance(value, (int, float)):
                            metrics[metric_key] = float(value)
                        else:
                            metrics[metric_key] = float(str(value).replace(',', ''))
                    except:
                        pass

        # Calculate total visits if we have components
        if 'visits_doctor_1' in metrics and 'visits_doctor_2' in metrics:
            metrics['visits_doctor_total'] = metrics.get('visits_doctor_1', 0) + metrics.get('visits_doctor_2', 0)

        if 'visits_doctor_total' in metrics and 'visits_hygiene' in metrics:
            visits_specialist = metrics.get('visits_specialist', 0)
            metrics['visits_total'] = metrics['visits_doctor_total'] + visits_specialist + metrics['visits_hygiene']

        # Only add if we have meaningful data
        if len(metrics) > 5:
            record = {
                'practice_code': practice_code.lower().replace(' ', '_'),
                'practice_name': practice_name,
                'report_month': report_month,
                'tenant_id': 'silvercreek',
                'raw_data': metrics,
                'source_file': Path(excel_file).name
            }
            all_records.append(record)

    print(f"   ✅ Extracted {len(all_records)} monthly records")
    print(f"   📊 Average metrics per month: {sum(len(r['raw_data']) for r in all_records) / len(all_records):.0f}")
    print()

    return all_records


def upload_to_snowflake(records: list):
    """
    Upload all records to Snowflake Bronze layer
    """
    print("=" * 80)
    print("UPLOADING TO SNOWFLAKE BRONZE LAYER")
    print("=" * 80)
    print()

    # Connect to Snowflake
    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        role=os.getenv('SNOWFLAKE_ROLE', 'ACCOUNTADMIN'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE')
    )

    cursor = conn.cursor()

    print(f"📤 Uploading {len(records)} records...")
    print()

    success_count = 0
    error_count = 0

    for i, record in enumerate(records, 1):
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
                    '{record['source_file']}' AS source_file,
                    CURRENT_TIMESTAMP() AS uploaded_at,
                    CURRENT_TIMESTAMP() AS loaded_at
            ) AS source
            ON target.id = source.id
            WHEN MATCHED THEN
                UPDATE SET
                    raw_data = source.raw_data,
                    source_file = source.source_file,
                    loaded_at = source.loaded_at
            WHEN NOT MATCHED THEN
                INSERT (id, practice_code, practice_name, report_month, tenant_id, raw_data, source_file, uploaded_at, loaded_at)
                VALUES (source.id, source.practice_code, source.practice_name, source.report_month,
                        source.tenant_id, source.raw_data, source.source_file, source.uploaded_at, source.loaded_at)
        """

        try:
            cursor.execute(query)
            conn.commit()
            success_count += 1
            print(f"   [{i:2d}/{len(records)}] ✅ {record['practice_code']:20s} {record['report_month']} ({len(record['raw_data'])} metrics)")
        except Exception as e:
            error_count += 1
            print(f"   [{i:2d}/{len(records)}] ❌ {record_id}: {str(e)[:60]}")

    print()
    print(f"✅ Upload complete: {success_count} successful, {error_count} errors")
    print()

    # Verify Bronze count
    cursor.execute("SELECT COUNT(*) FROM bronze.operations_metrics_raw")
    total_count = cursor.fetchone()[0]
    print(f"📊 Total records in Bronze: {total_count}")

    cursor.close()
    conn.close()

    return success_count, error_count


def refresh_dynamic_tables():
    """
    Force refresh Silver and Gold dynamic tables
    """
    print()
    print("=" * 80)
    print("REFRESHING DYNAMIC TABLES")
    print("=" * 80)
    print()

    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        role=os.getenv('SNOWFLAKE_ROLE'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE')
    )

    cursor = conn.cursor()

    print("🔄 Refreshing Silver: bronze_silver.stg_operations_metrics...")
    cursor.execute("ALTER DYNAMIC TABLE bronze_silver.stg_operations_metrics REFRESH")
    print("   ✅ Silver refreshed")
    print()

    print("🔄 Refreshing Gold: bronze_gold.operations_kpis_monthly...")
    cursor.execute("ALTER DYNAMIC TABLE bronze_gold.operations_kpis_monthly REFRESH")
    print("   ✅ Gold refreshed")
    print()

    cursor.close()
    conn.close()


def verify_data_pipeline():
    """
    Verify data in each layer and show sample KPIs
    """
    print("=" * 80)
    print("VERIFYING DATA PIPELINE")
    print("=" * 80)
    print()

    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        role=os.getenv('SNOWFLAKE_ROLE'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE')
    )

    cursor = conn.cursor()

    # 1. Bronze Layer
    print("1️⃣  BRONZE LAYER: operations_metrics_raw")
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT practice_code), MIN(report_month), MAX(report_month) FROM bronze.operations_metrics_raw")
    result = cursor.fetchone()
    print(f"   Records: {result[0]}")
    print(f"   Practices: {result[1]}")
    print(f"   Date Range: {result[2]} to {result[3]}")
    print()

    # 2. Silver Layer
    print("2️⃣  SILVER LAYER: stg_operations_metrics")
    cursor.execute("SELECT COUNT(*), SUM(total_production), SUM(collections), SUM(visits_total) FROM bronze_silver.stg_operations_metrics")
    result = cursor.fetchone()
    print(f"   Records: {result[0]}")
    print(f"   Total Production: ${result[1]:,.2f}" if result[1] else "   Total Production: N/A")
    print(f"   Total Collections: ${result[2]:,.2f}" if result[2] else "   Total Collections: N/A")
    print(f"   Total Visits: {result[3]:,}" if result[3] else "   Total Visits: N/A")
    print()

    # 3. Gold Layer
    print("3️⃣  GOLD LAYER: operations_kpis_monthly")
    cursor.execute("""
        SELECT
            COUNT(*) AS record_count,
            SUM(total_production) AS total_prod,
            AVG(collection_rate_pct) AS avg_collection_rate,
            AVG(ppv_overall) AS avg_ppv,
            AVG(case_acceptance_rate_pct) AS avg_case_acceptance,
            AVG(hygiene_productivity_ratio) AS avg_hygiene_ratio
        FROM bronze_gold.operations_kpis_monthly
    """)
    result = cursor.fetchone()
    print(f"   Records: {result[0]}")
    if result[1]:
        print(f"   Total Production: ${result[1]:,.2f}")
        print(f"   Avg Collection Rate: {result[2]:.1f}%")
        print(f"   Avg Production/Visit: ${result[3]:,.2f}")
        print(f"   Avg Case Acceptance: {result[4]:.1f}%")
        print(f"   Avg Hygiene Ratio: {result[5]:.2f}")
    print()

    # 4. Sample Records
    print("📊 SAMPLE GOLD LAYER RECORDS:")
    print("-" * 80)
    cursor.execute("""
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
        ORDER BY report_month DESC
        LIMIT 5
    """)

    results = cursor.fetchall()
    for row in results:
        print(f"   Practice: {row[0]:25s} Month: {row[1]}")
        print(f"      Production: ${row[2]:>12,.2f}  |  Collection Rate: {row[3]:>5.1f}%")
        print(f"      PPV: ${row[4]:>7,.2f}  |  Case Acceptance: {row[5]:>5.1f}%  |  Hygiene Ratio: {row[6]:>4.2f}")
        print(f"      LTM Production: ${row[7]:>12,.2f}" if row[7] else f"      LTM Production: N/A")
        print()

    cursor.close()
    conn.close()


if __name__ == '__main__':
    excel_file = 'examples/ingestion/Operations Report(28).xlsx'

    # Step 1: Parse Excel
    records = extract_metrics_from_operations_report(excel_file)

    # Step 2: Upload to Bronze
    success, errors = upload_to_snowflake(records)

    # Step 3: Refresh dynamic tables
    if success > 0:
        refresh_dynamic_tables()

        # Wait a moment for refresh to complete
        print("⏳ Waiting 5 seconds for dynamic table refresh to complete...")
        import time
        time.sleep(5)
        print()

        # Step 4: Verify pipeline
        verify_data_pipeline()

    print("=" * 80)
    print("✅ OPERATIONS REPORT PARSING COMPLETE")
    print("=" * 80)
    print()
    print(f"📊 Summary:")
    print(f"   • Parsed: {len(records)} monthly records")
    print(f"   • Uploaded: {success} successful")
    print(f"   • Errors: {errors}")
    print()
    print("🚀 Next: Test API endpoints")
    print("   curl http://localhost:8085/api/v1/operations/kpis/monthly \\")
    print("     -H 'Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars' \\")
    print("     -H 'X-Tenant-ID: silvercreek'")
    print()
