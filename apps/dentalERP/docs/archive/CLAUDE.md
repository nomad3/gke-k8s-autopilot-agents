# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dental Practice Rollup Mini ERP - A **multi-tenant, multi-product** SaaS platform for dental practice management with enterprise-grade data isolation. Built for dental practice roll-ups acquiring multiple locations, enabling centralized financial, operational, and production analytics across all practices.

**Architecture**: Multi-tenant SaaS with triple-redundant security (middleware, application, database row-level policies)

**Products**:
- **DentalERP**: Core dental practice management (production tracking, financial analytics, PMS integration)
- **AgentProvision**: AI agent platform (extensible for additional products)

**Production URLs:**
- Frontend & API: https://dentalerp.agentprovision.com
- MCP Integration Hub: https://mcp.agentprovision.com
- Tenant Subdomains: `{tenant}.dentalerp.agentprovision.com` (e.g., `silvercreek.dentalerp.agentprovision.com`)

**Client**: Silvercreek Dental Practice (~15 locations, $40k MVP + $190/location/month)

## Development Commands

### Full Stack Development

```bash
# Start all services (PostgreSQL, Redis, MCP Server, Backend, Frontend)
docker-compose up

# Start specific services
docker-compose up postgres redis mcp-server -d  # Infrastructure only
docker-compose up backend                        # Backend + deps
docker-compose up frontend                       # Frontend only

# View logs
docker-compose logs -f [service-name]

# Stop all services
docker-compose down

# Rebuild containers after dependency changes
docker-compose up --build [service-name]
```

### Backend (Node.js + TypeScript + Express)

```bash
cd backend

# Development
npm install
npm run dev              # Hot-reload development server

# Database Management (Drizzle ORM)
npm run db:generate      # Generate migration from schema changes
npm run db:push          # Push schema to database
npm run db:migrate       # Run migrations
npm run db:seed          # Seed development data
npm run db:reset         # Reset database

# Testing
npm test                 # Run Jest tests
npm run test:watch       # Watch mode
npm run test:coverage    # Coverage report

# Code Quality
npm run lint             # ESLint
npm run lint:fix         # Auto-fix issues
npm run type-check       # TypeScript check without build
npm run build            # Production build
```

### Frontend (React 18 + TypeScript + Vite)

```bash
cd frontend

# Development
npm install
npm run dev              # Vite dev server with HMR

# Testing
npm run test             # Vitest unit tests
npm run test:ui          # Vitest UI
npm run test:coverage    # Coverage report
npm run test:e2e         # Playwright E2E tests
npm run test:e2e:ui      # Playwright UI mode

# Code Quality
npm run lint             # ESLint
npm run lint:fix         # Auto-fix issues
npm run type-check       # TypeScript check
npm run format           # Prettier format
npm run build            # Production build
npm run preview          # Preview production build

# Storybook (Component Library)
npm run storybook        # Start Storybook dev server
npm run build-storybook  # Build static Storybook
```

### MCP Server (Python + FastAPI)

```bash
cd mcp-server

# Setup
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt  # Includes snowflake-connector-python

# Development
uvicorn src.main:app --reload --host 0.0.0.0 --port 8085

# Testing
pytest
pytest --cov=src --cov-report=html

# API Documentation (auto-generated)
# Visit http://localhost:8085/docs when server is running

# Snowflake Connection Test
python -c "from src.connectors.snowflake import get_snowflake_connector; import asyncio; connector = get_snowflake_connector(); print('✅ Connected' if asyncio.run(connector.test_connection()) else '❌ Failed')"
```

### Testing & Utilities

```bash
# Test all service URLs
./test-setup.sh

# Run comprehensive test suite
./run-all-tests.sh

# Manual data ingestion demo
./scripts/ingestion-demo.sh

# Check MCP Server status
./check-mcp-status.sh

# Debug MCP Server
./debug-mcp.sh
```

## Architecture

### Multi-Tenant Architecture (🆕 Phase 4 Complete)

The system is a **multi-tenant, multi-product SaaS platform** with enterprise-grade data isolation:

```
Tenant Request → Middleware (Identify Tenant) → Application (Filter by tenant_id) → Snowflake (Row Access Policies)
                       ↓                              ↓                                        ↓
               TenantContext Set                tenant_id in queries                  Database-level isolation
```

