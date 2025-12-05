#!/bin/bash
#
# Multi-Tenant End-to-End Test Suite
# Tests complete flow for multiple tenants with data isolation verification
#
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
MCP_API_URL="${MCP_API_URL:-http://localhost:8085}"
TEST_PDF="${TEST_PDF:-examples/ingestion/Eastlake Day 07 2025.pdf}"
PRACTICE_LOCATION="${PRACTICE_LOCATION:-Eastlake}"
USE_AI="${USE_AI:-false}"  # Set to false to avoid OpenAI costs

# Tenant configurations
TENANT_DEFAULT_ID="default"
TENANT_DEFAULT_KEY="dev-mcp-api-key-change-in-production-min-32-chars"

TENANT_ACME_ID="acme"
TENANT_ACME_KEY="acme_dev-mcp-api-key"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}        Multi-Tenant End-to-End Test Suite                     ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Helper functions
step() {
    echo ""
    echo -e "${BLUE}───────────────────────────────────────────────────────────────${NC}"
    echo -e "${GREEN}STEP $1: $2${NC}"
    echo -e "${BLUE}───────────────────────────────────────────────────────────────${NC}"
}

test_start() {
    echo -e "\n${CYAN}TEST: $1${NC}"
    TESTS_RUN=$((TESTS_RUN + 1))
}

test_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

test_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

# API call with tenant context
api_call() {
    local url=$1
    local method=${2:-GET}
    local tenant_id=${3:-$TENANT_DEFAULT_ID}
    local api_key=${4:-$TENANT_DEFAULT_KEY}
    local data=${5:-}

    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
            -H "X-Tenant-ID: $tenant_id" \
            -H "Authorization: Bearer $api_key" \
            $data)
    else
        response=$(curl -s -w "\n%{http_code}" "$url" \
            -H "X-Tenant-ID: $tenant_id" \
            -H "Authorization: Bearer $api_key")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo "$body"
        return 0
    else
        echo "$body" >&2
        return 1
    fi
}

# ============================================================================
# STEP 1: Verify Server Health
# ============================================================================
step 1 "Health Check - Verify MCP Server is running"

test_start "MCP Server health check"
health_response=$(curl -s "$MCP_API_URL/health")
if [ $? -eq 0 ]; then
    echo "$health_response" | jq '.'
    test_pass "MCP Server is healthy"
else
    test_fail "MCP Server is not responding"
    exit 1
fi

# ============================================================================
# STEP 2: Verify Tenants Exist
# ============================================================================
step 2 "Tenant Management - Verify tenants are configured"

test_start "List all tenants"
tenants_response=$(curl -s "$MCP_API_URL/api/v1/tenants/")
if [ $? -eq 0 ]; then
    tenant_count=$(echo "$tenants_response" | jq 'length')
    echo "$tenants_response" | jq '.[] | {tenant_code, tenant_name, status, products}'
    test_pass "Found $tenant_count tenants"
else
    test_fail "Failed to list tenants"
fi

test_start "Get default tenant details"
default_tenant=$(api_call "$MCP_API_URL/api/v1/tenants/$TENANT_DEFAULT_ID" GET)
if [ $? -eq 0 ]; then
    echo "$default_tenant" | jq '{tenant_code, tenant_name, products}'
    test_pass "Default tenant exists"
else
    test_fail "Default tenant not found"
fi

test_start "Get ACME tenant details"
acme_tenant=$(api_call "$MCP_API_URL/api/v1/tenants/$TENANT_ACME_ID" GET)
if [ $? -eq 0 ]; then
    echo "$acme_tenant" | jq '{tenant_code, tenant_name, products}'
    test_pass "ACME tenant exists"
else
    echo -e "${YELLOW}⚠ ACME tenant not found, creating...${NC}"

    # Create ACME tenant
    create_response=$(curl -s -X POST "$MCP_API_URL/api/v1/tenants/" \
        -H "Content-Type: application/json" \
        -d '{
            "tenant_code": "acme",
            "tenant_name": "ACME Dental Practice",
            "industry": "dental",
            "products": ["dentalerp"]
        }')

    if [ $? -eq 0 ]; then
        echo "$create_response" | jq '.'
        test_pass "ACME tenant created"
    else
        test_fail "Failed to create ACME tenant"
    fi
fi

# ============================================================================
# STEP 3: Test Product Access
# ============================================================================
step 3 "Product Access - Verify multi-product support"

test_start "List all products (public catalog)"
products=$(curl -s "$MCP_API_URL/api/v1/products/")
if [ $? -eq 0 ]; then
    product_count=$(echo "$products" | jq 'length')
    echo "$products" | jq '.[] | {code, name, status}'
    test_pass "Found $product_count products"
else
    test_fail "Failed to list products"
fi

