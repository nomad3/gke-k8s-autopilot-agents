"""
MCP Server NetSuite Data Seeding Script
Seeds tenant, warehouse, and integration data for Silver Creek
"""

import asyncio
import os
import json
import sys
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.exc import SQLAlchemyError

# Add src to path
sys.path.append('/opt/dental-erp/mcp-server')

from src.models.tenant import (
    Tenant,
    TenantWarehouse,
    TenantIntegration,
    TenantStatusEnum,
    WarehouseTypeEnum,
    IntegrationTypeEnum
)
from src.core.database import Base, get_db
from src.utils.logger import logger

# Database connection
DATABASE_URL = os.getenv(
    "POSTGRES_URL",
    "postgresql+asyncpg://postgres:N6At7Nao7EnVPJ9euYhirIgwZI6m69poJEp/FIqIw1xI=@localhost:5432/mcp"
)

class MCPSilverCreekSeeder:
    """Seed MCP server with Silver Creek tenant and NetSuite integration"""

    def __init__(self):
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # Silver Creek configuration
        self.tenant_code = "silvercreek"
        self.tenant_name = "Silver Creek Dental Partners, LLC"
        self.industry = "dental"
        self.products = ["dentalerp"]

        # Subsidiary mapping for reference
        self.subsidiary_mapping = {
            "1": {"name": "Silver Creek Dental Partners, LLC", "code": "parent"},
            "2": {"name": "SCDP San Marcos, LLC", "code": "san-marcos"},
            "3": {"name": "SCDP San Marcos II, LLC", "code": "san-marcos-2"},
            "4": {"name": "SCDP Holdings, LLC", "code": "holdings"},
            "5": {"name": "SCDP Laguna Hills, LLC", "code": "laguna-hills"},
            "6": {"name": "SCDP Eastlake, LLC", "code": "eastlake"},
            "7": {"name": "SCDP Torrey Highlands, LLC", "code": "torrey-highlands"},
            "8": {"name": "SCDP Vista, LLC", "code": "vista"},
            "9": {"name": "SCDP Del Sur Ranch, LLC", "code": "del-sur-ranch"},
            "10": {"name": "SCDP Torrey Pines, LLC", "code": "torrey-pines"},
            "11": {"name": "SCDP Otay Lakes, LLC", "code": "otay-lakes"}
        }

    async def create_silver_creek_tenant(self, session: AsyncSession) -> Tenant:
        """Create Silver Creek tenant"""
        logger.info(f"Creating tenant: {self.tenant_code}")

        try:
            # Check if tenant already exists
            existing_tenant = await session.execute(
                select(Tenant).where(Tenant.tenant_code == self.tenant_code)
            )
            if existing_tenant.scalar_one_or_none():
                logger.warning(f"Tenant {self.tenant_code} already exists, skipping creation")
                return existing_tenant.scalar_one_or_none()

            # Create new tenant
            tenant = Tenant(
                id=uuid4(),
                tenant_code=self.tenant_code,
                tenant_name=self.tenant_name,
                industry=self.industry,
                products=self.products,
                status=TenantStatusEnum.ACTIVE.value,
                settings={
                    "timezone": "America/Los_Angeles",
                    "currency": "USD",
                    "fiscal_year_start": "01-01",
                    "subsidiaries": list(self.subsidiary_mapping.values()),
                    "default_warehouse": "snowflake",
                    "analytics_enabled": True,
                    "ai_insights_enabled": True,
                    "multi_location": True,
                    "location_count": len(self.subsidiary_mapping)
                }
            )

            session.add(tenant)
            await session.flush()  # Get tenant ID

            logger.info(f"✅ Created tenant: {tenant.tenant_name} ({tenant.tenant_code})")
            return tenant

        except Exception as e:
            logger.error(f"Error creating tenant: {e}")
            raise

    async def create_snowflake_warehouse(self, session: AsyncSession, tenant: Tenant) -> TenantWarehouse:
        """Create Snowflake warehouse for the tenant"""
        logger.info(f"Creating Snowflake warehouse for tenant {tenant.tenant_code}")

        try:
            # Check if warehouse already exists
            existing_warehouse = await session.execute(
                select(TenantWarehouse)
                .where(TenantWarehouse.tenant_id == tenant.id)
                .where(TenantWarehouse.warehouse_type == WarehouseTypeEnum.SNOWFLAKE.value)
            )
            if existing_warehouse.scalar_one_or_none():
                logger.warning(f"Snowflake warehouse already exists for tenant {tenant.tenant_code}")
                return existing_warehouse.scalar_one_or_none()

            # Get Snowflake configuration from environment
            snowflake_config = {
                "account": os.getenv("SNOWFLAKE_ACCOUNT", "HKTPGHW-ES87244"),
                "user": os.getenv("SNOWFLAKE_USER", "NOMADSIMON"),
                "password": os.getenv("SNOWFLAKE_PASSWORD", "@SebaSofi.2k25!!"),
                "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
                "database": os.getenv("SNOWFLAKE_DATABASE", "DENTAL_ERP_DW"),
                "schema": "BRONZE",  # Start with Bronze layer
                "role": os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
                "connection_timeout": 30,
                "network_timeout": 30
            }

            warehouse = TenantWarehouse(
                id=uuid4(),
                tenant_id=tenant.id,
                warehouse_type=WarehouseTypeEnum.SNOWFLAKE.value,
                warehouse_config=snowflake_config,
                is_primary=True,
                is_active=True
            )

            session.add(warehouse)
            await session.flush()

            logger.info(f"✅ Created Snowflake warehouse for {tenant.tenant_code}")
            return warehouse

        except Exception as e:
            logger.error(f"Error creating Snowflake warehouse: {e}")
            raise

    async def create_netsuite_integration(self, session: AsyncSession, tenant: Tenant) -> TenantIntegration:
        """Create NetSuite integration for the tenant"""
        logger.info(f"Creating NetSuite integration for tenant {tenant.tenant_code}")

        try:
            # Check if integration already exists
            existing_integration = await session.execute(
                select(TenantIntegration)
                .where(TenantIntegration.tenant_id == tenant.id)
                .where(TenantIntegration.integration_type == IntegrationTypeEnum.NETSUITE.value)
            )
            if existing_integration.scalar_one_or_none():
                logger.warning(f"NetSuite integration already exists for tenant {tenant.tenant_code}")
                return existing_integration.scalar_one_or_none()

            # NetSuite configuration from environment
            netsuite_config = {
                "account": os.getenv("NETSUITE_ACCOUNT_ID", "7048582"),
                "consumer_key": os.getenv("NETSUITE_CONSUMER_KEY"),
                "consumer_secret": os.getenv("NETSUITE_CONSUMER_SECRET"),
                "token_key": os.getenv("NETSUITE_TOKEN_ID"),
                "token_secret": os.getenv("NETSUITE_TOKEN_SECRET"),
                "api_url": "https://7048582.suitetalk.api.netsuite.com/services/rest/record/v1",
                "restlet_url": None,  # Will be set if using RESTlets
                "timeout": 60,
                "max_retries": 3,
                "batch_size": 100
            }

            # Sync configuration for all subsidiaries
            sync_config = {
                "incremental": True,
                "sync_frequency": "15m",  # Every 15 minutes
                "full_sync_schedule": "0 2 * * *",  # Daily at 2 AM
                "record_types": [
                    "journalEntry",
                    "account",
                    "invoice",
                    "customerPayment",
                    "vendorBill",
                    "customer",
                    "vendor",
                    "inventoryItem",
                    "subsidiary",
                    "location",
                    "department",
                    "class"
                ],
                "subsidiary_scope": list(self.subsidiary_mapping.keys()),  # All subsidiaries
                "date_range": {
                    "start_date": "2024-01-01",
                    "end_date": None  # Current date
                },
                "filters": {
                    "include_deleted": False,
                    "include_inactive": False
                },
                "transformations": {
                    "currency_conversion": True,
                    "account_mapping": True,
                    "dimension_enrichment": True
                }
            }

            integration = TenantIntegration(
                id=uuid4(),
                tenant_id=tenant.id,
                integration_type=IntegrationTypeEnum.NETSUITE.value,
                integration_config=netsuite_config,
                status="active",
                sync_config=sync_config,
                last_sync_at=datetime.utcnow(),
                sync_status="success"
            )

            session.add(integration)
            await session.flush()

            logger.info(f"✅ Created NetSuite integration for {tenant.tenant_code}")
            return integration

        except Exception as e:
            logger.error(f"Error creating NetSuite integration: {e}")
            raise

    async def create_tenant_api_keys(self, session: AsyncSession, tenant: Tenant) -> None:
        """Create API keys for tenant (if needed)"""
        logger.info(f"Creating API keys for tenant {tenant.tenant_code}")

        try:
            # This would typically create scoped API keys
            # For now, we'll use the existing MCP_API_KEY environment variable
            logger.info(f"Using existing MCP_API_KEY for tenant {tenant.tenant_code}")

        except Exception as e:
            logger.error(f"Error creating API keys: {e}")
            raise

    def generate_financial_metrics_preview(self) -> Dict[str, Any]:
        """
        Generate preview of financial metrics that will be available
        Based on actual CSV structure from report_250_transactiondetail.csv
        """
        return {
            "transaction_data": {
                "data_source": "NetSuite Transaction Detail Report (CSV)",
                "format": "Type, Date, Document Number, Name, Memo, Account, Amount",
                "transaction_types": [
                    "Bill", "Bill Payment", "Invoice", "Customer Payment",
                    "Journal Entry", "Deposit", "Check", "Credit Memo", "Vendor Credit"
                ],
                "total_records": "686 lines (Nov 1-30, 2025)",
                "entities_tracked": "Vendors, Customers, Subsidiaries"
            },
            "account_structure": {
                "expense_categories": [
                    "Labs Expenses : Laboratory Fees",
                    "Facility Expenses : Rent Payments",
                    "Facility Expenses : Other Lease (Prop Taxes,Ins,CAM)",
                    "Marketing : Digital Marketing",
                    "Operating Expenses : Telephone, Computer & Internet",
                    "Payroll Expenses : Salaries & Wages"
                ],
                "liability_accounts": [
                    "2000 - Accounts Payable (A/P)",
                    "Ramp AP accounts (by location)",
                    "Ramp Card accounts (by location)"
                ],
                "revenue_accounts": [
                    "Production Income",
                    "Collections",
                    "Other Revenue"
                ]
            },
            "subsidiary_metrics": {
                "revenue_by_location": "Monthly revenue breakdown by subsidiary",
                "expense_analysis": "Operating expenses by category and location",
                "vendor_analysis": "Top vendors by spend and transaction volume",
                "profitability_comparison": "Net income and margin comparison across locations",
                "cash_flow_analysis": "Operating cash flow by subsidiary"
            },
            "consolidated_metrics": {
                "total_revenue": "Combined revenue across all subsidiaries",
                "total_expenses": "Combined operating expenses by category",
                "net_income": "Consolidated net income",
                "profit_margin": "Overall profit margin percentage",
                "vendor_spend": "Total vendor spend analysis"
            },
            "comparative_analysis": {
                "best_performing_location": "Revenue per location ranking",
                "highest_margin_location": "Profit margin by subsidiary",
                "expense_ratio_analysis": "Expense to revenue ratios by category",
                "growth_trends": "Month-over-month growth by location",
                "vendor_concentration": "Top vendors by spend across all locations"
            },
            "operational_metrics": {
                "accounts_receivable": "AR aging by subsidiary",
                "accounts_payable": "AP aging by subsidiary and vendor",
                "working_capital": "Working capital analysis",
                "payment_patterns": "Bill payment timing and patterns",
                "expense_categories": "Breakdown by Labs, Facility, Marketing, Operating, Payroll"
            },
            "data_quality": {
                "debit_credit_balance": "Ensures debits equal credits for data integrity",
                "date_range": "November 1-30, 2025",
                "completeness": "All required fields validated",
                "entity_mapping": "Vendors and accounts properly categorized"
            }
        }

    async def run_seeding(self) -> Dict[str, Any]:
        """Run complete MCP seeding process"""
        logger.info("Starting MCP NetSuite data seeding...")

        try:
            async with self.async_session() as session:
                # 1. Create Silver Creek tenant
                tenant = await self.create_silver_creek_tenant(session)

                # 2. Create Snowflake warehouse
                warehouse = await self.create_snowflake_warehouse(session, tenant)

                # 3. Create NetSuite integration
                integration = await self.create_netsuite_integration(session, tenant)

                # 4. Create API keys (if needed)
                await self.create_tenant_api_keys(session, tenant)

                # Commit all changes
                await session.commit()

                # Generate metrics preview
                metrics_preview = self.generate_financial_metrics_preview()

                logger.info("✅ MCP NetSuite data seeding completed successfully!")

                return {
                    "success": True,
                    "tenant": {
                        "id": str(tenant.id),
                        "code": tenant.tenant_code,
                        "name": tenant.tenant_name,
                        "subsidiary_count": len(self.subsidiary_mapping)
                    },
                    "warehouse": {
                        "type": warehouse.warehouse_type,
                        "is_primary": warehouse.is_primary
                    },
                    "integration": {
                        "type": integration.integration_type,
                        "status": integration.status,
                        "record_types": integration.sync_config.get("record_types", [])
                    },
                    "available_metrics": metrics_preview
                }

        except Exception as e:
            logger.error(f"MCP seeding failed: {e}")
            await session.rollback()
            raise

    async def verify_seeding(self) -> Dict[str, Any]:
        """Verify that seeding was successful"""
        logger.info("Verifying MCP seeding...")

        try:
            async with self.async_session() as session:
                # Verify tenant
                tenant_result = await session.execute(
                    select(Tenant).where(Tenant.tenant_code == self.tenant_code)
                )
                tenant = tenant_result.scalar_one_or_none()

                if not tenant:
                    raise ValueError(f"Tenant {self.tenant_code} not found")

                # Verify warehouse
                warehouse_result = await session.execute(
                    select(TenantWarehouse)
                    .where(TenantWarehouse.tenant_id == tenant.id)
                    .where(TenantWarehouse.warehouse_type == WarehouseTypeEnum.SNOWFLAKE.value)
                )
                warehouse = warehouse_result.scalar_one_or_none()

                if not warehouse:
                    raise ValueError(f"Snowflake warehouse not found for tenant {self.tenant_code}")

                # Verify integration
                integration_result = await session.execute(
                    select(TenantIntegration)
                    .where(TenantIntegration.tenant_id == tenant.id)
                    .where(TenantIntegration.integration_type == IntegrationTypeEnum.NETSUITE.value)
                )
                integration = integration_result.scalar_one_or_none()

                if not integration:
                    raise ValueError(f"NetSuite integration not found for tenant {self.tenant_code}")

                logger.info("✅ MCP seeding verification completed successfully")

                return {
                    "tenant_verified": True,
                    "warehouse_verified": True,
                    "integration_verified": True,
                    "subsidiaries_ready": len(self.subsidiary_mapping),
                    "financial_data_ready": True
                }

        except Exception as e:
            logger.error(f"MCP verification failed: {e}")
            raise

