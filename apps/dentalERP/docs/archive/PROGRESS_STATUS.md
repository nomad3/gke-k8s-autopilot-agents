# Silvercreek Dental ERP MVP – Progress Tracker

## 🔍 Current Alignment vs Proposal

| Area | Proposal Commitment | Current Implementation Snapshot | Status |
| --- | --- | --- | --- |
| **Data Integration (AI-Powered)** | Connect ADP, NetSuite, DentalIntel, Dentrix/Eaglesoft exports via AI-generated ETL, automate schema mapping/cleaning. | `backend/src/services/integrationConnectors.ts` & `backend/src/services/ingestionQueue.ts` add JSON API connectors + Redis-backed queue. MCP orchestration (`backend/src/services/temporal.ts`, `src/workflows/*`, `src/workers/integrationWorker.ts`) now drives `/api/integrations/ingestion/api/enqueue` when enabled, scheduling jobs via MCP server (`docker-compose.yml` MCP services). Schema inference helper (`IngestionService.suggestMapping`) recommends field maps. | ⏳ Partial (queue + MCP orchestration + mapping hints) |
| **Data Warehouse & Modeling** | Bronze-Silver-Gold warehouse, AI-assisted dbt models for KPI/variance/MoM. | PostgreSQL schema (`backend/src/database/schema.ts`) includes BI metrics tables, ingestion staging, but **no dbt project, Bronze/Silver/Gold layering, or AI modeling**. | ⚠️ Missing |
| **Analytics Dashboards** | Real-time MoM production & collections, AI insights summarization. | Backend analytics endpoints (`backend/src/routes/analytics.ts`) and services (`backend/src/services/analytics.ts`) provide mocked KPI/forecasting data, some aggregation using Drizzle. Frontend pages under `frontend/src/pages/analytics/` largely placeholders with static content (e.g., `ForecastingPage.tsx`). | ⏳ Partial (mocked data + placeholders) |
| **Forecasting Module** | AI models for revenue/cost projections. | `backend/src/services/analytics.ts#getForecasting()` performs basic historical comparison using DB data; no AI models. Frontend forecasting view placeholder. | ⏳ Partial (basic calc, no AI) |
| **Variance Detection & Anomaly Alerts** | Automated alerting for financial KPIs. | No dedicated variance/anomaly service; analytics service contains no alerting logic beyond static alerts in manager metrics. | ⚠️ Missing |
| **Privacy-First Design** | Aggregated reporting by default, PHI hidden unless role allows. | Role-based auth via JWT (`backend/src/middleware/auth.ts`). Dashboards mostly mock data. No explicit PHI masking/auditing beyond general RBAC. | ⏳ Partial |
| **AI Automation Add-Ons** | Weekly AI insights to email/Slack, variance/anomaly alerts. | No automation pipelines or notification integrations present (`backend/src/routes/reports.ts` only mocks scheduling). | ⚠️ Missing |
| **Core MVP Deliverable** | Centralized ERP MVP for 3–5 pilot locations. | System boasts multi-practice scaffolding (practice/location tables, ingestion). Frontend not production-ready (still compiling per `README.md`). Production URL referenced but status uncertain. | ⏳ Partial |
| **Documentation** | Technical docs & deployment guide. | `DEPLOYMENT_GCP_VM.md`, `IMPLEMENTATION_GUIDE.md`, `README.md`, etc. cover deployment/design. Missing AI/ETL specifics promised. | ⏳ Partial |

## ✅ Completed Foundations

- **Auth & Security** (`backend/src/routes/auth.ts`, `backend/src/middleware/auth.ts`): JWT auth, role enforcement.
- **Ingestion Framework** (`backend/src/services/ingestion.ts`): CSV/PDF parsing, patient/payroll/financial promotion, Dentrix/Eaglesoft parsers, JSON payload ingestion + mapping suggestions.
- **Integration Queue + Connectors** (`backend/src/services/integrationConnectors.ts`, `backend/src/services/ingestionQueue.ts`, `backend/src/server.ts`): Redis-backed worker ingesting ADP/NetSuite/DentalIntel APIs via new `/api/integrations/ingestion/api/enqueue`.
- **MCP Orchestration** (`backend/src/services/temporal.ts`, `backend/src/workflows/`, `backend/src/workers/integrationWorker.ts`, `docker-compose.yml` MCP services): Optional MCP workflows enqueue integration jobs with retry/backoff and provide UI at port 8233.
- **BI Metrics Schema** (`backend/src/database/schema.ts`): Tables for `biDailyMetrics`, AR buckets, scheduling metrics.
- **Mocked Analytics API** (`backend/src/routes/analytics.ts`): Endpoints covering executive, manager, clinician, forecasting, retention cohorts, benchmarking.
- **Report Generation Skeleton** (`backend/src/routes/reports.ts`): Start/status/download endpoints with mocks.
- **Frontend Shell** (`frontend/src/pages/analytics/*`, `frontend/src/layouts/`): Routing, placeholder dashboards, ingest UI.

