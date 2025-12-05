You are a principal platform engineer designing a SaaS "UnifiedOps" platform that unifies data from fragmented systems (ERP, CRM, Payroll, Support, Marketing, e-commerce, PDFs/EDI) into a canonical model, then layers AI to drive real business outcomes (faster decisions, revenue protection, cost reduction). The system must be multi-tenant, API-first, and deployable in sprints.

## INPUT PARAMETERS (allow defaults, but auto-suggest where missing)
VERTICALS = one or more of ["dental", "healthcare", "retail", "hospitality", "logistics", "manufacturing", "field_services"]
REGION = "US" | "EU" | "LATAM" (affects compliance & currency/locale)
SOURCES = choose/connect: ERP(NetSuite/SAP/Oracle), Accounting(QB/Xero), Payroll(ADP/Gusto), CRM(Salesforce/HubSpot), Support(Zendesk/Fresh), Ads(GA4/Google/Meta), eCom(Shopify/Woo), PMS(industry-specific), Files(PDF/CSV/SFTP), EDI(X12)
TARGET_STACK = { ETL: Python, Orchestrator: Prefect/Airflow, Warehouse: Postgres (OLAP-first) + Object Store, Services: Node/TS (Nest/Fastify) or Python (FastAPI), UI: Next.js/React, Mobile optional, Infra: Docker + IaC }

## CORE GOAL
Ship a wedge product called **KPI Control Tower** (real-time KPIs + drilldowns + exports) + **ETL Connectors**, then expand into **AI Workflows** that save time or increase revenue.
The system MUST: ingest → validate → normalize to canonical schema → compute KPIs → alert/automate → expose APIs/UI.

## ARCHITECTURE (generate concrete)
- Ingestion: connectors for APIs, webhooks, polling, SFTP/CSV, PDF/EDI (AI OCR). Idempotent, backfillable, rate-limit aware.
- Staging & Canonical: raw landing (object store) → staging tables → canonical DIM/FACT model.
- Transform & Data Quality: dbt/SQL + Great-Expectations-style checks; lineage; SCD2 on key dimensions.
- Serving: REST/GraphQL `/kpi/query`, `/ingest/*`, `/ai/*`, `/export/*`; role-aware result filtering.
- UI: multi-tenant dashboards, drilldowns org→region→site→user→transaction (as permitted).
- Multi-tenancy: row-level security, per-tenant secrets, per-tenant KMS keys; usage metering.
- Observability: traces, structured logs, metrics; runbooks and alerts for DAG failures.

## CONNECTOR CATALOG (generate adapters + schemas)
- ERP/Accounting: NetSuite, SAP, Oracle, QuickBooks, Xero
- Payroll/HR: ADP, Gusto
- CRM/Support: Salesforce, HubSpot, Zendesk, Freshdesk
- Marketing/Analytics: GA4, Google Ads, Meta Ads
- eCommerce: Shopify, WooCommerce
- Industry PMS: plug-in interface (e.g., Dental: Dentrix/OpenDental/Eaglesoft; Hospitality: PMS; Logistics: TMS/WMS)
- Files/Legacy: SFTP CSV, PDF (AI OCR), EDI X12
For each connector output: auth pattern, pagination/rate limits, change data capture approach, schemas, mapping to canonical.

## CANONICAL DATA MODEL (generate DDL)
Dimensions: dim_date, dim_org, dim_site, dim_user/provider/employee, dim_customer/patient, dim_product/service, dim_payer/vendor, dim_channel
Facts: fact_revenue, fact_costs, fact_transactions/orders, fact_appointments/schedules, fact_payroll, fact_tickets, fact_marketing_spend, fact_inventory, fact_claims (if healthcare)
Also: cross_system_id_map, audit_loads, dq_results
Provide SQL DDL (Postgres), indexes, partitioning strategy, and a synthetic data generator.

## KPI LIBRARY (auto-tailor per VERTICALS)
Common KPIs: revenue, gross margin, COGS, CAC/ROAS, payroll %, utilization, churn/retention, SLA, backlog/burn, on-time rate.
Vertical overlays:
- Dental/Healthcare: production per provider, cancellations/no-show %, collections %, denial rate, days in A/R.
- Retail/eCom: AOV, conversion, inventory turns, stockouts, returns %, gross margin by SKU.
- Hospitality: RevPAR, ADR, occupancy, cancellation lead time, channel mix.
- Logistics: OTIF, cost per drop, route utilization, dwell time.
- Manufacturing: yield, OEE, scrap rate, throughput, downtime.
Generate formulas, grain, filters, and sample SQL for each selected vertical.

## AI WORKFLOWS (prioritize real $$ impact; add domain toggles)
1) AI-OCR Intake (PDF/EDI/EOB/invoices) → JSON with confidence scores; review queue UI.
2) Anomaly Detection (KPIs vs. baseline) → alert feed with “why” (SHAP-like reasons).
3) Forecasting (demand/appointments/revenue) → staffing or inventory suggestions.
4) Risk Scoring (e.g., claim denial risk, churn risk, stockout risk) → pre-submit checks & playbooks.
5) Copilot Actions: “Morning Briefing” that summarizes yesterday + actions (call list, price update, reorder, reschedule).
All AI must be human-in-the-loop with audit trails.

## SECURITY, TRUST & COMPLIANCE
- SOC2 roadmap; HIPAA toggle for healthcare; GDPR/CCPA data rights; PII/PHI minimization.
- Encryption in transit/at rest, audit logs, secret rotation, RBAC/ABAC, tenant isolation tests.
- Data retention policies; deletion & export endpoints.

## DEVOPS & COST
- Monorepo structure:
  /services/ingest/*, /services/transform, /services/serve, /ui/web, /ai, /infra (IaC), /tests, /examples
- CI/CD with migration gating; seed & demo mode; backfill commands.
- Provide cloud-cost rough order-of-magnitude for 10 tenants and scaling notes.

## DELIVERABLES (return as a single Markdown spec with code blocks)
1) System architecture diagram description (ASCII + component list).
2) Connector specs for 5 core systems in SOURCES (auth, pagination, schemas).
3) Postgres DDL for canonical model + example dbt models.
4) ETL DAGs: names, dependencies, retry/backfill patterns; DQ rules.
5) KPI definitions per selected VERTICALS with sample SQL and /kpi/query API examples.
6) AI workflow specs: inputs/outputs, model choices, evaluation, human review UI.
7) REST/GraphQL API surface with endpoints, request/response JSON, and auth.
8) UI wireframe JSON (filters, drilldowns, role views) + “Morning Briefing” example.
9) Multi-tenant security model (RLS policies, scopes) and audit strategy.
10) Monorepo scaffold (folders, package.json/pyproject.toml samples), docker-compose, env template.
11) Sprints plan (3 x 2-week): Wedge MVP (KPI Tower), AI-OCR, Predictive #1; risks & mitigations.

## STYLE & CONSTRAINTS
- Keep it implementation-ready. Prefer TypeScript for services, Python for ETL/AI.
- Use clear, typed schemas; include test stubs and sample payloads.
- Avoid vendor lock-in; adapters and feature flags for vertical packs.
- Output MUST be deterministic and actionable for a team to start coding today.
