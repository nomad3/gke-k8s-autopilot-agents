## 🧩 **MASTER PROMPT — AgentProvision MCP Server**

```
You are building the "MCP Server" (Mapping & Control Plane) for AgentProvision — the AI orchestration and integration backbone that powers DataFlow AI (the customizable ERP for roll-ups like Silvercreek Dental Partners).

### 🧠 Purpose
The MCP Server is the control plane and data sync manager for all business integrations:
- ADP → Payroll data
- Eaglesoft → Procedures, payments, visits
- DentalIntel → Production KPIs
- NetSuite → Financial GL, AP/AR
- Merchant Processors → Payments, deposits

It normalizes, maps, and orchestrates these data flows into a single API & warehouse layer called **DentalERP**.

---

### 🏗️ Core Requirements
1. **Framework:** FastAPI (Python 3.11)
2. **Database:** PostgreSQL (SQLAlchemy + Alembic)
3. **Queue:** Kafka (or fallback to Redis Streams)
4. **Orchestration:** MCP.io (preferred) or Airflow
5. **Caching:** Redis
6. **Data Modeling:** dbt models for transformations
7. **Observability:** Prometheus + Grafana + OpenTelemetry
8. **Auth:** JWT + API Key per integration
9. **Containerization:** Docker + Docker Compose
10. **IaC:** Terraform-ready outputs (S3, ECS, RDS)

---

### ⚙️ System Design Goals
- Stateless microservice with scalable REST + gRPC endpoints.
- Modular connectors for each integration (ADP, Eaglesoft, DentalIntel, NetSuite).
- Map registry tables (source_id, internal_id, entity_type, status, last_synced_at).
- Orchestration workflows: ingestion → validation → transformation → sync.
- Support async event-driven operations via Kafka topics.

---

### 📁 Project Structure
```

/mcp-server
├── src/
│   ├── api/
│   │   ├── main.py (FastAPI entrypoint)
│   │   ├── routers/
│   │   │   ├── mappings.py
│   │   │   ├── sync.py
│   │   │   ├── health.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   ├── db/
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── crud.py
│   │   ├── init_db.py
│   ├── integrations/
│   │   ├── adp_connector.py
│   │   ├── eaglesoft_connector.py
│   │   ├── dentalintel_connector.py
│   │   ├── netsuite_connector.py
│   │   ├── bank_connector.py
│   ├── orchestration/
│   │   ├── workflows.py
│   │   ├── tasks.py
│   ├── utils/
│   │   ├── logger.py
│   │   ├── telemetry.py
│   ├── **init**.py
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── README.md
├── .env.example
├── scripts/
│   ├── seed_db.py
│   ├── create_mappings_table.sql
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf

```

---

### 🧩 Core Entities & Tables
- **mappings** → store cross-system identifiers
- **jobs** → orchestration runs and states
- **audit_logs** → track syncs and API calls
- **integrations** → credentials, tokens, configs per system

---

### 🧠 Example API Endpoints
```

POST /api/v1/mappings/register
→ Register new mapping between systems

GET /api/v1/mappings/status
→ Return current sync state for given system

POST /api/v1/workflows/run
→ Trigger data sync workflow between systems

GET /api/v1/health
→ Return uptime and system metrics

```

---

### 🧩 Example Mapping Registry Schema (SQLAlchemy)
```

class Mapping(Base):
**tablename** = "mappings"
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
source_system = Column(String, nullable=False)
source_id = Column(String, nullable=False)
target_system = Column(String, nullable=False)
target_id = Column(String, nullable=False)
entity_type = Column(String, nullable=False)
status = Column(String, default="pending")
last_synced_at = Column(DateTime, default=datetime.utcnow)

```

---

### 🧠 Prompt Behavior
When I type:
> “Generate the MCP Server scaffolding”
You should:
- Create the FastAPI app, folders, and init scripts.
- Scaffold Dockerfile, docker-compose, and requirements.txt.
- Add one working example endpoint (`/api/v1/health`) and mapping model.
- Include SQLAlchemy, Pydantic, and connection to Postgres.
- Prepare the repo for incremental connector development.

When I type:
> “Add ADP connector”
You should:
- Generate the integration module for ADP.
- Include async API calls, token refresh, and data ingestion example.

---

### 💬 Coding Rules
- Write clean, modular code with comments.
- Use async/await for IO operations.
- Return JSON responses with standardized structure.
- Log every step (info, error, debug).
- Keep secrets in `.env` (never hardcode).

---

### ✅ Deliverable
A fully working scaffold for the MCP server that:
- Runs locally with Docker Compose.
- Connects to Postgres + Redis.
- Exposes REST endpoints to register mappings and run sync jobs.
- Logs all operations and is ready for connector and AI agent extensions.

```
