"""Warehouse routing service for multi-tenant warehouse abstraction"""

from typing import Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..connectors.warehouse_base import BaseWarehouseConnector
from ..connectors.snowflake import SnowflakeConnector
from ..connectors.databricks import DatabricksConnector
from ..core.tenant import TenantContext
from ..core.database import AsyncSessionLocal
from ..models.tenant import TenantWarehouse
from ..utils.logger import logger


class WarehouseRouter:
    """
    Route queries to the appropriate data warehouse for current tenant

    Features:
    - Automatic tenant detection from context
    - Connection pooling (cached connectors per tenant)
    - Support for multiple warehouses per tenant
    - Primary warehouse selection
    - Graceful error handling
    """

    def __init__(self):
        """Initialize warehouse router with connection cache"""
        self._connectors: Dict[str, BaseWarehouseConnector] = {}

    async def get_connector(
        self,
        warehouse_type: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> BaseWarehouseConnector:
        """
        Get warehouse connector for current tenant

        Args:
            warehouse_type: Specific warehouse type ('snowflake', 'databricks')
                           If None, uses tenant's primary warehouse
            db: Database session (optional, creates new if None)

        Returns:
            BaseWarehouseConnector: Warehouse connector instance

        Raises:
            ValueError: If no tenant context or no warehouse configured
        """
        # Get current tenant from context
        tenant = TenantContext.require_tenant()

        # Get or create database session
        if db is None:
            async with AsyncSessionLocal() as db_session:
                return await self._get_connector_internal(
                    tenant.id, warehouse_type, db_session
                )
        else:
            return await self._get_connector_internal(
                tenant.id, warehouse_type, db
            )

    async def _get_connector_internal(
        self,
        tenant_id: str,
        warehouse_type: Optional[str],
        db: AsyncSession
    ) -> BaseWarehouseConnector:
        """Internal method to get connector with database session"""

        # Get tenant's warehouse configuration
        if warehouse_type:
            warehouse_config = await self._get_warehouse_config(
                db, tenant_id, warehouse_type
            )
        else:
            warehouse_config = await self._get_primary_warehouse_config(db, tenant_id)

        if not warehouse_config:
            tenant = TenantContext.get_tenant()
            raise ValueError(
                f"No warehouse configuration found for tenant {tenant.tenant_code}"
            )

        # Create cache key
        cache_key = f"{tenant_id}_{warehouse_config['type']}"

        # Return cached connector if available
        if cache_key in self._connectors:
            connector = self._connectors[cache_key]
            # Check if connection is still alive
            if await connector.check_connection():
                logger.debug(f"Reusing cached {warehouse_config['type']} connector for tenant {tenant_id}")
                return connector
            else:
                # Connection dead, remove from cache
                logger.warning(f"Cached connector dead, recreating for tenant {tenant_id}")
                await connector.close()
                del self._connectors[cache_key]

        # Create new connector
        connector = self._create_connector(
            warehouse_config['type'],
            warehouse_config['config']
        )

        await connector.connect()
        self._connectors[cache_key] = connector

        logger.info(
            f"Created new {warehouse_config['type']} connector for tenant {tenant_id}"
        )

        return connector

    def _create_connector(
        self,
        warehouse_type: str,
        config: Dict[str, Any]
    ) -> BaseWarehouseConnector:
        """
        Factory method to create warehouse connector

        Args:
            warehouse_type: Type of warehouse ('snowflake', 'databricks')
            config: Warehouse configuration dictionary

        Returns:
            BaseWarehouseConnector: Connector instance

        Raises:
            ValueError: If unsupported warehouse type
        """
        if warehouse_type == 'snowflake':
            # Check if config signals to use environment variables
            if config.get('use_env_credentials'):
                logger.info("Using Snowflake credentials from environment variables")
                # Pass minimal config with just the schema override if present
                minimal_config = {}
                if 'schema' in config:
                    minimal_config['schema'] = config['schema']
                # Pass None to use settings from environment (SnowflakeConnector will use global settings)
                # But we need to merge any overrides like schema
                from ..core.config import settings
                env_config = {
                    'account': settings.snowflake_account,
                    'user': settings.snowflake_user,
                    'password': settings.snowflake_password,
                    'warehouse': settings.snowflake_warehouse,
                    'database': settings.snowflake_database,
                    'schema': config.get('schema', settings.snowflake_schema or 'PUBLIC'),
                    'role': settings.snowflake_role,
                }
                return SnowflakeConnector(env_config)
            else:
                return SnowflakeConnector(config)
        elif warehouse_type == 'databricks':
            return DatabricksConnector(config)
        else:
            raise ValueError(f"Unsupported warehouse type: {warehouse_type}")

    async def _get_warehouse_config(
        self,
        db: AsyncSession,
        tenant_id: str,
        warehouse_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get warehouse configuration for tenant by type

        Args:
            db: Database session
            tenant_id: Tenant UUID
            warehouse_type: Warehouse type to find

        Returns:
            Dictionary with 'type' and 'config' keys, or None if not found
        """
        result = await db.execute(
            select(TenantWarehouse).where(
                TenantWarehouse.tenant_id == tenant_id,
                TenantWarehouse.warehouse_type == warehouse_type,
                TenantWarehouse.is_active == True
            )
        )
        warehouse = result.scalar_one_or_none()

        if not warehouse:
            return None

        return {
            'type': warehouse.warehouse_type,
            'config': warehouse.warehouse_config
        }

    async def _get_primary_warehouse_config(
        self,
        db: AsyncSession,
        tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get primary warehouse configuration for tenant

        Args:
            db: Database session
            tenant_id: Tenant UUID

        Returns:
            Dictionary with 'type' and 'config' keys, or None if not found
        """
        result = await db.execute(
            select(TenantWarehouse).where(
                TenantWarehouse.tenant_id == tenant_id,
                TenantWarehouse.is_primary == True,
                TenantWarehouse.is_active == True
            )
        )
        warehouse = result.scalar_one_or_none()

        if not warehouse:
            # Fallback: get any active warehouse
            result = await db.execute(
                select(TenantWarehouse).where(
                    TenantWarehouse.tenant_id == tenant_id,
                    TenantWarehouse.is_active == True
                ).limit(1)
            )
            warehouse = result.scalar_one_or_none()

        if not warehouse:
            return None

        return {
            'type': warehouse.warehouse_type,
            'config': warehouse.warehouse_config
        }

    async def close_all(self) -> None:
        """Close all cached warehouse connections"""
        for cache_key, connector in list(self._connectors.items()):
            try:
                await connector.close()
                logger.info(f"Closed warehouse connector: {cache_key}")
            except Exception as e:
                logger.warning(f"Error closing connector {cache_key}: {e}")

        self._connectors.clear()

    async def close_tenant_connections(self, tenant_id: str) -> None:
        """
        Close all cached connections for a specific tenant

        Useful when tenant warehouse configuration changes.

        Args:
            tenant_id: Tenant UUID
        """
        keys_to_remove = [
            key for key in self._connectors.keys()
            if key.startswith(f"{tenant_id}_")
        ]

        for key in keys_to_remove:
            try:
                await self._connectors[key].close()
                del self._connectors[key]
                logger.info(f"Closed tenant warehouse connector: {key}")
            except Exception as e:
                logger.warning(f"Error closing tenant connector {key}: {e}")

    async def get_warehouse_health(
        self,
        tenant_id: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Get health status of all warehouses for tenant(s)

        Args:
            tenant_id: Optional tenant UUID (if None, checks current tenant)
            db: Database session

        Returns:
            Dictionary with warehouse health information
        """
        if not tenant_id:
            tenant = TenantContext.require_tenant()
            tenant_id = tenant.id

        health_info = {
            'tenant_id': tenant_id,
            'warehouses': [],
            'overall_status': 'healthy'
        }

        # Get all tenant warehouses
        async def _check_warehouses(session: AsyncSession):
            result = await session.execute(
                select(TenantWarehouse).where(
                    TenantWarehouse.tenant_id == tenant_id,
                    TenantWarehouse.is_active == True
                )
            )
            warehouses = result.scalars().all()

            for wh in warehouses:
                wh_health = {
                    'type': wh.warehouse_type,
                    'is_primary': wh.is_primary,
                    'status': 'unknown',
                    'error': None
                }

                try:
                    # Try to get or create connector
                    cache_key = f"{tenant_id}_{wh.warehouse_type}"
                    if cache_key in self._connectors:
                        connector = self._connectors[cache_key]
                    else:
                        connector = self._create_connector(wh.warehouse_type, wh.warehouse_config)
                        await connector.connect()
                        self._connectors[cache_key] = connector

                    # Check connection health
                    is_healthy = await connector.check_connection()
                    wh_health['status'] = 'healthy' if is_healthy else 'unhealthy'

                    if not is_healthy:
                        health_info['overall_status'] = 'degraded'

                except Exception as e:
                    wh_health['status'] = 'error'
                    wh_health['error'] = str(e)
                    health_info['overall_status'] = 'degraded'
                    logger.error(f"Warehouse health check failed for {wh.warehouse_type}: {e}")

                health_info['warehouses'].append(wh_health)

            # If no primary warehouse is healthy, status is critical
            primary_healthy = any(
                w['is_primary'] and w['status'] == 'healthy'
                for w in health_info['warehouses']
            )
            if not primary_healthy and health_info['warehouses']:
                health_info['overall_status'] = 'critical'

        if db:
            await _check_warehouses(db)
        else:
            async with AsyncSessionLocal() as session:
                await _check_warehouses(session)

        return health_info

    async def get_connector_with_failover(
        self,
        warehouse_type: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> BaseWarehouseConnector:
        """
        Get warehouse connector with automatic failover

        If primary warehouse fails, tries to fall back to secondary warehouses.

        Args:
            warehouse_type: Specific warehouse type (optional)
            db: Database session

        Returns:
            BaseWarehouseConnector: Working warehouse connector

        Raises:
            ConnectionError: If all warehouses fail
        """
        tenant = TenantContext.require_tenant()

        try:
            # Try to get primary or specified warehouse
            return await self.get_connector(warehouse_type, db)
        except (ValueError, ConnectionError) as e:
            logger.warning(f"Primary warehouse failed for tenant {tenant.tenant_code}: {e}")

            # Try failover to any available warehouse
            if not db:
                async with AsyncSessionLocal() as session:
                    return await self._failover_to_backup(tenant.id, session)
            else:
                return await self._failover_to_backup(tenant.id, db)

    async def _failover_to_backup(
        self,
        tenant_id: str,
        db: AsyncSession
    ) -> BaseWarehouseConnector:
        """
        Attempt to fail over to backup warehouse

        Args:
            tenant_id: Tenant UUID
            db: Database session

        Returns:
            BaseWarehouseConnector: Working backup warehouse

        Raises:
            ConnectionError: If no backup warehouses available
        """
        # Get all active warehouses (sorted by is_primary DESC)
        result = await db.execute(
            select(TenantWarehouse).where(
                TenantWarehouse.tenant_id == tenant_id,
                TenantWarehouse.is_active == True
            ).order_by(TenantWarehouse.is_primary.desc())
        )
        warehouses = result.scalars().all()

        if not warehouses:
            raise ConnectionError(f"No active warehouses configured for tenant {tenant_id}")

        # Try each warehouse until one works
        last_error = None
        for wh in warehouses:
            try:
                logger.info(f"Attempting failover to {wh.warehouse_type} warehouse")
                connector = self._create_connector(wh.warehouse_type, wh.warehouse_config)
                await connector.connect()

                # Verify it's actually working
                if await connector.check_connection():
                    logger.info(f"✅ Failover successful to {wh.warehouse_type} warehouse")
                    cache_key = f"{tenant_id}_{wh.warehouse_type}"
                    self._connectors[cache_key] = connector
                    return connector
                else:
                    await connector.close()

            except Exception as e:
                logger.warning(f"Failover to {wh.warehouse_type} failed: {e}")
                last_error = e
                continue

        # All warehouses failed
        raise ConnectionError(
            f"All warehouses failed for tenant {tenant_id}. Last error: {last_error}"
        )


# Global warehouse router instance
_warehouse_router: Optional[WarehouseRouter] = None


def get_warehouse_router() -> WarehouseRouter:
    """
    Get global warehouse router instance (singleton)

    Returns:
        WarehouseRouter: Global router instance
    """
    global _warehouse_router
    if _warehouse_router is None:
        _warehouse_router = WarehouseRouter()
    return _warehouse_router


async def get_tenant_warehouse() -> BaseWarehouseConnector:
    """
    Convenience function to get current tenant's primary warehouse connector

    Returns:
        BaseWarehouseConnector: Tenant's primary warehouse connector

    Raises:
        ValueError: If no tenant context or no warehouse configured
    """
    router = get_warehouse_router()
    return await router.get_connector()
