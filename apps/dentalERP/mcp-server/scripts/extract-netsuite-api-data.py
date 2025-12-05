#!/usr/bin/env python3
"""
NetSuite API Data Extraction - Real-time Data Pull
Extracts all financial data from NetSuite API for all Silver Creek subsidiaries
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

# Add src to path
sys.path.append('/opt/dental-erp/mcp-server')

from src.core.database import get_db
from src.core.tenant import TenantContext
from src.services.integration_router import get_integration_router
from src.models.tenant import Tenant
from src.utils.logger import logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NetSuiteAPIExtractor:
    """Extract financial data from NetSuite API for all subsidiaries"""

    def __init__(self, tenant_code: str = "silvercreek"):
        self.tenant_code = tenant_code
        self.subsidiary_data = {}
        self.financial_metrics = {}
        self.journal_entries_by_subsidiary = {}

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

    async def extract_all_subsidiary_data(self, db_session) -> Dict[str, Any]:
        """Extract data for all subsidiaries from NetSuite API"""
        logger.info(f"Starting NetSuite API extraction for tenant: {self.tenant_code}")

        try:
            # Get tenant context
            tenant = await self._get_tenant(db_session)
            if not tenant:
                raise ValueError(f"Tenant {self.tenant_code} not found")

            # Set tenant context
            TenantContext.set_tenant(tenant)

            # Get NetSuite connector
            router = get_integration_router()
            netsuite_connector = await router.get_connector("netsuite", db_session)

            logger.info("Connected to NetSuite API")

            # Extract data for each subsidiary
            for subsidiary_id, subsidiary_info in self.subsidiaries.items():
                logger.info(f"Extracting data for subsidiary {subsidiary_id}: {subsidiary_info['name']}")

                try:
                    # Extract journal entries
                    journal_entries = await self._extract_journal_entries(netsuite_connector, subsidiary_id)

                    # Extract financial metrics
                    financial_metrics = await self._extract_financial_metrics(netsuite_connector, subsidiary_id)

                    # Extract chart of accounts
                    chart_of_accounts = await self._extract_chart_of_accounts(netsuite_connector, subsidiary_id)

                    # Extract customers
                    customers = await self._extract_customers(netsuite_connector, subsidiary_id)

                    # Extract vendors
                    vendors = await self._extract_vendors(netsuite_connector, subsidiary_id)

                    # Store data by subsidiary
                    self.subsidiary_data[subsidiary_id] = {
                        'subsidiary_info': subsidiary_info,
                        'journal_entries': journal_entries,
                        'financial_metrics': financial_metrics,
                        'chart_of_accounts': chart_of_accounts,
                        'customers': customers,
                        'vendors': vendors,
                        'extraction_timestamp': datetime.utcnow().isoformat()
                    }

                    logger.info(f"✅ Completed extraction for subsidiary {subsidiary_id}")

                except Exception as e:
                    logger.error(f"Error extracting data for subsidiary {subsidiary_id}: {e}")
                    # Continue with other subsidiaries even if one fails
                    self.subsidiary_data[subsidiary_id] = {
                        'subsidiary_info': subsidiary_info,
                        'error': str(e),
                        'extraction_timestamp': datetime.utcnow().isoformat()
                    }

            # Calculate consolidated metrics
            await self._calculate_consolidated_metrics()

            logger.info("✅ NetSuite API extraction completed for all subsidiaries")
            return self.subsidiary_data

        except Exception as e:
            logger.error(f"Error in NetSuite API extraction: {e}")
            raise
        finally:
            # Clear tenant context
            TenantContext.clear_tenant()

    async def _get_tenant(self, session) -> Optional[Tenant]:
        """Get tenant from database"""
        from sqlalchemy import select
        result = await session.execute(select(Tenant).where(Tenant.tenant_code == self.tenant_code))
        return result.scalar_one_or_none()

    async def _extract_journal_entries(self, connector, subsidiary_id: str) -> List[Dict[str, Any]]:
        """Extract journal entries for a specific subsidiary"""
        logger.info(f"Extracting journal entries for subsidiary {subsidiary_id}")

        try:
            # Use NetSuite REST API to get journal entries
            # Filter by subsidiary and date range
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')  # Last 90 days

            # Query journal entries
            query_params = {
                'q': f"subsidiary = {subsidiary_id} AND trandate >= {start_date} AND trandate <= {end_date}",
                'limit': 1000
            }

            journal_entries = await connector.query_records('journalEntry', query_params)

            # Transform to standard format
            transformed_entries = []
            for entry in journal_entries:
                transformed_entry = {
                    'id': entry.get('id'),
                    'subsidiary_id': subsidiary_id,
                    'subsidiary_name': self.subsidiaries.get(subsidiary_id, {}).get('name', f'Subsidiary {subsidiary_id}'),
                    'journal_entry_id': entry.get('tranId'),
                    'transaction_date': entry.get('trandate'),
                    'account_id': entry.get('account', {}).get('id'),
                    'account_name': entry.get('account', {}).get('name'),
                    'debit_amount': float(entry.get('debit', 0)),
                    'credit_amount': float(entry.get('credit', 0)),
                    'description': entry.get('memo', ''),
                    'reference': entry.get('name', ''),
                    'currency': entry.get('currency', {}).get('name', 'USD'),
                    'exchange_rate': float(entry.get('exchangerate', 1.0)),
                    'status': entry.get('status', 'Posted'),
                    'created_at': entry.get('createddate'),
                    'last_modified': entry.get('lastmodifieddate')
                }
                transformed_entries.append(transformed_entry)

            logger.info(f"Extracted {len(transformed_entries)} journal entries for subsidiary {subsidiary_id}")
            return transformed_entries

        except Exception as e:
            logger.error(f"Error extracting journal entries for subsidiary {subsidiary_id}: {e}")
            return []

    async def _extract_financial_metrics(self, connector, subsidiary_id: str) -> Dict[str, Any]:
        """Extract financial metrics for a specific subsidiary"""
        logger.info(f"Extracting financial metrics for subsidiary {subsidiary_id}")

        try:
            # Get current month and previous month
            current_month = datetime.now().strftime('%Y-%m')
            previous_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime('%Y-%m')

            metrics = {
                'subsidiary_id': subsidiary_id,
                'subsidiary_name': self.subsidiaries.get(subsidiary_id, {}).get('name', f'Subsidiary {subsidiary_id}'),
                'current_month': current_month,
                'previous_month': previous_month
            }

            # Extract revenue accounts
            revenue_accounts = await self._get_account_balances(connector, subsidiary_id, 'Revenue')
            total_revenue = sum(float(acc.get('balance', 0)) for acc in revenue_accounts)

            # Extract expense accounts
            expense_accounts = await self._get_account_balances(connector, subsidiary_id, 'Expense')
            total_expenses = sum(float(acc.get('balance', 0)) for acc in expense_accounts)

            # Extract asset accounts
            asset_accounts = await self._get_account_balances(connector, subsidiary_id, 'Asset')
            total_assets = sum(float(acc.get('balance', 0)) for acc in asset_accounts)

            # Extract liability accounts
            liability_accounts = await self._get_account_balances(connector, subsidiary_id, 'Liability')
            total_liabilities = sum(float(acc.get('balance', 0)) for acc in liability_accounts)

            # Calculate metrics
            net_income = total_revenue - total_expenses
            profit_margin = (net_income / total_revenue * 100) if total_revenue > 0 else 0
            working_capital = total_assets - total_liabilities

            metrics.update({
                'total_revenue': total_revenue,
                'total_expenses': total_expenses,
                'net_income': net_income,
                'profit_margin': profit_margin,
                'total_assets': total_assets,
                'total_liabilities': total_liabilities,
                'working_capital': working_capital,
                'revenue_accounts': len(revenue_accounts),
                'expense_accounts': len(expense_accounts),
                'asset_accounts': len(asset_accounts),
                'liability_accounts': len(liability_accounts)
            })

            logger.info(f"Extracted financial metrics for subsidiary {subsidiary_id}")
            return metrics

        except Exception as e:
            logger.error(f"Error extracting financial metrics for subsidiary {subsidiary_id}: {e}")
            return {'error': str(e), 'subsidiary_id': subsidiary_id}

    async def _get_account_balances(self, connector, subsidiary_id: str, account_type: str) -> List[Dict[str, Any]]:
        """Get account balances by type for a subsidiary"""
        try:
            # Query accounts by type and subsidiary
            query_params = {
                'q': f"subsidiary = {subsidiary_id} AND type = '{account_type}'",
                'limit': 500
            }

            accounts = await connector.query_records('account', query_params)
            return accounts

        except Exception as e:
            logger.error(f"Error getting {account_type} accounts for subsidiary {subsidiary_id}: {e}")
            return []

    async def _extract_chart_of_accounts(self, connector, subsidiary_id: str) -> List[Dict[str, Any]]:
        """Extract chart of accounts for a specific subsidiary"""
        logger.info(f"Extracting chart of accounts for subsidiary {subsidiary_id}")

        try:
            # Get all accounts for the subsidiary
            query_params = {
                'q': f"subsidiary = {subsidiary_id}",
                'limit': 1000
            }

            accounts = await connector.query_records('account', query_params)

            # Transform to standard format
            chart_of_accounts = []
            for account in accounts:
                account_data = {
                    'id': account.get('id'),
                    'account_number': account.get('acctnumber'),
                    'account_name': account.get('acctname'),
                    'account_type': account.get('type'),
                    'account_category': self._categorize_account(account.get('acctname', '')),
                    'parent_account': account.get('parent', {}).get('name'),
                    'is_active': account.get('isinactive') != 'Yes',
                    'description': account.get('description', ''),
                    'balance': float(account.get('balance', 0)),
                    'currency': account.get('currency', {}).get('name', 'USD'),
                    'subsidiary_id': subsidiary_id
                }
                chart_of_accounts.append(account_data)

            logger.info(f"Extracted {len(chart_of_accounts)} accounts for subsidiary {subsidiary_id}")
            return chart_of_accounts

        except Exception as e:
            logger.error(f"Error extracting chart of accounts for subsidiary {subsidiary_id}: {e}")
            return []

    async def _extract_customers(self, connector, subsidiary_id: str) -> List[Dict[str, Any]]:
        """Extract customers for a specific subsidiary"""
        logger.info(f"Extracting customers for subsidiary {subsidiary_id}")

        try:
            query_params = {
                'q': f"subsidiary = {subsidiary_id}",
                'limit': 1000
            }

            customers = await connector.query_records('customer', query_params)

            # Transform customer data
            transformed_customers = []
            for customer in customers:
                customer_data = {
                    'id': customer.get('id'),
                    'entity_id': customer.get('entityid'),
                    'company_name': customer.get('companyname'),
                    'email': customer.get('email'),
                    'phone': customer.get('phone'),
                    'subsidiary_id': subsidiary_id,
                    'is_active': customer.get('isinactive') != 'Yes',
                    'customer_type': customer.get('customertype', {}).get('name'),
                    'credit_limit': float(customer.get('creditlimit', 0))
                }
                transformed_customers.append(customer_data)

            logger.info(f"Extracted {len(transformed_customers)} customers for subsidiary {subsidiary_id}")
            return transformed_customers

        except Exception as e:
            logger.error(f"Error extracting customers for subsidiary {subsidiary_id}: {e}")
            return []

    async def _extract_vendors(self, connector, subsidiary_id: str) -> List[Dict[str, Any]]:
        """Extract vendors for a specific subsidiary"""
        logger.info(f"Extracting vendors for subsidiary {subsidiary_id}")

        try:
            query_params = {
                'q': f"subsidiary = {subsidiary_id}",
                'limit': 1000
            }

            vendors = await connector.query_records('vendor', query_params)

            # Transform vendor data
            transformed_vendors = []
            for vendor in vendors:
                vendor_data = {
                    'id': vendor.get('id'),
                    'entity_id': vendor.get('entityid'),
                    'company_name': vendor.get('companyname'),
                    'email': vendor.get('email'),
                    'phone': vendor.get('phone'),
                    'subsidiary_id': subsidiary_id,
                    'is_active': vendor.get('isinactive') != 'Yes',
                    'vendor_type': vendor.get('vendortype', {}).get('name'),
                    'credit_limit': float(vendor.get('creditlimit', 0))
                }
                transformed_vendors.append(vendor_data)

            logger.info(f"Extracted {len(transformed_vendors)} vendors for subsidiary {subsidiary_id}")
            return transformed_vendors

        except Exception as e:
            logger.error(f"Error extracting vendors for subsidiary {subsidiary_id}: {e}")
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

    async def _calculate_consolidated_metrics(self) -> None:
        """Calculate consolidated financial metrics across all subsidiaries"""
        logger.info("Calculating consolidated financial metrics...")

        try:
            consolidated_metrics = {
                'total_revenue': 0,
                'total_expenses': 0,
                'total_assets': 0,
                'total_liabilities': 0,
                'subsidiary_count': 0,
                'active_subsidiaries': []
            }

            for subsidiary_id, data in self.subsidiary_data.items():
                if 'error' in data:
                    continue  # Skip subsidiaries with errors

                financial_metrics = data.get('financial_metrics', {})
                if 'error' not in financial_metrics:
                    consolidated_metrics['total_revenue'] += financial_metrics.get('total_revenue', 0)
                    consolidated_metrics['total_expenses'] += financial_metrics.get('total_expenses', 0)
                    consolidated_metrics['total_assets'] += financial_metrics.get('total_assets', 0)
                    consolidated_metrics['total_liabilities'] += financial_metrics.get('total_liabilities', 0)
                    consolidated_metrics['subsidiary_count'] += 1
                    consolidated_metrics['active_subsidiaries'].append({
                        'id': subsidiary_id,
                        'name': data['subsidiary_info']['name'],
                        'net_income': financial_metrics.get('net_income', 0),
                        'profit_margin': financial_metrics.get('profit_margin', 0)
                    })

            consolidated_metrics['consolidated_net_income'] = consolidated_metrics['total_revenue'] - consolidated_metrics['total_expenses']
            consolidated_metrics['consolidated_working_capital'] = consolidated_metrics['total_assets'] - consolidated_metrics['total_liabilities']

            self.financial_metrics['consolidated'] = consolidated_metrics

            logger.info(f"Calculated consolidated metrics for {consolidated_metrics['subsidiary_count']} subsidiaries")

        except Exception as e:
            logger.error(f"Error calculating consolidated metrics: {e}")

    def generate_financial_comparison_report(self) -> Dict[str, Any]:
        """Generate financial comparison report across subsidiaries"""
        logger.info("Generating financial comparison report...")

        try:
            report = {
                'summary': {
                    'total_subsidiaries': len(self.subsidiaries),
                    'active_subsidiaries': len([s for s in self.subsidiary_data.values() if 'error' not in s]),
                    'extraction_date': datetime.utcnow().isoformat(),
                    'currency': 'USD'
                },
                'subsidiary_performance': [],
                'rankings': {
                    'by_revenue': [],
                    'by_profit_margin': [],
                    'by_net_income': []
                },
                'financial_ratios': {
                    'average_profit_margin': 0,
                    'total_consolidated_revenue': 0,
                    'total_consolidated_expenses': 0,
                    'consolidated_net_income': 0
                }
            }

            # Collect performance data
            performance_data = []
            for subsidiary_id, data in self.subsidiary_data.items():
                if 'error' in data:
                    continue

                financial_metrics = data.get('financial_metrics', {})
                if 'error' not in financial_metrics:
                    performance_data.append({
                        'subsidiary_id': subsidiary_id,
                        'subsidiary_name': data['subsidiary_info']['name'],
                        'total_revenue': financial_metrics.get('total_revenue', 0),
                        'total_expenses': financial_metrics.get('total_expenses', 0),
                        'net_income': financial_metrics.get('net_income', 0),
                        'profit_margin': financial_metrics.get('profit_margin', 0),
                        'journal_entries': len(data.get('journal_entries', [])),
                        'customers': len(data.get('customers', [])),
                        'vendors': len(data.get('vendors', []))
                    })

            # Sort by different metrics
            report['rankings']['by_revenue'] = sorted(performance_data, key=lambda x: x['total_revenue'], reverse=True)
            report['rankings']['by_profit_margin'] = sorted(performance_data, key=lambda x: x['profit_margin'], reverse=True)
            report['rankings']['by_net_income'] = sorted(performance_data, key=lambda x: x['net_income'], reverse=True)

            # Calculate averages
            if performance_data:
                report['financial_ratios']['average_profit_margin'] = sum(p['profit_margin'] for p in performance_data) / len(performance_data)
                report['financial_ratios']['total_consolidated_revenue'] = sum(p['total_revenue'] for p in performance_data)
                report['financial_ratios']['total_consolidated_expenses'] = sum(p['total_expenses'] for p in performance_data)
                report['financial_ratios']['consolidated_net_income'] = sum(p['net_income'] for p in performance_data)

            report['subsidiary_performance'] = performance_data

            logger.info("Generated financial comparison report")
            return report

        except Exception as e:
            logger.error(f"Error generating financial comparison report: {e}")
            return {'error': str(e)}

    async def save_extracted_data(self, output_dir: str = '/tmp/netsuite-api-extracted') -> None:
        """Save extracted data to files"""
        logger.info(f"Saving extracted data to {output_dir}")

        try:
            import os
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)

            # Save subsidiary data
            subsidiaries_file = output_path / "subsidiary_data.json"
            with open(subsidiaries_file, 'w') as f:
                json.dump(self.subsidiary_data, f, indent=2, default=str)

            # Save financial metrics
            metrics_file = output_path / "financial_metrics.json"
            with open(metrics_file, 'w') as f:
                json.dump(self.financial_metrics, f, indent=2, default=str)

            # Save comparison report
            report_file = output_path / "financial_comparison_report.json"
            comparison_report = self.generate_financial_comparison_report()
            with open(report_file, 'w') as f:
                json.dump(comparison_report, f, indent=2, default=str)

            # Generate summary
            summary = {
                'extraction_date': datetime.utcnow().isoformat(),
                'tenant_code': self.tenant_code,
                'total_subsidiaries': len(self.subsidiaries),
                'successful_extractions': len([s for s in self.subsidiary_data.values() if 'error' not in s]),
                'failed_extractions': len([s for s in self.subsidiary_data.values() if 'error' in s]),
                'total_journal_entries': sum(len(s.get('journal_entries', [])) for s in self.subsidiary_data.values() if 'error' not in s),
                'total_customers': sum(len(s.get('customers', [])) for s in self.subsidiary_data.values() if 'error' not in s),
                'total_vendors': sum(len(s.get('vendors', [])) for s in self.subsidiary_data.values() if 'error' not in s),
                'total_accounts': sum(len(s.get('chart_of_accounts', [])) for s in self.subsidiary_data.values() if 'error' not in s)
            }

            summary_file = output_path / "extraction_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)

            logger.info(f"✅ Data saved successfully to {output_dir}")
            logger.info(f"   - Subsidiary data: {subsidiaries_file}")
            logger.info(f"   - Financial metrics: {metrics_file}")
            logger.info(f"   - Comparison report: {report_file}")
            logger.info(f"   - Summary: {summary_file}")

        except Exception as e:
            logger.error(f"Error saving extracted data: {e}")
            raise

    def print_extraction_summary(self) -> None:
        """Print summary of extraction results"""
        print("\n" + "="*80)
        print("NETSUITE API EXTRACTION SUMMARY")
        print("="*80)

        successful_extractions = len([s for s in self.subsidiary_data.values() if 'error' not in s])
        failed_extractions = len([s for s in self.subsidiary_data.values() if 'error' in s])

        print(f"Tenant: {self.tenant_code}")
        print(f"Total Subsidiaries: {len(self.subsidiaries)}")
        print(f"Successful Extractions: {successful_extractions}")
        print(f"Failed Extractions: {failed_extractions}")

        if self.subsidiary_data:
            print("\n📊 Data Extracted:")
            total_journal_entries = sum(len(s.get('journal_entries', [])) for s in self.subsidiary_data.values() if 'error' not in s)
            total_customers = sum(len(s.get('customers', [])) for s in self.subsidiary_data.values() if 'error' not in s)
            total_vendors = sum(len(s.get('vendors', [])) for s in self.subsidiary_data.values() if 'error' not in s)
            total_accounts = sum(len(s.get('chart_of_accounts', [])) for s in self.subsidiary_data.values() if 'error' not in s)

            print(f"  Journal Entries: {total_journal_entries:,}")
            print(f"  Customers: {total_customers:,}")
            print(f"  Vendors: {total_vendors:,}")
            print(f"  Chart of Accounts: {total_accounts:,}")

        if self.financial_metrics and 'consolidated' in self.financial_metrics:
            consolidated = self.financial_metrics['consolidated']
            print(f"\n💰 Financial Overview:")
            print(f"  Total Revenue: ${consolidated['total_revenue']:,.2f}")
            print(f"  Total Expenses: ${consolidated['total_expenses']:,.2f}")
            print(f"  Net Income: ${consolidated['consolidated_net_income']:,.2f}")
            print(f"  Working Capital: ${consolidated['consolidated_working_capital']:,.2f}")

        print("\n✅ Ready for Snowflake loading and dashboard display!")
        print("="*80)

async def main():
    """Main execution function"""
    logger.info("Starting NetSuite API data extraction...")

    try:
        extractor = NetSuiteAPIExtractor()

        # Get database session
        async with get_db() as session:
            # Extract data
            extracted_data = await extractor.extract_all_subsidiary_data(session)

            # Save data
            await extractor.save_extracted_data()

            # Print summary
            extractor.print_extraction_summary()

            logger.info("🎉 NetSuite API extraction completed successfully!")
            return 0

    except Exception as e:
        logger.error(f"NetSuite API extraction failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)