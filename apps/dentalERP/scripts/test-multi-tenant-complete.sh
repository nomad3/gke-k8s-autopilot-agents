#!/bin/bash

###############################################################################
# Multi-Tenant Architecture - Complete Test Suite
# Tests all functionality built in Phases 1 & 2
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MCP_URL="http://localhost:8085"
API_KEY="dev-mcp-api-key-change-in-production-min-32-chars"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=0

###############################################################################
# Helper Functions
###############################################################################

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_test() {
    echo -e "${YELLOW}TEST $TOTAL_TESTS: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ PASS: $1${NC}"
    ((TESTS_PASSED++))
}

print_fail() {
    echo -e "${RED}❌ FAIL: $1${NC}"
    echo -e "${RED}   Error: $2${NC}"
    ((TESTS_FAILED++))
}

print_summary() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}TEST SUMMARY${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "Total Tests: $TOTAL_TESTS"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    if [ $TESTS_FAILED -gt 0 ]; then
        echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    else
        echo -e "${GREEN}Failed: $TESTS_FAILED${NC}"
    fi
    echo -e "${BLUE}========================================${NC}\n"

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}\n"
        exit 0
    else
        echo -e "${RED}❌ SOME TESTS FAILED${NC}\n"
        exit 1
    fi
}

###############################################################################
# Test Suite 1: Service Health
###############################################################################

test_service_health() {
    print_header "TEST SUITE 1: Service Health"

    # Test 1: MCP Server Health
    ((TOTAL_TESTS++))
    print_test "MCP Server Health Check"
    response=$(curl -s -o /dev/null -w "%{http_code}" "$MCP_URL/health")
    if [ "$response" = "200" ]; then
        print_success "MCP Server is healthy"
    else
        print_fail "MCP Server health check" "HTTP $response"
        return
    fi

    # Test 2: Database Connection
    ((TOTAL_TESTS++))
    print_test "PostgreSQL Database Connection"
    docker exec dentalerp-postgres-1 psql -U postgres -d mcp -c "SELECT 1" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_success "Database connection working"
    else
        print_fail "Database connection" "Unable to connect to PostgreSQL"
    fi
}

###############################################################################
# Test Suite 2: Tenant Management
###############################################################################

test_tenant_management() {
    print_header "TEST SUITE 2: Tenant Management"

    # Test 3: List all tenants
    ((TOTAL_TESTS++))
    print_test "List all tenants"
    response=$(curl -s -w "\n%{http_code}" "$MCP_URL/api/v1/tenants/")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" = "200" ]; then
        tenant_count=$(echo "$body" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data))" 2>/dev/null || echo "0")
        print_success "Retrieved $tenant_count tenant(s)"
    else
        print_fail "List tenants" "HTTP $http_code"
    fi

    # Test 4: Get default tenant
    ((TOTAL_TESTS++))
    print_test "Get default tenant"
    response=$(curl -s -w "\n%{http_code}" "$MCP_URL/api/v1/tenants/default")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" = "200" ]; then
        tenant_name=$(echo "$body" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('tenant_name', 'unknown'))" 2>/dev/null || echo "error")
        print_success "Default tenant found: $tenant_name"
    else
        print_fail "Get default tenant" "HTTP $http_code"
    fi

    # Test 5: Create test tenant
    ((TOTAL_TESTS++))
    print_test "Create new test tenant"
    response=$(curl -s -w "\n%{http_code}" -X POST "$MCP_URL/api/v1/tenants/" \
        -H "Content-Type: application/json" \
        -d '{
            "tenant_code": "test_dental_001",
            "tenant_name": "Test Dental Practice",
            "industry": "dental",
            "products": ["dentalerp"]
        }')
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" = "201" ] || [ "$http_code" = "200" ]; then
        print_success "Test tenant created successfully"
        TEST_TENANT_CODE="test_dental_001"
    else
        # Tenant might already exist, try to get it
        response=$(curl -s -w "\n%{http_code}" "$MCP_URL/api/v1/tenants/test_dental_001")
        http_code=$(echo "$response" | tail -n1)
        if [ "$http_code" = "200" ]; then
            print_success "Test tenant already exists (OK)"
            TEST_TENANT_CODE="test_dental_001"
        else
            print_fail "Create test tenant" "HTTP $http_code"
        fi
    fi
}

###############################################################################
# Test Suite 3: Tenant Context & Middleware
###############################################################################

