#!/usr/bin/env python3
"""
Execute Snowflake SQL via direct connection
Standalone script - no MCP dependencies
"""

import sys
import os
import snowflake.connector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def execute_sql_file(conn, filepath, description):
    """Execute SQL file using Snowflake connector"""
    print(f"\n{'='*80}")
    print(f"Executing: {description}")
    print(f"File: {filepath}")
    print(f"{'='*80}\n")

    # Read SQL file
    with open(filepath, 'r') as f:
        sql = f.read()

    # Split by semicolon
    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]

    executed = 0
    failed = 0
    cursor = conn.cursor()

    for i, statement in enumerate(statements, 1):
        # Skip comments and empty lines
        if not statement or statement.startswith('--'):
            continue

        try:
            print(f"[{i}/{len(statements)}] Executing...")

            # Execute statement
            cursor.execute(statement)

            # Try to fetch results
            try:
                results = cursor.fetchall()
                if results:
                    print(f"  ✅ Result: {len(results)} rows")
                    if len(results) <= 10:
                        for row in results:
                            print(f"     {row}")
                else:
                    print(f"  ✅ Statement executed successfully")
            except:
                print(f"  ✅ Statement executed successfully (no results)")

            executed += 1

        except Exception as e:
            error_msg = str(e)

            # Ignore expected errors
            if any(phrase in error_msg.lower() for phrase in ['does not exist', 'already exists']):
                print(f"  ℹ️  {error_msg[:100]}")
                executed += 1
            else:
                print(f"  ❌ Error: {error_msg}")
                failed += 1

    cursor.close()
    print(f"\n{'='*80}")
    print(f"Results: {executed} executed, {failed} failed")
    print(f"{'='*80}\n")

    return failed == 0

def main():
    print("="*80)
    print("Snowflake MVP AI Setup")
    print("="*80)

    # Connect to Snowflake
    print("\nConnecting to Snowflake...")
    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema='PUBLIC'
    )
    print("✅ Connected to Snowflake\n")

    success = True

    try:
        # Execute Dynamic Tables setup
        if os.path.exists('/app/snowflake-mvp-ai-setup.sql'):
            result = execute_sql_file(conn, '/app/snowflake-mvp-ai-setup.sql', 'MVP AI Dynamic Tables Setup')
            success = success and result
        else:
            print("⚠️  snowflake-mvp-ai-setup.sql not found")

        # Execute duplicate cleanup
        if os.path.exists('/app/cleanup_netsuite_duplicates.sql'):
            result = execute_sql_file(conn, '/app/cleanup_netsuite_duplicates.sql', 'NetSuite Duplicate Cleanup')
            success = success and result
        else:
            print("⚠️  cleanup_netsuite_duplicates.sql not found")

        print("\n" + "="*80)
        if success:
            print("✅ ALL SNOWFLAKE SETUP COMPLETE")
        else:
            print("⚠️  SETUP COMPLETED WITH SOME ERRORS")
        print("="*80)

    finally:
        conn.close()
        print("\n✅ Connection closed")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
