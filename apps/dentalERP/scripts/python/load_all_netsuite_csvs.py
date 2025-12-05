#!/usr/bin/env python3
"""
Load ALL NetSuite TransactionDetail CSV files to Snowflake
Extracts subsidiary name from CSV header and loads transaction data
"""

import os
import csv
import snowflake.connector
from dotenv import load_dotenv
from pathlib import Path

load_dotenv('mcp-server/.env')

# Mapping of subsidiary names to practice IDs
SUBSIDIARY_TO_PRACTICE = {
    'SCDP Eastlake, LLC': 'sed',
    'SCDP Laguna Hills, LLC': 'lhd',
    'SCDP Laguna Hills II, LLC': 'lhd_ii',
    'SCDP Torrey Pines, LLC': 'efd_i',
    'SCDP Torrey Highlands, LLC': 'th',
    'SCDP Del Sur Ranch, LLC': 'dsr',
    'SCDP Coronado, LLC': 'coronado',
    'SCDP Temecula, LLC': 'temecula',
    'SCDP Kearny Mesa, LLC': 'km',
    'SCDP Vista, LLC': 'vista',
    'SCDP Carlsbad, LLC': 'carlsbad',
    'SCDP UTC, LLC': 'ucfd',
    'Steve P. Theodosis Dental Corporation, PC': 'theodosis',
}

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
print("LOADING ALL NETSUITE TRANSACTION DETAIL CSVs")
print("=" * 80)
print()

# Clear existing data
print("Clearing existing transaction data...")
cursor.execute("DELETE FROM bronze.netsuite_transaction_details")
conn.commit()
print("✅ Cleared")
print()

csv_files = sorted([f for f in os.listdir('backup') if f.startswith('TransactionDetail-') and f.endswith('.csv')])

total_loaded = 0

for csv_file in csv_files:
    filepath = f'backup/{csv_file}'

    print(f"📄 Processing: {csv_file}")

    # Read subsidiary name from second row
    with open(filepath, 'r') as f:
        lines = f.readlines()
        if len(lines) >= 2:
            parent_line = lines[1].strip().strip('"')
            parts = parent_line.split(':')
            subsidiary_name = parts[-1].strip() if len(parts) > 1 else 'Unknown'

            practice_id = SUBSIDIARY_TO_PRACTICE.get(subsidiary_name, 'unknown')

            print(f"   Subsidiary: {subsidiary_name}")
            print(f"   Practice ID: {practice_id}")

    # Load CSV data (skip first 6 rows: company, parent, title, date, blank, blank)
    with open(filepath, 'r') as f:
        # Skip first 6 rows
        for _ in range(6):
            next(f)

        # Now read from row 7 which has the header
        reader = csv.DictReader(f)
        transactions = list(reader)

        if transactions:
            print(f"   Loading {len(transactions)} transactions...")

            # Bulk insert
            for txn in transactions:
                query = """
                    INSERT INTO bronze.netsuite_transaction_details
                    (TYPE, DATE, DOCUMENT, NAME, MEMO, ACCOUNT, CLR, SPLIT, QTY, AMOUNT)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                # Note: CSV headers have trailing spaces
                values = (
                    txn.get('Type ', '').strip(),
                    txn.get('Date ', '').strip(),
                    txn.get('Document Number ', '').strip(),
                    txn.get('Name ', '').strip(),
                    txn.get('Memo ', '').strip(),
                    txn.get('Account ', '').strip(),
                    txn.get('Clr ', '').strip(),
                    txn.get('Split ', '').strip(),
                    txn.get('Qty ', '').strip(),
                    txn.get('Amount ', '').strip()
                )

                try:
                    cursor.execute(query, values)
                except Exception as e:
                    print(f"      ⚠️  Error on row: {str(e)[:50]}")

            conn.commit()
            total_loaded += len(transactions)
            print(f"   ✅ Loaded {len(transactions)} transactions")
        else:
            print(f"   ⚠️  No transaction data found")

    print()

print("=" * 80)
print(f"✅ TOTAL LOADED: {total_loaded} transactions from {len(csv_files)} files")
print("=" * 80)
print()

# Verify load
cursor.execute("SELECT COUNT(*) FROM bronze.netsuite_transaction_details WHERE TYPE != 'Type'")
count = cursor.fetchone()[0]
print(f"📊 Records in bronze.netsuite_transaction_details: {count}")

# Check practice distribution
cursor.execute("""
    SELECT practice_id, COUNT(*)
    FROM bronze.netsuite_transactions_with_practice
    WHERE practice_id IS NOT NULL
    GROUP BY practice_id
    ORDER BY COUNT(*) DESC
""")

print("\nPractices identified:")
for r in cursor.fetchall():
    print(f"  {r[0]:15s}: {r[1]:5d} transactions")

cursor.close()
conn.close()

print()
print("✅ All NetSuite CSV data loaded!")
print("   Next: Refresh netsuite_monthly_financials and unified view")
