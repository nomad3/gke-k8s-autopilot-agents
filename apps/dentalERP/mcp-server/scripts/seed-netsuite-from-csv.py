"""
NetSuite CSV Data Seeding Script
Transforms backup/report_250_transactiondetail.csv into Bronze layer format
Prepares data for Bronze → Silver → Gold transformation pipeline
"""

import asyncio
import csv
import json
import os
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.append('/opt/dental-erp/mcp-server')

from src.utils.logger import logger

# Database connection
DATABASE_URL = os.getenv(
    "POSTGRES_URL",
    "postgresql+asyncpg://postgres:N6At7Nao7EnVPJ9euYhirIgwZI6m69poJEp/FIqIw1xI=@localhost:5432/mcp"
)

# Snowflake configuration (for Bronze layer insertion)
SNOWFLAKE_CONFIG = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT", "HKTPGHW-ES87244"),
    "user": os.getenv("SNOWFLAKE_USER", "NOMADSIMON"),
    "password": os.getenv("SNOWFLAKE_PASSWORD", "@SebaSofi.2k25!!"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
    "database": os.getenv("SNOWFLAKE_DATABASE", "DENTAL_ERP_DW"),
    "schema": "BRONZE",
    "role": os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
}


class NetSuiteCSVSeeder:
    """
    Seeds Bronze layer with NetSuite CSV transaction data
    Matches the structure from backup/report_250_transactiondetail.csv
    """

    def __init__(self):
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # CSV file path
        self.csv_path = Path("/Users/nomade/Documents/GitHub/dentalERP/backup/report_250_transactiondetail.csv")

        # Transaction type mapping
        self.transaction_type_map = {
            "Bill": "vendor_bill",
            "Bill Payment": "bill_payment",
            "Invoice": "invoice",
            "Customer Payment": "customer_payment",
            "Journal Entry": "journal_entry",
            "Deposit": "deposit",
            "Check": "check",
            "Credit Memo": "credit_memo",
            "Vendor Credit": "vendor_credit"
        }

        # Account category mapping (from Account field structure)
        self.account_category_map = {
            "Labs Expenses": "Operating Expenses",
            "Facility Expenses": "Operating Expenses",
            "Marketing": "Operating Expenses",
            "Operating Expenses": "Operating Expenses",
            "Payroll Expenses": "Operating Expenses",
            "Accounts Payable (A/P)": "Current Liabilities",
            "Production Income": "Revenue",
            "Collections": "Revenue",
            "Ramp AP": "Current Assets",
            "Ramp Card": "Current Assets"
        }

    def parse_amount(self, amount_str: str) -> Decimal:
        """Parse amount string to Decimal, handling currency formatting"""
        if not amount_str or amount_str.strip() == "":
            return Decimal("0.00")

        # Remove currency symbols, commas, and handle parentheses (negative)
        cleaned = amount_str.replace("$", "").replace(",", "").strip()

        # Handle negative amounts in parentheses
        if cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = "-" + cleaned[1:-1]

        try:
            return Decimal(cleaned)
        except Exception as e:
            logger.warning(f"Failed to parse amount '{amount_str}': {e}")
            return Decimal("0.00")

    def parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to ISO format"""
        if not date_str or date_str.strip() == "":
            return None

        try:
            # Format: MM/DD/YYYY
            parsed = datetime.strptime(date_str.strip(), "%m/%d/%Y")
            return parsed.strftime("%Y-%m-%d")
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
            return None

    def extract_account_info(self, account_str: str) -> Dict[str, str]:
        """
        Extract account number, name, and category from account string
        Examples:
        - "Labs Expenses : Laboratory Fees" → category: "Labs Expenses", subcategory: "Laboratory Fees"
        - "2000 - Accounts Payable (A/P)" → number: "2000", name: "Accounts Payable (A/P)"
        """
        if not account_str:
            return {"number": None, "name": None, "category": None, "subcategory": None}

        # Pattern 1: "Category : Subcategory"
        if " : " in account_str:
            parts = account_str.split(" : ", 1)
            category = parts[0].strip()
            subcategory = parts[1].strip() if len(parts) > 1 else None
            return {
                "number": None,
                "name": account_str,
                "category": category,
                "subcategory": subcategory
            }

        # Pattern 2: "1234 - Account Name"
        elif " - " in account_str:
            parts = account_str.split(" - ", 1)
            number = parts[0].strip()
            name = parts[1].strip() if len(parts) > 1 else account_str
            return {
                "number": number,
                "name": name,
                "category": self.account_category_map.get(name, "Other"),
                "subcategory": None
            }

        # Pattern 3: Just account name
        else:
            return {
                "number": None,
                "name": account_str,
                "category": self.account_category_map.get(account_str, "Other"),
                "subcategory": None
            }

    def determine_debit_credit(self, amount: Decimal, account_name: str, transaction_type: str) -> tuple[Decimal, Decimal]:
        """
        Determine if amount is debit or credit based on accounting rules
        Returns: (debit_amount, credit_amount)
        """
        # Negative amounts (in parentheses) are typically credits for expense accounts
        if amount < 0:
            # For A/P and split entries, negative means debit
            if "Accounts Payable" in account_name or "Split" in account_name:
                return (abs(amount), Decimal("0.00"))
            else:
                return (Decimal("0.00"), abs(amount))
        else:
            # Positive amounts
            # Revenue accounts are credits
            if "Income" in account_name or "Revenue" in account_name or "Collections" in account_name:
                return (Decimal("0.00"), amount)
            # Expense accounts are debits
            elif "Expense" in account_name or "Labs" in account_name or "Payroll" in account_name:
                return (amount, Decimal("0.00"))
            # A/P is typically credit
            elif "Accounts Payable" in account_name and "Bill Payment" not in transaction_type:
                return (Decimal("0.00"), amount)
            # Default to debit
            else:
                return (amount, Decimal("0.00"))

    async def read_csv_transactions(self) -> List[Dict[str, Any]]:
        """Read and parse CSV file into transaction records"""
        logger.info(f"Reading CSV from: {self.csv_path}")

        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")

        transactions = []

        with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
            # Skip header lines (company name, report title, date range, blank lines)
            for _ in range(6):
                next(f)

            # Read CSV data
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=7):
                # Skip summary/total rows
                if row.get('Type', '').strip().lower() in ['total', '']:
                    continue

                # Extract and clean data
                transaction_type = row.get('Type', '').strip()
                date_str = row.get('Date', '').strip()
                doc_number = row.get('Document Number', '').strip()
                name = row.get('Name', '').strip()
                memo = row.get('Memo', '').strip()
                account_str = row.get('Account', '').strip()
                split_account = row.get('Split', '').strip()
                amount_str = row.get('Amount', '').strip()

                # Skip if missing critical data
                if not transaction_type or not date_str or not account_str:
                    continue

                # Parse amount
                amount = self.parse_amount(amount_str)

                # Parse date
                transaction_date = self.parse_date(date_str)
                if not transaction_date:
                    continue

                # Extract account info
                account_info = self.extract_account_info(account_str)
                split_info = self.extract_account_info(split_account) if split_account else None

                # Determine debit/credit
                debit_amount, credit_amount = self.determine_debit_credit(
                    amount, account_info['name'], transaction_type
                )

                # Build transaction record
                transaction = {
                    "id": str(uuid4()),
                    "sync_id": str(uuid4()),
                    "tenant_id": "silvercreek",
                    "transaction_type": self.transaction_type_map.get(transaction_type, "other"),
                    "transaction_date": transaction_date,
                    "document_number": doc_number or None,
                    "entity_name": name or None,
                    "memo": memo or None,
                    "account_number": account_info.get("number"),
                    "account_name": account_info.get("name"),
                    "account_category": account_info.get("category"),
                    "account_subcategory": account_info.get("subcategory"),
                    "split_account": split_info.get("name") if split_info else None,
                    "debit_amount": float(debit_amount),
                    "credit_amount": float(credit_amount),
                    "amount": float(amount),
                    "raw_data": {
                        "Type": transaction_type,
                        "Date": date_str,
                        "Document Number": doc_number,
                        "Name": name,
                        "Memo": memo,
                        "Account": account_str,
                        "Split": split_account,
                        "Amount": amount_str,
                        "csv_row": row_num
                    },
                    "extracted_at": datetime.utcnow().isoformat(),
                    "is_deleted": False
                }

                transactions.append(transaction)

        logger.info(f"Parsed {len(transactions)} transactions from CSV")
        return transactions

    async def insert_to_bronze_layer(self, transactions: List[Dict[str, Any]]) -> int:
        """
        Insert transactions into Snowflake Bronze layer
        Uses netsuite_transactions table (consolidated transaction detail)
        """
        logger.info("Inserting transactions to Bronze layer...")

        try:
            # Import Snowflake connector
            import snowflake.connector

            # Connect to Snowflake
            conn = snowflake.connector.connect(
                account=SNOWFLAKE_CONFIG["account"],
                user=SNOWFLAKE_CONFIG["user"],
                password=SNOWFLAKE_CONFIG["password"],
                warehouse=SNOWFLAKE_CONFIG["warehouse"],
                database=SNOWFLAKE_CONFIG["database"],
                schema=SNOWFLAKE_CONFIG["schema"],
                role=SNOWFLAKE_CONFIG["role"]
            )

            cursor = conn.cursor()

            # Create table if not exists
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS bronze.netsuite_transactions (
                id VARCHAR(50) PRIMARY KEY,
                sync_id VARCHAR(36),
                tenant_id VARCHAR(50),
                transaction_type VARCHAR(50),
                transaction_date DATE,
                document_number VARCHAR(100),
                entity_name VARCHAR(255),
                memo TEXT,
                account_number VARCHAR(50),
                account_name VARCHAR(255),
                account_category VARCHAR(100),
                account_subcategory VARCHAR(255),
                split_account VARCHAR(255),
                debit_amount DECIMAL(15,2),
                credit_amount DECIMAL(15,2),
                amount DECIMAL(15,2),
                raw_data VARIANT,
                extracted_at TIMESTAMP,
                is_deleted BOOLEAN DEFAULT FALSE,
                _ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
            )
            """
            cursor.execute(create_table_sql)

            # Clear existing data for this tenant
            cursor.execute("DELETE FROM bronze.netsuite_transactions WHERE tenant_id = 'silvercreek'")

            # Insert transactions
            insert_sql = """
            INSERT INTO bronze.netsuite_transactions (
                id, sync_id, tenant_id, transaction_type, transaction_date,
                document_number, entity_name, memo, account_number, account_name,
                account_category, account_subcategory, split_account,
                debit_amount, credit_amount, amount, raw_data, extracted_at, is_deleted
            ) VALUES (
                %(id)s, %(sync_id)s, %(tenant_id)s, %(transaction_type)s, %(transaction_date)s,
                %(document_number)s, %(entity_name)s, %(memo)s, %(account_number)s, %(account_name)s,
                %(account_category)s, %(account_subcategory)s, %(split_account)s,
                %(debit_amount)s, %(credit_amount)s, %(amount)s, PARSE_JSON(%(raw_data)s), %(extracted_at)s, %(is_deleted)s
            )
            """

            inserted_count = 0
            for transaction in transactions:
                # Convert raw_data to JSON string
                transaction['raw_data'] = json.dumps(transaction['raw_data'])

                try:
                    cursor.execute(insert_sql, transaction)
                    inserted_count += 1
                except Exception as e:
                    logger.error(f"Failed to insert transaction {transaction['id']}: {e}")

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"✅ Inserted {inserted_count} transactions to Bronze layer")
            return inserted_count

        except Exception as e:
            logger.error(f"Failed to insert to Bronze layer: {e}")
            raise

    async def generate_summary_stats(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics from parsed transactions"""
        total_debits = sum(Decimal(str(t['debit_amount'])) for t in transactions)
        total_credits = sum(Decimal(str(t['credit_amount'])) for t in transactions)

        transaction_types = {}
        for t in transactions:
            ttype = t['transaction_type']
            transaction_types[ttype] = transaction_types.get(ttype, 0) + 1

        account_categories = {}
        for t in transactions:
            cat = t['account_category']
            if cat:
                account_categories[cat] = account_categories.get(cat, 0) + 1

        # Date range
        dates = [t['transaction_date'] for t in transactions if t['transaction_date']]
        date_range = {
            "start": min(dates) if dates else None,
            "end": max(dates) if dates else None
        }

        return {
            "total_transactions": len(transactions),
            "total_debits": float(total_debits),
            "total_credits": float(total_credits),
            "balance_check": float(total_debits - total_credits),
            "transaction_types": transaction_types,
            "account_categories": account_categories,
            "date_range": date_range,
            "entities_count": len(set(t['entity_name'] for t in transactions if t['entity_name']))
        }

    async def run_seeding(self) -> Dict[str, Any]:
        """Run complete CSV seeding process"""
        logger.info("Starting NetSuite CSV data seeding...")

        try:
            # 1. Read and parse CSV
            transactions = await self.read_csv_transactions()

            # 2. Generate summary stats
            stats = await self.generate_summary_stats(transactions)

            # 3. Insert to Bronze layer
            inserted_count = await self.insert_to_bronze_layer(transactions)

            logger.info("✅ NetSuite CSV data seeding completed successfully!")

            return {
                "success": True,
                "transactions_parsed": len(transactions),
                "transactions_inserted": inserted_count,
                "summary_stats": stats
            }

        except Exception as e:
            logger.error(f"CSV seeding failed: {e}")
            raise


async def main():
    """Main execution function"""
    logger.info("Starting NetSuite CSV seeding process...")

    try:
        seeder = NetSuiteCSVSeeder()

        # Run seeding
        result = await seeder.run_seeding()

        if result["success"]:
            logger.info("🎉 NetSuite CSV seeding completed successfully!")

            # Print summary
            print("\n" + "="*80)
            print("NETSUITE CSV SEEDING SUMMARY")
            print("="*80)
            print(f"Transactions Parsed: {result['transactions_parsed']}")
            print(f"Transactions Inserted to Bronze: {result['transactions_inserted']}")
            print(f"\nSummary Statistics:")
            stats = result['summary_stats']
            print(f"  Total Debits: ${stats['total_debits']:,.2f}")
            print(f"  Total Credits: ${stats['total_credits']:,.2f}")
            print(f"  Balance Check: ${stats['balance_check']:,.2f}")
            print(f"  Date Range: {stats['date_range']['start']} to {stats['date_range']['end']}")
            print(f"  Unique Entities: {stats['entities_count']}")
            print(f"\nTransaction Types:")
            for ttype, count in stats['transaction_types'].items():
                print(f"    {ttype}: {count}")
            print(f"\nAccount Categories:")
            for cat, count in stats['account_categories'].items():
                print(f"    {cat}: {count}")
            print("\n✅ Ready for Bronze → Silver → Gold transformation!")
            print("="*80)

            return 0
        else:
            logger.error("❌ CSV seeding failed")
            return 1

    except Exception as e:
        logger.error(f"❌ CSV seeding process failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
