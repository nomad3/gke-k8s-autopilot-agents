# Snowflake Schema Design — NetSuite Financials (Bronze/Silver/Gold)

## Bronze Layer (Raw Landing)
- **Schema**: `netsuite_bronze`
- **Purpose**: Immutable copy of API extracts with minimal processing; includes ingestion metadata.

### Tables
- **`transaction_raw`**
  - `practice_id` STRING
  - `source_system` STRING DEFAULT 'netsuite'
  - `payload` VARIANT (full JSON from NetSuite transactions endpoint)
  - `ingested_at` TIMESTAMP_LTZ
  - `batch_id` STRING
  - `file_name` STRING (optional, when loading from files)
  - `correlation_id` STRING
- **`account_raw`** (chart of accounts)
  - Similar structure: `practice_id`, `payload`, `ingested_at`, `batch_id`, etc.
- **`vendor_raw`, `customer_raw`, `subsidiary_raw`** for supporting dimensions.

## Silver Layer (Cleaned & Modeled)
- **Schema**: `netsuite_silver`
- **Purpose**: Flattened, typed tables ready for analytics joins. Handle deduplication, type casting, and basic business rules (e.g., currency handling).

### Tables
- **`transactions_clean`**
  - `practice_id` STRING
  - `transaction_id` STRING
  - `transaction_type` STRING (invoice, vendorbill, journalentry, etc.)
  - `transaction_date` DATE
  - `posting_period` STRING
  - `account_id` STRING
  - `subsidiary_id` STRING
  - `customer_id` STRING
  - `vendor_id` STRING
  - `amount` NUMBER(18,2)
  - `currency` STRING
  - `status` STRING
  - `created_at` TIMESTAMP_LTZ
  - `last_modified_at` TIMESTAMP_LTZ
  - `source_batch_id` STRING
- **`accounts_clean`**, **`vendors_clean`**, **`customers_clean`**, **`subsidiaries_clean`** hold normalized dimension attributes.

## Gold Layer (Analytics-Ready)
- **Schema**: `netsuite_gold`
- **Purpose**: Business aggregates for dashboards, MoM/YoY KPIs, and AI insights.

### Tables / Views
- **`financial_summary`**
  - `practice_id` STRING
  - `period_start` DATE
  - `period_end` DATE
  - `revenue_total` NUMBER(18,2)
  - `cogs_total` NUMBER(18,2)
  - `operating_expense_total` NUMBER(18,2)
  - `net_income` NUMBER(18,2)
  - `currency` STRING
- **`ar_aging`**
  - `practice_id` STRING
  - `customer_id` STRING
  - `aging_bucket` STRING (0-30, 31-60, etc.)
  - `balance` NUMBER(18,2)
  - `currency` STRING
- **`ap_aging`**, **`cash_flow_summary`**, **`expense_trends`** as needed for dashboards/AI.

## Data Flow Overview
1. `NetsuiteConnector.sync()` fetches NetSuite data per practice and stores JSON payloads in `netsuite_bronze` using the staging helper.
2. Snowflake ingestion helper writes to Bronze tables with `batch_id`/`ingested_at` for traceability.
3. dbt models transform Bronze → Silver → Gold (version-controlled dbt project targeting Snowflake).
4. Gold outputs feed dashboards and AI insights (MoM comparisons, forecasting).

---

# Snowflake Ingestion Helper — NetSuite

## Proposed File: `backend/src/services/integrationHub/netsuiteIngestion.ts`
- Mirror existing manual ingestion helper but tailored for NetSuite API payloads.
- Responsible for inserting JSON payloads into Snowflake Bronze tables via `SnowflakeService`.

### Key Functions
```typescript
export type NetsuiteIngestionPayload = {
  practiceId: string;
  integrationType: 'netsuite';
  batchId: string;
  entity: 'transaction' | 'account' | 'vendor' | 'customer' | 'subsidiary';
  data: Record<string, unknown>[];
  correlationId?: string;
};

export async function stageNetSuitePayload(payload: NetsuiteIngestionPayload): Promise<void> {
  // 1. Resolve Snowflake credentials via IntegrationCredentialsService (practice-level or env default).
  // 2. Insert each record as JSON rows into netsuite_bronze.<entity>_raw with metadata columns.
}
```

- Use parameterized `INSERT` statements with `PARSE_JSON` for payloads or `COPY INTO` from staged files if batch size large.
- Ensure idempotency by upserting on `(practice_id, entity, record_id)` or tracking `batch_id`/`correlation_id` combinations.

---

# Integration Hub Metadata Configuration (Per Practice)

NetSuite connector behavior can be customized per practice through `IntegrationCredentialsService` metadata.

```jsonc
{
  "endpoints": {
    "transactions": "record/v1/journalEntry"
  },
  "query": {
    "transactions": {
      "sort": "lastModifiedDate:DESC",
      "fields": "internalId,tranId,tranDate,postingPeriod,subsidiary,entity,amount,currency,status,memo,createdDate,lastModifiedDate"
    }
  },
  "fieldMapping": {
    "transactions": {
      "tranId": "transaction_number",
      "tranDate": "transaction_date",
      "postingPeriod": "posting_period",
      "subsidiary": "subsidiary",
      "entity": "counterparty",
      "amount": "amount",
      "currency": "currency",
      "status": "status",
      "memo": "memo",
      "createdDate": "created_at",
      "lastModifiedDate": "last_modified_at"
    }
  }
}
```

- **`endpoints.transactions`** overrides the REST resource path (default `record/v1/journalEntry`).
- **`query.transactions`** supplies default query parameters (sorting, field selection, filters). Additional filters (e.g., date range) are merged during runtime.
- **`fieldMapping.transactions`** remaps NetSuite JSON properties to Snowflake column names in Silver/Gold layers.

If metadata is omitted, the connector falls back to these defaults.
