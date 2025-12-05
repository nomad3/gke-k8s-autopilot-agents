# MCP Server API Reference

Complete API documentation for the DentalERP MCP Server.

## Base URL

```
Development: http://localhost:8085
Production:  https://mcp.agentprovision.com
```

## Authentication

All endpoints (except `/health`) require Bearer token authentication:

```http
Authorization: Bearer <MCP_API_KEY>
```

**Example:**
```bash
curl -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  http://localhost:8085/api/v1/warehouse/status
```

---

## Health & Monitoring

### GET /health

Basic health check endpoint (no authentication required).

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-10-30T12:56:38.909038",
  "service": "mcp-server"
}
```

### GET /health/detailed

Detailed health check including database and cache status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-30T12:56:38.909038",
  "services": {
    "database": "connected",
    "redis": "connected",
    "snowflake": "connected"
  }
}
```

---

## PDF Ingestion API

### POST /api/v1/pdf/upload

Upload a single PDF for data extraction.

**Request:**
- **Content-Type:** `multipart/form-data`
- **Authorization:** Required

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | PDF file to upload |
| `practice_location` | string | Yes | Practice name/location |
| `use_ai` | boolean | No | Use AI extraction (default: false) |
| `report_type` | string | No | Override auto-detection |

**Example:**
```bash
curl -X POST "http://localhost:8085/api/v1/pdf/upload" \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  -F "file=@Eastlake_Day_Sheet.pdf" \
  -F "practice_location=Eastlake" \
  -F "use_ai=false"
```

**Response (Success):**
```json
{
  "status": "success",
  "success": true,
  "record_id": "pdf_eastlake_20251030_122024_765153",
  "table_name": "bronze.pms_day_sheets",
  "report_type": "day_sheet",
  "practice_location": "Eastlake",
  "extraction_method": "rules",
  "records_inserted": 1,
  "extracted_fields": [
    "extraction_note",
    "raw_text_length",
    "dates_found",
    "amounts_found",
    "total_amount_sum",
    "practice_location"
  ],
  "message": "Successfully ingested PDF into bronze.pms_day_sheets"
}
```

**Response (Error):**
```json
{
  "status": "error",
  "error": "Failed to extract data from PDF",
  "details": "No recognizable text found"
}
```

### POST /api/v1/pdf/upload/batch

Upload multiple PDFs in a single request.

**Request:**
- **Content-Type:** `multipart/form-data`
- **Authorization:** Required

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `files` | file[] | Yes | Array of PDF files |
| `practice_location` | string | Yes | Practice name/location |
| `use_ai` | boolean | No | Use AI extraction for all files |

**Example:**
```bash
curl -X POST "http://localhost:8085/api/v1/pdf/upload/batch" \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  -F "files=@file1.pdf" \
  -F "files=@file2.pdf" \
  -F "files=@file3.pdf" \
  -F "practice_location=Eastlake" \
  -F "use_ai=false"
```

**Response:**
```json
{
  "status": "success",
  "total_files": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "filename": "file1.pdf",
      "status": "success",
      "record_id": "pdf_eastlake_..."
    },
    {
      "filename": "file2.pdf",
      "status": "success",
      "record_id": "pdf_eastlake_..."
    },
    {
      "filename": "file3.pdf",
      "status": "success",
      "record_id": "pdf_eastlake_..."
    }
  ]
}
```

### GET /api/v1/pdf/stats

Get PDF ingestion statistics.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `practice_location` | string | No | Filter by practice |
| `start_date` | string | No | Start date (YYYY-MM-DD) |
| `end_date` | string | No | End date (YYYY-MM-DD) |

**Example:**
```bash
curl -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  "http://localhost:8085/api/v1/pdf/stats?practice_location=Eastlake"
```

**Response:**
```json
{
  "total_uploads": 150,
  "successful": 145,
  "failed": 5,
  "by_practice": {
    "Eastlake": 75,
    "Torrey Pines": 50,
    "ADS": 25
  },
  "by_method": {
    "rules": 100,
    "ai": 50
  },
  "avg_processing_time": 3.2
}
```

