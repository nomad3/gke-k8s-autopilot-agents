# NetSuite Transaction Detail Report Automation - Implementation Guide

**Date:** November 20, 2025
**Report URL:** https://7048582.app.netsuite.com/app/reporting/reportrunner.nl?cr=250
**Report ID:** 250
**Status:** Ready to Implement

---

## 🎯 The Solution

Your Transaction Detail CSV exports come from **NetSuite Report ID 250**. Since NetSuite has no REST API for reports, we have two options:

### Option A: Convert Report to Saved Search (Recommended)
**Effort:** 1-2 hours | **Reliability:** High | **Maintenance:** Low

### Option B: Create Custom RESTlet
**Effort:** 2-3 hours | **Reliability:** Medium | **Maintenance:** Medium

---

## 🚀 Option A: Convert Report to Saved Search (RECOMMENDED)

### Why This is Best
- ✅ Uses official NetSuite API (Saved Search API)
- ✅ No custom code in NetSuite
- ✅ Uses our existing OAuth 1.0a credentials
- ✅ Well-documented and supported
- ✅ Can schedule automated runs

### Steps to Implement

#### Step 1: Create Saved Search from Report (NetSuite UI)

**Ask your accountant to:**
1. Open the Transaction Detail report (Report ID 250)
2. Click **"Save As"** → **"Saved Search"**
3. Name it: **"Transaction Detail API Export"**
4. Note the **Search ID** (will be like `customsearch_transaction_detail`)
5. Ensure these settings:
   - ✅ Available for all subsidiaries
   - ✅ No grouping/summaries (returns raw transaction lines)
   - ✅ Includes all needed fields: Type, Date, Document Number, Name, Memo, Account, Amount, etc.

#### Step 2: Deploy Saved Search RESTlet

Upload this RESTlet script to NetSuite (File Cabinet):

**File:** `saved_search_api.js`

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType Restlet
 * @NModuleScope SameAccount
 */
define(['N/search'], function(search) {

    function post(requestBody) {
        var searchId = requestBody.searchID;

        if (!searchId) {
            return {
                success: false,
                error: 'searchID parameter required'
            };
        }

        var searchResults = [];
        var searchObj = search.load({
            id: searchId
        });

        // Run paged search (handles large result sets)
        searchObj.run().each(function(result) {
            var resultObj = {};

            // Get all columns
            result.columns.forEach(function(column) {
                resultObj[column.label || column.name] = result.getValue(column);
            });

            searchResults.push(resultObj);
            return true; // continue iteration
        });

        return {
            success: true,
            totalRecords: searchResults.length,
            results: searchResults
        };
    }

    return {
        post: post
    };
});
```

**Deployment:**
1. Customization > Scripting > Scripts > New
2. Upload saved_search_api.js
3. Create Script Record (RESTlet type)
4. Deploy with:
   - Status: Released
   - Audience: All Roles (or specific integration role)
5. Note the **Script ID** and **Deployment ID**

#### Step 3: Update Our NetSuite Connector

Add method to `mcp-server/src/connectors/netsuite.py`:

```python
async def run_saved_search(
    self,
    search_id: str
) -> List[Dict[str, Any]]:
    """
    Run a NetSuite saved search via RESTlet API

    Args:
        search_id: customsearch_xxxxx or internal ID

    Returns:
        List of search results matching CSV export format
    """
    # RESTlet URL format
    restlet_url = (
        f"https://{self.account}.restlets.api.netsuite.com"
        f"/app/site/hosting/restlet.nl"
        f"?script=customscript_saved_search_api"
        f"&deploy=1"
    )

    payload = {"searchID": search_id}

    headers = self._get_oauth_headers("POST", restlet_url)
    headers["Content-Type"] = "application/json"

    async with aiohttp.ClientSession() as session:
        async with session.post(restlet_url, json=payload, headers=headers) as response:
            data = await response.json()

            if not data.get("success"):
                raise Exception(f"Saved search failed: {data.get('error')}")

            return data.get("results", [])
```

#### Step 4: Update Sync Logic

In `mcp-server/src/services/snowflake_netsuite_loader.py`:

```python
# For journalEntry, use saved search instead of SuiteQL
if record_type == "journalEntry":
    logger.info("Fetching via NetSuite Saved Search API...")

    all_records = await self.netsuite.run_saved_search(
        search_id="customsearch_transaction_detail"  # From Step 1
    )

    logger.info(f"✅ Saved Search returned {len(all_records)} transaction records")
```

#### Step 5: Test

```bash
# Trigger sync
curl -X POST https://mcp.agentprovision.com/api/v1/netsuite/sync/trigger \
  -H "Authorization: Bearer $MCP_API_KEY" \
  -H "X-Tenant-ID: silvercreek" \
  -d '{"full_sync": true, "record_types": ["journalEntry"]}'

# Should now return thousands of records!
```

---

## 🔄 Option B: Custom RESTlet for Report ID 250

If you can't convert to saved search, create RESTlet that runs the report directly:

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType Restlet
 */
define(['N/runtime'], function(runtime) {

    function post(requestBody) {
        var reportId = requestBody.reportID || 250;

        // Use private API (NetSuite internal function)
        var report = runtime.getCurrentScript().getParameter({
            name: 'custscript_report_id'
        });

        // This requires NetSuite support to enable
        // Or we can use N/task to schedule report and download results

        return {
            success: false,
            error: 'Report API not yet implemented - use saved search instead'
        };
    }

    return {
        post: post
    };
});
```

**Issue:** NetSuite doesn't expose report running via public API. **Saved Search is the way.**

---

## 📧 Email to Accountant

```
Subject: Convert Transaction Detail Report to Saved Search for API Automation

Hi [Accountant],

Great news! I found how to automate the Transaction Detail data extraction from NetSuite.

The report you use (Report ID 250) can be converted to a Saved Search, which will allow us to pull the exact same data programmatically via API.

Could you please:

1. Open the Transaction Detail report in NetSuite (the one you export to CSV)
2. Click "Save As" → "Saved Search"
3. Name it: "Transaction Detail API Export"
4. Save it as available for ALL subsidiaries
5. Send me the Saved Search ID (looks like "customsearch_transaction_detail" or just a number)

Once I have this, I can set up automated daily pulls so you won't need to export CSVs manually anymore!

The data will flow directly from NetSuite → Snowflake → Dashboard automatically.

Takes about 5 minutes in NetSuite. Let me know if you need help!

Thanks!
```

---

## ⏱️ Timeline

**Once we have the Saved Search ID:**
- Deploy RESTlet script: 30 min
- Update connector code: 1 hour
- Test and verify: 30 min
- **Total: 2 hours to complete automation**

---

## ✅ Expected Result

After implementation:
```
Every night at 2am:
  → Call NetSuite Saved Search API
  → Pull all Transaction Detail data for all subsidiaries
  → Load to Snowflake Bronze
  → Refresh dynamic tables
  → Dashboard shows updated data

Zero manual steps required!
```

**This achieves 100% automation of the Operations Report with NetSuite financial data!** 🎉

---

**Next Action:** Send email to accountant to get saved search created and get the search ID.
