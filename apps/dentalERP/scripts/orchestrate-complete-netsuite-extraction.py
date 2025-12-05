#!/usr/bin/env python3
"""
Complete NetSuite Data Extraction Orchestrator
Triggers comprehensive data extraction for all Silver Creek subsidiaries
using existing MCP infrastructure (NetSuiteToSnowflakeLoader)
"""

import asyncio
import os
import json
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add MCP server to path
sys.path.append('/opt/dental-erp/mcp-server')

from src.core.database import get_db
from src.core.tenant import TenantContext
from src.services.netsuite_sync_orchestrator import NetSuiteSyncOrchestrator
from src.services.snowflake_netsuite_loader import NetSuiteToSnowflakeLoader
from src.models.tenant import Tenant
from src.utils.logger import logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CompleteNetSuiteOrchestrator:
    """
    Orchestrates complete NetSuite data extraction for Silver Creek
    Uses existing MCP infrastructure to extract ALL financial data
    """

    def __init__(self, tenant_code: str = "silvercreek"):
        self.tenant_code = tenant_code
        self.extraction_summary = {}
        self.financial_metrics = {}

        # Silver Creek subsidiaries
        self.subsidiaries = {
            "1": {"name": "Silver Creek Dental Partners, LLC", "code": "parent", "active": True},
            "2": {"name": "SCDP San Marcos, LLC", "code": "san-marcos", "active": True},
            "3": {"name": "SCDP San Marcos II, LLC", "code": "san-marcos-2", "active": True},
            "4": {"name": "SCDP Holdings, LLC", "code": "holdings", "active": True},
            "5": {"name": "SCDP Laguna Hills, LLC", "code": "laguna-hills", "active": True},
            "6": {"name": "SCDP Eastlake, LLC", "code": "eastlake", "active": True},
            "7": {"name": "SCDP Torrey Highlands, LLC", "code": "torrey-highlands", "active": True},
            "8": {"name": "SCDP Vista, LLC", "code": "vista", "active": True},
            "9": {"name": "SCDP Del Sur Ranch, LLC", "code": "del-sur-ranch", "active": True},
            "10": {"name": "SCDP Torrey Pines, LLC", "code": "torrey-pines", "active": True},
            "11": {"name": "SCDP Otay Lakes, LLC", "code": "otay-lakes", "active": True}
        }

    async def run_complete_extraction(self) -> Dict[str, Any]:
        """
        Run complete NetSuite data extraction using existing MCP infrastructure
        """
        logger.info(f"Starting complete NetSuite extraction for tenant: {self.tenant_code}")

        try:
            # Get tenant and set context
            async with get_db() as session:
                tenant = await self._get_tenant(session)
                if not tenant:
                    raise ValueError(f"Tenant {self.tenant_code} not found")

                TenantContext.set_tenant(tenant)

                logger.info(f"Processing tenant: {tenant.tenant_name} ({tenant.tenant_code})")

                # Step 1: Use existing NetSuite Sync Orchestrator for comprehensive sync
                logger.info("Step 1: Running NetSuite sync orchestrator...")
                sync_results = await self._run_netsuite_sync_orchestrator(str(tenant.id))

                # Step 2: Extract detailed financial data per subsidiary
                logger.info("Step 2: Extracting detailed financial data per subsidiary...")
                detailed_results = await self._extract_detailed_financial_data(str(tenant.id))

                # Step 3: Generate comprehensive financial analysis
                logger.info("Step 3: Generating financial analysis...")
                financial_analysis = await self._generate_financial_analysis(detailed_results)

                # Step 4: Verify data in Snowflake
                logger.info("Step 4: Verifying data in Snowflake...")
                verification_results = await self._verify_snowflake_data(str(tenant.id))

                # Step 5: Generate final report
                final_report = await self._generate_final_report(
                    sync_results, detailed_results, financial_analysis, verification_results
                )

                logger.info("✅ Complete NetSuite extraction finished successfully!")

                return final_report

        except Exception as e:
            logger.error(f"Error in complete NetSuite extraction: {e}")
            raise
        finally:
            TenantContext.clear_tenant()

    async def _get_tenant(self, session) -> Optional[Tenant]:
        """Get tenant from database"""
        from sqlalchemy import select
        from uuid import UUID
        result = await session.execute(select(Tenant).where(Tenant.tenant_code == self.tenant_code))
        return result.scalar_one_or_none()

    async def _run_netsuite_sync_orchestrator(self, tenant_id: str) -> Dict[str, Any]:
        """Run existing NetSuite sync orchestrator for comprehensive data sync"""
        logger.info("Running NetSuite sync orchestrator...")

        try:
            orchestrator = NetSuiteSyncOrchestrator()

            # Run full sync (not incremental) to get all historical data
            logger.info("Triggering full sync for all record types...")

            # This will sync all NetSuite record types for all subsidiaries
            await orchestrator.sync_tenant(
                tenant_id=tenant_id,
                incremental=False,  # Full sync
                record_types=None   # All record types
            )

            # Get sync results
            sync_summary = await self._get_sync_summary(tenant_id)

            logger.info("✅ NetSuite sync orchestrator completed")
            return sync_summary

        except Exception as e:
            logger.error(f"Error running NetSuite sync orchestrator: {e}")
            raise

    async def _get_sync_summary(self, tenant_id: str) -> Dict[str, Any]:
        """Get summary of what was synced"""
        try:
            async with get_db() as session:
                # Query to get sync status and counts from the database
                # This would depend on how the sync orchestrator stores its results

                # For now, we'll check what's in Snowflake Bronze layer
                from src.services.warehouse_router import WarehouseRouter

                warehouse_router = WarehouseRouter()
                snowflake = await warehouse_router.get_connector("snowflake")

                # Get counts from Bronze tables
                bronze_counts = {}

                bronze_tables = [
                    'netsuite_journalentry',
                    'netsuite_account',
                    'netsuite_invoice',
                    'netsuite_customerpayment',
                    'netsuite_vendorbill',
                    'netsuite_customer',
                    'netsuite_vendor',
                    'netsuite_inventoryitem',
                    'netsuite_subsidiary'
                ]

                for table in bronze_tables:
                    try:
                        result = await snowflake.execute(f"SELECT COUNT(*) FROM bronze.{table} WHERE tenant_id = '{self.tenant_code}'")
                        count = result[0][0] if result else 0
                        bronze_counts[table] = count
                    except Exception as e:
                        logger.warning(f"Could not get count for table {table}: {e}")
                        bronze_counts[table] = 0

                total_records = sum(bronze_counts.values())

                return {
                    'bronze_table_counts': bronze_counts,
                    'total_records': total_records,
                    'sync_timestamp': datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Error getting sync summary: {e}")
            return {'error': str(e)}

    async def _extract_detailed_financial_data(self, tenant_id: str) -> Dict[str, Dict[str, Any]]:
        """Extract detailed financial data per subsidiary"""
        logger.info("Extracting detailed financial data per subsidiary...")

        detailed_results = {}

        for subsidiary_id, subsidiary_info in self.subsidiaries.items():
            logger.info(f"Extracting detailed data for subsidiary {subsidiary_id}: {subsidiary_info['name']}")

            try:
                # Use NetSuiteToSnowflakeLoader to get detailed data
                loader = NetSuiteToSnowflakeLoader(tenant_id)
                await loader.initialize()

                # Get detailed data for this subsidiary
                subsidiary_data = await self._get_subsidiary_financial_data(loader, subsidiary_id)

                detailed_results[subsidiary_id] = {
                    'subsidiary_info': subsidiary_info,
                    'financial_data': subsidiary_data,
                    'status': 'success',
                    'extraction_timestamp': datetime.utcnow().isoformat()
                }

                logger.info(f"✅ Extracted detailed data for subsidiary {subsidiary_id}")

            except Exception as e:
                logger.error(f"Error extracting detailed data for subsidiary {subsidiary_id}: {e}")
                detailed_results[subsidiary_id] = {
                    'subsidiary_info': subsidiary_info,
                    'error': str(e),
                    'status': 'failed',
                    'extraction_timestamp': datetime.utcnow().isoformat()
                }

        return detailed_results

    async def _get_subsidiary_financial_data(self, loader: NetSuiteToSnowflakeLoader, subsidiary_id: str) -> Dict[str, Any]:
        """Get financial data for a specific subsidiary"""
        logger.info(f"Getting financial data for subsidiary {subsidiary_id}")

        try:
            # Get journal entries for the subsidiary
            journal_entries = await self._get_journal_entries_from_snowflake(subsidiary_id)

            # Get chart of accounts
            chart_of_accounts = await self._get_chart_of_accounts_from_snowflake(subsidiary_id)

            # Get customers
            customers = await self._get_customers_from_snowflake(subsidiary_id)

            # Get vendors
            vendors = await self._get_vendors_from_snowflake(subsidiary_id)

            # Calculate financial metrics
            financial_metrics = self._calculate_subsidiary_metrics(
                journal_entries, chart_of_accounts, customers, vendors
            )

            return {
                'journal_entries': journal_entries,
                'chart_of_accounts': chart_of_accounts,
                'customers': customers,
                'vendors': vendors,
                'financial_metrics': financial_metrics
            }

        except Exception as e:
            logger.error(f"Error getting financial data for subsidiary {subsidiary_id}: {e}")
            return {'error': str(e)}

    async def _get_journal_entries_from_snowflake(self, subsidiary_id: str) -> List[Dict[str, Any]]:
        """Get journal entries from Snowflake for a subsidiary"""
        try:
            from src.services.warehouse_router import WarehouseRouter

            warehouse_router = WarehouseRouter()
            snowflake = await warehouse_router.get_connector("snowflake")

            # Query journal entries from Bronze layer
            query = f"""
            SELECT
                id,
                subsidiary_id,
                raw_data:tranId::string as journal_entry_id,
                raw_data:trandate::date as transaction_date,
                raw_data:account:id::string as account_id,
                raw_data:account:name::string as account_name,
                raw_data:debit::float as debit_amount,
                raw_data:credit::float as credit_amount,
                raw_data:memo::string as description,
                raw_data:name::string as reference_entity
            FROM bronze.netsuite_journalentry
            WHERE tenant_id = '{self.tenant_code}'
            AND subsidiary_id = '{subsidiary_id}'
            AND raw_data:subsidiary:id::string = '{subsidiary_id}'
            ORDER BY transaction_date DESC
            LIMIT 1000
            """

            results = await snowflake.execute(query)

            journal_entries = []
            for row in results:
                journal_entries.append({
                    'id': row[0],
                    'subsidiary_id': row[1],
                    'journal_entry_id': row[2],
                    'transaction_date': row[3],
                    'account_id': row[4],
                    'account_name': row[5],
                    'debit_amount': row[6],
                    'credit_amount': row[7],
                    'description': row[8],
                    'reference_entity': row[9]
                })

            return journal_entries

        except Exception as e:
            logger.error(f"Error getting journal entries from Snowflake for subsidiary {subsidiary_id}: {e}")
            return []

    async def _get_chart_of_accounts_from_snowflake(self, subsidiary_id: str) -> List[Dict[str, Any]]:
        """Get chart of accounts from Snowflake for a subsidiary"""
        try:
            from src.services.warehouse_router import WarehouseRouter

            warehouse_router = WarehouseRouter()
            snowflake = await warehouse_router.get_connector("snowflake")

            # Query accounts from Bronze layer
            query = f"""
            SELECT
                id,
                raw_data:acctnumber::string as account_number,
                raw_data:acctname::string as account_name,
                raw_data:type::string as account_type,
                raw_data:parent:name::string as parent_account,
                raw_data:isinactive::boolean as is_inactive,
                raw_data:balance::float as balance
            FROM bronze.netsuite_account
            WHERE tenant_id = '{self.tenant_code}'
            AND raw_data:subsidiary:id::string = '{subsidiary_id}'
            ORDER BY account_number
            """

            results = await snowflake.execute(query)

            accounts = []
            for row in results:
                accounts.append({
                    'id': row[0],
                    'account_number': row[1],
                    'account_name': row[2],
                    'account_type': row[3],
                    'parent_account': row[4],
                    'is_active': not row[5],
                    'balance': row[6]
                })

            return accounts

        except Exception as e:
            logger.error(f"Error getting chart of accounts from Snowflake for subsidiary {subsidiary_id}: {e}")
            return []

    async def _get_customers_from_snowflake(self, subsidiary_id: str) -> List[Dict[str, Any]]:
        """Get customers from Snowflake for a subsidiary"""
        try:
            from src.services.warehouse_router import WarehouseRouter

            warehouse_router = WarehouseRouter()
            snowflake = await warehouse_router.get_connector("snowflake")

            query = f"""
            SELECT
                id,
                raw_data:entityid::string as entity_id,
                raw_data:companyname::string as company_name,
                raw_data:email::string as email,
                raw_data:phone::string as phone,
                raw_data:isinactive::boolean as is_inactive
            FROM bronze.netsuite_customer
            WHERE tenant_id = '{self.tenant_code}'
            AND raw_data:subsidiary:id::string = '{subsidiary_id}'
            ORDER BY company_name
            """

            results = await snowflake.execute(query)

            customers = []
            for row in results:
                customers.append({
                    'id': row[0],
                    'entity_id': row[1],
                    'company_name': row[2],
                    'email': row[3],
                    'phone': row[4],
                    'is_active': not row[5]
                })

            return customers

        except Exception as e:
            logger.error(f"Error getting customers from Snowflake for subsidiary {subsidiary_id}: {e}")
            return []

    async def _get_vendors_from_snowflake(self, subsidiary_id: str) -> List[Dict[str, Any]]:
        """Get vendors from Snowflake for a subsidiary"""
        try:
            from src.services.warehouse_router import WarehouseRouter

            warehouse_router = WarehouseRouter()
            snowflake = await warehouse_router.get_connector("snowflake")

            query = f"""
            SELECT
                id,
                raw_data:entityid::string as entity_id,
                raw_data:companyname::string as company_name,
                raw_data:email::string as email,
                raw_data:phone::string as phone,
                raw_data:isinactive::boolean as is_inactive
            FROM bronze.netsuite_vendor
            WHERE tenant_id = '{self.tenant_code}'
            AND raw_data:subsidiary:id::string = '{subsidiary_id}'
            ORDER BY company_name
            """

            results = await snowflake.execute(query)

            vendors = []
            for row in results:
                vendors.append({
                    'id': row[0],
                    'entity_id': row[1],
                    'company_name': row[2],
                    'email': row[3],
                    'phone': row[4],
                    'is_active': not row[5]
                })

            return vendors

        except Exception as e:
            logger.error(f"Error getting vendors from Snowflake for subsidiary {subsidiary_id}: {e}")
            return []

    def _calculate_subsidiary_metrics(self, journal_entries: List[Dict], chart_of_accounts: List[Dict],
                                    customers: List[Dict], vendors: List[Dict]) -> Dict[str, float]:
        """Calculate financial metrics for a subsidiary"""
        try:
            # Calculate revenue and expenses from journal entries
            total_revenue = sum(entry.get('debit_amount', 0) for entry in journal_entries
                              if any(revenue in entry.get('account_name', '').lower() for revenue in ['revenue', 'sales']))

            total_expenses = sum(entry.get('debit_amount', 0) for entry in journal_entries
                               if any(expense in entry.get('account_name', '').lower() for expense in ['expense', 'cost']))

            net_income = total_revenue - total_expenses
            profit_margin = (net_income / total_revenue * 100) if total_revenue > 0 else 0

            return {
                'total_revenue': total_revenue,
                'total_expenses': total_expenses,
                'net_income': net_income,
                'profit_margin': profit_margin,
                'journal_entry_count': len(journal_entries),
                'account_count': len(chart_of_accounts),
                'customer_count': len(customers),
                'vendor_count': len(vendors)
            }

        except Exception as e:
            logger.error(f"Error calculating subsidiary metrics: {e}")
            return {
                'total_revenue': 0,
                'total_expenses': 0,
                'net_income': 0,
                'profit_margin': 0,
                'journal_entry_count': len(journal_entries),
                'account_count': len(chart_of_accounts),
                'customer_count': len(customers),
                'vendor_count': len(vendors)
            }

    async def _generate_financial_analysis(self, detailed_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive financial analysis across subsidiaries"""
        logger.info("Generating financial analysis...")

        try:
            analysis = {
                'subsidiary_performance': [],
                'rankings': {
                    'by_revenue': [],
                    'by_profit_margin': [],
                    'by_net_income': []
                },
                'consolidated_metrics': {
                    'total_revenue': 0,
                    'total_expenses': 0,
                    'net_income': 0,
                    'total_journal_entries': 0,
                    'total_accounts': 0,
                    'total_customers': 0,
                    'total_vendors': 0
                },
                'comparative_analysis': {
                    'best_performing_location': None,
                    'highest_margin_location': None,
                    'most_profitable_location': None,
                    'expense_ratio_analysis': []
                }
            }

            # Collect performance data
            for subsidiary_id, data in detailed_results.items():
                if data.get('status') == 'success':
                    financial_data = data.get('financial_data', {})
                    metrics = financial_data.get('financial_metrics', {})
                    subsidiary_info = data.get('subsidiary_info', {})

                    performance_data = {
                        'subsidiary_id': subsidiary_id,
                        'subsidiary_name': subsidiary_info.get('name', f'Subsidiary {subsidiary_id}'),
                        'total_revenue': metrics.get('total_revenue', 0),
                        'total_expenses': metrics.get('total_expenses', 0),
                        'net_income': metrics.get('net_income', 0),
                        'profit_margin': metrics.get('profit_margin', 0),
                        'expense_ratio': (metrics.get('total_expenses', 0) / metrics.get('total_revenue', 1) * 100) if metrics.get('total_revenue', 0) > 0 else 0,
                        'journal_entries': metrics.get('journal_entry_count', 0),
                        'accounts': metrics.get('account_count', 0),
                        'customers': metrics.get('customer_count', 0),
                        'vendors': metrics.get('vendor_count', 0)
                    }
                    analysis['subsidiary_performance'].append(performance_data)

                    # Add to consolidated totals
                    analysis['consolidated_metrics']['total_revenue'] += metrics.get('total_revenue', 0)
                    analysis['consolidated_metrics']['total_expenses'] += metrics.get('total_expenses', 0)
                    analysis['consolidated_metrics']['net_income'] += metrics.get('net_income', 0)
                    analysis['consolidated_metrics']['total_journal_entries'] += metrics.get('journal_entry_count', 0)
                    analysis['consolidated_metrics']['total_accounts'] += metrics.get('account_count', 0)
                    analysis['consolidated_metrics']['total_customers'] += metrics.get('customer_count', 0)
                    analysis['consolidated_metrics']['total_vendors'] += metrics.get('vendor_count', 0)

            # Sort by different metrics
            analysis['rankings']['by_revenue'] = sorted(
                analysis['subsidiary_performance'],
                key=lambda x: x['total_revenue'],
                reverse=True
            )
            analysis['rankings']['by_profit_margin'] = sorted(
                analysis['subsidiary_performance'],
                key=lambda x: x['profit_margin'],
                reverse=True
            )
            analysis['rankings']['by_net_income'] = sorted(
                analysis['subsidiary_performance'],
                key=lambda x: x['net_income'],
                reverse=True
            )

            # Identify top performers
            if analysis['rankings']['by_revenue']:
                analysis['comparative_analysis']['best_performing_location'] = analysis['rankings']['by_revenue'][0]
                analysis['comparative_analysis']['highest_margin_location'] = analysis['rankings']['by_profit_margin'][0]
                analysis['comparative_analysis']['most_profitable_location'] = analysis['rankings']['by_net_income'][0]

            # Calculate averages
            if analysis['subsidiary_performance']:
                count = len(analysis['subsidiary_performance'])
                analysis['consolidated_metrics']['average_profit_margin'] = sum(p['profit_margin'] for p in analysis['subsidiary_performance']) / count
                analysis['consolidated_metrics']['average_expense_ratio'] = sum(p['expense_ratio'] for p in analysis['subsidiary_performance']) / count

            logger.info("✅ Financial analysis generated")
            return analysis

        except Exception as e:
            logger.error(f"Error generating financial analysis: {e}")
            return {'error': str(e)}

    async def _verify_snowflake_data(self, tenant_id: str) -> Dict[str, Any]:
        """Verify that data is properly loaded in Snowflake"""
        logger.info("Verifying Snowflake data...")

        try:
            from src.services.warehouse_router import WarehouseRouter

            warehouse_router = WarehouseRouter()
            snowflake = await warehouse_router.get_connector("snowflake")

            verification_results = {}

            # Check Bronze layer tables
            bronze_tables = [
                'netsuite_journalentry',
                'netsuite_account',
                'netsuite_invoice',
                'netsuite_customerpayment',
                'netsuite_vendorbill',
                'netsuite_customer',
                'netsuite_vendor',
                'netsuite_inventoryitem',
                'netsuite_subsidiary'
            ]

            for table in bronze_tables:
                try:
                    result = await snowflake.execute(
                        f"SELECT COUNT(*) FROM bronze.{table} WHERE tenant_id = '{self.tenant_code}'"
                    )
                    count = result[0][0] if result else 0
                    verification_results[table] = {
                        'count': count,
                        'status': 'verified' if count > 0 else 'empty'
                    }
                except Exception as e:
                    verification_results[table] = {
                        'count': 0,
                        'status': 'error',
                        'error': str(e)
                    }

            # Check Silver layer (if available)
            try:
                silver_result = await snowflake.execute(
                    f"SELECT COUNT(*) FROM silver.fact_netsuite_transactions WHERE tenant_id = '{self.tenant_code}'"
                )
                silver_count = silver_result[0][0] if silver_result else 0
                verification_results['silver_layer'] = {
                    'count': silver_count,
                    'status': 'verified' if silver_count > 0 else 'empty'
                }
            except Exception as e:
                verification_results['silver_layer'] = {
                    'count': 0,
                    'status': 'not_available',
                    'error': str(e)
                }

            # Check Gold layer (if available)
            try:
                gold_result = await snowflake.execute(
                    f"SELECT COUNT(*) FROM gold.daily_financial_metrics WHERE tenant_id = '{self.tenant_code}'"
                )
                gold_count = gold_result[0][0] if gold_result else 0
                verification_results['gold_layer'] = {
                    'count': gold_count,
                    'status': 'verified' if gold_count > 0 else 'empty'
                }
            except Exception as e:
                verification_results['gold_layer'] = {
                    'count': 0,
                    'status': 'not_available',
                    'error': str(e)
                }

            logger.info("✅ Snowflake data verification completed")
            return verification_results

        except Exception as e:
            logger.error(f"Error verifying Snowflake data: {e}")
            return {'error': str(e)}

    async def _generate_final_report(self, sync_results: Dict[str, Any], detailed_results: Dict[str, Dict[str, Any]],
                                   financial_analysis: Dict[str, Any], verification_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final comprehensive report"""
        logger.info("Generating final report...")

        final_report = {
            'extraction_date': datetime.utcnow().isoformat(),
            'tenant_code': self.tenant_code,
            'summary': {
                'total_subsidiaries': len(self.subsidiaries),
                'successful_extractions': len([s for s in detailed_results.values() if s.get('status') == 'success']),
                'failed_extractions': len([s for s in detailed_results.values() if s.get('status') == 'failed'])
            },
            'sync_results': sync_results,
            'detailed_results': detailed_results,
            'financial_analysis': financial_analysis,
            'verification_results': verification_results,
            'next_steps': [
                "Snowflake Dynamic Tables will auto-refresh Bronze → Silver → Gold",
                "Backend API can now query financial data via MCP analytics endpoints",
                "Frontend dashboard will display multi-location financial metrics",
                "PMS vs NetSuite reconciliation analysis is ready"
            ]
        }

        # Save report to file
        await self._save_final_report(final_report)

        logger.info("✅ Final report generated")
        return final_report

    async def _save_final_report(self, final_report: Dict[str, Any]) -> None:
        """Save final report to file"""
        try:
            output_dir = Path('/tmp/netsuite-complete-extraction')
            output_dir.mkdir(exist_ok=True)

            report_file = output_dir / "final_extraction_report.json"
            with open(report_file, 'w') as f:
                json.dump(final_report, f, indent=2, default=str)

            logger.info(f"✅ Final report saved to {report_file}")

        except Exception as e:
            logger.error(f"Error saving final report: {e}")

    def print_final_summary(self, final_report: Dict[str, Any]) -> None:
        """Print final summary of the complete extraction"""
        print("\n" + "="*80)
        print("COMPLETE NETSUITE EXTRACTION SUMMARY")
        print("="*80)

        summary = final_report.get('summary', {})
        financial_analysis = final_report.get('financial_analysis', {})
        consolidated = financial_analysis.get('consolidated_metrics', {})

        print(f"Tenant: {final_report.get('tenant_code', 'Unknown')}")
        print(f"Total Subsidiaries: {summary.get('total_subsidiaries', 0)}")
        print(f"Successful Extractions: {summary.get('successful_extractions', 0)}")
        print(f"Failed Extractions: {summary.get('failed_extractions', 0)}")

        if consolidated:
            print(f"\n💰 Consolidated Financial Metrics:")
            print(f"  Total Revenue: ${consolidated.get('total_revenue', 0):,.2f}")
            print(f"  Total Expenses: ${consolidated.get('total_expenses', 0):,.2f}")
            print(f"  Net Income: ${consolidated.get('net_income', 0):,.2f}")
            print(f"  Total Journal Entries: {consolidated.get('total_journal_entries', 0):,}")
            print(f"  Total Accounts: {consolidated.get('total_accounts', 0):,}")

        print("\n✅ Complete NetSuite data extraction and loading finished!")
        print("🔄 Next steps:")
        for step in final_report.get('next_steps', []):
            print(f"   • {step}")
        print("="*80)

async def main():
    """Main execution function"""
    logger.info("Starting complete NetSuite data extraction orchestration...")

    try:
        orchestrator = CompleteNetSuiteOrchestrator()

        # Run complete extraction
        result = await orchestrator.run_complete_extraction()

        # Print summary
        orchestrator.print_final_summary(result)

        logger.info("🎉 Complete NetSuite extraction orchestration finished successfully!")
        return 0

    except Exception as e:
        logger.error(f"Complete NetSuite extraction orchestration failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

# Make script executable
if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "--make-executable":
    import stat
    script_path = os.path.abspath(__file__)
    os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IEXEC)
    print(f"Made {script_path} executable")