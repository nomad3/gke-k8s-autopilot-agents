#!/bin/bash

# Test AI-based PDF extraction with OpenAI
# Compares rules-based vs AI extraction results

API_KEY="dev-mcp-api-key-change-in-production-min-32-chars"
BASE_URL="http://localhost:8085"
PDF_DIR="/Users/nomade/Documents/GitHub/dentalERP/examples/ingestion"

echo "=========================================="
echo "AI-Based PDF Extraction Test"
echo "=========================================="
echo ""

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY not set in environment"
    echo "   AI extraction will fall back to rules-based"
    echo ""
fi

# Test with 3 sample PDFs
test_pdfs=(
    "Eastlake Day 07 2025.pdf:Eastlake"
    "Torrey Pines - Day Sheet 08 - 2025.pdf:Torrey Pines"
    "ADS Day Sheet June 2025.pdf:ADS"
)

echo "Testing AI extraction on 3 sample PDFs..."
echo "==========================================

"

for pdf_info in "${test_pdfs[@]}"; do
    IFS=':' read -r filename practice <<< "$pdf_info"
    pdf_file="$PDF_DIR/$filename"

    echo "📄 Testing: $filename (Practice: $practice)"
    echo "   Location: $pdf_file"

    if [ ! -f "$pdf_file" ]; then
        echo "   ❌ File not found"
        continue
    fi

    # Upload with AI enabled
    echo "   🤖 Uploading with AI extraction (use_ai=true)..."

    response=$(curl -s -X POST "$BASE_URL/api/v1/pdf/upload" \
        -H "Authorization: Bearer $API_KEY" \
        -F "file=@$pdf_file" \
        -F "practice_location=$practice" \
        -F "use_ai=true")

    # Check if upload was successful
    if echo "$response" | grep -q '"status":"success"'; then
        echo "   ✅ Upload successful"

        # Extract key metrics from response
        echo "   📊 Extracted Data:"
        echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    extracted = data.get('extracted_data', {})

    print(f\"      Method: {extracted.get('extraction_method', 'N/A')}\")
    print(f\"      Date: {extracted.get('report_date', 'N/A')}\")
    print(f\"      Production: \${extracted.get('total_production', 'N/A')}\")
    print(f\"      Net Production: \${extracted.get('net_production', 'N/A')}\")
    print(f\"      Patient Visits: {extracted.get('patient_visits', 'N/A')}\")
    print(f\"      Adjustments: \${extracted.get('total_adjustments', 'N/A')}\")
except Exception as e:
    print(f'      Error parsing response: {e}')
" 2>/dev/null || echo "      Could not parse extraction results"
    else
        echo "   ❌ Upload failed"
        echo "$response" | python3 -m json.tool 2>/dev/null | head -10
    fi

    echo ""
    sleep 2
done

echo "=========================================="
echo "Running dbt transformations..."
echo "=========================================="
echo ""

# Run dbt pipeline
http_code=$(curl -s -o /tmp/dbt_ai_response.json -w "%{http_code}" \
    -X POST "$BASE_URL/api/v1/dbt/run/pdf-pipeline" \
    -H "Authorization: Bearer $API_KEY")

if [ "$http_code" = "200" ]; then
    echo "✅ dbt pipeline completed successfully"
else
    echo "❌ dbt pipeline failed (HTTP $http_code)"
fi

echo ""
echo "=========================================="
echo "Verifying AI-extracted data in Silver..."
echo "=========================================="
echo ""

# Query Silver layer to see AI extraction results
echo "SELECT * FROM bronze_silver.stg_pms_day_sheets WHERE extraction_method = 'ai' ORDER BY uploaded_at DESC LIMIT 5;" | python3 << 'EOF'
import os
import snowflake.connector
from dotenv import load_dotenv
from pathlib import Path

# Load environment
env_path = Path("/Users/nomade/Documents/GitHub/dentalERP/mcp-server/.env")
load_dotenv(env_path)

try:
    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database='DENTAL_ERP_DW',
        schema='bronze_silver'
    )

    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            practice_location,
            report_date,
            total_production,
            net_production,
            patient_visits,
            adjustments,
            extraction_method,
            data_quality_score
        FROM stg_pms_day_sheets
        WHERE extraction_method = 'ai'
        ORDER BY uploaded_at DESC
        LIMIT 5
    """)

    rows = cursor.fetchall()

    if rows:
        print(f"Found {len(rows)} AI-extracted records:\n")
        print(f"{'Practice':<15} | {'Date':<12} | {'Production':>12} | {'Net Prod':>12} | {'Visits':>7} | {'Quality':>7}")
        print("-" * 90)

        for row in rows:
            prod = f"${float(row[2]):,.2f}" if row[2] else "N/A"
            net = f"${float(row[3]):,.2f}" if row[3] else "N/A"
            visits = str(row[4]) if row[4] else "N/A"
            quality = f"{float(row[7]):.2f}" if row[7] else "N/A"

            print(f"{row[0]:<15} | {str(row[1]):<12} | {prod:>12} | {net:>12} | {visits:>7} | {quality:>7}")
    else:
        print("No AI-extracted records found. AI extraction may not be working.")
        print("\nPossible reasons:")
        print("  • OPENAI_API_KEY not set in mcp-server/.env")
        print("  • pdf2image or openai packages not installed")
        print("  • API key invalid or quota exceeded")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error querying database: {e}")
EOF

echo ""
echo "=========================================="
echo "Test Complete!"
echo "=========================================="
