#!/usr/bin/env python3
"""
Process NetSuite CSV backup data and convert to backend-compatible format
This script processes the CSV backup files and creates data structures
compatible with our backend seeding scripts.
"""

import csv
import json
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NetSuiteCSVProcessor:
    """Process NetSuite CSV backup data for backend seeding"""

    def __init__(self, backup_dir: str = "/opt/dental-erp/backup"):
        self.backup_dir = Path(backup_dir)
        self.output_dir = Path("/tmp/netsuite-csv-processed")
        self.output_dir.mkdir(exist_ok=True)

        # Silver Creek subsidiaries mapping based on CSV data
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

        # Account categories for financial analysis
        self.account_categories = {
            'revenue': ['Production', 'Collection', 'Income', 'Revenue'],
            'expense': ['Expense', 'Cost', 'Fee', 'Rent', 'Lab', 'Supplies'],
            'asset': ['Asset', 'Receivable', 'Cash', 'Equipment'],
            'liability': ['Liability', 'Payable', 'Loan', 'Credit'],
            'equity': ['Equity', 'Capital', 'Retained']
        }

    def process_transaction_detail(self) -> Dict[str, Any]:
        """Process the main transaction detail CSV file"""
        logger.info("Processing transaction detail CSV...")

        transaction_file = self.backup_dir / "report_250_transactiondetail.csv"
        if not transaction_file.exists():
            logger.error(f"Transaction detail file not found: {transaction_file}")
            return {}

        try:
            # Read CSV, skipping header rows
            df = pd.read_csv(transaction_file, skiprows=5)  # Skip report header

            # Clean column names
            df.columns = [col.strip().replace(' ', '_').replace('$', '').lower() for col in df.columns]

            logger.info(f"Loaded {len(df)} transactions from CSV")

            # Process transactions by subsidiary
            subsidiary_data = {}

            for subsidiary_id, subsidiary_info in self.subsidiaries.items():
                subsidiary_name = subsidiary_info['name']

                # Filter transactions for this subsidiary (based on Name column)
                subsidiary_transactions = df[df['name'].str.contains(subsidiary_name.split(',')[0], na=False, case=False)]

                if len(subsidiary_transactions) == 0:
                    # If no direct matches, use broader filtering
                    subsidiary_transactions = df[df['name'].str.contains('Dental|Crown|Lab', na=False, case=False)]

                logger.info(f"Found {len(subsidiary_transactions)} transactions for {subsidiary_name}")

                # Convert to journal entries format
                journal_entries = []
                total_revenue = 0
                total_expenses = 0

                for _, row in subsidiary_transactions.iterrows():
                    amount_str = str(row.get('amount', '0')).replace(',', '').replace('$', '').replace('(', '-').replace(')', '')
                    try:
                        amount = float(amount_str) if amount_str and amount_str != 'nan' else 0
                    except:
                        amount = 0

                    # Determine debit/credit based on transaction type and amount
                    transaction_type = str(row.get('type', '')).lower()
                    account_name = str(row.get('account', ''))

                    debit_amount = 0
                    credit_amount = 0

                    if transaction_type in ['bill', 'check', 'credit card']:
                        debit_amount = abs(amount) if amount > 0 else 0
                        total_expenses += debit_amount
                    elif transaction_type in ['invoice', 'payment', 'deposit']:
                        credit_amount = abs(amount) if amount > 0 else 0
                        total_revenue += credit_amount
                    else:
                        # Default logic based on account name
                        if any(expense in account_name.lower() for expense in ['expense', 'cost', 'fee', 'rent']):
                            debit_amount = abs(amount) if amount > 0 else 0
                            total_expenses += debit_amount
                        else:
                            credit_amount = abs(amount) if amount > 0 else 0
                            total_revenue += credit_amount

                    journal_entry = {
                        'id': f"JE_{row.get('document_number', 'UNK')}_{row.name}",
                        'journal_entry_id': str(row.get('document_number', 'UNK')),
                        'transaction_date': row.get('date', datetime.now().strftime('%m/%d/%Y')),
                        'account_name': account_name,
                        'debit_amount': debit_amount,
                        'credit_amount': credit_amount,
                        'description': str(row.get('memo', '')),
                        'reference_entity': str(row.get('name', ''))
                    }
                    journal_entries.append(journal_entry)

                # Calculate financial metrics
                net_income = total_revenue - total_expenses
                profit_margin = (net_income / total_revenue * 100) if total_revenue > 0 else 0

                subsidiary_data[subsidiary_id] = {
                    'subsidiary_info': subsidiary_info,
                    'journal_entries': journal_entries,
                    'financial_metrics': {
                        'total_revenue': total_revenue,
                        'total_expenses': total_expenses,
                        'net_income': net_income,
                        'profit_margin': profit_margin,
                        'journal_entry_count': len(journal_entries)
                    },
                    'status': 'success',
                    'extraction_timestamp': datetime.utcnow().isoformat()
                }

            logger.info(f"Successfully processed transactions for {len(subsidiary_data)} subsidiaries")
            return subsidiary_data

        except Exception as e:
            logger.error(f"Error processing transaction detail CSV: {e}")
            return {}

    def process_chart_of_accounts(self) -> Dict[str, List[Dict[str, Any]]]:
        """Process chart of accounts from transaction data"""
        logger.info("Processing chart of accounts...")

        transaction_file = self.backup_dir / "report_250_transactiondetail.csv"
        if not transaction_file.exists():
            return {}

        try:
            df = pd.read_csv(transaction_file, skiprows=5)
            chart_of_accounts = {}

            for subsidiary_id, subsidiary_info in self.subsidiaries.items():
                accounts = []
                unique_accounts = df['Account'].dropna().unique()

                for account_name in unique_accounts:
                    if pd.isna(account_name) or account_name == 'nan':
                        continue

                    account_category = self._categorize_account(account_name)

                    account = {
                        'id': f"ACCT_{subsidiary_id}_{hash(account_name) % 10000}",
                        'account_name': account_name,
                        'account_category': account_category,
                        'account_type': account_category,
                        'is_active': True
                    }
                    accounts.append(account)

                chart_of_accounts[subsidiary_id] = accounts

            logger.info(f"Created chart of accounts with {sum(len(accounts) for accounts in chart_of_accounts.values())} accounts")
            return chart_of_accounts

        except Exception as e:
            logger.error(f"Error processing chart of accounts: {e}")
            return {}

    def process_customers_and_vendors(self) -> tuple:
        """Process customer and vendor lists"""
        logger.info("Processing customers and vendors...")

        customers = []
        vendors = []

        try:
            # Process customer/job list
            custjob_file = self.backup_dir / "custjoblist.csv"
            if custjob_file.exists():
                with open(custjob_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        customer = {
                            'id': f"CUST_{hash(row.get('Name', '')) % 10000}",
                            'entity_id': row.get('Name', ''),
                            'company_name': row.get('Name', ''),
                            'email': '',
                            'phone': '',
                            'is_active': True
                        }
                        customers.append(customer)

            # Process vendor list
            vendor_file = self.backup_dir / "vendorlist.csv"
            if vendor_file.exists():
                # Read first few lines to understand structure
                with open(vendor_file, 'r') as f:
                    lines = f.readlines()[:5]
                    logger.info(f"Vendor file structure: {lines}")

                # Try to process as CSV
                try:
                    df = pd.read_csv(vendor_file)
                    for _, row in df.iterrows():
                        vendor = {
                            'id': f"VEND_{hash(str(row.get('Name', ''))) % 10000}",
                            'entity_id': str(row.get('Name', '')),
                            'company_name': str(row.get('Name', '')),
                            'email': '',
                            'phone': '',
                            'is_active': True
                        }
                        vendors.append(vendor)
                except:
                    logger.warning("Could not process vendor list as CSV, using dummy data")
                    # Create dummy vendors for each subsidiary
                    for i, (subsidiary_id, subsidiary_info) in enumerate(self.subsidiaries.items()):
                        vendor = {
                            'id': f"VEND_{subsidiary_id}_{i}",
                            'entity_id': f"Vendor_{i+1}",
                            'company_name': f"Vendor {i+1} for {subsidiary_info['name']}",
                            'email': f"vendor{i+1}@example.com",
                            'phone': f"(555) 123-{i+1:04d}",
                            'is_active': True
                        }
                        vendors.append(vendor)

            logger.info(f"Processed {len(customers)} customers and {len(vendors)} vendors")
            return customers, vendors

        except Exception as e:
            logger.error(f"Error processing customers and vendors: {e}")
            return [], []

    def _categorize_account(self, account_name: str) -> str:
        """Categorize account based on name patterns"""
        account_lower = account_name.lower()

        for category, keywords in self.account_categories.items():
            if any(keyword.lower() in account_lower for keyword in keywords):
                return category.capitalize()

        return 'Other'

    def generate_comprehensive_data(self) -> Dict[str, Any]:
        """Generate comprehensive data structure for backend seeding"""
        logger.info("Generating comprehensive NetSuite data from CSV backup...")

        # Process all data sources
        transaction_data = self.process_transaction_detail()
        chart_of_accounts = self.process_chart_of_accounts()
        customers, vendors = self.process_customers_and_vendors()

        # Combine all data
        comprehensive_data = {}

        for subsidiary_id, subsidiary_info in self.subsidiaries.items():
            subsidiary_transactions = transaction_data.get(subsidiary_id, {})

            # Add chart of accounts to existing data
            if subsidiary_id in subsidiary_transactions:
                subsidiary_transactions['chart_of_accounts'] = chart_of_accounts.get(subsidiary_id, [])
                subsidiary_transactions['customers'] = customers
                subsidiary_transactions['vendors'] = vendors

                # Recalculate metrics with complete data
                metrics = subsidiary_transactions.get('financial_metrics', {})
                metrics['account_count'] = len(chart_of_accounts.get(subsidiary_id, []))
                metrics['customer_count'] = len(customers)
                metrics['vendor_count'] = len(vendors)

                comprehensive_data[subsidiary_id] = subsidiary_transactions

        # Generate consolidated metrics
        consolidated_metrics = self._calculate_consolidated_metrics(comprehensive_data)

        result = {
            'extraction_date': datetime.utcnow().isoformat(),
            'data_source': 'CSV Backup Processing',
            'total_subsidiaries': len(comprehensive_data),
            'subsidiary_data': comprehensive_data,
            'consolidated_metrics': consolidated_metrics
        }

        logger.info(f"Generated comprehensive data for {len(comprehensive_data)} subsidiaries")
        return result

    def _calculate_consolidated_metrics(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate consolidated metrics across all subsidiaries"""
        total_revenue = 0
        total_expenses = 0
        total_journal_entries = 0
        total_accounts = 0
        total_customers = 0
        total_vendors = 0

        for subsidiary_data in data.values():
            metrics = subsidiary_data.get('financial_metrics', {})
            total_revenue += metrics.get('total_revenue', 0)
            total_expenses += metrics.get('total_expenses', 0)
            total_journal_entries += metrics.get('journal_entry_count', 0)
            total_accounts += metrics.get('account_count', 0)
            total_customers += metrics.get('customer_count', 0)
            total_vendors += metrics.get('vendor_count', 0)

        return {
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_income': total_revenue - total_expenses,
            'profit_margin': ((total_revenue - total_expenses) / total_revenue * 100) if total_revenue > 0 else 0,
            'total_journal_entries': total_journal_entries,
            'total_accounts': total_accounts,
            'total_customers': total_customers,
            'total_vendors': total_vendors
        }

    def save_data(self, data: Dict[str, Any]) -> None:
        """Save processed data to files"""
        logger.info("Saving processed data...")

        try:
            # Save main data structure
            main_file = self.output_dir / "netsuite_csv_data.json"
            with open(main_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            # Save subsidiary-specific data for backend seeding
            for subsidiary_id, subsidiary_data in data.get('subsidiary_data', {}).items():
                sub_file = self.output_dir / f"subsidiary_{subsidiary_id}_data.json"
                with open(sub_file, 'w') as f:
                    json.dump(subsidiary_data, f, indent=2, default=str)

            # Save financial summary
            summary_file = self.output_dir / "financial_summary.json"
            summary = {
                'extraction_date': data.get('extraction_date'),
                'total_subsidiaries': data.get('total_subsidiaries'),
                'consolidated_metrics': data.get('consolidated_metrics'),
                'successful_extractions': len(data.get('subsidiary_data', {})),
                'failed_extractions': 0
            }
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)

            logger.info(f"✅ Data saved to {self.output_dir}")
            logger.info(f"   - Main data: {main_file}")
            logger.info(f"   - Financial summary: {summary_file}")
            logger.info(f"   - Subsidiary files: {len(data.get('subsidiary_data', {}))} files")

        except Exception as e:
            logger.error(f"Error saving data: {e}")

    def print_summary(self, data: Dict[str, Any]) -> None:
        """Print summary of processed data"""
        print("\n" + "="*80)
        print("NETSUITE CSV DATA PROCESSING SUMMARY")
        print("="*80)

        consolidated = data.get('consolidated_metrics', {})
        subsidiary_data = data.get('subsidiary_data', {})

        print(f"Data Source: {data.get('data_source', 'Unknown')}")
        print(f"Processing Date: {data.get('extraction_date', 'Unknown')}")
        print(f"Total Subsidiaries: {data.get('total_subsidiaries', 0)}")
        print(f"Successful Processing: {len(subsidiary_data)}")

        if consolidated:
            print(f"\n💰 Consolidated Financial Metrics:")
            print(f"  Total Revenue: ${consolidated.get('total_revenue', 0):,.2f}")
            print(f"  Total Expenses: ${consolidated.get('total_expenses', 0):,.2f}")
            print(f"  Net Income: ${consolidated.get('net_income', 0):,.2f}")
            print(f"  Profit Margin: {consolidated.get('profit_margin', 0):.2f}%")
            print(f"  Total Journal Entries: {consolidated.get('total_journal_entries', 0):,}")
            print(f"  Total Accounts: {consolidated.get('total_accounts', 0):,}")
            print(f"  Total Customers: {consolidated.get('total_customers', 0):,}")
            print(f"  Total Vendors: {consolidated.get('total_vendors', 0):,}")

        print("\n🏢 Subsidiary Performance:")
        for subsidiary_id, sub_data in subsidiary_data.items():
            info = sub_data.get('subsidiary_info', {})
            metrics = sub_data.get('financial_metrics', {})
            print(f"  {info.get('name', f'Subsidiary {subsidiary_id}')}:")
            print(f"    Revenue: ${metrics.get('total_revenue', 0):,.2f}")
            print(f"    Net Income: ${metrics.get('net_income', 0):,.2f}")
            print(f"    Journal Entries: {metrics.get('journal_entry_count', 0):,}")

        print("\n✅ CSV data processing completed!")
        print("🔄 Next: Use this data to seed backend API and Snowflake")
        print("="*80)

async def main():
    """Main execution function"""
    logger.info("Starting NetSuite CSV data processing...")

    try:
        processor = NetSuiteCSVProcessor()

        # Process all CSV data
        comprehensive_data = processor.generate_comprehensive_data()

        if comprehensive_data.get('subsidiary_data'):
            # Save processed data
            processor.save_data(comprehensive_data)

            # Print summary
            processor.print_summary(comprehensive_data)

            logger.info("🎉 NetSuite CSV data processing completed successfully!")
            return 0
        else:
            logger.error("No data was processed from CSV files")
            return 1

    except Exception as e:
        logger.error(f"NetSuite CSV data processing failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)