**Tenant Identification** (3 methods, priority order):
1. **Subdomain**: `silvercreek.dentalerp.com` → tenant_code='silvercreek' (production)
2. **X-Tenant-ID header**: `X-Tenant-ID: silvercreek` (development/testing)
3. **API key prefix**: `Bearer silvercreek_sk_abc123...` → tenant_code='silvercreek' (service-to-service)

**Triple-Redundant Security**:
- **Layer 1**: Middleware (`tenant_identifier.py`) blocks requests without valid tenant
- **Layer 2**: Application enforces `WHERE tenant_id = '{code}'` in all queries
- **Layer 3**: Snowflake row access policies prevent unauthorized data access (database-level)

**Key Files**:
- `mcp-server/src/middleware/tenant_identifier.py`: Tenant identification & context setting
- `mcp-server/src/core/tenant.py`: Thread-safe tenant context (Python contextvars)
- `mcp-server/src/models/tenant.py`: Tenant, TenantWarehouse, TenantProduct models
- `mcp-server/src/services/tenant_service.py`: Tenant CRUD operations
- `mcp-server/src/services/product_registry.py`: Multi-product support (DentalERP, AgentProvision)
- `snowflake-multi-tenant-migration.sql`: Database row access policies (410 lines, ready to execute)

**Test Suite**: `test-multi-tenant-e2e.sh` (17 tests, 15/17 passing)

### Microservices Architecture

The system uses a **three-tier microservices architecture** with the MCP Server as the integration hub:

```
Frontend (React/TS) → ERP Backend (Node.js/TS) → MCP Server (FastAPI/Python) → External APIs
                             ↓                            ↓
                      PostgreSQL (ERP Data)        PostgreSQL (MCP Data) + Snowflake
                             ↓                            ↓
                         Redis Cache                  Redis Cache
```

**Key principle**: The ERP backend NEVER directly connects to external systems (ADP, NetSuite, DentalIntel, Eaglesoft, Dentrix, Snowflake). All integration logic is handled by the MCP Server.

### Backend Architecture (`backend/src/`)

```
backend/src/
├── server.ts           # Express + Socket.io server bootstrap
├── config/             # Environment configuration
├── database/           # Drizzle ORM schema, migrations, seed
│   ├── schema.ts       # Database schema definitions
│   ├── migrate.ts      # Migration runner
│   ├── seed.ts         # Development seed data
│   └── ensure.ts       # Auto-ensure tables on startup
├── routes/             # Express route handlers (REST APIs)
│   ├── auth.ts         # Public auth endpoints (login, refresh)
│   ├── dashboard.ts    # Role-based dashboard data
│   ├── analytics.ts    # BI analytics endpoints
│   ├── integrations.ts # Integration status & manual ingestion
│   ├── practices.ts    # Practice management
│   ├── patients.ts     # Patient data
│   ├── appointments.ts # Appointment scheduling
│   ├── users.ts        # User management
│   ├── widgets.ts      # Dashboard widget configuration
│   └── reports.ts      # Report generation
├── services/           # Business logic layer
│   ├── auth.ts         # JWT auth & refresh tokens
│   ├── database.ts     # Database connection & query helpers
│   ├── mcpClient.ts    # MCP Server API client (CRITICAL)
│   └── analytics.ts    # Analytics aggregation
├── middleware/         # Express middleware
│   ├── auth.ts         # JWT verification
│   ├── audit.ts        # Audit logging
│   └── errorHandler.ts # Global error handling
├── utils/              # Utilities
│   ├── logger.ts       # Winston logger
│   ├── errors.ts       # Custom error classes
│   └── validation.ts   # Joi/Zod validation helpers
└── workers/            # Background workers (Temporal.io ready)
```

**IMPORTANT**: When making changes to integrations, ALWAYS work through the `mcpClient.ts` service. Never attempt to create direct connections to external APIs.

### Frontend Architecture (`frontend/src/`)

```
frontend/src/
├── main.tsx            # Application entry point
├── App.tsx             # Root component with routing
├── components/         # Reusable UI components
│   ├── ui/             # Base UI primitives (buttons, inputs, etc.)
│   ├── dashboard/      # Dashboard-specific components
│   └── analytics/      # Analytics visualizations
├── pages/              # Route components
│   ├── auth/           # Login, register
│   ├── dashboard/      # Role-based dashboards (executive, manager, clinician, staff)
│   ├── analytics/      # BI analytics deep-dives
│   ├── patients/       # Patient management
│   ├── appointments/   # Scheduling
│   └── integrations/   # Integration management & manual ingestion
├── layouts/            # Layout wrappers
│   ├── AuthLayout.tsx  # Public pages layout
│   └── DashboardLayout.tsx # Authenticated app layout
├── store/              # Zustand state management
│   ├── authStore.ts    # Auth state & tokens
│   └── dashboardStore.ts # Dashboard preferences
├── hooks/              # Custom React hooks
│   ├── useAuth.ts      # Authentication hook
│   ├── useWebSocket.ts # Socket.io connection
│   └── useQuery.ts     # React Query wrappers
├── services/           # API service layer
│   ├── api.ts          # Axios instance with interceptors
│   └── auth.ts         # Auth API calls
└── types/              # TypeScript type definitions
```

