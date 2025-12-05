# ❄️ Snowflake-Centric Architecture - Quick Reference

## ✅ **Correct Architecture**

```
┌───────────────────┐
│  External APIs    │  NetSuite, ADP, DentalIntel
└─────────┬─────────┘
          │
          ▼ MCP extracts (API calls only)
┌─────────────────────────────────────────────────────────────┐
│  MCP Server (Thin Orchestration - Python/FastAPI)           │
│  ✅ Extract raw JSON from APIs                               │
│  ✅ Load raw JSON to Snowflake Bronze                        │
│  ❌ NO transformations                                        │
│  ❌ NO aggregations                                           │
│  ❌ NO joins                                                  │
└─────────┬───────────────────────────────────────────────────┘
          │
          ▼ Load raw JSON
┌─────────────────────────────────────────────────────────────┐
│           SNOWFLAKE (Heavy Compute - SQL/dbt)                │
│                                                               │
│  BRONZE: Raw JSON storage (VARIANT columns)                  │
│    bronze.netsuite_journalentry                              │
│    bronze.adp_employees                                      │
│          │                                                    │
│          ▼ dbt transforms (SQL in Snowflake)                 │
│  SILVER: Cleaned & standardized                              │
│    ✅ Deduplication (ROW_NUMBER() OVER...)                   │
│    ✅ Type casting (::DATE, ::DECIMAL)                       │
│    ✅ Field extraction (raw_data:field::TYPE)                │
│          │                                                    │
│          ▼ dbt aggregates (SQL in Snowflake)                 │
│  GOLD: Business metrics & KPIs                               │
│    ✅ SUM(), AVG(), COUNT() aggregations                     │
│    ✅ Window functions (LAG, LEAD)                           │
│    ✅ Complex joins (facts + dimensions)                     │
│    ✅ MoM growth calculations                                │
└─────────┬───────────────────────────────────────────────────┘
          │
          ▼ MCP queries (SELECT only)
┌─────────────────────────────────────────────────────────────┐
│  MCP Server (Query Gold Tables)                              │
│  ✅ SELECT from gold.monthly_production_kpis                  │
│  ✅ Cache results in Redis (5 min)                           │
│  ✅ Return JSON to ERP                                        │
│  ❌ NO calculations                                           │
└─────────┬───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│  ERP Backend → Frontend                                      │
│  ✅ Display pre-computed metrics                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 **Who Does What**

### **MCP Server (Python/FastAPI)** - THIN
**Responsibilities:**
- ✅ Call external APIs (NetSuite, ADP)
- ✅ Load raw JSON to Snowflake `bronze.*` tables
- ✅ Query Snowflake `gold.*` tables (pre-computed)
- ✅ Cache results in Redis
- ✅ Return JSON to ERP

**NEVER Do:**
- ❌ Transform data (use dbt in Snowflake)
- ❌ Aggregate data (use Snowflake SQL)
- ❌ Calculate KPIs (use dbt models)
- ❌ Join tables (use Snowflake)

---

### **Snowflake + dbt (SQL)** - HEAVY
**Responsibilities:**
- ✅ Store raw data in Bronze (VARIANT columns)
- ✅ Transform data in Silver (SQL transformations)
- ✅ Aggregate data in Gold (SUM, AVG, COUNT)
- ✅ Calculate KPIs (MoM growth, profit margins)
- ✅ Deduplicate records (window functions)
- ✅ Join tables (facts + dimensions)
- ✅ Run all analytics queries

**Processing Power:**
- ✅ Parallel execution (10-100 compute nodes)
- ✅ Columnar storage (10-100x faster)
- ✅ Auto-scaling clusters
- ✅ Query result caching
- ✅ Handles petabytes of data

---

## 📝 **Code Examples**

### **✅ CORRECT: MCP Extracts + Loads Raw**
```python
# mcp-server/src/services/sync_orchestrator.py

# Extract raw JSON from NetSuite
response = await netsuite.fetch_journal_entries()

