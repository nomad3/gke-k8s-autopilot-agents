#!/bin/bash
#
# Test Manual Ingestion Endpoints
# Tests both NetSuite and Operations Report CSV/Excel uploads
#

set -euo pipefail

MCP_URL="${MCP_URL:-https://mcp.agentprovision.com}"
MCP_API_KEY="${MCP_API_KEY:-d876e6163089364d96a45a80ed576e99fc55b306133e258d9f861007e824b456}"
TENANT_ID="${TENANT_ID:-silvercreek}"

echo "=========================================="
echo "Manual Ingestion Test Suite"
echo "=========================================="
echo "MCP Server: $MCP_URL"
echo "Tenant: $TENANT_ID"
echo ""

# Test 1: NetSuite TransactionDetail CSV Upload
echo "TEST 1: NetSuite TransactionDetail CSV Upload"
echo "----------------------------------------------"

if [ -f "backup/TransactionDetail-83.csv" ]; then
    echo "Uploading NetSuite TransactionDetail-83.csv..."

    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$MCP_URL/api/v1/netsuite/upload/transactions" \
      -H "Authorization: Bearer $MCP_API_KEY" \
      -H "X-Tenant-ID: $TENANT_ID" \
      -F "file=@backup/TransactionDetail-83.csv")

    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE:/d')

    if [ "$http_code" == "200" ]; then
        echo "✅ PASS: NetSuite CSV upload successful"
        echo "Response: $body" | python3 -m json.tool 2>/dev/null || echo "$body"
    else
        echo "❌ FAIL: HTTP $http_code"
        echo "Response: $body"
    fi
else
    echo "⚠️  SKIP: backup/TransactionDetail-83.csv not found"
fi

echo ""

# Test 2: Operations Report Upload (if we have sample file)
echo "TEST 2: Operations Report Excel/CSV Upload"
echo "----------------------------------------------"

if [ -f "examples/ingestion/operations_report_raw.csv" ]; then
    echo "Uploading Operations Report CSV..."

    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$MCP_URL/api/v1/operations/upload" \
      -H "Authorization: Bearer $MCP_API_KEY" \
      -H "X-Tenant-ID: $TENANT_ID" \
      -F "file=@examples/ingestion/operations_report_raw.csv" \
      -F "practice_code=test" \
      -F "practice_name=Test Practice" \
      -F "report_month=2025-11-01")

    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE:/d')

    if [ "$http_code" == "200" ]; then
        echo "✅ PASS: Operations Report upload successful"
        echo "Response: $body" | python3 -m json.tool 2>/dev/null || echo "$body"
    else
        echo "❌ FAIL: HTTP $http_code"
        echo "Response: $body"
    fi
else
    echo "⚠️  SKIP: examples/ingestion/operations_report_raw.csv not found"
fi

echo ""

# Test 3: Bulk NetSuite Upload (processes all CSV files in backup/)
echo "TEST 3: Bulk NetSuite Upload"
echo "----------------------------------------------"
echo "This will process ALL TransactionDetail-*.csv files in backup/"
read -p "Run bulk upload? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Triggering bulk upload..."

    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$MCP_URL/api/v1/netsuite/upload/bulk-transactions" \
      -H "Authorization: Bearer $MCP_API_KEY" \
      -H "X-Tenant-ID: $TENANT_ID")

    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE:/d')

    if [ "$http_code" == "200" ]; then
        echo "✅ PASS: Bulk upload completed"
        echo "Response: $body" | python3 -m json.tool 2>/dev/null || echo "$body"
    else
        echo "❌ FAIL: HTTP $http_code"
        echo "Response: $body"
    fi
else
    echo "Skipped bulk upload"
fi

echo ""
echo "=========================================="
echo "Test Suite Complete"
echo "=========================================="
