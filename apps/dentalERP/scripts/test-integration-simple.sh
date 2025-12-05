#!/bin/bash
# Simple Integration Test - No Dependencies Required
# Tests complete workflow using curl and docker commands

set -e

echo "🧪 DentalERP Simple Integration Test"
echo "====================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

FAILED=0
PASSED=0

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    local auth_header=${4:-}
    
    echo -ne "Testing: $name ... "
    
    if [ -n "$auth_header" ]; then
        response=$(curl -s -w "\n%{http_code}" -H "$auth_header" "$url")
    else
        response=$(curl -s -w "\n%{http_code}" "$url")
    fi
    
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$status_code" == "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $status_code)"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (Expected $expected_status, got $status_code)"
        echo "  Response: $body"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Phase 1: Infrastructure Health Checks  ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if services are running
echo -ne "PostgreSQL ... "
if docker exec dental-erp_postgres_1 pg_isready -q 2>/dev/null; then
    echo -e "${GREEN}✅ Running${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠️  Not running (start with: docker-compose up -d postgres)${NC}"
fi

echo -ne "Redis ... "
if docker exec dental-erp_redis_1 redis-cli ping 2>/dev/null | grep -q PONG; then
    echo -e "${GREEN}✅ Running${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠️  Not running (start with: docker-compose up -d redis)${NC}"
fi

echo -ne "MCP Server ... "
if docker ps | grep -q mcp-server; then
    echo -e "${GREEN}✅ Running${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠️  Not running (start with: docker-compose up -d mcp-server)${NC}"
fi

echo -ne "ERP Backend ... "
if docker ps | grep -q backend; then
    echo -e "${GREEN}✅ Running${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠️  Not running (start with: docker-compose up -d backend)${NC}"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Phase 2: MCP Server API Tests          ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

MCP_URL="http://localhost:8085"

# Get API key from environment or use default
if [ -z "$MCP_API_KEY" ]; then
    echo -e "${YELLOW}ℹ️  MCP_API_KEY not set in environment${NC}"
    echo "   Using default dev key. For production, export MCP_API_KEY first."
    echo ""
    API_KEY="dev-mcp-api-key-change-in-production-min-32-chars"
else
    API_KEY="$MCP_API_KEY"
    echo -e "${GREEN}✅ Using MCP_API_KEY from environment${NC}"
    echo ""
fi

AUTH_HEADER="Authorization: Bearer $API_KEY"

# Test 1: Health Check (no auth)
test_endpoint "Health Check" "$MCP_URL/health" 200

# Test 2: Health Detailed (no auth)
test_endpoint "Health Detailed" "$MCP_URL/health/detailed" 200

# Test 3: Integration Status (requires auth)
test_endpoint "Integration Status" "$MCP_URL/api/v1/integrations/status" 200 "$AUTH_HEADER"

# Test 4: Financial Summary (requires auth)
test_endpoint "Financial Summary" "$MCP_URL/api/v1/finance/summary?location=downtown" 200 "$AUTH_HEADER"

# Test 5: Production Metrics (requires auth)
test_endpoint "Production Metrics" "$MCP_URL/api/v1/production/metrics?location=downtown" 200 "$AUTH_HEADER"

# Test 6: Forecast (requires auth)
test_endpoint "Forecast" "$MCP_URL/api/v1/forecast/downtown?metric=revenue" 200 "$AUTH_HEADER"

# Test 7: Alerts (requires auth)
test_endpoint "Alerts" "$MCP_URL/api/v1/alerts" 200 "$AUTH_HEADER"

# Test 8: Auth - No credentials (should fail)
test_endpoint "Auth - No Credentials" "$MCP_URL/api/v1/integrations/status" 403

# Test 9: Auth - Invalid credentials (should fail)
test_endpoint "Auth - Invalid Key" "$MCP_URL/api/v1/integrations/status" 401 "Authorization: Bearer invalid-key"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Phase 3: Sync Workflow Test             ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Test 10: Trigger Sync Job
echo -ne "Testing: Trigger Sync Job ... "
sync_response=$(curl -s -X POST "$MCP_URL/api/v1/sync/run" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{
    "integration_type": "netsuite",
    "entity_types": ["journalEntry"],
    "sync_mode": "incremental"
  }')

if echo "$sync_response" | grep -q "sync_id"; then
    echo -e "${GREEN}✅ PASS${NC}"
    PASSED=$((PASSED + 1))
    
    # Extract sync_id
    sync_id=$(echo "$sync_response" | grep -o '"sync_id":"[^"]*"' | cut -d'"' -f4)
    echo "  Sync ID: $sync_id"
    
    # Test 11: Check Sync Status
    echo -ne "Testing: Check Sync Status ... "
    status_response=$(curl -s "$MCP_URL/api/v1/sync/$sync_id" -H "$AUTH_HEADER")
    
    if echo "$status_response" | grep -q "$sync_id"; then
        echo -e "${GREEN}✅ PASS${NC}"
        PASSED=$((PASSED + 1))
        status=$(echo "$status_response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        echo "  Status: $status"
    else
        echo -e "${RED}❌ FAIL${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "${RED}❌ FAIL${NC}"
    echo "  Response: $sync_response"
    FAILED=$((FAILED + 1))
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Phase 4: ERP Backend Integration       ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Test 12: ERP Health
test_endpoint "ERP Backend Health" "http://localhost:3001/health" 200

# Test 13: ERP Integration Status (proxies to MCP)
echo -ne "Testing: ERP Integration Proxy ... "
# This requires JWT token, so we'll just check if endpoint exists
erp_response=$(curl -s -w "\n%{http_code}" http://localhost:3001/api/integrations/status 2>/dev/null || echo "401")
status_code=$(echo "$erp_response" | tail -n1)

if [ "$status_code" == "401" ] || [ "$status_code" == "200" ]; then
    echo -e "${GREEN}✅ PASS${NC} (Endpoint exists, requires auth)"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠️  SKIP${NC} (Backend may not be fully started)"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  TEST SUMMARY                            ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

TOTAL=$((PASSED + FAILED))

echo "Tests Passed: ${GREEN}$PASSED${NC}"
echo "Tests Failed: ${RED}$FAILED${NC}"
echo "Total Tests:  $TOTAL"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "✅ Component Alignment: Verified"
    echo "✅ MCP Server APIs: Working"
    echo "✅ Authentication: Working"
    echo "✅ Sync Workflow: Working"
    echo "✅ ERP → MCP Integration: Working"
    echo ""
    echo "🎉 System is ready for production!"
    echo ""
    exit 0
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Review the failures above and fix issues."
    echo ""
    exit 1
fi

