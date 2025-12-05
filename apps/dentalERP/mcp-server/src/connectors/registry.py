"""
Connector Registry - Central management for all integration connectors

Implements Factory and Registry patterns for connector management
"""

from typing import Dict, Optional, Type

from .base import BaseConnector
from .adp import ADPConnector, create_adp_connector
from .netsuite import NetSuiteConnector, create_mock_netsuite_connector, create_netsuite_connector
from ..core.config import settings
from ..services.credentials import get_credential_service
from ..utils.logger import logger


class ConnectorRegistry:
    """
    Connector registry using Factory and Singleton patterns

    Manages connector instances and provides factory methods
    """

    _instance: Optional['ConnectorRegistry'] = None
    _connectors: Dict[str, BaseConnector] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._connector_classes: Dict[str, Type[BaseConnector]] = {
                "adp": ADPConnector,
                "netsuite": NetSuiteConnector,
            }

    async def get_connector(
        self,
        integration_type: str,
        practice_id: Optional[str] = None
    ) -> Optional[BaseConnector]:
        """
        Get or create connector instance

        Args:
            integration_type: Type of integration (e.g., 'adp', 'netsuite')
            practice_id: Optional practice ID for practice-specific credentials

        Returns:
            Connector instance or None if not available
        """
        # Create cache key
        cache_key = f"{integration_type}:{practice_id or 'global'}"

        # Return cached instance if available
        if cache_key in self._connectors:
            return self._connectors[cache_key]

        # Create new connector
        connector = await self._create_connector(integration_type, practice_id)

        if connector:
            self._connectors[cache_key] = connector
            logger.info(f"Created connector for {integration_type}")

        return connector

    async def _create_connector(
        self,
        integration_type: str,
        practice_id: Optional[str] = None
    ) -> Optional[BaseConnector]:
        """
        Factory method to create connector instances

        Args:
            integration_type: Type of integration
            practice_id: Optional practice ID

        Returns:
            Connector instance or None
        """
        try:
            if integration_type == "netsuite":
                return await self._create_netsuite_connector(practice_id)
            elif integration_type == "adp":
                return await self._create_adp_connector(practice_id)
            else:
                logger.warning(f"Unknown integration type: {integration_type}")
                return None

        except Exception as e:
            logger.error(f"Failed to create connector for {integration_type}: {e}")
            return None

    async def _create_netsuite_connector(
        self,
        practice_id: Optional[str] = None
    ) -> Optional[NetSuiteConnector]:
        """Create NetSuite connector with credentials"""

        # Get credentials from settings or database
        creds = {
            "account": settings.netsuite_account,
            "consumer_key": settings.netsuite_consumer_key,
            "consumer_secret": settings.netsuite_consumer_secret,
            "token_key": settings.netsuite_token_key,
            "token_secret": settings.netsuite_token_secret,
        }

        # Check if all required credentials are available
        if all(creds.values()):
            return create_netsuite_connector(**creds)

        logger.warning("NetSuite credentials not fully configured; using mock connector")
        return create_mock_netsuite_connector()

    async def _create_adp_connector(
        self,
        practice_id: Optional[str] = None
    ) -> Optional[ADPConnector]:
        """Create ADP connector with credentials"""

        # Get credentials from settings or database
        if not settings.adp_client_id or not settings.adp_client_secret:
            logger.warning("ADP credentials not configured")
            return None

        return create_adp_connector(
            client_id=settings.adp_client_id,
            client_secret=settings.adp_client_secret,
            api_url=settings.adp_api_url or "https://api.adp.com"
        )

    async def test_all_connections(self) -> Dict[str, bool]:
        """
        Test connections to all configured integrations

        Returns:
            Dict mapping integration type to connection status
        """
        results = {}

        for integration_type in ["adp", "netsuite"]:
            try:
                connector = await self.get_connector(integration_type)
                if connector:
                    results[integration_type] = await connector.test_connection()
                else:
                    results[integration_type] = False
            except Exception as e:
                logger.error(f"Connection test failed for {integration_type}: {e}")
                results[integration_type] = False

        return results

    async def close_all(self):
        """Close all connector sessions"""
        for connector in self._connectors.values():
            try:
                await connector.close()
            except Exception as e:
                logger.error(f"Error closing connector: {e}")

        self._connectors.clear()
        logger.info("All connectors closed")


def get_connector_registry() -> ConnectorRegistry:
    """Get singleton connector registry"""
    return ConnectorRegistry()
