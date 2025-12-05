#!/bin/bash
#
# dbt Run Script - Executes dbt transformations with Snowflake credentials
# Usage: ./run-dbt.sh [command]
#
# Prerequisites: Snowflake migration must be complete first
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}        dbt Transformations - DentalERP                          ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Load Snowflake credentials from mcp-server/.env
if [ -f "mcp-server/.env" ]; then
    export $(grep -v '^#' mcp-server/.env | grep SNOWFLAKE | xargs)
    echo -e "${GREEN}✓${NC} Loaded Snowflake credentials from mcp-server/.env"
else
    echo -e "${RED}✗${NC} mcp-server/.env not found!"
    exit 1
fi

# Verify required env vars
required_vars=("SNOWFLAKE_ACCOUNT" "SNOWFLAKE_USER" "SNOWFLAKE_PASSWORD" "SNOWFLAKE_DATABASE")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}✗${NC} Missing required environment variable: $var"
        exit 1
    fi
done

echo -e "${GREEN}✓${NC} Snowflake Account: $SNOWFLAKE_ACCOUNT"
echo -e "${GREEN}✓${NC} Snowflake Database: $SNOWFLAKE_DATABASE"
echo -e "${GREEN}✓${NC} Snowflake Warehouse: ${SNOWFLAKE_WAREHOUSE:-COMPUTE_WH}"
echo ""

# Navigate to dbt project
cd dbt/dentalerp

# Get command (default: run)
COMMAND=${1:-run}

echo -e "${BLUE}───────────────────────────────────────────────────────────────${NC}"
echo -e "${YELLOW}Running: dbt $COMMAND${NC}"
echo -e "${BLUE}───────────────────────────────────────────────────────────────${NC}"
echo ""

# Execute dbt command
case $COMMAND in
    "run")
        echo -e "${YELLOW}→ dbt run (transform all models)${NC}"
        dbt run
        ;;
    "test")
        echo -e "${YELLOW}→ dbt test (validate data quality)${NC}"
        dbt test
        ;;
    "debug")
        echo -e "${YELLOW}→ dbt debug (test connection)${NC}"
        dbt debug
        ;;
    "compile")
        echo -e "${YELLOW}→ dbt compile (check SQL syntax)${NC}"
        dbt compile
        ;;
    "deps")
        echo -e "${YELLOW}→ dbt deps (install dependencies)${NC}"
        dbt deps
        ;;
    "docs")
        echo -e "${YELLOW}→ dbt docs generate${NC}"
        dbt docs generate
        echo -e "${YELLOW}→ dbt docs serve${NC}"
        dbt docs serve
        ;;
    "full")
        echo -e "${YELLOW}→ Full pipeline: deps → run → test${NC}"
        dbt deps
        dbt run
        dbt test
        ;;
    *)
        echo -e "${YELLOW}→ dbt $COMMAND${NC}"
        dbt $COMMAND
        ;;
esac

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ dbt $COMMAND completed successfully!${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""

    if [ "$COMMAND" = "run" ] || [ "$COMMAND" = "full" ]; then
        echo -e "${YELLOW}Next Steps:${NC}"
        echo "  1. Verify data in Snowflake:"
        echo "     SELECT tenant_id, COUNT(*) FROM bronze_gold.daily_production_metrics GROUP BY tenant_id;"
        echo "  2. Fix Snowflake async issue (if not done yet)"
        echo "  3. Run test suite: ./test-multi-tenant-e2e.sh"
        echo ""
    fi
else
    echo ""
    echo -e "${RED}✗ dbt $COMMAND failed!${NC}"
    echo ""
    echo -e "${YELLOW}Common Issues:${NC}"
    echo "  • Snowflake migration not executed → Run snowflake-multi-tenant-migration.sql first"
    echo "  • Wrong credentials → Check mcp-server/.env"
    echo "  • Network issues → Check Snowflake connectivity"
    echo "  • Model errors → Review error message above"
    echo ""
    exit 1
fi