### GET /api/v1/pdf/supported-types

Get list of supported PDF report types.

**Response:**
```json
{
  "supported_types": [
    {
      "type": "day_sheet",
      "description": "Daily production report",
      "systems": ["Dentrix", "Eaglesoft", "Open Dental"]
    },
    {
      "type": "deposit_slip",
      "description": "Daily deposit report",
      "systems": ["Dentrix", "Eaglesoft"]
    },
    {
      "type": "production_report",
      "description": "Monthly production summary",
      "systems": ["Dentrix"]
    }
  ]
}
```

### POST /api/v1/pdf/extract-preview

Preview PDF extraction without saving to database.

**Request:**
```bash
curl -X POST "http://localhost:8085/api/v1/pdf/extract-preview" \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  -F "file=@test.pdf" \
  -F "use_ai=true"
```

**Response:**
```json
{
  "report_type": "day_sheet",
  "extraction_method": "ai",
  "extracted_data": {
    "date": "2025-08-04",
    "practice": "Eastlake",
    "production": 115128.72,
    "adjustments": 0.00,
    "visits": 464
  },
  "confidence_score": 0.95,
  "preview_only": true
}
```

---

## Production Analytics API

### GET /api/v1/analytics/production/summary

Get overall production metrics summary.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `practice_location` | string | No | Filter by practice |
| `start_date` | string | No | Start date (YYYY-MM-DD) |
| `end_date` | string | No | End date (YYYY-MM-DD) |

**Example:**
```bash
curl -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  "http://localhost:8085/api/v1/analytics/production/summary"
```

**Response:**
```json
{
  "PRACTICE_COUNT": 1,
  "DATE_COUNT": 4,
  "TOTAL_PRODUCTION": "847822.48",
  "TOTAL_NET_PRODUCTION": "842021.03",
  "TOTAL_VISITS": 464,
  "AVG_PRODUCTION_PER_VISIT": "62.03",
  "AVG_COLLECTION_RATE": "0.00",
  "EARLIEST_DATE": "2025-06-02",
  "LATEST_DATE": "2025-08-04"
}
```

### GET /api/v1/analytics/production/daily

Get daily production metrics.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `practice_location` | string | No | Filter by practice |
| `start_date` | string | No | Start date (YYYY-MM-DD) |
| `end_date` | string | No | End date (YYYY-MM-DD) |
| `limit` | integer | No | Max records to return (default: 100) |

**Example:**
```bash
curl -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  "http://localhost:8085/api/v1/analytics/production/daily?limit=5"
```

**Response:**
```json
[
  {
    "PRACTICE_LOCATION": "Eastlake",
    "REPORT_DATE": "2025-08-04",
    "DAY_NAME": "Mon",
    "TOTAL_PRODUCTION": "115128.72",
    "NET_PRODUCTION": "109327.27",
    "ADJUSTMENTS": "0.00",
    "COLLECTIONS": "0.00",
    "PATIENT_VISITS": 464,
    "PRODUCTION_PER_VISIT": "248.12",
    "COLLECTION_RATE_PCT": "0.00",
    "EXTRACTION_METHOD": "ai",
    "DATA_QUALITY_SCORE": "0.95",
    "UPLOADED_AT": "2025-10-30T00:59:00.003114-07:00"
  }
]
```

### GET /api/v1/analytics/production/by-practice

Get production metrics grouped by practice.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | No | Start date (YYYY-MM-DD) |
| `end_date` | string | No | End date (YYYY-MM-DD) |

**Example:**
```bash
curl -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  "http://localhost:8085/api/v1/analytics/production/by-practice"
```

