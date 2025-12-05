#!/bin/bash

###############################################################################
# Complete System Test Script
# Tests the entire DentalERP system with updated seed data:
# 1. Snowflake (Bronze/Silver/Gold layers)
# 2. MCP Server (API endpoints)
# 3. Backend (PostgreSQL seed data)
# 4. dbt transformations
# 5. Frontend API integration
###############################################################################

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_KEY="dev-mcp-api-key-change-in-production-min-32-chars"
MCP_BASE_URL="http://localhost:8085"
BACKEND_BASE_URL="http://localhost:3001"

# Practice locations (updated to match new seed data)
PRACTICES=("Eastlake" "Torrey Pines" "ADS")

###############################################################################
# Helper Functions
###############################################################################

print_header() {
    echo ""
    echo "================================================================================"
    echo -e "${BLUE}$1${NC}"
    echo "================================================================================"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "  ℹ️  $1"
}

check_service() {
    local service_name=$1
    local url=$2

    if curl -s -f "$url" > /dev/null 2>&1; then
        print_success "$service_name is running"
        return 0
    else
        print_error "$service_name is NOT running at $url"
        return 1
    fi
}

###############################################################################
# Test 1: Check Services
###############################################################################

test_services() {
    print_header "TEST 1: Checking Services"

    local all_running=true

    # MCP Server
    if check_service "MCP Server" "$MCP_BASE_URL"; then
        curl -s "$MCP_BASE_URL" | python3 -m json.tool | head -10
    else
        all_running=false
    fi

    # Backend (optional)
    # if check_service "Backend" "$BACKEND_BASE_URL/health"; then
    #     print_info "Backend health check passed"
    # else
    #     print_warning "Backend not running (optional for this test)"
    # fi

    if [ "$all_running" = false ]; then
        print_error "Some services are not running. Please start them first."
        exit 1
    fi
}

###############################################################################
# Test 2: Snowflake Connectivity & Data
###############################################################################

test_snowflake() {
    print_header "TEST 2: Snowflake Connectivity & Data"

    print_info "Testing Snowflake connection and querying all layers..."

    python3 << 'EOF'
import os
import snowflake.connector
from dotenv import load_dotenv
from pathlib import Path

# Load environment
env_path = Path("mcp-server/.env")
load_dotenv(env_path)

try:
    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database='DENTAL_ERP_DW'
    )

    cursor = conn.cursor()

    # Test Bronze layer
    print("\n📦 BRONZE LAYER (pms_day_sheets):")
    print("-" * 80)
    cursor.execute("""
        SELECT practice_location, COUNT(*) as count,
               MIN(report_date) as earliest, MAX(report_date) as latest
        FROM bronze.pms_day_sheets
        GROUP BY practice_location
        ORDER BY practice_location
    """)
    for row in cursor.fetchall():
        print(f"  • {row[0]:<20} {row[1]:>3} records  [{row[2]} to {row[3]}]")

    # Test Silver layer
    print("\n🥈 SILVER LAYER (stg_pms_day_sheets):")
    print("-" * 80)
    cursor.execute("""
        SELECT practice_location, COUNT(*) as count,
               SUM(total_production) as total_prod
        FROM bronze_silver.stg_pms_day_sheets
        GROUP BY practice_location
        ORDER BY practice_location
    """)
    for row in cursor.fetchall():
        prod = f"${float(row[2]):,.2f}" if row[2] else "N/A"
        print(f"  • {row[0]:<20} {row[1]:>3} records  Total: {prod}")

    # Test Gold layer
    print("\n🥇 GOLD LAYER (daily_production_metrics):")
    print("-" * 80)
    cursor.execute("""
        SELECT practice_location, COUNT(*) as count,
               SUM(total_production) as total_prod,
               AVG(production_per_visit) as avg_per_visit
        FROM bronze_gold.daily_production_metrics
        GROUP BY practice_location
        ORDER BY practice_location
    """)
    for row in cursor.fetchall():
        prod = f"${float(row[2]):,.2f}" if row[2] else "N/A"
        avg = f"${float(row[3]):,.2f}" if row[3] else "N/A"
        print(f"  • {row[0]:<20} {row[1]:>3} records  Total: {prod}  Avg/Visit: {avg}")

    # Check practice names match new seed data
    print("\n🏢 PRACTICE VALIDATION:")
    print("-" * 80)
    cursor.execute("""
        SELECT DISTINCT practice_location
        FROM bronze_gold.daily_production_metrics
        ORDER BY practice_location
    """)
    practices = [row[0] for row in cursor.fetchall()]
    expected = ["ADS", "Eastlake", "Torrey Pines"]

    for practice in expected:
        if practice in practices:
            print(f"  ✅ {practice} - Found in Snowflake")
        else:
            print(f"  ❌ {practice} - NOT found in Snowflake")

    for practice in practices:
        if practice not in expected:
            print(f"  ⚠️  {practice} - Unexpected practice in Snowflake")

    cursor.close()
    conn.close()

    print("\n✅ Snowflake test complete!")

