#!/usr/bin/env python3
"""
Test script for NetSuite SuiteQL fix
Tests the corrected SuiteQL syntax to bypass the broken User Event Script
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

# Add the mcp-server directory to Python path
import sys
sys.path.insert(0, '/Users/nomade/Documents/GitHub/dentalERP/mcp-server/src')

from connectors.netsuite import NetSuiteConnector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_suiteql():
    """Test the SuiteQL query fix"""

    # Load environment variables
    load_dotenv('/Users/nomade/Documents/GitHub/dentalERP/mcp-server/.env')

    # Initialize NetSuite connector
    config = {
        'account_id': os.getenv('NETSUITE_ACCOUNT_ID'),
        'consumer_key': os.getenv('NETSUITE_CONSUMER_KEY'),
        'consumer_secret': os.getenv('NETSUITE_CONSUMER_SECRET'),
        'token_id': os.getenv('NETSUITE_TOKEN_ID'),
        'token_secret': os.getenv('NETSUITE_TOKEN_SECRET'),
        'base_url': f"https://{os.getenv('NETSUITE_ACCOUNT_ID').replace('_', '-').lower()}.suitetalk.api.netsuite.com"
    }

    logger.info("Initializing NetSuite connector...")
    connector = NetSuiteConnector(config)

    try:
        # Test 1: Simple SuiteQL query for journal entries
        logger.info("=" * 60)
        logger.info("TEST 1: Testing basic SuiteQL query")
        logger.info("-" * 60)

        # This is the corrected query
        test_query = """
            SELECT
                t.id,
                t.tranid,
                t.trandate,
                t.subsidiary,
                BUILTIN.DF(t.status) AS status,
                t.memo
            FROM transaction t
            WHERE t.type = 'Journal'
            ORDER BY t.trandate DESC
            LIMIT 5
        """

        logger.info("Executing SuiteQL query...")
        logger.info(f"Query: {test_query}")

        result = await connector._make_suiteql_request(test_query)

        if result:
            logger.info(f"✅ SuiteQL query successful!")
            logger.info(f"Response keys: {result.keys() if result else 'None'}")
            if 'items' in result:
                logger.info(f"Found {len(result['items'])} journal entries")
                if result['items']:
                    logger.info(f"First entry: {result['items'][0]}")
        else:
            logger.error("❌ SuiteQL query failed - no result returned")

        # Test 2: Test the full journal entry sync with SuiteQL
        logger.info("=" * 60)
        logger.info("TEST 2: Testing full journal entry sync via SuiteQL")
        logger.info("-" * 60)

        journal_entries = await connector._fetch_journal_entries_via_suiteql(limit=3)

        if journal_entries:
            logger.info(f"✅ Successfully fetched {len(journal_entries)} journal entries with line items")
            for i, entry in enumerate(journal_entries[:1], 1):  # Show first entry details
                logger.info(f"\nJournal Entry {i}:")
                logger.info(f"  ID: {entry.get('id')}")
                logger.info(f"  Transaction ID: {entry.get('tranId')}")
                logger.info(f"  Date: {entry.get('tranDate')}")
                logger.info(f"  Subsidiary: {entry.get('subsidiary', {}).get('id')}")
                logger.info(f"  Number of lines: {len(entry.get('line', []))}")
                if entry.get('line'):
                    logger.info(f"  First line: {entry['line'][0]}")
        else:
            logger.error("❌ Failed to fetch journal entries via SuiteQL")

        logger.info("=" * 60)
        logger.info("TEST COMPLETE")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Close the session
        if hasattr(connector, 'session') and connector.session:
            await connector.session.close()

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_suiteql())