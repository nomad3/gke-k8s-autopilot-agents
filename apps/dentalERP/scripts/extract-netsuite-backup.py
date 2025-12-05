#!/usr/bin/env python3
"""
NetSuite Backup Data Extraction and Transformation Script
Extracts data from backup CSV files and transforms to current schema format
"""

import pandas as pd
import json
import re
import uuid
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/netsuite-extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NetSuiteBackupExtractor:
    """Extract and transform NetSuite backup data to current schema format"""

    def __init__(self, backup_dir: str = '/opt/dental-erp/backup'):
        self.backup_dir = Path(backup_dir)
        self.output_dir = Path('/tmp/netsuite-extracted')
        self.output_dir.mkdir(exist_ok=True)

        # Silver Creek specific mappings
        self.tenant_code = "silvercreek"
        self.practice_name = "Silver Creek Dental Partners, LLC"

        # Subsidiary ID to location mapping
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

    def extract_transaction_details(self) -> Dict[str, pd.DataFrame]:
        """Extract and categorize transaction details"""
        logger.info("Extracting transaction details...")

        try:
            # Read CSV, skipping header rows
            df = pd.read_csv(
                self.backup_dir / "report_250_transactiondetail.csv",
                skiprows=5,  # Skip report header
                dtype=str  # Read all as strings initially
            )

            logger.info(f"Loaded {len(df)} transaction records")

            # Clean and standardize data
            df = df.fillna('')

            # Separate by transaction type
            journal_entries = df[df['Type '] == 'Journal'].copy()
            bills = df[df['Type '] == 'Bill'].copy()
            invoices = df[df['Type '] == 'Invoice'].copy()
            customer_payments = df[df['Type '] == 'Customer Payment'].copy()
            vendor_bills = df[df['Type '] == 'Vendor Bill'].copy()

            logger.info(f"Found {len(journal_entries)} journal entries")
            logger.info(f"Found {len(bills)} bills")
            logger.info(f"Found {len(invoices)} invoices")
            logger.info(f"Found {len(customer_payments)} customer payments")
            logger.info(f"Found {len(vendor_bills)} vendor bills")

            # Transform journal entries to standard format
            journal_entries_transformed = self._transform_journal_entries(journal_entries)

            return {
                'journal_entries': journal_entries_transformed,
                'bills': bills,
                'invoices': invoices,
                'customer_payments': customer_payments,
                'vendor_bills': vendor_bills,
                'all_transactions': df
            }

        except Exception as e:
            logger.error(f"Error extracting transaction details: {e}")
            raise

    def _transform_journal_entries(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform journal entries to standard format"""
        logger.info("Transforming journal entries...")

        if df.empty:
            return df

        # Clean column names
        df = df.rename(columns=lambda x: x.strip())

        # Extract key fields
        transformed = pd.DataFrame({
            'journal_entry_id': df['Document Number'],
            'transaction_date': pd.to_datetime(df['Date '], format='%m/%d/%Y'),
            'subsidiary_id': self._extract_subsidiary_id(df),
            'account_name': df['Account'].str.strip(),
            'debit_amount': self._extract_debit_amount(df['Amount']),
            'credit_amount': self._extract_credit_amount(df['Amount']),
            'description': df['Memo'].str.strip(),
            'reference_entity': df['Name'].str.strip(),
            'currency': 'USD',
            'exchange_rate': 1.0,
            'status': 'Posted',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        })

        return transformed

    def _extract_subsidiary_id(self, df: pd.DataFrame) -> pd.Series:
        """Extract subsidiary ID from reference entity or memo"""
        # Try to extract from entity name first
        subsidiary_ids = []

        for _, row in df.iterrows():
            entity = str(row.get('Name', '')).strip()
            memo = str(row.get('Memo', '')).strip()

            # Look for known subsidiary patterns
            subsidiary_id = None

            # Check if entity name contains subsidiary info
            for sid, info in self.subsidiary_mapping.items():
                if info['name'] in entity:
                    subsidiary_id = sid
                    break

            # If not found, try to extract from memo
            if not subsidiary_id and memo:
                # Look for location codes in memo
                for sid, info in self.subsidiary_mapping.items():
                    if info['code'].replace('-', ' ').title() in memo:
                        subsidiary_id = sid
                        break

            # Default to parent company if not found
            if not subsidiary_id:
                subsidiary_id = '1'  # Parent company

            subsidiary_ids.append(subsidiary_id)

        return pd.Series(subsidiary_ids)

    def _extract_debit_amount(self, amount_series: pd.Series) -> pd.Series:
        """Extract debit amounts (positive values)"""
        amounts = []

        for amount_str in amount_series:
            if pd.isna(amount_str) or amount_str == '':
                amounts.append(0.0)
                continue

            # Remove $ and commas, handle parentheses for negative
            clean_amount = str(amount_str).replace('$', '').replace(',', '')

            # Check if negative (parentheses)
            if '(' in clean_amount and ')' in clean_amount:
                amounts.append(0.0)  # Credit, not debit
            else:
                try:
                    amounts.append(float(clean_amount))
                except ValueError:
                    amounts.append(0.0)

        return pd.Series(amounts)

    def _extract_credit_amount(self, amount_series: pd.Series) -> pd.Series:
        """Extract credit amounts (negative values as positive)"""
        amounts = []

        for amount_str in amount_series:
            if pd.isna(amount_str) or amount_str == '':
                amounts.append(0.0)
                continue

            # Remove $ and commas, handle parentheses for negative
            clean_amount = str(amount_str).replace('$', '').replace(',', '')

            # Check if negative (parentheses)
            if '(' in clean_amount and ')' in clean_amount:
                # Extract number from parentheses
                number = clean_amount.replace('(', '').replace(')', '')
                try:
                    amounts.append(abs(float(number)))  # Make positive
                except ValueError:
                    amounts.append(0.0)
            else:
                amounts.append(0.0)  # Debit, not credit

        return pd.Series(amounts)

    def extract_customers_and_subsidiaries(self) -> Dict[str, pd.DataFrame]:
        """Extract customer and subsidiary data"""
        logger.info("Extracting customers and subsidiaries...")

        try:
            df = pd.read_csv(
                self.backup_dir / "custjoblist.csv",
                skiprows=3,  # Skip header rows
                dtype=str
            )

            df = df.fillna('')
            logger.info(f"Loaded {len(df)} customer/subsidiary records")

            # Separate parent company from subsidiaries
            parent_company = df[df['Name'] == 'Uncategorized'].copy()
            subsidiaries = df[df['Name'].str.startswith('IC SCDP')].copy()
            customers = df[~df['Name'].str.startswith('IC SCDP') & (df['Name'] != 'Uncategorized')].copy()

            logger.info(f"Found {len(parent_company)} parent company records")
            logger.info(f"Found {len(subsidiaries)} subsidiary records")
            logger.info(f"Found {len(customers)} customer records")

            # Transform subsidiaries to locations format
            locations = self._transform_subsidiaries_to_locations(subsidiaries)

            return {
                'parent_company': parent_company,
                'subsidiaries': subsidiaries,
                'customers': customers,
                'locations': locations
            }

        except Exception as e:
            logger.error(f"Error extracting customers: {e}")
            raise

    def _transform_subsidiaries_to_locations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform subsidiaries to backend locations format"""
        logger.info("Transforming subsidiaries to locations...")

        if df.empty:
            return df

        locations = []

        for _, row in df.iterrows():
            name = row['Name'].strip()

            # Remove "IC " prefix and clean up
            clean_name = name.replace('IC ', '').strip()

            # Map to known subsidiary
            location_data = None
            for sid, info in self.subsidiary_mapping.items():
                if info['name'] == clean_name:
                    location_data = {
                        'id': str(uuid.uuid4()),
                        'practice_id': 'PARENT_PRACTICE_ID',  # Will be replaced
                        'name': clean_name,
                        'subsidiary_name': clean_name,
                        'external_system_id': sid,
                        'external_system_type': 'netsuite',
                        'address': self._generate_dummy_address(info['code']),
                        'phone': f"(858) 555-{sid.zfill(4)}",
                        'email': f"{info['code']}@silvercreekdp.com",
                        'operating_hours': self._generate_operating_hours(),
                        'is_active': row['Inactive'] != 'Yes',
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    break

            if location_data:
                locations.append(location_data)

        return pd.DataFrame(locations)

    def _generate_dummy_address(self, location_code: str) -> Dict[str, str]:
        """Generate dummy address for location"""
        return {
            "street": f"{location_code.replace('-', ' ').title()} Plaza",
            "city": "San Diego",
            "state": "CA",
            "zipCode": "92101",
            "country": "USA"
        }

    def _generate_operating_hours(self) -> Dict[str, Any]:
        """Generate standard operating hours"""
        return {
            "monday": {"open": "08:00", "close": "17:00"},
            "tuesday": {"open": "08:00", "close": "17:00"},
            "wednesday": {"open": "08:00", "close": "17:00"},
            "thursday": {"open": "08:00", "close": "17:00"},
            "friday": {"open": "08:00", "close": "17:00"},
            "saturday": {"open": "09:00", "close": "13:00"},
            "sunday": {"open": None, "close": None}
        }

    def extract_employees(self) -> pd.DataFrame:
        """Extract employee data and transform to users format"""
        logger.info("Extracting employees...")

        try:
            df = pd.read_csv(
                self.backup_dir / "employeelist.csv",
                skiprows=3,
                dtype=str
            )

            df = df.fillna('')
            logger.info(f"Loaded {len(df)} employee records")

            # Transform to users format
            users = self._transform_employees_to_users(df)

            return users

        except Exception as e:
            logger.error(f"Error extracting employees: {e}")
            raise

    def _transform_employees_to_users(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform employees to backend users format"""
        logger.info("Transforming employees to users...")

        if df.empty:
            return df

        users = []

        for _, row in df.iterrows():
            full_name = row['Name'].strip()
            contact_info = row['Contact Info'].strip()

            # Parse name
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0] if len(name_parts) > 0 else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''

            # Extract email from HTML contact info
            email = self._extract_email_from_html(contact_info)

            # Generate phone if email not found
            phone = self._extract_phone_from_html(contact_info) or f"(858) 555-{str(len(users) + 1).zfill(4)}"

            # Determine role based on name/email patterns
            role = self._determine_user_role(full_name, email)

            user_data = {
                'id': str(uuid.uuid4()),
                'email': email or f"user{len(users) + 1}@silvercreekdp.com",
                'password_hash': '$2b$10$dummyHashForSeeding',  # Will be set by backend
                'first_name': first_name,
                'last_name': last_name,
                'role': role,
                'phone': phone,
                'active': row['Inactive'] != 'Yes',
                'last_login': None,
                'preferences': {},
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }

            users.append(user_data)

        return pd.DataFrame(users)

    def _extract_email_from_html(self, html_contact: str) -> str:
        """Extract email from HTML contact info"""
        if not html_contact or 'mailto:' not in html_contact:
            return ''

        # Simple regex to extract email from mailto:
        email_match = re.search(r'mailto:([^"\'\s\>]+)', html_contact)
        if email_match:
            email = email_match.group(1)
            # Clean up any HTML entities or extra characters
            email = email.split('"')[0].split('"')[0]
            return email.strip()

        return ''

    def _extract_phone_from_html(self, html_contact: str) -> str:
        """Extract phone from HTML contact info"""
        if not html_contact:
            return ''

        # Look for phone pattern
        phone_match = re.search(r'\(\d{3}\)\s*\d{3}-\d{4}', html_contact)
        if phone_match:
            return phone_match.group(0)

        return ''

    def _determine_user_role(self, full_name: str, email: str) -> str:
        """Determine user role based on name and email patterns"""
        # Executive patterns
        if any(exec_name in full_name.lower() for exec_name in ['starkweather', 'brad']):
            return 'executive'

        # Manager patterns
        if any(mgr_name in full_name.lower() for mgr_name in ['marra', 'barbara', 'schmidt', 'lindsey']):
            return 'manager'

        # Accountant patterns
        if 'accounting' in email.lower() or 'ap@' in email.lower():
            return 'manager'  # Accounting managers

        # Default to staff
        return 'staff'

    def extract_vendors(self) -> pd.DataFrame:
        """Extract vendor data"""
        logger.info("Extracting vendors...")

        try:
            df = pd.read_csv(
                self.backup_dir / "vendorlist.csv",
                skiprows=3,
                dtype=str
            )

            df = df.fillna('')
            logger.info(f"Loaded {len(df)} vendor records")

            # Transform to vendor format
            vendors = self._transform_vendors(df)

            return vendors

        except Exception as e:
            logger.error(f"Error extracting vendors: {e}")
            raise

    def _transform_vendors(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform vendor data to standard format"""
        logger.info("Transforming vendors...")

        if df.empty:
            return df

        vendors = []

        for _, row in df.iterrows():
            vendor_data = {
                'id': str(uuid.uuid4()),
                'vendor_name': row['Name'].strip(),
                'vendor_type': row['Category'] if row['Category'] else 'General',
                'email': row['Email'].strip() if row['Email'] else None,
                'phone': row['Phone'].strip() if row['Phone'] else None,
                'subsidiary_name': row['Primary Subsidiary'].strip(),
                'is_active': row['Inactive'] != 'Yes',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }

            vendors.append(vendor_data)

        return pd.DataFrame(vendors)

    def extract_chart_of_accounts(self) -> pd.DataFrame:
        """Extract unique chart of accounts from transactions"""
        logger.info("Extracting chart of accounts...")

        try:
            # Get transaction details to extract accounts
            transactions = pd.read_csv(
                self.backup_dir / "report_250_transactiondetail.csv",
                skiprows=5,
                dtype=str
            )

            # Get unique accounts
            unique_accounts = transactions['Account'].dropna().unique()
            logger.info(f"Found {len(unique_accounts)} unique accounts")

            # Transform to account format
            accounts = self._transform_accounts(unique_accounts)

            return accounts

        except Exception as e:
            logger.error(f"Error extracting chart of accounts: {e}")
            raise

    def _transform_accounts(self, accounts: List[str]) -> pd.DataFrame:
        """Transform account names to standard format"""
        logger.info("Transforming chart of accounts...")

        account_data = []

        for account_name in accounts:
            if not account_name or account_name.strip() == '':
                continue

            account_name = account_name.strip()

            # Determine account category based on name
            category = self._categorize_account(account_name)

            # Extract hierarchy (if colon-separated)
            if ':' in account_name:
                parts = account_name.split(':', 1)
                parent_account = parts[0].strip()
                account_name = parts[1].strip()
            else:
                parent_account = None

            account_data.append({
                'id': str(uuid.uuid4()),
                'account_name': account_name,
                'account_category': category,
                'account_type': self._determine_account_type(category),
                'parent_account': parent_account,
                'is_active': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })

        return pd.DataFrame(account_data)

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

    def _determine_account_type(self, category: str) -> str:
        """Determine detailed account type from category"""
        type_mapping = {
            'Revenue': 'Revenue',
            'Expense': 'Operating Expense',
            'Asset': 'Current Asset',
            'Liability': 'Current Liability',
            'Equity': 'Equity',
            'Other': 'Other'
        }
        return type_mapping.get(category, 'Other')

    def save_extracted_data(self, data: Dict[str, Any]) -> None:
        """Save extracted data to JSON files for seeding"""
        logger.info("Saving extracted data...")

        try:
            # Save journal entries
            if 'journal_entries' in data and not data['journal_entries'].empty:
                journal_file = self.output_dir / "journal_entries.json"
                data['journal_entries'].to_json(journal_file, orient='records', date_format='iso')
                logger.info(f"Saved {len(data['journal_entries'])} journal entries to {journal_file}")

            # Save locations
            if 'locations' in data and not data['locations'].empty:
                locations_file = self.output_dir / "locations.json"
                data['locations'].to_json(locations_file, orient='records', date_format='iso')
                logger.info(f"Saved {len(data['locations'])} locations to {locations_file}")

            # Save users
            if 'users' in data and not data['users'].empty:
                users_file = self.output_dir / "users.json"
                data['users'].to_json(users_file, orient='records', date_format='iso')
                logger.info(f"Saved {len(data['users'])} users to {users_file}")

            # Save vendors
            if 'vendors' in data and not data['vendors'].empty:
                vendors_file = self.output_dir / "vendors.json"
                data['vendors'].to_json(vendors_file, orient='records', date_format='iso')
                logger.info(f"Saved {len(data['vendors'])} vendors to {vendors_file}")

            # Save chart of accounts
            if 'chart_of_accounts' in data and not data['chart_of_accounts'].empty:
                accounts_file = self.output_dir / "chart_of_accounts.json"
                data['chart_of_accounts'].to_json(accounts_file, orient='records', date_format='iso')
                logger.info(f"Saved {len(data['chart_of_accounts'])} accounts to {accounts_file}")

            # Save summary
            summary = {
                'extraction_date': datetime.now().isoformat(),
                'tenant_code': self.tenant_code,
                'record_counts': {
                    'journal_entries': len(data.get('journal_entries', pd.DataFrame())),
                    'locations': len(data.get('locations', pd.DataFrame())),
                    'users': len(data.get('users', pd.DataFrame())),
                    'vendors': len(data.get('vendors', pd.DataFrame())),
                    'chart_of_accounts': len(data.get('chart_of_accounts', pd.DataFrame()))
                }
            }

            summary_file = self.output_dir / "extraction_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)

            logger.info(f"Extraction summary saved to {summary_file}")

        except Exception as e:
            logger.error(f"Error saving extracted data: {e}")
            raise

    def run_extraction(self) -> Dict[str, Any]:
        """Run complete data extraction process"""
        logger.info("Starting NetSuite backup data extraction...")

        try:
            extracted_data = {}

            # Extract transaction details
            transaction_data = self.extract_transaction_details()
            extracted_data.update(transaction_data)

            # Extract customers and subsidiaries
            customer_data = self.extract_customers_and_subsidiaries()
            extracted_data.update(customer_data)

            # Extract employees
            users = self.extract_employees()
            extracted_data['users'] = users

            # Extract vendors
            vendors = self.extract_vendors()
            extracted_data['vendors'] = vendors

            # Extract chart of accounts
            chart_of_accounts = self.extract_chart_of_accounts()
            extracted_data['chart_of_accounts'] = chart_of_accounts

            # Save all extracted data
            self.save_extracted_data(extracted_data)

            logger.info("NetSuite backup data extraction completed successfully!")

            return extracted_data

        except Exception as e:
            logger.error(f"Error during extraction: {e}")
            raise

def main():
    """Main execution function"""
    try:
        # Initialize extractor
        extractor = NetSuiteBackupExtractor()

        # Run extraction
        extracted_data = extractor.run_extraction()

        # Print summary
        print("\n" + "="*60)
        print("NETSUITE BACKUP EXTRACTION COMPLETED")
        print("="*60)

        for data_type, df in extracted_data.items():
            if isinstance(df, pd.DataFrame):
                print(f"{data_type}: {len(df)} records")
            elif isinstance(df, dict) and 'locations' in df:
                print(f"locations: {len(df['locations'])} records")

        print(f"\nExtracted data saved to: {extractor.output_dir}")
        print("="*60)

        return 0

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())