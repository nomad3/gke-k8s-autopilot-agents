# NetSuite MCP SuiteApp Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement automated NetSuite transaction data extraction using the MCP Standard Tools SuiteApp (com.netsuite.mcpstandardtools v1.0.4) to replace manual CSV exports and fully automate the Operations Report.

**Architecture:** Create OAuth 2.0 client credentials flow for server-to-server authentication, implement JSON-RPC 2.0 client to call runCustomSuiteQL tool, query TransactionAccountingLine table for complete financial data, load to Snowflake Bronze layer, integrate with existing sync pipeline.

**Tech Stack:** Python 3.11, FastAPI, aiohttp, NetSuite MCP Standard Tools SuiteApp, OAuth 2.0 Client Credentials, JSON-RPC 2.0, Snowflake

---

## Prerequisites

**User must complete in NetSuite UI (15 minutes):**
1. Create OAuth 2.0 integration record (Setup > Integration > Manage Integrations > New)
   - Name: "DentalERP MCP Integration"
   - Enable "Client Credentials (M2M) Grant"
   - Save and copy Client ID + Client Secret
2. Create OAuth 2.0 M2M mapping (Setup > Integration > OAuth 2.0 Client Credentials Setup)
   - Map integration to Administrator role
3. Provide: Client ID and Client Secret

**Follow guide:** `NETSUITE_MCP_OAUTH_SETUP_GUIDE.md`

---

## Task 1: Add OAuth 2.0 Credentials to Environment

**Files:**
- Modify: `mcp-server/.env`

**Step 1: Add MCP OAuth 2.0 credentials**

Add these lines to `mcp-server/.env`:

```bash
# NetSuite MCP Standard Tools OAuth 2.0 (Client Credentials M2M)
NETSUITE_MCP_CLIENT_ID=your-client-id-from-netsuite
NETSUITE_MCP_CLIENT_SECRET=your-client-secret-from-netsuite
NETSUITE_MCP_ENDPOINT=https://7048582.suitetalk.api.netsuite.com/services/mcp/v1/all
NETSUITE_MCP_TOKEN_ENDPOINT=https://7048582.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token
```

**Step 2: Verify credentials are set**

Run:
```bash
cd mcp-server
grep NETSUITE_MCP .env
```

Expected: Shows 4 new NETSUITE_MCP_* variables

**Step 3: Commit**

```bash
git add mcp-server/.env.example
git commit -m "feat: add NetSuite MCP OAuth 2.0 environment variables

Added OAuth 2.0 client credentials configuration for NetSuite MCP
Standard Tools integration.

Environment variables:
- NETSUITE_MCP_CLIENT_ID
- NETSUITE_MCP_CLIENT_SECRET
- NETSUITE_MCP_ENDPOINT
- NETSUITE_MCP_TOKEN_ENDPOINT

Note: Actual credentials in .env (not committed)"
```

---

## Task 2: Create OAuth 2.0 Token Manager

**Files:**
- Create: `mcp-server/src/auth/netsuite_oauth2.py`

**Step 1: Write test for token fetching**

Create: `mcp-server/tests/test_netsuite_oauth2.py`

```python
import pytest
from src.auth.netsuite_oauth2 import NetSuiteOAuth2TokenManager
import os
from dotenv import load_dotenv

load_dotenv()

@pytest.mark.asyncio
async def test_get_access_token():
    """Test OAuth 2.0 token fetch from NetSuite"""
    manager = NetSuiteOAuth2TokenManager(
        client_id=os.getenv('NETSUITE_MCP_CLIENT_ID'),
        client_secret=os.getenv('NETSUITE_MCP_CLIENT_SECRET'),
        token_endpoint=os.getenv('NETSUITE_MCP_TOKEN_ENDPOINT')
    )

    token = await manager.get_access_token()

    assert token is not None
    assert len(token) > 20
    assert token.startswith('eyJ')  # JWT format

@pytest.mark.asyncio
async def test_token_caching():
    """Test token is cached and not re-fetched unnecessarily"""
    manager = NetSuiteOAuth2TokenManager(
        client_id=os.getenv('NETSUITE_MCP_CLIENT_ID'),
        client_secret=os.getenv('NETSUITE_MCP_CLIENT_SECRET'),
        token_endpoint=os.getenv('NETSUITE_MCP_TOKEN_ENDPOINT')
    )

    token1 = await manager.get_access_token()
    token2 = await manager.get_access_token()

    # Should return same token (cached)
    assert token1 == token2
```

