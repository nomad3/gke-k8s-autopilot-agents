#!/usr/bin/env python3
"""
Test transaction data availability for ALL subsidiaries (1-24)
Find which subsidiaries actually have transaction data
"""

import os
import sys
sys.path.insert(0, 'mcp-server/src')

import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv('mcp-server/.env')

# Import our NetSuite connector
from connectors.netsuite import NetSuiteConnector

async def test_all_subsidiaries():
    # Initialize NetSuite connector with existing OAuth 1.0a credentials
    netsuite = NetSuiteConnector(
        account=os.getenv('NETSUITE_ACCOUNT_ID'),
        consumer_key=os.getenv('NETSUITE_CONSUMER_KEY'),
        consumer_secret=os.getenv('NETSUITE_CONSUMER_SECRET'),
        token_key=os.getenv('NETSUITE_TOKEN_ID'),
        token_secret=os.getenv('NETSUITE_TOKEN_SECRET')
    )

    print("=" * 100)
    print("TESTING TRANSACTION DATA FOR ALL SUBSIDIARIES (1-24)")
    print("=" * 100)
    print()

    subsidiary_ids = list(range(1, 25))  # 1 to 24
    results = {}

    for sub_id in subsidiary_ids:
        print(f"Testing Subsidiary {sub_id}...")

        # Build simple SuiteQL query for this subsidiary
        query = f"""
            SELECT COUNT(*) as txn_count
            FROM transaction t
            WHERE t.subsidiary = '{sub_id}'
            AND t.trandate >= TO_DATE('2025-01-01', 'YYYY-MM-DD')
        """

        try:
            response = await netsuite._make_suiteql_request(query, limit=1, offset=0)

            if response and 'items' in response and len(response['items']) > 0:
                count = response['items'][0].get('TXN_COUNT', 0)
                results[sub_id] = count

                if count > 0:
                    print(f"  ✅ Subsidiary {sub_id}: {count:>6,} transactions")
                else:
                    print(f"  ⚠️  Subsidiary {sub_id}: 0 transactions")
            else:
                results[sub_id] = 0
                print(f"  ❌ Subsidiary {sub_id}: No data returned")

        except Exception as e:
            results[sub_id] = -1
            print(f"  ❌ Subsidiary {sub_id}: Error - {str(e)[:50]}")

        # Rate limit
        await asyncio.sleep(0.5)

    print()
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print()

    subsidiaries_with_data = [sid for sid, count in results.items() if count > 0]
    subsidiaries_with_no_data = [sid for sid, count in results.items() if count == 0]
    subsidiaries_with_errors = [sid for sid, count in results.items() if count < 0]

    print(f"Subsidiaries WITH transaction data: {subsidiaries_with_data}")
    print(f"Subsidiaries with NO data: {subsidiaries_with_no_data}")
    print(f"Subsidiaries with errors: {subsidiaries_with_errors}")
    print()

    total_transactions = sum([c for c in results.values() if c > 0])
    print(f"✅ Total transactions found: {total_transactions:,}")

    if subsidiaries_with_data:
        print()
        print("🎯 NEXT STEP: Query these subsidiaries for full transaction details:")
        for sid in subsidiaries_with_data:
            print(f"   Subsidiary {sid}: {results[sid]:,} transactions")

if __name__ == "__main__":
    asyncio.run(test_all_subsidiaries())