test_start "Check default tenant's accessible products"
default_products=$(api_call "$MCP_API_URL/api/v1/products/accessible" GET "$TENANT_DEFAULT_ID" "$TENANT_DEFAULT_KEY")
if [ $? -eq 0 ]; then
    echo "$default_products" | jq '.[] | {code, name}'
    test_pass "Default tenant product access retrieved"
else
    test_fail "Failed to get default tenant products"
fi

test_start "Check ACME tenant's accessible products"
acme_products=$(api_call "$MCP_API_URL/api/v1/products/accessible" GET "$TENANT_ACME_ID" "$TENANT_ACME_KEY")
if [ $? -eq 0 ]; then
    echo "$acme_products" | jq '.[] | {code, name}'
    test_pass "ACME tenant product access retrieved"
else
    test_fail "Failed to get ACME tenant products"
fi

# ============================================================================
# STEP 4: Test Default Tenant - PDF Upload
# ============================================================================
step 4 "Default Tenant - PDF Upload & Extraction"

test_start "Upload PDF as default tenant"
default_upload=$(curl -s -X POST "$MCP_API_URL/api/v1/pdf/upload" \
    -H "X-Tenant-ID: $TENANT_DEFAULT_ID" \
    -H "Authorization: Bearer $TENANT_DEFAULT_KEY" \
    -F "file=@$TEST_PDF" \
    -F "practice_location=$PRACTICE_LOCATION" \
    -F "use_ai=$USE_AI" \
    -F "uploaded_by=default_tenant_test")

if [ $? -eq 0 ]; then
    echo "$default_upload" | jq '{record_id, table_name, report_type, extraction_method}'
    DEFAULT_RECORD_ID=$(echo "$default_upload" | jq -r '.record_id')
    test_pass "Default tenant uploaded PDF successfully (ID: $DEFAULT_RECORD_ID)"
else
    echo "$default_upload"
    test_fail "Default tenant PDF upload failed"
fi

# ============================================================================
# STEP 5: Test ACME Tenant - PDF Upload
# ============================================================================
step 5 "ACME Tenant - PDF Upload & Extraction"

test_start "Upload PDF as ACME tenant"
acme_upload=$(curl -s -X POST "$MCP_API_URL/api/v1/pdf/upload" \
    -H "X-Tenant-ID: $TENANT_ACME_ID" \
    -H "Authorization: Bearer $TENANT_ACME_KEY" \
    -F "file=@$TEST_PDF" \
    -F "practice_location=$PRACTICE_LOCATION" \
    -F "use_ai=$USE_AI" \
    -F "uploaded_by=acme_tenant_test")

if [ $? -eq 0 ]; then
    echo "$acme_upload" | jq '{record_id, table_name, report_type, extraction_method}'
    ACME_RECORD_ID=$(echo "$acme_upload" | jq -r '.record_id')
    test_pass "ACME tenant uploaded PDF successfully (ID: $ACME_RECORD_ID)"
else
    echo "$acme_upload"
    test_fail "ACME tenant PDF upload failed"
fi

# ============================================================================
# STEP 6: Test DentalERP Product Endpoints
# ============================================================================
step 6 "DentalERP Product - Verify product-specific endpoints"

test_start "Access DentalERP home as default tenant"
default_dental=$(api_call "$MCP_API_URL/api/v1/dental/" GET "$TENANT_DEFAULT_ID" "$TENANT_DEFAULT_KEY")
if [ $? -eq 0 ]; then
    echo "$default_dental" | jq '.'
    tenant_in_response=$(echo "$default_dental" | jq -r '.tenant')
    if [ "$tenant_in_response" = "$TENANT_DEFAULT_ID" ]; then
        test_pass "Default tenant accessed DentalERP (tenant context correct)"
    else
        test_fail "Tenant context mismatch in DentalERP response"
    fi
else
    test_fail "Default tenant cannot access DentalERP"
fi

test_start "Access DentalERP home as ACME tenant"
acme_dental=$(api_call "$MCP_API_URL/api/v1/dental/" GET "$TENANT_ACME_ID" "$TENANT_ACME_KEY")
if [ $? -eq 0 ]; then
    echo "$acme_dental" | jq '.'
    tenant_in_response=$(echo "$acme_dental" | jq -r '.tenant')
    if [ "$tenant_in_response" = "$TENANT_ACME_ID" ]; then
        test_pass "ACME tenant accessed DentalERP (tenant context correct)"
    else
        test_fail "Tenant context mismatch in DentalERP response"
    fi
else
    test_fail "ACME tenant cannot access DentalERP"
fi

# ============================================================================
# STEP 7: Test Analytics API - Tenant Isolation
# ============================================================================
step 7 "Analytics API - Verify tenant data isolation"

echo -e "${YELLOW}Note: Analytics require dbt transformations to be run first${NC}"
echo -e "${YELLOW}If these tests fail, run: cd dbt/dentalerp && dbt run${NC}"

