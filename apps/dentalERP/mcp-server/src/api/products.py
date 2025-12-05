"""
Product API endpoints

Provides product management and product-specific API routing.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from ..models.product import (
    Product,
    ProductType,
    ProductFeature,
    ProductStatus,
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    TenantProductAccess
)
from ..services.product_registry import (
    get_product_registry,
    get_tenant_product_registry,
    check_product_access,
    check_product_feature,
    ProductRegistry,
    TenantProductRegistry
)
from ..core.tenant import TenantContext
from ..utils.logger import logger


# Main products router
router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    status: Optional[ProductStatus] = None,
    include_inactive: bool = False
) -> List[ProductResponse]:
    """
    List all available products

    Returns all products registered in the system.
    Does NOT filter by tenant access - use /products/accessible for that.

    Args:
        status: Filter by product status (optional)
        include_inactive: Include deprecated/sunset products

    Returns:
        List of available products
    """
    registry = get_product_registry()
    products = registry.list_all(status=status, include_inactive=include_inactive)

    return [
        ProductResponse(
            id=p.id,
            code=p.code,
            name=p.name,
            description=p.description,
            version=p.version,
            status=p.status,
            api_prefix=p.api_prefix,
            features=p.features,
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in products
    ]


@router.get("/accessible", response_model=List[ProductResponse])
async def list_accessible_products() -> List[ProductResponse]:
    """
    List products accessible to current tenant

    Returns only products that the tenant has access to based on their
    subscription/license configuration.

    Returns:
        List of accessible products for current tenant

    Raises:
        401: If no tenant context
    """
    tenant = TenantContext.require_tenant()
    tenant_registry = get_tenant_product_registry()

    if not tenant_registry:
        logger.warning(f"Tenant {tenant.tenant_code} has no products configured")
        return []

    # Get accessible product codes
    accessible_codes = tenant_registry.list_accessible_products()

    # Get full product details
    registry = get_product_registry()
    products = []
    for code in accessible_codes:
        product = registry.get(code)
        if product:
            products.append(
                ProductResponse(
                    id=product.id,
                    code=product.code,
                    name=product.name,
                    description=product.description,
                    version=product.version,
                    status=product.status,
                    api_prefix=product.api_prefix,
                    features=product.features,
                    created_at=product.created_at,
                    updated_at=product.updated_at
                )
            )

    return products


@router.get("/{product_code}", response_model=ProductResponse)
async def get_product(product_code: str) -> ProductResponse:
    """
    Get product details by code

    Args:
        product_code: Product code (e.g., 'dentalerp')

    Returns:
        Product details

    Raises:
        404: If product not found
    """
    registry = get_product_registry()
    product = registry.get(product_code)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_code}' not found"
        )

    return ProductResponse(
        id=product.id,
        code=product.code,
        name=product.name,
        description=product.description,
        version=product.version,
        status=product.status,
        api_prefix=product.api_prefix,
        features=product.features,
        created_at=product.created_at,
        updated_at=product.updated_at
    )


@router.get("/{product_code}/access")
async def check_product_access_endpoint(product_code: str) -> dict:
    """
    Check if current tenant has access to product

    Args:
        product_code: Product code to check

    Returns:
        Access information including enabled features

    Raises:
        401: If no tenant context
        404: If product not found
    """
    tenant = TenantContext.require_tenant()

    # Verify product exists
    registry = get_product_registry()
    product = registry.get(product_code)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_code}' not found"
        )

    # Check tenant access
    tenant_registry = get_tenant_product_registry()
    if not tenant_registry:
        return {
            "tenant_code": tenant.tenant_code,
            "product_code": product_code,
            "has_access": False,
            "reason": "No products configured for tenant"
        }

    has_access = tenant_registry.has_access(product_code)
    access_config = tenant_registry.get_access(product_code)

    return {
        "tenant_code": tenant.tenant_code,
        "product_code": product_code,
        "has_access": has_access,
        "configuration": access_config.dict() if access_config else None
    }


@router.get("/{product_code}/features")
async def list_product_features(product_code: str) -> dict:
    """
    List all features for a product

    Args:
        product_code: Product code

    Returns:
        Product features and tenant's access to them

    Raises:
        401: If no tenant context
        404: If product not found
    """
    tenant = TenantContext.require_tenant()

    # Get product
    registry = get_product_registry()
    product = registry.get(product_code)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_code}' not found"
        )

    # Get tenant access
    tenant_registry = get_tenant_product_registry()
    tenant_access = tenant_registry.get_access(product_code) if tenant_registry else None

    # Build feature access map
    feature_access = {}
    for feature in product.features:
        has_access = tenant_registry.has_feature(product_code, feature) if tenant_registry else False
        feature_access[feature.value] = {
            "name": feature.value,
            "accessible": has_access
        }

    return {
        "product_code": product_code,
        "tenant_code": tenant.tenant_code,
        "all_features": [f.value for f in product.features],
        "tenant_features": [f.value for f in tenant_access.features] if tenant_access else [],
        "feature_access": feature_access
    }


# ====================================================================
# Product-specific sub-routers
# ====================================================================

# Dental ERP router
dental_router = APIRouter(prefix="/api/v1/dental", tags=["dental"])


@dental_router.get("/")
async def dental_home():
    """
    Dental ERP product home endpoint

    Returns:
        Product information and available endpoints

    Raises:
        401: If no tenant context
        403: If tenant doesn't have access to DentalERP
    """
    tenant = TenantContext.require_tenant()

    # Check product access
    if not check_product_access(ProductType.DENTAL_ERP.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant '{tenant.tenant_code}' does not have access to DentalERP"
        )

    registry = get_product_registry()
    product = registry.get(ProductType.DENTAL_ERP.value)

    return {
        "product": ProductType.DENTAL_ERP.value,
        "name": product.name if product else "Dental ERP",
        "tenant": tenant.tenant_code,
        "message": "Welcome to DentalERP API",
        "available_endpoints": [
            "/api/v1/dental/analytics/production/daily",
            "/api/v1/dental/analytics/production/summary",
            "/api/v1/dental/analytics/production/by-practice",
        ]
    }


# Agent Provision router
agent_router = APIRouter(prefix="/api/v1/agent", tags=["agentprovision"])


@agent_router.get("/")
async def agent_home():
    """
    Agent Provision product home endpoint

    Returns:
        Product information and available endpoints

    Raises:
        401: If no tenant context
        403: If tenant doesn't have access to AgentProvision
    """
    tenant = TenantContext.require_tenant()

    # Check product access
    if not check_product_access("agentprovision"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant '{tenant.tenant_code}' does not have access to AgentProvision"
        )

    registry = get_product_registry()
    product = registry.get("agentprovision")

    return {
        "product": "agentprovision",
        "name": product.name if product else "Agent Provision",
        "tenant": tenant.tenant_code,
        "message": "Welcome to AgentProvision API",
        "available_endpoints": [
            "/api/v1/agent/provisions",
            "/api/v1/agent/agents",
            "/api/v1/agent/deployments",
            "/api/v1/agent/analytics"
        ]
    }


# ====================================================================
# Product-specific analytics endpoints (for DentalERP)
# ====================================================================

@dental_router.get("/analytics/production/summary")
async def get_dental_production_summary(
    practice_location: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get dental production summary analytics

    Requires ProductFeature.ANALYTICS access.

    Args:
        practice_location: Filter by practice location (optional)
        start_date: Start date filter (ISO format, optional)
        end_date: End date filter (ISO format, optional)

    Returns:
        Production summary metrics

    Raises:
        401: If no tenant context
        403: If tenant doesn't have analytics feature access
    """
    tenant = TenantContext.require_tenant()

    # Check product access
    if not check_product_access(ProductType.DENTAL_ERP.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant '{tenant.tenant_code}' does not have access to DentalERP"
        )

    # Check feature access
    if not check_product_feature(ProductType.DENTAL_ERP.value, ProductFeature.ANALYTICS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant '{tenant.tenant_code}' does not have access to analytics feature"
        )

    # Import here to avoid circular dependency
    from .analytics import get_production_summary

    # Delegate to existing analytics endpoint
    return await get_production_summary(practice_location, start_date, end_date)


