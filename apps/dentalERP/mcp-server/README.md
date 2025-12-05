# MCP Server - DentalERP Integration Hub

The **Mapping & Control Plane (MCP) Server** is the central integration hub for the DentalERP system. It orchestrates data ingestion, transformation, and analytics across multiple dental practices.

## 🎯 Overview

The MCP Server provides:

- **PDF Ingestion**: Extract data from PMS day sheets using AI (GPT-4 Vision) or rules-based parsing
- **Snowflake Integration**: Direct access to Bronze/Silver/Gold data layers
- **Production Analytics**: Real-time metrics and KPIs from Snowflake Gold layer
- **dbt Orchestration**: Trigger data transformations on-demand
- **External Integrations**: Sync with NetSuite, ADP, Dentrix, and other systems
- **RESTful API**: FastAPI-powered endpoints with OpenAPI documentation

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Snowflake account (for analytics)
- OpenAI API key (optional, for AI extraction)

### 1. Configure Environment

Create `.env` file in the mcp-server directory:

```bash
# Snowflake Connection
SNOWFLAKE_ACCOUNT=your-account-locator
SNOWFLAKE_USER=your-username
SNOWFLAKE_PASSWORD=your-password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=DENTAL_ERP_DW
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=ACCOUNTADMIN

# OpenAI for AI Extraction (optional)
OPENAI_API_KEY=sk-proj-...

# MCP Server
MCP_API_KEY=dev-mcp-api-key-change-in-production-min-32-chars
SECRET_KEY=your-secret-key-for-jwt-min-32-chars-abc123

# Database
POSTGRES_HOST=postgres
POSTGRES_DB=mcp
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
```

### 2. Start Services

```bash
# From project root
docker-compose up -d

# Or from mcp-server directory (local development)
cd mcp-server
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8085
```

### 3. Verify Connection

```bash
# Health check
curl http://localhost:8085/health

# Snowflake status
curl -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  http://localhost:8085/api/v1/warehouse/status
```

### 4. Access API Documentation

- **Swagger UI**: http://localhost:8085/docs
- **ReDoc**: http://localhost:8085/redoc

## 📡 API Endpoints

### Health & Monitoring

```bash
GET  /health                # Basic health check
GET  /health/detailed       # Detailed system status
```

### PDF Ingestion

```bash
POST /api/v1/pdf/upload           # Upload single PDF
POST /api/v1/pdf/upload/batch     # Batch upload PDFs
GET  /api/v1/pdf/stats            # Ingestion statistics
GET  /api/v1/pdf/supported-types  # Supported PDF types
POST /api/v1/pdf/extract-preview  # Preview extraction
```

**Example: Upload Day Sheet**

```bash
curl -X POST "http://localhost:8085/api/v1/pdf/upload" \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  -F "file=@Eastlake_Day_Sheet.pdf" \
  -F "practice_location=Eastlake" \
  -F "use_ai=false"
```

**Response:**
```json
{
  "status": "success",
  "record_id": "pdf_eastlake_...",
  "table_name": "bronze.pms_day_sheets",
  "report_type": "day_sheet",
  "practice_location": "Eastlake",
  "extraction_method": "rules",
  "records_inserted": 1,
  "message": "Successfully ingested PDF"
}
```

### Production Analytics

```bash
GET  /api/v1/analytics/production/summary      # Overall production summary
GET  /api/v1/analytics/production/daily        # Daily production metrics
GET  /api/v1/analytics/production/by-practice  # Metrics grouped by practice
```

**Example: Get Production Summary**

```bash
curl -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  http://localhost:8085/api/v1/analytics/production/summary
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
  "EARLIEST_DATE": "2025-06-02",
  "LATEST_DATE": "2025-08-04"
}
```

### Snowflake Data Warehouse

```bash
GET  /api/v1/warehouse/status         # Connection & layer status
GET  /api/v1/warehouse/freshness      # Data freshness by table
POST /api/v1/warehouse/query          # Execute custom SQL query
GET  /api/v1/warehouse/bronze/status  # Bronze layer status
```

