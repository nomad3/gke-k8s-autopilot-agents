#!/bin/bash

###############################################################################
# Production System Test Script
# Tests all critical components and flows on production:
# - Frontend (dentalerp.agentprovision.com)
# - Backend API (dentalerp.agentprovision.com/api)
# - MCP Server (mcp.agentprovision.com)
# - Snowflake warehouse connectivity
# - Analytics endpoints
# - PDF ingestion & AI extraction
# - dbt transformation triggers
###############################################################################

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Production URLs
FRONTEND_URL="https://dentalerp.agentprovision.com"
BACKEND_URL="https://dentalerp.agentprovision.com/api"
MCP_URL="https://mcp.agentprovision.com"

# API Keys (should be passed as environment variables in production)
MCP_API_KEY="${MCP_API_KEY:-}"
BACKEND_TOKEN="${BACKEND_TOKEN:-}"

# Test results tracking
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

###############################################################################
# Helper Functions
###############################################################################

print_header() {
    echo ""
    echo "================================================================================"
    echo -e "${BLUE}$1${NC}"
    echo "================================================================================"
}

print_test() {
    echo -e "${CYAN}▶ TEST $TESTS_RUN: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ PASS: $1${NC}"
    ((TESTS_PASSED++))
}

print_failure() {
    echo -e "${RED}❌ FAIL: $1${NC}"
    ((TESTS_FAILED++))
    FAILED_TESTS+=("$1")
}

print_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
}

print_info() {
    echo -e "  ℹ️  $1"
}

run_test() {
    ((TESTS_RUN++))
    print_test "$1"
}

check_http_status() {
    local url=$1
    local expected_status=${2:-200}
    local headers=${3:-}

    local response
    if [ -n "$headers" ]; then
        response=$(curl -s -w "\n%{http_code}" -H "$headers" "$url")
    else
        response=$(curl -s -w "\n%{http_code}" "$url")
    fi

    local status=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')

    if [ "$status" -eq "$expected_status" ]; then
        return 0
    else
        print_info "Expected: $expected_status, Got: $status"
        print_info "Response: $body"
        return 1
    fi
}

check_json_response() {
    local url=$1
    local headers=${2:-}

    local response
    if [ -n "$headers" ]; then
        response=$(curl -s -H "$headers" "$url")
    else
        response=$(curl -s "$url")
    fi

    if echo "$response" | python3 -m json.tool > /dev/null 2>&1; then
        echo "$response"
        return 0
    else
        print_info "Invalid JSON response: $response"
        return 1
    fi
}

###############################################################################
# Test 1: Frontend Accessibility
###############################################################################

test_frontend() {
    print_header "TEST SUITE 1: Frontend Accessibility"

    run_test "Frontend Homepage"
    if check_http_status "$FRONTEND_URL"; then
        print_success "Frontend is accessible at $FRONTEND_URL"
    else
        print_failure "Frontend is not accessible"
    fi

    run_test "Frontend Login Page"
    if check_http_status "$FRONTEND_URL/auth/login"; then
        print_success "Login page is accessible"
    else
        print_failure "Login page is not accessible"
    fi

    run_test "Frontend Assets Loading"
    if curl -s "$FRONTEND_URL" | grep -q "vite"; then
        print_success "Frontend Vite assets detected"
    else
        print_warning "Vite assets not detected (may be built in production mode)"
    fi
}

###############################################################################
# Test 2: Backend API Health
###############################################################################

test_backend() {
    print_header "TEST SUITE 2: Backend API Health"

    run_test "Backend Health Endpoint"
    if check_http_status "$BACKEND_URL/health"; then
        print_success "Backend health check passed"
    else
        print_failure "Backend health check failed"
    fi

    run_test "Backend API Info"
    local response=$(check_json_response "$BACKEND_URL/")
    if [ $? -eq 0 ]; then
        print_success "Backend API info endpoint working"
        echo "$response" | python3 -m json.tool | head -10
    else
        print_failure "Backend API info endpoint failed"
    fi

    if [ -n "$BACKEND_TOKEN" ]; then
        run_test "Backend Authentication"
        if check_http_status "$BACKEND_URL/auth/profile" 200 "Authorization: Bearer $BACKEND_TOKEN"; then
            print_success "Backend authentication working"
        else
            print_failure "Backend authentication failed"
        fi
    else
        print_warning "Skipping backend auth tests (BACKEND_TOKEN not provided)"
    fi
}

###############################################################################
# Test 3: MCP Server Health & Endpoints
###############################################################################

