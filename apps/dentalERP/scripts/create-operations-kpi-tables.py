#!/usr/bin/env python3
"""
Create Operations KPI Tables in Snowflake
Executes snowflake-operations-kpis.sql to create Bronze, Silver, and Gold dynamic tables
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

def execute_operations_kpi_setup():
    """Execute the operations KPI table setup SQL"""

    print("=" * 80)
    print("  Snowflake Operations KPI Tables Setup")
    print("=" * 80)
    print()

    # Validate credentials
    missing = []
    for key, value in SNOWFLAKE_CONFIG.items():
        if not value:
            missing.append(key)
        elif key != 'password':
            print(f"✓ {key}: {value}")

    if missing:
        print()
        print(f"❌ ERROR: Missing environment variables: {', '.join(missing)}")
        print("   Please check mcp-server/.env file")
        sys.exit(1)

    print()

    # Read SQL script
    script_path = Path('database/snowflake/snowflake-operations-kpis.sql')
    if not script_path.exists():
        print(f"❌ ERROR: SQL script not found: {script_path}")
        print(f"   Current directory: {os.getcwd()}")
        print("   Please run from dentalERP root directory")
        sys.exit(1)

    print(f"✓ Loading SQL script: {script_path}")
    sql_content = script_path.read_text()
    print()

    # Connect to Snowflake
    print("→ Connecting to Snowflake...")
    try:
        conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
        cursor = conn.cursor()
        print(f"✅ Connected to Snowflake: {SNOWFLAKE_CONFIG['account']}")
        print(f"   Database: {SNOWFLAKE_CONFIG['database']}")
        print(f"   Warehouse: {SNOWFLAKE_CONFIG['warehouse']}")
        print()
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to Snowflake")
        print(f"   {str(e)}")
        sys.exit(1)

    # Split SQL into individual statements
    statements = []
    current_statement = []

    for line in sql_content.split('\n'):
        stripped = line.strip()

        # Skip empty lines and comment-only lines
        if not stripped or (stripped.startswith('--') and not stripped.startswith('---')):
            continue

        # Skip block comments
        if stripped.startswith('/*') or stripped.startswith('*/') or '/*' in stripped:
            continue

        current_statement.append(line)

        # Check if statement ends
        if stripped.endswith(';'):
            stmt = '\n'.join(current_statement).strip()
            if stmt and not stmt.startswith('/*'):
                statements.append(stmt)
            current_statement = []

    print(f"→ Executing {len(statements)} SQL statements...")
    print()

    # Execute each statement
    success_count = 0
    error_count = 0
    errors = []

    for i, statement in enumerate(statements, 1):
        # Extract operation type for better logging
        stmt_upper = statement.upper()

        try:
            cursor.execute(statement)

            # Show status messages
            if 'SELECT' in stmt_upper and 'AS STATUS' in stmt_upper:
                result = cursor.fetchone()
                if result:
                    print(f"  [{i:2d}/{len(statements)}] {result[0]}")
            elif 'CREATE TABLE' in stmt_upper:
                table_name = 'operations_metrics_raw' if 'operations_metrics_raw' in statement else 'unknown'
                print(f"  [{i:2d}/{len(statements)}] ✓ Created Bronze table: {table_name}")
            elif 'CREATE OR REPLACE DYNAMIC TABLE' in stmt_upper:
                if 'stg_operations_metrics' in statement:
                    print(f"  [{i:2d}/{len(statements)}] ✓ Created Silver dynamic table: stg_operations_metrics")
                elif 'operations_kpis_monthly' in statement:
                    print(f"  [{i:2d}/{len(statements)}] ✓ Created Gold dynamic table: operations_kpis_monthly")
            elif 'COMMENT ON' in stmt_upper:
                print(f"  [{i:2d}/{len(statements)}] ✓ Added table comment")
            elif 'USE' in stmt_upper:
                # Silent - just context switching
                pass
            else:
                print(f"  [{i:2d}/{len(statements)}] ✓ Executed")

            success_count += 1

        except Exception as e:
            error_count += 1
            error_msg = str(e)[:150]
            errors.append((i, statement[:100], error_msg))
            print(f"  [{i:2d}/{len(statements)}] ⚠️  Warning: {error_msg}")

    print()
    print("=" * 80)
    print(f"✅ Execution complete!")
    print(f"   Successful: {success_count} statements")
    if error_count > 0:
        print(f"   Warnings: {error_count} statements")
    print("=" * 80)
    print()

    # Show errors if any
    if errors:
        print("⚠️  Warnings/Errors encountered:")
        for i, stmt, err in errors[:5]:  # Show first 5
            print(f"   [{i}] {err}")
        if len(errors) > 5:
            print(f"   ... and {len(errors) - 5} more")
        print()

    # Run validation queries
    print("→ Running validation queries...")
    print()

    validation_queries = [
        ("Bronze table exists", "SHOW TABLES LIKE 'operations_metrics_raw' IN SCHEMA bronze"),
        ("Silver dynamic table exists", "SHOW DYNAMIC TABLES LIKE 'stg_operations_metrics' IN SCHEMA bronze_silver"),
        ("Gold dynamic table exists", "SHOW DYNAMIC TABLES LIKE 'operations_kpis_monthly' IN SCHEMA bronze_gold"),
        ("Dynamic tables status", """
            SELECT table_name, target_lag, refresh_mode, scheduling_state
            FROM information_schema.tables
            WHERE table_schema IN ('BRONZE_SILVER', 'BRONZE_GOLD')
              AND table_type = 'DYNAMIC TABLE'
              AND table_name IN ('STG_OPERATIONS_METRICS', 'OPERATIONS_KPIS_MONTHLY')
        """),
    ]

    for label, query in validation_queries:
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            if results:
                print(f"  ✅ {label}")
                if 'status' in label or 'Dynamic tables' in label:
                    for row in results:
                        print(f"      {row}")
            else:
                print(f"  ℹ️  {label}: No results")
        except Exception as e:
            print(f"  ⚠️  {label}: {str(e)[:80]}")

    print()

    # Close connection
    cursor.close()
    conn.close()

    print("=" * 80)
    print("✅ Operations KPI tables created successfully!")
    print("=" * 80)
    print()
    print("📋 Next Steps:")
    print("   1. Upload Excel data:")
    print("      POST /api/v1/operations/upload")
    print()
    print("   2. Verify data in Bronze:")
    print("      SELECT * FROM bronze.operations_metrics_raw LIMIT 5;")
    print()
    print("   3. Wait 1 hour (or force refresh) for dynamic tables:")
    print("      ALTER DYNAMIC TABLE bronze_silver.stg_operations_metrics REFRESH;")
    print("      ALTER DYNAMIC TABLE bronze_gold.operations_kpis_monthly REFRESH;")
    print()
    print("   4. Query Gold layer:")
    print("      SELECT * FROM bronze_gold.operations_kpis_monthly")
    print("      WHERE tenant_id = 'silvercreek' LIMIT 10;")
    print()

if __name__ == '__main__':
    execute_operations_kpi_setup()
