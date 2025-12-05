#!/usr/bin/env python3
"""
Seed Snowflake Bronze layer with CSV journal entries for client demo
Loads Transaction Detail CSVs directly into bronze.netsuite_journal_entries
"""

import json
import os
import sys

# Load the parsed journal entries
with open('/tmp/journal_entries_for_bronze.json') as f:
    journal_entries = json.load(f)

print(f"=== Seeding Snowflake with {len(journal_entries)} Journal Entries ===\n")

# Prepare data for Bronze schema
bronze_records = []

for entry in journal_entries:
    bronze_record = {
        'ID': entry['id'],
        'SUBSIDIARY_ID': entry['subsidiary']['id'],
        'SYNC_ID': 'csv_seed_demo',
        'TENANT_ID': 'cc5c0900-ae80-4004-8381-4629b2031ed9',  # silvercreek
        'RAW_DATA': json.dumps(entry),
        'LAST_MODIFIED_DATE': None,
        'EXTRACTED_AT': '2025-11-13T18:00:00',
        'IS_DELETED': False
    }
    bronze_records.append(bronze_record)

print(f"✅ Prepared {len(bronze_records)} records for Bronze layer")
print(f"\nSample record:")
print(json.dumps(bronze_records[0], indent=2))

# Save for upload
with open('/tmp/bronze_seed_data.json', 'w') as f:
    json.dumps(bronze_records, f, indent=2)

print(f"\n📄 Bronze records saved to: /tmp/bronze_seed_data.json")
print(f"\nNext: Upload to Snowflake using MCP API or direct insertion")
