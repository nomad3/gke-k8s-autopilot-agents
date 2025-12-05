# Docker End-to-End Testing Guide
## PDF Ingestion with Snowflake Integration

**Purpose:** Test the complete PDF ingestion flow using Docker Compose
**Components:** MCP Server, Snowflake, PostgreSQL, Redis

---

## Quick Start

### 1. Set Up Environment Variables

Copy the example file and fill in your credentials:

```bash
cp .env.docker .env

# Edit .env with your actual credentials
nano .env
```

Required variables:
```bash
# Snowflake (from your setup)
SNOWFLAKE_ACCOUNT=HKTPGHW-ES87244
SNOWFLAKE_USER=NOMADSIMON
SNOWFLAKE_PASSWORD=@SebaSofi.2k25!!
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=DENTAL_ERP_DW
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=ACCOUNTADMIN

# OpenAI (optional - for AI extraction)
OPENAI_API_KEY=sk-proj-your-key-here  # Leave empty to use rules-based extraction
```

### 2. Start Services

```bash
# Start only the MCP server with its dependencies
docker-compose up -d postgres redis mcp-server

# Wait for services to be healthy
docker-compose ps

# Check logs
docker-compose logs -f mcp-server
```

### 3. Run End-to-End Test

```bash
# Run the comprehensive test suite
./test-pdf-ingestion-e2e.sh

# Or with custom PDF
TEST_PDF="examples/ingestion/Torrey Pines - Day Sheet 08 - 2025.pdf" \
PRACTICE_LOCATION="Torrey Pines" \
./test-pdf-ingestion-e2e.sh

# Enable AI extraction (costs ~$0.025 per PDF)
USE_AI=true ./test-pdf-ingestion-e2e.sh
```

---

## What the Test Does

The end-to-end test performs these 9 steps:

### Step 1: Health Check
```bash
GET /health
```
Verifies MCP Server is running and responding

### Step 2: Snowflake Connection
```bash
GET /api/v1/warehouse/status
```
Confirms connection to Snowflake warehouse

### Step 3: Supported Report Types
```bash
GET /api/v1/pdf/supported-types
```
Lists available report types and extraction schemas

### Step 4: Preview Extraction
```bash
POST /api/v1/pdf/extract-preview
```
Tests extraction WITHOUT saving to database (safe for testing)

### Step 5: Upload PDF
```bash
POST /api/v1/pdf/upload
```
Uploads PDF, extracts data, saves to Snowflake Bronze layer

### Step 6: Query Bronze Layer
```bash
GET /api/v1/warehouse/query?sql=SELECT * FROM bronze.pms_day_sheets WHERE id='...'
```
Verifies data was persisted correctly

### Step 7: Ingestion Statistics
```bash
GET /api/v1/pdf/stats?practice_location=Eastlake&days=1
```
Checks upload metrics and success rate

### Step 8: Parse Extracted Fields
```bash
GET /api/v1/warehouse/query?sql=SELECT extracted_data:total_production...
```
Extracts specific fields from VARIANT columns

### Step 9: Batch Upload (Optional)
```bash
POST /api/v1/pdf/upload/batch
```
Tests multiple file upload if `TEST_BATCH=true`

---

## Expected Output

