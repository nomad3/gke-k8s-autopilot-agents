#!/usr/bin/env python3
"""
Seed tenant warehouse configurations
This connects tenants to their Snowflake warehouses
"""

import os
import sys
import asyncio
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv('mcp-server/.env')

# Database connection
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
DB_NAME = os.getenv('POSTGRES_DB', 'mcp')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')

# Snowflake configuration
SNOWFLAKE_CONFIG = {
    'account': os.getenv('SNOWFLAKE_ACCOUNT'),
    'user': os.getenv('SNOWFLAKE_USER'),
    'password': os.getenv('SNOWFLAKE_PASSWORD'),
    'role': os.getenv('SNOWFLAKE_ROLE', 'ACCOUNTADMIN'),
    'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
    'database': os.getenv('SNOWFLAKE_DATABASE', 'DENTAL_ERP_DW'),
    'schema': os.getenv('SNOWFLAKE_SCHEMA', 'BRONZE'),
}

async def seed_warehouses():
    """Seed tenant warehouse configurations"""

    print("=" * 80)
    print("  Seeding Tenant Warehouse Configurations")
    print("=" * 80)
    print()

    # Connect to PostgreSQL
    print(f"→ Connecting to PostgreSQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    try:
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print("✅ Connected to PostgreSQL")
        print()
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to PostgreSQL: {e}")
        sys.exit(1)

    # Get all tenants
    tenants = await conn.fetch("SELECT id, tenant_code, tenant_name FROM tenants WHERE status = 'active'")
    print(f"→ Found {len(tenants)} active tenants:")
    for tenant in tenants:
        print(f"  • {tenant['tenant_code']}: {tenant['tenant_name']}")
    print()

    # Insert warehouse configurations for each tenant
    for tenant in tenants:
        tenant_id = tenant['id']
        tenant_code = tenant['tenant_code']

        print(f"→ Configuring Snowflake warehouse for tenant: {tenant_code}")

        # Check if warehouse already exists
        existing = await conn.fetchrow(
            "SELECT id FROM tenant_warehouses WHERE tenant_id = $1 AND warehouse_type = 'snowflake'",
            tenant_id
        )

        if existing:
            print(f"  ⚠️  Warehouse already configured, updating...")
            await conn.execute(
                """
                UPDATE tenant_warehouses
                SET warehouse_config = $1,
                    is_active = true,
                    is_primary = true,
                    updated_at = NOW()
                WHERE tenant_id = $2 AND warehouse_type = 'snowflake'
                """,
                SNOWFLAKE_CONFIG,
                tenant_id
            )
            print(f"  ✓ Updated Snowflake warehouse for {tenant_code}")
        else:
            await conn.execute(
                """
                INSERT INTO tenant_warehouses (tenant_id, warehouse_type, warehouse_config, is_primary, is_active)
                VALUES ($1, 'snowflake', $2, true, true)
                """,
                tenant_id,
                SNOWFLAKE_CONFIG
            )
            print(f"  ✓ Created Snowflake warehouse for {tenant_code}")

    print()

    # Verify configurations
    print("→ Verifying warehouse configurations...")
    warehouses = await conn.fetch(
        """
        SELECT t.tenant_code, tw.warehouse_type, tw.is_primary, tw.is_active
        FROM tenant_warehouses tw
        JOIN tenants t ON tw.tenant_id = t.id
        ORDER BY t.tenant_code
        """
    )

    print(f"✓ Found {len(warehouses)} warehouse configurations:")
    for wh in warehouses:
        primary = "PRIMARY" if wh['is_primary'] else "BACKUP"
        active = "ACTIVE" if wh['is_active'] else "INACTIVE"
        print(f"  • {wh['tenant_code']}: {wh['warehouse_type']} ({primary}, {active})")

    print()
    print("=" * 80)
    print("✅ Tenant warehouse configurations seeded successfully!")
    print("=" * 80)
    print()

    await conn.close()

if __name__ == '__main__':
    asyncio.run(seed_warehouses())
