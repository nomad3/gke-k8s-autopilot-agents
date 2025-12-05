# NetSuite Saved Search Setup - Step-by-Step Guide for Admin

**Goal:** Convert your Transaction Detail Report (ID 250) to a Saved Search so we can call it via API

**Time:** 10-15 minutes

---

## Part 1: Create Saved Search from Report

### Step 1: Open the Transaction Detail Report

1. Log into NetSuite
2. Navigate to: **Reports > Financial > Transaction Detail**
   - OR directly go to: `https://7048582.app.netsuite.com/app/reporting/reportrunner.nl?cr=250`

### Step 2: Run the Report

1. Select a subsidiary (e.g., "SCDP Eastlake, LLC")
2. Set date range (e.g., Jan 1, 2025 - Nov 30, 2025)
3. Click **"Refresh"** to run the report
4. Verify you see transaction data

### Step 3: Convert to Saved Search

1. Look for **"Save"** or **"Actions"** menu in the report
2. Click **"Save As Saved Search"** or **"Create Saved Search"**

   **If that option doesn't exist:**
   - Note the columns shown in the report
   - Go to Lists > Search > Saved Searches > New
   - Create a new Transaction search manually (see Part 2 below)

### Step 4: Configure the Saved Search

**Search Name:** `Transaction Detail API Export`

**Search Type:** Transaction

**Criteria Tab:**
- Main Line: **is false** (get detail lines, not summary)
- Subsidiary: **any of** [leave blank or select all]
- Posting: **is true** (posted transactions only)
- Date: **on or after** 1/1/2025 (or leave blank for all historical data)

**Results Tab - Add these columns:**
- Type
- Date
- Document Number
- Name (Entity)
- Memo
- Account
- Amount (or Debit/Credit)
- Subsidiary

**Available For:**
- ✅ Check "Public" or "All Roles"
- This allows API access

**Save the search!**

### Step 5: Get the Saved Search ID

After saving:
1. The URL will change to show the search ID
2. Look for `id=` in the URL
3. It will be either:
   - A number like `1234` (internal ID)
   - Or `customsearch_xxxxx` (script ID)

**Copy this ID - we need it for the API!**

Example URL after save:
```
https://7048582.app.netsuite.com/app/common/search/search.nl?id=customsearch_transaction_detail
```

The ID is: `customsearch_transaction_detail`

---

## Part 2: Create Saved Search Manually (If "Save As" Doesn't Work)

### Step 1: Create New Saved Search

1. Go to: **Lists > Search > Saved Searches > New**
2. Select **Transaction** as the search type
3. Click **Create**

### Step 2: Set Criteria

**Criteria Tab - Add these filters:**

| Field | Operator | Value |
|-------|----------|-------|
| Main Line | is | False |
| Posting | is | True |
| Type | any of | (leave all checked or select specific types) |
| Date | on or after | 1/1/2025 (or leave blank) |

### Step 3: Set Results Columns

**Results Tab - Add these columns in order:**

1. **Type** (Formula: Text)
2. **Date** (Transaction Date)
3. **Document Number**
4. **Name** (Entity Name)
5. **Memo**
6. **Account** (Account Display Name)
7. **Debit Amount**
8. **Credit Amount**
9. **Amount** (Formula: {debitamount} - {creditamount})
10. **Subsidiary** (Subsidiary Name)

### Step 4: Set Availability

1. **Available** tab
2. Check: **"Public"** or **"All Roles"**
3. This is CRITICAL for API access!

### Step 5: Save and Get ID

1. Click **Save**
2. Name: `Transaction Detail API Export`
3. ID: `customsearch_transaction_detail_api` (or let NetSuite auto-generate)
4. Copy the ID from the URL

---

## Part 3: Deploy RESTlet for API Access

### Step 1: Create RESTlet Script File

1. Go to: **Documents > Files > SuiteScripts**
2. Click **Add File**
3. Name: `saved_search_api.js`
4. Paste this code:

```javascript
/**
 * @NApiVersion 2.1
 * @NScriptType Restlet
 * @NModuleScope SameAccount
 */
define(['N/search'], function(search) {

    /**
     * POST handler to run saved search
     * @param {Object} requestBody - {searchID: 'customsearch_xxx'}
     * @returns {Object} {success, totalRecords, results}
     */
    function post(requestBody) {
        try {
            var searchId = requestBody.searchID;

            if (!searchId) {
                return {
                    success: false,
                    error: 'searchID parameter required'
                };
            }

            log.audit('Running Saved Search', 'Search ID: ' + searchId);

            var searchResults = [];
            var searchObj = search.load({
                id: searchId
            });

            // Run paged search
            var pagedData = searchObj.runPaged({
                pageSize: 1000
            });

            log.audit('Search Stats', 'Total: ' + pagedData.count + ' pages: ' + pagedData.pageRanges.length);

            // Iterate through pages
            pagedData.pageRanges.forEach(function(pageRange) {
                var page = pagedData.fetch({index: pageRange.index});

                page.data.forEach(function(result) {
                    var resultObj = {};

                    // Get all columns
                    result.columns.forEach(function(column) {
                        var label = column.label || column.name;
                        resultObj[label] = result.getValue(column);
                    });

                    searchResults.push(resultObj);
                });
            });

            log.audit('Search Complete', 'Records: ' + searchResults.length);

            return {
                success: true,
                totalRecords: searchResults.length,
                results: searchResults
            };

        } catch (e) {
            log.error('Search Error', e.toString());
            return {
                success: false,
                error: e.toString()
            };
        }
    }

    return {
        post: post
    };
});
```

5. Click **Save**

### Step 2: Create Script Record

1. Go to: **Customization > Scripting > Scripts > New**
2. Click **Browse** and select `saved_search_api.js`
3. Click **Create Script Record**
4. Fill in:
   - **Name:** Saved Search API
   - **ID:** `customscript_saved_search_api`
   - **Audience:** All Roles (or specific integration role)
5. Click **Save**

### Step 3: Deploy the Script

1. On the Script page, go to **Deployments** tab
2. Click **Add Deployment**
3. Fill in:
   - **Title:** Saved Search API Deployment
   - **ID:** `customdeploy_saved_search_api` (or let it auto-generate)
   - **Status:** **Released**
   - **Audience:** All Roles
4. Click **Save**

### Step 4: Get the RESTlet URL

After deployment, the URL will be:
```
https://7048582.restlets.api.netsuite.com/app/site/hosting/restlet.nl?script=customscript_saved_search_api&deploy=1
```

**Copy this URL - we need it!**

---

## Part 4: Test the Setup

### Option A: Test in Browser

1. Go to the RESTlet URL in a browser (will require login)
2. POST this JSON:
```json
{"searchID": "customsearch_transaction_detail_api"}
```

### Option B: Test with Our API

Once you send me:
- Saved Search ID
- RESTlet Script ID
- RESTlet Deployment ID

I can update the code and test immediately!

---

## 📋 What to Send Me

After completing the above:

```
Saved Search ID: customsearch_transaction_detail_api (or whatever ID was generated)
RESTlet Script ID: customscript_saved_search_api
RESTlet Deployment ID: customdeploy_saved_search_api (or deployment ID)
RESTlet URL: https://7048582.restlets.api.netsuite.com/app/site/hosting/restlet.nl?script=customscript_saved_search_api&deploy=1
```

---

## 🎯 Expected Result

Once implemented:
```
Daily at 2am:
  → API calls RESTlet
  → RESTlet runs saved search
  → Returns all Transaction Detail data
  → Loads to Snowflake
  → Dashboard auto-updates

ZERO manual CSV exports needed!
```

**This completes the automation of the Operations Report!** 🎉

---

## ⏱️ Your Time: 15 minutes
## My Time (next session): 2 hours
## Result: Complete automation

Let me know once you have the saved search created and I'll implement the API integration!