**Design System**: Follow the healthcare-focused design system in `/design-system/` with Inter + Lexend fonts, professional blue color palette, and WCAG 2.1 AA accessibility compliance.

### MCP Server Architecture (`mcp-server/src/`)

```
mcp-server/src/
├── main.py             # FastAPI application & startup
├── api/                # REST API endpoints (v1)
│   ├── health.py       # Health checks
│   ├── mappings.py     # Entity ID mapping registration
│   ├── integrations.py # Integration status & sync orchestration
│   ├── data.py         # Data access (finance, production, forecasts)
│   └── warehouse.py    # Snowflake warehouse management (NEW)
├── core/               # Core configuration
│   ├── config.py       # Settings (loads from env vars)
│   ├── database.py     # SQLAlchemy session management
│   └── security.py     # API key authentication
├── models/             # SQLAlchemy database models
│   └── mapping.py      # Mapping, IntegrationStatus, SyncJob models
├── connectors/         # External API connectors
│   ├── base.py         # Base connector with retry logic
│   ├── registry.py     # Connector registry
│   ├── adp.py          # ADP payroll API
│   ├── netsuite.py     # NetSuite financial API
│   ├── dentalintel.py  # DentalIntel analytics API
│   ├── eaglesoft.py    # Eaglesoft PMS API
│   ├── dentrix.py      # Dentrix PMS API
│   └── snowflake.py    # Snowflake data warehouse connector (PRODUCTION-READY)
├── services/           # Business logic for MCP
│   ├── sync_orchestrator.py  # Data sync orchestration (Extract + Load)
│   ├── snowflake.py    # Snowflake service (high-level queries)
│   ├── forecasting.py  # Forecasting service
│   ├── alerts.py       # Alert service
│   └── schema_mapper.py # Schema mapping utilities
└── utils/              # Utilities
    ├── logger.py       # Loguru logger
    ├── cache.py        # Redis caching decorators
    └── retry.py        # Retry logic & circuit breaker
```

**Authentication**: All MCP API endpoints (except `/health`) require `Authorization: Bearer <MCP_API_KEY>` header.

**Snowflake Integration**: The MCP Server now includes full Snowflake data warehouse capabilities. See `mcp-server/SNOWFLAKE_ORCHESTRATION.md` for complete guide.

### Database Schema (`backend/src/database/schema.ts`)

Key tables using Drizzle ORM:
- **users**: User accounts with role-based access (executive, manager, clinician, staff)
- **practices**: Top-level practice organizations
- **locations**: Physical practice locations (linked to PMS systems)
- **patients**: Patient records (ingested from PMS or manual upload)
- **appointments**: Scheduling data
- **integrations**: Integration configuration & credentials (deprecated - migrated to MCP)
- **ingestion_jobs**: Manual CSV/PDF upload jobs
- **ingestion_staging**: Staged records before promotion to domain tables
- **audit_logs**: HIPAA-compliant audit trail

**Note**: The database schema includes ingestion enums/tables that are auto-ensured on backend startup. Manual migration is only needed for structural changes.

## Snowflake Data Warehouse Architecture

**CRITICAL PRINCIPLE**: Snowflake does ALL the heavy lifting. MCP Server is a thin orchestration layer.

### Bronze → Silver → Gold Pattern

```
External APIs → MCP (Extract) → Snowflake Bronze (Raw JSON)
                                       ↓
                                  dbt Transforms
                                       ↓
                                Snowflake Silver (Cleaned)
                                       ↓
                                  dbt Aggregates
                                       ↓
                                Snowflake Gold (KPIs)
                                       ↓
                            MCP Queries (< 200ms) → ERP → Frontend
```

### MCP Server Responsibilities (Thin Layer)