**Step 2: Run test to verify it fails**

Run:
```bash
cd mcp-server
pytest tests/test_netsuite_oauth2.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.auth.netsuite_oauth2'"

**Step 3: Create OAuth 2.0 token manager**

Create: `mcp-server/src/auth/__init__.py` (empty file)

Create: `mcp-server/src/auth/netsuite_oauth2.py`

```python
"""
NetSuite OAuth 2.0 Client Credentials (M2M) Token Manager
For NetSuite MCP Standard Tools integration
"""

import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from ..utils.logger import logger


class NetSuiteOAuth2TokenManager:
    """
    Manages OAuth 2.0 access tokens for NetSuite MCP API

    Uses Client Credentials (M2M) grant type for server-to-server auth
    Caches tokens and auto-refreshes before expiration
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_endpoint: str
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_endpoint = token_endpoint

        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    async def get_access_token(self) -> str:
        """
        Get valid access token, fetching new one if needed

        Returns:
            Bearer token for Authorization header
        """
        # Check if we have cached token that's still valid
        if self._access_token and self._token_expires_at:
            # Refresh if within 5 minutes of expiry
            if datetime.utcnow() < (self._token_expires_at - timedelta(minutes=5)):
                logger.debug("[NetSuite OAuth 2.0] Using cached token")
                return self._access_token

        # Fetch new token
        logger.info("[NetSuite OAuth 2.0] Fetching new access token")

        async with aiohttp.ClientSession() as session:
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            async with session.post(
                self.token_endpoint,
                data=data,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(
                        f"Failed to get OAuth 2.0 token: {response.status} - {error_text}"
                    )

                result = await response.json()

                self._access_token = result['access_token']
                expires_in = result.get('expires_in', 3600)  # Default 1 hour
                self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

                logger.info(
                    f"[NetSuite OAuth 2.0] Token acquired, expires in {expires_in}s"
                )

                return self._access_token

    async def invalidate_token(self):
        """Force token refresh on next request"""
        self._access_token = None
        self._token_expires_at = None
        logger.info("[NetSuite OAuth 2.0] Token invalidated")
```

**Step 4: Run test to verify it passes**

Run:
```bash
cd mcp-server
pytest tests/test_netsuite_oauth2.py -v
```

Expected: PASS (both tests)

**Step 5: Commit**

```bash
git add mcp-server/src/auth/ mcp-server/tests/test_netsuite_oauth2.py mcp-server/.env.example
git commit -m "feat: add NetSuite OAuth 2.0 token manager for MCP integration

Implements OAuth 2.0 Client Credentials (M2M) flow for NetSuite MCP
Standard Tools API access.

Features:
- Token caching with auto-refresh
- Client credentials grant type
- Async aiohttp client
- 5-minute pre-expiry refresh

Tested with pytest to verify token fetch and caching behavior."
```

---

## Task 3: Create MCP JSON-RPC Client

**Files:**
- Create: `mcp-server/src/connectors/netsuite_mcp.py`

**Step 1: Write test for MCP JSON-RPC call**

Create: `mcp-server/tests/test_netsuite_mcp.py`

```python
import pytest
from src.connectors.netsuite_mcp import NetSuiteMCPConnector
import os
from dotenv import load_dotenv

load_dotenv()

@pytest.mark.asyncio
async def test_list_tools():
    """Test listing available MCP tools"""
    mcp = NetSuiteMCPConnector(
        account_id=os.getenv('NETSUITE_ACCOUNT_ID'),
        client_id=os.getenv('NETSUITE_MCP_CLIENT_ID'),
        client_secret=os.getenv('NETSUITE_MCP_CLIENT_SECRET')
    )

    tools = await mcp.list_tools()

    assert isinstance(tools, list)
    assert len(tools) > 0

    # Check for runCustomSuiteQL tool
    tool_names = [t.get('name') for t in tools]
    assert 'runCustomSuiteQL' in tool_names

@pytest.mark.asyncio
async def test_run_suiteql():
    """Test running SuiteQL query via MCP"""
    mcp = NetSuiteMCPConnector(
        account_id=os.getenv('NETSUITE_ACCOUNT_ID'),
        client_id=os.getenv('NETSUITE_MCP_CLIENT_ID'),
        client_secret=os.getenv('NETSUITE_MCP_CLIENT_SECRET')
    )

    # Simple query to test connection
    result = await mcp.run_suiteql("SELECT COUNT(*) as account_count FROM account")

    assert result is not None
    assert isinstance(result, list)
    assert len(result) > 0
    assert 'account_count' in result[0]
```

**Step 2: Run test to verify it fails**

Run:
```bash
cd mcp-server
pytest tests/test_netsuite_mcp.py::test_list_tools -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.connectors.netsuite_mcp'"

**Step 3: Implement MCP JSON-RPC client**

Create: `mcp-server/src/connectors/netsuite_mcp.py`

```python
"""
NetSuite MCP Standard Tools JSON-RPC Client

