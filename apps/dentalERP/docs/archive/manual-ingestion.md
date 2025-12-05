Manual Data Ingestion

Overview
- Enables manual upload of CSV, PDF, JSON, or TXT files when direct integrations (Dentrix, DentalIntel, ADP, Eaglesoft, NetSuite, QuickBooks Online) are unavailable or incomplete.
- Backend creates an ingestion job, stores the raw file, parses it into staging records, and exposes endpoints to view progress and promote staged data into domain tables.

Backend Endpoints (under `/api/integrations`)
- GET `/ingestion/supported`: list accepted file types and limits
- POST `/ingestion/upload` (multipart): fields `practiceId`, `sourceSystem`, optional `dataset`, and `file`
- POST `/ingestion/jobs/:id/process`: parse the uploaded file and create staging records
- GET `/ingestion/jobs`: list jobs for current user’s accessible practices (optional `practiceId`)
- GET `/ingestion/jobs/:id`: job details
- GET `/ingestion/jobs/:id/records`: paginated staging records (default 50)
- GET `/ingestion/jobs/:id/headers`: inspect available headers for mapping
- POST `/ingestion/jobs/:id/map`: persist a reusable mapping template (patients, payroll, financials)
- POST `/ingestion/jobs/:id/promote`: promote staged rows into domain tables (`target` = `patients` | `payroll` | `financials`)

Data Model (Drizzle ORM)
- `ingestion_jobs`: tracks uploaded file, type, status, counts, and errors
- `ingestion_records`: staging rows extracted from the file (JSON)
- `payroll_records`: canonical payroll rows hydrated from ADP exports (per employee / pay period)
- `financial_periods`: month-level financial rollups (NetSuite + QuickBooks historical totals)

Install Dependencies
- cd `backend` then install:
  - npm i multer pdf-parse csv-parse
  - npm i -D @types/multer

Database Migrations
- Update Drizzle schema config already points to `src/database/schema.ts` and `src/database/ingestion.ts`.
- Run: `npm run db:generate` then `npm run db:push` (in `backend`).

Configuration
- Upload directory env var (optional): `INGESTION_UPLOAD_DIR=/path/to/uploads`
  - Defaults to `<repo>/backend/uploads`

Frontend
- New page `Integrations → Manual Ingestion` at `/integrations/ingestion`.
- Upload a file, then click Process to parse and stage records.
- After processing, select a job → `View Records` to review raw rows, fine-tune the auto-generated field map, and promote into Patients, Payroll, or Financial Periods.
- Required fields per target are highlighted before promotion (e.g., `employeeName` + `grossPay` for payroll).

Notes
- CSV is parsed using header row (columns: true); PDF text is extracted as a single staging record.
- Mapping UI now supports manual overrides for patients, payroll, and monthly financials.
- Historical QuickBooks Online data (pre-Jul 2025) should be uploaded with dataset `financials`; canonical monthly metrics will land in `financial_periods`.
- Sample data lives in `examples/ingestion/`. Use `scripts/ingestion-demo.sh` (requires Docker backend, `curl`, `jq`) to validate patients, payroll, financial rollups, and Dentrix/Eaglesoft day sheet PDFs end-to-end.