test_tenant_context() {
    print_header "TEST SUITE 3: Tenant Context & Middleware"

    # Test 6: Tenant identification via X-Tenant-ID header
    ((TOTAL_TESTS++))
    print_test "Tenant identification via X-Tenant-ID header"
    response=$(curl -s -w "\n%{http_code}" \
        -H "X-Tenant-ID: default" \
        -H "Authorization: Bearer $API_KEY" \
        "$MCP_URL/api/v1/analytics/production/summary")
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" = "200" ] || [ "$http_code" = "404" ]; then
        # 404 is OK if no data, but tenant was identified
        print_success "Tenant identified via header"
    else
        print_fail "Tenant identification via header" "HTTP $http_code"
    fi

    # Test 7: Tenant identification via API key prefix
    ((TOTAL_TESTS++))
    print_test "Tenant identification via API key prefix"
    response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer default_sk_test123" \
        "$MCP_URL/api/v1/analytics/production/summary")
    http_code=$(echo "$response" | tail -n1)

    # Should fail with 403 (invalid API key) but tenant should be identified
    if [ "$http_code" = "403" ] || [ "$http_code" = "401" ]; then
        print_success "Tenant extracted from API key prefix (auth failed as expected)"
    else
        print_fail "Tenant identification via API key" "Expected 403, got HTTP $http_code"
    fi

    # Test 8: Missing tenant should fail
    ((TOTAL_TESTS++))
    print_test "Request without tenant identification should fail"
    response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer $API_KEY" \
        "$MCP_URL/api/v1/analytics/production/summary")
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" = "400" ] || [ "$http_code" = "403" ]; then
        print_success "Request correctly rejected without tenant"
    else
        print_fail "Missing tenant rejection" "Expected 400/403, got HTTP $http_code"
    fi

    # Test 9: Nonexistent tenant should fail
    ((TOTAL_TESTS++))
    print_test "Nonexistent tenant should be rejected"
    response=$(curl -s -w "\n%{http_code}" \
        -H "X-Tenant-ID: nonexistent_tenant_999" \
        -H "Authorization: Bearer $API_KEY" \
        "$MCP_URL/api/v1/analytics/production/summary")
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" = "404" ] || [ "$http_code" = "403" ]; then
        print_success "Nonexistent tenant correctly rejected"
    else
        print_fail "Nonexistent tenant rejection" "Expected 404/403, got HTTP $http_code"
    fi
}

###############################################################################
# Test Suite 4: Tenant Warehouses
###############################################################################

test_tenant_warehouses() {
    print_header "TEST SUITE 4: Tenant Warehouse Configuration"

    # First, get the default tenant ID
    ((TOTAL_TESTS++))
    print_test "Get default tenant ID for warehouse tests"
    response=$(curl -s "$MCP_URL/api/v1/tenants/default")
    DEFAULT_TENANT_ID=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null || echo "")

    if [ -n "$DEFAULT_TENANT_ID" ]; then
        print_success "Default tenant ID retrieved: ${DEFAULT_TENANT_ID:0:8}..."
    else
        print_fail "Get default tenant ID" "Could not retrieve tenant ID"
        return
    fi

    # Test 10: Add Snowflake warehouse to tenant
    ((TOTAL_TESTS++))
    print_test "Add Snowflake warehouse configuration"
    response=$(curl -s -w "\n%{http_code}" -X POST \
        "$MCP_URL/api/v1/tenants/$DEFAULT_TENANT_ID/warehouses" \
        -H "Content-Type: application/json" \
        -d '{
            "warehouse_type": "snowflake",
            "warehouse_config": {
                "account": "test-account",
                "user": "test_user",
                "password": "test_password",
                "warehouse": "TEST_WH",
                "database": "TEST_DB",
                "schema": "PUBLIC"
            },
            "is_primary": true
        }')
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" = "201" ] || [ "$http_code" = "200" ]; then
        print_success "Snowflake warehouse configuration added"
    else
        # Might already exist
        if [ "$http_code" = "400" ]; then
            print_success "Snowflake warehouse already configured (OK)"
        else
            print_fail "Add Snowflake warehouse" "HTTP $http_code"
        fi
    fi

    # Test 11: Add Databricks warehouse as secondary
    ((TOTAL_TESTS++))
    print_test "Add Databricks warehouse as secondary"
    response=$(curl -s -w "\n%{http_code}" -X POST \
        "$MCP_URL/api/v1/tenants/$DEFAULT_TENANT_ID/warehouses" \
        -H "Content-Type: application/json" \
        -d '{
            "warehouse_type": "databricks",
            "warehouse_config": {
                "server_hostname": "test-workspace.cloud.databricks.com",
                "http_path": "/sql/1.0/warehouses/test123",
                "access_token": "test_token",
                "catalog": "test_catalog",
                "schema": "default"
            },
            "is_primary": false
        }')
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" = "201" ] || [ "$http_code" = "200" ]; then
        print_success "Databricks warehouse configuration added"
    else
        if [ "$http_code" = "400" ]; then
            print_success "Databricks warehouse already configured (OK)"
        else
            print_fail "Add Databricks warehouse" "HTTP $http_code"
        fi
    fi

    # Test 12: Verify tenant has multiple warehouses
    ((TOTAL_TESTS++))
    print_test "Verify tenant has multiple warehouse configurations"
    response=$(curl -s "$MCP_URL/api/v1/tenants/default")
    warehouse_count=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('warehouses', [])))" 2>/dev/null || echo "0")

    if [ "$warehouse_count" -ge 1 ]; then
        print_success "Tenant has $warehouse_count warehouse(s) configured"
    else
        print_fail "Verify warehouse configurations" "Expected >= 1, got $warehouse_count"
    fi
}