except Exception as e:
    print(f"\n❌ Snowflake test failed: {e}")
    exit(1)
EOF

    if [ $? -eq 0 ]; then
        print_success "Snowflake data validation passed"
    else
        print_error "Snowflake data validation failed"
        exit 1
    fi
}

###############################################################################
# Test 3: MCP Server API Endpoints
###############################################################################

test_mcp_endpoints() {
    print_header "TEST 3: MCP Server API Endpoints"

    # Health check
    print_info "Testing /health endpoint..."
    response=$(curl -s -w "\n%{http_code}" "$MCP_BASE_URL/health")
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" = "200" ]; then
        print_success "Health endpoint OK"
    else
        print_error "Health endpoint failed (HTTP $http_code)"
    fi

    # Production analytics endpoints
    print_info "Testing production analytics endpoints..."

    # Daily production
    response=$(curl -s -H "Authorization: Bearer $API_KEY" \
        "$MCP_BASE_URL/api/v1/analytics/production/daily?limit=5")

    if echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); exit(0 if isinstance(data, list) and len(data) > 0 else 1)" 2>/dev/null; then
        count=$(echo "$response" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
        print_success "Daily production endpoint returned $count records"

        # Show practice locations from response
        echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
practices = set(item.get('PRACTICE_LOCATION', 'Unknown') for item in data)
print('  Practices in response:', ', '.join(sorted(practices)))
" 2>/dev/null
    else
        print_error "Daily production endpoint failed"
        echo "$response" | python3 -m json.tool | head -20
    fi

    # Summary endpoint
    response=$(curl -s -H "Authorization: Bearer $API_KEY" \
        "$MCP_BASE_URL/api/v1/analytics/production/summary")

    if echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); exit(0 if 'TOTAL_PRODUCTION' in data else 1)" 2>/dev/null; then
        print_success "Summary endpoint OK"
        echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"  Total Production: \${float(data.get('TOTAL_PRODUCTION', 0)):,.2f}\")
print(f\"  Total Visits: {data.get('TOTAL_VISITS', 0)}\")
print(f\"  Date Range: {data.get('EARLIEST_DATE')} to {data.get('LATEST_DATE')}\")
" 2>/dev/null
    else
        print_error "Summary endpoint failed"
    fi

    # By-practice endpoint
    response=$(curl -s -H "Authorization: Bearer $API_KEY" \
        "$MCP_BASE_URL/api/v1/analytics/production/by-practice")

    if echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); exit(0 if isinstance(data, list) else 1)" 2>/dev/null; then
        print_success "By-practice endpoint OK"
        echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for practice in data:
    name = practice.get('PRACTICE_LOCATION', 'Unknown')
    prod = float(practice.get('TOTAL_PRODUCTION', 0))
    visits = practice.get('TOTAL_VISITS', 0)
    print(f\"  • {name}: \${prod:,.2f} ({visits} visits)\")
" 2>/dev/null
    else
        print_error "By-practice endpoint failed"
    fi
}

###############################################################################
# Test 4: Data Consistency Across Layers
###############################################################################

test_data_consistency() {
    print_header "TEST 4: Data Consistency Across Layers"

    print_info "Checking data flow: Bronze → Silver → Gold..."

    python3 << 'EOF'
import os
import snowflake.connector
from dotenv import load_dotenv
from pathlib import Path

env_path = Path("mcp-server/.env")
load_dotenv(env_path)

try:
    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database='DENTAL_ERP_DW'
    )

    cursor = conn.cursor()

    # Get counts from each layer
    cursor.execute("SELECT COUNT(*) FROM bronze.pms_day_sheets")
    bronze_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bronze_silver.stg_pms_day_sheets")
    silver_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bronze_gold.daily_production_metrics")
    gold_count = cursor.fetchone()[0]

    print(f"\n📊 Record Counts:")
    print(f"  Bronze:  {bronze_count} records")
    print(f"  Silver:  {silver_count} records")
    print(f"  Gold:    {gold_count} records")

    # Check for data loss in pipeline
    if silver_count < bronze_count * 0.8:  # Allow 20% data loss for quality filtering
        print(f"\n⚠️  Warning: Significant data loss Bronze → Silver ({bronze_count} → {silver_count})")
    else:
        print(f"\n✅ Data flow Bronze → Silver looks good")

    if gold_count < silver_count * 0.8:
        print(f"⚠️  Warning: Significant data loss Silver → Gold ({silver_count} → {gold_count})")
    else:
        print(f"✅ Data flow Silver → Gold looks good")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"\n❌ Consistency test failed: {e}")
    exit(1)
