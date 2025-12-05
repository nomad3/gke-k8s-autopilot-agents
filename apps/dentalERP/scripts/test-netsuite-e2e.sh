#!/bin/bash
# NetSuite End-to-End Test Script
# Tests complete data flow: NetSuite → Snowflake → Backend → Frontend
# Date: November 12, 2025

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MCP_URL="${MCP_URL:-http://localhost:8085}"
BACKEND_URL="${BACKEND_URL:-http://localhost:3001}"
TENANT_ID="${TENANT_ID:-default}"

# Check for required environment variables
if [ -z "$MCP_API_KEY" ]; then
    echo -e "${RED}ERROR: MCP_API_KEY environment variable not set${NC}"
    echo "Set it with: export MCP_API_KEY='your-api-key'"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}NetSuite End-to-End Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Configuration:"
echo "  MCP Server: $MCP_URL"
echo "  Backend API: $BACKEND_URL"
echo "  Tenant ID: $TENANT_ID"
echo ""

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function for test status
test_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

echo -e "${YELLOW}=== Test 1: NetSuite Connection ===${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$MCP_URL/api/v1/netsuite/sync/test-connection" \
    -H "Authorization: Bearer $MCP_API_KEY" \
    -H "X-Tenant-ID: $TENANT_ID" \
    -H "Content-Type: application/json")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" -eq 200 ]; then
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    test_status 0 "NetSuite API connection successful"
else
    echo "HTTP $HTTP_CODE: $BODY"
    test_status 1 "NetSuite API connection failed"
fi
echo ""

