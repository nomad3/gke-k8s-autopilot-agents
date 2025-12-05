#!/bin/bash
#
# End-to-End PDF Ingestion Test
# Tests the complete flow: PDF Upload → AI Extraction → Snowflake Bronze → Query Data
#
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MCP_API_URL="${MCP_API_URL:-http://localhost:8085}"
MCP_API_KEY="${MCP_API_KEY:-dev-mcp-api-key-change-in-production-min-32-chars}"
TEST_PDF="${TEST_PDF:-examples/ingestion/Eastlake Day 07 2025.pdf}"
PRACTICE_LOCATION="${PRACTICE_LOCATION:-Eastlake}"
USE_AI="${USE_AI:-false}"  # Set to false to avoid OpenAI costs during testing

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}     PDF Ingestion End-to-End Test Suite                       ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  MCP API URL: $MCP_API_URL"
echo "  Test PDF: $TEST_PDF"
echo "  Practice Location: $PRACTICE_LOCATION"
echo "  Use AI Extraction: $USE_AI"
echo ""

# Function to print step headers
step() {
    echo ""
    echo -e "${BLUE}───────────────────────────────────────────────────────────────${NC}"
    echo -e "${GREEN}STEP $1: $2${NC}"
    echo -e "${BLUE}───────────────────────────────────────────────────────────────${NC}"
}

# Function to check command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}Error: $1 is not installed${NC}"
        exit 1
    fi
}

# Function to make API call with retry
api_call() {
    local url=$1
    local method=${2:-GET}
    local data=${3:-}
    local max_retries=3
    local retry=0

    while [ $retry -lt $max_retries ]; do
        if [ "$method" = "POST" ] && [ -n "$data" ]; then
            response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
                -H "Authorization: Bearer $MCP_API_KEY" \
                $data)
        else
            response=$(curl -s -w "\n%{http_code}" "$url" \
                -H "Authorization: Bearer $MCP_API_KEY")
        fi

        http_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | sed '$d')

        if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
            echo "$body"
            return 0
        fi

        retry=$((retry + 1))
        if [ $retry -lt $max_retries ]; then
            echo -e "${YELLOW}Request failed (HTTP $http_code), retrying...${NC}" >&2
            sleep 2
        fi
    done

    echo -e "${RED}Request failed after $max_retries attempts (HTTP $http_code)${NC}" >&2
    echo "$body" >&2
    return 1
}

# Check prerequisites
check_command curl
check_command jq
check_command python3

# Verify PDF file exists
if [ ! -f "$TEST_PDF" ]; then
    echo -e "${RED}Error: Test PDF not found: $TEST_PDF${NC}"
    exit 1
fi

# ============================================================================
# STEP 1: Health Check
# ============================================================================
step 1 "Health Check - Verify MCP Server is running"

health_response=$(api_call "$MCP_API_URL/health" GET)
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ MCP Server health check failed${NC}"
    echo "Make sure the server is running:"
    echo "  docker-compose up -d mcp-server"
    echo "  OR"
    echo "  cd mcp-server && uvicorn src.main:app --reload --port 8085"
    exit 1
fi

echo "$health_response" | jq '.'
echo -e "${GREEN}✓ MCP Server is healthy${NC}"

# ============================================================================
# STEP 2: Check Snowflake Connection
# ============================================================================
step 2 "Snowflake Connection - Verify warehouse is accessible"

warehouse_status=$(api_call "$MCP_API_URL/api/v1/warehouse/status" GET)
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Snowflake connection failed${NC}"
    echo "Check your Snowflake credentials in .env or docker-compose.yml"
    exit 1
fi

echo "$warehouse_status" | jq '.'

connected=$(echo "$warehouse_status" | jq -r '.connected')
if [ "$connected" != "true" ]; then
    echo -e "${RED}❌ Snowflake is not connected${NC}"
    exit 1
fi

warehouse_name=$(echo "$warehouse_status" | jq -r '.warehouse.WAREHOUSE')
database_name=$(echo "$warehouse_status" | jq -r '.warehouse.DATABASE')
echo -e "${GREEN}✓ Connected to Snowflake: $warehouse_name / $database_name${NC}"

# ============================================================================
# STEP 3: Get Supported Report Types
# ============================================================================
step 3 "Check Supported Report Types"

supported_types=$(api_call "$MCP_API_URL/api/v1/pdf/supported-types" GET)
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to get supported report types${NC}"
    exit 1
fi

