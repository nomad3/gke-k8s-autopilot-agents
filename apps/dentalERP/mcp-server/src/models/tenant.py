"""Tenant models for multi-tenant support"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..core.database import Base


class TenantStatusEnum(str, enum.Enum):
    """Tenant status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class WarehouseTypeEnum(str, enum.Enum):
    """Data warehouse types"""
    SNOWFLAKE = "snowflake"
    DATABRICKS = "databricks"


class TenantRoleEnum(str, enum.Enum):
    """Tenant user roles"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class IntegrationTypeEnum(str, enum.Enum):
    """External integration types"""
    NETSUITE = "netsuite"
    ADP = "adp"
    DENTRIX = "dentrix"
    EAGLESOFT = "eaglesoft"
    DENTALINTEL = "dentalintel"
    OPEN_DENTAL = "opendental"
    CURVE_DENTAL = "curvedental"


class Tenant(Base):
    """Tenant registry - represents a single organization/customer"""
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    tenant_code = Column(String(50), unique=True, nullable=False, index=True)  # e.g., 'dental_001'
    tenant_name = Column(String(255), nullable=False)  # e.g., 'Smiles Dental Group'
    industry = Column(String(50), nullable=False)  # 'dental', 'medical', 'veterinary'
    products = Column(JSON, nullable=False)  # ['dentalerp', 'medicalerp']
    status = Column(String(20), nullable=False, default=TenantStatusEnum.ACTIVE.value, index=True)
    settings = Column(JSON, nullable=True)  # Tenant-specific settings
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    warehouses = relationship("TenantWarehouse", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("TenantUser", back_populates="tenant", cascade="all, delete-orphan")
    api_keys = relationship("TenantAPIKey", back_populates="tenant", cascade="all, delete-orphan")
    integrations = relationship("TenantIntegration", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant {self.tenant_code} ({self.tenant_name})>"


class TenantWarehouse(Base):
    """Data warehouse configurations per tenant"""
    __tablename__ = "tenant_warehouses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    warehouse_type = Column(String(20), nullable=False, index=True)  # 'snowflake', 'databricks'
    warehouse_config = Column(JSON, nullable=False)  # Connection details (encrypted)
    is_primary = Column(Boolean, default=False)  # Primary warehouse for this tenant
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="warehouses")

    def __repr__(self):
        return f"<TenantWarehouse {self.warehouse_type} for tenant {self.tenant_id}>"


class TenantUser(Base):
    """User-tenant mapping"""
    __tablename__ = "tenant_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)  # Email or external user ID
    role = Column(String(50), nullable=False)  # 'admin', 'user', 'viewer'
    permissions = Column(JSON, nullable=True)  # Product-specific permissions
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="users")

    def __repr__(self):
        return f"<TenantUser {self.user_id} in tenant {self.tenant_id}>"


class TenantAPIKey(Base):
    """Tenant-specific API keys"""
    __tablename__ = "tenant_api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    key_hash = Column(String(255), nullable=False)  # Hashed API key
    key_prefix = Column(String(20), nullable=False, index=True)  # First 8 chars for identification
    name = Column(String(100), nullable=True)  # Key description
    permissions = Column(JSON, nullable=True)  # Scoped permissions
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys")

    def __repr__(self):
        return f"<TenantAPIKey {self.key_prefix}... for tenant {self.tenant_id}>"


class TenantIntegration(Base):
    """External integration credentials per tenant"""
    __tablename__ = "tenant_integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    integration_type = Column(String(50), nullable=False, index=True)  # 'netsuite', 'adp', 'dentrix', etc.
    integration_config = Column(JSON, nullable=False)  # Encrypted credentials & config
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)  # Last successful sync
    sync_status = Column(String(50), nullable=True)  # 'success', 'error', 'pending'
    sync_error = Column(Text, nullable=True)  # Last error message
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="integrations")

    def __repr__(self):
        return f"<TenantIntegration {self.integration_type} for tenant {self.tenant_id}>"
