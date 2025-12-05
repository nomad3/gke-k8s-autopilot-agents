#!/usr/bin/env python3
"""
Fix Row Access Policy
Executes the row access policy fix script
"""

import os
import sys
import snowflake.connector
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv('mcp-server/.env')

# Snowflake connection parameters
SNOWFLAKE_CONFIG = {
    'account': os.getenv('SNOWFLAKE_ACCOUNT'),
    'user': os.getenv('SNOWFLAKE_USER'),
    'password': os.getenv('SNOWFLAKE_PASSWORD'),
    'role': os.getenv('SNOWFLAKE_ROLE', 'ACCOUNTADMIN'),
    'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
    'database': os.getenv('SNOWFLAKE_DATABASE', 'DENTAL_ERP_DW'),
}

def execute_fix():
    """Execute the row access policy fix"""

    print("=" * 80)
    print("  Fixing Row Access Policy")
    print("=" * 80)
    print()

    # Read fix script
    script_path = Path('fix-row-access-policy.sql')
    fix_sql = script_path.read_text()

    # Connect to Snowflake
    print("→ Connecting to Snowflake...")
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    cursor = conn.cursor()
    print("✅ Connected")
    print()

    # Split and execute statements
    statements = [s.strip() for s in fix_sql.split(';') if s.strip() and not s.strip().startswith('--')]

    for i, statement in enumerate(statements, 1):
        if 'SELECT' in statement and 'as status' in statement:
            try:
                cursor.execute(statement)
                result = cursor.fetchone()
                if result:
                    print(f"  [{i}/{len(statements)}] {result[0]}")
            except Exception as e:
                print(f"  [{i}/{len(statements)}] Status query: {e}")
        else:
            try:
                cursor.execute(statement)
                if 'CREATE TABLE' in statement:
                    print(f"  [{i}/{len(statements)}] ✓ Created tenant_access_mapping table")
                elif 'INSERT INTO' in statement:
                    print(f"  [{i}/{len(statements)}] ✓ Inserted access grants")
                elif 'CREATE OR REPLACE ROW ACCESS POLICY' in statement:
                    print(f"  [{i}/{len(statements)}] ✓ Created row access policy")
                elif 'ADD ROW ACCESS POLICY' in statement:
                    table = statement.split('ALTER TABLE')[1].split('ADD ROW')[0].strip()
                    print(f"  [{i}/{len(statements)}] ✓ Applied policy to {table}")
                elif 'SHOW ROW ACCESS POLICIES' in statement:
                    cursor.execute(statement)
                    policies = cursor.fetchall()
                    print(f"  [{i}/{len(statements)}] ✓ Found {len(policies)} row access policies")
            except Exception as e:
                print(f"  [{i}/{len(statements)}] ⚠️  {str(e)[:100]}")

    print()
    print("=" * 80)
    print("✅ Row access policy fix complete!")
    print("=" * 80)
    print()

    cursor.close()
    conn.close()

if __name__ == '__main__':
    execute_fix()
