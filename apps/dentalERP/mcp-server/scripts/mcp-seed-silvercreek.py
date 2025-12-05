"""
MCP Server Seed Script - Silver Creek Tenant Configuration
Seeds tenant, warehouse, and integration data using raw SQL
"""

import asyncio
import os
import json
from uuid import uuid4
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Database connection - use asyncpg
DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql+asyncpg://postgres:N6At7Nao7EnVPJ9euYhirIgwZI6m69poJEp%2FIqIw1xI%3D@postgres:5432/mcp"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed_silvercreek():
    print("🌱 Seeding Silver Creek tenant configuration...")

    async with async_session() as session:
        try:
            # 1. Create Silver Creek tenant
            tenant_id = str(uuid4())
            tenant_data = {
                "id": tenant_id,
                "tenant_code": "silvercreek",
                "tenant_name": "Silver Creek Dental Partners, LLC",
                "industry": "dental",
                "products": json.dumps(["dentalerp", "analytics"]),
                "status": "active",
                "settings": json.dumps({
                    "timezone": "America/Los_Angeles",
                    "currency": "USD",
                    "fiscal_year_start": "01-01"
                })
            }

            insert_tenant = text("""
                INSERT INTO tenants (id, tenant_code, tenant_name, industry, products, status, settings)
                VALUES (:id, :tenant_code, :tenant_name, :industry, :products, :status, :settings)
            """)
            await session.execute(insert_tenant, tenant_data)

            print(f"✅ Created tenant: {tenant_data['tenant_name']} ({tenant_data['tenant_code']})")

            # 2. Add Snowflake warehouse
            warehouse_id = str(uuid4())
            snowflake_config = {
                "account": os.getenv("SNOWFLAKE_ACCOUNT"),
                "user": os.getenv("SNOWFLAKE_USER"),
                "password": os.getenv("SNOWFLAKE_PASSWORD"),
                "warehouse": "COMPUTE_WH",
                "database": "DENTAL_ERP_DW",
                "schema": "BRONZE",
                "role": "ACCOUNTADMIN"
            }

            insert_warehouse = text("""
                INSERT INTO tenant_warehouses (id, tenant_id, warehouse_type, warehouse_config, is_primary, is_active)
                VALUES (:id, :tenant_id, :warehouse_type, :warehouse_config, :is_primary, :is_active)
            """)
            await session.execute(insert_warehouse, {
                "id": warehouse_id,
                "tenant_id": tenant_id,
                "warehouse_type": "snowflake",
                "warehouse_config": json.dumps(snowflake_config),
                "is_primary": True,
                "is_active": True
            })

            print(f"✅ Added Snowflake warehouse for silvercreek")

            # 3. Add NetSuite integration
            integration_id = str(uuid4())
            netsuite_config = {
                "account": os.getenv("NETSUITE_ACCOUNT_ID", "7048582"),
                "consumer_key": os.getenv("NETSUITE_CONSUMER_KEY"),
                "consumer_secret": os.getenv("NETSUITE_CONSUMER_SECRET"),
                "token_key": os.getenv("NETSUITE_TOKEN_ID"),
                "token_secret": os.getenv("NETSUITE_TOKEN_SECRET"),
                "api_url": "https://7048582.suitetalk.api.netsuite.com/services/rest/record/v1"
            }

            sync_config = {
                "incremental": True,
                "sync_frequency": "15m",
                "record_types": [
                    "journalEntry",
                    "account",
                    "invoice",
                    "customerPayment",
                    "vendorBill",
                    "customer",
                    "vendor",
                    "inventoryItem",
                    "subsidiary"
                ]
            }

            insert_integration = text("""
                INSERT INTO tenant_integrations (id, tenant_id, integration_type, integration_config, is_active, sync_status)
                VALUES (:id, :tenant_id, :integration_type, :integration_config, :is_active, :sync_status)
            """)
            await session.execute(insert_integration, {
                "id": integration_id,
                "tenant_id": tenant_id,
                "integration_type": "netsuite",
                "integration_config": json.dumps(netsuite_config),
                "is_active": True,
                "sync_status": "ready"
            })

            print(f"✅ Added NetSuite integration for silvercreek")

            # Commit all changes
            await session.commit()

            print(f"\n✨ Silver Creek tenant setup complete!")
            print(f"   Tenant ID: {tenant_id}")
            print(f"   Tenant Code: silvercreek")
            print(f"   Warehouse: Snowflake (primary)")
            print(f"   Integrations: NetSuite")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error seeding tenant: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    asyncio.run(seed_silvercreek())
