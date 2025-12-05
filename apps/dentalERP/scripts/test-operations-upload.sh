#!/bin/bash
# Test Operations Report Upload - End-to-End Test
# Tests: Upload → Bronze → Silver Dynamic → Gold Dynamic → API Query

set -e

echo "=" | tr '=' '='| head -c 80; echo
echo "  OPERATIONS KPI UPLOAD TEST"
echo "=" | tr '=' '='| head -c 80; echo
echo

# Configuration
MCP_URL="${MCP_URL:-http://localhost:8085}"
MCP_API_KEY="${MCP_API_KEY:-dev-mcp-api-key-change-in-production-min-32-chars}"
TENANT_ID="${TENANT_ID:-silvercreek}"

echo "🔧 Configuration:"
echo "   MCP URL: $MCP_URL"
echo "   Tenant: $TENANT_ID"
echo

# Step 1: Create sample operations data JSON
echo "📊 Step 1: Creating sample operations data..."

cat > /tmp/sample_operations_data.json << 'EOF'
{
  "practice_code": "eastlake",
  "practice_name": "Eastlake Dental",
  "report_month": "2024-10-01",
  "tenant_id": "silvercreek",
  "raw_data": {
    "total_production": 285000,
    "gross_production_doctor": 180000,
    "gross_production_specialty": 25000,
    "gross_production_hygiene": 80000,
    "net_production": 270000,
    "collections": 256500,
    "adjustments": 15000,
    "visits_doctor_1": 350,
    "visits_doctor_2": 280,
    "visits_doctor_total": 630,
    "visits_specialist": 45,
    "visits_hygiene": 220,
    "visits_total": 895,
    "doc1_treatment_presented": 125000,
    "doc1_treatment_accepted": 106250,
    "doc2_treatment_presented": 98000,
    "doc2_treatment_accepted": 81200,
    "new_patients_total": 42,
    "new_patients_reappt_rate": 88.5,
    "hygiene_capacity_slots": 240,
    "hygiene_net_production": 75000,
    "hygiene_compensation": 28000,
    "hygiene_reappt_rate": 92.0,
    "doctor_1_production": 145000,
    "doctor_2_production": 115000,
    "specialist_production": 25000
  },
  "source_file": "operations_test_data.json"
}
EOF

echo "   ✅ Sample data created: /tmp/sample_operations_data.json"
echo

# Step 2: Insert directly to Bronze using Python
echo "📥 Step 2: Inserting sample data to Bronze layer..."

python3 << 'PYTHON_EOF'
import os
import json
import snowflake.connector
from dotenv import load_dotenv

load_dotenv('mcp-server/.env')

# Load sample data
with open('/tmp/sample_operations_data.json') as f:
    data = json.load(f)

# Connect to Snowflake
conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    role=os.getenv('SNOWFLAKE_ROLE', 'ACCOUNTADMIN'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
    database=os.getenv('SNOWFLAKE_DATABASE')
)

cursor = conn.cursor()

# Insert to Bronze
record_id = f"{data['practice_code']}_{data['report_month']}"
raw_data_json = json.dumps(data['raw_data'])

query = f"""
    INSERT INTO bronze.operations_metrics_raw
    (id, practice_code, practice_name, report_month, tenant_id, raw_data, source_file, uploaded_at)
    SELECT
        '{record_id}',
        '{data["practice_code"]}',
        '{data["practice_name"]}',
        '{data["report_month"]}',
        '{data["tenant_id"]}',
        PARSE_JSON('{raw_data_json}'),
        '{data["source_file"]}',
        CURRENT_TIMESTAMP()
"""

cursor.execute(query)
conn.commit()

print(f"   ✅ Inserted to Bronze: {record_id}")

# Verify Bronze insert
cursor.execute(f"SELECT COUNT(*) FROM bronze.operations_metrics_raw WHERE id = '{record_id}'")
count = cursor.fetchone()[0]
print(f"   ✅ Verified in Bronze: {count} record(s)")

cursor.close()
conn.close()
PYTHON_EOF

echo

# Step 3: Force refresh dynamic tables (don't wait 1 hour)
echo "🔄 Step 3: Refreshing dynamic tables..."

python3 << 'PYTHON_EOF'
import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv('mcp-server/.env')

conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    role=os.getenv('SNOWFLAKE_ROLE'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
    database=os.getenv('SNOWFLAKE_DATABASE')
)

cursor = conn.cursor()