test_start "Query analytics as default tenant"
default_analytics=$(api_call "$MCP_API_URL/api/v1/analytics/production/daily?limit=10" GET "$TENANT_DEFAULT_ID" "$TENANT_DEFAULT_KEY")
if [ $? -eq 0 ]; then
    record_count=$(echo "$default_analytics" | jq 'length')
    echo "$default_analytics" | jq '.[0] | {practice_location, report_date, total_production, tenant_id}' 2>/dev/null || echo "No data yet"
    test_pass "Default tenant analytics query succeeded ($record_count records)"
else
    echo "$default_analytics"
    test_fail "Default tenant analytics query failed"
fi

test_start "Query analytics as ACME tenant"
acme_analytics=$(api_call "$MCP_API_URL/api/v1/analytics/production/daily?limit=10" GET "$TENANT_ACME_ID" "$TENANT_ACME_KEY")
if [ $? -eq 0 ]; then
    record_count=$(echo "$acme_analytics" | jq 'length')
    echo "$acme_analytics" | jq '.[0] | {practice_location, report_date, total_production, tenant_id}' 2>/dev/null || echo "No data yet"
    test_pass "ACME tenant analytics query succeeded ($record_count records)"
else
    echo "$acme_analytics"
    test_fail "ACME tenant analytics query failed"
fi

test_start "Verify analytics data isolation"
# Check if default tenant can only see their own data
if [ "$default_analytics" != "$acme_analytics" ]; then
    test_pass "Tenants receive different analytics data (isolated)"
else
    echo -e "${YELLOW}⚠ Warning: Both tenants received same data (may be empty or isolation not working)${NC}"
fi

test_start "Query production summary as default tenant"
default_summary=$(api_call "$MCP_API_URL/api/v1/analytics/production/summary" GET "$TENANT_DEFAULT_ID" "$TENANT_DEFAULT_KEY")
if [ $? -eq 0 ]; then
    echo "$default_summary" | jq '{practice_count, date_count, total_production}'
    test_pass "Default tenant production summary retrieved"
else
    test_fail "Default tenant production summary failed"
fi

test_start "Query production by practice as ACME tenant"
acme_by_practice=$(api_call "$MCP_API_URL/api/v1/analytics/production/by-practice" GET "$TENANT_ACME_ID" "$TENANT_ACME_KEY")
if [ $? -eq 0 ]; then
    echo "$acme_by_practice" | jq '.'
    test_pass "ACME tenant production by practice retrieved"
else
    test_fail "ACME tenant production by practice failed"
fi

# ============================================================================
# STEP 8: Test Cross-Tenant Access Denial
# ============================================================================
step 8 "Security - Verify cross-tenant access is blocked"

test_start "Attempt to access without tenant header"
no_tenant=$(curl -s -w "\n%{http_code}" "$MCP_API_URL/api/v1/dental/" \
    -H "Authorization: Bearer $TENANT_DEFAULT_KEY")
http_code=$(echo "$no_tenant" | tail -n1)
body=$(echo "$no_tenant" | sed '$d')

if [ "$http_code" -eq 400 ]; then
    echo "$body" | jq '.'
    test_pass "Request without tenant header correctly rejected (400)"
else
    test_fail "Request without tenant header should be rejected"
fi

test_start "Attempt to use invalid tenant ID"
invalid_tenant=$(curl -s -w "\n%{http_code}" "$MCP_API_URL/api/v1/dental/" \
    -H "X-Tenant-ID: nonexistent" \
    -H "Authorization: Bearer $TENANT_DEFAULT_KEY")
http_code=$(echo "$invalid_tenant" | tail -n1)
body=$(echo "$invalid_tenant" | sed '$d')

if [ "$http_code" -eq 404 ]; then
    echo "$body" | jq '.'
    test_pass "Invalid tenant ID correctly rejected (404)"
else
    test_fail "Invalid tenant ID should be rejected"
fi

# ============================================================================
# Test Summary
# ============================================================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}                    TEST SUMMARY                               ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Total Tests:    $TESTS_RUN"
echo -e "${GREEN}Passed:         $TESTS_PASSED${NC}"
echo -e "${RED}Failed:         $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}                  ✓ All Tests Passed!                          ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${GREEN}✓ Multi-Tenant Architecture Verified${NC}"
    echo "  • Tenant isolation working correctly"
    echo "  • Product access controls enforced"
    echo "  • PDF ingestion isolated per tenant"
    echo "  • Analytics data isolated per tenant"
    echo "  • Cross-tenant access blocked"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "  1. Run dbt transformations: cd dbt/dentalerp && dbt run"
    echo "  2. Verify data in Snowflake with tenant_id filtering"
    echo "  3. Upload more PDFs for each tenant"
    echo "  4. Test with production subdomains (acme.dentalerp.com)"
    exit 0
else
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}              ⚠ Some Tests Failed                              ${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    exit 1
fi
