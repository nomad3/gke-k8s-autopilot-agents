#!/usr/bin/env python3
"""
Simple Direct CSV to Snowflake Loader
Loads the already-mapped transaction CSV files directly to Bronze layer
"""
import csv
import os
import sys
import json
from datetime import datetime
from decimal import Decimal

try:
    import snowflake.connector
except ImportError:
    print("ERROR: pip install snowflake-connector-python")
    sys.exit(1)

# Configuration
BACKUP_DIR = os.path.join(os.path.dirname(__file__), '..', 'backup')

FILES = [
    ('TransactionDetail_eastlake_mapped.csv', 'eastlake'),
    ('TransactionDetail_torrey_pines_mapped.csv', 'torrey_pines'),
    ('TransactionDetail_ads_mapped.csv', 'ads')
]

# Snowflake connection from environment
conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    database=os.getenv('SNOWFLAKE_DATABASE'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE')
)

cursor = conn.cursor()

# Table already exists with schema: id, sync_id, tenant_id, raw_data, last_modified_date, extracted_at, is_deleted
# We'll use the standard Bronze schema

total_loaded = 0

for csv_file, practice_id in FILES:
    csv_path = os.path.join(BACKUP_DIR, csv_file)
    print(f"\nLoading {csv_file} for {practice_id}...")

    with open(csv_path, 'r', encoding='utf-8') as f:
        # Skip header rows
        for _ in range(6):
            next(f)

        reader = csv.DictReader(f)
        batch = []

        for row in reader:
            # Clean field names
            clean_row = {k.strip(): v.strip() for k, v in row.items()}

            # Parse date
            try:
                date_str = clean_row.get('Date', '').split('T')[0]
                trans_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except:
                continue

            # Parse amount
            try:
                amount_str = clean_row.get('Amount', '0')
                amount = float(amount_str.replace(',', ''))
            except:
                amount = 0.0

            # Create record matching Bronze schema
            record = (
                f"{practice_id}_{clean_row.get('Document Number', '')}_{len(batch)}",  # id
                f"csv_load_{datetime.now().strftime('%Y%m%d')}",  # sync_id
                practice_id,  # tenant_id
                json.dumps(clean_row),  # raw_data
                datetime.now(),  # last_modified_date
                datetime.now(),  # extracted_at
                False  # is_deleted
            )

            batch.append(record)

            # Insert in batches of 500
            if len(batch) >= 500:
                for rec in batch:
                    cursor.execute("""
                        INSERT INTO bronze.netsuite_journal_entries
                        (id, sync_id, tenant_id, raw_data, last_modified_date, extracted_at, is_deleted)
                        SELECT %s, %s, %s, PARSE_JSON(%s), %s, %s, %s
                    """, rec)
                conn.commit()
                total_loaded += len(batch)
                print(f"  Loaded {total_loaded} records...")
                batch = []

        # Load remaining
        if batch:
            for rec in batch:
                cursor.execute("""
                    INSERT INTO bronze.netsuite_journal_entries
                    (id, sync_id, tenant_id, raw_data, last_modified_date, extracted_at, is_deleted)
                    SELECT %s, %s, %s, PARSE_JSON(%s), %s, %s, %s
                """, rec)
            conn.commit()
            total_loaded += len(batch)

    print(f"✓ Loaded {csv_file}: {total_loaded} total records")

conn.commit()
cursor.close()
conn.close()

print(f"\n✅ SUCCESS: Loaded {total_loaded} transactions to Snowflake!")
print(f"   Query: SELECT COUNT(*) FROM bronze.netsuite_journal_entries;")