echo "$supported_types" | jq '.supported_types'
ai_available=$(echo "$supported_types" | jq -r '.ai_extraction_available')
echo -e "${GREEN}✓ Supported types loaded${NC}"
echo "  AI extraction available: $ai_available"

# ============================================================================
# STEP 4: Preview Extraction (No Save)
# ============================================================================
step 4 "Preview Extraction - Test extraction without saving"

echo "Extracting from: $TEST_PDF"
echo "This will NOT save to database..."

preview_response=$(curl -s -w "\n%{http_code}" -X POST "$MCP_API_URL/api/v1/pdf/extract-preview" \
    -H "Authorization: Bearer $MCP_API_KEY" \
    -F "file=@$TEST_PDF" \
    -F "use_ai=$USE_AI")

http_code=$(echo "$preview_response" | tail -n1)
body=$(echo "$preview_response" | sed '$d')

if [ "$http_code" -ne 200 ]; then
    echo -e "${RED}❌ Preview extraction failed (HTTP $http_code)${NC}"
    echo "$body" | jq '.'
    exit 1
fi

echo "$body" | jq '.extraction_preview' | head -50
report_type=$(echo "$body" | jq -r '.extraction_preview.report_type')
extraction_method=$(echo "$body" | jq -r '.extraction_preview.extraction_method')

echo -e "${GREEN}✓ Preview extraction successful${NC}"
echo "  Report type detected: $report_type"
echo "  Extraction method: $extraction_method"

# ============================================================================
# STEP 5: Upload PDF to Bronze Layer
# ============================================================================
step 5 "Upload PDF - Save extracted data to Snowflake Bronze layer"

echo "Uploading: $TEST_PDF"
echo "Practice: $PRACTICE_LOCATION"
echo "Use AI: $USE_AI"

upload_response=$(curl -s -w "\n%{http_code}" -X POST "$MCP_API_URL/api/v1/pdf/upload" \
    -H "Authorization: Bearer $MCP_API_KEY" \
    -F "file=@$TEST_PDF" \
    -F "practice_location=$PRACTICE_LOCATION" \
    -F "use_ai=$USE_AI" \
    -F "uploaded_by=e2e_test")

http_code=$(echo "$upload_response" | tail -n1)
body=$(echo "$upload_response" | sed '$d')

if [ "$http_code" -ne 200 ]; then
    echo -e "${RED}❌ PDF upload failed (HTTP $http_code)${NC}"
    echo "$body" | jq '.'
    exit 1
fi

echo "$body" | jq '.'

record_id=$(echo "$body" | jq -r '.record_id')
table_name=$(echo "$body" | jq -r '.table_name')
success=$(echo "$body" | jq -r '.success')

if [ "$success" != "true" ]; then
    echo -e "${RED}❌ Upload was not successful${NC}"
    exit 1
fi

echo -e "${GREEN}✓ PDF uploaded successfully${NC}"
echo "  Record ID: $record_id"
echo "  Bronze table: $table_name"
echo "  Report type: $(echo "$body" | jq -r '.report_type')"
echo "  Extraction method: $(echo "$body" | jq -r '.extraction_method')"

# ============================================================================
# STEP 6: Query Snowflake to Verify Data
# ============================================================================
step 6 "Query Bronze Layer - Verify data was saved"

