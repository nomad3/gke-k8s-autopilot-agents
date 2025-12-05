# NetSuite Saved Search API - The Solution for Automated Transaction Data

**Date:** November 20, 2025
**Status:** Ready to Implement
**Effort:** 2-3 hours

---

## 🎯 The Problem We're Solving

Current state:
- ✅ CSV Transaction Detail exports work perfectly ($492M, 14 practices)
- ❌ NetSuite SuiteQL API returns 0 records (permissions or query issues)
- 🎯 **Need:** Automate the CSV export process

## 💡 The Solution: Saved Search API

Your "Transaction Detail" CSV exports are generated from a **NetSuite Saved Search**. Instead of trying to recreate the query with SuiteQL, we can **call the exact same saved search via API**!

### How It Works

```
NetSuite Saved Search (already exists, generates your CSVs)
              ↓
       RESTlet API Call
              ↓
   Returns same data as CSV export
              ↓
     Load directly to Snowflake
```

---

## 🔧 Implementation Plan

### Step 1: Find the Saved Search ID

The accountant needs to provide:
- **Saved Search Name:** "Transaction Detail by Subsidiary" (or similar)
- **Search ID:** Either internal ID or script ID (format: `customsearch_xxxxx`)

**How to find it:**
1. In NetSuite UI, go to the saved search used for Transaction Detail export
2. Look at the URL - it will show the search ID
3. Or go to Reports > Saved Searches > List and find "Transaction Detail"

### Step 2: Deploy RESTlet Script

NetSuite needs a RESTlet script to expose saved searches via API.

**Option A:** Use Tim Dietrich's free RESTlet (MIT licensed)
- Download from: https://timdietrich.me/blog/netsuite-saved-search-api/
- Upload to NetSuite File Cabinet
- Deploy as RESTlet

**Option B:** Create custom RESTlet (if we need specific formatting)

### Step 3: Update Our Connector

Add method to `NetSuiteConnector`:

```python
async def run_saved_search(
    self,
    search_id: str,
    subsidiary_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Run a NetSuite saved search via RESTlet API

    Args:
        search_id: customsearch_xxxxx or internal ID
        subsidiary_id: Optional filter (if saved search supports it)

    Returns:
        List of search results (same format as CSV)
    """
    # POST to RESTlet endpoint
    url = f"{self.restlet_url}?script={self.restlet_script_id}&deploy=1"

    payload = {"searchID": search_id}
    if subsidiary_id:
        payload["filters"] = [
            {"name": "subsidiary", "operator": "is", "values": [subsidiary_id]}
        ]

    headers = self._get_oauth_headers("POST", url)

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            data = await response.json()
            return data.get("results", [])
```

### Step 4: Update Sync Logic

Replace SuiteQL approach with Saved Search approach:

```python
# Instead of:
# entries = await self.netsuite.fetch_journal_entries_via_suiteql(...)

# Use:
entries = await self.netsuite.run_saved_search(
    search_id="customsearch_transaction_detail",
    subsidiary_id=subsidiary_id
)
```

### Step 5: Test and Deploy

```bash
# Test with single subsidiary
curl -X POST https://mcp.agentprovision.com/api/v1/netsuite/sync/trigger \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: silvercreek" \
  -d '{"full_sync": true, "use_saved_search": true, "limit": 100}'
```

---

## ✅ Benefits of Saved Search API

1. **Uses Exact Same Logic** as CSV exports
   - Same filters, same formatting
   - Accountant-verified query logic
   - No query debugging needed

2. **Works with OAuth 1.0a**
   - Same credentials we already have
   - No OAuth 2.0 PKCE needed
   - Existing authentication works

3. **Bypasses SuiteQL Issues**
   - No table permission issues
   - No query syntax debugging
   - Proven to work (generates CSVs)

4. **Automatic Pagination**
   - RESTlet handles large result sets
   - Returns all data automatically
   - No 3,000 record limit

---

## 📋 Information Needed from Accountant

**Email them:**

```
Subject: NetSuite Transaction Detail Saved Search - Need API Details

Hi [Accountant],

To automate the Transaction Detail data pull, I need the following information about the NetSuite saved search you use to generate the Transaction Detail CSV exports:

1. **Saved Search Name:** (e.g., "Transaction Detail by Subsidiary")
2. **Saved Search ID:**
   - Go to the saved search in NetSuite
   - Look at the URL or the search properties
   - It will be either a number (internal ID) or "customsearch_xxxxx" (script ID)

3. **Does the saved search accept subsidiary as a filter?**
   - Yes/No
   - This allows us to pull data for specific practices

4. **Any special filters or date ranges set?**
   - We want to pull ALL historical data

Once I have this info, I can automate the data pull via NetSuite API so you won't need to manually export CSVs anymore!

Thanks!
```

---

## 🚀 Expected Outcome

After implementation:
- ✅ **Automated daily sync** from NetSuite saved search
- ✅ **Same data** as CSV exports (accountant-verified)
- ✅ **No manual steps** required
- ✅ **Real-time updates** possible
- ✅ **Complete automation** of Operations Report

---

## ⏱️ Timeline

- **Get saved search ID:** 15 minutes (email to accountant)
- **Deploy RESTlet:** 30 minutes
- **Update connector code:** 1 hour
- **Test and deploy:** 30 minutes
- **Total:** 2-3 hours

---

**This is the correct solution for automating NetSuite data extraction!**

We bypass the SuiteQL issues entirely by using the exact same saved search that generates the CSV files.

**Next action:** Get the saved search ID from your accountant, then we implement this in the next session.
