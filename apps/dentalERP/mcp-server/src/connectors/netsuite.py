"""
NetSuite SuiteTalk REST API Connector

Reference: https://system.netsuite.com/help/helpcenter/en_US/APIs/REST_API_Browser/record/v1/2023.1/index.html

Implements OAuth 1.0a Token-Based Authentication (TBA) for NetSuite REST API
"""

import asyncio
import base64
import hashlib
import hmac
import os
import secrets
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlparse, parse_qs

import aiohttp

from .base import BaseConnector, ConnectorConfig, ConnectorResponse
from ..utils.logger import logger


class NetSuiteConnector(BaseConnector):
    """
    NetSuite SuiteTalk REST API connector

    Uses OAuth 1.0a Token-Based Authentication (TBA)
    Supports REST API v1 for record operations
    """

    @property
    def name(self) -> str:
        return "NetSuite"

    @property
    def integration_type(self) -> str:
        return "netsuite"

    def __init__(
        self,
        account: str,
        consumer_key: str,
        consumer_secret: str,
        token_key: str,
        token_secret: str,
        api_url: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize NetSuite connector with OAuth 1.0a TBA

        Args:
            account: NetSuite account ID (e.g., '7048582')
            consumer_key: OAuth 1.0a Consumer Key from integration
            consumer_secret: OAuth 1.0a Consumer Secret from integration
            token_key: OAuth 1.0a Token ID from access token
            token_secret: OAuth 1.0a Token Secret from access token
            api_url: Optional custom API URL
        """
        # Check if we should use environment variables instead of passed credentials
        env_account = os.environ.get('NETSUITE_ACCOUNT_ID')
        env_consumer_key = os.environ.get('NETSUITE_CONSUMER_KEY')
        env_consumer_secret = os.environ.get('NETSUITE_CONSUMER_SECRET')
        env_token_key = os.environ.get('NETSUITE_TOKEN_ID')
        env_token_secret = os.environ.get('NETSUITE_TOKEN_SECRET')

        # Use environment variables if available (bypass database caching issue)
        if env_consumer_key and env_token_key:
            logger.info("[NetSuite] Using credentials from environment variables")
            account = env_account or account
            consumer_key = env_consumer_key
            consumer_secret = env_consumer_secret
            token_key = env_token_key
            token_secret = env_token_secret
        else:
            logger.info("[NetSuite] Using credentials from database/config")

        # Build API URL if not provided (using REST Record API)
        if not api_url:
            api_url = f"https://{account.replace('_', '-').lower()}.suitetalk.api.netsuite.com/services/rest/record/v1"

        config = ConnectorConfig(
            api_url=api_url,
            **kwargs
        )

        super().__init__(config)

        self.account = account
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.token_key = token_key
        self.token_secret = token_secret
        self.realm = account

        # DEBUG: Log initialization
        logger.info(f"[NetSuite] Initialized with OAuth 1.0a TBA")
        logger.info(f"[NetSuite] Account: {account}")
        logger.info(f"[NetSuite] Consumer Key (first 20 chars): {consumer_key[:20] if consumer_key else 'MISSING'}...")
        logger.info(f"[NetSuite] Token Key (first 20 chars): {token_key[:20] if token_key else 'MISSING'}...")
        logger.info(f"[NetSuite] API URL: {api_url}")

    def _generate_oauth_signature(
        self,
        method: str,
        url: str,
        params: Dict[str, str]
    ) -> str:
        """
        Generate OAuth 1.0a signature for NetSuite

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Base URL (no query params)
            params: OAuth + query parameters

        Returns:
            Base64 encoded HMAC-SHA1 signature
        """
        # Sort parameters
        sorted_params = sorted(params.items())

        # Create parameter string
        param_string = "&".join([f"{quote(k, safe='')}={quote(v, safe='')}" for k, v in sorted_params])

        # Create base string
        base_string = f"{method.upper()}&{quote(url, safe='')}&{quote(param_string, safe='')}"

        # Create signing key (matching SOAP pattern that works)
        signing_key = f"{self.consumer_secret}&{self.token_secret}"

        # Generate signature (HMAC-SHA256 - same as working SOAP connector)
        signature = hmac.new(
            signing_key.encode(),
            base_string.encode(),
            hashlib.sha256
        ).digest()

        return base64.b64encode(signature).decode()

    def _get_oauth_headers(self, method: str, url: str) -> Dict[str, str]:
        """
        Generate OAuth 1.0a authorization header for NetSuite

        Args:
            method: HTTP method
            url: Request URL (may include query parameters)

        Returns:
            Dict with Authorization header
        """
        # Parse URL to separate base URL from query parameters
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        # Generate OAuth parameters
        timestamp = str(int(time.time()))
        nonce = secrets.token_hex(16)

        oauth_params = {
            "oauth_consumer_key": self.consumer_key,
            "oauth_token": self.token_key,
            "oauth_signature_method": "HMAC-SHA256",
            "oauth_timestamp": timestamp,
            "oauth_nonce": nonce,
            "oauth_version": "1.0",
        }

        # Add query parameters to oauth_params for signature (OAuth 1.0a spec)
        if parsed.query:
            query_params = parse_qs(parsed.query)
            for key, values in query_params.items():
                oauth_params[key] = values[0]  # Take first value

        # Generate signature with base URL (no query params in URL)
        signature = self._generate_oauth_signature(method, base_url, oauth_params)

        # Build authorization header with realm (only oauth_* parameters, not query params)
        oauth_header_params = {
            "oauth_consumer_key": self.consumer_key,
            "oauth_token": self.token_key,
            "oauth_signature_method": "HMAC-SHA256",
            "oauth_timestamp": timestamp,
            "oauth_nonce": nonce,
            "oauth_version": "1.0",
            "oauth_signature": signature
        }

        # Build header with realm (required by NetSuite)
        auth_header = f'OAuth realm="{self.realm}", ' + ", ".join([
            f'{k}="{quote(v, safe="")}"' for k, v in sorted(oauth_header_params.items())
        ])

        logger.info(f"[NetSuite OAuth] Method: {method}, URL: {url}")
        logger.info(f"[NetSuite OAuth] Authorization: {auth_header[:100]}...")

        return {
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "Prefer": "transient",
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make authenticated request to NetSuite API

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters

        Returns:
            JSON response
        """
        url = f"{self.config.api_url.rstrip('/')}/{endpoint.lstrip('/')}"

        # Get OAuth 1.0a headers with signature
        oauth_headers = self._get_oauth_headers(method, url)

        # Merge with any custom headers
        headers = kwargs.pop("headers", {})
        headers.update(oauth_headers)

        logger.info(f"[NetSuite] {method} {endpoint}")

        session = await self.get_session()

        try:
            async with session.request(method, url, headers=headers, **kwargs) as response:
                # NetSuite returns errors as JSON even with error status codes
                response_text = await response.text()

                try:
                    data = await response.json() if response_text else {}
                except:
                    data = {"raw_response": response_text}

                if response.status >= 400:
                    error_msg = data.get("o:errorDetails", [{}])[0].get("detail", response_text)
                    logger.error(f"[NetSuite] Error {response.status}: {error_msg}")
                    raise aiohttp.ClientError(f"NetSuite API error: {error_msg}")

                logger.debug(f"[NetSuite] Response: {response.status}")
                return data

        except aiohttp.ClientError as e:
            logger.error(f"[NetSuite] Request failed: {e}")
            raise

    async def _test_connection_impl(self):
        """Test NetSuite REST Record API connection"""
        try:
            # Fetch one subsidiary record (simple test)
            await self._make_request("GET", "subsidiary?limit=1")
            logger.info(f"[NetSuite REST] ✅ Connection test successful")
        except Exception as e:
            logger.error(f"[NetSuite REST] Connection test failed: {e}")
            raise

    async def fetch_data(
        self,
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> ConnectorResponse:
        """
        Fetch data from NetSuite

        Args:
            entity_type: Record type (e.g., 'journalEntry', 'customer', 'vendor')
            filters: Optional query filters (limit, offset, q, fields, subsidiary)

        Returns:
            ConnectorResponse with data
        """
        try:
            # Build query parameters
            params = []

            if filters:
                # Add filters as query params
                if filters.get("limit"):
                    params.append(f"limit={filters['limit']}")
                if filters.get("offset"):
                    params.append(f"offset={filters['offset']}")

                # Build query filter string
                q_parts = []
                if filters.get("q"):
                    q_parts.append(filters["q"])

                # Add subsidiary filter to query
                if filters.get("subsidiary"):
                    q_parts.append(f'subsidiary.id == "{filters["subsidiary"]}"')

                if q_parts:
                    params.append(f"q={' AND '.join(q_parts)}")

                if filters.get("fields"):
                    params.append(f"fields={filters['fields']}")

            query_string = "?" + "&".join(params) if params else ""
            endpoint = f"{entity_type}{query_string}"

            # Make request with circuit breaker
            data = await self.circuit_breaker.call_async(
                self._make_request,
                "GET",
                endpoint
            )

            # NetSuite returns items in 'items' array
            items = data.get("items", [])

            return ConnectorResponse(
                success=True,
                data=items,
                metadata={
                    "total_results": data.get("totalResults", len(items)),
                    "count": data.get("count", len(items)),
                    "has_more": data.get("hasMore", False),
                    "offset": data.get("offset", 0),
                }
            )

        except Exception as e:
            logger.error(f"[NetSuite] Failed to fetch {entity_type}: {e}")
            return ConnectorResponse(
                success=False,
                error=str(e)
            )

    async def fetch_journal_entries(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        subsidiary: Optional[str] = None,
        limit: int = 1000
    ) -> ConnectorResponse:
        """
        Fetch journal entries from NetSuite

        Args:
            from_date: Start date filter
            to_date: End date filter
            subsidiary: Subsidiary filter
            limit: Maximum records to fetch

        Returns:
            ConnectorResponse with journal entries
        """
        filters = {"limit": limit}

        # Build query filter
        q_parts = []
        if from_date:
            q_parts.append(f'tranDate >= "{from_date}"')
        if to_date:
            q_parts.append(f'tranDate <= "{to_date}"')
        if subsidiary:
            q_parts.append(f'subsidiary.name == "{subsidiary}"')

        if q_parts:
            filters["q"] = " AND ".join(q_parts)

        # Specify fields to return (including 'line' for transaction details)
        filters["fields"] = ",".join([
            "internalId",
            "tranId",
            "tranDate",
            "postingPeriod",
            "subsidiary",
            "amount",
            "currency",
            "status",
            "memo",
            "line",  # CRITICAL: Contains debit/credit line items
            "createdDate",
            "lastModifiedDate",
        ])

        return await self.fetch_data("journalEntry", filters)

    async def fetch_customers(
        self,
        subsidiary: Optional[str] = None,
        limit: int = 1000
    ) -> ConnectorResponse:
        """
        Fetch customers from NetSuite

        Args:
            subsidiary: Subsidiary filter
            limit: Maximum records to fetch

        Returns:
            ConnectorResponse with customers
        """
        filters = {"limit": limit}

        if subsidiary:
            filters["q"] = f'subsidiary.name == "{subsidiary}"'

        filters["fields"] = ",".join([
            "internalId",
            "entityId",
            "companyName",
            "email",
            "phone",
            "subsidiary",
            "status",
        ])

        return await self.fetch_data("customer", filters)

    async def fetch_vendors(
        self,
        subsidiary: Optional[str] = None,
        limit: int = 1000
    ) -> ConnectorResponse:
        """
        Fetch vendors from NetSuite

        Args:
            subsidiary: Subsidiary filter
            limit: Maximum records to fetch

        Returns:
            ConnectorResponse with vendors
        """
        filters = {"limit": limit}

        if subsidiary:
            filters["q"] = f'subsidiary.name == "{subsidiary}"'

        filters["fields"] = ",".join([
            "internalId",
            "entityId",
            "companyName",
            "email",
            "phone",
            "subsidiary",
        ])

        return await self.fetch_data("vendor", filters)

    async def get_subsidiaries(self) -> List[Dict[str, Any]]:
        """
        Fetch all subsidiaries from NetSuite

        Returns:
            List of subsidiary dictionaries with id and name
        """
        logger.info("[NetSuite] Fetching all subsidiaries")

        response = await self.fetch_data("subsidiary", {"limit": 100})

        if not response.success:
            logger.error(f"Failed to fetch subsidiaries: {response.error}")
            return []

        subsidiaries = response.data
        logger.info(f"[NetSuite] Found {len(subsidiaries)} subsidiaries")

        return subsidiaries

    async def fetch_journal_entries_via_suiteql(
        self,
        subsidiary_id: Optional[str] = None,
        from_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch ALL journal entries with line items using SuiteQL with automatic batching

        SuiteQL bypasses User Event Scripts that block REST Record API.
        Queries Transaction and TransactionLine tables directly.
        Automatically fetches ALL available records until NetSuite returns no more data.

        Args:
            subsidiary_id: Filter by subsidiary
            from_date: ISO date string (YYYY-MM-DD)
            limit: Optional max records (None = fetch ALL available records)

        Returns:
            List of ALL journal entries with line items
        """
        try:
            # Build SuiteQL query for journal entries with lines
            # FIX: Don't filter by type - NetSuite transaction.type field might use different values
            # CSV shows "Journal" but that's export format, not SuiteQL field value
            # Query ALL transactions and let the data come through
            where_clauses = []

            # Don't filter by subsidiary - query ALL subsidiaries at once
            # The subsidiary field will be in the returned data for parsing
            # if subsidiary_id:
            #     where_clauses.append(f"t.subsidiary = '{subsidiary_id}'")

            if from_date:
                where_clauses.append(f"t.trandate >= TO_DATE('{from_date}', 'YYYY-MM-DD')")

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            # Query TransactionAccountingLine for actual financial data (what CSV exports use)
            # This table has actual debits/credits that hit the GL
            # IMPORTANT: Use BUILTIN.DF() for fields that reference other records
            # FIX: Use URL parameters for pagination (limit/offset), NOT SQL LIMIT or ROWNUM
            query = f"""
                SELECT
                    t.id,
                    t.tranid,
                    t.trandate,
                    BUILTIN.DF(t.subsidiary) AS subsidiary_name,
                    BUILTIN.DF(t.type) AS transaction_type,
                    BUILTIN.DF(tal.account) AS account_name,
                    tal.debit,
                    tal.credit,
                    t.memo
                FROM transaction t
                INNER JOIN transactionaccountingline tal ON tal.transaction = t.id
                WHERE {where_sql}
                AND tal.posting = 'T'
                ORDER BY t.trandate DESC
            """.strip()

            # AUTO-FETCH ALL: Continue batching until NetSuite returns no more data
            # NetSuite max: 3,000 records per request
            BATCH_SIZE = 3000
            all_entries = []
            offset = 0

            if limit is None:
                logger.info(f"[NetSuite SuiteQL] Fetching ALL available journal entries (auto-batching at {BATCH_SIZE} per request)")
            else:
                logger.info(f"[NetSuite SuiteQL] Fetching up to {limit} journal entries (auto-batching at {BATCH_SIZE} per request)")

            while True:
                # If limit specified, check if we've reached it
                if limit and len(all_entries) >= limit:
                    logger.info(f"[NetSuite SuiteQL] Reached requested limit of {limit} records")
                    break

                # Calculate batch size
                if limit:
                    remaining = limit - len(all_entries)
                    current_batch_size = min(BATCH_SIZE, remaining)
                else:
                    # No limit = fetch full batches until empty
                    current_batch_size = BATCH_SIZE

                # Execute SuiteQL with offset-based pagination
                suiteql_response = await self._make_suiteql_request(query, limit=current_batch_size, offset=offset)

                if not suiteql_response or 'items' not in suiteql_response:
                    logger.info(f"[NetSuite SuiteQL] No more records at offset {offset}, stopping")
                    break

                batch_items = suiteql_response['items']
                if not batch_items:
                    logger.info(f"[NetSuite SuiteQL] Empty batch at offset {offset}, stopping")
                    break

                logger.info(f"[NetSuite SuiteQL] Batch {offset//BATCH_SIZE + 1}: Fetched {len(batch_items)} journal entries at offset {offset}")

                # For each journal entry, fetch its lines
                for je in batch_items:
                    je_id = je.get('id')

                    # Query line items for this journal entry
                    # IMPORTANT: Use BUILTIN.DF() for account field (NetSuite requirement)
                    # FIX: Use URL parameter for limit, not SQL ROWNUM
                    # FIX 2: Remove ORDER BY tl.line (field doesn't exist)
                    # FIX 3: Use 'amount' field instead of 'debit'/'credit' (transactionline has amount, not debit/credit)
                    #        - Positive amount = Debit
                    #        - Negative amount = Credit
                    lines_query = f"""
                        SELECT
                            tl.account,
                            tl.amount,
                            tl.entity,
                            tl.memo,
                            BUILTIN.DF(tl.account) AS account_name,
                            a.acctnumber AS account_number
                        FROM transactionline tl
                        LEFT JOIN account a ON tl.account = a.id
                        WHERE tl.transaction = {je_id}
                    """

                    lines_response = await self._make_suiteql_request(lines_query, limit=1000)

                    # Build journal entry with lines
                    entry = {
                        'id': je_id,
                        'tranId': je.get('tranid'),
                        'tranDate': je.get('trandate'),
                        'subsidiary': {'id': str(je.get('subsidiary'))},
                        'status': {'name': je.get('status')},
                        'memo': je.get('memo'),
                        'line': []
                    }

                    # Add line items
                    if lines_response and 'items' in lines_response:
                        for line in lines_response['items']:
                            # Convert amount to debit/credit (positive = debit, negative = credit)
                            amount = float(line.get('amount') or 0)
                            debit = amount if amount > 0 else 0
                            credit = -amount if amount < 0 else 0

                            entry['line'].append({
                                'account': {
                                    'name': line.get('account_name'),
                                    'accountNumber': line.get('account_number')
                                },
                                'debit': debit,
                                'credit': credit,
                                'entity': line.get('entity'),
                                'memo': line.get('memo')
                            })

                    all_entries.append(entry)

                # Update offset for next batch
                offset += len(batch_items)

                # Rate limiting between batches (avoid overwhelming NetSuite)
                if len(all_entries) < total_requested and len(batch_items) == current_batch_size:
                    logger.info(f"[NetSuite SuiteQL] Rate limiting: waiting 2 seconds before next batch...")
                    await asyncio.sleep(2)

            logger.info(f"[NetSuite SuiteQL] ✅ Fetched {len(all_entries)} total journal entries with line items across {offset//BATCH_SIZE + 1} batches")
            return all_entries

        except Exception as e:
            logger.error(f"[NetSuite SuiteQL] Failed to fetch journal entries: {e}")
            return []

    async def _make_suiteql_request(self, query: str, limit: Optional[int] = None, offset: int = 0) -> Optional[Dict]:
        """
        Execute SuiteQL query via REST endpoint

        SuiteQL endpoint: POST /services/rest/query/v1/suiteql
        Bypasses User Event Scripts

        Args:
            query: SuiteQL query string (WITHOUT LIMIT/ROWNUM - use URL params instead)
            limit: Max records to return (via URL ?limit= parameter)
            offset: Offset for pagination (via URL ?offset= parameter)

        Returns:
            Query results or None
        """
        try:
            # SuiteQL uses different base URL
            # FIX: Add limit and offset as URL parameters (NetSuite SuiteTalk REST API pagination)
            suiteql_url = f"https://{self.account.replace('_', '-').lower()}.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql"

            # Build query parameters for pagination
            url_params = []
            if limit:
                url_params.append(f"limit={limit}")
            if offset > 0:
                url_params.append(f"offset={offset}")

            if url_params:
                suiteql_url = f"{suiteql_url}?{'&'.join(url_params)}"

            # Build OAuth headers for POST request (with query params in URL for signature)
            headers = self._get_oauth_headers("POST", suiteql_url)

            # DIAGNOSTIC: Log the exact query and URL being sent
            logger.info(f"[NetSuite SuiteQL] URL: {suiteql_url}")
            logger.info(f"[NetSuite SuiteQL] Query: {query}")

            # Make POST request with query
            # Query goes in POST body as {"q": "SELECT ..."}
            # Pagination goes in URL as ?limit=X&offset=Y
            session = await self.get_session()

            async with session.post(
                suiteql_url,
                headers=headers,
                json={"q": query},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:

                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    # DIAGNOSTIC: Log full error, not truncated
                    logger.error(f"[NetSuite SuiteQL] Error {response.status}: {error_text}")
                    logger.error(f"[NetSuite SuiteQL] Failed query was: {query}")
                    return None

        except Exception as e:
            logger.error(f"[NetSuite SuiteQL] Request failed: {e}")
            return None

    async def fetch_journal_entry_detail(self, internal_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch full journal entry details including line items

        NetSuite REST API limitation: List endpoints don't return sublists (like 'line').
        Must fetch individual records with expandSubResources=true to get line items.

        Args:
            internal_id: Journal entry internal ID

        Returns:
            Full journal entry with line items, or None if failed
        """
        try:
            endpoint = f"journalEntry/{internal_id}?expandSubResources=true"

            data = await self.circuit_breaker.call_async(
                self._make_request,
                "GET",
                endpoint
            )

            logger.debug(f"[NetSuite] Fetched journal entry {internal_id} with {len(data.get('line', []))} line items")
            return data

        except Exception as e:
            logger.error(f"[NetSuite] Failed to fetch journal entry detail {internal_id}: {e}")
            return None

    async def transform_data(
        self,
        raw_data: Any,
        entity_type: str
    ) -> List[Dict[str, Any]]:
        """
        Transform NetSuite data to standard format

        Args:
            raw_data: Raw data from NetSuite API
            entity_type: Entity type

        Returns:
            Transformed data in standard format
        """
        if not raw_data:
            return []

        transformed = []

        for record in raw_data:
            # Extract nested values safely
            transformed_record = {
                "source_id": str(record.get("id") or record.get("internalId", "")),
                "source_system": "netsuite",
                "entity_type": entity_type,
                "raw_data": record,
                "extracted_at": self._get_timestamp(),
            }

            # Add entity-specific transformations
            if entity_type == "journalEntry":
                transformed_record.update({
                    "transaction_id": record.get("tranId"),
                    "transaction_date": record.get("tranDate"),
                    "amount": record.get("amount"),
                    "currency": record.get("currency", {}).get("refName"),
                    "subsidiary": record.get("subsidiary", {}).get("refName"),
                    "status": record.get("status", {}).get("refName"),
                    "memo": record.get("memo"),
                })
            elif entity_type == "customer":
                transformed_record.update({
                    "entity_id": record.get("entityId"),
                    "company_name": record.get("companyName"),
                    "email": record.get("email"),
                    "phone": record.get("phone"),
                    "subsidiary": record.get("subsidiary", {}).get("refName"),
                })

            transformed.append(transformed_record)

        return transformed

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"


def create_netsuite_connector(
    account: str,
    consumer_key: str,
    consumer_secret: str,
    token_key: str,
    token_secret: str,
    **kwargs
) -> NetSuiteConnector:
    """
    Factory function to create NetSuite connector with OAuth 1.0a TBA

    Args:
        account: NetSuite account ID
        consumer_key: OAuth 1.0a Consumer Key
        consumer_secret: OAuth 1.0a Consumer Secret
        token_key: OAuth 1.0a Token ID
        token_secret: OAuth 1.0a Token Secret

    Returns:
        Configured NetSuiteConnector instance
    """
    return NetSuiteConnector(
        account=account,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        token_key=token_key,
        token_secret=token_secret,
        **kwargs
    )


class MockNetSuiteConnector(BaseConnector):
    @property
    def name(self) -> str:
        return "NetSuiteMock"

    @property
    def integration_type(self) -> str:
        return "netsuite"

    def __init__(self):
        super().__init__(ConnectorConfig(api_url="https://mock.netsuite.local"))

    async def _test_connection_impl(self):
        return

    async def fetch_data(
        self,
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> ConnectorResponse:
        sample_data: Dict[str, List[Dict[str, Any]]] = {
            "journalEntry": [
                {
                    "internalId": "JE123",
                    "tranId": "JE-001",
                    "tranDate": "2025-01-01",
                    "amount": 1250.0,
                    "currency": {"refName": "USD"},
                    "subsidiary": {"refName": "Downtown"},
                }
            ],
            "customer": [
                {
                    "internalId": "CUST1",
                    "entityId": "Acme Dental",
                    "companyName": "Acme Dental",
                    "email": "contact@acme.test",
                    "phone": "+1-555-0100",
                    "subsidiary": {"refName": "Downtown"},
                }
            ],
            "vendor": [
                {
                    "internalId": "VEND1",
                    "entityId": "Supplier One",
                    "companyName": "Supplier One",
                    "email": "support@supplier.test",
                    "phone": "+1-555-0200",
                    "subsidiary": {"refName": "Downtown"},
                }
            ],
        }

        data = sample_data.get(entity_type, [])

        return ConnectorResponse(
            success=True,
            data=data,
            metadata={
                "total_results": len(data),
                "count": len(data),
                "has_more": False,
                "offset": 0,
            }
        )


def create_mock_netsuite_connector() -> MockNetSuiteConnector:
    return MockNetSuiteConnector()
