"""
NetSuite Sync API Endpoints
Manual trigger and status endpoints
"""

from fastapi import APIRouter, HTTPException, Header, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

from ..services.netsuite_sync_orchestrator import NetSuiteSyncOrchestrator
from ..services.snowflake_netsuite_loader import NetSuiteToSnowflakeLoader
from ..core.tenant import TenantContext
from ..core.database import get_db_context
from ..core.security import get_api_key_header
from ..utils.logger import logger


router = APIRouter(prefix="/api/v1/netsuite", tags=["netsuite"])


class SyncRequest(BaseModel):
    full_sync: bool = False
    record_types: Optional[list[str]] = None
    from_date: Optional[str] = None  # YYYY-MM-DD format
    limit: Optional[int] = None  # None = fetch ALL records automatically
    use_suiteql: bool = True  # Default to SuiteQL (bypasses User Event Scripts)


class SyncResponse(BaseModel):
    sync_id: str
    status: str
    message: str
    started_at: datetime


@router.post("/sync/trigger", response_model=SyncResponse)
async def trigger_sync(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key_header),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """
    Manually trigger NetSuite sync

    Args:
        full_sync: If True, ignore last sync time (full refresh)
        record_types: Optional list of specific record types to sync
    """

    # Get tenant
    tenant = TenantContext.get_tenant()
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant not found")

    tenant_id = str(tenant.id)

    # Start sync in background
    orchestrator = NetSuiteSyncOrchestrator()

    sync_id = f"manual_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    async def run_sync():
        try:
            await orchestrator.sync_tenant(
                tenant_id=tenant_id,
                incremental=not request.full_sync,
                record_types=request.record_types,
                from_date=request.from_date,
                limit=request.limit
            )
        except Exception as e:
            logger.error(f"Sync failed: {e}")

    background_tasks.add_task(run_sync)

    return SyncResponse(
        sync_id=sync_id,
        status="started",
        message=f"Sync started for tenant {tenant.tenant_code}",
        started_at=datetime.utcnow()
    )


@router.get("/sync/status")
async def get_sync_status(
    api_key: str = Depends(get_api_key_header),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """Get current sync status for tenant"""

    tenant = TenantContext.get_tenant()
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant not found")

    # Query sync state from database
    from ..core.database import get_db
    from sqlalchemy import text

    async with get_db_context() as session:
        result = await session.execute(
            text("""
                SELECT record_type, last_sync_timestamp, last_sync_status,
                       records_synced, error_message, retry_count
                FROM netsuite_sync_state
                WHERE tenant_id = :tenant_id
                ORDER BY last_sync_timestamp DESC NULLS LAST
            """),
            {"tenant_id": str(tenant.id)}
        )

        rows = result.fetchall()

        sync_statuses = []
        for row in rows:
            sync_statuses.append({
                "record_type": row[0],
                "last_sync": row[1].isoformat() if row[1] else None,
                "status": row[2],
                "records_synced": row[3],
                "error": row[4],
                "retry_count": row[5]
            })

        return {
            "tenant_code": tenant.tenant_code,
            "sync_statuses": sync_statuses
        }


@router.post("/sync/test-connection")
async def test_netsuite_connection(
    api_key: str = Depends(get_api_key_header),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """Test NetSuite connection for tenant"""

    tenant = TenantContext.get_tenant()
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant not found")

    loader = NetSuiteToSnowflakeLoader(str(tenant.id))

    try:
        await loader.initialize()

        # Test connection by fetching 1 subsidiary
        response = await loader.netsuite.fetch_data("subsidiary", {"limit": 1})

        if response.success:
            return {
                "status": "success",
                "message": "NetSuite connection successful",
                "sample_data": response.data[0] if response.data else None
            }
        else:
            return {
                "status": "failed",
                "message": response.error
            }
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
