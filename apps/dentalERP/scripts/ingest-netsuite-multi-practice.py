#!/usr/bin/env python3
"""
NetSuite CSV Backup Multi-Practice Ingestion Script
===================================================

Purpose: Load NetSuite CSV backup data into 3 demo practices with proper
         subsidiary mapping to Bronze layer in Snowflake

Author: DentalERP Team
Date: November 12, 2025
"""

import csv
import os
import sys
import json
import uuid
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp-server', 'src'))

try:
    import snowflake.connector
    from snowflake.connector import DictCursor
except ImportError:
    print("ERROR: snowflake-connector-python not installed")
    print("Install with: pip install snowflake-connector-python")
    sys.exit(1)


# ============================================================================
# CONFIGURATION
# ============================================================================

BACKUP_DIR = os.path.join(os.path.dirname(__file__), '..', 'backup')

# Demo practice mapping based on NetSuite subsidiaries
PRACTICE_MAPPING = {
    'eastlake': {
        'name': 'Eastlake Dental',
        'location': 'Seattle, WA',
        'subsidiary_patterns': [
            'SCDP Eastlake',
            'Eastlake'
        ],
        'tenant_id': 'eastlake'
    },
    'torrey_pines': {
        'name': 'Torrey Pines Dental',
        'location': 'San Diego, CA',
        'subsidiary_patterns': [
            'SCDP Torrey Pines',
            'Torrey Pines',
            'Torrey Highlands'
        ],
        'tenant_id': 'torrey_pines'
    },
    'ads': {
        'name': 'Advanced Dental Solutions',
        'location': 'San Diego, CA',
        'subsidiary_patterns': [
            'SCDP San Marcos',
            'San Marcos',
            'Mission Hills'
        ],
        'tenant_id': 'ads'
    }
}

# Default practice for records without specific subsidiary
DEFAULT_PRACTICE = 'eastlake'

