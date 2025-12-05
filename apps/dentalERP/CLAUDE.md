# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# DentalERP Codebase Overview

This document provides a comprehensive guide to the DentalERP codebase structure, key architectural patterns, and development workflows.

## High-Level Architecture

DentalERP is a **multi-layer, multi-tenant dental practice management system** with AI-powered data extraction, analytics via Snowflake, and integrations with external ERP/HR/PMS systems.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ARCHITECTURE OVERVIEW                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  React Frontend (Port 3000)                                             │
│  └─ TypeScript + Vite + Zustand + TanStack Query                        │
│     └─ Multi-role dashboards: Executive, Manager, Clinician, Staff      │
│                     │                                                    │
│                     ▼                                                    │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │      Backend API (Port 3001) - Express + PostgreSQL           │       │
│  │  ├─ Authentication & JWT tokens                              │       │
│  │  ├─ Business logic & routing                                 │       │
│  │  ├─ User/Practice/Integration management                     │       │
│  │  └─ Socket.IO for real-time updates                          │       │
│  └──────────────────────────────────────────────────────────────┘       │
│                     │                                                    │
│                     ▼                                                    │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │  MCP Server (Port 8085) - FastAPI + Multi-Tenant Support      │       │
│  │  ├─ Tenant context management (contextvars)                  │       │
│  │  ├─ Warehouse routing (Snowflake/Databricks)                 │       │
│  │  ├─ Integration routing (NetSuite, ADP, Dentrix, etc.)       │       │
│  │  ├─ PDF AI extraction (OpenAI GPT-4 Vision)                  │       │
│  │  ├─ Analytics APIs (thin layer to warehouse)                 │       │
│  │  └─ dbt transformation orchestration                         │       │
│  └──────────────────────────────────────────────────────────────┘       │
│         │                                    │                          │
│         ▼                                    ▼                          │
│  ┌────────────────────────┐    ┌──────────────────────────────┐         │
│  │ Snowflake Data         │    │ External Systems             │         │
│  │ Warehouse              │    │ ├─ NetSuite (Finance)       │         │
│  │ ├─ Bronze (raw)        │    │ ├─ ADP (Payroll)            │         │
│  │ ├─ Silver (clean)      │    │ ├─ Dentrix (PMS)            │         │
│  │ └─ Gold (analytics)    │    │ ├─ Eaglesoft (PMS)          │         │
│  └────────────────────────┘    │ └─ DentalIntel (Analytics)  │         │
│         │                       └──────────────────────────────┘         │
│         ▼                                                                │
│  ┌────────────────────────┐                                             │
│  │ dbt Transformations    │                                             │
│  │ └─ Bronze→Silver→Gold  │                                             │
│  └────────────────────────┘                                             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Essential Commands

### Development Environment
```bash
# Start all services (frontend + backend + MCP + databases)
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f                        # All services
docker-compose logs -f mcp-server             # Specific service

# Rebuild services after code changes
docker-compose build                          # All services
docker-compose build --no-cache mcp-server    # Specific service

# Start production profile (prod images + nginx)
docker-compose --profile production up -d

# Start with tools profile (includes pgAdmin)
docker-compose --profile tools up -d

# Install all dependencies across workspaces
npm run install:all

# Run both frontend and backend concurrently (outside Docker)
npm run dev

# Frontend only (outside Docker)
npm run dev:frontend

# Backend only (outside Docker)
npm run dev:backend
```

### Database Operations
```bash
# Run migrations (applies pending migrations)
npm run db:migrate

# Seed test data (populate with sample data)
npm run db:seed

# Reset database (drop and recreate)
npm run db:reset

# Generate new migration file from schema changes
npm run db:generate

# Push schema directly to database (dev only)
cd backend && npm run db:push
```

### Build & Test
```bash
# Build all components
npm run build

# Type checking
npm run type-check

# Linting
npm run lint

# Run all tests
npm run test

# Frontend unit tests
npm run test:frontend

# Backend unit tests
npm run test:backend

# E2E tests
npm run test:e2e
```

### System Integration Tests
```bash
# Full system integration test (6 comprehensive tests)
./scripts/test-complete-system.sh

# PDF ingestion test with AI extraction
./scripts/test-pdf-ingestion-e2e.sh

# Test all PDFs in examples directory
./scripts/test-all-pdfs.sh

# Multi-tenant workflow test
./scripts/test-multi-tenant-e2e.sh

# Snowflake connectivity test
./scripts/test-snowflake.sh
```

