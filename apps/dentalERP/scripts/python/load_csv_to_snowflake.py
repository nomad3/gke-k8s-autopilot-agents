#!/usr/bin/env python3
"""
Load Transaction Detail CSVs directly into Snowflake Bronze layer
Creates sample journal entries for client demo
"""

import csv
import json
import sys
from collections import defaultdict
from datetime import datetime
import uuid

def parse_csv_to_journal_entries(csv_file, location, subsidiary_id):
    """Parse CSV into journal entry format for Bronze layer"""

    entries_by_doc = defaultdict(list)

    with open(csv_file) as f:
        lines = f.readlines()

        # Find header row
        header_idx = None
        for i, line in enumerate(lines):
            if 'Type,Date,Document Number' in line:
                header_idx = i
                break

        if header_idx is None:
            print(f"ERROR: No header found in {csv_file}")
            return []

        # Parse from header onwards
        reader = csv.DictReader(lines[header_idx:])

        for row in reader:
            row_type = row.get('Type', '').strip()
            doc_num = row.get('Document Number', '').strip()

            # Only process Journal entries with document numbers
            if row_type == 'Journal' and doc_num:
                entries_by_doc[doc_num].append(row)

    print(f"{location}: {len(entries_by_doc)} unique journal entries, {sum(len(v) for v in entries_by_doc.values())} line items")

    # Convert to Bronze schema
    journal_entries = []

    for doc_num, lines in entries_by_doc.items():
        first_line = lines[0]

        # Build line items
        line_items = []
        for line in lines:
            try:
                amount = float(line.get('Amount', 0) or 0)
            except:
                amount = 0

            line_items.append({
                'account': {
                    'name': line.get('Account', ''),
                    'accountNumber': ''
                },
                'debit': amount if amount > 0 else 0,
                'credit': -amount if amount < 0 else 0,
                'entity': line.get('Name', ''),
                'memo': line.get('Memo', '')
            })

        # Create journal entry
        entry = {
            'id': f'{location}_{doc_num}',
            'tranId': doc_num,
            'tranDate': first_line.get('Date', '')[:10] if first_line.get('Date') else '2025-01-01',
            'subsidiary': {
                'id': subsidiary_id,
                'name': location
            },
            'status': {'name': 'Approved'},
            'memo': f'{location} - {doc_num}',
            'line': line_items
        }

        journal_entries.append(entry)

    return journal_entries

# Parse all 3 CSVs
print("=== Loading Transaction Detail CSVs ===\n")

csv_mappings = [
    ('/Users/nomade/Documents/GitHub/dentalERP/backup/TransactionDetail_eastlake_mapped.csv', 'Eastlake', '6'),
    ('/Users/nomade/Documents/GitHub/dentalERP/backup/TransactionDetail_torrey_pines_mapped.csv', 'Torrey Pines', '10'),
    ('/Users/nomade/Documents/GitHub/dentalERP/backup/TransactionDetail_ads_mapped.csv', 'ADS', '11')
]

all_entries = []

for csv_file, location, sub_id in csv_mappings:
    entries = parse_csv_to_journal_entries(csv_file, location, sub_id)
    all_entries.extend(entries)

print(f"\n✅ Total journal entries ready: {len(all_entries)}")

# Save to JSON for upload
output_file = '/tmp/journal_entries_for_bronze.json'
with open(output_file, 'w') as f:
    json.dump(all_entries, f, indent=2)

print(f"📄 Saved to: {output_file}")
print(f"\nSample entry:")
if all_entries:
    print(json.dumps(all_entries[0], indent=2))