# Load raw JSON to Bronze (no transformation)
await snowflake.bulk_insert(
    "bronze.netsuite_journalentry",
    records=[{
        "raw_data": record,  # Entire JSON as VARIANT
        "extracted_at": now()
    } for record in response.data]
)
```

---

### **✅ CORRECT: dbt Transforms in Snowflake**
```sql
-- dbt/dentalerp/models/silver/core/stg_financials.sql

-- ALL transformations happen in Snowflake SQL
SELECT
    raw_data:internalId::VARCHAR AS internal_id,
    raw_data:tranDate::DATE AS transaction_date,
    raw_data:amount::DECIMAL(18,2) AS amount,
    -- Deduplication in Snowflake (window function)
    ROW_NUMBER() OVER (
        PARTITION BY internal_id
        ORDER BY extracted_at DESC
    ) AS row_num
FROM bronze.netsuite_journalentry
WHERE row_num = 1
```

---

### **✅ CORRECT: dbt Aggregates in Snowflake**
```sql
-- dbt/dentalerp/models/gold/facts/fact_financials.sql

-- ALL aggregations happen in Snowflake SQL
SELECT
    practice_name,
    DATE_TRUNC('MONTH', transaction_date) AS month_date,
    SUM(amount) AS total_production,        -- Snowflake aggregates
    COUNT(DISTINCT transaction_id) AS txn_count,
    AVG(amount) AS avg_transaction,
    -- MoM growth in Snowflake (window function)
    LAG(total_production) OVER (
        PARTITION BY practice_name
        ORDER BY month_date
    ) AS prev_month_production
FROM {{ ref('stg_financials') }}
GROUP BY 1, 2
```

---

### **✅ CORRECT: MCP Queries Pre-Computed Gold**
```python
# mcp-server/src/services/snowflake.py

@cached(ttl=300)  # Cache for 5 min
async def get_financial_summary(location_id):
    # Just SELECT from pre-computed Gold table
    # NO calculations here!
    query = """
        SELECT * FROM gold.monthly_production_kpis
        WHERE practice_name = %s
        ORDER BY month_date DESC
        LIMIT 12
    """
    # Snowflake returns in ~100ms
    return await snowflake.execute(query, [location_id])
```

---

## ⚡ **Performance Benefits**

### **Processing 1M Transactions:**

| Approach | Where | Time | Scalability |
|----------|-------|------|-------------|
| ❌ Python loop in MCP | Python | 30-60 sec | Poor |
| ❌ Pandas in MCP | Python Memory | 10-20 sec | Limited |
| ✅ **dbt + Snowflake** | **Snowflake Warehouse** | **< 1 sec** | **Unlimited** |

### **Why Snowflake is 100x Faster:**
- **Columnar Storage**: Only scans needed columns
- **Parallel Execution**: 10-100 compute nodes simultaneously
- **Result Caching**: Automatic query result reuse
- **Pushdown**: Filters applied at storage layer
- **Optimized for Analytics**: Purpose-built for aggregations

---

## 🔄 **Data Flow Timeline**

### **Nightly Sync (Automated)**
```
23:00 - MCP extracts from NetSuite (5 min)
23:05 - Raw data in bronze.netsuite_* tables
23:10 - dbt runs transformations (2 min)
        Bronze → Silver (clean)
        Silver → Gold (aggregate)
23:12 - All Gold tables updated & ready
```

### **Dashboard Load (User Request)**
```
User opens dashboard → ERP → MCP → Snowflake Gold table
Query: SELECT * FROM gold.monthly_production_kpis
Response time: ~100ms (pre-computed!)
With Redis cache: ~10ms
```

---

## 📚 **Summary**

**Golden Rules:**
1. ✅ **MCP Server**: Extract (API) + Load (Bronze)
2. ✅ **Snowflake/dbt**: Transform + Aggregate + Calculate
3. ✅ **MCP Server**: Query (Gold) + Cache (Redis)
4. ✅ **Frontend**: Display only

**Result:**
- 100x faster analytics
- Infinite scalability
- Lower infrastructure costs
- Maintainable SQL vs complex Python

---

**Architecture**: ✅ Snowflake-Centric
**Processing**: ✅ 100% in Snowflake
**MCP Role**: ✅ Thin orchestration layer
**Status**: ✅ Correctly Implemented