Connects to NetSuite MCP Standard Tools SuiteApp via JSON-RPC 2.0
Uses OAuth 2.0 Client Credentials for authentication
"""

import aiohttp
import uuid
from typing import Dict, List, Any, Optional
from ..auth.netsuite_oauth2 import NetSuiteOAuth2TokenManager
from ..utils.logger import logger


class NetSuiteMCPConnector:
    """
    Client for NetSuite MCP Standard Tools SuiteApp

    Provides methods to call MCP tools like runCustomSuiteQL via JSON-RPC 2.0
    """

    def __init__(
        self,
        account_id: str,
        client_id: str,
        client_secret: str
    ):
        self.account_id = account_id
        self.mcp_endpoint = f"https://{account_id}.suitetalk.api.netsuite.com/services/mcp/v1/all"
        self.token_endpoint = f"https://{account_id}.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token"

        # Initialize token manager
        self.token_manager = NetSuiteOAuth2TokenManager(
            client_id=client_id,
            client_secret=client_secret,
            token_endpoint=self.token_endpoint
        )

    async def _make_jsonrpc_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make JSON-RPC 2.0 request to NetSuite MCP endpoint

        Args:
            method: JSON-RPC method (e.g., 'tools/list', 'tools/call')
            params: Method parameters

        Returns:
            JSON-RPC result object
        """
        # Get valid access token
        access_token = await self.token_manager.get_access_token()

        # Build JSON-RPC request
        request_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        logger.debug(f"[NetSuite MCP] JSON-RPC request: {method}")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.mcp_endpoint,
                json=payload,
                headers=headers
            ) as response:
                if response.status == 401:
                    # Token expired, invalidate and retry once
                    logger.warning("[NetSuite MCP] 401 Unauthorized, refreshing token")
                    await self.token_manager.invalidate_token()
                    access_token = await self.token_manager.get_access_token()
                    headers["Authorization"] = f"Bearer {access_token}"

                    async with session.post(
                        self.mcp_endpoint,
                        json=payload,
                        headers=headers
                    ) as retry_response:
                        if retry_response.status != 200:
                            error_text = await retry_response.text()
                            raise Exception(
                                f"MCP request failed after retry: {retry_response.status} - {error_text}"
                            )
                        result = await retry_response.json()

                elif response.status != 200:
                    error_text = await response.text()
                    raise Exception(
                        f"MCP request failed: {response.status} - {error_text}"
                    )
                else:
                    result = await response.json()

                # Check for JSON-RPC error
                if "error" in result:
                    raise Exception(f"JSON-RPC error: {result['error']}")

                return result.get("result", {})

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available MCP tools

        Returns:
            List of tool definitions
        """
        logger.info("[NetSuite MCP] Listing available tools")

        result = await self._make_jsonrpc_request("tools/list")

        tools = result.get("tools", [])
        logger.info(f"[NetSuite MCP] Found {len(tools)} available tools")

        return tools

    async def run_suiteql(
        self,
        query: str,
        description: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Run SuiteQL query via runCustomSuiteQL MCP tool

        Args:
            query: SuiteQL query string (read-only)
            description: Optional query description

        Returns:
            List of query result rows as dictionaries
        """
        logger.info(f"[NetSuite MCP] Running SuiteQL: {query[:100]}...")

        params = {
            "name": "runCustomSuiteQL",
            "arguments": {
                "sqlQuery": query
            }
        }

        if description:
            params["arguments"]["description"] = description

        result = await self._make_jsonrpc_request("tools/call", params)

        # MCP returns results in content array with text
        # Parse the results from the response
        content = result.get("content", [])

        if not content:
            logger.warning("[NetSuite MCP] No content in response")
            return []

        # Extract text from first content item
        result_text = content[0].get("text", "") if content else ""

        # Parse results (MCP returns as string, need to parse)
        # Format: "Query results: [{'col1': 'val1'}, ...]"
        if "Query results:" in result_text:
            import json
            import re
            match = re.search(r'\[(.*)\]', result_text, re.DOTALL)
            if match:
                # Convert string representation to actual list
                results_str = f"[{match.group(1)}]"
                results = eval(results_str)  # Safe because it's from NetSuite
                logger.info(f"[NetSuite MCP] Query returned {len(results)} rows")
                return results

        logger.warning(f"[NetSuite MCP] Could not parse results: {result_text[:200]}")
        return []