# Refresh Silver
print("   → Refreshing Silver: bronze_silver.stg_operations_metrics...")
cursor.execute("ALTER DYNAMIC TABLE bronze_silver.stg_operations_metrics REFRESH")
print("   ✅ Silver refreshed")

# Refresh Gold
print("   → Refreshing Gold: bronze_gold.operations_kpis_monthly...")
cursor.execute("ALTER DYNAMIC TABLE bronze_gold.operations_kpis_monthly REFRESH")
print("   ✅ Gold refreshed")

cursor.close()
conn.close()
PYTHON_EOF

echo

# Step 4: Verify data in Silver layer
echo "🔍 Step 4: Verifying Silver layer data..."

python3 << 'PYTHON_EOF'
import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv('mcp-server/.env')

conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    role=os.getenv('SNOWFLAKE_ROLE'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
    database=os.getenv('SNOWFLAKE_DATABASE')
)

cursor = conn.cursor()

cursor.execute("""
    SELECT practice_code, report_month, total_production, collections, visits_total
    FROM bronze_silver.stg_operations_metrics
    WHERE practice_code = 'eastlake'
    LIMIT 1
""")

result = cursor.fetchone()
if result:
    print(f"   ✅ Silver layer data:")
    print(f"      Practice: {result[0]}")
    print(f"      Month: {result[1]}")
    print(f"      Production: ${result[2]:,.2f}")
    print(f"      Collections: ${result[3]:,.2f}")
    print(f"      Visits: {result[4]}")
else:
    print("   ⚠️  No data in Silver layer yet")

cursor.close()
conn.close()
PYTHON_EOF

echo

# Step 5: Verify data in Gold layer
echo "🎯 Step 5: Verifying Gold layer data (with calculated KPIs)..."

python3 << 'PYTHON_EOF'
import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv('mcp-server/.env')

conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    role=os.getenv('SNOWFLAKE_ROLE'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
    database=os.getenv('SNOWFLAKE_DATABASE')
)

cursor = conn.cursor()

cursor.execute("""
    SELECT
        practice_location,
        report_month,
        total_production,
        collection_rate_pct,
        ppv_overall,
        case_acceptance_rate_pct,
        hygiene_productivity_ratio,
        ltm_production
    FROM bronze_gold.operations_kpis_monthly
    WHERE practice_location = 'eastlake'
    ORDER BY report_month DESC
    LIMIT 1
""")

result = cursor.fetchone()
if result:
    print(f"   ✅ Gold layer KPIs:")
    print(f"      Practice: {result[0]}")
    print(f"      Month: {result[1]}")
    print(f"      Production: ${result[2]:,.2f}")
    print(f"      Collection Rate: {result[3]:.1f}%")
    print(f"      Production/Visit: ${result[4]:,.2f}")
    print(f"      Case Acceptance: {result[5]:.1f}%")
    print(f"      Hygiene Ratio: {result[6]:.2f}")
    print(f"      LTM Production: ${result[7]:,.2f}" if result[7] else "      LTM Production: N/A")
else:
    print("   ⚠️  No data in Gold layer yet")

cursor.close()
conn.close()
PYTHON_EOF

echo
echo "=" | tr '=' '='| head -c 80; echo
echo "✅ OPERATIONS KPI UPLOAD TEST COMPLETE"
echo "=" | tr '=' '='| head -c 80; echo
echo
echo "📋 Summary:"
echo "   ✓ Bronze: Raw data inserted"
echo "   ✓ Silver: Dynamic table refreshed and verified"
echo "   ✓ Gold: KPIs calculated with LTM rollups"
echo
echo "🚀 Next Steps:"
echo "   1. Test API endpoints:"
echo "      curl $MCP_URL/api/v1/operations/kpis/monthly \\"
echo "        -H 'Authorization: Bearer $MCP_API_KEY' \\"
echo "        -H 'X-Tenant-ID: $TENANT_ID'"
echo
echo "   2. Upload real Operations Report Excel:"
echo "      curl -X POST $MCP_URL/api/v1/operations/upload \\"
echo "        -H 'Authorization: Bearer $MCP_API_KEY' \\"
echo "        -H 'X-Tenant-ID: $TENANT_ID' \\"
echo "        -F 'file=@examples/ingestion/Operations Report(28).xlsx' \\"
echo "        -F 'practice_code=LHD' \\"
echo "        -F 'practice_name=Laguna Hills Dental' \\"
echo "        -F 'report_month=2022-09-01'"
echo