```
═══════════════════════════════════════════════════════════════
     PDF Ingestion End-to-End Test Suite
═══════════════════════════════════════════════════════════════

Configuration:
  MCP API URL: http://localhost:8085
  Test PDF: examples/ingestion/Eastlake Day 07 2025.pdf
  Practice Location: Eastlake
  Use AI Extraction: false

───────────────────────────────────────────────────────────────
STEP 1: Health Check - Verify MCP Server is running
───────────────────────────────────────────────────────────────
{
  "status": "healthy",
  "timestamp": "2025-10-29T20:00:00Z"
}
✓ MCP Server is healthy

───────────────────────────────────────────────────────────────
STEP 2: Snowflake Connection - Verify warehouse is accessible
───────────────────────────────────────────────────────────────
{
  "connected": true,
  "warehouse": {
    "WAREHOUSE": "COMPUTE_WH",
    "DATABASE": "DENTAL_ERP_DW",
    "SCHEMA": "PUBLIC",
    "VERSION": "9.34.0"
  },
  "layers": {
    "bronze": {"table_count": 1},
    "silver": {"table_count": 0},
    "gold": {"table_count": 2}
  }
}
✓ Connected to Snowflake: COMPUTE_WH / DENTAL_ERP_DW

───────────────────────────────────────────────────────────────
STEP 3: Check Supported Report Types
───────────────────────────────────────────────────────────────
[
  "day_sheet",
  "deposit_slip",
  "pay_reconciliation",
  "operations_report"
]
✓ Supported types loaded
  AI extraction available: false

───────────────────────────────────────────────────────────────
STEP 4: Preview Extraction - Test extraction without saving
───────────────────────────────────────────────────────────────
Extracting from: examples/ingestion/Eastlake Day 07 2025.pdf
This will NOT save to database...
{
  "report_type": "day_sheet",
  "extraction_method": "rules",
  "data": {
    "extraction_note": "Rules-based extraction (less accurate than AI)",
    "dates_found": ["07-15-2025"],
    "amounts_found": [15234.50, 1234.00, ...],
    "practice_location": "Eastlake"
  }
}
✓ Preview extraction successful
  Report type detected: day_sheet
  Extraction method: rules

───────────────────────────────────────────────────────────────
STEP 5: Upload PDF - Save extracted data to Snowflake Bronze layer
───────────────────────────────────────────────────────────────
Uploading: examples/ingestion/Eastlake Day 07 2025.pdf
Practice: Eastlake
Use AI: false
{
  "success": true,
  "record_id": "pdf_eastlake_eastlake_day_07_2025_20251029_200001_123456",
  "table_name": "bronze.pms_day_sheets",
  "report_type": "day_sheet",
  "practice_location": "Eastlake",
  "extraction_method": "rules",
  "records_inserted": 1,
  "extracted_fields": ["dates_found", "amounts_found", "practice_location"],
  "message": "Successfully ingested Eastlake Day 07 2025.pdf into bronze.pms_day_sheets"
}
✓ PDF uploaded successfully
  Record ID: pdf_eastlake_eastlake_day_07_2025_20251029_200001_123456
  Bronze table: bronze.pms_day_sheets
  Report type: day_sheet
  Extraction method: rules

───────────────────────────────────────────────────────────────
STEP 6: Query Bronze Layer - Verify data was saved
───────────────────────────────────────────────────────────────
{
  "ID": "pdf_eastlake_eastlake_day_07_2025_20251029_200001_123456",
  "SOURCE_SYSTEM": "manual_pdf",
  "PRACTICE_LOCATION": "Eastlake",
  "REPORT_DATE": "2025-07-15",
  "REPORT_TYPE": "day_sheet",
  "RAW_DATA": {...},
  "EXTRACTED_DATA": {...},
  "EXTRACTION_METHOD": "rules",
  "FILE_NAME": "Eastlake Day 07 2025.pdf",
  "UPLOADED_BY": "e2e_test",
  "UPLOADED_AT": "2025-10-29T20:00:01.123Z"
}
✓ Record found in Bronze layer
  Records returned: 1

  Practice: Eastlake
  Report Date: 2025-07-15
  File Name: Eastlake Day 07 2025.pdf

───────────────────────────────────────────────────────────────
STEP 7: Ingestion Statistics - Check upload metrics
───────────────────────────────────────────────────────────────
{
  "total_records": 1,
  "period_days": 1,
  "tables": [
    {
      "table_name": "bronze.pms_day_sheets",
      "record_count": 1
    }
  ]
}
✓ Ingestion stats retrieved
  Total records (last 24h): 1

───────────────────────────────────────────────────────────────
STEP 8: Extract Specific Fields - Parse VARIANT columns
───────────────────────────────────────────────────────────────
[
  {
    "PRACTICE_LOCATION": "Eastlake",
    "REPORT_DATE": "2025-07-15",
    "EXTRACTION_METHOD": "rules",
    "TOTAL_PRODUCTION": 15234.50,
    "NET_PRODUCTION": 14000.50,
    "PATIENT_VISITS": null,
    "FILE_NAME": "Eastlake Day 07 2025.pdf",
    "UPLOADED_AT": "2025-10-29T20:00:01.123Z"
  }
]
✓ Extracted data fields retrieved

═══════════════════════════════════════════════════════════════
                    ✓ All Tests Passed!
═══════════════════════════════════════════════════════════════

Summary:
  ✓ MCP Server is healthy
  ✓ Snowflake connection verified
  ✓ PDF extraction working (method: rules)
  ✓ Data saved to Bronze layer: bronze.pms_day_sheets
  ✓ Record ID: pdf_eastlake_eastlake_day_07_2025_20251029_200001_123456
  ✓ Data queryable from API

Next Steps:
  1. View data in Snowflake Web UI: https://app.snowflake.com/
     SELECT * FROM bronze.pms_day_sheets WHERE practice_location = 'Eastlake';

  2. Create dbt models to transform Bronze → Silver → Gold

  3. Upload more PDFs:
     curl -X POST http://localhost:8085/api/v1/pdf/upload \
       -H "Authorization: Bearer $MCP_API_KEY" \
       -F "file=@your-file.pdf" \
       -F "practice_location=YourPractice" \
       -F "use_ai=true"

═══════════════════════════════════════════════════════════════
```

