#!/usr/bin/env python3
"""
Fetch ALL subsidiaries from NetSuite API using SuiteQL
Gets current list with IDs and names to update practice_master mappings
"""

import os
import sys
import json

# Add mcp-server to path
sys.path.insert(0, 'mcp-server')

# Set up environment
from dotenv import load_dotenv
load_dotenv('mcp-server/.env')

# Import after env loaded
from src.connectors.netsuite import NetSuiteConnector

# Create connector with credentials from .env
connector = NetSuiteConnector()

print("=" * 80)
print("FETCHING ALL SUBSIDIARIES FROM NETSUITE API")
print("=" * 80)
print()

try:
    # Query all active subsidiaries
    query = """
        SELECT
            id,
            name,
            legalName,
            country,
            state,
            city,
            isInactive
        FROM subsidiary
        ORDER BY id
    """

    print(f"Executing SuiteQL query...")
    print(f"Query: {query}")
    print()

    results = connector.execute_suiteql(query)

    if results:
        print(f"✅ Found {len(results)} subsidiaries in NetSuite:")
        print()
        print(f"{'ID':<6s} {'Name':<50s} {'Legal Name':<40s} {'Location'}")
        print("-" * 140)

        for sub in results:
            sub_id = sub.get('id', 'N/A')
            name = sub.get('name', 'N/A')
            legal = sub.get('legalName', 'N/A')
            city = sub.get('city', '')
            state = sub.get('state', '')
            location = f"{city}, {state}" if city or state else ''
            inactive = sub.get('isInactive', False)

            status = '(inactive)' if inactive else ''
            print(f"{sub_id:<6s} {name:<50s} {legal:<40s} {location} {status}")

        # Save to file for reference
        with open('/tmp/netsuite_subsidiaries.json', 'w') as f:
            json.dump(results, f, indent=2)

        print()
        print(f"✅ Saved to /tmp/netsuite_subsidiaries.json")
        print()
        print("=" * 80)
        print("NEXT STEPS:")
        print("=" * 80)
        print("1. Map these NetSuite subsidiary names to practice_master")
        print("2. Update netsuite_subsidiary_name for each practice_id")
        print("3. Refresh unified view to join financial data")

    else:
        print("⚠️  No subsidiaries returned from NetSuite")

except Exception as e:
    print(f"❌ Error calling NetSuite API: {e}")
    print(f"\nError details: {type(e).__name__}")
    import traceback
    traceback.print_exc()