✅ **DO**:
- Extract raw data from external APIs
- Load raw JSON to Snowflake Bronze tables (bulk insert)
- Query pre-computed Gold layer tables
- Cache results in Redis (5 min TTL)

❌ **DON'T**:
- Transform data (that's dbt's job in Snowflake)
- Aggregate data (that's Snowflake SQL's job)
- Calculate KPIs (that's dbt models' job)

### Snowflake + dbt Responsibilities (Heavy Lifting)

✅ **ALL** data transformations, aggregations, and calculations happen in Snowflake using dbt:
- Deduplication with window functions
- Type casting and validation
- SUM(), AVG(), COUNT() aggregations
- Complex joins across fact and dimension tables
- MoM/YoY growth calculations
- Data quality tests

### Example Data Flow

```python
# 1. MCP extracts from NetSuite API (lightweight)
response = await netsuite_connector.fetch_data("journalentry")

# 2. MCP loads RAW JSON to Bronze (no transformation)
await snowflake_connector.bulk_insert_bronze(
    table_name="bronze.netsuite_journalentry",
    records=[{"raw_data": record, "extracted_at": now()}]
)

# 3. dbt transforms Bronze → Silver → Gold (in Snowflake)
# Run: dbt run --select stg_financials monthly_production_kpis

# 4. MCP queries pre-computed Gold table (fast)
results = await snowflake_service.get_financial_summary("downtown")
# Returns: revenue, expenses, MoM growth (all pre-computed)
```

### Key Snowflake APIs

```bash
# Warehouse Management
GET  /api/v1/warehouse/status          # Connection & layer status
GET  /api/v1/warehouse/bronze/status   # Bronze layer data freshness
GET  /api/v1/warehouse/freshness       # Check stale data
POST /api/v1/warehouse/dbt/run         # Trigger dbt transformations

# Data Sync (Extract & Load)
POST /api/v1/sync/run                  # Trigger data sync to Bronze
GET  /api/v1/sync/{sync_id}            # Check sync status

# Analytics (Query Gold)
GET  /api/v1/finance/summary           # Pre-computed financial KPIs
GET  /api/v1/production/metrics        # Pre-computed production metrics
GET  /api/v1/forecast/{location}       # ML forecasts from Snowflake
```

For complete Snowflake orchestration guide, see: `mcp-server/SNOWFLAKE_ORCHESTRATION.md`

---

## Key Workflows

### Authentication Flow

1. User logs in via `POST /api/auth/login` (email + password)
2. Backend validates credentials, returns short-lived access token (15min) + refresh token (7d)
3. Access token stored in memory/state, refresh token in httpOnly cookie
4. Frontend includes `Authorization: Bearer <token>` on all protected requests
5. On 401, frontend automatically refreshes via `POST /api/auth/refresh` with refresh token
6. Tokens stored in Redis with practice/role claims for fast lookup

### Integration Data Flow (MCP Architecture)

1. **Frontend** requests integration data (e.g., financial summary)
2. **ERP Backend** receives request at `/api/analytics/...`
3. **Backend** calls `mcpClient.getFinancialSummary(...)` (never direct API calls)
4. **MCP Server** orchestrates external API calls (ADP, NetSuite, etc.)
5. **MCP Server** maps external IDs to ERP IDs using `mappings` table
6. **MCP Server** returns transformed data to ERP Backend
7. **ERP Backend** returns data to Frontend

**CRITICAL**: Always use `mcpClient` service for integration data. Direct external API calls are prohibited.

### Manual Data Ingestion Flow (CSV/PDF Upload)

When API integrations aren't configured, users can manually upload files:

1. Upload file via `POST /api/integrations/ingestion/upload` (practiceId, sourceSystem, dataset, file)
2. Process file via `POST /api/integrations/ingestion/jobs/:id/process` (parses CSV/PDF, stages records)
3. Get headers via `GET /api/integrations/ingestion/jobs/:id/headers` (for field mapping UI)
4. Map fields via `POST /api/integrations/ingestion/jobs/:id/map` (save sourceSystem → target field mapping)
5. Promote via `POST /api/integrations/ingestion/jobs/:id/promote` (target: patients|appointments)

**Supported formats**: CSV, PDF, JSON, TXT
**Example files**: `examples/ingestion/` (Torrey Pines Dentrix, Eastlake Eaglesoft samples)
**Frontend UI**: `/integrations/ingestion`

## Environment Variables

### ERP Backend Required Variables

