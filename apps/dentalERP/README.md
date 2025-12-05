# DentalERP - Multi-Practice Management System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node.js Version](https://img.shields.io/badge/node-20%2B-brightgreen)](https://nodejs.org/)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-blue)](https://www.typescriptlang.org/)
[![React](https://img.shields.io/badge/React-18-61dafb)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-009688)](https://fastapi.tiangolo.com/)
[![Snowflake](https://img.shields.io/badge/Snowflake-Data%20Warehouse-29B5E8)](https://www.snowflake.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4%20Vision-412991)](https://openai.com/)
[![dbt](https://img.shields.io/badge/dbt-1.7%2B-FF694B)](https://www.getdbt.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)](https://www.docker.com/)

Modern dental practice management platform with AI-powered data extraction, Snowflake analytics, and multi-location support.

## 🎯 Core Features

- **AI Document Extraction**: GPT-4 Vision for PDF day sheets (production, payments, visits)
- **Snowflake Data Warehouse**: Bronze/Silver/Gold medallion architecture for analytics
- **Multi-Practice Support**: Manage Eastlake, Torrey Pines, and ADS from unified dashboard
- **Real-Time Analytics**: Production metrics, patient visits, collection rates by practice
- **MCP Integration Hub**: Centralized connector for NetSuite, ADP, Dentrix, DentalIntel
- **Role-Based Access**: Executive, Manager, Clinician, Staff dashboards

## 🚀 Quick Start

```bash
# Clone and start all services
git clone <repository-url>
cd dentalERP
docker-compose up

# Test the system
./scripts/test-complete-system.sh
```

**Access Points**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:3001
- MCP Server: http://localhost:8085
- API Docs: http://localhost:8085/docs

**Default Credentials**: See `backend/src/database/seed.ts`

## 🏗️ Architecture

```
┌─────────────────┐
│  React Frontend │  TypeScript + Vite + Zustand
│     :3000       │  Analytics Dashboard
└────────┬────────┘
         │
┌────────▼────────┐
│  Node.js API    │  Express + PostgreSQL + Redis
│     :3001       │  Auth + Business Logic
└────────┬────────┘
         │
┌────────▼────────┐
│   MCP Server    │  FastAPI + Python
│     :8085       │  Integration Hub (Multi-Tenant)
└────────┬────────┘
         │
    ┌────┴────┬─────────────┬──────────┐
    ▼         ▼             ▼          ▼
Snowflake  NetSuite  ADP Payroll  Dentrix PMS
(Analytics) (ERP)    (HR)         (Clinical)
```

## 🏢 Multi-Tenant Architecture

The MCP Server implements **complete multi-tenancy** to support multiple organizations (AgentProvision.com and individual dental practices) using the same infrastructure while maintaining data isolation.

### Key Features

- **Tenant Isolation**: Each tenant has isolated data warehouses, credentials, and integrations
- **Flexible Identification**: Tenants identified via subdomain, X-Tenant-ID header, or API key prefix
- **Multiple Data Warehouses**: Support for Snowflake and Databricks per tenant
- **External Integration Routing**: Tenant-specific credentials for NetSuite, ADP, Dentrix, etc.
- **Connection Pooling**: Cached connectors per tenant for optimal performance
- **Backward Compatible**: "default" tenant preserves existing single-tenant functionality

### Multi-Tenant Architecture Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                      Incoming Request                          │
│  (subdomain, X-Tenant-ID header, or API key prefix)           │
└───────────────────────────────┬────────────────────────────────┘
                                │
                ┌───────────────▼──────────────┐
                │  Tenant Identifier Middleware │
                │  - Extract tenant code        │
                │  - Validate tenant status     │
                │  - Set tenant context         │
                └───────────────┬──────────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        │                                               │
┌───────▼────────┐                            ┌─────────▼────────┐
│ Warehouse       │                            │ Integration      │
│ Router          │                            │ Router           │
│ - Snowflake     │                            │ - NetSuite       │
│ - Databricks    │                            │ - ADP            │
│                 │                            │ - Dentrix        │
└───────┬────────┘                            └─────────┬────────┘
        │                                               │
        │ Tenant-specific                              │ Tenant-specific
        │ warehouse config                             │ credentials
        │                                               │
┌───────▼──────────────────────────────────────────────▼────────┐
│                   Tenant's External Systems                    │
│  - Data Warehouse (Snowflake/Databricks)                     │
│  - ERP (NetSuite)                                             │
│  - HR/Payroll (ADP)                                           │
│  - PMS (Dentrix, Eaglesoft, OpenDental, etc.)                │
└────────────────────────────────────────────────────────────────┘
```

### Database Schema

**Tenant Registry** (`tenants` table):
- Unique tenant code (e.g., 'default', 'acme', 'agentprovision')
- Tenant name and industry
- Products enabled per tenant
- Status (active, suspended, deleted)

**Tenant Data Warehouses** (`tenant_warehouses` table):
- Warehouse type (Snowflake, Databricks)
- Connection credentials (encrypted)
- Primary warehouse flag
- Active status

**Tenant Integrations** (`tenant_integrations` table):
- Integration type (NetSuite, ADP, Dentrix, Eaglesoft, DentalIntel, OpenDental, CurveDental)
- API credentials and config (encrypted JSON)
- Sync status and last sync timestamp
- Error tracking

**Tenant Users** (`tenant_users` table):
- User-to-tenant mappings
- Role-based access control
- Product-specific permissions

**Tenant API Keys** (`tenant_api_keys` table):
- Tenant-specific API keys
- Key prefix for identification (e.g., 'acme_sk_...')
- Scoped permissions
- Expiration and usage tracking

### Tenant Identification Methods

#### 1. Subdomain Extraction
```bash
# Request to acme.dentalerp.com
curl https://acme.dentalerp.com/api/v1/analytics/production/summary
# → Tenant: 'acme'
```

#### 2. X-Tenant-ID Header
```bash
curl -H "X-Tenant-ID: acme" \
     -H "Authorization: Bearer dev-mcp-api-key-..." \
     http://localhost:8085/api/v1/analytics/production/summary
# → Tenant: 'acme'
```

#### 3. API Key Prefix
```bash
curl -H "Authorization: Bearer acme_sk_abc123..." \
     http://localhost:8085/api/v1/analytics/production/summary
# → Tenant: 'acme' (extracted from key prefix)
```

### Usage Examples

#### Create a New Tenant
```bash
curl -X POST http://localhost:8085/api/v1/tenants/ \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_code": "acme",
    "tenant_name": "ACME Dental Practice",
    "industry": "dental",
    "products": ["dentalerp"]
  }'
```

#### Add Tenant Warehouse
```bash
curl -X POST http://localhost:8085/api/v1/tenants/{tenant_id}/warehouses \
  -H "Content-Type: application/json" \
  -d '{
    "warehouse_type": "snowflake",
    "warehouse_config": {
      "account": "your-account.snowflakecomputing.com",
      "user": "acme_user",
      "password": "encrypted_password",
      "warehouse": "ACME_WH",
      "database": "ACME_DB",
      "schema": "BRONZE"
    },
    "is_primary": true
  }'
```

#### Query Tenant Data
```bash
# All analytics endpoints automatically use the tenant's warehouse
curl -H "X-Tenant-ID: acme" \
     -H "Authorization: Bearer dev-mcp-api-key-..." \
     http://localhost:8085/api/v1/analytics/production/summary
# Queries ACME's Snowflake warehouse, not the default one
```

### Security Features

- **Context Isolation**: Python `contextvars` ensures thread-safe request-scoped tenant context
- **Credential Encryption**: All integration credentials stored as encrypted JSON
- **Row-Level Security**: Database queries automatically filtered by tenant_id
- **API Key Scoping**: Tenant API keys only access their own data
- **Status Validation**: Suspended or deleted tenants blocked at middleware level

### Implementation Files

- `mcp-server/src/models/tenant.py` - Tenant data models (151 lines)
- `mcp-server/src/core/tenant.py` - Tenant context management (84 lines)
- `mcp-server/src/middleware/tenant_identifier.py` - Identification middleware (235 lines)
- `mcp-server/src/api/tenants.py` - Tenant CRUD API (221 lines)
- `mcp-server/src/services/tenant_service.py` - Business logic (164 lines)
- `mcp-server/src/services/warehouse_router.py` - Warehouse routing (295 lines)
- `mcp-server/src/services/integration_router.py` - Integration routing (310 lines)
- `mcp-server/migrations/001_create_tenant_tables.sql` - Database schema (73 lines)
- `mcp-server/migrations/002_create_tenant_integrations.sql` - Integration schema (68 lines)

See [MCP Server README](./mcp-server/README.md) for detailed technical documentation.

### Technology Stack

| Layer | Tech | Purpose |
|-------|------|---------|
| Frontend | React 18 + TypeScript + Tailwind | Production analytics dashboard |
| Backend | Node.js 20 + Express + Drizzle | REST API + Authentication |
| MCP Server | Python 3.11 + FastAPI | AI extraction + Integrations |
| Data Warehouse | Snowflake | Bronze → Silver → Gold pipeline |
| Transformations | dbt | SQL-based data modeling |
| Databases | PostgreSQL 15 + Redis 7 | Operational data + Cache |

## 📊 Data Pipeline

### AI-Powered PDF Extraction

```bash
# Upload PDF day sheet with AI extraction
curl -X POST http://localhost:8085/api/v1/pdf/upload \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  -F "file=@examples/ingestion/Eastlake Day 07 2025.pdf" \
  -F "practice_location=Eastlake" \
  -F "use_ai=true"
```

**AI Extraction Features**:
- OpenAI GPT-4 Vision (gpt-4o) for multimodal understanding
- Extracts: date, production, adjustments, net, collections, patient visits
- Data quality scores (0-1) per extraction
- Fallback to rules-based parser if AI unavailable

### Data Flow

```
PDF Upload → AI Extraction → Bronze Layer (raw JSON)
                ↓
         dbt Transformations
                ↓
    Silver Layer (cleaned/standardized)
                ↓
         Gold Layer (analytics-ready)
                ↓
    Analytics API → React Dashboard
```

**Snowflake Schema**:
- **Bronze**: `bronze.pms_day_sheets` - Raw extracted data (VARIANT column)
- **Silver**: `bronze_silver.stg_pms_day_sheets` - Cleaned and typed
- **Gold**: `bronze_gold.daily_production_metrics` - Aggregated metrics

## 📈 Analytics API

### Production Endpoints

All endpoints query Snowflake Gold layer directly (thin API layer):

```bash
# Daily production metrics
GET /api/v1/analytics/production/daily
  ?practice_location=Eastlake
  &start_date=2025-06-01
  &end_date=2025-07-31
  &limit=100

# Summary statistics
GET /api/v1/analytics/production/summary
  ?practice_location=Eastlake
  &start_date=2025-06-01

# By-practice comparison
GET /api/v1/analytics/production/by-practice
  ?start_date=2025-06-01
  &end_date=2025-07-31
```

**Sample Response**:
```json
{
  "PRACTICE_LOCATION": "Eastlake",
  "REPORT_DATE": "2025-07-01",
  "TOTAL_PRODUCTION": 109327.27,
  "NET_PRODUCTION": 109327.27,
  "COLLECTIONS": 72545.0,
  "PATIENT_VISITS": 464,
  "PRODUCTION_PER_VISIT": 235.62,
  "COLLECTION_RATE_PCT": 66.37,
  "DATA_QUALITY_SCORE": 0.95,
  "EXTRACTION_METHOD": "ai"
}
```

## 🧪 Testing

### End-to-End System Test

```bash
# Comprehensive test suite (6 tests)
./scripts/test-complete-system.sh

# Tests include:
# 1. Service health checks (MCP, Backend)
# 2. Snowflake connectivity (Bronze/Silver/Gold)
# 3. Analytics API endpoints
# 4. Data consistency across layers
# 5. Practice name alignment
# 6. dbt transformations
```

### PDF Ingestion Test

```bash
# Test AI extraction with sample PDF
./scripts/test-pdf-ingestion-e2e.sh

# Test all PDFs in examples directory
./scripts/test-all-pdfs.sh

# Test specific PDF with AI
USE_AI=true ./scripts/test-pdf-ingestion-e2e.sh
```

### Data Verification

```bash
# Python script to verify Snowflake data
python3 examples/ingestion/verify-data.py

# Expected output:
# ✅ Bronze: 11 records
# ✅ Silver: 11 records
# ✅ Gold: 4 records
# ✅ Total Production: $847,822.48
```

## 📁 Project Structure

```
dentalERP/
├── frontend/                    # React + TypeScript SPA
│   ├── src/
│   │   ├── pages/analytics/     # Production analytics dashboard
│   │   ├── hooks/               # React Query hooks (useProductionDaily)
│   │   ├── services/            # API client (analyticsAPI)
│   │   └── store/               # Zustand state management
│   └── .env                     # VITE_PROXY_TARGET=http://localhost:8085
│
├── backend/                     # Node.js + Express API
│   ├── src/
│   │   ├── database/            # Drizzle ORM schema + seed data
│   │   ├── routes/              # REST API endpoints
│   │   ├── services/            # Business logic (auth, mcpClient)
│   │   └── middleware/          # Auth, audit, error handling
│   └── .env                     # DATABASE_URL, MCP_API_URL
│
├── mcp-server/                  # Python + FastAPI Integration Hub
│   ├── src/
│   │   ├── api/                 # REST endpoints
│   │   │   ├── analytics.py     # Production analytics (3 endpoints)
│   │   │   ├── pdf_ingestion.py # PDF upload + AI extraction
│   │   │   └── dbt_runner.py    # Trigger dbt transformations
│   │   ├── services/            # Business logic
│   │   │   ├── pdf_ingestion.py # OpenAI GPT-4 Vision integration
│   │   │   └── dbt_runner.py    # dbt subprocess execution
│   │   ├── connectors/          # External system clients
│   │   │   └── snowflake.py     # Snowflake connector
│   │   └── main.py              # FastAPI application
│   ├── .env                     # OPENAI_API_KEY, SNOWFLAKE_*
│   └── seed_data.py             # Integration mappings seed script
│
├── dbt/dentalerp/               # dbt Transformations
│   ├── models/
│   │   ├── bronze/              # Source definitions
│   │   ├── silver/              # Staging models (stg_pms_day_sheets)
│   │   └── gold/                # Analytics models (daily_production_metrics)
│   ├── dbt_project.yml          # Project configuration
│   └── .gitignore               # Exclude dbt_packages/
│
├── examples/ingestion/          # Sample PDFs for testing
│   ├── Eastlake Day 07 2025.pdf
│   ├── Torrey Pines Day 08 2025.pdf
│   └── verify-data.py
│
├── scripts/                     # Shell scripts and utilities
│   ├── test-complete-system.sh  # Comprehensive system test
│   ├── test-pdf-ingestion-e2e.sh # PDF upload test
│   ├── test-all-pdfs.sh         # Batch PDF test
│   ├── test-ai-extraction.sh    # AI extraction test
│   ├── setup-snowflake-connection.sh # Snowflake setup
│   └── *.sh                     # Other utility scripts
│
├── documentation/               # Project documentation
│   ├── DOCKER_E2E_TEST_GUIDE.md
│   ├── PDF_INGESTION_GUIDE.md
│   ├── SNOWFLAKE_FRONTEND_INTEGRATION.md
│   └── *.md                     # Other documentation
│
├── docker-compose.yml           # Development environment
├── deploy.sh                    # Production deployment
└── README.md                    # This file
```

## 🔐 Environment Variables

### Backend (`backend/.env`)

```bash
NODE_ENV=development
PORT=3001
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dental_erp_dev
REDIS_URL=redis://localhost:6379

# MCP Integration
MCP_API_URL=http://localhost:8085
MCP_API_KEY=dev-mcp-api-key-change-in-production-min-32-chars

# Auth
JWT_SECRET=your-jwt-secret-min-32-chars
JWT_REFRESH_SECRET=your-refresh-secret-min-32-chars
JWT_EXPIRES_IN=15m
JWT_REFRESH_EXPIRES_IN=7d
```

### MCP Server (`mcp-server/.env`)

```bash
# API Security
MCP_API_KEY=dev-mcp-api-key-change-in-production-min-32-chars
MCP_SECRET_KEY=dev-secret-key-change-in-production-min-32-chars

# OpenAI (for AI extraction)
OPENAI_API_KEY=sk-...

# Snowflake Data Warehouse
SNOWFLAKE_ACCOUNT=your-account.snowflakecomputing.com
SNOWFLAKE_USER=your-user
SNOWFLAKE_PASSWORD=your-password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=DENTAL_ERP_DW
SNOWFLAKE_SCHEMA=BRONZE

# Database
POSTGRES_HOST=postgres
POSTGRES_DB=mcp
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
```

### Frontend (`frontend/.env`)

```bash
VITE_API_BASE_URL=/api
VITE_WS_URL=/socket.io
VITE_PROXY_TARGET=http://localhost:8085
VITE_NODE_ENV=development
```

## 🗄️ Database Setup

### PostgreSQL Schemas

**ERP Backend Database** (`dental_erp_dev`):
- User authentication and authorization
- Practice and location management
- Patient and appointment data
- Integration job tracking

**MCP Server Database** (`mcp`):
- Integration mappings and credentials
- Data source configurations
- Sync job history

### Snowflake Setup

```sql
-- Run snowflake-setup-updated.sql in Snowflake UI
-- Creates:
-- 1. Bronze schema (raw ingestion)
-- 2. Silver schema (cleaned data)
-- 3. Gold schema (analytics)
-- 4. Sample data for all 3 practices

-- Database: DENTAL_ERP_DW
-- Schemas: BRONZE, BRONZE_SILVER, BRONZE_GOLD
```

**Key Tables**:
- `bronze.pms_day_sheets` - Raw PDF extractions
- `bronze_silver.stg_pms_day_sheets` - Cleaned staging
- `bronze_gold.daily_production_metrics` - Analytics-ready

## 🔄 Development Workflow

### 1. Start Development Environment

```bash
docker-compose up -d
```

### 2. Seed Data

```bash
# Backend seed (practices, users)
cd backend
npm run db:seed

# MCP seed (integration mappings)
cd mcp-server
python seed_data.py

# Or use the setup script
./scripts/setup-snowflake-connection.sh
```

### 3. Upload Sample PDFs

```bash
# Upload with AI extraction
curl -X POST http://localhost:8085/api/v1/pdf/upload \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  -F "file=@examples/ingestion/Eastlake Day 07 2025.pdf" \
  -F "practice_location=Eastlake" \
  -F "use_ai=true"
```

### 4. Run dbt Transformations

```bash
# Via API
curl -X POST http://localhost:8085/api/v1/dbt/run/pdf-pipeline \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars"

# Or directly
cd dbt/dentalerp
dbt run
```

### 5. View Analytics

Navigate to:
- http://localhost:3000/analytics/production

## 🧩 Integration Guide

### Adding a New Practice

1. **Update Backend Seed Data** (`backend/src/database/seed.ts`):
   ```typescript
   const practiceSeed: NewPractice[] = [
     {
       name: 'New Practice',
       address: { street: '123 Main St', city: 'Seattle', state: 'WA', ... },
       phone: '206-555-0400',
       email: 'newpractice@dentalerp.demo',
       isActive: true,
     },
   ];
   ```

2. **Add Snowflake Sample Data** (`snowflake-setup-updated.sql`):
   ```sql
   INSERT INTO bronze.pms_day_sheets VALUES (
     'sample-newpractice-20250601',
     'New Practice',
     '2025-06-01',
     ...
   );
   ```

3. **Run Seeds and Tests**:
   ```bash
   npm run db:seed
   ./scripts/test-complete-system.sh
   ```

### Adding External Integration

1. **Create Connector** (`mcp-server/src/connectors/new_system.py`):
   ```python
   class NewSystemConnector:
       def __init__(self, api_key: str):
           self.api_key = api_key

       async def fetch_data(self):
           # Implementation
   ```

2. **Register in MCP** (`mcp-server/seed_data.py`):
   ```python
   integrations = [
       {"type": "new_system", "name": "New System", "enabled": True},
   ]
   ```

3. **Add Credentials** (`mcp-server/.env`):
   ```bash
   NEW_SYSTEM_API_KEY=your-key
   ```

## 📝 Practice Information

### Current Practices

| Practice | Location | PMS System | Area Code |
|----------|----------|------------|-----------|
| Eastlake | Seattle, WA | Eaglesoft v21.00.18 | 206 |
| Torrey Pines | San Diego, CA | Dentrix v23.4.4.11088 | 858 |
| ADS | San Diego, CA | Dentrix v23.4.4.11088 | 858 |

### Test Data Summary

```bash
# Run verification script
python3 examples/ingestion/verify-data.py

# Expected Results:
# Bronze Layer: 11 records (raw PDFs)
# Silver Layer: 11 records (cleaned)
# Gold Layer: 4 records (aggregated)
# Total Production: $847,822.48
# Total Visits: 464
# Practices: Eastlake (primary test data)
```

## 🚢 Deployment

### Production Environment

**Domains**:
- ERP: https://dentalerp.agentprovision.com
- MCP: https://mcp.agentprovision.com

**Deploy Script**:
```bash
./deploy.sh
```

**CI/CD Pipeline**:
- GitHub Actions workflow in `.github/workflows/`
- Automated testing on PR
- Deploy to production on merge to `main`

## 🔍 Troubleshooting

### Common Issues

**MCP Server Not Starting**:
```bash
# Check logs
docker logs dentalerp-mcp-server-1

# Common fix: Ensure Snowflake credentials are set
docker-compose restart mcp-server
```

**Frontend Build Issues**:
```bash
# Clear cache and rebuild
docker-compose build --no-cache frontend
docker-compose up frontend
```

**Snowflake Connection Failed**:
```bash
# Test connection
python3 << EOF
import snowflake.connector
conn = snowflake.connector.connect(
    account='your-account',
    user='your-user',
    password='your-password'
)
print("Connected!")
EOF
```

**dbt Transformations Failing**:
```bash
# Check dbt logs
cd dbt/dentalerp
dbt debug
dbt run --full-refresh
```

## 📚 Documentation

- **Architecture**: This README
- **API Documentation**: http://localhost:8085/docs (FastAPI interactive docs)
- **Testing Guide**: `documentation/DOCKER_E2E_TEST_GUIDE.md`
- **Frontend Integration**: `documentation/frintend-integration-mcp.md`
- **Data Ingestion**: `documentation/test-data-ingestion-full.md`
- **PDF Ingestion**: `documentation/PDF_INGESTION_GUIDE.md`
- **Snowflake Integration**: `documentation/SNOWFLAKE_FRONTEND_INTEGRATION.md`
- **Design System**: `design-system/` directory
- **Wireframes**: `wireframes/` directory
- **Scripts**: `scripts/` directory (all test and utility scripts)

## 🤝 Contributing

1. Follow conventional commits: `feat:`, `fix:`, `chore:`, etc.
2. Update tests for new features
3. Ensure `./scripts/test-complete-system.sh` passes
4. Update documentation

## 📄 License

MIT License - See `package.json`

---

**Built with**:
React • TypeScript • Node.js • FastAPI • Snowflake • dbt • OpenAI GPT-4 • PostgreSQL • Redis • Docker