### dbt Transformations

```bash
POST /api/v1/dbt/run                 # Run all dbt models
POST /api/v1/dbt/run/pdf-pipeline    # Run PDF-specific models
GET  /api/v1/dbt/status              # Check dbt run status
```

### Data Integration

```bash
POST /api/v1/sync/run           # Trigger integration sync
GET  /api/v1/sync/{sync_id}     # Get sync status
GET  /api/v1/integrations/status # Integration health
```

## 🏗️ Architecture

### Multi-Tenant Data Flow

```
┌─────────────────┐
│  Dental PMS     │
│  (Day Sheets)   │
└────────┬────────┘
         │
         ├─ PDF Upload (with tenant context)
         ↓
┌─────────────────────────────────────────────┐
│           MCP Server (FastAPI)              │
│  ┌────────────────────────────────────┐    │
│  │  Tenant Identifier Middleware       │    │
│  │  - Subdomain / Header / API Key     │    │
│  └──────────────┬──────────────────────┘    │
│                 │                            │
│  ┌──────────────▼──────────────┐            │
│  │  Tenant Context (contextvars)│           │
│  └──────────────┬──────────────┘            │
│                 │                            │
│      ┌──────────┴──────────┐                │
│      │                     │                │
│  ┌───▼──────┐      ┌──────▼─────┐          │
│  │Warehouse │      │Integration │          │
│  │ Router   │      │  Router    │          │
│  │(Snowflake│      │ (NetSuite, │          │
│  │Databricks)      │  ADP, etc.)│          │
│  └───┬──────┘      └──────┬─────┘          │
└──────┼─────────────────────┼────────────────┘
       │                     │
       │ Tenant-specific     │ Tenant-specific
       │ warehouse config    │ credentials
       │                     │
┌──────▼─────────────────────▼──────────────┐
│    Tenant's External Systems               │
│  ┌──────────────┐  ┌──────────────┐      │
│  │  Snowflake   │  │   NetSuite   │      │
│  │  Bronze      │  │     ERP      │      │
│  └──────┬───────┘  └──────────────┘      │
│         │                                  │
│         ├─ dbt transform                   │
│         ↓                                  │
│  ┌──────────────┐  ┌──────────────┐      │
│  │  Snowflake   │  │     ADP      │      │
│  │  Silver      │  │   Payroll    │      │
│  └──────┬───────┘  └──────────────┘      │
│         │                                  │
│         ├─ dbt aggregate                   │
│         ↓                                  │
│  ┌──────────────┐  ┌──────────────┐      │
│  │  Snowflake   │  │   Dentrix    │      │
│  │  Gold        │  │     PMS      │      │
│  │ (Analytics)  │  └──────────────┘      │
│  └──────┬───────┘                         │
└─────────┼─────────────────────────────────┘
          │
          ├─ API queries
          ↓
┌──────────────────┐
│  Frontend        │
│  (React)         │
└──────────────────┘
```

### Multi-Tenant Architecture Overview

The MCP Server implements **complete multi-tenancy** to support:
- **AgentProvision.com** (SaaS platform)
- **Individual Dental Practices** (each with their own credentials)

Every external system integration (warehouses, NetSuite, ADP, Dentrix, etc.) is tenant-aware, ensuring complete data isolation and security.

### Key Components

1. **PDF Ingestion Service** (`src/services/pdf_ingestion.py`)
   - AI extraction using GPT-4 Vision
   - Rules-based fallback parsing
   - Direct Bronze layer insertion

2. **Snowflake Connector** (`src/connectors/snowflake.py`)
   - Connection pooling
   - Query execution
   - Layer management (Bronze/Silver/Gold)

3. **Analytics API** (`src/api/analytics.py`)
   - Production metrics aggregation
   - Practice-level KPIs
   - Time-series analysis

4. **dbt Runner** (`src/services/dbt_runner.py`)
   - Model execution
   - Dependency resolution
   - Run status tracking

## 🏢 Multi-Tenant Architecture

### Overview