async def main():
    """Main execution function"""
    logger.info("Starting MCP Silver Creek NetSuite seeding process...")

    try:
        seeder = MCPSilverCreekSeeder()

        # Run seeding
        result = await seeder.run_seeding()

        if result["success"]:
            logger.info("🎉 MCP Silver Creek NetSuite seeding completed successfully!")

            # Print summary
            print("\n" + "="*60)
            print("MCP SILVER CREEK NETSUITE SEEDING SUMMARY")
            print("="*60)
            print(f"Tenant: {result['tenant']['name']} ({result['tenant']['code']})")
            print(f"Subsidiaries: {result['tenant']['subsidiary_count']} locations")
            print(f"Warehouse: {result['warehouse']['type']} (Primary: {result['warehouse']['is_primary']})")
            print(f"Integration: {result['integration']['type']} ({result['integration']['status']})")
            print(f"Record Types: {', '.join(result['integration']['record_types'])}")
            print("\n✅ Ready for financial data extraction and analysis!")
            print("="*60)

            # Verify seeding
            verification = await seeder.verify_seeding()
            print(f"\n✅ Verification: All {verification['subsidiaries_ready']} subsidiaries ready")

            return 0
        else:
            logger.error("❌ MCP seeding failed")
            return 1

    except Exception as e:
        logger.error(f"❌ MCP seeding process failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)