**Response:**
```json
[
  {
    "PRACTICE_LOCATION": "Eastlake",
    "DAYS_REPORTED": 4,
    "TOTAL_PRODUCTION": "847822.48",
    "TOTAL_NET_PRODUCTION": "842021.03",
    "TOTAL_VISITS": 464,
    "AVG_PRODUCTION_PER_VISIT": "62.03",
    "AVG_COLLECTION_RATE": "0.00",
    "EARLIEST_DATE": "2025-06-02",
    "LATEST_DATE": "2025-08-04"
  },
  {
    "PRACTICE_LOCATION": "Torrey Pines",
    "DAYS_REPORTED": 3,
    "TOTAL_PRODUCTION": "650000.00",
    "TOTAL_NET_PRODUCTION": "645000.00",
    "TOTAL_VISITS": 320,
    "AVG_PRODUCTION_PER_VISIT": "75.50",
    "AVG_COLLECTION_RATE": "0.95",
    "EARLIEST_DATE": "2025-06-01",
    "LATEST_DATE": "2025-08-01"
  }
]
```

---

## Snowflake Data Warehouse API

### GET /api/v1/warehouse/status

Get Snowflake connection and layer status.

**Example:**
```bash
curl -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  "http://localhost:8085/api/v1/warehouse/status"
```

**Response:**
```json
{
  "connected": true,
  "warehouse": {
    "WAREHOUSE": "COMPUTE_WH",
    "DATABASE": "DENTAL_ERP_DW",
    "SCHEMA": "PUBLIC",
    "VERSION": "9.34.0"
  },
  "layers": {
    "bronze": {
      "table_count": 3,
      "tables": ["pms_day_sheets", "pms_deposits", "pms_procedures"]
    },
    "silver": {
      "table_count": 2,
      "tables": ["stg_pms_day_sheets", "stg_procedures"]
    },
    "gold": {
      "table_count": 2,
      "tables": ["daily_production_metrics", "practice_performance"]
    }
  },
  "timestamp": "2025-10-30T12:56:38.909038"
}
```

### GET /api/v1/warehouse/freshness

Get data freshness for each table.

**Response:**
```json
{
  "bronze.pms_day_sheets": {
    "last_updated": "2025-10-30T05:15:00Z",
    "row_count": 1250,
    "freshness_hours": 2.5
  },
  "bronze_gold.daily_production_metrics": {
    "last_updated": "2025-10-30T06:00:00Z",
    "row_count": 450,
    "freshness_hours": 1.75
  }
}
```

### POST /api/v1/warehouse/query

Execute a custom SQL query (admin only).

**Request:**
```json
{
  "query": "SELECT * FROM bronze_gold.daily_production_metrics WHERE practice_location = 'Eastlake' LIMIT 10",
  "parameters": {}
}
```

**Response:**
```json
{
  "status": "success",
  "rows": [...],
  "row_count": 10,
  "execution_time_ms": 245
}
```

### GET /api/v1/warehouse/bronze/status

Get Bronze layer specific status.

**Response:**
```json
{
  "layer": "bronze",
  "tables": [
    {
      "name": "pms_day_sheets",
      "row_count": 1250,
      "last_updated": "2025-10-30T05:15:00Z",
      "size_mb": 45.2
    }
  ]
}
```

---

## dbt Transformation API

### POST /api/v1/dbt/run

Trigger dbt model execution.

**Request:**
```json
{
  "models": ["all"],
  "full_refresh": false
}
```

**Response:**
```json
{
  "status": "started",
  "run_id": "dbt_run_20251030_123456",
  "models_to_run": 15,
  "estimated_duration_minutes": 5
}
```

### POST /api/v1/dbt/run/pdf-pipeline

Run PDF-specific dbt models only.

**Response:**
```json
{
  "status": "started",
  "run_id": "dbt_run_pdf_20251030_123456",
  "models_to_run": 3,
  "models": [
    "stg_pms_day_sheets",
    "daily_production_metrics",
    "practice_performance"
  ]
}
```

### GET /api/v1/dbt/status

Check dbt run status.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `run_id` | string | No | Specific run ID to check |

**Response:**
```json
{
  "run_id": "dbt_run_20251030_123456",
  "status": "completed",
  "started_at": "2025-10-30T12:30:00Z",
  "completed_at": "2025-10-30T12:35:00Z",
  "duration_seconds": 300,
  "models_run": 15,
  "models_succeeded": 15,
  "models_failed": 0,
  "models_skipped": 0
}
```

