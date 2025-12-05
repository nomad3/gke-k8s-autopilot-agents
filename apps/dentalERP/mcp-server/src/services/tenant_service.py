"""Tenant management service"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.tenant import Tenant, TenantWarehouse, TenantUser, TenantAPIKey


class TenantService:
    """Service for tenant CRUD operations"""

    @staticmethod
    async def get_by_id(db: AsyncSession, tenant_id: UUID) -> Optional[Tenant]:
        """Get tenant by ID"""
        result = await db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_code(db: AsyncSession, tenant_code: str) -> Optional[Tenant]:
        """Get tenant by code"""
        result = await db.execute(
            select(Tenant).where(Tenant.tenant_code == tenant_code)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_tenants(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Tenant]:
        """List all tenants with optional filtering"""
        query = select(Tenant)

        if status:
            query = query.where(Tenant.status == status)

        query = query.offset(skip).limit(limit).order_by(Tenant.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create_tenant(
        db: AsyncSession,
        tenant_code: str,
        tenant_name: str,
        industry: str,
        products: list,
        settings: dict = None
    ) -> Tenant:
        """Create a new tenant"""
        tenant = Tenant(
            tenant_code=tenant_code,
            tenant_name=tenant_name,
            industry=industry,
            products=products,
            status="active",
            settings=settings or {}
        )
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
        return tenant

    @staticmethod
    async def update_tenant(
        db: AsyncSession,
        tenant_id: UUID,
        **kwargs
    ) -> Optional[Tenant]:
        """Update tenant fields"""
        tenant = await TenantService.get_by_id(db, tenant_id)
        if not tenant:
            return None

        for key, value in kwargs.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)

        await db.commit()
        await db.refresh(tenant)
        return tenant

    @staticmethod
    async def delete_tenant(db: AsyncSession, tenant_id: UUID) -> bool:
        """Delete tenant (cascade deletes warehouses, users, api_keys)"""
        tenant = await TenantService.get_by_id(db, tenant_id)
        if not tenant:
            return False

        await db.delete(tenant)
        await db.commit()
        return True

    @staticmethod
    async def get_tenant_warehouses(
        db: AsyncSession,
        tenant_id: UUID
    ) -> List[TenantWarehouse]:
        """Get all warehouses for a tenant"""
        result = await db.execute(
            select(TenantWarehouse).where(TenantWarehouse.tenant_id == tenant_id)
        )
        return result.scalars().all()

    @staticmethod
    async def add_warehouse(
        db: AsyncSession,
        tenant_id: UUID,
        warehouse_type: str,
        warehouse_config: dict,
        is_primary: bool = False
    ) -> TenantWarehouse:
        """Add warehouse configuration to tenant"""
        warehouse = TenantWarehouse(
            tenant_id=tenant_id,
            warehouse_type=warehouse_type,
            warehouse_config=warehouse_config,
            is_primary=is_primary,
            is_active=True
        )
        db.add(warehouse)
        await db.commit()
        await db.refresh(warehouse)
        return warehouse

    @staticmethod
    async def get_tenant_users(
        db: AsyncSession,
        tenant_id: UUID
    ) -> List[TenantUser]:
        """Get all users for a tenant"""
        result = await db.execute(
            select(TenantUser).where(TenantUser.tenant_id == tenant_id)
        )
        return result.scalars().all()

    @staticmethod
    async def add_user(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: str,
        role: str,
        permissions: dict = None
    ) -> TenantUser:
        """Add user to tenant"""
        user = TenantUser(
            tenant_id=tenant_id,
            user_id=user_id,
            role=role,
            permissions=permissions or {}
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