---

## Manual Testing Steps

### 1. Upload a PDF via curl

```bash
curl -X POST http://localhost:8085/api/v1/pdf/upload \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  -F "file=@examples/ingestion/Eastlake Day 07 2025.pdf" \
  -F "practice_location=Eastlake" \
  -F "use_ai=false"
```

### 2. Query the Bronze Layer

```bash
curl -X GET "http://localhost:8085/api/v1/warehouse/query?sql=SELECT%20*%20FROM%20bronze.pms_day_sheets%20LIMIT%205" \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" | jq '.'
```

### 3. Check Upload Statistics

```bash
curl -X GET "http://localhost:8085/api/v1/pdf/stats?days=7" \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" | jq '.'
```

### 4. Preview Extraction (No Save)

```bash
curl -X POST http://localhost:8085/api/v1/pdf/extract-preview \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  -F "file=@examples/ingestion/Torrey Pines - Day Sheet 08 - 2025.pdf" \
  -F "use_ai=false" | jq '.extraction_preview'
```

---

## Verify in Snowflake

### 1. Log in to Snowflake Web UI

https://app.snowflake.com/

### 2. Run Queries

```sql
-- Check all uploaded PDFs
SELECT
    practice_location,
    report_type,
    extraction_method,
    file_name,
    uploaded_at,
    uploaded_by
FROM bronze.pms_day_sheets
ORDER BY uploaded_at DESC;

-- Extract specific fields from VARIANT columns
SELECT
    practice_location,
    report_date,
    extraction_method,
    extracted_data:dates_found[0]::VARCHAR as first_date_found,
    extracted_data:amounts_found[0]::DECIMAL(18,2) as first_amount,
    ARRAY_SIZE(extracted_data:amounts_found) as amount_count,
    file_name
FROM bronze.pms_day_sheets
WHERE practice_location = 'Eastlake';

-- Aggregate stats
SELECT
    practice_location,
    report_type,
    extraction_method,
    COUNT(*) as upload_count,
    MIN(uploaded_at) as first_upload,
    MAX(uploaded_at) as last_upload
FROM bronze.pms_day_sheets
GROUP BY practice_location, report_type, extraction_method
ORDER BY upload_count DESC;
```

---

## Troubleshooting

### Issue: "MCP Server health check failed"

**Check logs:**
```bash
docker-compose logs mcp-server
```

**Restart service:**
```bash
docker-compose restart mcp-server
docker-compose logs -f mcp-server
```

### Issue: "Snowflake connection failed"

**Check environment variables:**
```bash
docker-compose exec mcp-server env | grep SNOWFLAKE
```

**Test connection directly:**
```bash
docker-compose exec mcp-server python3 -c "
from src.connectors.snowflake import SnowflakeConnector
from src.core.config import get_settings
settings = get_settings()
connector = SnowflakeConnector(settings)
import asyncio
result = asyncio.run(connector.test_connection())
print('Connected!' if result else 'Failed')
"
```

### Issue: "PDF extraction returns empty data"

**Check PDF file:**
- Is it a valid PDF?
- Is it text-based or scanned image?
- Can you read text from it manually?

**Try with AI extraction:**
```bash
USE_AI=true ./test-pdf-ingestion-e2e.sh
```

