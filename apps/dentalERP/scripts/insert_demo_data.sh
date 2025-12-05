#!/bin/bash
# Insert demo data from CSV into Snowflake for client demo
set -e

echo "=== Loading Demo Data into Snowflake ==="
echo ""
echo "Source: 986 Eastlake journal entries from CSV"
echo "Destination: bronze.netsuite_journal_entries"
echo ""

# Upload JSON file to GCP VM
echo "Step 1: Uploading data to GCP..."
gcloud compute scp /tmp/journal_entries_for_bronze.json dental-erp-vm:/tmp/ --zone=us-central1-a

# Insert into Snowflake
echo ""
echo "Step 2: Inserting into Snowflake Bronze layer..."

gcloud compute ssh dental-erp-vm --zone=us-central1-a --command="
cd /opt/dental-erp && python3 << 'PYEOF'
import json
import snowflake.connector
import os

# Load journal entries
with open('/tmp/journal_entries_for_bronze.json') as f:
    entries = json.load(f)

print(f'Loading {len(entries)} journal entries...')

# Get Snowflake credentials from .env
env = {}
with open('.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            env[k] = v

# Connect to Snowflake
conn = snowflake.connector.connect(
    account=env['SNOWFLAKE_ACCOUNT'],
    user=env['SNOWFLAKE_USER'],
    password=env['SNOWFLAKE_PASSWORD'],
    warehouse='COMPUTE_WH',
    database='DENTAL_ERP_DW',
    schema='BRONZE'
)

cursor = conn.cursor()

# Truncate existing data
cursor.execute('TRUNCATE TABLE bronze.netsuite_journal_entries')
print('✅ Cleaned existing data')

# Insert journal entries
inserted = 0
for entry in entries:
    try:
        cursor.execute('''
            INSERT INTO bronze.netsuite_journal_entries
            (id, subsidiary_id, sync_id, tenant_id, raw_data, extracted_at, is_deleted)
            VALUES (%s, %s, %s, %s, PARSE_JSON(%s), %s, %s)
        ''', (
            entry['id'],
            entry['subsidiary']['id'],
            'csv_demo_seed',
            'cc5c0900-ae80-4004-8381-4629b2031ed9',
            json.dumps(entry),
            '2025-11-13T18:00:00',
            False
        ))
        inserted += 1

        if inserted % 100 == 0:
            print(f'  Inserted {inserted}/{len(entries)}...')

    except Exception as e:
        print(f'Error inserting {entry[\"id\"]}: {e}')

conn.commit()
conn.close()

print(f'\n✅ Inserted {inserted} journal entries into Snowflake!')
PYEOF
"

echo ""
echo "Step 3: Verifying data..."
gcloud compute ssh dental-erp-vm --zone=us-central1-a --command="
cd /opt/dental-erp && python3 << 'PYEOF'
import snowflake.connector
import os

env = {}
with open('.env') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            k, v = line.strip().split('=', 1)
            env[k] = v

conn = snowflake.connector.connect(
    account=env['SNOWFLAKE_ACCOUNT'],
    user=env['SNOWFLAKE_USER'],
    password=env['SNOWFLAKE_PASSWORD'],
    warehouse='COMPUTE_WH',
    database='DENTAL_ERP_DW',
    schema='BRONZE'
)

cursor = conn.cursor()

# Count records
cursor.execute('SELECT COUNT(*) FROM bronze.netsuite_journal_entries')
count = cursor.fetchone()[0]

print(f'\n✅ Total records in Bronze: {count}')

# Sample
cursor.execute('SELECT id, raw_data:tranId, _ingestion_timestamp FROM bronze.netsuite_journal_entries LIMIT 3')
print(f'\nSample records:')
for row in cursor:
    print(f'  - ID: {row[0]}, TranID: {row[1]}, Ingested: {row[2]}')

conn.close()
PYEOF
"

echo ""
echo "✅ Demo data loaded successfully!"
echo ""
echo "Next steps:"
echo "  1. Run dbt transformations"
echo "  2. Test analytics APIs"
echo "  3. View in frontend dashboard"