### Production Environment Tests
```bash
# Set production API key
export MCP_API_KEY="your-production-mcp-api-key"

# Full production system test (9 test suites, ~30 tests)
./scripts/test-production.sh

# NetSuite E2E test (journal entries, accounts, sync status)
./scripts/test-netsuite-e2e.sh

# NetSuite SuiteQL test (direct API query validation)
./scripts/test-netsuite-suiteql.sh
```

### Running Individual Tests
```bash
# Frontend (Vitest)
cd frontend
npm run test                                    # All tests in watch mode
npm run test src/path/to/file.test.ts          # Single test file
npm run test -- --run                           # Run once (CI mode)
npm run test:coverage                           # With coverage
npm run test:ui                                 # Launch Vitest UI
npm run test:e2e                                # Run Playwright E2E tests
npm run test:e2e:ui                             # Playwright UI mode

# Backend (Jest)
cd backend
npm run test                                    # All tests in watch mode
npm run test src/path/to/file.test.ts          # Single test file
npm run test -- --watch=false                   # Run once (CI mode)
npm run test:coverage                           # With coverage

# MCP Server (pytest)
cd mcp-server
pytest tests/test_specific.py                  # Single test file
pytest tests/test_specific.py::test_function   # Single test function
pytest -v                                       # Verbose output
pytest -k "keyword"                             # Run tests matching keyword
pytest --lf                                     # Rerun last failed tests
pytest -x                                       # Stop on first failure
pytest --pdb                                    # Drop to debugger on failure
```

### dbt Transformations
```bash
cd dbt/dentalerp
dbt debug                         # Test Snowflake connection
dbt run                           # Run all models (Bronze → Silver → Gold)
dbt run --select pdf-pipeline     # Run specific model selector
dbt test                          # Run data quality tests
dbt docs generate                 # Generate documentation
dbt docs serve                    # View docs in browser (localhost:8080)
./scripts/run-dbt.sh              # Convenience script to run dbt
```

### MCP Server (Python)
```bash
cd mcp-server

# Setup and seeding
python seed_data.py                        # Seed integration mappings
pip install -r requirements.txt            # Install dependencies
pip install -e .                           # Install in editable mode

# Testing
pytest                                      # Run all tests
pytest -v                                   # Verbose output
pytest tests/test_*.py                      # Run specific test file
pytest --cov                                # Run with coverage

# Development server (outside Docker)
uvicorn src.main:app --reload --port 8085
```

### Manual Data Ingestion (CSV/Excel Upload)

```bash
# Upload NetSuite TransactionDetail CSV
curl -X POST http://localhost:8085/api/v1/netsuite/upload/transactions \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  -H "X-Tenant-ID: silvercreek" \
  -F "file=@backup/TransactionDetail-83.csv"

# Bulk upload all NetSuite CSVs from backup/ directory
curl -X POST http://localhost:8085/api/v1/netsuite/upload/bulk-transactions \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  -H "X-Tenant-ID: silvercreek"

# Upload Operations Report (Excel or CSV)
curl -X POST http://localhost:8085/api/v1/operations/upload \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  -H "X-Tenant-ID: silvercreek" \
  -F "file=@operations_report.xlsx" \
  -F "practice_code=lhd" \
  -F "practice_name=Laguna Hills Dental" \
  -F "report_month=2025-11-01"

# Test manual ingestion endpoints
./scripts/test-manual-ingestion.sh
```

**Duplicate Handling**:
- NetSuite: Deletes existing records for same subsidiary and date range before insert
- Operations: Uses MERGE (upsert) on practice_code + report_month key
- Both are idempotent - safe to re-upload same files

**Data Flow**: CSV Upload → MCP Parser → Snowflake Bronze → Dynamic Tables Auto-Refresh → Gold Layer → Analytics API

### Data Seeding & Demo Setup
```bash
# Load CSV demo data into Snowflake (for client demos)
./scripts/insert_demo_data.sh

# Process NetSuite CSV exports to Bronze format
python scripts/python/load_csv_to_snowflake.py

# Seed Snowflake from CSV files
python scripts/python/seed_snowflake_from_csv.py

# Ingest multi-practice NetSuite data
python scripts/ingest-netsuite-multi-practice.py
```

## Key Architectural Patterns

### 1. Frontend Architecture (React + Zustand)

**State Management:**
- **Zustand Store** (`authStore.ts`): User, auth tokens, practices (persisted to localStorage)
- **React Query**: Server state (analytics, integrations) with caching
- **React Context**: TenantContext for multi-tenant awareness
- **Route-based code splitting**: Pages lazy-loaded with React.lazy()

**Routing Pattern:**
```
/auth/login, /auth/register (PublicRoute - redirect if authenticated)
/dashboard (ProtectedRoute - requires auth)
/executive, /compare, /analytics/* (ProtectedRoute with role checks)
/admin/mcp (ProtectedRoute - admin only)
```

