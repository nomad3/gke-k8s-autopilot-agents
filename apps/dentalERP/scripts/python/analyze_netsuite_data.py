#!/usr/bin/env python3
"""Analyze NetSuite data to find how practices are identified"""

import os, snowflake.connector
from dotenv import load_dotenv

load_dotenv('mcp-server/.env')
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
print("NETSUITE DATA STRUCTURE ANALYSIS")
print("=" * 80)

# Get all columns
cursor.execute("DESCRIBE TABLE bronze.netsuite_transaction_details")
columns = [c[0] for c in cursor.fetchall()]

print(f"\nColumns in netsuite_transaction_details ({len(columns)}):")
for col in columns:
    print(f"  • {col}")

# Get sample records (skip header row which has 'Type' = 'Type')
cursor.execute("SELECT * FROM bronze.netsuite_transaction_details WHERE TYPE != 'Type' LIMIT 10")
results = cursor.fetchall()

if results:
    print(f"\nSample Transactions ({len(results)}):")
    for i, r in enumerate(results[:3], 1):
        print(f"\n  Transaction {i}:")
        for col, val in zip(columns, r):
            if val and str(val).strip():
                print(f"     {col}: {val}")

# Check for patterns in NAME, MEMO, ACCOUNT columns that might indicate practice
print("\n" + "=" * 80)
print("LOOKING FOR PRACTICE/LOCATION INDICATORS:")
print("=" * 80)

for col in ['NAME', 'MEMO', 'ACCOUNT', 'SPLIT', 'DOCUMENT']:
    try:
        cursor.execute(f"""
            SELECT DISTINCT {col}
            FROM bronze.netsuite_transaction_details
            WHERE {col} IS NOT NULL
              AND {col} != '{col}'
              AND {col} != ''
            LIMIT 20
        """)
        values = cursor.fetchall()
        if values:
            unique_values = [v[0] for v in values if v[0]]
            if unique_values:
                print(f"\n{col} column samples ({len(unique_values)}):")
                for v in unique_values[:15]:
                    if any(keyword in str(v).upper() for keyword in ['EASTLAKE', 'LAGUNA', 'TORREY', 'ENCINITAS', 'DENTAL', 'SCDP', 'ADS', 'SED']):
                        print(f"  ⭐ {v}")  # Highlight potential practice names
                    else:
                        print(f"  • {v}")
    except Exception as e:
        print(f"\n{col}: Error - {str(e)[:50]}")

cursor.close()
conn.close()

print()
print("=" * 80)
print("💡 Look for practice names (Eastlake, Laguna Hills, Torrey Pines, etc.)")
print("   These indicate which column contains the practice identifier")
