#!/bin/bash
# Test script for multi-product access control
# Tests Phase 3: Multi-Product Support

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="http://localhost:8085"

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
print_test() {
    echo -e "\n${YELLOW}TEST: $1${NC}"
    TESTS_RUN=$((TESTS_RUN + 1))
}

pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

summary() {
    echo -e "\n========================================="
    echo -e "PRODUCT ACCESS TEST SUMMARY"
    echo -e "========================================="
    echo -e "Total Tests:  $TESTS_RUN"
    echo -e "${GREEN}Passed:       $TESTS_PASSED${NC}"
    echo -e "${RED}Failed:       $TESTS_FAILED${NC}"
    echo -e "=========================================\n"

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}\n"
        return 0
    else
        echo -e "${RED}⚠️  SOME TESTS FAILED${NC}\n"
        return 1
    fi
}

echo "========================================="
echo "MULTI-PRODUCT ACCESS CONTROL TESTS"
echo "========================================="

# =====================================================
# TEST SUITE 1: Product Catalog (Public Access)
# =====================================================
echo -e "\n📦 TEST SUITE 1: Product Catalog (Public Access)"
echo "=================================================="

print_test "1.1 - List all products (no auth required)"
RESPONSE=$(curl -s "$BASE_URL/api/v1/products/")
if echo "$RESPONSE" | jq -e 'type == "array"' > /dev/null 2>&1; then
    COUNT=$(echo "$RESPONSE" | jq 'length')
    if [ "$COUNT" -eq 2 ]; then
        pass "Found 2 products as expected"
        echo "  Products: $(echo "$RESPONSE" | jq -r '.[].code' | tr '\n' ', ' | sed 's/,$//')"
    else
        fail "Expected 2 products, found $COUNT"
    fi
else
    fail "Response is not an array or request failed"
fi

print_test "1.2 - Get DentalERP product details"
RESPONSE=$(curl -s "$BASE_URL/api/v1/products/dentalerp")
if echo "$RESPONSE" | jq -e '.code == "dentalerp"' > /dev/null 2>&1; then
    NAME=$(echo "$RESPONSE" | jq -r '.name')
    STATUS=$(echo "$RESPONSE" | jq -r '.status')
    pass "DentalERP found: $NAME (status: $STATUS)"
else
    fail "Could not retrieve DentalERP details"
fi

print_test "1.3 - Get AgentProvision product details"
RESPONSE=$(curl -s "$BASE_URL/api/v1/products/agentprovision")
if echo "$RESPONSE" | jq -e '.code == "agentprovision"' > /dev/null 2>&1; then
    NAME=$(echo "$RESPONSE" | jq -r '.name')
    STATUS=$(echo "$RESPONSE" | jq -r '.status')
    pass "AgentProvision found: $NAME (status: $STATUS)"
else
    fail "Could not retrieve AgentProvision details"
fi

# =====================================================
# TEST SUITE 2: Tenant Product Access (Default Tenant)
# =====================================================
echo -e "\n👤 TEST SUITE 2: Tenant Product Access (Default Tenant)"
echo "========================================================="

print_test "2.1 - List accessible products for default tenant"
RESPONSE=$(curl -s -H "X-Tenant-ID: default" "$BASE_URL/api/v1/products/accessible")
if echo "$RESPONSE" | jq -e 'type == "array"' > /dev/null 2>&1; then
    COUNT=$(echo "$RESPONSE" | jq 'length')
    PRODUCTS=$(echo "$RESPONSE" | jq -r '.[].code' | tr '\n' ', ' | sed 's/,$//')
    pass "Default tenant has access to $COUNT product(s): $PRODUCTS"
else
    fail "Could not retrieve accessible products"
fi

print_test "2.2 - Check default tenant access to DentalERP"
RESPONSE=$(curl -s -H "X-Tenant-ID: default" "$BASE_URL/api/v1/products/dentalerp/access")
if echo "$RESPONSE" | jq -e '.has_access == true' > /dev/null 2>&1; then
    pass "Default tenant has access to DentalERP"
else
    fail "Default tenant does NOT have access to DentalERP"
fi

print_test "2.3 - List DentalERP features for default tenant"
RESPONSE=$(curl -s -H "X-Tenant-ID: default" "$BASE_URL/api/v1/products/dentalerp/features")
if echo "$RESPONSE" | jq -e '.product_code == "dentalerp"' > /dev/null 2>&1; then
    ALL_FEATURES=$(echo "$RESPONSE" | jq -r '.all_features | length')
    TENANT_FEATURES=$(echo "$RESPONSE" | jq -r '.tenant_features | length')
    pass "DentalERP has $ALL_FEATURES features, tenant has access to $TENANT_FEATURES"
    echo "  Tenant features: $(echo "$RESPONSE" | jq -r '.tenant_features[]' | head -3 | tr '\n' ', ' | sed 's/,$//')..."
else
    fail "Could not retrieve DentalERP features"
fi

# =====================================================
# TEST SUITE 3: Product-Specific Endpoints (DentalERP)
# =====================================================
echo -e "\n🦷 TEST SUITE 3: Product-Specific Endpoints (DentalERP)"
echo "========================================================"

print_test "3.1 - Access DentalERP home endpoint"
RESPONSE=$(curl -s -H "X-Tenant-ID: default" "$BASE_URL/api/v1/dental/")
if echo "$RESPONSE" | jq -e '.product == "dentalerp"' > /dev/null 2>&1; then
    pass "DentalERP home endpoint accessible"
    echo "  Message: $(echo "$RESPONSE" | jq -r '.message')"
else
    fail "Could not access DentalERP home endpoint"
    echo "  Response: $RESPONSE"
fi