**API Integration:**
- **Axios instance** with automatic token injection and refresh logic
- Request interceptor: adds `Authorization: Bearer <token>` & `X-Tenant-ID` header
- Response interceptor: handles 401 with token refresh queue
- Base URL: `/api` (proxied to backend in dev, direct in prod)

**Key Files:**
- `App.tsx`: Route definitions, ProtectedRoute wrapper, lazy loading
- `authStore.ts`: User/practice state with selectors for optimization
- `services/api.ts`: Axios setup with interceptors
- `services/mcpAPI.ts`: Direct MCP Server calls (bypasses backend)
- `hooks/useAnalytics.ts`: React Query hooks for dashboard data

---

### 2. Backend Architecture (Express + PostgreSQL)

**Middleware Stack:**
```javascript
CORS → Helmet (security) → Rate Limiting → Morgan (logging)
→ Body Parser → Compression → Auth Middleware (protected routes only)
→ Audit Middleware (log all changes)
→ Route Handler → Error Handler (global, at end)
```

**Request Flow for Protected Routes:**
1. **authMiddleware**: Extracts JWT token, validates, adds `req.user` to request
2. **auditMiddleware**: Logs action (user, endpoint, timestamp)
3. **Route handler**: Business logic, calls MCP Server via `MCPClient`
4. **Error handler**: Catches errors, returns standardized JSON response

**Database (PostgreSQL + Drizzle ORM):**
- Drizzle ORM for type-safe queries (no string SQL)
- Migrations in `/drizzle` folder (Drizzle Kit auto-generates)
- Schema: Users, Practices, Locations, UserPractices (M2M), Integrations, IntegrationCredentials
- Indexes on foreign keys for performance

