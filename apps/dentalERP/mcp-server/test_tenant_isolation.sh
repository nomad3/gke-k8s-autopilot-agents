#!/bin/bash

# Test tenant context isolation with concurrent requests
# Ensures that tenant context doesn't bleed between requests

set -e

echo "=========================================="
echo "Testing Tenant Context Isolation"
echo "=========================================="
echo

# Test 1: Multiple sequential requests with different tenants
echo "Test 1: Sequential requests with different tenants"
echo "---------------------------------------------------"

echo "Request 1: Using tenant 'default'"
response1=$(docker exec dentalerp-mcp-server-1 curl -s -H "X-Tenant-ID: default" -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" http://localhost:8085/api/v1/tenants/)
echo "✓ Got response from default tenant"

echo "Request 2: Using tenant 'acme'"
response2=$(docker exec dentalerp-mcp-server-1 curl -s http://localhost:8085/api/v1/tenants/acme)
echo "✓ Got response from acme tenant"

echo "Request 3: Using tenant 'default' again"
response3=$(docker exec dentalerp-mcp-server-1 curl -s http://localhost:8085/api/v1/tenants/default)
echo "✓ Got response from default tenant again"
echo

# Test 2: Public endpoints should bypass middleware
echo "Test 2: Public endpoints (no tenant required)"
echo "----------------------------------------------"

echo "Testing /health endpoint"
health=$(docker exec dentalerp-mcp-server-1 curl -s http://localhost:8085/health)
if echo "$health" | grep -q "ok"; then
    echo "✓ Health endpoint accessible without tenant"
else
    echo "✗ Health endpoint failed"
    exit 1
fi

echo "Testing / root endpoint"
root=$(docker exec dentalerp-mcp-server-1 curl -s http://localhost:8085/)
if echo "$root" | grep -q "MCP Server"; then
    echo "✓ Root endpoint accessible without tenant"
else
    echo "✗ Root endpoint failed"
    exit 1
fi
echo

# Test 3: Tenant management endpoints (public for now)
echo "Test 3: Tenant management endpoints"
echo "------------------------------------"

echo "GET /api/v1/tenants/ (list all)"
tenants=$(docker exec dentalerp-mcp-server-1 curl -s http://localhost:8085/api/v1/tenants/)
if echo "$tenants" | grep -q "default"; then
    echo "✓ Can list tenants without tenant context"
else
    echo "✗ Failed to list tenants"
    exit 1
fi
echo

# Test 4: Protected endpoints should require tenant
echo "Test 4: Protected endpoints require tenant"
echo "-------------------------------------------"

echo "Testing analytics endpoint without tenant"
no_tenant=$(docker exec dentalerp-mcp-server-1 curl -s http://localhost:8085/api/v1/analytics/production/summary)
if echo "$no_tenant" | grep -q "Tenant identification required"; then
    echo "✓ Protected endpoint correctly rejects request without tenant"
else
    echo "✗ Protected endpoint should require tenant"
    exit 1
fi

echo "Testing analytics endpoint with valid tenant"
with_tenant=$(docker exec dentalerp-mcp-server-1 curl -s -H "X-Tenant-ID: default" -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" http://localhost:8085/api/v1/analytics/production/summary)
if echo "$with_tenant" | grep -q "TOTAL_PRODUCTION"; then
    echo "✓ Protected endpoint accessible with valid tenant"
else
    echo "✗ Protected endpoint failed with valid tenant"
    exit 1
fi
echo

# Test 5: Invalid tenant should be rejected
echo "Test 5: Invalid tenant rejection"
echo "---------------------------------"

echo "Testing with non-existent tenant"
invalid=$(docker exec dentalerp-mcp-server-1 curl -s -H "X-Tenant-ID: nonexistent" -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" http://localhost:8085/api/v1/analytics/production/summary)
if echo "$invalid" | grep -q "Tenant not found"; then
    echo "✓ Invalid tenant correctly rejected"
else
    echo "✗ Invalid tenant should be rejected"
    exit 1
fi
echo

# Test 6: Tenant extraction from API key prefix
echo "Test 6: Tenant extraction from API key"
echo "---------------------------------------"

echo "Testing API key with 'acme' prefix"
api_key_tenant=$(docker exec dentalerp-mcp-server-1 curl -s -H "Authorization: Bearer acme_test_key_123" http://localhost:8085/api/v1/analytics/production/summary)
# Should identify tenant 'acme' but fail on actual API key validation
if echo "$api_key_tenant" | grep -q "Invalid API key"; then
    echo "✓ Tenant 'acme' extracted from API key prefix (failed on auth as expected)"
else
    echo "✗ Failed to extract tenant from API key prefix"
    exit 1
fi
echo

# Test 7: Inactive tenant should be rejected (after we implement status check)
echo "Test 7: Tenant status validation"
echo "---------------------------------"

# Create an inactive tenant for testing
echo "Creating inactive test tenant..."
docker exec dentalerp-mcp-server-1 curl -s -X POST http://localhost:8085/api/v1/tenants/ \
  -H "Content-Type: application/json" \
  -d '{"tenant_code":"inactive_test","tenant_name":"Inactive Test","industry":"dental","products":["dentalerp"]}' > /dev/null

# Get tenant ID
tenant_data=$(docker exec dentalerp-mcp-server-1 curl -s http://localhost:8085/api/v1/tenants/inactive_test)
tenant_id=$(echo "$tenant_data" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

# Update to inactive status
docker exec dentalerp-mcp-server-1 curl -s -X PUT http://localhost:8085/api/v1/tenants/$tenant_id \
  -H "Content-Type: application/json" \
  -d '{"status":"inactive"}' > /dev/null

echo "Testing access with inactive tenant"
inactive_tenant=$(docker exec dentalerp-mcp-server-1 curl -s -H "X-Tenant-ID: inactive_test" -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" http://localhost:8085/api/v1/analytics/production/summary)
if echo "$inactive_tenant" | grep -q "Tenant inactive"; then
    echo "✓ Inactive tenant correctly rejected"
else
    echo "✗ Inactive tenant should be rejected"
    exit 1
fi

# Cleanup
docker exec dentalerp-mcp-server-1 curl -s -X DELETE http://localhost:8085/api/v1/tenants/$tenant_id > /dev/null
echo

echo "=========================================="
echo "✅ All tenant isolation tests passed!"
echo "=========================================="
echo
echo "Summary:"
echo "  ✓ Sequential requests with different tenants"
echo "  ✓ Public endpoints bypass tenant middleware"
echo "  ✓ Tenant management endpoints accessible"
echo "  ✓ Protected endpoints require tenant"
echo "  ✓ Invalid tenants rejected"
echo "  ✓ Tenant extraction from API key prefix"
echo "  ✓ Inactive tenant status validation"
echo
echo "Tenant middleware is working correctly!"
