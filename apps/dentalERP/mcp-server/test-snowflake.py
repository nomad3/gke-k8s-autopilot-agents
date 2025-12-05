#!/usr/bin/env python3
"""
Snowflake Connection Test Script

Tests the Snowflake integration for MCP Server
Run this script to verify your Snowflake credentials are configured correctly
"""

import asyncio
import sys
from datetime import datetime

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")


def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")


def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")


def print_info(msg):
    print(f"{BLUE}ℹ️  {msg}{RESET}")


def print_header(msg):
    print(f"\n{BLUE}{'='*60}")
    print(f"{msg}")
    print(f"{'='*60}{RESET}\n")


async def test_configuration():
    """Test if Snowflake is configured"""
    print_header("1. Testing Configuration")

    try:
        from src.core.config import settings

        print_info(f"Environment: {settings.environment}")
        print_info(f"Debug mode: {settings.debug}")

        # Check if Snowflake credentials are set
        required_settings = {
            'SNOWFLAKE_ACCOUNT': settings.snowflake_account,
            'SNOWFLAKE_USER': settings.snowflake_user,
            'SNOWFLAKE_PASSWORD': '***' if settings.snowflake_password else None,
            'SNOWFLAKE_WAREHOUSE': settings.snowflake_warehouse,
            'SNOWFLAKE_DATABASE': settings.snowflake_database,
        }

        all_set = True
        for key, value in required_settings.items():
            if value:
                print_success(f"{key}: {value}")
            else:
                print_error(f"{key}: NOT SET")
                all_set = False

        if all_set:
            print_success("All required Snowflake settings are configured")
            return True
        else:
            print_error("Some Snowflake settings are missing. Check your .env file.")
            return False

    except Exception as e:
        print_error(f"Configuration test failed: {e}")
        return False


async def test_connector_import():
    """Test if Snowflake connector can be imported"""
    print_header("2. Testing Snowflake Connector Import")

    try:
        import snowflake.connector
        print_success(f"snowflake-connector-python is installed (version: {snowflake.connector.__version__})")

        from src.connectors.snowflake import get_snowflake_connector
        connector = get_snowflake_connector()
        print_success("Snowflake connector module imported successfully")

        return connector

    except ImportError as e:
        print_error("snowflake-connector-python is not installed")
        print_warning("Install it with: pip install snowflake-connector-python")
        return None
    except Exception as e:
        print_error(f"Failed to import Snowflake connector: {e}")
        return None


async def test_connection(connector):
    """Test Snowflake connection"""
    print_header("3. Testing Snowflake Connection")

    if not connector:
        print_error("Connector not available")
        return False

    if not connector.is_enabled:
        print_error("Snowflake is not enabled (credentials not configured)")
        return False

    print_info("Attempting to connect to Snowflake...")

    try:
        is_connected = await connector.test_connection()

        if is_connected:
            print_success("Successfully connected to Snowflake!")
            return True
        else:
            print_error("Connection test failed")
            print_warning("Check your credentials and network connection")
            return False

    except Exception as e:
        print_error(f"Connection failed: {e}")
        print_warning("Common issues:")
        print_warning("  - Incorrect account identifier format")
        print_warning("  - Wrong username or password")
        print_warning("  - Warehouse is suspended")
        print_warning("  - Network/firewall issues")
        return False


async def test_query_execution(connector):
    """Test query execution"""
    print_header("4. Testing Query Execution")

    if not connector or not connector.is_enabled:
        print_warning("Skipping query test (connector not available)")
        return False

    try:
        print_info("Executing test query: SELECT CURRENT_VERSION()")

        results = await connector.execute_query("SELECT CURRENT_VERSION() as version")

        if results:
            version = results[0].get('VERSION', 'unknown')
            print_success(f"Query executed successfully! Snowflake version: {version}")
            return True
        else:
            print_error("Query returned no results")
            return False

    except Exception as e:
        print_error(f"Query execution failed: {e}")
        return False


