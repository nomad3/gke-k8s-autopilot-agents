"""
ADP Workforce Now API Connector

Reference: https://developers.adp.com/articles/api/workforce-now-api

Implements OAuth 2.0 client credentials flow for ADP API
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

import aiohttp

from .base import BaseConnector, ConnectorConfig, ConnectorResponse
from ..utils.logger import logger


class ADPConnector(BaseConnector):
    """
    ADP Workforce Now API connector

    Uses OAuth 2.0 client credentials flow
    Supports employee, payroll, and time tracking data
    """

    @property
    def name(self) -> str:
        return "ADP"

    @property
    def integration_type(self) -> str:
        return "adp"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        api_url: str = "https://api.adp.com",
        **kwargs
    ):
        """
        Initialize ADP connector

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            api_url: ADP API base URL
        """
        config = ConnectorConfig(
            api_url=api_url,
            **kwargs
        )

        super().__init__(config)

        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    async def _get_access_token(self) -> str:
        """
        Get OAuth 2.0 access token

        Returns:
            Access token string
        """
        # Check if we have a valid cached token
        if self._access_token and self._token_expires_at:
            if datetime.utcnow() < self._token_expires_at - timedelta(minutes=5):
                return self._access_token

        # Request new token
        token_url = f"{self.config.api_url}/auth/oauth/v2/token"

        auth = aiohttp.BasicAuth(self.client_id, self.client_secret)
        data = {
            "grant_type": "client_credentials",
            "scope": "api"
        }

        logger.info("[ADP] Requesting OAuth access token")

        session = await self.get_session()

        async with session.post(token_url, auth=auth, data=data) as response:
            response.raise_for_status()
            token_data = await response.json()

            self._access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

            logger.info(f"[ADP] Access token obtained (expires in {expires_in}s)")

            return self._access_token

    def _get_default_headers(self) -> Dict[str, str]:
        """Override to not include API key in headers (uses OAuth)"""
        return {
            "Content-Type": "application/json",
            "User-Agent": f"MCP-Server/1.0 ({self.name})"
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make authenticated request to ADP API

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters

        Returns:
            JSON response
        """
        # Get access token
        token = await self._get_access_token()

        url = f"{self.config.api_url.rstrip('/')}/{endpoint.lstrip('/')}"

        # Add OAuth token to headers
        headers = kwargs.pop("headers", {})
        headers.update(self._get_default_headers())
        headers["Authorization"] = f"Bearer {token}"

        logger.info(f"[ADP] {method} {endpoint}")

        session = await self.get_session()

        async with session.request(method, url, headers=headers, **kwargs) as response:
            response.raise_for_status()
            data = await response.json()

            logger.debug(f"[ADP] Response: {response.status}")
            return data

    async def _test_connection_impl(self):
        """Test ADP API connection"""
        # Test by fetching worker information (should be accessible with valid credentials)
        try:
            # Note: This is a placeholder endpoint - actual endpoint depends on ADP product
            await self._get_access_token()
        except Exception as e:
            logger.error(f"[ADP] Connection test failed: {e}")
            raise

    async def fetch_data(
        self,
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> ConnectorResponse:
        """
        Fetch data from ADP

        Args:
            entity_type: Entity type (e.g., 'employee', 'payroll')
            filters: Optional query filters

        Returns:
            ConnectorResponse with data
        """
        try:
            # Map entity types to ADP API endpoints
            endpoint_map = {
                "employee": "hr/v2/workers",
                "payroll": "payroll/v1/payroll-output",
                "timecard": "time/v2/time-cards",
            }

            endpoint = endpoint_map.get(entity_type)
            if not endpoint:
                raise ValueError(f"Unsupported entity type: {entity_type}")

            # Make request with circuit breaker
            data = await self.circuit_breaker.call_async(
                self._make_request,
                "GET",
                endpoint
            )

            # Extract data from ADP response format
            # ADP typically wraps data in specific structures
            items = data.get("workers", data.get("payrolls", data.get("timeCards", [])))

            return ConnectorResponse(
                success=True,
                data=items,
                metadata={
                    "total_results": len(items),
                    "entity_type": entity_type,
                }
            )

        except Exception as e:
            logger.error(f"[ADP] Failed to fetch {entity_type}: {e}")
            return ConnectorResponse(
                success=False,
                error=str(e)
            )

    async def fetch_employees(
        self,
        limit: int = 1000
    ) -> ConnectorResponse:
        """
        Fetch employee data from ADP

        Args:
            limit: Maximum records to fetch

        Returns:
            ConnectorResponse with employee data
        """
        return await self.fetch_data("employee", {"limit": limit})

    async def fetch_payroll(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> ConnectorResponse:
        """
        Fetch payroll data from ADP

        Args:
            from_date: Start date
            to_date: End date

        Returns:
            ConnectorResponse with payroll data
        """
        filters = {}
        if from_date:
            filters["from_date"] = from_date
        if to_date:
            filters["to_date"] = to_date

        return await self.fetch_data("payroll", filters)

    async def transform_data(
        self,
        raw_data: Any,
        entity_type: str
    ) -> List[Dict[str, Any]]:
        """
        Transform ADP data to standard format

        Args:
            raw_data: Raw data from ADP API
            entity_type: Entity type

        Returns:
            Transformed data in standard format
        """
        if not raw_data:
            return []

        transformed = []

        for record in raw_data:
            transformed_record = {
                "source_id": str(record.get("associateOID", record.get("id", ""))),
                "source_system": "adp",
                "entity_type": entity_type,
                "raw_data": record,
                "extracted_at": datetime.utcnow().isoformat() + "Z",
            }

            # Add entity-specific transformations
            if entity_type == "employee":
                person = record.get("person", {})
                transformed_record.update({
                    "employee_id": record.get("workerID", {}).get("idValue"),
                    "first_name": person.get("legalName", {}).get("givenName"),
                    "last_name": person.get("legalName", {}).get("familyName1"),
                    "email": person.get("communication", {}).get("email", {}).get("emailUri"),
                    "status": record.get("workerStatus", {}).get("statusCode", {}).get("codeValue"),
                })
            elif entity_type == "payroll":
                transformed_record.update({
                    "payroll_id": record.get("payrollAgreementID"),
                    "gross_pay": record.get("grossPay", {}).get("amountValue"),
                    "net_pay": record.get("netPay", {}).get("amountValue"),
                    "pay_date": record.get("payDate"),
                })

            transformed.append(transformed_record)

        return transformed


def create_adp_connector(
    client_id: str,
    client_secret: str,
    api_url: str = "https://api.adp.com",
    **kwargs
) -> ADPConnector:
    """
    Factory function to create ADP connector

    Args:
        client_id: OAuth client ID
        client_secret: OAuth client secret
        api_url: ADP API base URL

    Returns:
        Configured ADPConnector instance
    """
    return ADPConnector(
        client_id=client_id,
        client_secret=client_secret,
        api_url=api_url,
        **kwargs
    )