The MCP Server supports **complete multi-tenancy** to enable:
- **SaaS Deployment**: AgentProvision.com serving multiple dental practices
- **Data Isolation**: Each tenant has isolated warehouses and integrations
- **Flexible Deployment**: Single-tenant or multi-tenant configurations

### Tenant Identification

Three methods for identifying tenants in requests:

#### 1. Subdomain Extraction
```bash
# Request to acme.dentalerp.com extracts tenant code "acme"
curl https://acme.dentalerp.com/api/v1/analytics/production/summary \
  -H "Authorization: Bearer dev-mcp-api-key-..."
```

#### 2. X-Tenant-ID Header
```bash
# Explicit tenant header (recommended for API clients)
curl http://localhost:8085/api/v1/analytics/production/summary \
  -H "X-Tenant-ID: acme" \
  -H "Authorization: Bearer dev-mcp-api-key-..."
```

#### 3. API Key Prefix
```bash
# Tenant extracted from API key prefix "acme_sk_..."
curl http://localhost:8085/api/v1/analytics/production/summary \
  -H "Authorization: Bearer acme_sk_abc123..."
```

### Tenant Management API

#### Create Tenant
```bash
POST /api/v1/tenants/
{
  "tenant_code": "acme",
  "tenant_name": "ACME Dental Practice",
  "industry": "dental",
  "products": ["dentalerp"]
}
```

#### Get All Tenants
```bash
GET /api/v1/tenants/
# Returns list of all active tenants
```

#### Get Tenant by Code
```bash
GET /api/v1/tenants/{tenant_code}
# Returns tenant details with warehouses, users, integrations
```

#### Add Data Warehouse to Tenant
```bash
POST /api/v1/tenants/{tenant_id}/warehouses
{
  "warehouse_type": "snowflake",
  "warehouse_config": {
    "account": "acme-account.snowflakecomputing.com",
    "user": "acme_user",
    "password": "encrypted_password",
    "warehouse": "ACME_WH",
    "database": "ACME_DB",
    "schema": "BRONZE"
  },
  "is_primary": true
}
```

#### Add User to Tenant
```bash
POST /api/v1/tenants/{tenant_id}/users
{
  "user_id": "user@acme.com",
  "role": "admin",
  "permissions": {
    "analytics": true,
    "pdf_ingestion": true
  }
}
```

### How Multi-Tenancy Works

**1. Request arrives with tenant identifier** (subdomain, header, or API key)

**2. Tenant Identifier Middleware** (`src/middleware/tenant_identifier.py`):
   - Extracts tenant code from request
   - Validates tenant exists and is active
   - Sets tenant in request context using Python `contextvars`

**3. Warehouse Router** (`src/services/warehouse_router.py`):
   - Reads tenant from context
   - Fetches tenant's primary warehouse configuration
   - Returns tenant-specific warehouse connector (Snowflake or Databricks)
   - Maintains connection pool per tenant

**4. Integration Router** (`src/services/integration_router.py`):
   - Reads tenant from context
   - Fetches tenant's integration credentials (NetSuite, ADP, etc.)
   - Returns tenant-specific integration connector
   - Maintains connection pool per tenant

**5. All API endpoints automatically use tenant context**:
   ```python
   # Example: Analytics endpoint automatically queries tenant's warehouse
   @router.get("/api/v1/analytics/production/summary")
   async def get_production_summary():
       warehouse = await get_tenant_warehouse()  # Gets current tenant's warehouse
       tenant = TenantContext.get_tenant()
       logger.info(f"Tenant '{tenant.tenant_code}' querying production")
       results = await warehouse.execute_query(query)
       return results
   ```

### Database Schema

**Core Tables**:

1. **`tenants`** - Tenant registry
   - `id` (UUID) - Primary key
   - `tenant_code` (VARCHAR) - Unique code (e.g., 'acme', 'agentprovision')
   - `tenant_name` (VARCHAR) - Display name
   - `industry` (VARCHAR) - Industry type ('dental', 'medical')
   - `products` (JSON) - Enabled products array
   - `status` (VARCHAR) - 'active', 'suspended', 'deleted'
   - `settings` (JSON) - Tenant-specific configuration

