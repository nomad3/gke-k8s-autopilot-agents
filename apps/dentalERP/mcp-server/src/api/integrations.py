"""Integration management endpoints"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import get_api_key_header
from ..models.mapping import IntegrationStatus, IntegrationTypeEnum, SyncJob, SyncStatusEnum
from ..services.sync_orchestrator import get_sync_orchestrator
from ..utils.logger import logger

router = APIRouter(prefix="/api/v1", tags=["integrations"])

# Get orchestrator
sync_orchestrator = get_sync_orchestrator()


class IntegrationStatusResponse(BaseModel):
    """Integration status response"""
    integration_type: str
    status: str
    last_sync_at: Optional[str] = None
    next_sync_at: Optional[str] = None
    error_message: Optional[str] = None
    extra_data: Optional[dict] = None


class SyncRequest(BaseModel):
    """Sync request model"""
    integration_type: str
    entity_types: List[str]
    location_ids: Optional[List[str]] = None
    sync_mode: str = "incremental"


class SyncResponse(BaseModel):
    """Sync response model"""
    sync_id: str
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    records_processed: Optional[int] = 0
    errors: Optional[List[str]] = None


@router.get("/integrations/status", response_model=List[IntegrationStatusResponse])
async def get_integration_status(
    integration_type: Optional[str] = Query(None, alias="type"),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key_header)
):
    """
    Get integration status

    Args:
        integration_type: Optional integration type filter
        db: Database session
        api_key: Verified API key

    Returns:
        List[IntegrationStatusResponse]: Integration statuses
    """
    query = select(IntegrationStatus)

    if integration_type:
        query = query.where(IntegrationStatus.integration_type == integration_type)

    result = await db.execute(query)
    statuses = result.scalars().all()

    # If no statuses exist, create defaults
    if not statuses:
        default_integrations = [
            IntegrationTypeEnum.ADP,
            IntegrationTypeEnum.NETSUITE,
            IntegrationTypeEnum.DENTALINTEL,
            IntegrationTypeEnum.EAGLESOFT,
            IntegrationTypeEnum.DENTRIX,
        ]

        for integration in default_integrations:
            status = IntegrationStatus(integration_type=integration)
            db.add(status)

        await db.commit()

        result = await db.execute(query)
        statuses = result.scalars().all()

    return [
        IntegrationStatusResponse(
            integration_type=status.integration_type.value,
            status=status.status.value,
            last_sync_at=status.last_sync_at.isoformat() if status.last_sync_at else None,
            next_sync_at=status.next_sync_at.isoformat() if status.next_sync_at else None,
            error_message=status.error_message,
            extra_data=status.extra_data
        )
        for status in statuses
    ]


@router.post("/sync/run", response_model=SyncResponse)
async def trigger_sync(
    request: SyncRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key_header)
):
    """
    Trigger a data sync job

    Args:
        request: Sync request data
        db: Database session
        api_key: Verified API key

    Returns:
        SyncResponse: Sync job information
    """
    logger.info(f"Triggering sync for {request.integration_type}")

    # Create and execute sync job via orchestrator
    sync_job = await sync_orchestrator.create_and_execute_sync(
        db=db,
        integration_type=request.integration_type,
        entity_types=request.entity_types,
        location_ids=request.location_ids,
        sync_mode=request.sync_mode
    )

    logger.info(f"Sync job {sync_job.id} {sync_job.status.value}")

    return SyncResponse(
        sync_id=sync_job.id,
        status=sync_job.status.value,
        started_at=sync_job.started_at.isoformat() if sync_job.started_at else None,
        completed_at=sync_job.completed_at.isoformat() if sync_job.completed_at else None,
        records_processed=sync_job.records_processed,
        errors=sync_job.errors
    )


@router.get("/sync/{sync_id}", response_model=SyncResponse)
async def get_sync_status(
    sync_id: str,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key_header)
):
    """
    Get sync job status

    Args:
        sync_id: Sync job ID
        db: Database session
        api_key: Verified API key

    Returns:
        SyncResponse: Sync job information
    """
    result = await db.execute(select(SyncJob).where(SyncJob.id == sync_id))
    sync_job = result.scalar_one_or_none()

    if not sync_job:
        return SyncResponse(
            sync_id=sync_id,
            status="not_found",
            records_processed=0
        )

    return SyncResponse(
        sync_id=sync_job.id,
        status=sync_job.status.value,
        started_at=sync_job.started_at.isoformat() if sync_job.started_at else None,
        completed_at=sync_job.completed_at.isoformat() if sync_job.completed_at else None,
        records_processed=sync_job.records_processed,
        errors=sync_job.errors
    )
