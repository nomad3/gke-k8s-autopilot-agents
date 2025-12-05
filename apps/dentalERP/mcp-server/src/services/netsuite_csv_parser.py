"""
NetSuite TransactionDetail CSV Parser Service
Parses NetSuite Transaction Detail export CSVs and loads into Snowflake Bronze layer

REUSES: operations_excel_parser.py pattern for consistency
Flow: Upload CSV → Parse transactions → Bronze Layer → Dynamic tables auto-refresh
"""

import csv
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from decimal import Decimal
from loguru import logger

from ..connectors.snowflake import SnowflakeConnector
from ..core.config import Settings
from ..core.tenant import TenantContext


# Mapping of real NetSuite subsidiary names (from TransactionDetail CSV files) to Operations practice IDs
# NOTE: Some subsidiaries don't have a direct Operations mapping (marked with netsuite_ prefix)
SUBSIDIARY_TO_PRACTICE = {
    # High-confidence mappings (based on name similarity or docs)
    'SCDP San Marcos, LLC': 'ads',           # Advanced Dental Solutions
    'SCDP San Marcos II, LLC': 'ads',        # Advanced Dental Solutions (second location)
    'SCDP Del Sur Ranch, LLC': 'dsr',        # Del Sur Dental
    'SCDP Eastlake, LLC': 'sed',             # Scripps Eastlake Dental
    'SCDP UTC, LLC': 'ucfd',                 # University City Family Dental
    'SCDP Carlsbad, LLC': 'lcd',             # La Costa Dental (Carlsbad area)
    'SCDP Torrey Pines, LLC': 'efd_i',       # Encinitas Family Dental I
    'SCDP Torrey Highlands, LLC': 'ipd',     # Imperial Point Dental
    'SCDP Coronado, LLC': 'dd',              # Downtown Dental
    'SCDP Vista, LLC': 'eawd',               # East Avenue Dental
    'SCDP Laguna Hills, LLC': 'efd_ii',      # Encinitas Family Dental II
    'SCDP Laguna Hills II, LLC': 'efd_ii',   # Same as above
    'SCDP Otay Lakes, LLC': 'lsd',           # La Senda Dental
    'SCDP Kearny Mesa, LLC': 'rd',           # Rancho Dental
    'SCDP Temecula, LLC': 'netsuite_temecula',        # No Operations mapping yet
    'SCDP Temecula II, LLC': 'netsuite_temecula_ii',  # No Operations mapping yet
    'Steve P. Theodosis Dental Corporation, PC': 'netsuite_theodosis',  # No Operations mapping
}


