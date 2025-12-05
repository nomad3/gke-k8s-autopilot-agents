#!/usr/bin/env python3
"""
Check if NetSuite data covers all subsidiaries (multi-practice)
Verifies we're not just getting data from one practice
"""

import snowflake.connector
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    print("="*80)
    print("NetSuite Multi-Subsidiary Coverage Check")
    print("="*80)
    print()

    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE')
    )

    cursor = conn.cursor()

    # Get all subsidiaries
    print("Step 1: All Subsidiaries in NetSuite")
    print("-"*80)
    cursor.execute("""
        SELECT
            id,
            raw_data:name::string as subsidiary_name
        FROM bronze.netsuite_subsidiaries
        ORDER BY id
    """)

    subsidiaries = cursor.fetchall()
    print(f"Total subsidiaries: {len(subsidiaries)}\n")

    for sub_id, name in subsidiaries[:10]:  # Show first 10
        print(f"  {sub_id}: {name}")

    if len(subsidiaries) > 10:
        print(f"  ... and {len(subsidiaries) - 10} more\n")

    # Check journal entries by subsidiary
    print("\nStep 2: Journal Entries by Subsidiary")
    print("-"*80)
    cursor.execute("""
        SELECT
            raw_data:subsidiary.id::string as subsidiary_id,
            raw_data:subsidiary.name::string as subsidiary_name,
            COUNT(DISTINCT id) as entry_count
        FROM bronze.netsuite_journal_entries
        GROUP BY raw_data:subsidiary.id::string, raw_data:subsidiary.name::string
        ORDER BY entry_count DESC
    """)

    je_by_sub = cursor.fetchall()

    if not je_by_sub or (len(je_by_sub) == 1 and je_by_sub[0][0] is None):
        print("  ❌ WARNING: Journal entries have NO subsidiary field!")
        print("  ❌ This means data may be from ONE practice only!")
    else:
        print(f"Journal entries cover {len(je_by_sub)} subsidiaries:\n")
        for sub_id, sub_name, count in je_by_sub[:10]:
            print(f"  Subsidiary {sub_id} ({sub_name}): {count} entries")

    # Check vendor bills by subsidiary
    print("\nStep 3: Vendor Bills by Subsidiary")
    print("-"*80)
    cursor.execute("""
        SELECT
            raw_data:subsidiary.id::string as subsidiary_id,
            raw_data:subsidiary.name::string as subsidiary_name,
            COUNT(DISTINCT id) as bill_count
        FROM bronze.netsuite_vendor_bills
        GROUP BY raw_data:subsidiary.id::string, raw_data:subsidiary.name::string
        ORDER BY bill_count DESC
        LIMIT 10
    """)

    bills_by_sub = cursor.fetchall()

    if bills_by_sub and bills_by_sub[0][0] is not None:
        print(f"Vendor bills cover {len(bills_by_sub)} subsidiaries:\n")
        for sub_id, sub_name, count in bills_by_sub:
            print(f"  Subsidiary {sub_id} ({sub_name}): {count} bills")
    else:
        print("  ℹ️  Vendor bills have no subsidiary field (may be corporate-level)")

    # Summary
    print("\n" + "="*80)
    print("MULTI-PRACTICE COVERAGE SUMMARY")
    print("="*80)

    print(f"\n✅ Total Subsidiaries Registered: {len(subsidiaries)}")

    if len(je_by_sub) > 1:
        print(f"✅ Journal Entries: Data from {len(je_by_sub)} subsidiaries")
    elif je_by_sub and je_by_sub[0][0]:
        print(f"⚠️  Journal Entries: Data from ONLY {len(je_by_sub)} subsidiary")
    else:
        print(f"❌ Journal Entries: NO subsidiary tracking (possible data gap)")

    if len(bills_by_sub) > 1:
        print(f"✅ Vendor Bills: Data from {len(bills_by_sub)} subsidiaries")

    print("\nRecommendation:")
    if len(je_by_sub) <= 1:
        print("  - Check NetSuite API filters - may be limiting to one subsidiary")
        print("  - Verify NetSuite permissions allow multi-subsidiary access")
        print("  - Add subsidiary filter to API calls if needed")
    else:
        print("  - Multi-subsidiary data ingestion working correctly!")

    conn.close()

if __name__ == "__main__":
    main()
