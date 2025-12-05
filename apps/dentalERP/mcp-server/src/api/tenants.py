"""Tenant management API endpoints"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..services.tenant_service import TenantService

router = APIRouter(prefix="/api/v1/tenants", tags=["Tenants"])


# Pydantic models for request/response
class TenantCreate(BaseModel):
    tenant_code: str
    tenant_name: str
    industry: str
    products: List[str]
    settings: Optional[dict] = None


class TenantUpdate(BaseModel):
    tenant_name: Optional[str] = None
    industry: Optional[str] = None
    products: Optional[List[str]] = None
    status: Optional[str] = None
    settings: Optional[dict] = None


class TenantResponse(BaseModel):
    id: UUID
    tenant_code: str
    tenant_name: str
    industry: str
    products: List[str]
    status: str
    settings: Optional[dict] = None

    class Config:
        from_attributes = True


class WarehouseCreate(BaseModel):
    warehouse_type: str  # 'snowflake' or 'databricks'
    warehouse_config: dict
    is_primary: bool = False


class WarehouseResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    warehouse_type: str
    is_primary: bool
    is_active: bool

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    user_id: str
    role: str  # 'admin', 'user', 'viewer'
    permissions: Optional[dict] = None


class UserResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: str
    role: str
    permissions: Optional[dict] = None

    class Config:
        from_attributes = True


# API Endpoints

@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all tenants with optional filtering"""
    tenants = await TenantService.list_tenants(db, skip=skip, limit=limit, status=status)
    return tenants


@router.get("/{tenant_code}", response_model=TenantResponse)
async def get_tenant(
    tenant_code: str,
    db: AsyncSession = Depends(get_db)
):
    """Get tenant by code"""
    tenant = await TenantService.get_by_code(db, tenant_code)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant '{tenant_code}' not found")
    return tenant


@router.post("/", response_model=TenantResponse, status_code=201)
async def create_tenant(
    tenant: TenantCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new tenant"""
    # Check if tenant code already exists
    existing = await TenantService.get_by_code(db, tenant.tenant_code)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Tenant with code '{tenant.tenant_code}' already exists"
        )

    new_tenant = await TenantService.create_tenant(
        db,
        tenant_code=tenant.tenant_code,
        tenant_name=tenant.tenant_name,
        industry=tenant.industry,
        products=tenant.products,
        settings=tenant.settings
    )
    return new_tenant


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    tenant_update: TenantUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update tenant"""
    # Filter out None values
    update_data = {k: v for k, v in tenant_update.dict().items() if v is not None}

    updated_tenant = await TenantService.update_tenant(db, tenant_id, **update_data)
    if not updated_tenant:
        raise HTTPException(status_code=404, detail=f"Tenant '{tenant_id}' not found")

    return updated_tenant


@router.delete("/{tenant_id}", status_code=204)
async def delete_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete tenant (cascade deletes all related data)"""
    success = await TenantService.delete_tenant(db, tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Tenant '{tenant_id}' not found")


@router.get("/{tenant_id}/warehouses", response_model=List[WarehouseResponse])
async def list_tenant_warehouses(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """List all warehouses for a tenant"""
    warehouses = await TenantService.get_tenant_warehouses(db, tenant_id)
    return warehouses


@router.post("/{tenant_id}/warehouses", response_model=WarehouseResponse, status_code=201)
async def add_tenant_warehouse(
    tenant_id: UUID,
    warehouse: WarehouseCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add warehouse configuration to tenant"""
    # Verify tenant exists
    tenant_obj = await TenantService.get_by_id(db, tenant_id)
    if not tenant_obj:
        raise HTTPException(status_code=404, detail=f"Tenant '{tenant_id}' not found")

    new_warehouse = await TenantService.add_warehouse(
        db,
        tenant_id=tenant_id,
        warehouse_type=warehouse.warehouse_type,
        warehouse_config=warehouse.warehouse_config,
        is_primary=warehouse.is_primary
    )
    return new_warehouse


@router.get("/{tenant_id}/users", response_model=List[UserResponse])
async def list_tenant_users(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """List all users for a tenant"""
    users = await TenantService.get_tenant_users(db, tenant_id)
    return users


@router.post("/{tenant_id}/users", response_model=UserResponse, status_code=201)
async def add_tenant_user(
    tenant_id: UUID,
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add user to tenant"""
    # Verify tenant exists
    tenant_obj = await TenantService.get_by_id(db, tenant_id)
    if not tenant_obj:
        raise HTTPException(status_code=404, detail=f"Tenant '{tenant_id}' not found")

    new_user = await TenantService.add_user(
        db,
        tenant_id=tenant_id,
        user_id=user.user_id,
        role=user.role,
        permissions=user.permissions
    )
    return new_user