async def test_warehouse_info(connector):
    """Get warehouse information"""
    print_header("5. Getting Warehouse Information")

    if not connector or not connector.is_enabled:
        print_warning("Skipping warehouse info (connector not available)")
        return False

    try:
        print_info("Fetching warehouse details...")

        query = """
        SELECT
            CURRENT_WAREHOUSE() as warehouse,
            CURRENT_DATABASE() as database,
            CURRENT_SCHEMA() as schema,
            CURRENT_USER() as user,
            CURRENT_ROLE() as role,
            CURRENT_REGION() as region
        """

        results = await connector.execute_query(query)

        if results:
            info = results[0]
            print_success("Warehouse Information:")
            for key, value in info.items():
                print(f"  {key}: {value}")
            return True
        else:
            print_error("Could not fetch warehouse info")
            return False

    except Exception as e:
        print_error(f"Failed to get warehouse info: {e}")
        return False


async def test_schema_check(connector):
    """Check for Bronze/Silver/Gold schemas"""
    print_header("6. Checking Data Layer Schemas")

    if not connector or not connector.is_enabled:
        print_warning("Skipping schema check (connector not available)")
        return False

    try:
        print_info("Checking for Bronze/Silver/Gold schemas...")

        query = """
        SHOW SCHEMAS IN DATABASE IDENTIFIER(?);
        """

        from src.core.config import settings
        results = await connector.execute_query(
            f"SHOW SCHEMAS IN DATABASE {settings.snowflake_database}"
        )

        if results:
            schema_names = [r.get('name', '').upper() for r in results]

            for layer in ['BRONZE', 'SILVER', 'GOLD']:
                if layer in schema_names:
                    print_success(f"{layer} schema exists")
                else:
                    print_warning(f"{layer} schema does not exist")
                    print_info(f"  Create it with: CREATE SCHEMA {settings.snowflake_database}.{layer};")

            return True
        else:
            print_warning("Could not retrieve schemas")
            return False

    except Exception as e:
        print_warning(f"Schema check failed: {e}")
        print_info("This is normal if schemas haven't been created yet")
        return False


async def run_all_tests():
    """Run all tests"""
    print(f"\n{BLUE}{'='*60}")
    print("Snowflake Integration Test Suite")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}{RESET}\n")

    results = {
        'configuration': False,
        'import': False,
        'connection': False,
        'query': False,
        'warehouse_info': False,
        'schema_check': False,
    }

    # Test 1: Configuration
    results['configuration'] = await test_configuration()

    if not results['configuration']:
        print_error("\nConfiguration test failed. Please set up your .env file.")
        print_info("See mcp-server/SNOWFLAKE_SETUP_GUIDE.md for instructions")
        return False

    # Test 2: Import
    connector = await test_connector_import()
    results['import'] = connector is not None

    if not results['import']:
        print_error("\nCannot proceed without Snowflake connector installed.")
        return False

    # Test 3: Connection
    results['connection'] = await test_connection(connector)

    if not results['connection']:
        print_error("\nConnection failed. Tests cannot continue.")
        print_info("Check your Snowflake credentials and try again")
        return False

    # Test 4: Query execution
    results['query'] = await test_query_execution(connector)

    # Test 5: Warehouse info
    results['warehouse_info'] = await test_warehouse_info(connector)

    # Test 6: Schema check
    results['schema_check'] = await test_schema_check(connector)

    # Summary
    print_header("Test Summary")

    passed = sum(results.values())
    total = len(results)

    for test_name, passed_test in results.items():
        status = f"{GREEN}PASSED{RESET}" if passed_test else f"{RED}FAILED{RESET}"
        print(f"{test_name.replace('_', ' ').title()}: {status}")

    print(f"\n{BLUE}Results: {passed}/{total} tests passed{RESET}")

    if passed == total:
        print_success("\n🎉 All tests passed! Snowflake integration is ready to use.")
        print_info("\nNext steps:")
        print_info("  1. Create Bronze/Silver/Gold schemas if not exist")
        print_info("  2. Set up dbt project for transformations")
        print_info("  3. Start syncing data via MCP API")
        print_info("\nSee SNOWFLAKE_ORCHESTRATION.md for complete guide")
        return True
    else:
        print_error("\n⚠️ Some tests failed. Review the errors above.")
        print_info("\nFor help, see:")
        print_info("  - mcp-server/SNOWFLAKE_SETUP_GUIDE.md")
        print_info("  - mcp-server/SNOWFLAKE_ORCHESTRATION.md")
        return False


def main():
    """Main entry point"""
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
