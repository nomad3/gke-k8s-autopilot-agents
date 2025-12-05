#!/bin/bash
# MCP Server Test Runner
# Runs different test suites with proper setup

set -e

echo "🧪 MCP Server Test Suite"
echo "========================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Parse arguments
TEST_TYPE=${1:-all}
RUN_INTEGRATION=${2:-false}

# Set up test environment
export ENVIRONMENT=test
export DEBUG=true
export MCP_API_KEY=test-api-key-for-integration-testing-min-32-chars
export SECRET_KEY=test-secret-key-for-integration-testing-min-32-chars
export POSTGRES_HOST=localhost
export POSTGRES_DB=mcp_test
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
export REDIS_HOST=localhost

echo "Test Environment:"
echo "  Type: $TEST_TYPE"
echo "  Integration Tests: $RUN_INTEGRATION"
echo ""

# Function to run tests
run_tests() {
    local test_path=$1
    local markers=$2
    local description=$3
    
    echo -e "${YELLOW}Running $description...${NC}"
    
    if [ "$RUN_INTEGRATION" == "true" ]; then
        pytest "$test_path" -m "$markers" --run-integration
    else
        pytest "$test_path" -m "$markers"
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $description passed${NC}"
    else
        echo -e "${RED}❌ $description failed${NC}"
        exit 1
    fi
    echo ""
}

# Run test suites based on type
case $TEST_TYPE in
    unit)
        echo "📦 Running Unit Tests Only"
        run_tests "tests/" "unit" "Unit Tests"
        ;;
    
    integration)
        echo "🔗 Running Integration Tests"
        run_tests "tests/test_integration/" "integration" "Integration Tests"
        ;;
    
    e2e)
        echo "🎯 Running End-to-End Tests"
        run_tests "tests/test_integration/test_e2e_workflow.py" "e2e" "E2E Workflow Tests"
        ;;
    
    all)
        echo "🚀 Running All Tests"
        run_tests "tests/" "not integration" "Unit Tests"
        
        if [ "$RUN_INTEGRATION" == "true" ]; then
            run_tests "tests/" "integration" "Integration Tests"
        else
            echo -e "${YELLOW}⚠️  Skipping integration tests (use: ./run-tests.sh all true)${NC}"
        fi
        ;;
    
    coverage)
        echo "📊 Running Tests with Coverage Report"
        pytest tests/ --cov=src --cov-report=html --cov-report=term
        echo ""
        echo "Coverage report generated: htmlcov/index.html"
        echo "Open with: open htmlcov/index.html"
        ;;
    
    *)
        echo "Usage: ./run-tests.sh [unit|integration|e2e|all|coverage] [true|false]"
        echo ""
        echo "Examples:"
        echo "  ./run-tests.sh unit              # Run unit tests only"
        echo "  ./run-tests.sh integration true  # Run integration tests with external services"
        echo "  ./run-tests.sh e2e true          # Run end-to-end workflow tests"
        echo "  ./run-tests.sh all true          # Run all tests including integration"
        echo "  ./run-tests.sh coverage          # Generate coverage report"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Test suite completed successfully!${NC}"

