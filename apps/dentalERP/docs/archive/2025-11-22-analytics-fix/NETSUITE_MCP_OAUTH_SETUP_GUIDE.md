# NetSuite MCP Standard Tools - OAuth 2.0 Setup Guide

**Goal:** Set up OAuth 2.0 credentials to call the MCP Standard Tools SuiteApp programmatically

**Time:** 15-20 minutes in NetSuite UI

---

## Part 1: Create OAuth 2.0 Integration Record

### Step 1: Create Integration

1. Log into NetSuite as Administrator
2. Go to: **Setup > Integration > Manage Integrations > New**
3. Fill in:
   - **Name:** `DentalERP MCP Integration`
   - **State:** **Enabled**
   - **Client Credentials (Machine to Machine) Grant:** ✅ **CHECK THIS BOX**
   - **Scope:** `mcp` (or leave default)
   - **Redirect URI:** Not needed for M2M
4. Click **Save**

### Step 2: Copy Client Credentials

**IMPORTANT:** After clicking Save, you'll see:
- **Client ID:** (copy this - looks like: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`)
- **Client Secret:** (copy this - **ONLY SHOWN ONCE!**)

**Save these immediately!** The client secret will NOT be shown again.

Example:
```
Client ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
Client Secret: xYz123AbC456DeF789GhI012JkL345MnO678
```

---

## Part 2: Create OAuth 2.0 Client Credentials Mapping

### Step 3: Map Integration to User/Role

1. Go to: **Setup > Integration > OAuth 2.0 Client Credentials (M2M) Setup**
2. Click **New**
3. Fill in:
   - **User:** Your integration user (or your admin user)
   - **Role:** Administrator (or custom MCP role)
   - **Application:** Select **"DentalERP MCP Integration"** (from Step 1)
4. Click **Save**

This maps the client credentials to a specific user and role in NetSuite.

---

## Part 3: Get Access Token

### Step 4: Generate Bearer Token via API

You'll use the client credentials to get an access token via OAuth 2.0 Client Credentials flow.

**Token Endpoint:**
```
https://7048582.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token
```

**Request:**
```bash
curl -X POST "https://7048582.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Copy the access_token** - this is your Bearer token!

---

## Part 4: Test MCP Connection

### Step 5: Test runCustomSuiteQL

**MCP Endpoint:**
```
https://7048582.suitetalk.api.netsuite.com/services/mcp/v1/all
```

**JSON-RPC Request:**
```json
{
  "jsonrpc": "2.0",
  "id": "test-1",
  "method": "tools/call",
  "params": {
    "name": "runCustomSuiteQL",
    "arguments": {
      "sqlQuery": "SELECT COUNT(*) as record_count FROM account",
      "description": "Test query to count accounts"
    }
  }
}
```

**Full cURL Test:**
```bash
# Get token first
TOKEN=$(curl -X POST "https://7048582.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" | jq -r '.access_token')

# Call MCP tool
curl -X POST "https://7048582.suitetalk.api.netsuite.com/services/mcp/v1/all" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test-1",
    "method": "tools/call",
    "params": {
      "name": "runCustomSuiteQL",
      "arguments": {
        "sqlQuery": "SELECT COUNT(*) FROM account"
      }
    }
  }'
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": "test-1",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Query results: [{'record_count': 413}]"
      }
    ]
  }
}
```

---

## Part 5: Query Transaction Data

### Step 6: Test TransactionAccountingLine Query

```bash
curl -X POST "https://7048582.suitetalk.api.netsuite.com/services/mcp/v1/all" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "txn-query",
    "method": "tools/call",
    "params": {
      "name": "runCustomSuiteQL",
      "arguments": {
        "sqlQuery": "SELECT t.id, t.tranid, t.trandate, BUILTIN.DF(t.subsidiary) AS subsidiary, tal.debit, tal.credit, BUILTIN.DF(tal.account) AS account FROM transaction t INNER JOIN transactionaccountingline tal ON tal.transaction = t.id WHERE t.trandate >= TO_DATE('\''2025-01-01'\'', '\''YYYY-MM-DD'\'') AND tal.posting = '\''T'\'' LIMIT 10"
      }
    }
  }'
```

If this returns data, **THE MCP INTEGRATION WORKS!**

---

## 📋 What to Send Me

After completing Steps 1-4:

```
Client ID: [your-client-id]
Client Secret: [your-client-secret]
Access Token (for testing): [bearer-token]
```

I'll add these to `mcp-server/.env`:
```bash
NETSUITE_MCP_CLIENT_ID=your-client-id
NETSUITE_MCP_CLIENT_SECRET=your-client-secret
```

And implement the MCP client connector!

---

## ⏱️ Timeline

**Your time (NetSuite UI):** 15 minutes
- Create integration record
- Create M2M mapping
- Copy credentials

**My time (Implementation):** 3-4 hours
- Implement OAuth 2.0 token management
- Create JSON-RPC client
- Add MCP connector to sync pipeline
- Test and verify

**Result:** Fully automated NetSuite transaction data pull via official MCP SuiteApp!

---

## ✅ Why This Will Work

1. ✅ You already have MCP Standard Tools installed
2. ✅ Official NetSuite integration (not experimental)
3. ✅ `runCustomSuiteQL` tool can query TransactionAccountingLine
4. ✅ Returns same data as CSV exports
5. ✅ OAuth 2.0 Client Credentials (server-to-server, no manual auth)
6. ✅ Can schedule automated syncs

**This is the official NetSuite automation solution!**