## 🚧 In-Progress / Partial

- **Forecasting Calculations** (`backend/src/services/analytics.ts#getForecasting()`): basic growth deltas without ML.
- **Scheduling & Financial Aggregations**: DB-backed calculations exist but depend on populated `biDailyMetrics` (requires ingestion jobs).
- **Integration Monitoring UI** (`frontend/src/pages/integrations/StatusPage.tsx`): consumes mocked data.

## ❌ Missing / Not Started

- **AI ETL Connectors**: Queue + connectors in place; still need downstream enrichment, error handling dashboards, orchestration (Airflow/n8n).
- **AI Insights & Automation**: No text-to-insights engine, Slack/email automation, anomaly detection.
- **Data Warehouse Layers**: No dbt project, no Bronze/Silver/Gold pipeline, no BigQuery integration.
- **Real-Time Streaming**: WebSocket scaffolding exists but no live data ingestion from external systems.
- **AI Forecasting Models**: No ML model integration/tooling.
- **Privacy/PHI Controls**: Need explicit aggregation enforcement and audit logging for PHI access.
- **Deployment Confirmation**: Need to verify production environment parity with MVP scope.

## 📅 Timeline vs Reality (8-week target)

| Week | Planned Outcome | Actual Progress |
| --- | --- | --- |
| Week 1 | Requirements, architecture, AI ETL setup | Architecture & docs done; AI ETL setup outstanding. |
| Weeks 2–3 | Data warehouse, dbt models, dashboards MVP | Warehouse/dbt absent. Dashboards partially scaffolded with mock data. |
| Week 4 | Forecasting, AI automation add-ons | Basic forecasting calc only; automation missing. |
| Weeks 5–6 | UAT, training, documentation, go-live | Production readiness unclear; significant scope pending. |

## 🛠️ Next Steps (Suggested)

1. **Data Integration Roadmap**
   - Implement connectors or ingestion pipelines for ADP, NetSuite, DentalIntel using queue-based ingestion.
   - Introduce schema inference + mapping assistance (e.g., LLM prompts via LangChain) for CSV uploads.
   - Add orchestration (n8n/Airflow) definitions for scheduled ETL.

2. **Data Warehouse & Modeling**
   - Stand up dbt project aligning with Bronze/Silver/Gold layers.
   - Populate base models from ingestion tables, create KPI/variance models feeding `biDailyMetrics`.
   - Document transformation lineage.

3. **Analytics & AI Enhancements**
   - Replace mocked analytics with real aggregations or stubbed integration with external warehouses.
   - Add AI-generated narrative summaries using LLM APIs.
   - Expand forecasting to leverage Prophet/AutoARIMA or custom ML service.

4. **Automation & Alerts**
   - Build variance detection service monitoring KPIs, push alerts to Slack/email via webhook connectors.
   - Implement scheduled insight dispatch using cron/n8n with AI summarization.

5. **Privacy & Compliance**
   - Enforce aggregated views by default, audit access to PHI fields, add masking utilities.
   - Add logging/monitoring for role-based overrides.

6. **Frontend Completion**
   - Flesh out analytics dashboards with data-fetch hooks (`frontend/src/services/analytics.ts`).
   - Integrate ingestion workflows with new AI mapping hints.
   - Ensure responsive design matches proposal (reference `design-system/`).

7. **Validation & Launch**
   - Seed realistic sample data spanning multiple practices.
   - Create end-to-end tests for ingestion → analytics dashboards.
   - Conduct UAT and produce training materials aligned with MVP scope.

### Integration Focus: Recommended Next Actions

- **Harden Queue Lifecycle**: Persist job attempts/status in the database, introduce dead-letter handling, and wire alerting for repeated failures.
- **Implement Scheduler**: Adopt n8n, Airflow, or MCP to orchestrate recurring syncs per practice/location and manage retries.
- **Normalize & Promote Data**: Build transformation services to standardize incoming payloads, handle units/currency/time zones, and extend promotion flows beyond current placeholders.
- **Expose Monitoring**: Add structured logs/metrics and enhance `/api/integrations` endpoints so the frontend can surface job health, throughput, and errors.
- **Finalize Ops Documentation**: Expand `IMPLEMENTATION_GUIDE.md` with credential management, scheduler setup, queue toggles, and incident runbooks for integration failures.
- **Adopt MCP Orchestration**:
  - Provision MCP server (local Docker and production deployment), configure namespaces, and expose worker/SDK configuration env vars (`TEMPORAL_ADDRESS`, namespace names).
  - Implement TypeScript workflows/activities under `backend/src/workers/temporal/` that drive ingestion queue jobs, including retry/backoff policies and compensation hooks.
  - Schedule per-practice workflows via MCP cron, persist workflow IDs/state alongside `ingestionJobs`, and expose APIs/UI panels for run history, manual retries, and pause/resume controls.

## 📌 Planning Notes

- **Owner Assignment**: _Pending_
- **Milestone Targets**: _Pending_