# URL encode the SQL query
sql_query="SELECT * FROM $table_name WHERE id = '$record_id' LIMIT 1"
encoded_sql=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$sql_query'''))")

query_url="$MCP_API_URL/api/v1/warehouse/query?sql=$encoded_sql"

query_response=$(api_call "$query_url" GET)
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to query Bronze layer${NC}"
    exit 1
fi

record_count=$(echo "$query_response" | jq 'length')

if [ "$record_count" -eq 0 ]; then
    echo -e "${RED}❌ No record found in Bronze layer${NC}"
    exit 1
fi

echo "$query_response" | jq '.[0]' | head -100

echo -e "${GREEN}✓ Record found in Bronze layer${NC}"
echo "  Records returned: $record_count"

# Extract key fields from the Bronze record
practice=$(echo "$query_response" | jq -r '.[0].PRACTICE_LOCATION')
report_date=$(echo "$query_response" | jq -r '.[0].REPORT_DATE // "N/A"')
file_name=$(echo "$query_response" | jq -r '.[0].FILE_NAME')

echo ""
echo "  Practice: $practice"
echo "  Report Date: $report_date"
echo "  File Name: $file_name"

# ============================================================================
# STEP 7: Check Ingestion Statistics
# ============================================================================
step 7 "Ingestion Statistics - Check upload metrics"

stats_url="$MCP_API_URL/api/v1/pdf/stats?practice_location=$PRACTICE_LOCATION&days=1"
stats_response=$(api_call "$stats_url" GET)

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠ Failed to get ingestion stats (non-critical)${NC}"
else
    echo "$stats_response" | jq '{total_records, period_days, tables: .tables | map({table_name, record_count})}'
    total_records=$(echo "$stats_response" | jq -r '.total_records')
    echo -e "${GREEN}✓ Ingestion stats retrieved${NC}"
    echo "  Total records (last 24h): $total_records"
fi

# ============================================================================
# STEP 8: Query Extracted Data Fields
# ============================================================================
step 8 "Extract Specific Fields - Parse VARIANT columns"

# Query with JSON parsing
sql_query2="SELECT
    practice_location,
    report_date,
    extraction_method,
    extracted_data:total_production::DECIMAL(18,2) as total_production,
    extracted_data:net_production::DECIMAL(18,2) as net_production,
    extracted_data:patient_visits::INT as patient_visits,
    file_name,
    uploaded_at
FROM $table_name
WHERE practice_location = '$PRACTICE_LOCATION'
ORDER BY uploaded_at DESC
LIMIT 5"

encoded_sql2=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$sql_query2'''))")
query_url2="$MCP_API_URL/api/v1/warehouse/query?sql=$encoded_sql2"

query_response2=$(api_call "$query_url2" GET)

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠ Failed to query extracted data (non-critical)${NC}"
else
    echo "$query_response2" | jq '.'
    echo -e "${GREEN}✓ Extracted data fields retrieved${NC}"
fi

# ============================================================================
# STEP 9: Test Batch Upload (Optional)
# ============================================================================
if [ "$TEST_BATCH" = "true" ]; then
    step 9 "Batch Upload - Upload multiple PDFs"

    # Find all PDFs in examples/ingestion that match our practice
    pdf_files=$(find examples/ingestion -name "*$PRACTICE_LOCATION*.pdf" -o -name "*Eastlake*.pdf" | head -3)

    if [ -z "$pdf_files" ]; then
        echo -e "${YELLOW}⚠ No additional PDFs found for batch test${NC}"
    else
        echo "Found PDFs for batch upload:"
        echo "$pdf_files"

        # Build curl command with multiple files
        curl_files=""
        for pdf in $pdf_files; do
            curl_files="$curl_files -F files=@$pdf"
        done

        batch_response=$(curl -s -w "\n%{http_code}" -X POST "$MCP_API_URL/api/v1/pdf/upload/batch" \
            -H "Authorization: Bearer $MCP_API_KEY" \
            $curl_files \
            -F "practice_location=$PRACTICE_LOCATION" \
            -F "use_ai=$USE_AI" \
            -F "uploaded_by=e2e_batch_test")

        http_code=$(echo "$batch_response" | tail -n1)
        body=$(echo "$batch_response" | sed '$d')

        if [ "$http_code" -eq 200 ]; then
            echo "$body" | jq '{batch_id, total_files, successful, failed}'
            echo -e "${GREEN}✓ Batch upload successful${NC}"
        else
            echo -e "${YELLOW}⚠ Batch upload failed (HTTP $http_code)${NC}"
        fi
    fi
fi

# ============================================================================
# Test Summary
# ============================================================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                    ✓ All Tests Passed!                        ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo "  ✓ MCP Server is healthy"
echo "  ✓ Snowflake connection verified"
echo "  ✓ PDF extraction working (method: $extraction_method)"
echo "  ✓ Data saved to Bronze layer: $table_name"
echo "  ✓ Record ID: $record_id"
echo "  ✓ Data queryable from API"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. View data in Snowflake Web UI: https://app.snowflake.com/"
echo "     SELECT * FROM $table_name WHERE practice_location = '$PRACTICE_LOCATION';"
echo ""
echo "  2. Create dbt models to transform Bronze → Silver → Gold"
echo ""
echo "  3. Upload more PDFs:"
echo "     curl -X POST $MCP_API_URL/api/v1/pdf/upload \\"
echo "       -H \"Authorization: Bearer \$MCP_API_KEY\" \\"
echo "       -F \"file=@your-file.pdf\" \\"
echo "       -F \"practice_location=YourPractice\" \\"
echo "       -F \"use_ai=true\""
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