```

**Step 4: Run test to verify it passes**

Run:
```bash
cd mcp-server
pytest tests/test_netsuite_mcp.py::test_list_tools -v
```

Expected: PASS (should list tools including runCustomSuiteQL)

Run:
```bash
pytest tests/test_netsuite_mcp.py::test_run_suiteql -v
```

Expected: PASS (should return account count ~413)

**Step 5: Commit**

```bash
git add mcp-server/src/auth/netsuite_oauth2.py mcp-server/src/connectors/netsuite_mcp.py mcp-server/tests/test_netsuite_mcp.py
git commit -m "feat: add NetSuite MCP JSON-RPC client connector

Implements JSON-RPC 2.0 client for NetSuite MCP Standard Tools SuiteApp.

Features:
- OAuth 2.0 token management with auto-refresh
- JSON-RPC 2.0 request/response handling
- list_tools() to discover available tools
- run_suiteql() to execute SuiteQL queries via runCustomSuiteQL tool
- Result parsing from MCP content format

Tested with account query to verify connectivity."
```

---

## Task 4: Query Transaction Data via MCP

**Files:**
- Modify: `mcp-server/src/connectors/netsuite_mcp.py`

**Step 1: Write test for transaction query**

Add to: `mcp-server/tests/test_netsuite_mcp.py`

```python
@pytest.mark.asyncio
async def test_query_transaction_accounting_lines():
    """Test querying TransactionAccountingLine via MCP"""
    mcp = NetSuiteMCPConnector(
        account_id=os.getenv('NETSUITE_ACCOUNT_ID'),
        client_id=os.getenv('NETSUITE_MCP_CLIENT_ID'),
        client_secret=os.getenv('NETSUITE_MCP_CLIENT_SECRET')
    )

    # Query actual transaction data
    query = """
        SELECT
            t.id,
            t.tranid,
            t.trandate,
            BUILTIN.DF(t.subsidiary) AS subsidiary_name,
            BUILTIN.DF(t.type) AS transaction_type,
            BUILTIN.DF(tal.account) AS account_name,
            tal.debit,
            tal.credit
        FROM transaction t
        INNER JOIN transactionaccountingline tal ON tal.transaction = t.id
        WHERE t.trandate >= TO_DATE('2025-01-01', 'YYYY-MM-DD')
        AND tal.posting = 'T'
        LIMIT 10
    """

    results = await mcp.run_suiteql(query)

    assert isinstance(results, list)
    assert len(results) > 0

    # Verify structure matches CSV format
    first_row = results[0]
    assert 'tranid' in first_row
    assert 'trandate' in first_row
    assert 'account_name' in first_row
    assert 'debit' in first_row or 'credit' in first_row
