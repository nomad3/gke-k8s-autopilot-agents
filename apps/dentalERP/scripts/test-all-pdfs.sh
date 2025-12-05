#!/bin/bash

# Test script to upload all PDFs and verify data parsing
# Tests the complete pipeline: PDF → Bronze → Silver → Gold

set -e

API_KEY="dev-mcp-api-key-change-in-production-min-32-chars"
BASE_URL="http://localhost:8085"
PDF_DIR="/Users/nomade/Documents/GitHub/dentalERP/examples/ingestion"

echo "=========================================="
echo "PDF Ingestion Pipeline Test"
echo "=========================================="
echo ""

# Function to get practice location from filename
get_practice() {
    case "$1" in
        *Eastlake*) echo "Eastlake" ;;
        *"Torrey Pines"*) echo "Torrey Pines" ;;
        *Aesthetic*|*Aesthatic*) echo "Aesthetic" ;;
        *ADS*) echo "ADS" ;;
        *) echo "Unknown" ;;
    esac
}

# Upload all PDFs
echo "Step 1: Uploading all PDFs..."
echo "------------------------------"

UPLOAD_COUNT=0
FAILED_COUNT=0

for pdf_file in "$PDF_DIR"/*.pdf; do
    filename=$(basename "$pdf_file")
    practice=$(get_practice "$filename")

    if [ "$practice" = "Unknown" ]; then
        echo "⚠️  Skipping $filename (no practice mapping)"
        continue
    fi

    echo "📄 Uploading: $filename → Practice: $practice"

    http_code=$(curl -s -o /tmp/upload_response.json -w "%{http_code}" \
        -X POST "$BASE_URL/api/v1/pdf/upload" \
        -H "Authorization: Bearer $API_KEY" \
        -F "file=@$pdf_file" \
        -F "practice_location=$practice" \
        -F "use_ai=false")

    if [ "$http_code" = "200" ]; then
        echo "   ✅ Uploaded successfully"
        ((UPLOAD_COUNT++))
    else
        echo "   ❌ Upload failed (HTTP $http_code)"
        ((FAILED_COUNT++))
    fi

    sleep 0.5
done

echo ""
echo "Uploaded $UPLOAD_COUNT PDFs successfully, $FAILED_COUNT failed"
echo ""

# Run dbt transformations
echo "Step 2: Running dbt transformations..."
echo "---------------------------------------"

echo "Running dbt pipeline (Bronze → Silver → Gold)..."
http_code=$(curl -s -o /tmp/dbt_response.json -w "%{http_code}" \
    -X POST "$BASE_URL/api/v1/dbt/run/pdf-pipeline" \
    -H "Authorization: Bearer $API_KEY")

if [ "$http_code" = "200" ]; then
    echo "✅ dbt pipeline completed successfully"
else
    echo "❌ dbt pipeline failed (HTTP $http_code)"
    cat /tmp/dbt_response.json | python3 -m json.tool 2>/dev/null || cat /tmp/dbt_response.json
    exit 1
fi

echo ""

# Query Bronze layer
echo "Step 3: Verifying Bronze Layer Data..."
echo "---------------------------------------"

curl -s -X POST "$BASE_URL/api/v1/warehouse/query" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "SELECT practice_location, report_type, extraction_method, file_name, TO_VARCHAR(uploaded_at, '\''YYYY-MM-DD HH24:MI:SS'\'') as uploaded_at FROM bronze.pms_day_sheets ORDER BY uploaded_at DESC LIMIT 20"
    }' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'rows' in data:
        print(f\"Found {len(data['rows'])} records in Bronze layer\")
        print()
        for row in data['rows'][:12]:
            print(f\"  • {row[0]:15} | {row[1]:20} | {row[2]:10} | {row[3][:50]}\")
    else:
        print('Error querying Bronze layer')
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f'Error: {e}')
"

echo ""

# Query Silver layer
echo "Step 4: Verifying Silver Layer Data..."
echo "---------------------------------------"

curl -s -X POST "$BASE_URL/api/v1/warehouse/query" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "SELECT practice_location, report_date, total_production, net_production, patient_visits, extraction_method, data_quality_score FROM bronze_silver.stg_pms_day_sheets ORDER BY report_date DESC, practice_location LIMIT 20"
    }' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'rows' in data:
        print(f\"Found {len(data['rows'])} records in Silver layer\")
        print()
        print(f\"{'Practice':<15} | {'Date':<12} | {'Production':>12} | {'Net Prod':>12} | {'Visits':>7} | {'Method':>10} | {'Quality':>7}\")
        print('-' * 95)
        for row in data['rows']:
            prod = f\"\${float(row[2]):,.2f}\" if row[2] else 'N/A'
            net = f\"\${float(row[3]):,.2f}\" if row[3] else 'N/A'
            visits = str(row[4]) if row[4] else 'N/A'
            method = str(row[5]) if row[5] else 'N/A'
            quality = f\"{float(row[6]):.2f}\" if row[6] else 'N/A'
            print(f\"{row[0]:<15} | {str(row[1]):<12} | {prod:>12} | {net:>12} | {visits:>7} | {method:>10} | {quality:>7}\")
    else:
        print('Error querying Silver layer')
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f'Error: {e}')
"

echo ""

# Query Gold layer
echo "Step 5: Verifying Gold Layer Metrics..."
echo "----------------------------------------"

curl -s -X POST "$BASE_URL/api/v1/warehouse/query" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "SELECT practice_location, report_date, total_production, net_production, patient_visits, production_per_visit, collection_rate_pct, extraction_method FROM bronze_gold.daily_production_metrics ORDER BY report_date DESC, practice_location LIMIT 20"
    }' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'rows' in data:
        print(f\"Found {len(data['rows'])} aggregated metrics in Gold layer\")
        print()
        print(f\"{'Practice':<15} | {'Date':<12} | {'Production':>12} | {'\$/Visit':>10} | {'Visits':>7} | {'Method':>10}\")
        print('-' * 85)
        for row in data['rows']:
            prod = f\"\${float(row[2]):,.2f}\" if row[2] else 'N/A'
            per_visit = f\"\${float(row[5]):,.0f}\" if row[5] else 'N/A'
            visits = str(row[4]) if row[4] else 'N/A'
            method = str(row[7]) if row[7] else 'N/A'
            print(f\"{row[0]:<15} | {str(row[1]):<12} | {prod:>12} | {per_visit:>10} | {visits:>7} | {method:>10}\")

        # Summary statistics
        print()
        print('Summary Statistics:')
        print('-' * 50)
        total_prod = sum(float(row[2]) for row in data['rows'] if row[2])
        total_visits = sum(int(row[4]) for row in data['rows'] if row[4])
        avg_per_visit = total_prod / total_visits if total_visits > 0 else 0

        practices = set(row[0] for row in data['rows'])
        dates = set(str(row[1]) for row in data['rows'])

        print(f\"  Practices: {len(practices)} ({', '.join(sorted(practices))})\")
        print(f\"  Date Range: {len(dates)} unique dates\")
        print(f\"  Total Production: \${total_prod:,.2f}\")
        print(f\"  Total Visits: {total_visits}\")
        print(f\"  Average \$/Visit: \${avg_per_visit:,.2f}\")
    else:
        print('Error querying Gold layer')
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f'Error: {e}')
"

echo ""
echo "=========================================="
echo "Test Complete!"
echo "=========================================="