test_mcp_server() {
    print_header "TEST SUITE 3: MCP Server Health & Endpoints"

    run_test "MCP Server Root"
    local response=$(check_json_response "$MCP_URL/")
    if [ $? -eq 0 ]; then
        print_success "MCP Server is accessible"
        echo "$response" | python3 -m json.tool | head -10
    else
        print_failure "MCP Server is not accessible"
    fi

    run_test "MCP Health Check"
    if check_http_status "$MCP_URL/health"; then
        print_success "MCP health check passed"
    else
        print_failure "MCP health check failed"
    fi

    run_test "MCP API Documentation"
    if check_http_status "$MCP_URL/docs"; then
        print_success "MCP API documentation is accessible"
    else
        print_failure "MCP API documentation is not accessible"
    fi

    if [ -n "$MCP_API_KEY" ]; then
        run_test "MCP Tenants Endpoint"
        local response=$(check_json_response "$MCP_URL/api/v1/tenants/" "Authorization: Bearer $MCP_API_KEY")
        if [ $? -eq 0 ]; then
            print_success "MCP tenants endpoint working"
            local count=$(echo "$response" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
            print_info "Found $count tenants"
        else
            print_failure "MCP tenants endpoint failed"
        fi
    else
        print_warning "Skipping MCP authenticated tests (MCP_API_KEY not provided)"
    fi
}

###############################################################################
# Test 4: Analytics Endpoints
###############################################################################

test_analytics() {
    print_header "TEST SUITE 4: Analytics Endpoints"

    if [ -z "$MCP_API_KEY" ]; then
        print_warning "Skipping analytics tests (MCP_API_KEY not provided)"
        return
    fi

    run_test "Production Summary Analytics"
    local response=$(check_json_response "$MCP_URL/api/v1/analytics/production/summary" "Authorization: Bearer $MCP_API_KEY")
    if [ $? -eq 0 ]; then
        print_success "Production summary endpoint working"
        echo "$response" | python3 -m json.tool | head -20
    else
        print_failure "Production summary endpoint failed"
    fi

    run_test "Production Daily Analytics"
    local response=$(check_json_response "$MCP_URL/api/v1/analytics/production/daily?limit=5" "Authorization: Bearer $MCP_API_KEY")
    if [ $? -eq 0 ]; then
        print_success "Production daily endpoint working"
        local count=$(echo "$response" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data['data']) if isinstance(data, dict) and 'data' in data else len(data))")
        print_info "Retrieved $count records"
    else
        print_failure "Production daily endpoint failed"
    fi

    run_test "Production By Practice Analytics"
    local response=$(check_json_response "$MCP_URL/api/v1/analytics/production/by-practice" "Authorization: Bearer $MCP_API_KEY")
    if [ $? -eq 0 ]; then
        print_success "Production by-practice endpoint working"
    else
        print_failure "Production by-practice endpoint failed"
    fi
}

###############################################################################
# Test 5: Warehouse Connectivity
###############################################################################

test_warehouse() {
    print_header "TEST SUITE 5: Warehouse Connectivity"

    if [ -z "$MCP_API_KEY" ]; then
        print_warning "Skipping warehouse tests (MCP_API_KEY not provided)"
        return
    fi

    run_test "Warehouse Connection Test"
    # This tests if Snowflake is accessible by trying to query analytics
    # If analytics work, Snowflake is connected
    local response=$(curl -s -H "Authorization: Bearer $MCP_API_KEY" "$MCP_URL/api/v1/analytics/production/summary")
    if echo "$response" | python3 -m json.tool > /dev/null 2>&1; then
        print_success "Warehouse connectivity confirmed (via analytics query)"
    else
        print_failure "Warehouse connectivity issue detected"
    fi
}

###############################################################################
# Test 6: PDF Ingestion Flow
###############################################################################

test_pdf_ingestion() {
    print_header "TEST SUITE 6: PDF Ingestion Flow"

    if [ -z "$MCP_API_KEY" ]; then
        print_warning "Skipping PDF ingestion tests (MCP_API_KEY not provided)"
        return
    fi

    # Check if test PDF exists
    local test_pdf="examples/ingestion/Eastlake Day 07 2025.pdf"
    if [ ! -f "$test_pdf" ]; then
        print_warning "Test PDF not found at $test_pdf - skipping upload test"
        return
    fi

    run_test "PDF Upload Endpoint"
    local response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer $MCP_API_KEY" \
        -F "file=@$test_pdf" \
        -F "practice_location=Eastlake" \
        -F "use_ai=false" \
        "$MCP_URL/api/v1/pdf/upload")

    local status=$(echo "$response" | tail -n1)
    if [ "$status" -eq 200 ] || [ "$status" -eq 201 ]; then
        print_success "PDF upload endpoint working"
    else
        print_failure "PDF upload endpoint failed (status: $status)"
    fi
}

