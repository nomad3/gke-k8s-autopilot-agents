#!/usr/bin/env python3
"""
Check for duplicate NetSuite records in Snowflake Bronze layer
"""

import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

def connect_snowflake():
    return snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema='BRONZE'
    )

def main():
    print("=" * 80)
    print("NetSuite Data Duplication Check")
    print("=" * 80)
    print()

    conn = connect_snowflake()
    cursor = conn.cursor()

    tables = [
        'NETSUITE_JOURNAL_ENTRIES',
        'NETSUITE_ACCOUNTS',
        'NETSUITE_VENDOR_BILLS',
        'NETSUITE_CUSTOMERS',
        'NETSUITE_VENDORS',
        'NETSUITE_SUBSIDIARIES'
    ]

    total_duplicates = 0

    for table in tables:
        # Check for duplicate IDs
        cursor.execute(f"""
            SELECT
                ID,
                COUNT(*) as duplicate_count
            FROM BRONZE.{table}
            GROUP BY ID
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC
            LIMIT 5
        """)

        duplicates = cursor.fetchall()

        if duplicates:
            print(f"❌ {table}:")
            print(f"   Found {len(duplicates)} duplicate IDs (showing top 5):")
            for id, count in duplicates:
                print(f"     - ID {id}: {count} occurrences")
                total_duplicates += (count - 1)  # Count extras only
        else:
            print(f"✅ {table}: No duplicates")

        # Also check total vs distinct
        cursor.execute(f"""
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT ID) as distinct_ids
            FROM BRONZE.{table}
        """)
        total, distinct = cursor.fetchone()
        if total != distinct:
            print(f"   ⚠️  Total: {total}, Distinct IDs: {distinct}, Duplicates: {total - distinct}")

        print()

    print("=" * 80)
    if total_duplicates > 0:
        print(f"❌ DUPLICATES FOUND: {total_duplicates} duplicate records")
        print()
        print("Recommendation: Add UNIQUE constraint or ON CONFLICT logic to prevent duplicates")
    else:
        print("✅ NO DUPLICATES FOUND - Data quality is good")
    print("=" * 80)

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