```bash
# Core
NODE_ENV=development|production
PORT=3001

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Auth (JWT)
JWT_SECRET=your-secret-32-chars-minimum
JWT_REFRESH_SECRET=your-refresh-secret-32-chars-minimum
JWT_EXPIRES_IN=15m
JWT_REFRESH_EXPIRES_IN=7d

# MCP Integration (CRITICAL)
MCP_API_URL=http://mcp-server:8085
MCP_API_KEY=your-mcp-api-key-32-chars-minimum

# Cache
REDIS_URL=redis://redis:6379

# CORS
FRONTEND_URL=http://localhost:3000,https://dentalerp.agentprovision.com

# Features
MOCK_INTEGRATIONS=true|false
ENABLE_AUDIT_LOGGING=true
```

### MCP Server Required Variables

```bash
# Server
HOST=0.0.0.0
PORT=8085
ENVIRONMENT=development|production

# Security
MCP_API_KEY=same-as-erp-backend-mcp-api-key
SECRET_KEY=your-secret-key-for-internal-jwt

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=mcp
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Cache
REDIS_HOST=redis
REDIS_PORT=6379

# External Integration Credentials (managed by MCP)
# ADP_CLIENT_ID=...
# NETSUITE_ACCOUNT=...
# (20+ more integration credentials)
```

**Note**: See `backend/.env.example` and `mcp-server/.env.example` for complete lists.

## Common Development Tasks

### Adding a New API Endpoint

1. Define route in appropriate file under `backend/src/routes/`
2. Add authentication middleware if protected: `router.get('/path', authenticateJWT, handler)`
3. Implement handler with request validation (Joi/Zod)
4. Add service layer logic in `backend/src/services/`
5. Update API types in `frontend/src/types/`
6. Create frontend service method in `frontend/src/services/api.ts`

### Adding a New Integration (via MCP)

**IMPORTANT**: Never add integration connectors to the ERP backend. All integrations go through MCP Server.

1. Add credentials to `mcp-server/.env`
2. Add config fields to `mcp-server/src/core/config.py`
3. Create connector in `mcp-server/src/connectors/new_integration.py`
4. Register integration type in `mcp-server/src/models/mapping.py` (IntegrationTypeEnum)
5. Add sync logic to `mcp-server/src/services/sync.py`
6. No changes needed in ERP backend (it uses `mcpClient`)

### Modifying Database Schema

1. Edit `backend/src/database/schema.ts` (Drizzle ORM)
2. Generate migration: `npm run db:generate`
3. Review generated migration in `backend/drizzle/`
4. Apply migration: `npm run db:migrate` or `npm run db:push` (dev)
5. Update seed data if needed: `backend/src/database/seed.ts`

### Debugging Production Issues

```bash
# Check service health
curl https://dentalerp.agentprovision.com/api/health
curl https://mcp.agentprovision.com/health

# View logs (Docker)
docker-compose logs -f backend
docker-compose logs -f mcp-server

# Test MCP connectivity from backend
docker exec dental-erp_backend_1 curl http://mcp-server:8085/health

# Check database
docker exec dental-erp_postgres_1 psql -U postgres -d dental_erp_dev -c "SELECT COUNT(*) FROM users;"

# Check Redis
docker exec dental-erp_redis_1 redis-cli ping
```

## Role-Based Dashboards

The system has four distinct user roles with different dashboard layouts:

1. **Executive**: Strategic KPIs, multi-location performance matrix, revenue analytics (4 KPI widgets + 2x2 charts)
2. **Manager**: Daily operations, staff coordination, patient flow, real-time schedule timeline (3x1 overview + 2x2 schedule + 1x2 queue)
3. **Clinician**: Patient care focus, treatment tracking, clinical workflows, direct Dentrix/Eaglesoft access
4. **Staff**: Simplified interface for essential tasks, patient check-in, appointment viewing

Wireframes and specifications available in `/wireframes/` and `/design-system/`.

## Manual Ingestion (CSV/PDF)

For practices without API integrations, the system supports manual data uploads:

- **Upload directory**: `backend/uploads/` (configurable via `INGESTION_UPLOAD_DIR`)
- **Supported formats**: CSV, PDF, JSON, TXT (up to 50MB)
- **Workflow**: Upload → Process (auto-parse) → Map (field mapping) → Promote (to patients/appointments)
- **Example files**: `examples/ingestion/` (Torrey Pines Dentrix, Eastlake Eaglesoft)
- **Frontend**: `/integrations/ingestion`
- **Endpoints**: `/api/integrations/ingestion/*` (see README.md for full list)

