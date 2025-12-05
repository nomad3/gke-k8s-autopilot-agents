# Snowflake Migration Execution Guide
**Script**: `snowflake-multi-tenant-migration.sql` (410 lines)
**Time**: 30 minutes
**Risk**: Low (transaction-based, reversible)

---

## 🚀 Quick Start

### Option 1: Snowflake Web UI (Recommended)

1. **Open Snowflake Web UI**
   - URL: https://app.snowflake.com/
   - Account: `HKTPGHW-ES87244` (GCP Singapore)
   - User: `NOMADSIMON`
   - Password: `@SebaSofi.2k25!!`

2. **Switch Context**
   ```sql
   USE DATABASE DENTAL_ERP_DW;
   USE ROLE ACCOUNTADMIN;
   ```

3. **Open Migration Script**
   - File: `snowflake-multi-tenant-migration.sql`
   - Copy entire contents (410 lines)

4. **Execute in Transaction**
   ```sql
   BEGIN TRANSACTION;

   -- Paste the 410 lines here
   -- (Everything from "USE DATABASE DENTAL_ERP_DW;" to the end)

   -- Review results in Results panel
   -- If everything looks good:
   COMMIT;

   -- If there are issues:
   -- ROLLBACK;
   ```

5. **Verify Migration**
   ```sql
   -- Check tenant_access_mapping table
   SELECT * FROM tenant_access_mapping;

   -- Verify tenant_id columns exist
   DESCRIBE TABLE bronze.pms_day_sheets;

   -- Check existing data has tenant_id
   SELECT tenant_id, COUNT(*)
   FROM bronze.pms_day_sheets
   GROUP BY tenant_id;
   ```

---

## ⚠️ IMPORTANT: Manual Execution Required

**Why manual?**
- Row access policies require ACCOUNTADMIN role
- NOT NULL constraints need careful validation
- Table structure changes need review before commit

**Cannot be automated** due to Snowflake security model.

---

## 📋 What the Script Does

### Step 1: Add tenant_id to Bronze Layer (Lines 18-45)
```sql
ALTER TABLE bronze.netsuite_journalentry ADD COLUMN tenant_id VARCHAR(50);
ALTER TABLE bronze.pms_day_sheets ADD COLUMN tenant_id VARCHAR(50);
ALTER TABLE bronze.pms_deposit_slips ADD COLUMN tenant_id VARCHAR(50);
```

### Step 2: Add tenant_id to Silver Layer (Lines 48-65)
```sql
ALTER TABLE bronze_silver.stg_pms_day_sheets ADD COLUMN tenant_id VARCHAR(50);
```

### Step 3: Add tenant_id to Gold Layer (Lines 68-115)
```sql
ALTER TABLE bronze_gold.daily_production_metrics ADD COLUMN tenant_id VARCHAR(50);
ALTER TABLE bronze_gold.production_by_practice ADD COLUMN tenant_id VARCHAR(50);
ALTER TABLE bronze_gold.production_summary ADD COLUMN tenant_id VARCHAR(50);
```

### Step 4: Backfill with 'default' (Lines 118-145)
```sql
UPDATE bronze.pms_day_sheets SET tenant_id = 'default' WHERE tenant_id IS NULL;
-- (Repeated for all 7 tables)
```

### Step 5: Make NOT NULL (Lines 148-185)
```sql
ALTER TABLE bronze.pms_day_sheets ALTER COLUMN tenant_id SET NOT NULL;
-- (Repeated for all 7 tables)
```

### Step 6: Create Tenant Access Mapping (Lines 186-200)
```sql
CREATE TABLE IF NOT EXISTS tenant_access_mapping (
    tenant_id VARCHAR(50) PRIMARY KEY,
    tenant_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

INSERT INTO tenant_access_mapping VALUES
    ('default', 'Default Tenant', TRUE, CURRENT_TIMESTAMP()),
    ('acme', 'ACME Dental Practice', TRUE, CURRENT_TIMESTAMP());
```

### Step 7: Create Row Access Policy (Lines 201-350)
```sql
CREATE OR REPLACE ROW ACCESS POLICY tenant_isolation_policy
    AS (tenant_id VARCHAR) RETURNS BOOLEAN ->
    CASE
        WHEN CURRENT_ROLE() = 'ACCOUNTADMIN' THEN TRUE
        WHEN CURRENT_ROLE() = 'SYSADMIN' THEN TRUE
        ELSE tenant_id = CURRENT_USER()
    END;

-- Apply to all 7 tables
ALTER TABLE bronze.pms_day_sheets
    ADD ROW ACCESS POLICY tenant_isolation_policy ON (tenant_id);
-- (Repeated for all tables)
```

### Step 8: Update Clustering Keys (Lines 351-400)
```sql
ALTER TABLE bronze_gold.daily_production_metrics
    CLUSTER BY (tenant_id, practice_location, report_date);
-- (Repeated for relevant tables)
```

---

## ✅ Validation Checklist

After running the script, verify:

