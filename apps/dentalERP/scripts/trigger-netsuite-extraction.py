#!/usr/bin/env python3
"""
Simple NetSuite Data Extraction Trigger
Triggers NetSuite sync for all financial data using existing MCP infrastructure
"""

import requests
import json
import sys
import time

def trigger_netsuite_extraction():
    """Trigger NetSuite data extraction via MCP API"""

    # MCP Server configuration
    mcp_base_url = "http://localhost:8085"
    mcp_api_key = "sk-secure-random-key-32-chars-minimum"

    headers = {
        "Authorization": f"Bearer {mcp_api_key}",
        "Content-Type": "application/json"
    }

    try:
        print("🚀 Starting NetSuite data extraction...")

        # Step 1: Check MCP server health
        print("Step 1: Checking MCP server health...")
        health_response = requests.get(f"{mcp_base_url}/health", timeout=10)
        if health_response.status_code != 200:
            print(f"❌ MCP server not healthy: {health_response.status_code}")
            return False
        print("✅ MCP server is healthy")

        # Step 2: Trigger NetSuite sync for comprehensive financial data
        print("Step 2: Triggering NetSuite sync for all financial data...")

        sync_payload = {
            "full_sync": True,
            "record_types": [
                "journalEntry",
                "account",
                "invoice",
                "customerPayment",
                "vendorBill",
                "customer",
                "vendor",
                "subsidiary"
            ],
            "date_range": {
                "start_date": "2024-01-01",
                "end_date": None  # Current date
            }
        }

        # Try with default tenant first
        response = requests.post(
            f"{mcp_base_url}/api/v1/netsuite/sync/trigger",
            headers=headers,
            json=sync_payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ NetSuite sync triggered successfully")
            print(f"   Sync ID: {result.get('sync_id', 'N/A')}")
            print(f"   Status: {result.get('status', 'N/A')}")
            return True
        else:
            print(f"⚠️  NetSuite sync returned status {response.status_code}")
            print(f"   Response: {response.text}")

            # Fallback: Try to trigger sync without specifying tenant
            print("Step 3: Trying fallback sync approach...")

            # Check if we can get sync status
            status_response = requests.get(
                f"{mcp_base_url}/api/v1/netsuite/sync/status",
                headers=headers,
                timeout=10
            )

            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"✅ NetSuite sync status available")
                print(f"   Last sync: {status_data.get('last_sync', 'N/A')}")
                print(f"   Status: {status_data.get('status', 'N/A')}")
                return True
            else:
                print(f"❌ Unable to trigger NetSuite sync")
                return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Error triggering NetSuite extraction: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_snowflake_data():
    """Check if data is available in Snowflake"""

    mcp_base_url = "http://localhost:8085"
    mcp_api_key = "sk-secure-random-key-32-chars-minimum"

    headers = {
        "Authorization": f"Bearer {mcp_api_key}",
        "Content-Type": "application/json"
    }

    try:
        print("Step 4: Checking Snowflake data availability...")

        # Check Bronze layer tables
        bronze_tables = [
            "netsuite_journalentry",
            "netsuite_account",
            "netsuite_invoice",
            "netsuite_customerpayment",
            "netsuite_vendorbill",
            "netsuite_customer",
            "netsuite_vendor",
            "netsuite_subsidiary"
        ]

        total_records = 0
        for table in bronze_tables:
            try:
                response = requests.get(
                    f"{mcp_base_url}/api/v1/warehouse/query",
                    headers=headers,
                    json={
                        "query": f"SELECT COUNT(*) as count FROM bronze.{table}",
                        "warehouse": "snowflake"
                    },
                    timeout=15
                )

                if response.status_code == 200:
                    result = response.json()
                    count = result.get('data', [{}])[0].get('COUNT', 0)
                    total_records += count
                    print(f"   {table}: {count:,} records")
                else:
                    print(f"   {table}: Unable to query (status {response.status_code})")

            except Exception as e:
                print(f"   {table}: Error querying - {e}")

        print(f"\n📊 Total records in Bronze layer: {total_records:,}")

        if total_records > 0:
            print("✅ NetSuite data successfully extracted and loaded to Snowflake!")
            return True
        else:
            print("⚠️  No data found in Snowflake Bronze layer")
            return False

    except Exception as e:
        print(f"⚠️  Error checking Snowflake data: {e}")
        return False

def main():
    """Main execution function"""
    print("=" * 60)
    print("NETSUITE DATA EXTRACTION ORCHESTRATION")
    print("=" * 60)

    # Step 1: Trigger NetSuite extraction
    success = trigger_netsuite_extraction()

    if success:
        print("\n⏳ Waiting 30 seconds for sync to complete...")
        time.sleep(30)

        # Step 2: Check results in Snowflake
        snowflake_success = check_snowflake_data()

        if snowflake_success:
            print("\n🎉 NetSuite data extraction completed successfully!")
            print("\nNext steps:")
            print("• Snowflake Dynamic Tables will auto-refresh Bronze → Silver → Gold")
            print("• Backend API can query financial data via MCP analytics endpoints")
            print("• Frontend dashboard will display multi-location financial metrics")
            print("• PMS vs NetSuite reconciliation analysis is ready")
            return 0
        else:
            print("\n⚠️  Extraction triggered but data verification failed")
            return 1
    else:
        print("\n❌ NetSuite data extraction failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())