2. **`tenant_warehouses`** - Data warehouse configs per tenant
   - `id` (UUID) - Primary key
   - `tenant_id` (UUID) - Foreign key to tenants
   - `warehouse_type` (VARCHAR) - 'snowflake' or 'databricks'
   - `warehouse_config` (JSON) - Encrypted connection details
   - `is_primary` (BOOLEAN) - Primary warehouse flag
   - `is_active` (BOOLEAN) - Active status

3. **`tenant_integrations`** - External integration credentials
   - `id` (UUID) - Primary key
   - `tenant_id` (UUID) - Foreign key to tenants
   - `integration_type` (VARCHAR) - 'netsuite', 'adp', 'dentrix', etc.
   - `integration_config` (JSON) - Encrypted API credentials
   - `is_active` (BOOLEAN) - Active status
   - `last_sync_at` (TIMESTAMP) - Last successful sync
   - `sync_status` (VARCHAR) - 'success', 'error', 'pending'
   - `sync_error` (TEXT) - Last error message

4. **`tenant_users`** - User-tenant mappings
   - `id` (UUID) - Primary key
   - `tenant_id` (UUID) - Foreign key to tenants
   - `user_id` (VARCHAR) - User email or external ID
   - `role` (VARCHAR) - 'admin', 'user', 'viewer'
   - `permissions` (JSON) - Product-specific permissions

5. **`tenant_api_keys`** - Tenant-specific API keys
   - `id` (UUID) - Primary key
   - `tenant_id` (UUID) - Foreign key to tenants
   - `key_hash` (VARCHAR) - Hashed API key
   - `key_prefix` (VARCHAR) - First 8 chars (e.g., 'acme_sk_')
   - `name` (VARCHAR) - Key description
   - `permissions` (JSON) - Scoped permissions
   - `expires_at` (TIMESTAMP) - Expiration date
   - `is_active` (BOOLEAN) - Active status

### Running Migrations

Migrations are SQL scripts in `migrations/` directory:

```bash
# Apply all migrations
docker exec dentalerp-postgres-1 psql -U postgres -d mcp -f /app/migrations/001_create_tenant_tables.sql
docker exec dentalerp-postgres-1 psql -U postgres -d mcp -f /app/migrations/002_create_tenant_integrations.sql

# Or via Docker Compose
cat migrations/001_create_tenant_tables.sql | docker exec -i dentalerp-postgres-1 psql -U postgres -d mcp
```

**Migration Files**:
- `001_create_tenant_tables.sql` - Core tenant tables (tenants, warehouses, users, api_keys)
- `002_create_tenant_integrations.sql` - External integration tables

### Security Features

1. **Context Isolation**: Python `contextvars` ensures thread-safe tenant context
2. **Credential Encryption**: All credentials stored as encrypted JSON
3. **Row-Level Security**: Database queries filtered by `tenant_id`
4. **API Key Scoping**: Tenant API keys only access their own data
5. **Status Validation**: Suspended/deleted tenants blocked at middleware
6. **Connection Pooling**: Isolated connection pools per tenant

### Backward Compatibility

The "default" tenant preserves single-tenant behavior:
- Automatically created by migration `001_create_tenant_tables.sql`
- All existing data associated with "default" tenant
- Public endpoints (health checks) bypass tenant middleware
- Single-tenant deployments work without configuration changes

### Testing Multi-Tenancy

```bash
# Create test tenant
curl -X POST http://localhost:8085/api/v1/tenants/ \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_code": "test_tenant",
    "tenant_name": "Test Tenant",
    "industry": "dental",
    "products": ["dentalerp"]
  }'

# Test tenant isolation
curl -H "X-Tenant-ID: test_tenant" \
     -H "Authorization: Bearer dev-mcp-api-key-..." \
     http://localhost:8085/api/v1/analytics/production/summary

# Should return empty or tenant-specific data, not default tenant's data
```

### Implementation Files

**Models**:
- `src/models/tenant.py` - SQLAlchemy models (151 lines)

