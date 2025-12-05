#!/bin/bash
# NetSuite SuiteQL Test Script
# Tests SuiteQL approach to fetch journal entries with line items
# This bypasses User Event Scripts that crash on REST API detail fetches
# Date: November 12, 2025

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
MCP_URL="${MCP_URL:-https://mcp.agentprovision.com}"
TENANT_ID="${TENANT_ID:-default}"

if [ -z "$MCP_API_KEY" ]; then
    echo -e "${RED}ERROR: MCP_API_KEY not set${NC}"
    echo "Export it: export MCP_API_KEY='your-key'"
    exit 1
fi

echo -e "${BLUE}=== NetSuite SuiteQL Test ===${NC}"
echo "MCP Server: $MCP_URL"
echo "Tenant: $TENANT_ID"
echo ""

echo -e "${YELLOW}Step 1: Test NetSuite Connection${NC}"
curl -s -X POST "$MCP_URL/api/v1/netsuite/sync/test-connection" \
    -H "Authorization: Bearer $MCP_API_KEY" \
    -H "X-Tenant-ID: $TENANT_ID" \
    -H "Content-Type: application/json" | python3 -m json.tool
echo ""

echo -e "${YELLOW}Step 2: Trigger SuiteQL Sync (10 records)${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$MCP_URL/api/v1/netsuite/sync/trigger" \
    -H "Authorization: Bearer $MCP_API_KEY" \
    -H "X-Tenant-ID: $TENANT_ID" \
    -H "Content-Type: application/json" \
    -d '{
        "record_types": ["journalEntry"],
        "use_suiteql": true,
        "limit": 10,
        "subsidiary_id": "1"
    }')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

echo "HTTP Status: $HTTP_CODE"
echo "$BODY" | python3 -m json.tool
echo ""

if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 202 ]; then
    echo -e "${GREEN}✓ Sync triggered successfully${NC}"
    echo ""
    echo "Waiting 45 seconds for sync to complete..."
    sleep 45

    echo -e "${YELLOW}Step 3: Check Sync Status${NC}"
    curl -s "$MCP_URL/api/v1/netsuite/sync/status" \
        -H "Authorization: Bearer $MCP_API_KEY" \
        -H "X-Tenant-ID: $TENANT_ID" | python3 -m json.tool
    echo ""

    echo -e "${GREEN}✓ Test complete${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Check Snowflake Bronze layer for new records"
    echo "2. Verify records have 'line' field populated"
    echo "3. Run full E2E test: ./scripts/test-netsuite-e2e.sh"
else
    echo -e "${RED}✗ Sync failed${NC}"
    exit 1
fi
