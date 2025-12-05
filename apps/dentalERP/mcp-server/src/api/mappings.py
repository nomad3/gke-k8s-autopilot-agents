"""Mapping management endpoints"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import get_api_key_header
from ..models.mapping import Mapping
from ..utils.logger import logger

router = APIRouter(prefix="/api/v1/mappings", tags=["mappings"])


class MappingCreate(BaseModel):
    """Request model for creating a mapping"""
    source_system: str
    source_id: str
    target_system: str
    target_id: str
    entity_type: str
    extra_data: Optional[dict] = None


class MappingResponse(BaseModel):
    """Response model for mapping"""
    id: int
    source_system: str
    source_id: str
    target_system: str
    target_id: str
    entity_type: str
    extra_data: Optional[dict] = None

    class Config:
        from_attributes = True


@router.post("/register", response_model=MappingResponse)
async def register_mapping(
    mapping: MappingCreate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key_header)
):
    """
    Register a new ID mapping between systems

    Args:
        mapping: Mapping data
        db: Database session
        api_key: Verified API key

    Returns:
        MappingResponse: Created mapping
    """
    logger.info(f"Registering mapping: {mapping.source_system} -> {mapping.target_system}")

    # Create mapping
    db_mapping = Mapping(**mapping.model_dump())
    db.add(db_mapping)
    await db.commit()
    await db.refresh(db_mapping)

    return db_mapping


@router.get("/{entity_type}", response_model=List[MappingResponse])
async def get_mappings(
    entity_type: str,
    source_system: Optional[str] = Query(None),
    target_system: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key_header)
):
    """
    Get all mappings for an entity type

    Args:
        entity_type: Entity type to filter by
        source_system: Optional source system filter
        target_system: Optional target system filter
        db: Database session
        api_key: Verified API key

    Returns:
        List[MappingResponse]: List of mappings
    """
    query = select(Mapping).where(Mapping.entity_type == entity_type)

    if source_system:
        query = query.where(Mapping.source_system == source_system)
    if target_system:
        query = query.where(Mapping.target_system == target_system)

    result = await db.execute(query)
    mappings = result.scalars().all()

    return mappings