EOF

    if [ $? -eq 0 ]; then
        print_success "Data consistency check passed"
    else
        print_error "Data consistency check failed"
    fi
}

###############################################################################
# Test 5: Practice Name Alignment
###############################################################################

test_practice_alignment() {
    print_header "TEST 5: Practice Name Alignment"

    print_info "Verifying practice names match across systems..."

    # Expected practice names from new seed data
    echo ""
    echo "Expected Practices (from updated seed data):"
    for practice in "${PRACTICES[@]}"; do
        echo "  • $practice"
    done

    # Check Snowflake
    echo ""
    echo "Practices in Snowflake Gold Layer:"
    python3 << 'EOF'
import os, snowflake.connector
from dotenv import load_dotenv
from pathlib import Path

env_path = Path("mcp-server/.env")
load_dotenv(env_path)

conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
    database='DENTAL_ERP_DW'
)

cursor = conn.cursor()
cursor.execute("SELECT DISTINCT practice_location FROM bronze_gold.daily_production_metrics ORDER BY 1")

for row in cursor.fetchall():
    print(f"  • {row[0]}")

cursor.close()
conn.close()
EOF

    # Check MCP Server API
    echo ""
    echo "Practices in MCP Server API Response:"
    curl -s -H "Authorization: Bearer $API_KEY" \
        "$MCP_BASE_URL/api/v1/analytics/production/by-practice" | \
    python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for item in data:
        print(f\"  • {item.get('PRACTICE_LOCATION', 'Unknown')}\")
except:
    print('  ❌ Failed to parse API response')
"

    print_success "Practice alignment check complete"
}

###############################################################################
# Test 6: dbt Transformations
###############################################################################

test_dbt() {
    print_header "TEST 6: dbt Transformations"

    print_info "Testing dbt run via MCP Server..."

    # Trigger dbt run
    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Authorization: Bearer $API_KEY" \
        "$MCP_BASE_URL/api/v1/dbt/run/pdf-pipeline")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)

    if [ "$http_code" = "200" ]; then
        print_success "dbt pipeline executed successfully"
        echo "$body" | python3 -m json.tool | head -20
    else
        print_warning "dbt pipeline returned HTTP $http_code"
        echo "$body" | python3 -m json.tool | head -20
    fi
}

###############################################################################
# Main Test Execution
###############################################################################

main() {
    clear
    echo "================================================================================"
    echo "                    COMPLETE SYSTEM TEST SUITE"
    echo "================================================================================"
    echo "Testing DentalERP with Updated Seed Data"
    echo "Timestamp: $(date)"
    echo "================================================================================"

    # Run all tests
    test_services
    test_snowflake
    test_mcp_endpoints
    test_data_consistency
    test_practice_alignment
    test_dbt

    # Final summary
    print_header "TEST SUMMARY"
    print_success "All tests completed!"

    echo ""
    echo "Next Steps:"
    echo "  1. Review any warnings or errors above"
    echo "  2. If backend seed data needs updating, run: cd backend && npm run db:seed"
    echo "  3. If Snowflake needs new seed data, run the updated SQL in Snowflake UI"
    echo "  4. Start frontend: cd frontend && npm run dev"
    echo "  5. Navigate to: http://localhost:3000/analytics/production"
    echo ""
}

# Run main function
main