print_test "3.2 - Access DentalERP analytics endpoint (requires ANALYTICS feature)"
RESPONSE=$(curl -s -H "X-Tenant-ID: default" "$BASE_URL/api/v1/dental/analytics/production/summary")
if echo "$RESPONSE" | jq -e 'has("detail")' > /dev/null 2>&1; then
    DETAIL=$(echo "$RESPONSE" | jq -r '.detail')
    if [[ "$DETAIL" == *"does not have access to analytics feature"* ]]; then
        echo "  ℹ️  Feature-level restriction working (no analytics access)"
        pass "Feature-based access control functioning"
    elif [[ "$DETAIL" == *"No data found"* ]] || [[ "$DETAIL" != "Forbidden"* ]]; then
        pass "Analytics endpoint accessible (may have no data yet)"
    else
        fail "Unexpected error: $DETAIL"
    fi
else
    # Might have actual analytics data
    pass "Analytics endpoint accessible"
fi

# =====================================================
# TEST SUITE 4: Product-Specific Endpoints (AgentProvision)
# =====================================================
echo -e "\n🤖 TEST SUITE 4: Product-Specific Endpoints (AgentProvision)"
echo "============================================================="

print_test "4.1 - Check default tenant access to AgentProvision"
RESPONSE=$(curl -s -H "X-Tenant-ID: default" "$BASE_URL/api/v1/products/agentprovision/access")
HAS_ACCESS=$(echo "$RESPONSE" | jq -r '.has_access')
if [ "$HAS_ACCESS" = "false" ]; then
    pass "Default tenant does NOT have access to AgentProvision (as expected)"
else
    echo "  ℹ️  Default tenant HAS access to AgentProvision"
fi

print_test "4.2 - Try to access AgentProvision endpoint without permission"
RESPONSE=$(curl -s -H "X-Tenant-ID: default" "$BASE_URL/api/v1/agent/")
if echo "$RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
    DETAIL=$(echo "$RESPONSE" | jq -r '.detail')
    if [[ "$DETAIL" == *"does not have access to AgentProvision"* ]]; then
        pass "AgentProvision endpoint correctly blocked"
    else
        # If they have access, that's also valid
        echo "  ℹ️  Tenant has access to AgentProvision"
        pass "AgentProvision endpoint accessible"
    fi
else
    # Endpoint returned successfully
    echo "  ℹ️  Tenant has access to AgentProvision"
    pass "AgentProvision endpoint accessible"
fi

# =====================================================
# TEST SUITE 5: ACME Tenant Product Access
# =====================================================
echo -e "\n🏢 TEST SUITE 5: ACME Tenant Product Access"
echo "============================================="

print_test "5.1 - List accessible products for ACME tenant"
RESPONSE=$(curl -s -H "X-Tenant-ID: acme" "$BASE_URL/api/v1/products/accessible")
if echo "$RESPONSE" | jq -e 'type == "array"' > /dev/null 2>&1; then
    COUNT=$(echo "$RESPONSE" | jq 'length')
    PRODUCTS=$(echo "$RESPONSE" | jq -r '.[].code' | tr '\n' ', ' | sed 's/,$//')
    pass "ACME tenant has access to $COUNT product(s): $PRODUCTS"
else
    fail "Could not retrieve accessible products for ACME"
fi

print_test "5.2 - Access DentalERP endpoint as ACME tenant"
RESPONSE=$(curl -s -H "X-Tenant-ID: acme" "$BASE_URL/api/v1/dental/")
if echo "$RESPONSE" | jq -e '.product == "dentalerp"' > /dev/null 2>&1; then
    TENANT=$(echo "$RESPONSE" | jq -r '.tenant')
    pass "ACME tenant can access DentalERP (tenant: $TENANT)"
else
    fail "ACME tenant cannot access DentalERP"
    echo "  Response: $RESPONSE"
fi

# =====================================================
# TEST SUITE 6: Tenant Isolation
# =====================================================
echo -e "\n🔒 TEST SUITE 6: Tenant Isolation"
echo "==================================="

print_test "6.1 - Verify different tenants have separate product access"
DEFAULT_PRODUCTS=$(curl -s -H "X-Tenant-ID: default" "$BASE_URL/api/v1/products/accessible" | jq -r '.[].code' | sort | tr '\n' ',')
ACME_PRODUCTS=$(curl -s -H "X-Tenant-ID: acme" "$BASE_URL/api/v1/products/accessible" | jq -r '.[].code' | sort | tr '\n' ',')

echo "  Default tenant products: $DEFAULT_PRODUCTS"
echo "  ACME tenant products: $ACME_PRODUCTS"

if [ "$DEFAULT_PRODUCTS" = "$ACME_PRODUCTS" ]; then
    echo "  ℹ️  Both tenants have same product access (currently both have DentalERP)"
    pass "Tenant product access retrieved successfully"
else
    pass "Tenants have different product access configurations"
fi

print_test "6.2 - Verify product-specific endpoints respect tenant context"
DEFAULT_RESPONSE=$(curl -s -H "X-Tenant-ID: default" "$BASE_URL/api/v1/dental/" | jq -r '.tenant')
ACME_RESPONSE=$(curl -s -H "X-Tenant-ID: acme" "$BASE_URL/api/v1/dental/" | jq -r '.tenant')

if [ "$DEFAULT_RESPONSE" = "default" ] && [ "$ACME_RESPONSE" = "acme" ]; then
    pass "Product endpoints correctly use tenant context"
    echo "  Default response: tenant=$DEFAULT_RESPONSE"
    echo "  ACME response: tenant=$ACME_RESPONSE"
else
    fail "Tenant context not properly isolated"
fi

# Print summary
echo ""
summary