```

**Step 2: Run test to verify it passes**

Run:
```bash
cd mcp-server
pytest tests/test_netsuite_mcp.py::test_query_transaction_accounting_lines -v
```

Expected: PASS with 10 transaction records returned

**Step 3: Add convenience method for fetching all transactions**

Add method to `mcp-server/src/connectors/netsuite_mcp.py`:

```python
    async def fetch_transaction_details(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        subsidiary_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch transaction detail data via MCP (matches CSV export format)

        Args:
            from_date: Start date YYYY-MM-DD (default: 2025-01-01)
            to_date: End date YYYY-MM-DD (default: today)
            subsidiary_id: Filter by subsidiary ID
            limit: Max records (default: unlimited, auto-batched)

        Returns:
            List of transaction detail records
        """
        # Build SuiteQL query matching CSV Transaction Detail export
        where_clauses = ["tal.posting = 'T'"]  # Posted transactions only

        if from_date:
            where_clauses.append(f"t.trandate >= TO_DATE('{from_date}', 'YYYY-MM-DD')")

        if to_date:
            where_clauses.append(f"t.trandate <= TO_DATE('{to_date}', 'YYYY-MM-DD')")

        if subsidiary_id:
            where_clauses.append(f"t.subsidiary = '{subsidiary_id}'")

        where_sql = " AND ".join(where_clauses)

        # Query TransactionAccountingLine (matches CSV export)
        query = f"""
            SELECT
                t.id,
                t.tranid AS document_number,
                t.trandate AS date,
                BUILTIN.DF(t.type) AS type,
                BUILTIN.DF(t.subsidiary) AS subsidiary_name,
                BUILTIN.DF(tal.account) AS account,
                BUILTIN.DF(t.entity) AS name,
                t.memo,
                tal.debit,
                tal.credit
            FROM transaction t
            INNER JOIN transactionaccountingline tal ON tal.transaction = t.id
            WHERE {where_sql}
            ORDER BY t.trandate DESC, t.id, tal.id
        """

        if limit:
            query += f" LIMIT {limit}"

        logger.info(f"[NetSuite MCP] Fetching transaction details from {from_date or 'beginning'}")

        results = await self.run_suiteql(query, description="Transaction Detail export")

        logger.info(f"[NetSuite MCP] Fetched {len(results)} transaction accounting lines")

        return results
```

**Step 4: Run test**

```bash
pytest tests/test_netsuite_mcp.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add mcp-server/src/connectors/netsuite_mcp.py mcp-server/tests/test_netsuite_mcp.py
git commit -m "feat: add transaction detail query via MCP runCustomSuiteQL

Added fetch_transaction_details() method that queries TransactionAccountingLine
via NetSuite MCP Standard Tools.

Query matches CSV Transaction Detail export format:
- Document number, date, type
- Subsidiary, account, entity name
- Debit and credit amounts
- Memo fields

Returns same data structure as manual CSV exports for seamless integration."
```

---

## Task 5: Integrate MCP into Sync Pipeline

**Files:**
- Modify: `mcp-server/src/services/snowflake_netsuite_loader.py`

**Step 1: Write test for MCP-based sync**

Add to: `mcp-server/tests/test_netsuite_mcp.py`

```python
@pytest.mark.asyncio
async def test_sync_via_mcp_to_snowflake():
    """Test full sync pipeline using MCP"""
    from src.services.snowflake_netsuite_loader import NetSuiteToSnowflakeLoader
    import os

    # This test requires Snowflake connection
    loader = NetSuiteToSnowflakeLoader(
        tenant_id=os.getenv('TENANT_ID', 'test-tenant')
    )

    # Initialize with MCP connector
    await loader.initialize_with_mcp()

    # Sync small batch
    count = await loader.sync_transactions_via_mcp(
        from_date="2025-11-01",
        limit=10
    )

    assert count > 0
    assert count <= 10
```

**Step 2: Run test to verify it fails**

Run:
```bash
cd mcp-server
pytest tests/test_netsuite_mcp.py::test_sync_via_mcp_to_snowflake -v
```

Expected: FAIL with "AttributeError: 'NetSuiteToSnowflakeLoader' object has no attribute 'initialize_with_mcp'"

**Step 3: Add MCP initialization to loader**

Modify: `mcp-server/src/services/snowflake_netsuite_loader.py`

Add after the `__init__` method:

```python
    async def initialize_with_mcp(self):
        """Initialize with NetSuite MCP connector instead of REST API connector"""
        from ..models.tenant import Tenant
        from uuid import UUID
        from ..connectors.netsuite_mcp import NetSuiteMCPConnector
        import os

        # Get tenant from database
        async with get_db_context() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Tenant).where(Tenant.id == UUID(self.tenant_id))
            )
            tenant = result.scalar_one_or_none()

            if not tenant:
                raise Exception(f"Tenant {self.tenant_id} not found")

            # Set tenant context
            TenantContext.set_tenant(tenant)

            # Get Snowflake connector via warehouse router
            warehouse_router = WarehouseRouter()
            self.snowflake = await warehouse_router.get_connector(
                warehouse_type="snowflake"
            )

            if not self.snowflake:
                raise Exception(f"Snowflake connector not found for tenant {self.tenant_id}")

            # Initialize MCP connector from environment
            self.netsuite_mcp = NetSuiteMCPConnector(
                account_id=os.getenv('NETSUITE_ACCOUNT_ID'),
                client_id=os.getenv('NETSUITE_MCP_CLIENT_ID'),
                client_secret=os.getenv('NETSUITE_MCP_CLIENT_SECRET')
            )

            logger.info("[Loader] Initialized with NetSuite MCP connector")

    async def sync_transactions_via_mcp(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> int:
        """
        Sync transaction data using MCP runCustomSuiteQL tool

        Args:
            from_date: Start date YYYY-MM-DD
            to_date: End date YYYY-MM-DD
            limit: Max records

        Returns:
            Number of records synced
        """
        if not hasattr(self, 'netsuite_mcp'):
            raise Exception("Must call initialize_with_mcp() first")

        logger.info(f"[Loader] Syncing transactions via MCP from {from_date or 'beginning'}")

        # Fetch from NetSuite via MCP
        transactions = await self.netsuite_mcp.fetch_transaction_details(
            from_date=from_date,
            to_date=to_date,
            limit=limit
        )

        if not transactions:
            logger.info("[Loader] No transactions returned from MCP")
            return 0

        # Prepare for Snowflake
        sync_id = str(uuid.uuid4())
        bronze_records = []

        for txn in transactions:
            bronze_records.append({
                "ID": txn.get("id"),
                "SYNC_ID": sync_id,
                "TENANT_ID": self.tenant_id,
                "RAW_DATA": json.dumps(txn),
                "LAST_MODIFIED_DATE": None,
                "EXTRACTED_AT": datetime.utcnow().isoformat(),
                "IS_DELETED": False,
                "SUBSIDIARY_ID": None  # Parse from subsidiary_name if needed
            })

        # Bulk insert to Snowflake
        await self._bulk_insert_snowflake(
            table="BRONZE.NETSUITE_JOURNAL_ENTRIES",
            records=bronze_records
        )

        logger.info(f"[Loader] ✅ Synced {len(bronze_records)} transactions via MCP")

        return len(bronze_records)
```

**Step 4: Run test to verify it passes**

Run:
```bash
cd mcp-server
pytest tests/test_netsuite_mcp.py::test_sync_via_mcp_to_snowflake -v
```

Expected: PASS with 10 records synced to Snowflake

**Step 5: Verify data in Snowflake**

Run Python check:
```python
import os, snowflake.connector
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv('mcp-server/.env')
conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    role=os.getenv('SNOWFLAKE_ROLE'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
    database=os.getenv('SNOWFLAKE_DATABASE')
)

cursor = conn.cursor()

# Check for MCP data (last 5 minutes)
five_min_ago = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
cursor.execute(f"""
    SELECT COUNT(*)
    FROM bronze.netsuite_journal_entries
    WHERE _ingestion_timestamp >= '{five_min_ago}'
""")

new_count = cursor.fetchone()[0]
print(f"New records from MCP: {new_count}")

cursor.close()
conn.close()
```

Expected: "New records from MCP: 10"

**Step 6: Commit**

```bash
git add mcp-server/src/services/snowflake_netsuite_loader.py
git commit -m "feat: integrate MCP connector into NetSuite sync pipeline

Added MCP-based sync methods to NetSuiteToSnowflakeLoader:
- initialize_with_mcp() to use MCP connector
- sync_transactions_via_mcp() to pull transaction data

Uses runCustomSuiteQL tool to query TransactionAccountingLine table,
matching the Transaction Detail CSV export format.

Tested with Snowflake insert verification."
```

---

## Task 6: Update Sync API to Use MCP

**Files:**
- Modify: `mcp-server/src/api/netsuite_sync.py`

**Step 1: Add MCP option to sync request**

Modify: `mcp-server/src/api/netsuite_sync.py`

Update `SyncRequest` model:

```python
class SyncRequest(BaseModel):
    full_sync: bool = False
    record_types: Optional[list[str]] = None
    from_date: Optional[str] = None
    limit: Optional[int] = None
    use_mcp: bool = True  # NEW: Default to MCP (faster, more reliable)
```

**Step 2: Update sync trigger to use MCP**

Modify the `trigger_sync` function:

```python
    async def run_sync():
        try:
            if request.use_mcp:
                # Use MCP Standard Tools connector
                logger.info("[Sync] Using NetSuite MCP Standard Tools")

                from ..services.snowflake_netsuite_loader import NetSuiteToSnowflakeLoader

                loader = NetSuiteToSnowflakeLoader(tenant_id)
                await loader.initialize_with_mcp()

                # Sync transactions via MCP
                count = await loader.sync_transactions_via_mcp(
                    from_date=request.from_date if request.from_date else "2025-01-01",
                    limit=request.limit
                )

                logger.info(f"[Sync] MCP sync complete: {count} records")
            else:
                # Use original SuiteQL approach
                await orchestrator.sync_tenant(
                    tenant_id=tenant_id,
                    incremental=not request.full_sync,
                    record_types=request.record_types,
                    from_date=request.from_date,
                    limit=request.limit
                )
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            raise
```

**Step 3: Test MCP sync via API**

Run:
```bash
curl -X POST "http://localhost:8085/api/v1/netsuite/sync/trigger" \
  -H "Authorization: Bearer dev-mcp-api-key-change-in-production-min-32-chars" \
  -H "X-Tenant-ID: silvercreek" \
  -H "Content-Type: application/json" \
  -d '{"use_mcp": true, "limit": 100, "from_date": "2025-01-01"}'
```

Expected: Response shows "started" and records are loaded to Snowflake

**Step 4: Verify in Snowflake**

Check record count increased

**Step 5: Commit**

```bash
git add mcp-server/src/api/netsuite_sync.py
git commit -m "feat: add MCP option to NetSuite sync API

Added use_mcp parameter (default: true) to sync trigger endpoint.

When enabled:
- Uses NetSuite MCP Standard Tools SuiteApp
- Calls runCustomSuiteQL tool via JSON-RPC
- Queries TransactionAccountingLine table
- Returns complete transaction data

Falls back to SuiteQL if use_mcp=false.

MCP approach is faster and more reliable than direct SuiteQL."
```

---

## Task 7: Deploy and Test Production

**Files:**
- Modify: `mcp-server/.env` (on GCP)

**Step 1: Add MCP credentials to production**

Run:
```bash
gcloud compute ssh root@dental-erp-vm --zone=us-central1-a --command "
cd /opt/dental-erp/mcp-server
echo '' >> .env
echo '# NetSuite MCP Standard Tools OAuth 2.0' >> .env
echo 'NETSUITE_MCP_CLIENT_ID=YOUR_CLIENT_ID' >> .env
echo 'NETSUITE_MCP_CLIENT_SECRET=YOUR_CLIENT_SECRET' >> .env
echo 'NETSUITE_MCP_ENDPOINT=https://7048582.suitetalk.api.netsuite.com/services/mcp/v1/all' >> .env
echo 'NETSUITE_MCP_TOKEN_ENDPOINT=https://7048582.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token' >> .env
cat .env | grep MCP
"
```

Expected: Shows 4 new MCP variables

**Step 2: Copy updated code to production**

Run:
```bash
gcloud compute scp --zone=us-central1-a --recurse mcp-server/src/ root@dental-erp-vm:/opt/dental-erp/mcp-server/
```

Expected: Files copied successfully

**Step 3: Restart MCP server**

Run:
```bash
gcloud compute ssh root@dental-erp-vm --zone=us-central1-a --command "
cd /opt/dental-erp
docker-compose --profile production restart mcp-server-prod
sleep 10
docker-compose ps mcp-server-prod
"
```

Expected: mcp-server-prod shows "Up (healthy)"

**Step 4: Trigger production sync**

Run:
```bash
curl -X POST "https://mcp.agentprovision.com/api/v1/netsuite/sync/trigger" \
  -H "Authorization: Bearer d876e6163089364d96a45a80ed576e99fc55b306133e258d9f861007e824b456" \
  -H "X-Tenant-ID: silvercreek" \
  -H "Content-Type: application/json" \
  -d '{"use_mcp": true, "limit": 1000, "from_date": "2025-01-01"}'
```

Expected: `{"status": "started", ...}`

**Step 5: Wait and verify data loaded**

Wait 60 seconds, then check:

```python
import os, snowflake.connector
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv('mcp-server/.env')
conn = snowflake.connector.connect(
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    role=os.getenv('SNOWFLAKE_ROLE'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
    database=os.getenv('SNOWFLAKE_DATABASE')
)

cursor = conn.cursor()
five_min_ago = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
cursor.execute(f"""
    SELECT COUNT(*)
    FROM bronze.netsuite_journal_entries
    WHERE _ingestion_timestamp >= '{five_min_ago}'
""")
new_count = cursor.fetchone()[0]
print(f"✅ New records from MCP: {new_count}")
cursor.close()
conn.close()
```

Expected: "✅ New records from MCP: 1000" (or actual count)

**Step 6: Verify in dashboard**

1. Open: https://dentalerp.agentprovision.com/analytics/overview
2. Check that NetSuite financial data is showing
3. Verify practice counts and revenue totals

**Step 7: Commit**

```bash
git add -A
git commit -m "feat: deploy NetSuite MCP integration to production

Deployed complete MCP Standard Tools integration:
- OAuth 2.0 token management
- JSON-RPC client
- TransactionAccountingLine queries
- Automated sync pipeline

Production verified with 1000+ transaction records synced via MCP API.

This completes automation of NetSuite Transaction Detail data extraction,
replacing manual CSV exports with API-based automated sync."
git push origin main
```

---

## Verification Checklist

After all tasks complete:

- [ ] OAuth 2.0 token fetches successfully
- [ ] MCP tools/list returns runCustomSuiteQL
- [ ] runCustomSuiteQL executes test query
- [ ] TransactionAccountingLine query returns transaction data
- [ ] Data loads to Snowflake Bronze
- [ ] Production sync works
- [ ] Dashboard shows updated data
- [ ] All tests pass
- [ ] Code committed and deployed

---

## Success Criteria

**When complete:**
- ✅ NetSuite API automatically pulls transaction data
- ✅ No manual CSV exports needed
- ✅ Dashboard auto-updates with latest NetSuite data
- ✅ Scheduled daily syncs possible
- ✅ Complete automation of Operations Report

**Timeline:** 3-4 hours implementation after OAuth 2.0 credentials provided

---

**Next:** User creates OAuth 2.0 integration in NetSuite (follow NETSUITE_MCP_OAUTH_SETUP_GUIDE.md), then execute this plan task-by-task.