@dental_router.get("/analytics/production/daily")
async def get_dental_production_daily(
    practice_location: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100
):
    """
    Get daily dental production metrics

    Requires ProductFeature.PRODUCTION_TRACKING access.

    Args:
        practice_location: Filter by practice location (optional)
        start_date: Start date filter (ISO format, optional)
        end_date: End date filter (ISO format, optional)
        limit: Maximum number of records to return

    Returns:
        Daily production metrics

    Raises:
        401: If no tenant context
        403: If tenant doesn't have production tracking feature access
    """
    tenant = TenantContext.require_tenant()

    if not check_product_access(ProductType.DENTAL_ERP.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant '{tenant.tenant_code}' does not have access to DentalERP"
        )

    if not check_product_feature(ProductType.DENTAL_ERP.value, ProductFeature.PRODUCTION_TRACKING):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant '{tenant.tenant_code}' does not have access to production tracking feature"
        )

    from .analytics import get_daily_production
    return await get_daily_production(practice_location, start_date, end_date, limit)


@dental_router.get("/analytics/production/by-practice")
async def get_dental_production_by_practice(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get production metrics grouped by practice

    Requires ProductFeature.ANALYTICS access.

    Args:
        start_date: Start date filter (ISO format, optional)
        end_date: End date filter (ISO format, optional)

    Returns:
        Production metrics grouped by practice location

    Raises:
        401: If no tenant context
        403: If tenant doesn't have analytics feature access
    """
    tenant = TenantContext.require_tenant()

    if not check_product_access(ProductType.DENTAL_ERP.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant '{tenant.tenant_code}' does not have access to DentalERP"
        )

    if not check_product_feature(ProductType.DENTAL_ERP.value, ProductFeature.ANALYTICS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant '{tenant.tenant_code}' does not have access to analytics feature"
        )

    from .analytics import get_production_by_practice
    return await get_production_by_practice(start_date, end_date)