echo -e "${YELLOW}=== Test 2: Check Bronze Layer (Before Sync) ===${NC}"
# Count records in Bronze before sync
BRONZE_COUNT_BEFORE=$(python3 << 'EOF'
import os
import snowflake.connector

conn = snowflake.connector.connect(
    account=os.environ.get('SNOWFLAKE_ACCOUNT'),
    user=os.environ.get('SNOWFLAKE_USER'),
    password=os.environ.get('SNOWFLAKE_PASSWORD'),
    warehouse=os.environ.get('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
    database=os.environ.get('SNOWFLAKE_DATABASE', 'DENTAL_ERP_DW'),
    schema='BRONZE'
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM netsuite_journal_entries")
count = cursor.fetchone()[0]
print(count)
conn.close()
EOF
)

echo "Bronze records before sync: $BRONZE_COUNT_BEFORE"
test_status 0 "Bronze layer accessible"
echo ""

echo -e "${YELLOW}=== Test 3: Trigger NetSuite Sync (SuiteQL) ===${NC}"
echo "Starting sync with SuiteQL approach (bypasses User Event Scripts)..."

SYNC_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$MCP_URL/api/v1/netsuite/sync/trigger" \
    -H "Authorization: Bearer $MCP_API_KEY" \
    -H "X-Tenant-ID: $TENANT_ID" \
    -H "Content-Type: application/json" \
    -d '{
        "record_types": ["journalEntry"],
        "use_suiteql": true,
        "limit": 10
    }')

SYNC_HTTP_CODE=$(echo "$SYNC_RESPONSE" | tail -n1)
SYNC_BODY=$(echo "$SYNC_RESPONSE" | head -n-1)

if [ "$SYNC_HTTP_CODE" -eq 200 ] || [ "$SYNC_HTTP_CODE" -eq 202 ]; then
    echo "$SYNC_BODY" | python3 -m json.tool 2>/dev/null || echo "$SYNC_BODY"
    test_status 0 "NetSuite sync triggered successfully"

    # Wait for sync to complete
    echo "Waiting 30 seconds for sync to complete..."
    sleep 30
else
    echo "HTTP $SYNC_HTTP_CODE: $SYNC_BODY"
    test_status 1 "NetSuite sync trigger failed"
fi
echo ""

echo -e "${YELLOW}=== Test 4: Verify Bronze Layer (After Sync) ===${NC}"
BRONZE_ANALYSIS=$(python3 << 'EOF'
import os
import json
import snowflake.connector

conn = snowflake.connector.connect(
    account=os.environ.get('SNOWFLAKE_ACCOUNT'),
    user=os.environ.get('SNOWFLAKE_USER'),
    password=os.environ.get('SNOWFLAKE_PASSWORD'),
    warehouse=os.environ.get('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
    database=os.environ.get('SNOWFLAKE_DATABASE', 'DENTAL_ERP_DW'),
    schema='BRONZE'
)

cursor = conn.cursor()

# Total records
cursor.execute("SELECT COUNT(*) FROM netsuite_journal_entries")
total = cursor.fetchone()[0]

# Records with line items (complete data)
cursor.execute("""
    SELECT COUNT(*)
    FROM netsuite_journal_entries
    WHERE raw_data:line IS NOT NULL
""")
complete = cursor.fetchone()[0]

# Recent records (last hour)
cursor.execute("""
    SELECT COUNT(*)
    FROM netsuite_journal_entries
    WHERE _ingestion_timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'
""")
recent = cursor.fetchone()[0]

# Sample record to check structure
cursor.execute("""
    SELECT raw_data
    FROM netsuite_journal_entries
    WHERE raw_data:line IS NOT NULL
    LIMIT 1
""")
sample = cursor.fetchone()

result = {
    "total_records": total,
    "records_with_line_items": complete,
    "recent_records": recent,
    "completeness_pct": round((complete / total * 100), 2) if total > 0 else 0,
    "has_sample": sample is not None
}

print(json.dumps(result, indent=2))
conn.close()
EOF
)

echo "$BRONZE_ANALYSIS"
COMPLETE_PCT=$(echo "$BRONZE_ANALYSIS" | python3 -c "import sys, json; print(json.load(sys.stdin)['completeness_pct'])")

if (( $(echo "$COMPLETE_PCT > 5.0" | bc -l) )); then
    test_status 0 "Bronze layer has complete data (${COMPLETE_PCT}% with line items)"
else
    test_status 1 "Bronze layer data incomplete (only ${COMPLETE_PCT}% with line items)"
fi
echo ""

echo -e "${YELLOW}=== Test 5: Verify Silver Layer Processing ===${NC}"
SILVER_COUNT=$(python3 << 'EOF'
import os
import snowflake.connector

conn = snowflake.connector.connect(
    account=os.environ.get('SNOWFLAKE_ACCOUNT'),
    user=os.environ.get('SNOWFLAKE_USER'),
    password=os.environ.get('SNOWFLAKE_PASSWORD'),
    warehouse=os.environ.get('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
    database=os.environ.get('SNOWFLAKE_DATABASE', 'DENTAL_ERP_DW'),
    schema='SILVER'
)

cursor = conn.cursor()

# Check if Silver layer has stg_financials table
cursor.execute("""
    SELECT COUNT(*)
    FROM information_schema.tables
    WHERE table_schema = 'SILVER'
    AND table_name = 'STG_FINANCIALS'
""")
table_exists = cursor.fetchone()[0]

if table_exists:
    cursor.execute("SELECT COUNT(*) FROM silver.stg_financials")
    count = cursor.fetchone()[0]
    print(count)
else:
    print(0)

conn.close()
EOF
)

echo "Silver layer records: $SILVER_COUNT"
if [ "$SILVER_COUNT" -gt 0 ]; then
    test_status 0 "Silver layer processed Bronze data successfully"
else
    test_status 1 "Silver layer has no data"
fi
echo ""

echo -e "${YELLOW}=== Test 6: Verify Gold Layer Metrics ===${NC}"
GOLD_ANALYSIS=$(python3 << 'EOF'
import os
import json
import snowflake.connector

conn = snowflake.connector.connect(
    account=os.environ.get('SNOWFLAKE_ACCOUNT'),
    user=os.environ.get('SNOWFLAKE_USER'),
    password=os.environ.get('SNOWFLAKE_PASSWORD'),
    warehouse=os.environ.get('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
    database=os.environ.get('SNOWFLAKE_DATABASE', 'DENTAL_ERP_DW'),
    schema='GOLD'
)

cursor = conn.cursor()

# Check for daily_financial_metrics table
cursor.execute("""
    SELECT COUNT(*)
    FROM information_schema.tables
    WHERE table_schema = 'GOLD'
    AND table_name = 'DAILY_FINANCIAL_METRICS'
""")
table_exists = cursor.fetchone()[0]

if table_exists:
    cursor.execute("""
        SELECT
            COUNT(*) as record_count,
            SUM(total_revenue) as total_revenue,
            SUM(total_expenses) as total_expenses
        FROM gold.daily_financial_metrics
    """)
    row = cursor.fetchone()

    result = {
        "record_count": row[0],
        "total_revenue": float(row[1]) if row[1] else 0,
        "total_expenses": float(row[2]) if row[2] else 0
    }
else:
    result = {"record_count": 0, "total_revenue": 0, "total_expenses": 0}

print(json.dumps(result, indent=2))
conn.close()
EOF
)

echo "$GOLD_ANALYSIS"
GOLD_COUNT=$(echo "$GOLD_ANALYSIS" | python3 -c "import sys, json; print(json.load(sys.stdin)['record_count'])")

if [ "$GOLD_COUNT" -gt 0 ]; then
    test_status 0 "Gold layer has aggregated metrics"
else
    test_status 1 "Gold layer has no data"
fi
echo ""

echo -e "${YELLOW}=== Test 7: Backend Financial API ===${NC}"
FINANCIAL_RESPONSE=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/api/analytics/financial/summary?practice_name=Silver%20Creek")

FIN_HTTP_CODE=$(echo "$FINANCIAL_RESPONSE" | tail -n1)
FIN_BODY=$(echo "$FINANCIAL_RESPONSE" | head -n-1)

if [ "$FIN_HTTP_CODE" -eq 200 ]; then
    echo "$FIN_BODY" | python3 -m json.tool 2>/dev/null || echo "$FIN_BODY"
    test_status 0 "Backend financial API returns data"
else
    echo "HTTP $FIN_HTTP_CODE: $FIN_BODY"
    test_status 1 "Backend financial API failed"
fi
echo ""

echo -e "${YELLOW}=== Test 8: MCP Financial API (Direct) ===${NC}"
MCP_FINANCIAL_RESPONSE=$(curl -s -w "\n%{http_code}" "$MCP_URL/api/v1/analytics/financial/summary?practice_name=Silver%20Creek" \
    -H "Authorization: Bearer $MCP_API_KEY" \
    -H "X-Tenant-ID: $TENANT_ID")

MCP_FIN_HTTP_CODE=$(echo "$MCP_FINANCIAL_RESPONSE" | tail -n1)
MCP_FIN_BODY=$(echo "$MCP_FINANCIAL_RESPONSE" | head -n-1)

if [ "$MCP_FIN_HTTP_CODE" -eq 200 ]; then
    echo "$MCP_FIN_BODY" | python3 -m json.tool 2>/dev/null || echo "$MCP_FIN_BODY"
    test_status 0 "MCP financial API returns data"
else
    echo "HTTP $MCP_FIN_HTTP_CODE: $MCP_FIN_BODY"
    test_status 1 "MCP financial API failed"
fi
echo ""

echo -e "${YELLOW}=== Test 9: Data Quality Check ===${NC}"
DATA_QUALITY=$(python3 << 'EOF'
import os
import json
import snowflake.connector

conn = snowflake.connector.connect(
    account=os.environ.get('SNOWFLAKE_ACCOUNT'),
    user=os.environ.get('SNOWFLAKE_USER'),
    password=os.environ.get('SNOWFLAKE_PASSWORD'),
    warehouse=os.environ.get('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
    database=os.environ.get('SNOWFLAKE_DATABASE', 'DENTAL_ERP_DW'),
    schema='BRONZE'
)

cursor = conn.cursor()

# Sample a complete record and validate structure
cursor.execute("""
    SELECT raw_data
    FROM netsuite_journal_entries
    WHERE raw_data:line IS NOT NULL
    LIMIT 1
""")

row = cursor.fetchone()
quality_checks = {
    "has_id": False,
    "has_tranDate": False,
    "has_line_array": False,
    "line_has_account": False,
    "line_has_debit": False,
    "line_has_credit": False
}

if row and row[0]:
    data = json.loads(row[0])
    quality_checks["has_id"] = "id" in data
    quality_checks["has_tranDate"] = "tranDate" in data
    quality_checks["has_line_array"] = "line" in data and isinstance(data["line"], list)

    if quality_checks["has_line_array"] and len(data["line"]) > 0:
        first_line = data["line"][0]
        quality_checks["line_has_account"] = "account" in first_line
        quality_checks["line_has_debit"] = "debit" in first_line
        quality_checks["line_has_credit"] = "credit" in first_line

print(json.dumps(quality_checks, indent=2))
conn.close()
EOF
)

echo "$DATA_QUALITY"
ALL_CHECKS_PASSED=$(echo "$DATA_QUALITY" | python3 -c "import sys, json; checks = json.load(sys.stdin); print(all(checks.values()))")

if [ "$ALL_CHECKS_PASSED" = "True" ]; then
    test_status 0 "Data quality checks passed"
else
    test_status 1 "Data quality checks failed"
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! NetSuite E2E flow is working.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Review the output above.${NC}"
    exit 1
fi
