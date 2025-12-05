#!/usr/bin/env python3
"""
Verify PDF parsing results in Snowflake
Queries Bronze, Silver, and Gold layers to verify data pipeline
"""

import os
import snowflake.connector
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from mcp-server/.env
env_path = Path(__file__).parent.parent.parent / "mcp-server" / ".env"
load_dotenv(env_path)

def main():
    print("=" * 80)
    print("PDF Parsing Verification")
    print("=" * 80)
    print()

    # Connect to Snowflake
    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database='DENTAL_ERP_DW',
        schema='PUBLIC'
    )

    cursor = conn.cursor()

    # Query Bronze layer
    print("Step 1: Bronze Layer (Raw Data)")
    print("-" * 80)

    cursor.execute("""
        SELECT
            practice_location,
            report_type,
            extraction_method,
            file_name,
            TO_VARCHAR(uploaded_at, 'YYYY-MM-DD HH24:MI:SS') as uploaded_at
        FROM bronze.pms_day_sheets
        ORDER BY uploaded_at DESC
        LIMIT 15
    """)

    bronze_rows = cursor.fetchall()
    print(f"Found {len(bronze_rows)} records in Bronze layer:\n")

    for row in bronze_rows:
        print(f"  • {row[0]:15} | {row[1]:20} | {row[2]:10} | {row[3][:45]}")

    print()

    # Query Silver layer
    print("Step 2: Silver Layer (Parsed & Structured)")
    print("-" * 80)

    cursor.execute("""
        SELECT
            practice_location,
            report_date,
            total_production,
            net_production,
            patient_visits,
            total_amount_sum,
            extraction_method,
            data_quality_score
        FROM bronze_silver.stg_pms_day_sheets
        ORDER BY report_date DESC, practice_location
        LIMIT 20
    """)

    silver_rows = cursor.fetchall()
    print(f"Found {len(silver_rows)} records in Silver layer:\n")

    print(f"{'Practice':<15} | {'Date':<12} | {'Production':>12} | {'Net Prod':>12} | {'Visits':>7} | {'Method':>10} | {'Quality':>7}")
    print("-" * 100)

    for row in silver_rows:
        prod = f"${float(row[2]):,.2f}" if row[2] else "N/A"
        net = f"${float(row[3]):,.2f}" if row[3] else "N/A"
        amount_sum = f"${float(row[5]):,.2f}" if row[5] else "N/A"
        visits = str(row[4]) if row[4] else "N/A"
        method = str(row[6]) if row[6] else "N/A"
        quality = f"{float(row[7]):.2f}" if row[7] else "N/A"

        # Use total_amount_sum if total_production is null (rules-based extraction)
        display_prod = prod if row[2] else amount_sum

        print(f"{row[0]:<15} | {str(row[1]):<12} | {display_prod:>12} | {net:>12} | {visits:>7} | {method:>10} | {quality:>7}")

    print()

    # Query Gold layer
    print("Step 3: Gold Layer (Business Metrics)")
    print("-" * 80)

    cursor.execute("""
        SELECT
            practice_location,
            report_date,
            total_production,
            net_production,
            patient_visits,
            production_per_visit,
            collection_rate_pct,
            extraction_method,
            duplicate_count
        FROM bronze_gold.daily_production_metrics
        ORDER BY report_date DESC, practice_location
        LIMIT 20
    """)

    gold_rows = cursor.fetchall()
    print(f"Found {len(gold_rows)} metrics in Gold layer:\n")

    print(f"{'Practice':<15} | {'Date':<12} | {'Production':>12} | {'$/Visit':>10} | {'Visits':>7} | {'Method':>10} | {'Dups':>5}")
    print("-" * 95)

    for row in gold_rows:
        prod = f"${float(row[2]):,.2f}" if row[2] else "N/A"
        per_visit = f"${float(row[5]):,.0f}" if row[5] else "N/A"
        visits = str(row[4]) if row[4] else "N/A"
        method = str(row[7]) if row[7] else "N/A"
        dups = str(row[8]) if row[8] else "0"

        print(f"{row[0]:<15} | {str(row[1]):<12} | {prod:>12} | {per_visit:>10} | {visits:>7} | {method:>10} | {dups:>5}")

    # Summary statistics
    print()
    print("Summary Statistics:")
    print("-" * 50)

    total_prod = sum(float(row[2]) for row in gold_rows if row[2])
    total_visits = sum(int(row[4]) for row in gold_rows if row[4])
    avg_per_visit = total_prod / total_visits if total_visits > 0 else 0

    practices = set(row[0] for row in gold_rows)
    dates = set(str(row[1]) for row in gold_rows)

    print(f"  Practices: {len(practices)} ({', '.join(sorted(practices))})")
    print(f"  Date Range: {len(dates)} unique dates")
    print(f"  Total Production: ${total_prod:,.2f}")
    print(f"  Total Visits: {total_visits}")
    print(f"  Average $/Visit: ${avg_per_visit:,.2f}")

    # Data Quality Analysis
    print()
    print("Data Quality Analysis:")
    print("-" * 50)

    cursor.execute("""
        SELECT
            extraction_method,
            COUNT(*) as count,
            AVG(data_quality_score) as avg_quality,
            COUNT(CASE WHEN total_production IS NOT NULL THEN 1 END) as parsed_production,
            COUNT(CASE WHEN total_amount_sum IS NOT NULL THEN 1 END) as parsed_amounts
        FROM bronze_silver.stg_pms_day_sheets
        GROUP BY extraction_method
    """)

    quality_rows = cursor.fetchall()
    for row in quality_rows:
        print(f"  {row[0]:10} - {row[1]:2} records, Quality: {float(row[2]):.2f}, Production: {row[3]}, Amounts: {row[4]}")

    cursor.close()
    conn.close()

    print()
    print("=" * 80)
    print("Verification Complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