- [ ] All 7 tables have tenant_id column
- [ ] tenant_id is NOT NULL on all tables
- [ ] tenant_access_mapping has 'default' and 'acme' rows
- [ ] Row access policy created
- [ ] Policy applied to all 7 tables
- [ ] Existing data backfilled with tenant_id='default'
- [ ] No error messages in Results panel

**Validation Queries**:
```sql
-- Check tenant_access_mapping
SELECT * FROM tenant_access_mapping;
-- Expected: 2 rows (default, acme)

-- Check Bronze layer
SELECT tenant_id, COUNT(*) FROM bronze.pms_day_sheets GROUP BY tenant_id;
-- Expected: All rows have tenant_id='default'

-- Check Silver layer
SELECT tenant_id, COUNT(*) FROM bronze_silver.stg_pms_day_sheets GROUP BY tenant_id;
-- Expected: All rows have tenant_id='default'

-- Check Gold layer
SELECT tenant_id, COUNT(*) FROM bronze_gold.daily_production_metrics GROUP BY tenant_id;
-- Expected: All rows have tenant_id='default'

-- Verify row access policy
SHOW ROW ACCESS POLICIES;
-- Expected: tenant_isolation_policy exists

-- Check policy assignments
SELECT * FROM INFORMATION_SCHEMA.POLICY_REFERENCES
WHERE POLICY_NAME = 'TENANT_ISOLATION_POLICY';
-- Expected: 7 tables listed
```

---

## 🔄 Rollback Plan

If you need to undo the migration:

```sql
BEGIN TRANSACTION;

-- Remove row access policies
ALTER TABLE bronze.netsuite_journalentry DROP ROW ACCESS POLICY tenant_isolation_policy;
ALTER TABLE bronze.pms_day_sheets DROP ROW ACCESS POLICY tenant_isolation_policy;
ALTER TABLE bronze.pms_deposit_slips DROP ROW ACCESS POLICY tenant_isolation_policy;
ALTER TABLE bronze_silver.stg_pms_day_sheets DROP ROW ACCESS POLICY tenant_isolation_policy;
ALTER TABLE bronze_gold.daily_production_metrics DROP ROW ACCESS POLICY tenant_isolation_policy;
ALTER TABLE bronze_gold.production_by_practice DROP ROW ACCESS POLICY tenant_isolation_policy;
ALTER TABLE bronze_gold.production_summary DROP ROW ACCESS POLICY tenant_isolation_policy;

-- Drop row access policy
DROP ROW ACCESS POLICY IF EXISTS tenant_isolation_policy;

-- Drop tenant_access_mapping table
DROP TABLE IF EXISTS tenant_access_mapping;

-- Drop tenant_id columns (WARNING: This removes data!)
-- ALTER TABLE bronze.pms_day_sheets DROP COLUMN tenant_id;
-- (Repeat for all tables if needed)

COMMIT;
```

**Note**: Dropping tenant_id columns will lose the tenant associations. Only do this if absolutely necessary.

---

## 🚨 Common Issues

### Issue 1: "Insufficient privileges"
**Solution**: Ensure you're using ACCOUNTADMIN role:
```sql
USE ROLE ACCOUNTADMIN;
```

### Issue 2: "Column already exists"
**Solution**: Script is idempotent. Safe to re-run. Use IF EXISTS clauses.

### Issue 3: "Cannot add NOT NULL to column with NULL values"
**Solution**: Ensure Step 4 (backfill) completed successfully before Step 5 (NOT NULL).

### Issue 4: "Row access policy already exists"
**Solution**: Drop existing policy first:
```sql
DROP ROW ACCESS POLICY IF EXISTS tenant_isolation_policy;
```

---

## 📊 Expected Execution Time

| Step | Time | Notes |
|------|------|-------|
| Add columns (Steps 1-3) | 2 min | Fast, metadata only |
| Backfill data (Step 4) | 5-10 min | Depends on data volume |
| Set NOT NULL (Step 5) | 2 min | Fast, metadata only |
| Create mapping (Step 6) | 1 min | Small table |
| Create policy (Step 7) | 5 min | Policy creation + application |
| Update clustering (Step 8) | 5-10 min | Depends on table size |
| **Total** | **20-30 min** | Including validation |

---

## 🎯 Success Criteria

Migration is successful when:
1. ✅ All validation queries return expected results
2. ✅ No error messages in Results panel
3. ✅ Transaction committed (not rolled back)
4. ✅ dbt run completes successfully (next step)
5. ✅ Test suite passes (17/17 tests)

---

## 📞 Need Help?

If you encounter issues:
1. **DO NOT COMMIT** the transaction yet
2. Copy the error message
3. Check Common Issues section above
4. Run validation queries to see current state
5. Use ROLLBACK if needed to undo changes

---

**Next Steps After Migration**:
1. Run dbt transformations: `cd dbt/dentalerp && dbt run`
2. Fix Snowflake async issue (connector update)
3. Run test suite: `./test-multi-tenant-e2e.sh`
4. Verify 17/17 tests passing

---

**Prepared By**: Claude Code
**Last Updated**: 2025-10-30
