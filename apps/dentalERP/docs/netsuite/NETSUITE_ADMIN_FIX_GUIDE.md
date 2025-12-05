# NetSuite Administrator Fix Guide
**Issue:** Broken SuiteApp blocking journal entry API access
**Date:** November 9, 2025
**Priority:** CRITICAL - Blocks all financial data sync

---

## Problem Summary

**Error:** Every attempt to fetch journal entry details returns:
```json
{
  "type": "error.SuiteScriptError",
  "name": "SSS_SEARCH_ERROR_OCCURRED",
  "message": "Search error occurred: Record 'CUSTOMRECORD_VID_TEMPLATE' was not found.",
  "stack": [
    "VID_DistributionTemplateGateway.runQuery (/SuiteApps/com.netsuite.vendorinvoicedistribution/app/common/gateways/BaseGateway.js:305:32)",
    "VID_DistributionTemplateGateway.getAllTemplateList (/SuiteApps/com.netsuite.vendorinvoicedistribution/app/common/gateways/BaseGateway.js:382:25)"
  ]
}
```

**Root Cause:**
- SuiteApp: **Vendor Invoice Distribution** (`com.netsuite.vendorinvoicedistribution`)
- Broken script executes on journal entry GET requests (User Event or Client Script)
- Script searches for custom record `CUSTOMRECORD_VID_TEMPLATE` which doesn't exist
- **Blocks 100% of journal entry detail API calls**

---

## Fix Options (Choose One)

### Option 1: Disable the Vendor Invoice Distribution SuiteApp (Fastest)

**If you don't need this SuiteApp:**

1. Go to **Setup → SuiteApp → Manage SuiteApps**
2. Search for "Vendor Invoice Distribution" or "VID"
3. Find SuiteApp ID: `com.netsuite.vendorinvoicedistribution`
4. Click **Disable** or **Uninstall**
5. Confirm the change

**Time:** 2 minutes

**Test:** Run our test script again to see if journal entries are accessible

---

### Option 2: Fix the Missing Custom Record

**If you need the SuiteApp:**

1. Go to **Customization → Lists, Records, & Fields → Record Types**
2. Search for `CUSTOMRECORD_VID_TEMPLATE` or "VID Template"
3. **If it doesn't exist:**
   - Create new custom record type
   - Script ID: `customrecord_vid_template`
   - Name: "VID Distribution Template" (or similar)
   - Add any required fields the script expects

4. **If it exists but is inactive:**
   - Click on it
   - Check "Is Available" checkbox
   - Save

**Time:** 5-10 minutes

---

### Option 3: Disable Specific Script Trigger

**If SuiteApp is needed but script is broken:**

1. Go to **Customization → Scripting → Scripts**
2. Search for scripts in `vendorinvoicedistribution` bundle
3. Look for:
   - User Event Scripts on "Journal Entry" record
   - Client Scripts on "Journal Entry"
   - Scripts with "DistributionTemplateGateway" in the name

4. For each script found:
   - Click on the script
   - Go to **Deployments** tab
   - Change Status to **Testing** or **Not Deployed**
   - Save

5. Specifically look for scripts that trigger on:
   - `beforeLoad`
   - `afterSubmit`
   - `onView`

**Time:** 10-15 minutes

---

## Verification Steps

After applying any fix above, **test immediately**:

### Step 1: Test One Journal Entry via API

I can run this test for you - just tell me when you've made the NetSuite change:

```bash
# This will test fetching journal entry 24708 with expandSubResources=true
# Should return full journal entry with line items
```

**Expected Success:**
```
✅ Got response
✅✅✅ HAS 'line' field with N items
First line keys: ['account', 'debit', 'credit', 'entity', ...]
```

**If Still Failing:**
- You'll see the same CUSTOMRECORD_VID_TEMPLATE error
- Try next option

---

### Step 2: Trigger Small Sync

Once journal entry detail fetch works:

```bash
curl -X POST 'https://mcp.agentprovision.com/api/v1/netsuite/sync/trigger' \
  -H "Authorization: Bearer prod-mcp-api-key-change-in-production-min-32-chars-secure" \
  -H "X-Tenant-ID: default" \
  -H "Content-Type: application/json" \
  -d '{"record_types": ["journalEntry"], "full_sync": false, "limit": 5}'
```

**Expected:** Sync completes with journal entries that have line items

---

## Additional Diagnostic Info for NetSuite Support

**Account ID:** 7048582
**Failing Endpoint:** `GET /services/rest/record/v1/journalEntry/{id}?expandSubResources=true`
**Affected Record Type:** Journal Entry
**SuiteApp Bundle:** com.netsuite.vendorinvoicedistribution
**Script File:** `/SuiteApps/com.netsuite.vendorinvoicedistribution/app/common/gateways/BaseGateway.js`
**Failing Function:** `VID_DistributionTemplateGateway.runQuery()` at line 305
**Missing Object:** Custom Record Type `CUSTOMRECORD_VID_TEMPLATE`

**Impact:**
- Blocks REST API access to journal entry line items
- Prevents financial data sync to Snowflake
- Affects all financial analytics dashboards

---

## Quick Decision Matrix

| Scenario | Recommended Action | Time |
|----------|-------------------|------|
| Don't use Vendor Invoice Distribution | Option 1: Disable SuiteApp | 2 min |
| Need VID but record is missing | Option 2: Create custom record | 10 min |
| Need VID and it worked before | Option 3: Disable broken script | 15 min |
| Unsure about VID | Option 1 first (can re-enable later) | 2 min |

---

## Next Steps After Fix

Once you've fixed the NetSuite issue, let me know and I will:

1. ✅ Run test script to verify journal entries return line items
2. ✅ Trigger sync to populate Bronze layer with financial transaction details
3. ✅ Verify data flows through Silver → Gold layers
4. ✅ Test financial API endpoints return data
5. ✅ Confirm dashboard shows financial metrics

**Total time to complete after NetSuite fix:** 15-20 minutes

---

**Which option do you want to try first?**
