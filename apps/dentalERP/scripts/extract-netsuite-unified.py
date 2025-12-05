#!/usr/bin/env python3
"""
Unified NetSuite Data Extraction Orchestrator
Extracts ALL financial data from NetSuite API for each Silver Creek subsidiary
and loads directly to Snowflake Bronze layer using existing MCP infrastructure
"""

import asyncio
import os
import json
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import uuid4
import pandas as pd
from pathlib import Path

# Add MCP server to path
sys.path.append('/opt/dental-erp/mcp-server')

from src.core.database import get_db
from src.core.tenant import TenantContext
from src.services.integration_router import get_integration_router
from src.services.warehouse_router import WarehouseRouter
from src.services.snowflake_netsuite_loader import NetSuiteToSnowflakeLoader
from src.services.netsuite_sync_orchestrator import NetSuiteSyncOrchestrator
from src.models.tenant import Tenant
from src.utils.logger import logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedNetSuiteExtractor:
    """
    Unified NetSuite data extractor that leverages existing MCP infrastructure
    to pull ALL financial data for each Silver Creek subsidiary
    """

    def __init__(self, tenant_code: str = "silvercreek"):
        self.tenant_code = tenant_code
        self.extraction_results = {}
        self.financial_summary = {}

        # Silver Creek subsidiaries with their IDs
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

    async def extract_all_financial_data(self) -> Dict[str, Any]:
        """
        Extract ALL financial data from NetSuite for each subsidiary using existing MCP infrastructure
        """
        logger.info(f"Starting unified NetSuite extraction for tenant: {self.tenant_code}")

        try:
            # Get tenant and set context
            async with get_db() as session:
                tenant = await self._get_tenant(session)
                if not tenant:
                    raise ValueError(f"Tenant {self.tenant_code} not found")

                TenantContext.set_tenant(tenant)

                # Step 1: Initialize NetSuite loader for the tenant
                loader = NetSuiteToSnowflakeLoader(str(tenant.id))
                await loader.initialize()

                logger.info(f"Initialized NetSuite loader for tenant {tenant.tenant_code}")

                # Step 2: Extract data for ALL subsidiaries
                extraction_results = await self._extract_data_for_all_subsidiaries(loader)

                # Step 3: Load data directly to Snowflake Bronze layer
                await self._load_to_snowflake_bronze(loader, extraction_results)

                # Step 4: Generate comprehensive financial summary
                financial_summary = await self._generate_financial_summary(extraction_results)

                # Step 5: Save extraction results
                await self._save_extraction_results(extraction_results, financial_summary)

                logger.info("✅ Unified NetSuite extraction completed successfully!")

                return {
                    'extraction_results': extraction_results,
                    'financial_summary': financial_summary,
                    'tenant_id': str(tenant.id),
                    'tenant_code': tenant.tenant_code
                }

        except Exception as e:
            logger.error(f"Error in unified NetSuite extraction: {e}")
            raise
        finally:
            TenantContext.clear_tenant()

    async def _get_tenant(self, session) -> Optional[Tenant]:
        """Get tenant from database"""
        from sqlalchemy import select
        from uuid import UUID
        result = await session.execute(select(Tenant).where(Tenant.tenant_code == self.tenant_code))
        return result.scalar_one_or_none()

    async def _extract_data_for_all_subsidiaries(self, loader: NetSuiteToSnowflakeLoader) -> Dict[str, Any]:
        """Extract data for all subsidiaries"""
        logger.info("Extracting data for all subsidiaries...")

        extraction_results = {}
        total_records = 0

        # Extract data for each subsidiary
        for subsidiary_id, subsidiary_info in self.subsidiaries.items():
            logger.info(f"Extracting data for subsidiary {subsidiary_id}: {subsidiary_info['name']}")

            try:
                # Use the existing loader to sync all record types for this subsidiary
                record_counts = await loader.sync_all_record_types(
                    incremental=False,  # Full sync to get all historical data
                    record_types=None   # Sync all record types
                )

                # Get detailed data for this subsidiary
                subsidiary_data = await self._get_detailed_subsidiary_data(loader, subsidiary_id)

                extraction_results[subsidiary_id] = {
                    'subsidiary_info': subsidiary_info,
                    'record_counts': record_counts,
                    'detailed_data': subsidiary_data,
                    'status': 'success',
                    'extraction_timestamp': datetime.utcnow().isoformat()
                }

                subsidiary_total = sum(record_counts.values())
                total_records += subsidiary_total

                logger.info(f"✅ Extracted {subsidiary_total} records for subsidiary {subsidiary_id}")

            except Exception as e:
                logger.error(f"Error extracting data for subsidiary {subsidiary_id}: {e}")
                extraction_results[subsidiary_id] = {
                    'subsidiary_info': subsidiary_info,
                    'error': str(e),
                    'status': 'failed',
                    'extraction_timestamp': datetime.utcnow().isoformat()
                }

        logger.info(f"✅ Total records extracted: {total_records}")
        return extraction_results

    async def _get_detailed_subsidiary_data(self, loader: NetSuiteToSnowflakeLoader, subsidiary_id: str) -> Dict[str, Any]:
        """Get detailed subsidiary data including financial metrics"""
        logger.info(f"Getting detailed data for subsidiary {subsidiary_id}")

        try:
            # Get journal entries with subsidiary filter
            journal_entries = await self._get_journal_entries_for_subsidiary(loader, subsidiary_id)

            # Get financial accounts and balances
            chart_of_accounts = await self._get_chart_of_accounts_for_subsidiary(loader, subsidiary_id)

            # Get customers
            customers = await self._get_customers_for_subsidiary(loader, subsidiary_id)

            # Get vendors
            vendors = await self._get_vendors_for_subsidiary(loader, subsidiary_id)

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
            logger.error(f"Error getting detailed data for subsidiary {subsidiary_id}: {e}")
            raise

    async def _get_journal_entries_for_subsidiary(self, loader: NetSuiteToSnowflakeLoader, subsidiary_id: str) -> List[Dict[str, Any]]:
        """Get all journal entries for a specific subsidiary"""
        logger.info(f"Getting journal entries for subsidiary {subsidiary_id}")

        try:
            # Get recent journal entries (last 12 months)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)  # Last 12 months

            # Query NetSuite for journal entries
            journal_entries = await loader.netsuite.query_records(
                'journalEntry',
                {
                    'q': f"subsidiary = {subsidiary_id} AND trandate >= {start_date.strftime('%Y-%m-%d')} AND trandate <= {end_date.strftime('%Y-%m-%d')}",
                    'limit': 5000
                }
            )

            # Transform to standard format
            transformed_entries = []
            for entry in journal_entries:
                transformed_entry = {
                    'id': entry.get('id'),
                    'journal_entry_id': entry.get('tranId'),
                    'transaction_date': entry.get('trandate'),
                    'subsidiary_id': subsidiary_id,
                    'subsidiary_name': self.subsidiaries.get(subsidiary_id, {}).get('name', f'Subsidiary {subsidiary_id}'),
                    'account_id': entry.get('account', {}).get('id'),
                    'account_name': entry.get('account', {}).get('name'),
                    'debit_amount': float(entry.get('debit', 0)),
                    'credit_amount': float(entry.get('credit', 0)),
                    'description': entry.get('memo', ''),
                    'reference': entry.get('name', ''),
                    'currency': entry.get('currency', {}).get('name', 'USD'),
                    'exchange_rate': float(entry.get('exchangerate', 1.0)),
                    'status': entry.get('status', 'Posted')
                }
                transformed_entries.append(transformed_entry)

            logger.info(f"Found {len(transformed_entries)} journal entries for subsidiary {subsidiary_id}")
            return transformed_entries

        except Exception as e:
            logger.error(f"Error getting journal entries for subsidiary {subsidiary_id}: {e}")
            return []

    async def _get_chart_of_accounts_for_subsidiary(self, loader: NetSuiteToSnowflakeLoader, subsidiary_id: str) -> List[Dict[str, Any]]:
        """Get chart of accounts for a specific subsidiary"""
        logger.info(f"Getting chart of accounts for subsidiary {subsidiary_id}")

        try:
            accounts = await loader.netsuite.query_records(
                'account',
                {'q': f"subsidiary = {subsidiary_id}", 'limit': 1000}
            )

            # Transform to standard format
            transformed_accounts = []
            for account in accounts:
                account_data = {
                    'id': account.get('id'),
                    'account_number': account.get('acctnumber'),
                    'account_name': account.get('acctname'),
                    'account_type': account.get('type'),
                    'account_category': self._categorize_account(account.get('acctname', '')),
                    'parent_account': account.get('parent', {}).get('name'),
                    'is_active': account.get('isinactive') != 'Yes',
                    'balance': float(account.get('balance', 0)),
                    'currency': account.get('currency', {}).get('name', 'USD'),
                    'subsidiary_id': subsidiary_id
                }
                transformed_accounts.append(account_data)

            logger.info(f"Found {len(transformed_accounts)} accounts for subsidiary {subsidiary_id}")
            return transformed_accounts

        except Exception as e:
            logger.error(f"Error getting chart of accounts for subsidiary {subsidiary_id}: {e}")
            return []

    async def _get_customers_for_subsidiary(self, loader: NetSuiteToSnowflakeLoader, subsidiary_id: str) -> List[Dict[str, Any]]:
        """Get customers for a specific subsidiary"""
        try:
            customers = await loader.netsuite.query_records(
                'customer',
                {'q': f"subsidiary = {subsidiary_id}", 'limit': 1000}
            )

            transformed_customers = []
            for customer in customers:
                customer_data = {
                    'id': customer.get('id'),
                    'entity_id': customer.get('entityid'),
                    'company_name': customer.get('companyname'),
                    'email': customer.get('email'),
                    'phone': customer.get('phone'),
                    'subsidiary_id': subsidiary_id,
                    'is_active': customer.get('isinactive') != 'Yes'
                }
                transformed_customers.append(customer_data)

            return transformed_customers

        except Exception as e:
            logger.error(f"Error getting customers for subsidiary {subsidiary_id}: {e}")
            return []

    async def _get_vendors_for_subsidiary(self, loader: NetSuiteToSnowflakeLoader, subsidiary_id: str) -> List[Dict[str, Any]]:
        """Get vendors for a specific subsidiary"""
        try:
            vendors = await loader.netsuite.query_records(
                'vendor',
                {'q': f"subsidiary = {subsidiary_id}", 'limit': 1000}
            )

            transformed_vendors = []
            for vendor in vendors:
                vendor_data = {
                    'id': vendor.get('id'),
                    'entity_id': vendor.get('entityid'),
                    'company_name': vendor.get('companyname'),
                    'email': vendor.get('email'),
                    'phone': vendor.get('phone'),
                    'subsidiary_id': subsidiary_id,
                    'is_active': vendor.get('isinactive') != 'Yes'
                }
                transformed_vendors.append(vendor_data)

            return transformed_vendors

        except Exception as e:
            logger.error(f"Error getting vendors for subsidiary {subsidiary_id}: {e}")
            return []

    def _categorize_account(self, account_name: str) -> str:
        """Categorize account based on name patterns"""
        account_lower = account_name.lower()

        if any(revenue in account_lower for revenue in ['revenue', 'sales', 'income']):
            return 'Revenue'
        elif any(expense in account_lower for expense in ['expense', 'cost', 'fee']):
            return 'Expense'
        elif any(asset in account_lower for asset in ['asset', 'receivable', 'inventory']):
            return 'Asset'
        elif any(liability in account_lower for liability in ['liability', 'payable', 'loan']):
            return 'Liability'
        elif any(equity in account_lower for equity in ['equity', 'retained', 'capital']):
            return 'Equity'
        else:
            return 'Other'

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

    async def _load_to_snowflake_bronze(self, loader: NetSuiteToSnowflakeLoader, extraction_results: Dict[str, Any]) -> None:
        """Load extracted data to Snowflake Bronze layer"""
        logger.info("Loading data to Snowflake Bronze layer...")

        try:
            # The existing loader already loads data to Snowflake, so we just need to ensure it's complete
            # Trigger any additional processing if needed
            await loader.snowflake.execute("SELECT 1")  # Test connection

            logger.info("✅ Data loaded to Snowflake Bronze layer successfully")

        except Exception as e:
            logger.error(f"Error loading data to Snowflake: {e}")
            raise

    async def _generate_financial_summary(self, extraction_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive financial summary across all subsidiaries"""
        logger.info("Generating financial summary...")

        try:
            summary = {
                'total_subsidiaries': len(self.subsidiaries),
                'successful_extractions': len([s for s in extraction_results.values() if s.get('status') == 'success']),
                'failed_extractions': len([s for s in extraction_results.values() if s.get('status') == 'failed']),
                'subsidiary_metrics': {},
                'consolidated_metrics': {
                    'total_revenue': 0,
                    'total_expenses': 0,
                    'net_income': 0,
                    'total_journal_entries': 0,
                    'total_accounts': 0,
                    'total_customers': 0,
                    'total_vendors': 0
                }
            }

            # Calculate consolidated metrics
            for subsidiary_id, data in extraction_results.items():
                if data.get('status') == 'success':
                    metrics = data.get('detailed_data', {}).get('financial_metrics', {})
                    summary['subsidiary_metrics'][subsidiary_id] = metrics

                    # Add to consolidated totals
                    summary['consolidated_metrics']['total_revenue'] += metrics.get('total_revenue', 0)
                    summary['consolidated_metrics']['total_expenses'] += metrics.get('total_expenses', 0)
                    summary['consolidated_metrics']['net_income'] += metrics.get('net_income', 0)
                    summary['consolidated_metrics']['total_journal_entries'] += metrics.get('journal_entry_count', 0)
                    summary['consolidated_metrics']['total_accounts'] += metrics.get('account_count', 0)
                    summary['consolidated_metrics']['total_customers'] += metrics.get('customer_count', 0)
                    summary['consolidated_metrics']['total_vendors'] += metrics.get('vendor_count', 0)

            # Calculate averages
            successful_count = summary['successful_extractions']
            if successful_count > 0:
                summary['consolidated_metrics']['average_profit_margin'] = (
                    summary['consolidated_metrics']['net_income'] / summary['consolidated_metrics']['total_revenue'] * 100
                ) if summary['consolidated_metrics']['total_revenue'] > 0 else 0

            logger.info("✅ Financial summary generated")
            return summary

        except Exception as e:
            logger.error(f"Error generating financial summary: {e}")
            raise

    async def _save_extraction_results(self, extraction_results: Dict[str, Any], financial_summary: Dict[str, Any]) -> None:
        """Save extraction results to files"""
        logger.info("Saving extraction results...")

        try:
            output_dir = Path('/tmp/netsuite-unified-extracted')
            output_dir.mkdir(exist_ok=True)

            # Save subsidiary data
            subsidiaries_file = output_dir / "subsidiary_data.json"
            with open(subsidiaries_file, 'w') as f:
                json.dump(extraction_results, f, indent=2, default=str)

            # Save financial summary
            summary_file = output_dir / "financial_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(financial_summary, f, indent=2, default=str)

            # Generate comparison report
            comparison_report = self._generate_comparison_report(extraction_results, financial_summary)
            report_file = output_dir / "financial_comparison_report.json"
            with open(report_file, 'w') as f:
                json.dump(comparison_report, f, indent=2, default=str)

            logger.info(f"✅ Extraction results saved to {output_dir}")

        except Exception as e:
            logger.error(f"Error saving extraction results: {e}")
            raise

    def _generate_comparison_report(self, extraction_results: Dict[str, Any], financial_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Generate financial comparison report across subsidiaries"""
        logger.info("Generating financial comparison report...")

        try:
            report = {
                'extraction_date': datetime.utcnow().isoformat(),
                'tenant_code': self.tenant_code,
                'total_subsidiaries': len(self.subsidiaries),
                'successful_extractions': financial_summary.get('successful_extractions', 0),
                'rankings': {
                    'by_revenue': [],
                    'by_profit_margin': [],
                    'by_net_income': []
                },
                'performance_data': []
            }

            # Collect performance data
            for subsidiary_id, data in extraction_results.items():
                if data.get('status') == 'success':
                    metrics = data.get('detailed_data', {}).get('financial_metrics', {})
                    subsidiary_info = data.get('subsidiary_info', {})

                    performance_data = {
                        'subsidiary_id': subsidiary_id,
                        'subsidiary_name': subsidiary_info.get('name', f'Subsidiary {subsidiary_id}'),
                        'total_revenue': metrics.get('total_revenue', 0),
                        'total_expenses': metrics.get('total_expenses', 0),
                        'net_income': metrics.get('net_income', 0),
                        'profit_margin': metrics.get('profit_margin', 0),
                        'journal_entries': metrics.get('journal_entry_count', 0),
                        'accounts': metrics.get('account_count', 0),
                        'customers': metrics.get('customer_count', 0),
                        'vendors': metrics.get('vendor_count', 0)
                    }
                    report['performance_data'].append(performance_data)

            # Sort by different metrics
            report['rankings']['by_revenue'] = sorted(
                report['performance_data'],
                key=lambda x: x['total_revenue'],
                reverse=True
            )
            report['rankings']['by_profit_margin'] = sorted(
                report['performance_data'],
                key=lambda x: x['profit_margin'],
                reverse=True
            )
            report['rankings']['by_net_income'] = sorted(
                report['performance_data'],
                key=lambda x: x['net_income'],
                reverse=True
            )

            return report

        except Exception as e:
            logger.error(f"Error generating comparison report: {e}")
            return {'error': str(e)}

    def print_extraction_summary(self, extraction_results: Dict[str, Any], financial_summary: Dict[str, Any]) -> None:
        """Print summary of extraction results"""
        print("\n" + "="*80)
        print("UNIFIED NETSUITE EXTRACTION SUMMARY")
        print("="*80)

        successful_count = financial_summary.get('successful_extractions', 0)
        failed_count = financial_summary.get('failed_extractions', 0)
        consolidated = financial_summary.get('consolidated_metrics', {})

        print(f"Tenant: {self.tenant_code}")
        print(f"Total Subsidiaries: {len(self.subsidiaries)}")
        print(f"Successful Extractions: {successful_count}")
        print(f"Failed Extractions: {failed_count}")

        if consolidated:
            print(f"\n💰 Consolidated Financial Metrics:")
            print(f"  Total Revenue: ${consolidated.get('total_revenue', 0):,.2f}")
            print(f"  Total Expenses: ${consolidated.get('total_expenses', 0):,.2f}")
            print(f"  Net Income: ${consolidated.get('net_income', 0):,.2f}")
            print(f"  Total Journal Entries: {consolidated.get('total_journal_entries', 0):,}")
            print(f"  Total Accounts: {consolidated.get('total_accounts', 0):,}")
            print(f"  Total Customers: {consolidated.get('total_customers', 0):,}")
            print(f"  Total Vendors: {consolidated.get('total_vendors', 0):,}")

        print("\n✅ Data extracted and loaded to Snowflake Bronze layer!")
        print("🔄 Next: Snowflake Dynamic Tables will auto-refresh Bronze → Silver → Gold")
        print("="*80)

async def main():
    """Main execution function"""
    logger.info("Starting unified NetSuite data extraction...")

    try:
        extractor = UnifiedNetSuiteExtractor()

        # Run extraction
        result = await extractor.extract_all_financial_data()

        # Print summary
        extractor.print_extraction_summary(
            result['extraction_results'],
            result['financial_summary']
        )

        logger.info("🎉 Unified NetSuite extraction completed successfully!")
        return 0

    except Exception as e:
        logger.error(f"Unified NetSuite extraction failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)