# How to Sync ALL NetSuite Data (75K+ Records)

## 🚀 Quick Start - Single Command

The NetSuite connector now **automatically batches** large syncs. Just specify the total limit you want:

```bash
gcloud compute ssh dental-erp-vm --zone=us-central1-a --command="cd /opt/dental-erp && source .env && curl -s -X POST 'https://mcp.agentprovision.com/api/v1/netsuite/sync/trigger' -H \"Authorization: Bearer \$MCP_API_KEY\" -H 'X-Tenant-ID: silvercreek' -H 'Content-Type: application/json' -d '{
    \"record_types\": [\"journalEntry\"],
    \"use_suiteql\": true,
    \"limit\": 75000
}' | python3 -m json.tool"
```

That's it! The system will automatically:
- ✅ Batch into 3,000 record chunks (NetSuite max)
- ✅ Handle offset-based pagination
- ✅ Rate limit between batches (2 seconds)
- ✅ Prevent duplicates with MERGE in Snowflake
- ✅ Log progress for each batch

## 📊 What Happens Behind the Scenes

```
User requests: limit=75000
    ↓
Auto-batching splits into: 25 batches of 3,000
    ↓
Batch 1: offset=0, limit=3,000    → 3,000 records
Batch 2: offset=3000, limit=3,000 → 3,000 records
Batch 3: offset=6000, limit=3,000 → 3,000 records
...
Batch 25: offset=72000, limit=3,000 → 3,000 records
    ↓
Total: 75,000 records fetched
    ↓
MERGE into Snowflake (prevents duplicates by ID)
    ↓
✅ All data synced!
```

## 🔄 For Daily Automated Sync

Set `limit: 100000` to get everything:

```bash
curl -X POST https://mcp.agentprovision.com/api/v1/netsuite/sync/trigger \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: silvercreek" \
  -H "Content-Type: application/json" \
  -d '{
    "record_types": ["journalEntry", "vendorBill", "invoice", "customer", "vendor"],
    "use_suiteql": true,
    "limit": 100000
  }'
```

The system will:
- Automatically batch each record type
- Fetch all records across all 24 subsidiaries
- Handle rate limiting
- Prevent duplicates

## ✅ Duplicate Prevention

The Snowflake loader uses **MERGE** statement:

```sql
MERGE INTO bronze.netsuite_journal_entries t
USING (new_data) s
ON t.ID = s.id
WHEN MATCHED THEN UPDATE ...
WHEN NOT MATCHED THEN INSERT ...
```

This means:
- ✅ Running sync multiple times = no duplicates
- ✅ Safe to re-run daily
- ✅ Only new/updated records are added/updated

## 📈 Monitor Progress

Check sync status:
```bash
curl -s https://mcp.agentprovision.com/api/v1/netsuite/sync/status \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: silvercreek" | python3 -m json.tool
```

Watch logs in real-time:
```bash
gcloud compute ssh dental-erp-vm --zone=us-central1-a --command="docker logs -f dental-erp_mcp-server-prod_1"
```

You'll see messages like:
```
[NetSuite SuiteQL] Fetching up to 75000 journal entries (auto-batching at 3000 per request)
[NetSuite SuiteQL] Batch 1: Fetched 3000 journal entries at offset 0
[NetSuite SuiteQL] Rate limiting: waiting 2 seconds before next batch...
[NetSuite SuiteQL] Batch 2: Fetched 3000 journal entries at offset 3000
...
[NetSuite SuiteQL] ✅ Fetched 75000 total journal entries across 25 batches
```

## 🎯 Verify Data in Snowflake

```sql
-- Total records
SELECT COUNT(*) FROM bronze.netsuite_journal_entries;

-- Records per subsidiary
SELECT
    raw_data:subsidiary.id::STRING as subsidiary_id,
    COUNT(*) as record_count
FROM bronze.netsuite_journal_entries
GROUP BY subsidiary_id
ORDER BY record_count DESC;

-- Recent sync
SELECT COUNT(*) FROM bronze.netsuite_journal_entries
WHERE _ingestion_timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour';

-- Sample records with line items
SELECT
    id,
    raw_data:tranId::STRING as tran_id,
    ARRAY_SIZE(raw_data:line) as line_count,
    _ingestion_timestamp
FROM bronze.netsuite_journal_entries
WHERE ARRAY_SIZE(raw_data:line) > 0
LIMIT 10;
```

## ⚡ Performance

| Records | Batches | Est. Time |
|---------|---------|-----------|
| 3,000   | 1       | ~2-3 min  |
| 10,000  | 4       | ~8-10 min |
| 75,000  | 25      | ~50-60 min |

Time includes:
- NetSuite API calls
- Line item fetching
- Snowflake inserts
- Rate limiting between batches

---

**The system now handles large syncs automatically!**
**No manual batching required!** 🎉