# CSV file configurations - Use the mapped files with all subsidiaries
CSV_FILES = {
    'transactions_eastlake': {
        'file': 'TransactionDetail_eastlake_mapped.csv',
        'skip_rows': 6,  # Header metadata rows (verified)
        'table': 'bronze.netsuite_journal_entries',
        'practice': 'eastlake'
    },
    'transactions_torrey': {
        'file': 'TransactionDetail_torrey_pines_mapped.csv',
        'skip_rows': 6,
        'table': 'bronze.netsuite_journal_entries',
        'practice': 'torrey_pines'
    },
    'transactions_ads': {
        'file': 'TransactionDetail_ads_mapped.csv',
        'skip_rows': 6,
        'table': 'bronze.netsuite_journal_entries',
        'practice': 'ads'
    },
    'vendors': {
        'file': 'vendorlist.csv',
        'skip_rows': 5,  # Header metadata rows (5 blank/metadata lines)
        'table': 'bronze.netsuite_vendors'
    },
    'customers': {
        'file': 'custjoblist.csv',
        'skip_rows': 5,  # Header metadata rows (5 blank/metadata lines)
        'table': 'bronze.netsuite_customers'
    },
    'employees': {
        'file': 'employeelist.csv',
        'skip_rows': 5,  # Header metadata rows (5 blank/metadata lines)
        'table': 'bronze.netsuite_employees'
    }
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_snowflake_connection():
    """Create Snowflake connection from environment variables"""
    required_vars = [
        'SNOWFLAKE_ACCOUNT',
        'SNOWFLAKE_USER',
        'SNOWFLAKE_PASSWORD',
        'SNOWFLAKE_DATABASE',
        'SNOWFLAKE_SCHEMA',
        'SNOWFLAKE_WAREHOUSE'
    ]

    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema=os.getenv('SNOWFLAKE_SCHEMA'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        session_parameters={
            'QUERY_TAG': 'netsuite_csv_ingestion'
        }
    )


def map_subsidiary_to_practice(subsidiary_text: str) -> str:
    """
    Map NetSuite subsidiary hierarchy to practice tenant_id

    Args:
        subsidiary_text: Full subsidiary path from NetSuite
                        e.g., "Parent Company : Silver Creek Dental Partners, LLC : SCDP Holdings, LLC : SCDP Torrey Pines, LLC"

    Returns:
        Practice tenant_id (eastlake, torrey_pines, or ads)
    """
    if not subsidiary_text:
        return DEFAULT_PRACTICE

    # Check each practice's patterns
    for practice_id, practice_info in PRACTICE_MAPPING.items():
        for pattern in practice_info['subsidiary_patterns']:
            if pattern.lower() in subsidiary_text.lower():
                return practice_id

    return DEFAULT_PRACTICE


def clean_amount(amount_str: str) -> Optional[Decimal]:
    """
    Clean and convert currency string to Decimal

    Args:
        amount_str: Currency string like "$1,234.56" or "($123.45)"

    Returns:
        Decimal value (negative for parentheses notation)
    """
    if not amount_str or amount_str.strip() == '':
        return None

    try:
        # Remove currency symbols and commas
        cleaned = amount_str.replace('$', '').replace(',', '').strip()

        # Handle parentheses notation (negative)
        is_negative = cleaned.startswith('(') and cleaned.endswith(')')
        if is_negative:
            cleaned = cleaned[1:-1]

        value = Decimal(cleaned)
        return -value if is_negative else value

    except (InvalidOperation, ValueError):
        return None


def parse_date(date_str: str) -> Optional[str]:
    """
    Parse date string to ISO format

    Args:
        date_str: Date in format "11/1/2025" or similar

    Returns:
        ISO formatted date string "2025-11-01" or None
    """
    if not date_str:
        return None

    try:
        # Try MM/DD/YYYY format
        dt = datetime.strptime(date_str, '%m/%d/%Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        try:
            # Try M/D/YYYY format
            dt = datetime.strptime(date_str, '%-m/%-d/%Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            return None


def extract_email_from_html(html_text: str) -> Optional[str]:
    """Extract email address from HTML contact info"""
    if not html_text:
        return None

    # Look for mailto: links
    match = re.search(r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', html_text)
    if match:
        return match.group(1)

    # Look for plain email addresses
    match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', html_text)
    if match:
        return match.group(1)

    return None


# ============================================================================
# DATA EXTRACTION FUNCTIONS
# ============================================================================

def extract_transactions(csv_path: str, skip_rows: int = 6) -> Tuple[Dict[str, List], Dict]:
    """
    Extract and split transactions by practice

    Args:
        csv_path: Path to CSV file
        skip_rows: Number of header rows to skip (default: 6)

    Returns:
        Tuple of (practice_transactions_dict, stats_dict)
    """
    print(f"\n{'='*80}")
    print(f"EXTRACTING TRANSACTIONS from {os.path.basename(csv_path)}")
    print(f"{'='*80}")

    practice_data = {practice_id: [] for practice_id in PRACTICE_MAPPING.keys()}
    stats = defaultdict(int)

    with open(csv_path, 'r', encoding='utf-8') as f:
        # Skip metadata rows
        for _ in range(skip_rows):
            next(f)

        reader = csv.DictReader(f)

        for row in reader:
            stats['total_rows'] += 1

            # Skip empty rows
            if not row.get('Type '):
                continue

            # Clean field names (remove trailing spaces)
            clean_row = {k.strip(): v.strip() for k, v in row.items()}

            # Determine practice from account or vendor name
            # Transactions don't have direct subsidiary field, so we infer from other fields
            practice_id = DEFAULT_PRACTICE

            # Check account field for subsidiary clues
            account = clean_row.get('Account', '')
            split = clean_row.get('Split', '')

            # For now, assign to default practice (will be enhanced based on vendor/account mapping)
            # In production, you would cross-reference with vendor subsidiary

            # Build transaction record
            transaction = {
                'id': f"{clean_row.get('Document Number', '')}_{stats['total_rows']}",
                'sync_id': str(uuid.uuid4()),
                'tenant_id': practice_id,
                'raw_data': json.dumps(clean_row),
                'transaction_type': clean_row.get('Type', ''),
                'transaction_date': parse_date(clean_row.get('Date', '')),
                'document_number': clean_row.get('Document Number', ''),
                'name': clean_row.get('Name', ''),
                'account': account,
                'amount': clean_amount(clean_row.get('Amount', '')),
                'memo': clean_row.get('Memo', ''),
                'extracted_at': datetime.utcnow().isoformat()
            }

            practice_data[practice_id].append(transaction)
            stats[f'practice_{practice_id}'] += 1
            stats[f'type_{clean_row.get("Type", "unknown")}'] += 1

    print(f"\n✓ Extracted {stats['total_rows']} transaction records")
    for practice_id in PRACTICE_MAPPING.keys():
        print(f"  - {PRACTICE_MAPPING[practice_id]['name']}: {stats[f'practice_{practice_id}']} records")

    return practice_data, dict(stats)


def extract_vendors(csv_path: str) -> Tuple[Dict[str, List], Dict]:
    """
    Extract and split vendors by practice based on subsidiary

    Returns:
        Tuple of (practice_vendors_dict, stats_dict)
    """
    print(f"\n{'='*80}")
    print(f"EXTRACTING VENDORS from {os.path.basename(csv_path)}")
    print(f"{'='*80}")

    practice_data = {practice_id: [] for practice_id in PRACTICE_MAPPING.keys()}
    stats = defaultdict(int)

    with open(csv_path, 'r', encoding='utf-8') as f:
        # Skip metadata rows
        for _ in range(CSV_FILES['vendors']['skip_rows']):
            next(f)

        reader = csv.DictReader(f)

        for row in reader:
            stats['total_rows'] += 1

            # Clean field names
            clean_row = {k.strip(): v.strip() for k, v in row.items()}

            # Map subsidiary to practice
            subsidiary = clean_row.get('Primary Subsidiary', '')
            practice_id = map_subsidiary_to_practice(subsidiary)

            # Build vendor record
            vendor = {
                'id': f"vendor_{stats['total_rows']}",
                'sync_id': str(uuid.uuid4()),
                'tenant_id': practice_id,
                'raw_data': json.dumps(clean_row),
                'vendor_name': clean_row.get('Name', ''),
                'category': clean_row.get('Category', ''),
                'subsidiary': subsidiary,
                'phone': clean_row.get('Phone', ''),
                'email': clean_row.get('Email', ''),
                'is_inactive': clean_row.get('Inactive', 'No').lower() == 'yes',
                'extracted_at': datetime.utcnow().isoformat()
            }

            practice_data[practice_id].append(vendor)
            stats[f'practice_{practice_id}'] += 1

            if vendor['is_inactive']:
                stats['inactive_vendors'] += 1

    print(f"\n✓ Extracted {stats['total_rows']} vendor records")
    for practice_id in PRACTICE_MAPPING.keys():
        print(f"  - {PRACTICE_MAPPING[practice_id]['name']}: {stats[f'practice_{practice_id}']} records")
    print(f"  - Inactive vendors: {stats['inactive_vendors']}")

    return practice_data, dict(stats)


def extract_customers(csv_path: str) -> Tuple[Dict[str, List], Dict]:
    """
    Extract and split customers by practice based on subsidiary

    Returns:
        Tuple of (practice_customers_dict, stats_dict)
    """
    print(f"\n{'='*80}")
    print(f"EXTRACTING CUSTOMERS from {os.path.basename(csv_path)}")
    print(f"{'='*80}")

    practice_data = {practice_id: [] for practice_id in PRACTICE_MAPPING.keys()}
    stats = defaultdict(int)

    with open(csv_path, 'r', encoding='utf-8') as f:
        # Skip metadata rows
        for _ in range(CSV_FILES['customers']['skip_rows']):
            next(f)

        reader = csv.DictReader(f)

        for row in reader:
            stats['total_rows'] += 1

            # Clean field names
            clean_row = {k.strip(): v.strip() for k, v in row.items()}

            # Map subsidiary to practice
            subsidiary = clean_row.get('Primary Subsidiary', '')
            practice_id = map_subsidiary_to_practice(subsidiary)

            # Build customer record
            customer = {
                'id': clean_row.get('ID', f"customer_{stats['total_rows']}"),
                'sync_id': str(uuid.uuid4()),
                'tenant_id': practice_id,
                'raw_data': json.dumps(clean_row),
                'customer_name': clean_row.get('Name', ''),
                'category': clean_row.get('Category', ''),
                'subsidiary': subsidiary,
                'phone': clean_row.get('Phone', ''),
                'email': clean_row.get('Email', ''),
                'status': clean_row.get('Status', ''),
                'is_inactive': clean_row.get('Inactive', 'No').lower() == 'yes',
                'extracted_at': datetime.utcnow().isoformat()
            }

            practice_data[practice_id].append(customer)
            stats[f'practice_{practice_id}'] += 1

            if customer['is_inactive']:
                stats['inactive_customers'] += 1

    print(f"\n✓ Extracted {stats['total_rows']} customer records")
    for practice_id in PRACTICE_MAPPING.keys():
        print(f"  - {PRACTICE_MAPPING[practice_id]['name']}: {stats[f'practice_{practice_id}']} records")
    print(f"  - Inactive customers: {stats['inactive_customers']}")

    return practice_data, dict(stats)


def extract_employees(csv_path: str) -> Tuple[Dict[str, List], Dict]:
    """
    Extract and split employees by practice based on subsidiary

    Returns:
        Tuple of (practice_employees_dict, stats_dict)
    """
    print(f"\n{'='*80}")
    print(f"EXTRACTING EMPLOYEES from {os.path.basename(csv_path)}")
    print(f"{'='*80}")

    practice_data = {practice_id: [] for practice_id in PRACTICE_MAPPING.keys()}
    stats = defaultdict(int)

    with open(csv_path, 'r', encoding='utf-8') as f:
        # Skip metadata rows
        for _ in range(CSV_FILES['employees']['skip_rows']):
            next(f)

        reader = csv.DictReader(f)

        for row in reader:
            stats['total_rows'] += 1

            # Clean field names
            clean_row = {k.strip(): v.strip() for k, v in row.items()}

            # Map subsidiary to practice
            subsidiary = clean_row.get('Subsidiary (no hierarchy)', '')
            practice_id = map_subsidiary_to_practice(subsidiary)

            # Extract email from HTML contact info
            contact_info = clean_row.get('Contact Info', '')
            email = extract_email_from_html(contact_info)

            # Build employee record
            employee = {
                'id': f"employee_{stats['total_rows']}",
                'sync_id': str(uuid.uuid4()),
                'tenant_id': practice_id,
                'raw_data': json.dumps(clean_row),
                'employee_name': clean_row.get('Name', ''),
                'title': clean_row.get('Title', ''),
                'location': clean_row.get('Location (no hierarchy)', ''),
                'department': clean_row.get('Department (no hierarchy)', ''),
                'subsidiary': subsidiary,
                'email': email,
                'is_inactive': clean_row.get('Inactive', 'No').lower() == 'yes',
                'extracted_at': datetime.utcnow().isoformat()
            }

            practice_data[practice_id].append(employee)
            stats[f'practice_{practice_id}'] += 1

            if employee['is_inactive']:
                stats['inactive_employees'] += 1

    print(f"\n✓ Extracted {stats['total_rows']} employee records")
    for practice_id in PRACTICE_MAPPING.keys():
        print(f"  - {PRACTICE_MAPPING[practice_id]['name']}: {stats[f'practice_{practice_id}']} records")
    print(f"  - Inactive employees: {stats['inactive_employees']}")

    return practice_data, dict(stats)


# ============================================================================
# SNOWFLAKE LOADING FUNCTIONS
# ============================================================================

def create_bronze_tables(conn):
    """Create Bronze layer tables if they don't exist"""
    print(f"\n{'='*80}")
    print("CREATING BRONZE LAYER TABLES")
    print(f"{'='*80}")

    cursor = conn.cursor()

    # Create netsuite_employees table (not in original schema)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bronze.netsuite_employees (
            id VARCHAR(50),
            sync_id VARCHAR(36),
            tenant_id VARCHAR(50),
            raw_data VARIANT,
            employee_name VARCHAR(255),
            title VARCHAR(255),
            location VARCHAR(255),
            department VARCHAR(255),
            subsidiary VARCHAR(255),
            email VARCHAR(255),
            is_inactive BOOLEAN,
            extracted_at TIMESTAMP,
            _ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
        )
    """)

    print("✓ Bronze tables verified/created")
    cursor.close()


def load_to_snowflake(conn, table_name: str, practice_data: Dict[str, List], data_type: str):
    """
    Load practice-specific data to Snowflake Bronze layer

    Args:
        conn: Snowflake connection
        table_name: Target table (e.g., 'bronze.netsuite_vendors')
        practice_data: Dictionary of {practice_id: [records]}
        data_type: Type of data being loaded (for reporting)
    """
    print(f"\n{'='*80}")
    print(f"LOADING {data_type.upper()} TO SNOWFLAKE: {table_name}")
    print(f"{'='*80}")

    cursor = conn.cursor()
    total_inserted = 0

    for practice_id, records in practice_data.items():
        if not records:
            continue

        practice_name = PRACTICE_MAPPING[practice_id]['name']
        print(f"\nLoading {len(records)} records for {practice_name}...")

        # Build INSERT statement based on data type
        if data_type == 'transactions':
            insert_sql = """
                INSERT INTO {table} (
                    id, sync_id, tenant_id, raw_data,
                    last_modified_date, extracted_at, is_deleted
                )
                VALUES (%s, %s, %s, PARSE_JSON(%s), %s, %s, FALSE)
            """.format(table=table_name)

            for record in records:
                cursor.execute(insert_sql, (
                    record['id'],
                    record['sync_id'],
                    record['tenant_id'],
                    record['raw_data'],
                    record['transaction_date'],
                    record['extracted_at']
                ))
                total_inserted += 1

        elif data_type == 'vendors':
            insert_sql = """
                INSERT INTO {table} (
                    id, sync_id, tenant_id, raw_data,
                    extracted_at, is_deleted
                )
                VALUES (%s, %s, %s, PARSE_JSON(%s), %s, %s)
            """.format(table=table_name)

            for record in records:
                cursor.execute(insert_sql, (
                    record['id'],
                    record['sync_id'],
                    record['tenant_id'],
                    record['raw_data'],
                    record['extracted_at'],
                    record['is_inactive']
                ))
                total_inserted += 1

        elif data_type == 'customers':
            insert_sql = """
                INSERT INTO {table} (
                    id, sync_id, tenant_id, raw_data,
                    extracted_at, is_deleted
                )
                VALUES (%s, %s, %s, PARSE_JSON(%s), %s, %s)
            """.format(table=table_name)

            for record in records:
                cursor.execute(insert_sql, (
                    record['id'],
                    record['sync_id'],
                    record['tenant_id'],
                    record['raw_data'],
                    record['extracted_at'],
                    record['is_inactive']
                ))
                total_inserted += 1

        elif data_type == 'employees':
            insert_sql = """
                INSERT INTO bronze.netsuite_employees (
                    id, sync_id, tenant_id, raw_data,
                    employee_name, title, location, department,
                    subsidiary, email, is_inactive, extracted_at
                )
                VALUES (%s, %s, %s, PARSE_JSON(%s), %s, %s, %s, %s, %s, %s, %s, %s)
            """.format(table=table_name)

            for record in records:
                cursor.execute(insert_sql, (
                    record['id'],
                    record['sync_id'],
                    record['tenant_id'],
                    record['raw_data'],
                    record['employee_name'],
                    record['title'],
                    record['location'],
                    record['department'],
                    record['subsidiary'],
                    record['email'],
                    record['is_inactive'],
                    record['extracted_at']
                ))
                total_inserted += 1

        print(f"  ✓ Loaded {len(records)} records for {practice_name}")

    conn.commit()
    cursor.close()

    print(f"\n✓ Total {data_type} records inserted: {total_inserted}")
    return total_inserted


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_data_quality(conn):
    """Run data quality checks on loaded data"""
    print(f"\n{'='*80}")
    print("DATA QUALITY VALIDATION")
    print(f"{'='*80}")

    cursor = conn.cursor(DictCursor)

    # Check record counts by practice
    tables = [
        'bronze.netsuite_journal_entries',
        'bronze.netsuite_vendors',
        'bronze.netsuite_customers',
        'bronze.netsuite_employees'
    ]

    for table in tables:
        print(f"\n{table}:")
        cursor.execute(f"""
            SELECT
                tenant_id,
                COUNT(*) as record_count
            FROM {table}
            GROUP BY tenant_id
            ORDER BY tenant_id
        """)

        for row in cursor.fetchall():
            practice_name = PRACTICE_MAPPING.get(row['TENANT_ID'], {}).get('name', row['TENANT_ID'])
            print(f"  - {practice_name}: {row['RECORD_COUNT']:,} records")

    cursor.close()


def generate_summary_report(all_stats: Dict) -> str:
    """Generate summary report of ingestion"""
    lines = []
    lines.append("\n" + "="*80)
    lines.append("INGESTION SUMMARY REPORT")
    lines.append("="*80)
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    for data_type, stats in all_stats.items():
        lines.append(f"\n{data_type.upper()}:")
        lines.append(f"  Total Records: {stats.get('total_rows', 0):,}")

        for practice_id in PRACTICE_MAPPING.keys():
            count = stats.get(f'practice_{practice_id}', 0)
            practice_name = PRACTICE_MAPPING[practice_id]['name']
            lines.append(f"  - {practice_name}: {count:,}")

    lines.append("\n" + "="*80)

    report = "\n".join(lines)
    print(report)
    return report


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    print("\n" + "="*80)
    print("NetSuite Multi-Practice Data Ingestion")
    print("="*80)
    print("\nTarget Practices:")
    for practice_id, info in PRACTICE_MAPPING.items():
        print(f"  {practice_id}: {info['name']} ({info['location']})")

    # Verify backup directory exists
    if not os.path.exists(BACKUP_DIR):
        print(f"\nERROR: Backup directory not found: {BACKUP_DIR}")
        sys.exit(1)

    print(f"\nBackup Directory: {BACKUP_DIR}")

    # Extract data from CSV files
    all_stats = {}

    try:
        # Extract transactions from all 3 practice files
        all_transactions = {practice_id: [] for practice_id in PRACTICE_MAPPING.keys()}
        trans_stats = {'total_rows': 0}

        for file_key in ['transactions_eastlake', 'transactions_torrey', 'transactions_ads']:
            trans_path = os.path.join(BACKUP_DIR, CSV_FILES[file_key]['file'])
            practice_id = CSV_FILES[file_key]['practice']
            skip_rows = CSV_FILES[file_key]['skip_rows']

            print(f"\nExtracting {trans_path}...")
            transactions_data, stats = extract_transactions(trans_path, skip_rows)

            # Merge data from this file
            for pid, records in transactions_data.items():
                if pid == practice_id:  # Only use the target practice from this file
                    all_transactions[pid].extend(records)
                    trans_stats['total_rows'] += len(records)
                    trans_stats[f'practice_{pid}'] = trans_stats.get(f'practice_{pid}', 0) + len(records)

        all_stats['transactions'] = trans_stats

        # Extract vendors
        vendors_path = os.path.join(BACKUP_DIR, CSV_FILES['vendors']['file'])
        vendors_data, vendors_stats = extract_vendors(vendors_path)
        all_stats['vendors'] = vendors_stats

        # Extract customers
        customers_path = os.path.join(BACKUP_DIR, CSV_FILES['customers']['file'])
        customers_data, customers_stats = extract_customers(customers_path)
        all_stats['customers'] = customers_stats

        # Extract employees
        employees_path = os.path.join(BACKUP_DIR, CSV_FILES['employees']['file'])
        employees_data, employees_stats = extract_employees(employees_path)
        all_stats['employees'] = employees_stats

    except FileNotFoundError as e:
        print(f"\nERROR: CSV file not found: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR during extraction: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Connect to Snowflake and load data
    try:
        print(f"\n{'='*80}")
        print("CONNECTING TO SNOWFLAKE")
        print(f"{'='*80}")

        conn = get_snowflake_connection()
        print("✓ Connected to Snowflake")

        # Create tables if needed
        create_bronze_tables(conn)

        # Load data (use the consolidated all_transactions)
        load_to_snowflake(conn, 'bronze.netsuite_journal_entries',
                         all_transactions, 'transactions')
        load_to_snowflake(conn, CSV_FILES['vendors']['table'],
                         vendors_data, 'vendors')
        load_to_snowflake(conn, CSV_FILES['customers']['table'],
                         customers_data, 'customers')
        load_to_snowflake(conn, 'bronze.netsuite_employees',
                         employees_data, 'employees')

        # Validate data quality
        validate_data_quality(conn)

        # Generate summary report
        report = generate_summary_report(all_stats)

        # Save report to file
        report_path = os.path.join(os.path.dirname(__file__),
                                  f'ingestion_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"\n✓ Report saved to: {report_path}")

        conn.close()
        print("\n✓ Ingestion completed successfully!")

    except Exception as e:
        print(f"\nERROR during Snowflake operations: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