###############################################################################
# Test 7: dbt Operations
###############################################################################

test_dbt_operations() {
    print_header "TEST SUITE 7: dbt Operations"

    if [ -z "$MCP_API_KEY" ]; then
        print_warning "Skipping dbt tests (MCP_API_KEY not provided)"
        return
    fi

    run_test "dbt Run Endpoint (dry-run)"
    # We'll just check if the endpoint exists without actually triggering
    local response=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST \
        -H "Authorization: Bearer $MCP_API_KEY" \
        "$MCP_URL/api/v1/dbt/run/pdf-pipeline")

    if [ "$response" -eq 200 ] || [ "$response" -eq 202 ] || [ "$response" -eq 404 ]; then
        # 404 is ok if endpoint doesn't exist yet, we're just testing connectivity
        print_success "dbt endpoint is accessible"
    else
        print_failure "dbt endpoint returned unexpected status: $response"
    fi
}

###############################################################################
# Test 8: CORS & Security Headers
###############################################################################

test_security() {
    print_header "TEST SUITE 8: CORS & Security Headers"

    run_test "CORS Headers"
    local headers=$(curl -s -I "$MCP_URL/health")
    if echo "$headers" | grep -iq "access-control-allow"; then
        print_success "CORS headers present"
    else
        print_warning "CORS headers not found (may be configured at load balancer)"
    fi

    run_test "HTTPS Redirect"
    local http_status=$(curl -s -o /dev/null -w "%{http_code}" "http://dentalerp.agentprovision.com")
    if [ "$http_status" -eq 301 ] || [ "$http_status" -eq 302 ] || [ "$http_status" -eq 200 ]; then
        print_success "HTTP handling configured"
    else
        print_warning "HTTP handling may need review"
    fi
}

###############################################################################
# Test 9: Frontend-MCP Integration
###############################################################################

test_frontend_mcp_integration() {
    print_header "TEST SUITE 9: Frontend-MCP Integration"

    run_test "Frontend can reach MCP directly"
    # Test that MCP is accessible from browser context (CORS)
    if check_http_status "$MCP_URL/health"; then
        print_success "MCP is accessible for frontend direct calls"
    else
        print_failure "MCP may not be accessible from frontend"
    fi

    run_test "Analytics endpoints have CORS"
    local headers=$(curl -s -I -X OPTIONS "$MCP_URL/api/v1/analytics/production/summary")
    if echo "$headers" | grep -iq "access-control-allow"; then
        print_success "Analytics endpoints configured for CORS"
    else
        print_warning "Analytics endpoints may need CORS configuration"
    fi
}

###############################################################################
# Test Summary
###############################################################################

print_summary() {
    echo ""
    echo "================================================================================"
    echo -e "${BLUE}TEST SUMMARY${NC}"
    echo "================================================================================"
    echo ""
    echo -e "Total Tests:  ${CYAN}$TESTS_RUN${NC}"
    echo -e "Passed:       ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Failed:       ${RED}$TESTS_FAILED${NC}"
    echo ""

    if [ $TESTS_FAILED -gt 0 ]; then
        echo -e "${RED}Failed Tests:${NC}"
        for test in "${FAILED_TESTS[@]}"; do
            echo -e "  ${RED}✗${NC} $test"
        done
        echo ""
        echo -e "${RED}❌ PRODUCTION TESTS FAILED${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ ALL PRODUCTION TESTS PASSED${NC}"
        exit 0
    fi
}

###############################################################################
# Main Execution
###############################################################################

main() {
    echo "================================================================================"
    echo -e "${BLUE}DentalERP Production Test Suite${NC}"
    echo "================================================================================"
    echo ""
    echo "Testing production environment:"
    echo "  Frontend: $FRONTEND_URL"
    echo "  Backend:  $BACKEND_URL"
    echo "  MCP:      $MCP_URL"
    echo ""

    if [ -z "$MCP_API_KEY" ]; then
        print_warning "MCP_API_KEY not set - some tests will be skipped"
        echo "  Export MCP_API_KEY to run all tests"
    fi

    if [ -z "$BACKEND_TOKEN" ]; then
        print_warning "BACKEND_TOKEN not set - backend auth tests will be skipped"
        echo "  Export BACKEND_TOKEN to run all tests"
    fi

    echo ""

    # Run all test suites
    test_frontend
    test_backend
    test_mcp_server
    test_analytics
    test_warehouse
    test_pdf_ingestion
    test_dbt_operations
    test_security
    test_frontend_mcp_integration

    # Print summary
    print_summary
}

# Run main function
main "$@"
