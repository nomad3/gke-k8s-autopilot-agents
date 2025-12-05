#!/usr/bin/env python3
"""
Snowflake Migration Executor
Executes the multi-tenant migration script against Snowflake
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

def execute_migration():
    """Execute the Snowflake migration script"""

    print("=" * 80)
    print("  Snowflake Multi-Tenant Migration Executor")
    print("=" * 80)
    print()

    # Validate credentials
    for key, value in SNOWFLAKE_CONFIG.items():
        if not value:
            print(f"❌ ERROR: Missing {key} in environment variables")
            sys.exit(1)
        if key != 'password':
            print(f"✓ {key}: {value}")
    print()

    # Read migration script
    script_path = Path('snowflake-multi-tenant-migration.sql')
    if not script_path.exists():
        print(f"❌ ERROR: Migration script not found: {script_path}")
        sys.exit(1)

    print(f"✓ Loading migration script: {script_path}")
    migration_sql = script_path.read_text()
    print()

    # Connect to Snowflake
    print("→ Connecting to Snowflake...")
    try:
        conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
        cursor = conn.cursor()
        print(f"✅ Connected to Snowflake: {SNOWFLAKE_CONFIG['account']}")
        print()
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to Snowflake: {e}")
        sys.exit(1)

    # Split SQL into individual statements
    statements = []
    current_statement = []

    for line in migration_sql.split('\n'):
        # Skip empty lines and comments
        stripped = line.strip()
        if not stripped or stripped.startswith('--'):
            continue

        current_statement.append(line)

        # Check if statement ends with semicolon
        if stripped.endswith(';'):
            statements.append('\n'.join(current_statement))
            current_statement = []

    print(f"→ Executing {len(statements)} SQL statements...")
    print()

    # Execute each statement
    success_count = 0
    error_count = 0

    for i, statement in enumerate(statements, 1):
        statement = statement.strip()
        if not statement:
            continue

        # Show progress for key statements
        if 'SELECT' in statement and 'as status' in statement:
            # Extract status message
            try:
                cursor.execute(statement)
                result = cursor.fetchone()
                if result:
                    print(f"  [{i}/{len(statements)}] {result[0]}")
            except Exception as e:
                print(f"  [{i}/{len(statements)}] Status query error: {e}")
        else:
            try:
                cursor.execute(statement)
                success_count += 1

                # Show brief info for major operations
                if 'ALTER TABLE' in statement and 'ADD COLUMN' in statement:
                    table = statement.split('ALTER TABLE')[1].split('ADD COLUMN')[0].strip()
                    print(f"  [{i}/{len(statements)}] ✓ Added tenant_id to {table}")
                elif 'CREATE OR REPLACE ROW ACCESS POLICY' in statement:
                    print(f"  [{i}/{len(statements)}] ✓ Created row access policy")
                elif 'ADD ROW ACCESS POLICY' in statement:
                    table = statement.split('ALTER TABLE')[1].split('ADD ROW')[0].strip()
                    print(f"  [{i}/{len(statements)}] ✓ Applied policy to {table}")
                elif 'CLUSTER BY' in statement:
                    table = statement.split('ALTER TABLE')[1].split('CLUSTER')[0].strip()
                    print(f"  [{i}/{len(statements)}] ✓ Updated clustering for {table}")

            except Exception as e:
                error_count += 1
                print(f"  [{i}/{len(statements)}] ⚠️  Warning: {str(e)[:100]}")
                # Continue on errors (tables might not exist yet)

    print()
    print("=" * 80)
    print(f"✅ Migration execution complete!")
    print(f"   Successful: {success_count} statements")
    print(f"   Warnings: {error_count} statements")
    print("=" * 80)
    print()

    # Run validation queries
    print("→ Running validation queries...")
    print()

    validation_queries = [
        ("Bronze layer row count", "SELECT COUNT(*) FROM bronze.pms_day_sheets"),
        ("Bronze tenant_id check", "SELECT COUNT(DISTINCT tenant_id) as tenant_count FROM bronze.pms_day_sheets"),
        ("Silver layer row count", "SELECT COUNT(*) FROM bronze_silver.stg_pms_day_sheets"),
        ("Gold layer row count", "SELECT COUNT(*) FROM bronze_gold.daily_production_metrics"),
        ("Tenant access mapping", "SELECT COUNT(*) FROM bronze.tenant_access_mapping"),
    ]

    for label, query in validation_queries:
        try:
            cursor.execute(query)
            result = cursor.fetchone()
            print(f"  ✓ {label}: {result[0] if result else 'N/A'}")
        except Exception as e:
            print(f"  ⚠️  {label}: {str(e)[:80]}")

    print()

    # Close connection
    cursor.close()
    conn.close()

    print("✅ All done! Next steps:")
    print("   1. Run dbt transformations: ./run-dbt.sh full")
    print("   2. Test analytics API endpoints")
    print("   3. Run E2E test suite: ./test-multi-tenant-e2e.sh")
    print()

if __name__ == '__main__':
    execute_migration()
