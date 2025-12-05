#!/usr/bin/env python3
"""
Test NetSuite SuiteQL queries directly to diagnose why they return 0 records
"""

import asyncio
import sys
sys.path.insert(0, 'mcp-server/src')

from connectors.netsuite import NetSuiteConnector
import os
from dotenv import load_dotenv

load_dotenv('mcp-server/.env')

async def test_suiteql():
    # Initialize NetSuite connector
    netsuite = NetSuiteConnector(
        account=os.getenv('NETSUITE_ACCOUNT_ID'),
        consumer_key=os.getenv('NETSUITE_CONSUMER_KEY'),
        consumer_secret=os.getenv('NETSUITE_CONSUMER_SECRET'),
        token_key=os.getenv('NETSUITE_TOKEN_ID'),
        token_secret=os.getenv('NETSUITE_TOKEN_SECRET')
    )

    print("=" * 80)
    print("TESTING NETSUITE SUITEQL QUERIES")
    print("=" * 80)
    print()

    # Test 1: Simple query with no filters
    print("Test 1: Query transaction table with no filters (WHERE 1=1)")
    query1 = """
        SELECT t.id, t.tranid, t.trandate, t.subsidiary
        FROM transaction t
        WHERE 1=1
        ORDER BY t.trandate DESC
    """

    result1 = await netsuite._make_suiteql_request(query1, limit=5, offset=0)
    if result1 and 'items' in result1:
        print(f"✅ Returned {len(result1['items'])} records")
        if result1['items']:
            print(f"   Sample: {result1['items'][0]}")
    else:
        print(f"❌ No data returned: {result1}")

    print()

    # Test 2: Query without WHERE clause
    print("Test 2: Query without WHERE clause")
    query2 = """
        SELECT t.id, t.tranid, t.trandate
        FROM transaction t
        ORDER BY t.trandate DESC
    """

    result2 = await netsuite._make_suiteql_request(query2, limit=5, offset=0)
    if result2 and 'items' in result2:
        print(f"✅ Returned {len(result2['items'])} records")
    else:
        print(f"❌ No data returned: {result2}")

    print()

    # Test 3: Check if table name is correct
    print("Test 3: Try 'transactions' (plural) instead of 'transaction'")
    query3 = """
        SELECT t.id
        FROM transactions t
    """

    result3 = await netsuite._make_suiteql_request(query3, limit=5, offset=0)
    if result3 and 'items' in result3:
        print(f"✅ Returned {len(result3['items'])} records - transactions (plural) works!")
    else:
        print(f"❌ No data: {result3}")

    print()

    # Test 4: Check transactionline table
    print("Test 4: Query transactionline table")
    query4 = """
        SELECT tl.transaction, tl.account, tl.amount
        FROM transactionline tl
    """

    result4 = await netsuite._make_suiteql_request(query4, limit=5, offset=0)
    if result4 and 'items' in result4:
        print(f"✅ Returned {len(result4['items'])} records")
        if result4['items']:
            print(f"   Sample: {result4['items'][0]}")
    else:
        print(f"❌ No data: {result4}")

if __name__ == "__main__":
    asyncio.run(test_suiteql())