**Core**:
- `src/core/tenant.py` - Tenant context management (84 lines)
- `src/core/database.py` - Database connection

**Middleware**:
- `src/middleware/tenant_identifier.py` - Tenant identification (235 lines)

**API**:
- `src/api/tenants.py` - Tenant CRUD endpoints (221 lines)

**Services**:
- `src/services/tenant_service.py` - Business logic (164 lines)
- `src/services/warehouse_router.py` - Warehouse routing (295 lines)
- `src/services/integration_router.py` - Integration routing (310 lines)

**Migrations**:
- `migrations/001_create_tenant_tables.sql` - Core tables (73 lines)
- `migrations/002_create_tenant_integrations.sql` - Integration tables (68 lines)

## 🔒 Authentication

All API endpoints (except `/health` and `/api/v1/tenants`) require authentication:

```bash
Authorization: Bearer <MCP_API_KEY>
```

Set your API key in the `.env` file:
```bash
MCP_API_KEY=your-secure-api-key-min-32-characters
```

For tenant-specific API keys, use the format: `{tenant_code}_sk_{random}`
```bash
# Example: ACME tenant API key
Authorization: Bearer acme_sk_abc123def456...
```

## 📊 Snowflake Data Layers

### Bronze Layer (Raw Data)
- `bronze.pms_day_sheets` - Raw PDF extractions
- Direct inserts from MCP server
- No transformations applied

### Silver Layer (Cleaned Data)
- `bronze_silver.stg_pms_day_sheets` - Validated & cleaned
- Data type conversions
- Business rule validations

### Gold Layer (Analytics)
- `bronze_gold.daily_production_metrics` - Daily KPIs
- `bronze_gold.practice_performance` - Practice-level metrics
- Pre-aggregated for fast queries

## 🧪 Testing

### Run Unit Tests
```bash
cd mcp-server
pytest tests/
```

### Test PDF Ingestion
```bash
./scripts/test-pdf-ingestion-e2e.sh
```

### Test Complete System
```bash
./scripts/test-complete-system.sh
```

### Manual API Testing

```bash
# Test health endpoint
curl http://localhost:8085/health

# Test Snowflake connection
curl -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  http://localhost:8085/api/v1/warehouse/status

# Upload test PDF
curl -X POST http://localhost:8085/api/v1/pdf/upload \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  -F "file=@examples/ingestion/test_daysheet.pdf" \
  -F "practice_location=Test Practice" \
  -F "use_ai=false"

# Check production analytics
curl -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  http://localhost:8085/api/v1/analytics/production/summary
```

## 🐛 Troubleshooting

### Snowflake Connection Issues

**Error:** `Snowflake is not configured`

**Solution:**
1. Verify `.env` file has all Snowflake credentials
2. Check account locator format: `ACCOUNT-REGION` (e.g., `HKTPGHW-ES87244`)
3. Restart MCP server: `docker-compose restart mcp-server`

```bash
# Test connection
curl -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  http://localhost:8085/api/v1/warehouse/status
```

### PDF Upload Failures

**Error:** `Failed to extract PDF`

**Solutions:**
- Check PDF is not password-protected
- Verify practice_location matches existing practice
- Try with `use_ai=true` if rules-based fails
- Check logs: `docker-compose logs mcp-server --tail=50`

### Database Connection Issues

**Error:** `database "mcp" does not exist`

**Solution:**
```bash
# Create database
docker exec dentalerp-postgres-1 psql -U postgres -c "CREATE DATABASE mcp;"

# Restart MCP server
docker-compose restart mcp-server
```

### API Authentication Failures

**Error:** `Not authenticated` or `403 Forbidden`

**Solution:**
1. Verify API key in request header
2. Check key matches `.env` file
3. Ensure key is at least 32 characters

```bash
# Test authentication
curl -H "Authorization: Bearer your-api-key-here" \
  http://localhost:8085/health
```

## 📚 Additional Documentation

