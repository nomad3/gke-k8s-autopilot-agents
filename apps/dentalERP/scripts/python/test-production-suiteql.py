#!/usr/bin/env python3
"""
Test script for NetSuite SuiteQL fix in production
Tests the corrected SuiteQL syntax against the production MCP server
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_mcp_server():
    """Test NetSuite sync via MCP Server API"""

    # Production MCP Server configuration
    mcp_url = "https://mcp.agentprovision.com"
    api_key = "dev-mcp-api-key-change-in-production-min-32-chars"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Tenant-ID": "default",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        try:
            # Test 1: Check MCP Server health
            logger.info("=" * 60)
            logger.info("TEST 1: MCP Server Health Check")
            logger.info("-" * 60)

            async with session.get(f"{mcp_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ MCP Server is healthy: {data}")
                else:
                    logger.error(f"❌ MCP Server health check failed: {response.status}")
                    return

            # Test 2: Check NetSuite connection status
            logger.info("=" * 60)
            logger.info("TEST 2: NetSuite Connection Status")
            logger.info("-" * 60)

            async with session.post(
                f"{mcp_url}/api/v1/netsuite/sync/test-connection",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ NetSuite connection successful: {data}")
                else:
                    text = await response.text()
                    logger.warning(f"⚠️ NetSuite connection test returned {response.status}: {text}")

            # Test 3: Trigger journal entry sync with SuiteQL
            logger.info("=" * 60)
            logger.info("TEST 3: Trigger Journal Entry Sync (using SuiteQL)")
            logger.info("-" * 60)

            sync_payload = {
                "record_types": ["journalEntry"],
                "limit": 5,
                "full_sync": False
            }

            logger.info(f"Triggering sync with payload: {json.dumps(sync_payload, indent=2)}")

            async with session.post(
                f"{mcp_url}/api/v1/netsuite/sync/trigger",
                headers=headers,
                json=sync_payload
            ) as response:
                if response.status in [200, 202]:
                    data = await response.json()
                    logger.info(f"✅ Sync triggered successfully!")
                    logger.info(f"Response: {json.dumps(data, indent=2)}")

                    # Store sync_id if available
                    sync_id = data.get('sync_id') or data.get('id')

                    # Wait a moment for sync to progress
                    await asyncio.sleep(5)

                    # Test 4: Check sync status
                    logger.info("=" * 60)
                    logger.info("TEST 4: Check Sync Status")
                    logger.info("-" * 60)

                    status_url = f"{mcp_url}/api/v1/netsuite/sync/status"
                    if sync_id:
                        status_url += f"?sync_id={sync_id}"

                    async with session.get(status_url, headers=headers) as status_response:
                        if status_response.status == 200:
                            status_data = await status_response.json()
                            logger.info(f"Sync status: {json.dumps(status_data, indent=2)}")

                            if status_data.get('status') == 'completed':
                                logger.info(f"✅ Sync completed successfully!")
                                if 'records_synced' in status_data:
                                    logger.info(f"Records synced: {status_data['records_synced']}")
                            elif status_data.get('status') == 'failed':
                                logger.error(f"❌ Sync failed: {status_data.get('error')}")
                            else:
                                logger.info(f"⏳ Sync in progress: {status_data.get('status')}")
                        else:
                            text = await status_response.text()
                            logger.error(f"❌ Failed to get sync status: {text}")
                else:
                    text = await response.text()
                    logger.error(f"❌ Failed to trigger sync: {response.status}")
                    logger.error(f"Response: {text}")

            # Test 5: Query financial summary to see if data was loaded
            logger.info("=" * 60)
            logger.info("TEST 5: Query Financial Summary (verify data in Snowflake)")
            logger.info("-" * 60)

            async with session.get(
                f"{mcp_url}/api/v1/analytics/financial/summary",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Financial data retrieved:")
                    logger.info(json.dumps(data, indent=2, default=str))
                else:
                    text = await response.text()
                    logger.warning(f"⚠️ No financial data yet: {text}")

            logger.info("=" * 60)
            logger.info("TEST COMPLETE")
            logger.info("=" * 60)
            logger.info("")
            logger.info("Summary:")
            logger.info("- MCP Server is accessible")
            logger.info("- NetSuite sync has been triggered")
            logger.info("- SuiteQL fix should now allow journal entries to be fetched")
            logger.info("- Check the MCP Server logs for detailed sync progress")
            logger.info("")
            logger.info("Next steps:")
            logger.info("1. Wait for sync to complete (may take a few minutes)")
            logger.info("2. Check Snowflake for new journal entry records")
            logger.info("3. Verify line items are included in the synced data")

        except Exception as e:
            logger.error(f"❌ Test failed with error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_mcp_server())