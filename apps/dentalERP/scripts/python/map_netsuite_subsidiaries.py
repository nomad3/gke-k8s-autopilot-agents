#!/usr/bin/env python3
"""
Extract actual NetSuite subsidiary names from CSV files
and create mapping to Operations Report practice codes
"""

import os
import re

csv_files = [f for f in os.listdir('backup') if f.startswith('TransactionDetail-') and f.endswith('.csv')]

print("=" * 80)
print("EXTRACTING NETSUITE SUBSIDIARY NAMES FROM CSV FILES")
print("=" * 80)
print()

subsidiaries = {}

for csv_file in sorted(csv_files):
    filepath = f'backup/{csv_file}'

    with open(filepath, 'r') as f:
        lines = f.readlines()

        # First line has company name
        # Second line has "Parent Company : ... : SCDP <Location>, LLC"
        if len(lines) >= 2:
            parent_line = lines[1].strip().strip('"')

            # Extract subsidiary name (last part after last colon)
            parts = parent_line.split(':')
            if len(parts) > 1:
                subsidiary_name = parts[-1].strip()

                # Map to practice code based on location in name
                practice_code = None
                practice_name = None

                # Parse location from subsidiary name
                if 'Del Sur' in subsidiary_name:
                    practice_code, practice_name = 'dsr', 'Del Sur Dental'
                elif 'Coronado' in subsidiary_name:
                    practice_code, practice_name = 'coronado', 'Coronado Dental'
                elif 'Laguna Hills II' in subsidiary_name:
                    practice_code, practice_name = 'lhd_ii', 'Laguna Hills Dental II'
                elif 'Laguna Hills' in subsidiary_name:
                    practice_code, practice_name = 'lhd', 'Laguna Hills Dental'
                elif 'Temecula' in subsidiary_name:
                    practice_code, practice_name = 'temecula', 'Temecula Dental'
                elif 'Torrey Highlands' in subsidiary_name:
                    practice_code, practice_name = 'th', 'Torrey Highlands Dental'
                elif 'Torrey Pines' in subsidiary_name:
                    practice_code, practice_name = 'efd_i', 'Encinitas Family Dental I'
                elif 'Eastlake' in subsidiary_name:
                    practice_code, practice_name = 'sed', 'Scripps Eastlake Dental'
                elif 'Kearny Mesa' in subsidiary_name:
                    practice_code, practice_name = 'km', 'Kearny Mesa Dental'
                elif 'Vista' in subsidiary_name:
                    practice_code, practice_name = 'vista', 'Vista Dental'
                elif 'Carlsbad' in subsidiary_name:
                    practice_code, practice_name = 'carlsbad', 'Carlsbad Dental'
                elif 'UTC' in subsidiary_name or 'University' in subsidiary_name:
                    practice_code, practice_name = 'ucfd', 'University City Family Dental'
                elif 'Theodosis' in subsidiary_name:
                    practice_code, practice_name = 'theodosis', 'Theodosis Dental'

                if practice_code:
                    subsidiaries[csv_file] = {
                        'file': csv_file,
                        'subsidiary_name': subsidiary_name,
                        'practice_code': practice_code,
                        'practice_name': practice_name
                    }
                else:
                    print(f"  ⚠️  {csv_file}: Could not map '{subsidiary_name}'")

print(f"Found {len(subsidiaries)} subsidiaries:")
print()
print(f"{'File':<35s} {'Practice Code':<15s} {'NetSuite Subsidiary Name'}")
print("-" * 100)

for key, data in sorted(subsidiaries.items()):
    print(f"{data['file']:<35s} {data['practice_code']:<15s} {data['subsidiary_name']}")

print()
print("=" * 80)
print("SQL TO UPDATE PRACTICE_MASTER:")
print("=" * 80)
print()

# Generate SQL UPDATE statements
print("UPDATE gold.practice_master SET")
print("  netsuite_subsidiary_name = CASE practice_id")

for key, data in sorted(subsidiaries.items(), key=lambda x: x[1]['practice_code']):
    print(f"    WHEN '{data['practice_code']}' THEN '{data['subsidiary_name']}'")

print("    ELSE netsuite_subsidiary_name")
print("  END;")

print()
print(f"✅ {len(subsidiaries)} practice-to-subsidiary mappings ready to apply")