**Check extraction logs:**
```bash
docker-compose logs mcp-server | grep -A 10 "Extracting data from PDF"
```

### Issue: "OpenAI API error"

**Verify API key:**
```bash
docker-compose exec mcp-server env | grep OPENAI
```

**Use rules-based extraction instead:**
```bash
USE_AI=false ./test-pdf-ingestion-e2e.sh
```

---

## Docker Compose Commands

### Start Services
```bash
# Start only MCP server stack
docker-compose up -d postgres redis mcp-server

# Start entire stack (including backend/frontend)
docker-compose up -d

# Start with logs
docker-compose up mcp-server
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean start)
docker-compose down -v
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f mcp-server

# Last 100 lines
docker-compose logs --tail=100 mcp-server
```

### Rebuild After Code Changes
```bash
# Rebuild MCP server image
docker-compose build mcp-server

# Rebuild and restart
docker-compose up -d --build mcp-server
```

### Execute Commands in Container
```bash
# Open shell
docker-compose exec mcp-server sh

# Run Python script
docker-compose exec mcp-server python3 test-snowflake.py

# Install dependencies
docker-compose exec mcp-server pip install -r requirements.txt
```

---

## Performance Metrics

### Expected Timings (with rules-based extraction)

| Step | Time | Notes |
|------|------|-------|
| Health check | <1s | |
| Snowflake connection | 1-2s | First connection ~10s (warm-up) |
| Preview extraction | 2-3s | PDF text extraction |
| Upload & save to Bronze | 3-5s | Extraction + Snowflake insert |
| Query Bronze layer | <1s | Simple SELECT |
| **Total test runtime** | **10-15s** | Full end-to-end |

### With AI Extraction

| Step | Time | Cost |
|------|------|------|
| AI extraction | 5-10s | $0.025 per PDF |
| Upload & save | 6-12s | + Snowflake insert |
| **Total** | **15-20s** | ~$0.025 per PDF |

---

## Next Steps After Successful Test

### 1. Upload Real PDFs

```bash
# Single upload
curl -X POST http://localhost:8085/api/v1/pdf/upload \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  -F "file=@/path/to/real-day-sheet.pdf" \
  -F "practice_location=YourPractice" \
  -F "use_ai=true"

# Batch upload
curl -X POST http://localhost:8085/api/v1/pdf/upload/batch \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  -F "files=@file1.pdf" \
  -F "files=@file2.pdf" \
  -F "files=@file3.pdf" \
  -F "practice_location=YourPractice" \
  -F "use_ai=true"
```

### 2. Create dbt Models

See Week 4 deliverables in `SILVERCREEK_MVP_ROADMAP.md`

### 3. Automate Daily Uploads

Create a cron job or workflow to upload PDFs automatically:

```bash
#!/bin/bash
# upload-daily-reports.sh
for pdf in /path/to/daily/reports/*.pdf; do
    curl -X POST http://localhost:8085/api/v1/pdf/upload \
      -H "Authorization: Bearer $MCP_API_KEY" \
      -F "file=@$pdf" \
      -F "practice_location=AutoDetect" \
      -F "use_ai=true"
done
```

### 4. Monitor Ingestion Health

```bash
# Check daily stats
curl -X GET "http://localhost:8085/api/v1/pdf/stats?days=1" \
  -H "Authorization: Bearer $MCP_API_KEY" | jq '.total_records'

# Alert if no uploads in 24h
if [ $(curl -s ... | jq '.total_records') -eq 0 ]; then
    echo "WARNING: No PDF uploads in 24h!"
fi
```

---

## Success Criteria

Your end-to-end test is successful when:

- ✅ All 8 steps complete without errors
- ✅ Record is created in Snowflake Bronze layer
- ✅ Data is queryable via API
- ✅ Extracted fields are accessible in VARIANT columns
- ✅ Test completes in <20 seconds

---

## Resources

- **Test Script:** `./test-pdf-ingestion-e2e.sh`
- **Docker Compose:** `docker-compose.yml`
- **Environment:** `.env` (copy from `.env.docker`)
- **API Docs:** http://localhost:8085/docs
- **Snowflake UI:** https://app.snowflake.com/

---

✅ **Ready to Test!**

Run: `./test-pdf-ingestion-e2e.sh`