class NetSuiteCSVParser:
    """
    Parse NetSuite Transaction Detail CSV exports
    Follows OperationsReportParser pattern for consistency
    """

    def __init__(self, snowflake_connector: SnowflakeConnector, settings: Settings):
        """
        Initialize NetSuite CSV parser

        Args:
            snowflake_connector: Snowflake connector instance
            settings: Application settings
        """
        self.snowflake = snowflake_connector
        self.settings = settings

    async def process_and_insert(
        self,
        file_path: str,
        subsidiary_id: Optional[str] = None,
        subsidiary_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process NetSuite TransactionDetail CSV and insert to Snowflake

        Args:
            file_path: Path to CSV file
            subsidiary_id: Optional subsidiary ID (will auto-detect from CSV if not provided)
            subsidiary_name: Optional subsidiary name (will auto-detect from CSV if not provided)

        Returns:
            Dictionary with processing results
        """
        logger.info(f"Processing NetSuite TransactionDetail CSV: {file_path}")

        try:
            # Extract subsidiary from CSV header if not provided
            if not subsidiary_id or not subsidiary_name:
                extracted_subsidiary_name = self._extract_subsidiary_from_header(file_path)
                subsidiary_name = subsidiary_name or extracted_subsidiary_name
                subsidiary_id = subsidiary_id or SUBSIDIARY_TO_PRACTICE.get(subsidiary_name, 'unknown')

            logger.info(f"Subsidiary: {subsidiary_name} (ID: {subsidiary_id})")

            # Parse transactions from CSV
            transactions = self._parse_transaction_details(file_path, subsidiary_id, subsidiary_name)

            if not transactions:
                raise ValueError("No transactions found in CSV file")

            logger.info(f"Parsed {len(transactions)} transactions")

            # Insert to Snowflake Bronze layer
            tenant = TenantContext.get_tenant()
            tenant_id = tenant.tenant_code if tenant else 'silvercreek'

            # Prepare records for insertion (simple flat structure matching Bronze table)
            records_to_insert = []
            for txn in transactions:
                record = {
                    'transaction_type': txn['type'],
                    'transaction_date': txn['date'],
                    'document_number': txn['document_number'],
                    'name': txn['name'],
                    'memo': txn['memo'],
                    'account_name': txn['account'],
                    'split': txn['split'],
                    'amount': txn['amount'],
                }
                records_to_insert.append(record)

            # Check for duplicates before inserting
            # Use DELETE + INSERT pattern (simpler than MERGE for this use case)
            logger.info(f"Checking for existing transactions for subsidiary {subsidiary_id}...")

            # Delete existing records for this subsidiary and date range
            # This handles duplicate uploads of the same CSV file
            dates_in_upload = list(set([rec['transaction_date'] for rec in records_to_insert if rec['transaction_date']]))

            if dates_in_upload:
                # Get min and max dates
                min_date = min(dates_in_upload)
                max_date = max(dates_in_upload)

                delete_query = f"""
                    DELETE FROM bronze.netsuite_transaction_details
                    WHERE DATE >= '{min_date}'
                      AND DATE <= '{max_date}'
                      AND ACCOUNT LIKE '%{subsidiary_name}%'
                """

                deleted_count = await self.snowflake.execute_dml(delete_query)
                if deleted_count > 0:
                    logger.info(f"Removed {deleted_count} existing records to avoid duplicates")

            # Insert to table with subsidiary columns
            # Table schema: TYPE, DATE, DOCUMENT, NAME, MEMO, ACCOUNT, CLR, SPLIT, QTY, AMOUNT, SUBSIDIARY_NAME, PRACTICE_ID
            insert_query = """
                INSERT INTO bronze.netsuite_transaction_details
                (TYPE, DATE, DOCUMENT, NAME, MEMO, ACCOUNT, CLR, SPLIT, QTY, AMOUNT, SUBSIDIARY_NAME, PRACTICE_ID)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            # Prepare values for executemany - include subsidiary_name and practice_id
            values_list = [
                (
                    rec['transaction_type'],
                    rec['transaction_date'],
                    rec['document_number'],
                    rec['name'],
                    rec['memo'],
                    rec['account_name'],
                    '',  # CLR field (not in our data)
                    rec['split'],
                    '',  # QTY field (not in our data)
                    str(rec['amount']),
                    subsidiary_name,  # Store subsidiary with each transaction
                    subsidiary_id     # Store practice_id with each transaction
                )
                for rec in records_to_insert
            ]

            inserted_count = await self.snowflake.execute_many(insert_query, values_list)

            logger.info(f"✅ Inserted {inserted_count} transactions to Snowflake")

            return {
                'subsidiary_id': subsidiary_id,
                'subsidiary_name': subsidiary_name,
                'transactions_count': len(transactions),
                'records_inserted': inserted_count,
                'tenant_id': tenant_id,
                'source_file': Path(file_path).name
            }

        except Exception as e:
            logger.error(f"Failed to process NetSuite CSV: {e}")
            raise

    def _extract_subsidiary_from_header(self, file_path: str) -> str:
        """
        Extract subsidiary name from CSV header (row 2)

        CSV format:
        Row 1: "Silver Creek Dental Partners, LLC"
        Row 2: "Parent Company : ... : SCDP Laguna Hills, LLC"
        Row 3: Transaction Detail
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [next(f) for _ in range(2)]
            if len(lines) >= 2:
                parent_line = lines[1].strip().strip('"')
                parts = parent_line.split(':')
                subsidiary_name = parts[-1].strip() if len(parts) > 1 else 'Unknown'
                return subsidiary_name
            raise ValueError("Could not extract subsidiary from CSV header")

    def _parse_transaction_details(
        self,
        file_path: str,
        subsidiary_id: str,
        subsidiary_name: str
    ) -> List[Dict[str, Any]]:
        """
        Parse transactions from CSV

        CSV structure:
        - Rows 1-5: Header info
        - Row 6: Blank
        - Row 7: Column headers
        - Row 8+: Transaction data
        """
        transactions = []

        with open(file_path, 'r', encoding='utf-8') as f:
            # Skip first 6 rows (header info)
            for _ in range(6):
                next(f)

            # Row 7 has the headers
            reader = csv.DictReader(f)

            for row in reader:
                # Clean column names (CSV has trailing spaces)
                clean_row = {k.strip(): v.strip() for k, v in row.items()}

                # Parse amount (remove $ and commas, handle negatives in parentheses)
                amount_str = clean_row.get('Amount', '0')
                amount = self._parse_amount(amount_str)

                transaction = {
                    'type': clean_row.get('Type', ''),
                    'date': self._parse_date(clean_row.get('Date', '')),
                    'document_number': clean_row.get('Document Number', ''),
                    'name': clean_row.get('Name', ''),
                    'memo': clean_row.get('Memo', ''),
                    'account': clean_row.get('Account', ''),
                    'clr': clean_row.get('Clr', ''),
                    'split': clean_row.get('Split', ''),
                    'qty': clean_row.get('Qty', ''),
                    'amount': float(amount)
                }

                # Only add if there's meaningful data
                if transaction['date'] and transaction['amount'] != 0:
                    transactions.append(transaction)

        return transactions

    def _parse_amount(self, amount_str: str) -> Decimal:
        """
        Parse amount string to Decimal

        Handles:
        - "$1,234.56" → 1234.56
        - "($1,234.56)" → -1234.56
        - "" → 0
        """
        if not amount_str:
            return Decimal('0')

        # Remove $ and commas
        cleaned = amount_str.replace('$', '').replace(',', '').strip()

        # Handle parentheses for negative numbers
        if cleaned.startswith('(') and cleaned.endswith(')'):
            cleaned = '-' + cleaned[1:-1]

        try:
            return Decimal(cleaned)
        except:
            logger.warning(f"Could not parse amount: {amount_str}, defaulting to 0")
            return Decimal('0')

    def _parse_date(self, date_str: str) -> str:
        """
        Parse date from various formats to YYYY-MM-DD

        Handles:
        - "1/31/2025" → "2025-01-31"
        - "01/31/2025" → "2025-01-31"
        """
        if not date_str:
            return ''

        try:
            # Try parsing common formats
            for fmt in ['%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue

            logger.warning(f"Could not parse date: {date_str}")
            return date_str
        except Exception as e:
            logger.warning(f"Date parsing error for '{date_str}': {e}")
            return ''
