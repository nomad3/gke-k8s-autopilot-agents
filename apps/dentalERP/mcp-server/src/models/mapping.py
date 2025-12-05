"""Database models for MCP Server"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.sql import func
import enum

from ..core.database import Base


class IntegrationTypeEnum(str, enum.Enum):
    """Integration types"""
    ADP = "adp"
    NETSUITE = "netsuite"
    DENTALINTEL = "dentalintel"
    EAGLESOFT = "eaglesoft"
    DENTRIX = "dentrix"
    SNOWFLAKE = "snowflake"
    QUICKBOOKS = "quickbooks"


class IntegrationStatusEnum(str, enum.Enum):
    """Integration status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PENDING = "pending"


class SyncStatusEnum(str, enum.Enum):
    """Sync job status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Mapping(Base):
    """Entity mapping between systems"""
    __tablename__ = "mappings"

    id = Column(Integer, primary_key=True, index=True)
    source_system = Column(String(100), nullable=False, index=True)
    source_id = Column(String(255), nullable=False, index=True)
    target_system = Column(String(100), nullable=False, index=True)
    target_id = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    extra_data = Column(JSON, nullable=True)  # Renamed from 'metadata' (reserved by SQLAlchemy)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class IntegrationStatus(Base):
    """Integration status tracking"""
    __tablename__ = "integration_statuses"

    id = Column(Integer, primary_key=True, index=True)
    integration_type = Column(Enum(IntegrationTypeEnum), nullable=False, unique=True)
    status = Column(Enum(IntegrationStatusEnum), nullable=False, default=IntegrationStatusEnum.PENDING)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    next_sync_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)  # Renamed from 'metadata' (reserved by SQLAlchemy)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SyncJob(Base):
    """Sync job tracking"""
    __tablename__ = "sync_jobs"

    id = Column(String(100), primary_key=True, index=True)
    integration_type = Column(Enum(IntegrationTypeEnum), nullable=False)
    entity_types = Column(JSON, nullable=False)  # List of entity types to sync
    location_ids = Column(JSON, nullable=True)  # Optional location filter
    sync_mode = Column(String(20), nullable=False, default="incremental")  # full or incremental
    status = Column(Enum(SyncStatusEnum), nullable=False, default=SyncStatusEnum.PENDING)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    records_processed = Column(Integer, nullable=True, default=0)
    errors = Column(JSON, nullable=True)  # List of error messages
    extra_data = Column(JSON, nullable=True)  # Renamed from 'metadata' (reserved by SQLAlchemy)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
