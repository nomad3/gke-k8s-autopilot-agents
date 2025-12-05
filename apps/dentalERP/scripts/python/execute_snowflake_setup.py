#!/usr/bin/env python3
"""
Execute Snowflake MVP AI Setup
Runs Dynamic Tables SQL and duplicate cleanup
"""

import os
import sys
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

def execute_sql_file(conn, filepath, description):
    """Execute SQL file in Snowflake"""
    print(f"\n{'='*80}")
    print(f"Executing: {description}")
    print(f"File: {filepath}")
    print(f"{'='*80}\n")

    with open(filepath, 'r') as f:
        sql = f.read()

    # Split by semicolon and execute each statement
    statements = [s.strip() for s in sql.split(';') if s.strip()]

    cursor = conn.cursor()

    for i, statement in enumerate(statements, 1):
        if not statement or statement.startswith('--'):
            continue

        try:
            print(f"[{i}/{len(statements)}] Executing statement...")
            cursor.execute(statement)

            # Fetch results if available
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

        except Exception as e:
            # Ignore "does not exist" errors for DROP statements
            if "does not exist" in str(e).lower() or "already exists" in str(e).lower():
                print(f"  ℹ️  {e}")
            else:
                print(f"  ❌ Error: {e}")
                raise

    cursor.close()
    print(f"\n✅ {description} complete!\n")

def main():
    print("="*80)
    print("Snowflake MVP AI Setup Execution")
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
    print("✅ Connected to Snowflake")

    try:
        # Step 1: Execute Dynamic Tables setup
        if os.path.exists('snowflake-mvp-ai-setup.sql'):
            execute_sql_file(conn, 'snowflake-mvp-ai-setup.sql', 'MVP AI Dynamic Tables Setup')
        elif os.path.exists('/app/snowflake-mvp-ai-setup.sql'):
            execute_sql_file(conn, '/app/snowflake-mvp-ai-setup.sql', 'MVP AI Dynamic Tables Setup')
        else:
            print("⚠️  snowflake-mvp-ai-setup.sql not found, skipping")

        # Step 2: Execute duplicate cleanup
        if os.path.exists('scripts/cleanup_netsuite_duplicates.sql'):
            execute_sql_file(conn, 'scripts/cleanup_netsuite_duplicates.sql', 'Duplicate Cleanup')
        elif os.path.exists('/app/cleanup_netsuite_duplicates.sql'):
            execute_sql_file(conn, '/app/cleanup_netsuite_duplicates.sql', 'Duplicate Cleanup')
        else:
            print("⚠️  cleanup_netsuite_duplicates.sql not found, skipping")

        print("\n" + "="*80)
        print("✅ ALL SNOWFLAKE SETUP COMPLETE")
        print("="*80)

    finally:
        conn.close()
        print("\n✅ Connection closed")

if __name__ == "__main__":
    main()