**Note**: Backend auto-ensures ingestion tables on startup. Manual `db:generate` + `db:push` only needed for fresh remote databases.

## PMS Practice Mapping

- **Torrey Pines**: Dentrix v23.4.4.11088 (latest v25.12)
- **Eastlake**: Eaglesoft v21.00.18 (latest v24.20)

PMS database architecture is largely stable across versions for raw data ingestion. Some offices may need hardware upgrades for latest releases.

## Testing Strategy

### Backend Testing
- **Unit tests**: Jest with supertest for API endpoints
- **Test location**: `backend/src/**/*.test.ts`
- **Coverage**: Run `npm run test:coverage` (target: 80%+)

### Frontend Testing
- **Unit/Integration**: Vitest + Testing Library
- **E2E**: Playwright (multi-browser)
- **Visual**: Storybook for component library
- **Test location**: `frontend/src/**/*.test.tsx` and `frontend/tests/`

### Integration Testing
- Ensure all services running: `docker-compose up`
- Run test scripts: `./test-setup.sh`, `./run-all-tests.sh`
- Manual API testing: Use examples in README.md

## Production Deployment

**Primary deployment**: Google Cloud VM with Docker Compose + Caddy reverse proxy

```bash
# Deploy script (includes MCP + ERP)
./deploy.sh

# Deploy MCP Server first (always)
cd mcp-server && docker-compose --profile production up -d mcp-server-prod

# Deploy ERP Backend
cd backend && docker-compose --profile production up -d backend-prod

# Deploy Frontend
cd frontend && docker-compose --profile production up -d frontend-prod
```

**Important**: MCP Server MUST be deployed and healthy before deploying ERP Backend.

See `/documentation/MCP_DEPLOYMENT_GUIDE.md` and `/documentation/DEPLOYMENT_GCP_VM.md` for full instructions.

## Documentation Resources

- **README.md**: Comprehensive project overview, quickstart, architecture
- **CLAUDE.md**: This file - development guide for Claude Code
- **backend/MCP_MIGRATION.md**: Detailed MCP migration guide (completed Oct 2025)
- **mcp-server/README.md**: MCP Server complete guide
- **mcp-server/SNOWFLAKE_ORCHESTRATION.md**: ❄️ **NEW** - Complete Snowflake data warehouse orchestration guide
- **documentation/MCP_REFACTOR_SUMMARY.md**: MCP architecture benefits & implementation
- **documentation/DATA_PROCESSING_ARCHITECTURE.md**: Snowflake-centric processing patterns
- **documentation/SNOWFLAKE_ARCHITECTURE_SUMMARY.md**: Why Snowflake does the heavy lifting
- **documentation/snowflake_netsuite_schema.md**: Bronze/Silver/Gold schema design
- **documentation/technical-specification.md**: Full technical spec
- **documentation/manual-ingestion.md**: Manual CSV/PDF ingestion guide
- **documentation/BI_FEATURES_COMPLETE.md**: BI analytics features
- **design-system/**: Complete UI/UX design tokens, components, patterns
- **wireframes/**: High-fidelity dashboard layouts

## Git Workflow

- **Main branch**: `main` (production-ready code)
- **Commit style**: Conventional Commits (feat:, fix:, docs:, refactor:, test:)
- **Pre-commit hooks**: ESLint + Prettier (configured via husky + lint-staged)

## Key Constraints & Principles

1. **NEVER** add integration connectors to ERP backend - use MCP Server
2. **ALWAYS** use `mcpClient.ts` service for external data access
3. **FOLLOW** the healthcare design system (WCAG 2.1 AA compliance)
4. **MAINTAIN** HIPAA-conscious data handling (no PHI in logs, field-level encryption where applicable)
5. **TEST** authentication flows thoroughly (JWT + refresh tokens are critical)
6. **RESPECT** role-based access control (executive, manager, clinician, staff)
7. **LOG** all integration access via MCP audit trail
8. **USE** TypeScript strictly (no `any` types without justification)

## Quick Reference Links

- **API Docs (MCP)**: https://mcp.agentprovision.com/docs (FastAPI auto-generated)
- **Frontend Dev**: http://localhost:3000
- **Backend API**: http://localhost:3001/health
- **MCP Server**: http://localhost:8085/health
- **pgAdmin**: http://localhost:8080 (when running with `--profile tools`)
- **Storybook**: http://localhost:6006 (when running `npm run storybook`)