- [Architecture Overview](./ARCHITECTURE.md)
- [Snowflake Setup Guide](./SNOWFLAKE_SETUP_GUIDE.md)
- [Integration API Reference](./INTEGRATION_API_REFERENCE.md)
- [Snowflake Authentication](./SNOWFLAKE_AUTHENTICATION.md)
- [Snowflake Orchestration](./SNOWFLAKE_ORCHESTRATION.md)

## 🔧 Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SNOWFLAKE_ACCOUNT` | Yes | - | Snowflake account locator |
| `SNOWFLAKE_USER` | Yes | - | Snowflake username |
| `SNOWFLAKE_PASSWORD` | Yes | - | Snowflake password |
| `SNOWFLAKE_WAREHOUSE` | No | `COMPUTE_WH` | Warehouse name |
| `SNOWFLAKE_DATABASE` | No | `DENTAL_ERP_DW` | Database name |
| `SNOWFLAKE_SCHEMA` | No | `PUBLIC` | Schema name |
| `SNOWFLAKE_ROLE` | No | `ACCOUNTADMIN` | Role name |
| `OPENAI_API_KEY` | No | - | OpenAI API key for AI extraction |
| `MCP_API_KEY` | Yes | - | API authentication key (32+ chars) |
| `SECRET_KEY` | Yes | - | JWT secret key (32+ chars) |
| `POSTGRES_HOST` | No | `postgres` | PostgreSQL host |
| `POSTGRES_DB` | No | `mcp` | PostgreSQL database |
| `POSTGRES_USER` | No | `postgres` | PostgreSQL username |
| `POSTGRES_PASSWORD` | No | `postgres` | PostgreSQL password |
| `REDIS_HOST` | No | `redis` | Redis host |
| `REDIS_PORT` | No | `6379` | Redis port |
| `ENVIRONMENT` | No | `development` | Environment mode |
| `DEBUG` | No | `false` | Debug logging |
| `LOG_LEVEL` | No | `INFO` | Logging level |

## 🚀 Production Deployment

### Using Docker Compose

```bash
# Set production environment variables
export MCP_API_KEY="your-secure-production-key"
export MCP_SECRET_KEY="your-secure-jwt-secret"
export SNOWFLAKE_ACCOUNT="your-account"
export SNOWFLAKE_USER="your-user"
export SNOWFLAKE_PASSWORD="your-password"
export OPENAI_API_KEY="your-openai-key"

# Deploy
./deploy.sh
```

The deploy script will:
1. Auto-detect environment (local vs VM)
2. Validate credentials (in VM mode)
3. Build and start services
4. Configure nginx & SSL (in VM mode)
5. Display service URLs

### VM Deployment

On a VM with nginx and certbot installed:

```bash
# The script auto-detects VM mode
./deploy.sh

# Services will be available at:
# - https://dentalerp.agentprovision.com (Frontend)
# - https://mcp.agentprovision.com (MCP Server)
```

### Health Monitoring

```bash
# Check all services
docker-compose ps

# Check MCP health
curl https://mcp.agentprovision.com/health

# Check detailed status
curl -H "Authorization: Bearer your-api-key" \
  https://mcp.agentprovision.com/health/detailed
```

## 📊 Performance

### Benchmarks

- **PDF Ingestion**: ~2-5 seconds per file (rules-based), ~8-15 seconds (AI)
- **Analytics Queries**: <500ms (Gold layer, pre-aggregated)
- **Snowflake Query**: ~200ms average
- **Concurrent Requests**: Handles 100+ concurrent PDF uploads

### Optimization Tips

1. **Use Rules-Based Extraction** for known PDF formats (faster)
2. **Enable AI Extraction** only when needed (higher accuracy)
3. **Batch Upload** multiple PDFs for efficiency
4. **Cache Analytics** queries in Redis (future enhancement)
5. **Pre-aggregate** metrics in Gold layer with dbt

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](../LICENSE) for details

## 💬 Support

- **Issues**: https://github.com/your-org/dentalERP/issues
- **Documentation**: https://docs.dentalerp.com
- **Email**: support@dentalerp.com

---

**Built with**: FastAPI • Snowflake • OpenAI • PostgreSQL • Redis • dbt
