#!/usr/bin/env python3
"""Analyze all 14 practice sheets to understand layout variations"""

import pandas as pd

excel_file = 'examples/ingestion/Operations Report(28).xlsx'
xl_file = pd.ExcelFile(excel_file)

practice_sheets = [s for s in xl_file.sheet_names if s != 'Operating Metrics']

print("=" * 80)
print("OPERATIONS REPORT SHEET LAYOUT ANALYSIS")
print("=" * 80)
print()

for sheet_name in practice_sheets:
    print(f"\n📄 {sheet_name}")
    print("-" * 80)

    df = pd.read_excel(excel_file, sheet_name=sheet_name)

    # Find where metrics start (look for common labels in column 1)
    metric_labels = []
    for idx in range(100):
        if idx >= len(df):
            break
        val = str(df.iloc[idx, 1]).strip() if pd.notna(df.iloc[idx, 1]) else ''
        if val and val not in ['nan', '']:
            if any(keyword in val.upper() for keyword in ['PRODUCTION', 'VISITS', 'PATIENTS', 'HYGIENE', 'COLLECTION']):
                metric_labels.append((idx, val))

    print(f"   Key metric rows found: {len(metric_labels)}")
    for row_idx, label in metric_labels[:10]:
        print(f"      Row {row_idx:3d}: {label}")

    # Check date row (usually row 4)
    date_row = df.iloc[4]
    dates_found = sum(1 for val in date_row if pd.notna(val))
    print(f"   Date columns (row 4): {dates_found}")

print()
print("=" * 80)
print("💡 INSIGHT: Each sheet has metrics at different row positions")
print("   Need flexible parser that searches for metric labels, not fixed rows")
