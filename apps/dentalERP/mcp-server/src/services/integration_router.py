"""Integration routing service for multi-tenant external integrations"""

from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..connectors.base import BaseConnector, ConnectorConfig
from ..connectors.netsuite import NetSuiteConnector, MockNetSuiteConnector
from ..connectors.adp import ADPConnector
from ..core.tenant import TenantContext
from ..core.database import get_db_context
from ..models.tenant import TenantIntegration, IntegrationTypeEnum
from ..utils.logger import logger


class IntegrationRouter:
    """
    Route integration requests to tenant-specific connectors

    Features:
    - Automatic tenant detection from context
    - Connection pooling (cached connectors per tenant + integration type)
    - Support for multiple integrations per tenant
    - Secure credential management from database
    """

    def __init__(self):
        """Initialize integration router with connection cache"""
        self._connectors: Dict[str, BaseConnector] = {}

    async def get_connector(
        self,
        integration_type: str,
        db: Optional[AsyncSession] = None
    ) -> BaseConnector:
        """
        Get integration connector for current tenant

        Args:
            integration_type: Integration type ('netsuite', 'adp', 'dentrix', etc.)
            db: Database session (optional, creates new if None)

        Returns:
            BaseConnector: Integration connector instance

        Raises:
            ValueError: If no tenant context or no integration configured
        """
        # Get current tenant from context
        tenant = TenantContext.require_tenant()

        # Get or create database session
        if db is None:
            async with get_db_context() as db_session:
                return await self._get_connector_internal(
                    tenant.id, integration_type, db_session
                )
        else:
            return await self._get_connector_internal(
                tenant.id, integration_type, db
            )

    async def _get_connector_internal(
        self,
        tenant_id: str,
        integration_type: str,
        db: AsyncSession
    ) -> BaseConnector:
        """Internal method to get connector with database session"""

        # Get tenant's integration configuration
        integration_config = await self._get_integration_config(
            db, tenant_id, integration_type
        )

        if not integration_config:
            tenant = TenantContext.get_tenant()
            raise ValueError(
                f"No {integration_type} integration configured for tenant {tenant.tenant_code}"
            )

        # Create cache key
        cache_key = f"{tenant_id}_{integration_type}"

        # Return cached connector if available
        if cache_key in self._connectors:
            logger.debug(f"Reusing cached {integration_type} connector for tenant {tenant_id}")
            return self._connectors[cache_key]

        # Create new connector
        connector = self._create_connector(
            integration_type,
            integration_config['config']
        )

        self._connectors[cache_key] = connector

        logger.info(
            f"Created new {integration_type} connector for tenant {tenant_id}"
        )

        return connector

    def _create_connector(
        self,
        integration_type: str,
        config: Dict
    ) -> BaseConnector:
        """
        Factory method to create integration connector

        Args:
            integration_type: Type of integration ('netsuite', 'adp', etc.)
            config: Integration configuration from database

        Returns:
            BaseConnector: Connector instance

        Raises:
            ValueError: If unsupported integration type
        """
        # Create ConnectorConfig from database config
        connector_config = ConnectorConfig(
            api_url=config.get('api_url', ''),
            api_key=config.get('api_key'),
            api_secret=config.get('api_secret'),
            timeout=config.get('timeout', 30),
            max_retries=config.get('max_retries', 3),
            cache_ttl=config.get('cache_ttl', 300)
        )

        if integration_type == IntegrationTypeEnum.NETSUITE.value:
            # Check if mock mode
            if config.get('mock', False):
                return MockNetSuiteConnector()

            # NetSuite REST API with OAuth 1.0a TBA (HMAC-SHA256)
            # Map database keys to connector keys
            # Database stores: 'account', 'token_key'
            # Connector expects: 'account_id', 'token_id'
            account_id = config.get('account_id') or config.get('account')
            token_id = config.get('token_id') or config.get('token_key')

            logger.info(f"[IntegrationRouter] Creating NetSuite REST API connector:")
            logger.info(f"  account_id: {account_id}")
            logger.info(f"  consumer_key: {config.get('consumer_key', 'MISSING')[:20]}...")
            logger.info(f"  token_id: {token_id}")

            return NetSuiteConnector(
                account=account_id,
                consumer_key=config.get('consumer_key'),
                consumer_secret=config.get('consumer_secret'),
                token_key=token_id,
                token_secret=config.get('token_secret')
            )

        elif integration_type == IntegrationTypeEnum.ADP.value:
            return ADPConnector(connector_config)

        # Add more integration types as needed
        # elif integration_type == IntegrationTypeEnum.DENTRIX.value:
        #     return DentrixConnector(connector_config)

        else:
            raise ValueError(f"Unsupported integration type: {integration_type}")

    async def _get_integration_config(
        self,
        db: AsyncSession,
        tenant_id: str,
        integration_type: str
    ) -> Optional[Dict]:
        """
        Get integration configuration for tenant

        Args:
            db: Database session
            tenant_id: Tenant UUID
            integration_type: Integration type

        Returns:
            Dictionary with 'type' and 'config' keys, or None if not found
        """
        result = await db.execute(
            select(TenantIntegration).where(
                TenantIntegration.tenant_id == tenant_id,
                TenantIntegration.integration_type == integration_type,
                TenantIntegration.is_active == True
            )
        )
        integration = result.scalar_one_or_none()

        if not integration:
            return None

        return {
            'type': integration.integration_type,
            'config': integration.integration_config,
            'last_sync_at': integration.last_sync_at,
            'sync_status': integration.sync_status
        }

    async def update_sync_status(
        self,
        integration_type: str,
        status: str,
        error: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> None:
        """
        Update integration sync status after sync attempt

        Args:
            integration_type: Integration type
            status: Sync status ('success', 'error', 'pending')
            error: Error message if status is 'error'
            db: Database session
        """
        tenant = TenantContext.require_tenant()

        async def _update(session: AsyncSession):
            result = await session.execute(
                select(TenantIntegration).where(
                    TenantIntegration.tenant_id == tenant.id,
                    TenantIntegration.integration_type == integration_type
                )
            )
            integration = result.scalar_one_or_none()

            if integration:
                integration.sync_status = status
                integration.sync_error = error
                if status == 'success':
                    from datetime import datetime
                    integration.last_sync_at = datetime.utcnow()
                await session.commit()

        if db:
            await _update(db)
        else:
            async with get_db_context() as session:
                await _update(session)

    async def close_all(self) -> None:
        """Close all cached integration connections"""
        for cache_key, connector in list(self._connectors.items()):
            try:
                # Call close method if available
                if hasattr(connector, 'close'):
                    await connector.close()
                logger.info(f"Closed integration connector: {cache_key}")
            except Exception as e:
                logger.warning(f"Error closing connector {cache_key}: {e}")

        self._connectors.clear()

    async def close_tenant_connections(self, tenant_id: str) -> None:
        """
        Close all cached connections for a specific tenant

        Useful when tenant integration configuration changes.

        Args:
            tenant_id: Tenant UUID
        """
        keys_to_remove = [
            key for key in self._connectors.keys()
            if key.startswith(f"{tenant_id}_")
        ]

        for key in keys_to_remove:
            try:
                connector = self._connectors[key]
                if hasattr(connector, 'close'):
                    await connector.close()
                del self._connectors[key]
                logger.info(f"Closed tenant integration connector: {key}")
            except Exception as e:
                logger.warning(f"Error closing tenant connector {key}: {e}")


# Global integration router instance
_integration_router: Optional[IntegrationRouter] = None


def get_integration_router() -> IntegrationRouter:
    """
    Get global integration router instance (singleton)

    Returns:
        IntegrationRouter: Global router instance
    """
    global _integration_router
    if _integration_router is None:
        _integration_router = IntegrationRouter()
    return _integration_router


async def get_tenant_integration(integration_type: str) -> BaseConnector:
    """
    Convenience function to get current tenant's integration connector

    Args:
        integration_type: Integration type ('netsuite', 'adp', etc.)

    Returns:
        BaseConnector: Tenant's integration connector

    Raises:
        ValueError: If no tenant context or no integration configured
    """
    router = get_integration_router()
    return await router.get_connector(integration_type)