**MCP Client Integration:**
- `mcpClient.ts`: Centralized HTTP client for all MCP Server calls
- Retries built-in via axios
- All external system access goes through MCP (no direct API calls)
- Base URL: `MCP_API_URL` environment variable (default: http://localhost:8085)

**Key Files:**
- `server.ts`: Express app init, middleware setup, route registration
- `config/environment.ts`: Zod schema for env validation
- `database/schema.ts`: Drizzle table definitions
- `middleware/auth.ts`: JWT verification
- `services/mcpClient.ts`: MCP Server HTTP client
- `services/analytics.ts`: Analytics query builders (calls MCP)

---

### 3. MCP Server Architecture (FastAPI + Multi-Tenant)

**Tenant Identification (Priority Order):**
1. **Subdomain**: `acme.dentalerp.com` → `acme` tenant
2. **X-Tenant-ID header**: `X-Tenant-ID: acme`
3. **API key prefix**: `acme_sk_abc123...` → extract `acme`
4. Default to `default` tenant if none provided

**Tenant Context (Python contextvars):**
```python
# Thread-safe, async-safe request-scoped storage
_tenant_context: ContextVar[Optional[Tenant]] = ContextVar('tenant', default=None)

# In middleware:
TenantContext.set_tenant(tenant_obj)
# In endpoint:
tenant = TenantContext.require_tenant()  # Gets from context
```

**Middleware Pipeline:**
```
Request → CORS → TenantIdentifierMiddleware (extract, validate, set context)
→ Route Handler (can access TenantContext.get_tenant())
→ Warehouse Router / Integration Router (use tenant context)
```

**Warehouse Router:**
- Loads tenant's warehouse config from `tenant_warehouses` table
- Supports Snowflake & Databricks
- Caches connectors per tenant_id+warehouse_type
- Falls back to primary warehouse if type not specified

**Integration Router:**
- Loads tenant's integration credentials from `tenant_integrations` table
- Routes to Snowflake, NetSuite, ADP, Dentrix, Eaglesoft, DentalIntel
- Decrypts credentials on load
- Handles missing integrations gracefully

**Database Schema (PostgreSQL):**
```
tenants (id, tenant_code, tenant_name, status, products[])
tenant_warehouses (id, tenant_id, type, config{}, is_primary)
tenant_integrations (id, tenant_id, type, config{}, status)
tenant_users (id, user_id, tenant_id, role)
tenant_api_keys (id, tenant_id, key_prefix, scoped_permissions)
```

**PDF AI Extraction:**
- Endpoint: `POST /api/v1/pdf/upload`
- Extracts with OpenAI GPT-4 Vision (gpt-4o model)
- Parses: date, production, adjustments, net, collections, visits
- Scores extraction quality (0-1)
- Stores raw data in Snowflake Bronze layer
- Falls back to rules-based parser if AI unavailable

**dbt Orchestration:**
- Endpoint: `POST /api/v1/dbt/run/{selector}`
- Triggers `dbt run --select {selector}` via subprocess
- Logs output to MCP logs
- Returns job status

**APScheduler Automation:**
- Automated job scheduling for background tasks
- Daily full sync at 2am UTC
- Incremental sync every 4 hours
- Alert generation and insights computation
- Auto-batching (3,000 records per NetSuite request)
- MERGE-based deduplication

**Key Files:**
- `main.py`: FastAPI app, router registration, lifespan
- `core/tenant.py`: TenantContext class (contextvars)
- `middleware/tenant_identifier.py`: Tenant extraction & validation
- `services/tenant_service.py`: CRUD operations on tenants table
- `services/warehouse_router.py`: Warehouse lookup & connector caching
- `services/integration_router.py`: Integration lookup & credential decryption
- `connectors/snowflake.py`: Snowflake connection & query execution
- `connectors/netsuite.py`: NetSuite OAuth 1.0a connector with SuiteQL
- `services/snowflake_netsuite_loader.py`: NetSuite → Snowflake data sync
- `scheduler/jobs.py`: APScheduler job definitions
- `api/analytics.py`: Analytics endpoints (thin layer to warehouse)
- `parsers/pdf_extractor.py`: Rules-based PDF parser backup

---

### 4. Data Pipeline (Bronze → Silver → Gold)

**Bronze Layer (Raw Ingestion):**
- Table: `bronze.pms_day_sheets`
- Columns: id, practice_location, report_date, raw_data (VARIANT/JSON)
- Data source: PDF AI extraction or manual CSV import
- No transformations, minimal validation

**Silver Layer (Cleaned & Standardized):**
- Table: `bronze_silver.stg_pms_day_sheets` (PMS data)
- Table: `silver.stg_financials` (NetSuite data - dynamic table, auto-refresh)
- Columns: Typed columns (date, production DECIMAL, visits INT, etc.)
- dbt model: `models/silver/pms/stg_pms_day_sheets.sql`
- Transformations: Type casting, null handling, date parsing, outlier removal
- **Dynamic Tables**: Auto-refresh based on lag specification

**Gold Layer (Analytics-Ready):**
- Table: `bronze_gold.daily_production_metrics` (PMS metrics)
- Table: `gold.daily_financial_metrics` (NetSuite metrics - dynamic table)
- Columns: practice_location, report_date, total_production, collections, visits, kpis
- dbt model: `models/gold/metrics/daily_production_metrics.sql`
- Aggregations: Daily sums, ratios (production per visit, collection rate), running averages
- **Dynamic Tables**: Incremental materialization with automatic refresh

**dbt Project Structure:**
- `dbt_project.yml`: Config, model paths, vars
- `models/schema.yml`: Table docs, column descriptions
- `models/bronze/sources.yml`: Source definitions (Snowflake tables)
- Models materialized as tables (snapshots if needed for SCD Type 2)

**Transformation Flow:**
```
PDF AI Extract → POST /api/v1/pdf/upload
  ↓ (Inserted to bronze.pms_day_sheets)
→ POST /api/v1/dbt/run/pdf-pipeline
  ↓ (dbt runs transformations)
→ stg_pms_day_sheets (silver, cleaned)
→ daily_production_metrics (gold, aggregated)
  ↓ (Query in frontend)
→ Analytics Dashboard
```

**Key Files:**
- `dbt/dentalerp/dbt_project.yml`: Project config
- `dbt/dentalerp/models/bronze/sources.yml`: Source definitions
- `dbt/dentalerp/models/silver/pms/stg_pms_day_sheets.sql`: Staging model
- `dbt/dentalerp/models/gold/metrics/daily_production_metrics.sql`: Main KPI table
- `mcp-server/src/services/dbt_runner.py`: Subprocess dbt executor

**Note**: Most transformations now use Snowflake Dynamic Tables (TARGET_LAG auto-refresh) instead of dbt. dbt is still used for complex transformations when needed.

**Manual CSV Upload Flow**:
```
User uploads CSV → MCP API (/netsuite/upload or /operations/upload)
  ↓
MCP Parser (netsuite_csv_parser.py or operations_excel_parser.py)
  ↓
Snowflake BRONZE table (raw data with duplicate handling)
  ↓
Dynamic Tables auto-refresh (TARGET_LAG = 1 hour)
  ↓
SILVER layer (cleaned, typed)
  ↓
GOLD layer (analytics-ready, joined)
  ↓
MCP Analytics API queries GOLD
  ↓
Backend proxies to MCP
  ↓
Frontend displays in dashboard
```

---

## Database Migrations & Setup

### Backend (PostgreSQL - Dental ERP DB)

**Migration Files** (`backend/drizzle/`):
- `0000_strange_gravity.sql`: Initial schema (users, practices, locations, etc.)
- `0001_glamorous_sentry.sql`: Integrations, credentials
- `0002_day_sheet_pdf.sql`: PDF day sheet tracking
- `0003_add_user_avatar_column.sql`: User avatar
- `0004_queue_locking_and_auth_tokens.sql`: Token blacklist table
- `0005_unique_constraints_and_token_column_fix.sql`: Constraints

**Running Migrations:**
```bash
npm run db:migrate      # Apply pending migrations
npm run db:seed         # Seed with test data
npm run db:reset        # Drop and recreate
npm run db:generate     # Generate new migration file
```

### MCP Server (PostgreSQL - MCP DB)

**Migration Files** (`mcp-server/migrations/`):
- `001_create_tenant_tables.sql`: Tenants, warehouses, API keys
- `002_create_tenant_integrations.sql`: Tenant integrations & credentials
- `003_netsuite_sync_state.sql`: NetSuite sync state tracking

**Setup:**
```bash
# Alembic-style (or manual SQL execution)
python -m alembic upgrade head
```

### Snowflake (Data Warehouse)

**Schemas:**
- `BRONZE`: Raw ingested data (`pms_day_sheets`)
- `BRONZE_SILVER`: Cleaned staging tables (`stg_pms_day_sheets`)
- `BRONZE_GOLD`: Analytics-ready tables (`daily_production_metrics`)

**Setup:**
```sql
-- Run snowflake-setup-updated.sql in Snowflake UI
-- Creates databases, schemas, tables, sample data
```

---

## Integration Points Between Components

### Frontend ↔ Backend
- **Protocol**: REST + JSON
- **Auth**: JWT in `Authorization: Bearer <token>` header
- **Real-time**: Socket.IO for dashboard updates
- **Error handling**: Standardized JSON error responses
- **Proxy**: Dev server proxies `/api` to backend:3001

### Backend ↔ MCP Server
- **Protocol**: REST + JSON
- **Auth**: `Authorization: Bearer <MCP_API_KEY>` header
- **Tenant header**: `X-Tenant-ID` (if multi-tenant)
- **Examples**:
  - Fetch analytics: `GET /api/v1/analytics/production/daily`
  - Upload PDF: `POST /api/v1/pdf/upload`
  - Trigger dbt: `POST /api/v1/dbt/run/pdf-pipeline`

### MCP Server ↔ Snowflake
- **Protocol**: Python `snowflake-connector-python`
- **Auth**: Username/password or key-pair (environment variables)
- **Queries**: Direct SQL to Snowflake via connector
- **Routing**: `WarehouseRouter` handles tenant-specific config

### MCP Server ↔ External Integrations

**NetSuite ERP Integration** (Financial Data):
- **Connector**: `connectors/netsuite.py`
- **Auth**: OAuth 1.0a TBA with HMAC-SHA256
- **API**: REST Record API v1
- **Data**: Journal entries, accounts, invoices, payments, vendor bills, customers, vendors
- **Sync**: Every 15-30 min incremental + daily full refresh at 2am
- **Endpoints**:
  - `POST /api/v1/netsuite/sync/trigger` - Manual sync
  - `GET /api/v1/netsuite/sync/status` - Check progress
  - `POST /api/v1/netsuite/sync/test-connection` - Test connection
- **See**: `docs/NETSUITE_INTEGRATION_FINAL.md` for complete guide

**Other Integrations:**
- **Connectors**: `connectors/{adp, dentrix, etc.}.py`
- **Auth**: Encrypted credentials stored in `tenant_integrations` table
- **Routing**: `IntegrationRouter` selects correct connector per tenant

### Frontend ↔ MCP Server (Direct)
- **Path**: Some analytics calls bypass backend
- **Header**: `X-Tenant-ID` for multi-tenant awareness
- **Examples**: Real-time production metrics, warehouse status

---

## Production Testing

### Production Test Scripts

Three comprehensive test suites are available for production testing:

1. **Full System Test** (`test-production.sh`)
   - Tests all components: Frontend, Backend, MCP Server
   - Validates analytics endpoints
   - Checks warehouse connectivity
   - Verifies security headers and CORS

2. **Critical Flows Test** (`test-production-critical-flows.sh`)
   - User authentication and session management
   - Dashboard data loading (executive view)
   - PDF upload → AI extraction → dbt → analytics pipeline
   - Multi-tenant data isolation
   - Error handling and recovery
   - Performance and response times

3. **Connectors Test** (`test-production-connectors.sh`)
   - Snowflake warehouse connection
   - Tenant integrations status
   - Warehouse configuration
   - Products and capabilities
   - Data quality checks

### Running Production Tests

```bash
# Set environment variables
export MCP_API_KEY="your-production-key"
export BACKEND_TOKEN="your-jwt-token"  # Optional for backend tests
export TEST_EMAIL="test@dentalerp.demo"  # Optional for auth tests
export TEST_PASSWORD="password"  # Optional for auth tests

# Run all production tests
./scripts/test-production.sh
./scripts/test-production-critical-flows.sh
./scripts/test-production-connectors.sh
```

See [Production Testing Guide](tests/PRODUCTION_TESTING.md) for complete documentation.

---

## Important Conventions & Best Practices

### Naming Conventions
- **Branches**: `feat/feature-name`, `fix/bug-name`, `chore/task-name`
- **Commits**: "feat: add X", "fix: resolve Y", "chore: update Z"
- **Tables**: snake_case (PostgreSQL)
- **Columns**: snake_case
- **Functions**: camelCase (JavaScript), snake_case (Python)
- **Classes**: PascalCase
- **Constants**: UPPER_SNAKE_CASE

### Code Structure
- **One component per file** (React)
- **Services abstract APIs** (no direct axios in components)
- **Hooks for state logic** (custom React hooks for repeated patterns)
- **Middleware for cross-cutting concerns** (auth, logging, errors)
- **Models for data validation** (Zod in TypeScript, Pydantic in Python)

### Error Handling
- **Frontend**: Toast notifications + error logs
- **Backend**: AppError class with statusCode + message
- **MCP**: Custom exceptions that propagate as HTTP errors
- **Logging**: Winston (backend), Python logging (MCP)

### Security
- **Auth**: JWT tokens with 15m expiry + 7d refresh
- **Secrets**: Never commit `.env` files, use environment variables
- **DB**: Use ORM/parameterized queries (no string concatenation)
- **CORS**: Whitelist specific origins in production
- **Rate limiting**: 100 requests per 15 minutes per IP
- **Credentials**: Encrypt integration secrets before storing

### Performance
- **Frontend**: React Query caching, code splitting, lazy loading
- **Backend**: Connection pooling, Redis caching, indexed queries
- **MCP**: Connector caching per tenant, async/await throughout
- **Snowflake**: Pre-aggregated Gold layer, incremental dbt models

---

## Key Files to Understand System

**Frontend Entry Points:**
1. `frontend/src/App.tsx` - Routing & layout
2. `frontend/src/store/authStore.ts` - Auth state
3. `frontend/src/services/api.ts` - HTTP client
4. `frontend/src/pages/analytics/ProductionAnalyticsPage.tsx` - Main dashboard

**Backend Entry Points:**
1. `backend/src/server.ts` - Express setup
2. `backend/src/middleware/auth.ts` - Auth logic
3. `backend/src/services/mcpClient.ts` - MCP integration
4. `backend/src/routes/analytics.ts` - Analytics routes

**MCP Server Entry Points:**
1. `mcp-server/src/main.py` - FastAPI setup
2. `mcp-server/src/middleware/tenant_identifier.py` - Tenant detection
3. `mcp-server/src/services/warehouse_router.py` - Warehouse selection
4. `mcp-server/src/api/analytics.py` - Analytics endpoints

**Database:**
1. `backend/src/database/schema.ts` - Data models
2. `mcp-server/src/models/tenant.py` - Tenant models
3. `snowflake-setup-updated.sql` - Warehouse schema

---

## Common Development Tasks

### Add a New API Endpoint

1. **Backend**: Add route in `backend/src/routes/`
2. **Service**: Add business logic to `backend/src/services/`
3. **Frontend**: Add function to `frontend/src/services/api.ts`
4. **Hook**: Create React Query hook in `frontend/src/hooks/`
5. **Component**: Use hook in page component
6. **Test**: Add integration test in `scripts/`

### Add a New Practice

1. Update `backend/src/database/seed.ts` with new practice
2. Add sample data to `snowflake-setup-updated.sql`
3. Run `npm run db:seed`
4. Run `./scripts/test-complete-system.sh`

### Add External Integration

1. Create connector in `mcp-server/src/connectors/new_system.py`
2. Register in connector registry
3. Add credentials to `mcp-server/.env`
4. Create routes in `mcp-server/src/api/`
5. Update MCP client in backend if needed

### Debug Snowflake Issues

**If MCP returns "error 250001: Could not connect to Snowflake":**

1. **Check tenant_warehouses database table**:
   ```bash
   docker exec dental-erp_postgres_1 psql -U postgres -d mcp -c "SELECT warehouse_config->>'account', warehouse_config->>'user' FROM tenant_warehouses WHERE warehouse_type='snowflake';"
   ```
   - Should show real account/user, NOT "PLACEHOLDER"
   - If PLACEHOLDER: Update with real credentials (see ANALYTICS_FIX_COMPLETED.md)

2. **Check .env file password escaping**:
   ```bash
   docker exec dental-erp_mcp-server-prod_1 cat /app/.env | grep SNOWFLAKE_PASSWORD
   ```
   - Should be: `SNOWFLAKE_PASSWORD=@SebaSofi.2k25!!`
   - NOT: `SNOWFLAKE_PASSWORD=@SebaSofi.2k25\!\!` (backslashes break connection)

3. **Verify deploy.sh exports Snowflake variables**:
   - Check line ~68 in deploy.sh for: `export SNOWFLAKE_ACCOUNT SNOWFLAKE_USER SNOWFLAKE_PASSWORD`
   - Without this, docker-compose won't receive the credentials

4. **Test connection from MCP container**:
   ```bash
   docker exec dental-erp_mcp-server-prod_1 python3 -c "import snowflake.connector, os; from dotenv import load_dotenv; load_dotenv(); c=snowflake.connector.connect(account=os.getenv('SNOWFLAKE_ACCOUNT'), user=os.getenv('SNOWFLAKE_USER'), password=os.getenv('SNOWFLAKE_PASSWORD'), warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'), database=os.getenv('SNOWFLAKE_DATABASE')); print('✅ Connected')"
   ```

**If gold.practice_analytics_unified has NULL values:**

1. Check if it's a circular reference issue (VIEW reading from dynamic table that reads from VIEW)
2. Verify dynamic table lag is >= source table lag
3. Force refresh: `ALTER DYNAMIC TABLE gold.practice_analytics_unified REFRESH`

**General Snowflake debugging:**

1. Test connection: Check environment variables
2. Check schema: `SELECT * FROM information_schema.tables`
3. Check sample data: `SELECT * FROM bronze.pms_day_sheets LIMIT 10`
4. Check dbt: `cd dbt/dentalerp && dbt debug`

### Load Demo Data for Client Presentations

1. Prepare CSV exports from source systems (NetSuite, PMS)
2. Parse CSV to Bronze format: `python scripts/python/load_csv_to_snowflake.py`
3. Load into Snowflake: `./scripts/insert_demo_data.sh`
4. Verify data in Bronze layer
5. Check dynamic tables auto-refreshed Silver/Gold layers
6. Test analytics API endpoints
7. Verify frontend dashboard displays data

### Debug NetSuite Integration Issues

1. **Check SuiteQL query syntax**: NetSuite has specific requirements
   - Use URL parameters for `LIMIT` and `OFFSET` (not in SQL)
   - Avoid `ORDER BY` on joined fields
   - Check table name pluralization (transaction vs transactions)
2. **Verify date filters**: Ensure date ranges don't exclude all data
3. **Check transaction type filters**: Some filters may exclude valid records
4. **Test with minimal query**: Start simple, add filters incrementally
5. **Review NetSuite API logs**: Check actual API responses
6. **Fallback to CSV**: For demos, CSV ingestion is reliable alternative

---

## Architecture Decision Records (ADRs)

### Multi-Tenant via Context Variables
**Why**: Thread-safe, async-safe request-scoped storage without thread-locals or thread pools.

### Zendesktop → MCP Server
**Why**: Single integration point; easier to add new systems without backend changes; independent scaling.

### Bronze-Silver-Gold dbt
**Why**: Clear data quality tiers; auditable transformations; business logic separate from ETL.

### Zustand over Redux/Recoil
**Why**: Minimal boilerplate; good performance; native TypeScript; easy persistence.

### Snowflake Dynamic Tables for Silver/Gold
**Why**: Auto-refresh eliminates need for manual dbt scheduling; built-in incremental updates; declarative lag specification; better performance than views.

---

## Production Deployment

**Domains:**
- Frontend: https://dentalerp.agentprovision.com
- MCP Server: https://mcp.agentprovision.com

**Deploy Script:**
```bash
# On GCP VM (IMPORTANT: run git commands as nomade user)
gcloud compute ssh dental-erp-vm --zone=us-central1-a
cd /opt/dental-erp

# Pull latest code (must run as nomade, not root)
sudo -u nomade git pull origin main

# Deploy with Snowflake credentials
export SNOWFLAKE_ACCOUNT='HKTPGHW-ES87244'
export SNOWFLAKE_USER='NOMADSIMON'
export SNOWFLAKE_PASSWORD='@SebaSofi.2k25!!'
export SNOWFLAKE_WAREHOUSE='COMPUTE_WH'
export SNOWFLAKE_DATABASE='DENTAL_ERP_DW'
export SNOWFLAKE_SCHEMA='BRONZE'
export SNOWFLAKE_ROLE='ACCOUNTADMIN'
export MCP_API_KEY='d876e6163089364d96a45a80ed576e99fc55b306133e258d9f861007e824b456'
export MCP_SECRET_KEY='production-secret-key-for-jwt-signing-min-32-characters-secure'

sudo -E bash deploy.sh
```

**IMPORTANT**:
- The `/opt/dental-erp` directory is owned by `nomade` user
- Git commands MUST run as `nomade`: `sudo -u nomade git pull`
- Deploy script runs as root with `-E` flag to preserve environment variables

**CI/CD:**
- GitHub Actions in `.github/workflows/`
- Auto-test on PR
- Auto-deploy to prod on merge to `main`

**Monitoring:**
- Application logs via `docker-compose.monitoring.yml`
- Snowflake cost monitoring in dbt
- Health checks at `/health` endpoints

---

## NetSuite Integration

**Current Status**: Fully implemented and operational

**Connector**: `mcp-server/src/connectors/netsuite.py` (OAuth 1.0a Token-Based Authentication)

**Data Synced**:
- Journal Entries
- Accounts (Chart of Accounts)
- Invoices & Payments
- Vendor Bills
- Customers & Vendors

**Sync Schedule**:
- Incremental sync: Every 15-30 minutes
- Full refresh: Daily at 2am

**Manual Sync**:
```bash
# Trigger full sync
curl -X POST https://mcp.agentprovision.com/api/v1/netsuite/sync/trigger \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: default" \
  -d '{"full_sync": true}'

# Check sync status
curl https://mcp.agentprovision.com/api/v1/netsuite/sync/status \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: default"
```

**Credentials Setup**: See `docs/NETSUITE_INTEGRATION_FINAL.md`

**Known Issues & Workarounds**:
- SuiteQL may return 0 records depending on query structure
- CSV ingestion (`./scripts/insert_demo_data.sh`) is reliable fallback
- APScheduler automation handles retries and error recovery
- See `SESSION_COMPLETE_HANDOFF.md` for recent debugging context

---

## Recent Session Context

**Latest Work** (November 2025):
- Fixed analytics dashboard 500 errors (Snowflake connection issues)
- Updated deploy.sh to properly export Snowflake environment variables
- Fixed tenant_warehouses database table with correct Snowflake credentials
- Recreated gold.practice_analytics_unified dynamic table (was broken by circular reference)
- Organized documentation files (moved 22 old docs to archive)

**Previous Work** (November 2024):
- Fixed 6 NetSuite integration bugs (SuiteQL syntax, date filters, type filters)
- Built APScheduler automation (daily sync, incremental updates)
- Created CSV demo data pipeline for client presentations

**Critical Files for Recent Changes**:
- `docs/sessions/2025-11-23-session-complete.md` - Complete session summary
- `docs/archive/2025-11-22-analytics-fix/` - Archived troubleshooting documents
- `mcp-server/src/api/netsuite_upload.py` - NetSuite CSV manual upload
- `mcp-server/src/services/netsuite_csv_parser.py` - NetSuite CSV parser
- `scripts/test-manual-ingestion.sh` - Test manual uploads

---

## Documentation Structure

The project documentation has been organized into the following structure:

```
docs/
├── api/                  # MCP Server API documentation
├── architecture/         # System architecture and technical specs
├── archive/             # Historical docs, session handoffs, milestones
├── deployment/          # Deployment guides and procedures
├── development/         # Debug notes, root cause analyses
├── frontend/            # Frontend-specific documentation
├── guides/              # How-to guides and tutorials
├── images/              # Documentation images and diagrams
├── netsuite/            # NetSuite integration documentation
├── plans/               # Implementation plans
└── testing/             # Testing documentation (empty, see tests/)

tests/
├── e2e/                 # End-to-end test documentation
├── integration/         # Integration test code
└── *.md                 # Test guides and results
```

**Key Documentation**:
- Main README: `README.md` - Project overview and quick start
- AI Assistant: `CLAUDE.md` - This file
- Demo Guide: `STAKEHOLDER_DEMO_GUIDE.md` - Client demo preparation
- NetSuite Integration: `docs/netsuite/NETSUITE_INTEGRATION_FINAL.md`
- Testing Guide: `tests/PRODUCTION_TESTING.md`
- Deployment: `docs/deployment/DEPLOYMENT.md`

---

**Last Updated**: November 2024
**Maintainer**: DentalERP Team
**Questions**: See `docs/` for guides, or check GitHub Issues