---

## Integration Sync API

### POST /api/v1/sync/run

Trigger external integration synchronization.

**Request:**
```json
{
  "integration_type": "netsuite",
  "entity_types": ["journal_entries", "invoices"],
  "location_ids": ["eastlake_001"],
  "sync_mode": "incremental"
}
```

**Response:**
```json
{
  "status": "started",
  "sync_id": "sync_netsuite_20251030_123456",
  "integration_type": "netsuite",
  "estimated_duration_minutes": 10
}
```

### GET /api/v1/sync/{sync_id}

Get synchronization status.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sync_id` | string | Yes | Sync job ID |

**Example:**
```bash
curl -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  "http://localhost:8085/api/v1/sync/sync_netsuite_20251030_123456"
```

**Response:**
```json
{
  "sync_id": "sync_netsuite_20251030_123456",
  "integration_type": "netsuite",
  "status": "running",
  "progress": {
    "total_records": 1000,
    "processed": 650,
    "percent_complete": 65
  },
  "started_at": "2025-10-30T12:30:00Z",
  "errors": []
}
```

### GET /api/v1/integrations/status

Get health status of all integrations.

**Response:**
```json
{
  "integrations": [
    {
      "type": "netsuite",
      "status": "healthy",
      "last_sync": "2025-10-30T10:00:00Z",
      "last_successful_sync": "2025-10-30T10:00:00Z",
      "error_rate": 0.02
    },
    {
      "type": "adp",
      "status": "healthy",
      "last_sync": "2025-10-30T09:00:00Z",
      "last_successful_sync": "2025-10-30T09:00:00Z",
      "error_rate": 0.00
    }
  ]
}
```

---

## Error Responses

All endpoints return consistent error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters",
  "error_code": "INVALID_REQUEST",
  "fields": {
    "practice_location": "Required field missing"
  }
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Invalid or expired API key"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found",
  "resource_type": "sync_job",
  "resource_id": "sync_123"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error",
  "error_code": "INTERNAL_ERROR",
  "timestamp": "2025-10-30T12:56:38.909038"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Snowflake is not configured. Set SNOWFLAKE_* environment variables."
}
```

---

## Rate Limiting

- **Development**: No rate limits
- **Production**: 1000 requests per minute per API key
- **Batch Upload**: 50 files per request

**Rate Limit Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1698675600
```

---

## Webhooks (Future)

Coming soon: Webhook support for event notifications.

**Planned Events:**
- `pdf.uploaded`
- `pdf.processed`
- `dbt.run.completed`
- `sync.completed`
- `analytics.updated`

---

## OpenAPI Documentation

Interactive API documentation available at:

- **Swagger UI**: http://localhost:8085/docs
- **ReDoc**: http://localhost:8085/redoc
- **OpenAPI JSON**: http://localhost:8085/openapi.json

---

## SDKs & Client Libraries

### cURL Examples

See examples throughout this document.

### Python Client (Coming Soon)

```python
from dental_erp_mcp import MCPClient

client = MCPClient(api_key="your-api-key")

# Upload PDF
result = client.pdf.upload(
    file_path="daysheet.pdf",
    practice_location="Eastlake",
    use_ai=False
)

# Get analytics
metrics = client.analytics.production_summary()
print(metrics.total_production)
```

### JavaScript Client (Coming Soon)

```javascript
import { MCPClient } from '@dental-erp/mcp-client';

const client = new MCPClient({ apiKey: 'your-api-key' });

// Upload PDF
const result = await client.pdf.upload({
  file: file,
  practiceLocation: 'Eastlake',
  useAi: false
});

// Get analytics
const metrics = await client.analytics.productionSummary();
console.log(metrics.totalProduction);
```

---

## Support

- **API Issues**: https://github.com/your-org/dentalERP/issues
- **Email**: api-support@dentalerp.com
- **Documentation**: https://docs.dentalerp.com/mcp-api

---

**Last Updated**: October 30, 2025
**API Version**: 1.0.0
