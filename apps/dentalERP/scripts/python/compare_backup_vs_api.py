#!/usr/bin/env python3
"""
Compare NetSuite backup CSVs vs API ingestion
Verifies we're not missing any records
"""

import csv
import os
import snowflake.connector
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

def count_csv_records(filepath):
    """Count records in CSV file"""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        return sum(1 for row in reader)

def get_snowflake_counts():
    """Get record counts from Snowflake"""
    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE')
    )

    cursor = conn.cursor()

    counts = {}
    tables = [
        'netsuite_journal_entries',
        'netsuite_accounts',
        'netsuite_vendor_bills',
        'netsuite_customers',
        'netsuite_vendors',
        'netsuite_subsidiaries',
        'netsuite_items',
        'netsuite_invoices',
        'netsuite_payments'
    ]

    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(DISTINCT id) FROM bronze.{table}")
            count = cursor.fetchone()[0]
            counts[table] = count
        except:
            counts[table] = 0

    conn.close()
    return counts

def main():
    print("="*80)
    print("NetSuite Backup CSV vs API Ingestion Comparison")
    print("="*80)
    print()

    backup_dir = Path("backup")

    # CSV to Snowflake table mapping
    csv_mappings = {
        "vendorlist.csv": "netsuite_vendors",
        "custjoblist.csv": "netsuite_customers",
        "itemlist.csv": "netsuite_items",
        "report_250_transactiondetail.csv": "netsuite_journal_entries",
        "employeelist.csv": "netsuite_employees",
    }

    # Get Snowflake counts
    print("Fetching Snowflake record counts...")
    snowflake_counts = get_snowflake_counts()
    print("✅ Snowflake counts retrieved\n")

    # Compare each CSV
    print(f"{'CSV File':<50} {'CSV Count':>12} {'Snowflake':>12} {'Status':>10}")
    print("="*90)

    total_csv = 0
    total_snowflake = 0
    missing_data = []

    for csv_file, table_name in csv_mappings.items():
        csv_path = backup_dir / csv_file

        if csv_path.exists():
            csv_count = count_csv_records(csv_path)
            sf_count = snowflake_counts.get(table_name, 0)

            total_csv += csv_count
            total_snowflake += sf_count

            # Determine status
            if sf_count == 0:
                status = "❌ MISSING"
                missing_data.append((csv_file, csv_count, sf_count))
            elif sf_count < csv_count * 0.9:  # Less than 90% of CSV data
                status = "⚠️ PARTIAL"
                missing_data.append((csv_file, csv_count, sf_count))
            else:
                status = "✅ OK"

            print(f"{csv_file:<50} {csv_count:>12,} {sf_count:>12,} {status:>10}")
        else:
            print(f"{csv_file:<50} {'NOT FOUND':>12} {'N/A':>12} {'⚠️ SKIP':>10}")

    print("="*90)
    print(f"{'TOTAL':<50} {total_csv:>12,} {total_snowflake:>12,}")
    print()

    # Check for additional Snowflake tables not in CSV
    print("Additional Snowflake tables (not in backup CSVs):")
    print("-"*90)

    for table, count in snowflake_counts.items():
        if count > 0 and table not in csv_mappings.values():
            print(f"  {table:<40} {count:>10,} records (API only)")

    print()

    # Summary
    if missing_data:
        print("="*80)
        print("⚠️  MISSING OR PARTIAL DATA DETECTED")
        print("="*80)
        for csv_file, csv_count, sf_count in missing_data:
            pct = (sf_count / csv_count * 100) if csv_count > 0 else 0
            print(f"  {csv_file}: {pct:.1f}% ingested ({sf_count:,} of {csv_count:,})")
        print()
        print("Recommendation: Review API ingestion for these record types")
    else:
        print("✅ All backup data successfully ingested via API")

if __name__ == "__main__":
    main()
