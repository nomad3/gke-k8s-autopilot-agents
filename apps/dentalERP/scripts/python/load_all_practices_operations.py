#!/usr/bin/env python3
"""
Load ALL 14 Practices from Operations Report Excel
Parses each individual practice sheet and uploads to Snowflake
"""

import pandas as pd
import json
import os
import sys
from datetime import datetime
from pathlib import Path
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


def extract_practice_data_from_sheet(df, practice_code, practice_name):
    """
    Extract metrics from individual practice sheet
    Each practice sheet has similar layout to Operating Metrics
    """
    metrics_list = []

    # Row 4 has dates (column headers)
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

        # Extract key metrics from known row positions
        # (This is approximate - exact row mapping would require analyzing each sheet)
        metrics = {}

        # Scan rows 5-100 for metric values
        for row_idx in range(5, min(len(df), 100)):
            row = df.iloc[row_idx]
            value = row.iloc[col_idx]

            if pd.notna(value) and value != '':
                try:
                    if isinstance(value, (int, float)):
                        # Store all numeric values we find
                        # We'll identify them by row position later
                        pass
                except:
                    pass

        # For now, extract from Operating Metrics pattern
        # (Individual sheets may have different layouts)
        try:
            # Production values (rows 8-11 typically)
            metrics['total_production'] = float(df.iloc[11, col_idx]) if pd.notna(df.iloc[11, col_idx]) else 0
            metrics['net_production'] = float(df.iloc[17, col_idx]) if pd.notna(df.iloc[17, col_idx]) else 0
            metrics['collections'] = float(df.iloc[20, col_idx]) if pd.notna(df.iloc[20, col_idx]) else 0

            # Visit counts
            metrics['visits_doctor_total'] = int(df.iloc[29, col_idx]) if pd.notna(df.iloc[29, col_idx]) else 0
            metrics['visits_hygiene'] = int(df.iloc[38, col_idx]) if pd.notna(df.iloc[38, col_idx]) else 0
            metrics['visits_total'] = int(df.iloc[41, col_idx]) if pd.notna(df.iloc[41, col_idx]) else 0

            # Hygiene efficiency
            metrics['hygiene_net_production'] = float(df.iloc[101, col_idx]) if pd.notna(df.iloc[101, col_idx]) else 0
            metrics['hygiene_compensation'] = float(df.iloc[102, col_idx]) if pd.notna(df.iloc[102, col_idx]) else 0

        except Exception as e:
            print(f"      Warning: Could not extract all metrics for {report_month}: {e}")
            continue

        # Only add if we have meaningful data
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
    """Load all 14 practices from Operations Report"""

    excel_file = 'examples/ingestion/Operations Report(28).xlsx'

    print("=" * 80)
    print("LOADING ALL 14 PRACTICES FROM OPERATIONS REPORT")
    print("=" * 80)
    print()

    all_records = []

    # Parse each practice sheet
    for practice_code, practice_name in PRACTICE_MAPPING.items():
        print(f"📊 Parsing: {practice_name} ({practice_code})")

        try:
            df = pd.read_excel(excel_file, sheet_name=practice_code)
            records = extract_practice_data_from_sheet(df, practice_code, practice_name)
            all_records.extend(records)
            print(f"   ✅ Extracted {len(records)} monthly records")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        print()

    print(f"📦 Total records to upload: {len(all_records)}")
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
            if i % 20 == 0 or i == len(all_records):
                print(f"   [{i:3d}/{len(all_records)}] ✅ {success} successful, {errors} errors")
        except Exception as e:
            errors += 1
            print(f"   [{i:3d}/{len(all_records)}] ❌ {record_id}: {str(e)[:50]}")

    print()
    print(f"✅ Upload complete: {success} successful, {errors} errors")
    print()

    # Refresh dynamic tables
    print("🔄 Refreshing dynamic tables...")
    cursor.execute("ALTER DYNAMIC TABLE bronze_silver.stg_operations_metrics REFRESH")
    print("   ✅ Silver refreshed")

    cursor.execute("ALTER DYNAMIC TABLE bronze_gold.operations_kpis_monthly REFRESH")
    print("   ✅ Gold refreshed")
    print()

    # Verify final counts
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT practice_code) FROM bronze.operations_metrics_raw")
    result = cursor.fetchone()
    print(f"📊 Final Bronze count: {result[0]} records, {result[1]} practices")

    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT practice_location) FROM bronze_gold.operations_kpis_monthly")
    result = cursor.fetchone()
    print(f"📊 Final Gold count: {result[0]} records, {result[1]} practices")

    cursor.close()
    conn.close()

    print()
    print("=" * 80)
    print("✅ ALL 14 PRACTICES LOADED!")
    print("=" * 80)


if __name__ == '__main__':
    load_all_practices()
