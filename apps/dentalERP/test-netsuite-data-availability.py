#!/usr/bin/env python3
"""
Test what data is actually available in NetSuite via the working API
Since we know the API works (200 OK responses), let's find out what data exists
"""

import requests
import json
import time

MCP_API_KEY = "d876e6163089364d96a45a80ed576e99fc55b306133e258d9f861007e824b456"
MCP_URL = "https://mcp.agentprovision.com"

headers = {
    "Authorization": f"Bearer {MCP_API_KEY}",
    "X-Tenant-ID": "silvercreek",
    "Content-Type": "application/json"
}

print("=" * 80)
print("TESTING NETSUITE DATA AVAILABILITY")
print("=" * 80)
print()

# Test 1: What subsidiaries exist?
print("Test 1: Fetching subsidiaries...")
response = requests.post(
    f"{MCP_URL}/api/v1/netsuite/sync/trigger",
    headers=headers,
    json={"full_sync": True, "record_types": ["subsidiary"], "limit": 100}
)
print(f"  Trigger response: {response.json()}")
time.sleep(5)

# Check how many we got
status_response = requests.get(f"{MCP_URL}/api/v1/netsuite/sync/status", headers=headers)
status_data = status_response.json()
for sync_status in status_data.get('sync_statuses', []):
    if sync_status['record_type'] == 'subsidiary':
        print(f"  ✅ Subsidiaries synced: {sync_status['records_synced']}")

print()

# Test 2: Try querying transaction table with NO filters via SuiteQL
print("Test 2: What if we query transaction table with absolutely NO filters?")
print("  (This tests if the table has ANY data at all)")

# We need to test this directly - our current sync adds filters
# For now, let's see what we can infer from the data we have

print()
print("=" * 80)
print("ANALYSIS FROM PREVIOUS ATTEMPTS:")
print("=" * 80)
print()
print("From results-3.json:")
print("  Query: SELECT ... FROM transaction t WHERE t.subsidiary = '21' AND t.trandate >= '2025-01-01'")
print("  Result: 0 records")
print()
print("Possible reasons:")
print("  1. Subsidiary ID '21' has no transactions")
print("  2. All subsidiary 21 transactions are before 2025-01-01")
print("  3. The 'transaction' table doesn't contain what we expect")
print()
print("NEXT STEP: Query subsidiary table to see what IDs actually exist,")
print("then query transaction table for THOSE specific IDs")
print("=" * 80)