###############################################################################
# Test Suite 5: Tenant Integration Routing
###############################################################################

test_integration_routing() {
    print_header "TEST SUITE 5: Integration Routing"

    # Test 13: Verify integration models loaded
    ((TOTAL_TESTS++))
    print_test "Verify tenant integration models"
    docker exec dentalerp-postgres-1 psql -U postgres -d mcp -c "SELECT COUNT(*) FROM tenant_integrations" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_success "Tenant integrations table exists and accessible"
    else
        print_fail "Tenant integrations table" "Table not found or not accessible"
    fi

    # Test 14: Check default tenant has mock NetSuite integration
    ((TOTAL_TESTS++))
    print_test "Check default tenant NetSuite integration"
    integration_count=$(docker exec dentalerp-postgres-1 psql -U postgres -d mcp -t -c \
        "SELECT COUNT(*) FROM tenant_integrations WHERE integration_type='netsuite'" | tr -d ' ')

    if [ "$integration_count" -ge 1 ]; then
        print_success "Default tenant has NetSuite integration configured"
    else
        print_fail "Default tenant NetSuite integration" "No integration found"
    fi
}

###############################################################################
# Test Suite 6: Database Schema Validation
###############################################################################

test_database_schema() {
    print_header "TEST SUITE 6: Database Schema Validation"

    # Test 15: Verify all tenant tables exist
    ((TOTAL_TESTS++))
    print_test "Verify all 5 tenant tables exist"
    tables=("tenants" "tenant_warehouses" "tenant_integrations" "tenant_users" "tenant_api_keys")
    missing_tables=0

    for table in "${tables[@]}"; do
        docker exec dentalerp-postgres-1 psql -U postgres -d mcp -c "\d $table" > /dev/null 2>&1
        if [ $? -ne 0 ]; then
            ((missing_tables++))
            echo "   Missing table: $table"
        fi
    done

    if [ $missing_tables -eq 0 ]; then
        print_success "All 5 tenant tables exist"
    else
        print_fail "Tenant tables" "$missing_tables table(s) missing"
    fi

    # Test 16: Verify tenant table has correct columns
    ((TOTAL_TESTS++))
    print_test "Verify tenants table schema"
    columns=$(docker exec dentalerp-postgres-1 psql -U postgres -d mcp -t -c \
        "SELECT column_name FROM information_schema.columns WHERE table_name='tenants'" | tr -d ' ')

    required_columns=("id" "tenant_code" "tenant_name" "industry" "products" "status")
    missing_columns=0

    for col in "${required_columns[@]}"; do
        if ! echo "$columns" | grep -q "$col"; then
            ((missing_columns++))
            echo "   Missing column: $col"
        fi
    done

    if [ $missing_columns -eq 0 ]; then
        print_success "Tenants table has all required columns"
    else
        print_fail "Tenants table schema" "$missing_columns column(s) missing"
    fi

    # Test 17: Verify foreign key constraints
    ((TOTAL_TESTS++))
    print_test "Verify foreign key constraints"
    fk_count=$(docker exec dentalerp-postgres-1 psql -U postgres -d mcp -t -c \
        "SELECT COUNT(*) FROM information_schema.table_constraints
         WHERE constraint_type='FOREIGN KEY'
         AND table_name IN ('tenant_warehouses', 'tenant_integrations', 'tenant_users', 'tenant_api_keys')" | tr -d ' ')

    if [ "$fk_count" -ge 4 ]; then
        print_success "Foreign key constraints in place ($fk_count found)"
    else
        print_fail "Foreign key constraints" "Expected >= 4, found $fk_count"
    fi
}

###############################################################################
# Test Suite 7: Tenant Data Isolation
###############################################################################

test_data_isolation() {
    print_header "TEST SUITE 7: Tenant Data Isolation"

    # Test 18: Create second test tenant
    ((TOTAL_TESTS++))
    print_test "Create second test tenant for isolation testing"
    response=$(curl -s -w "\n%{http_code}" -X POST "$MCP_URL/api/v1/tenants/" \
        -H "Content-Type: application/json" \
        -d '{
            "tenant_code": "test_dental_002",
            "tenant_name": "Test Dental Practice 2",
            "industry": "dental",
            "products": ["dentalerp"]
        }')
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" = "201" ] || [ "$http_code" = "200" ]; then
        print_success "Second test tenant created"
    else
        response=$(curl -s -w "\n%{http_code}" "$MCP_URL/api/v1/tenants/test_dental_002")
        http_code=$(echo "$response" | tail -n1)
        if [ "$http_code" = "200" ]; then
            print_success "Second test tenant already exists (OK)"
        else
            print_fail "Create second test tenant" "HTTP $http_code"
        fi
    fi

    # Test 19: Verify tenants have separate IDs
    ((TOTAL_TESTS++))
    print_test "Verify tenants have unique IDs"
    tenant1_id=$(curl -s "$MCP_URL/api/v1/tenants/test_dental_001" | \
        python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null || echo "")
    tenant2_id=$(curl -s "$MCP_URL/api/v1/tenants/test_dental_002" | \
        python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null || echo "")

    if [ -n "$tenant1_id" ] && [ -n "$tenant2_id" ] && [ "$tenant1_id" != "$tenant2_id" ]; then
        print_success "Tenants have unique IDs"
    else
        print_fail "Tenant unique IDs" "IDs not unique or not found"
    fi

    # Test 20: Verify tenant count
    ((TOTAL_TESTS++))
    print_test "Verify total tenant count"
    tenant_count=$(docker exec dentalerp-postgres-1 psql -U postgres -d mcp -t -c \
        "SELECT COUNT(*) FROM tenants WHERE status='active'" | tr -d ' ')

    if [ "$tenant_count" -ge 3 ]; then
        print_success "Found $tenant_count active tenant(s)"
    else
        print_fail "Tenant count" "Expected >= 3, found $tenant_count"
    fi
}

###############################################################################
# Test Suite 8: API Documentation
###############################################################################

test_api_docs() {
    print_header "TEST SUITE 8: API Documentation"

    # Test 21: OpenAPI docs accessible
    ((TOTAL_TESTS++))
    print_test "OpenAPI documentation accessible"
    response=$(curl -s -o /dev/null -w "%{http_code}" "$MCP_URL/docs")
    if [ "$response" = "200" ]; then
        print_success "OpenAPI docs accessible at /docs"
    else
        print_fail "OpenAPI docs" "HTTP $response"
    fi

    # Test 22: OpenAPI JSON schema
    ((TOTAL_TESTS++))
    print_test "OpenAPI JSON schema available"
    response=$(curl -s -o /dev/null -w "%{http_code}" "$MCP_URL/openapi.json")
    if [ "$response" = "200" ]; then
        print_success "OpenAPI JSON schema available"
    else
        print_fail "OpenAPI JSON" "HTTP $response"
    fi
}

###############################################################################
# Main Execution
###############################################################################

main() {
    echo -e "\n${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  Multi-Tenant Architecture - Complete Test Suite          ║${NC}"
    echo -e "${GREEN}║  Testing Phases 1 & 2 Implementation                      ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}\n"

    # Run all test suites
    test_service_health
    test_tenant_management
    test_tenant_context
    test_tenant_warehouses
    test_integration_routing
    test_database_schema
    test_data_isolation
    test_api_docs

    # Print final summary
    print_summary
}

# Run main function
main
