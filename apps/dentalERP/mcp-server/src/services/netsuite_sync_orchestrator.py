"""
NetSuite Sync Orchestrator
Coordinates incremental syncs with retry logic
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .snowflake_netsuite_loader import NetSuiteToSnowflakeLoader
from ..core.database import get_db_context
from ..utils.logger import logger
from sqlalchemy import text


class NetSuiteSyncOrchestrator:
    """Orchestrate NetSuite syncs across all tenants"""

    async def sync_all_tenants(self, full_sync: bool = False):
        """
        Sync all tenants that have NetSuite integration

        Args:
            full_sync: If True, ignore last_sync_time (full refresh)
        """
        # Get all tenants with NetSuite integration
        tenants = await self._get_netsuite_tenants()

        logger.info(f"Starting sync for {len(tenants)} tenants (full_sync={full_sync})")

        for tenant in tenants:
            try:
                await self.sync_tenant(
                    tenant_id=tenant["id"],
                    incremental=not full_sync
                )
            except Exception as e:
                logger.error(f"Failed to sync tenant {tenant['id']}: {e}")

    async def sync_tenant(
        self,
        tenant_id: str,
        incremental: bool = True,
        record_types: Optional[List[str]] = None,
        from_date: Optional[str] = None,
        limit: Optional[int] = 100
    ):
        """
        Sync single tenant with retry logic

        Args:
            tenant_id: Tenant UUID
            incremental: Use incremental sync (vs full)
            record_types: Optional list of specific record types to sync. If None, syncs all.
            from_date: Optional start date for sync (YYYY-MM-DD). Overrides incremental logic.
            limit: Max records per subsidiary
        """
        loader = NetSuiteToSnowflakeLoader(tenant_id)

        retry_count = 0
        max_retries = 4
        backoff_seconds = [60, 120, 300, 600]  # 1m, 2m, 5m, 10m

        while retry_count <= max_retries:
            try:
                results = await loader.sync_all_record_types(
                    incremental=incremental,
                    record_types=record_types,
                    from_date=from_date,
                    limit=limit
                )

                # Check for failures
                failed_types = [k for k, v in results.items() if v == -1]

                if not failed_types:
                    logger.info(f"✅ Tenant {tenant_id} sync successful: {results}")
                    return results
                else:
                    logger.warning(
                        f"Partial failure for tenant {tenant_id}: "
                        f"failed={failed_types}, success={[k for k, v in results.items() if v != -1]}"
                    )

                    if retry_count < max_retries:
                        wait_time = backoff_seconds[retry_count]
                        logger.info(f"Retrying in {wait_time}s (attempt {retry_count + 1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                        retry_count += 1
                    else:
                        logger.error(f"Max retries reached for tenant {tenant_id}")
                        # Send alert here (email, Slack, etc.)
                        return results

            except Exception as e:
                logger.error(f"Sync error for tenant {tenant_id}: {e}")

                if retry_count < max_retries:
                    wait_time = backoff_seconds[retry_count]
                    logger.info(f"Retrying in {wait_time}s (attempt {retry_count + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    retry_count += 1
                else:
                    logger.error(f"Max retries reached for tenant {tenant_id}")
                    raise

    async def _get_netsuite_tenants(self) -> List[Dict]:
        """Get all tenants with active NetSuite integration"""
        async with get_db_context() as session:
            result = await session.execute(
                text("""
                    SELECT DISTINCT t.id, t.tenant_code, t.tenant_name
                    FROM tenants t
                    JOIN tenant_integrations ti ON t.id = ti.tenant_id
                    WHERE ti.integration_type = 'netsuite'
                      AND ti.status = 'active'
                      AND t.status = 'active'
                """)
            )

            return [
                {"id": str(row[0]), "code": row[1], "name": row[2]}
                for row in result.fetchall()
            ]
