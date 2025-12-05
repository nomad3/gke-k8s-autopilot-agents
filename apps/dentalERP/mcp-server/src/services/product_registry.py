"""
Product Registry Service

Manages product registration and discovery in the multi-product platform.
Provides a singleton registry for all available products.
"""

from typing import Dict, List, Optional
from uuid import UUID

from ..models.product import (
    Product,
    ProductType,
    ProductFeature,
    ProductStatus,
    TenantProductAccess
)
from ..core.tenant import TenantContext
from ..utils.logger import logger


class ProductRegistry:
    """
    Product registry singleton

    Central registry for all products available in the platform.
    Manages product definitions, features, and access control.
    """

    def __init__(self):
        """Initialize empty product registry"""
        self._products: Dict[str, Product] = {}
        self._products_by_id: Dict[UUID, Product] = {}
        logger.info("ProductRegistry initialized")

    def register(self, product: Product) -> None:
        """
        Register a product in the registry

        Args:
            product: Product instance to register

        Raises:
            ValueError: If product code already registered
        """
        if product.code in self._products:
            raise ValueError(f"Product '{product.code}' is already registered")

        self._products[product.code] = product
        self._products_by_id[product.id] = product
        logger.info(f"Registered product: {product.code} (v{product.version})")

    def get(self, code: str) -> Optional[Product]:
        """
        Get product by code

        Args:
            code: Product code (e.g., 'dentalerp')

        Returns:
            Product instance or None if not found
        """
        return self._products.get(code)

    def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """
        Get product by ID

        Args:
            product_id: Product UUID

        Returns:
            Product instance or None if not found
        """
        return self._products_by_id.get(product_id)

    def list_all(
        self,
        status: Optional[ProductStatus] = None,
        include_inactive: bool = False
    ) -> List[Product]:
        """
        List all registered products

        Args:
            status: Filter by status (optional)
            include_inactive: Include deprecated/sunset products

        Returns:
            List of Product instances
        """
        products = list(self._products.values())

        # Filter by status
        if status:
            products = [p for p in products if p.status == status]
        elif not include_inactive:
            # Exclude deprecated/sunset products by default
            products = [
                p for p in products
                if p.status not in [ProductStatus.DEPRECATED, ProductStatus.SUNSET]
            ]

        return products

    def is_registered(self, code: str) -> bool:
        """
        Check if product is registered

        Args:
            code: Product code

        Returns:
            True if registered, False otherwise
        """
        return code in self._products

    def unregister(self, code: str) -> bool:
        """
        Unregister a product

        Args:
            code: Product code

        Returns:
            True if unregistered, False if not found
        """
        product = self._products.pop(code, None)
        if product:
            self._products_by_id.pop(product.id, None)
            logger.warning(f"Unregistered product: {code}")
            return True
        return False

    def update_product(self, code: str, **updates) -> Optional[Product]:
        """
        Update product attributes

        Args:
            code: Product code
            **updates: Attributes to update

        Returns:
            Updated Product instance or None if not found
        """
        product = self._products.get(code)
        if not product:
            return None

        # Update mutable attributes
        for key, value in updates.items():
            if hasattr(product, key) and key not in ['id', 'code', 'created_at']:
                setattr(product, key, value)

        logger.info(f"Updated product: {code}")
        return product

    def get_product_features(self, code: str) -> List[ProductFeature]:
        """
        Get features for a product

        Args:
            code: Product code

        Returns:
            List of ProductFeature enums
        """
        product = self.get(code)
        return product.features if product else []

    def has_feature(self, code: str, feature: ProductFeature) -> bool:
        """
        Check if product has a specific feature

        Args:
            code: Product code
            feature: ProductFeature enum

        Returns:
            True if product has feature, False otherwise
        """
        features = self.get_product_features(code)
        return feature in features


class TenantProductRegistry:
    """
    Tenant-specific product access registry

    Manages which products a tenant has access to and their configurations.
    This is typically loaded from database tenant.products field.
    """

    def __init__(self, tenant_products: List[TenantProductAccess]):
        """
        Initialize tenant product registry

        Args:
            tenant_products: List of TenantProductAccess instances
        """
        self._products: Dict[str, TenantProductAccess] = {
            tp.product_code: tp for tp in tenant_products
        }

    def has_access(self, product_code: str) -> bool:
        """
        Check if tenant has access to product

        Args:
            product_code: Product code

        Returns:
            True if tenant has access, False otherwise
        """
        access = self._products.get(product_code)
        return access is not None and access.enabled

    def get_access(self, product_code: str) -> Optional[TenantProductAccess]:
        """
        Get tenant's product access configuration

        Args:
            product_code: Product code

        Returns:
            TenantProductAccess instance or None
        """
        return self._products.get(product_code)

    def has_feature(self, product_code: str, feature: ProductFeature) -> bool:
        """
        Check if tenant has access to specific product feature

        Args:
            product_code: Product code
            feature: ProductFeature enum

        Returns:
            True if tenant has feature access, False otherwise
        """
        access = self._products.get(product_code)
        if not access or not access.enabled:
            return False

        # If tenant has no feature restrictions, they have all features
        if not access.features:
            return True

        return feature in access.features

    def list_accessible_products(self) -> List[str]:
        """
        List all product codes tenant has access to

        Returns:
            List of product codes
        """
        return [
            code for code, access in self._products.items()
            if access.enabled
        ]


# Global product registry singleton
_product_registry: Optional[ProductRegistry] = None


def get_product_registry() -> ProductRegistry:
    """
    Get global product registry singleton

    Returns:
        ProductRegistry instance
    """
    global _product_registry
    if _product_registry is None:
        _product_registry = ProductRegistry()
        _initialize_products()
    return _product_registry


def _initialize_products() -> None:
    """
    Initialize default products in registry

    Registers DentalERP and AgentProvision.
    """
    registry = get_product_registry()

    # Register DentalERP
    dental_erp = Product(
        code=ProductType.DENTAL_ERP.value,
        name="Dental ERP",
        description="Complete ERP solution for dental practices with production tracking, analytics, and financial reporting",
        version="1.0.0",
        status=ProductStatus.ACTIVE,
        api_prefix="/dental",
        api_routes=[
            "/dental/analytics/production/daily",
            "/dental/analytics/production/summary",
            "/dental/analytics/production/by-practice",
            "/dental/practices",
            "/dental/providers",
            "/dental/patients",
            "/dental/appointments"
        ],
        warehouse_schemas={
            "bronze": "dental_bronze",
            "silver": "dental_silver",
            "gold": "dental_gold"
        },
        features=[
            ProductFeature.ANALYTICS,
            ProductFeature.PRODUCTION_TRACKING,
            ProductFeature.FINANCIAL_REPORTING,
            ProductFeature.APPOINTMENT_SCHEDULING,
            ProductFeature.BILLING,
            ProductFeature.INSURANCE_CLAIMS,
            ProductFeature.DOCUMENT_MANAGEMENT
        ],
        required_integrations=["dentrix"],
        optional_integrations=["netsuite", "adp", "opendental", "eaglesoft"],
        config={
            "default_data_retention_days": 730,
            "analytics_refresh_interval_minutes": 15,
            "max_locations_default": 5
        }
    )
    registry.register(dental_erp)
    logger.info("✅ DentalERP product registered")

    # Register AgentProvision
    agent_provision = Product(
        code="agentprovision",
        name="Agent Provision",
        description="Intelligent agent provisioning and management platform",
        version="1.0.0",
        status=ProductStatus.ACTIVE,
        api_prefix="/agent",
        api_routes=[
            "/agent/provisions",
            "/agent/agents",
            "/agent/deployments",
            "/agent/analytics"
        ],
        warehouse_schemas={
            "bronze": "agent_bronze",
            "silver": "agent_silver",
            "gold": "agent_gold"
        },
        features=[
            ProductFeature.ANALYTICS,
            ProductFeature.DOCUMENT_MANAGEMENT
        ],
        required_integrations=[],
        optional_integrations=["netsuite", "adp"],
        config={
            "default_data_retention_days": 365,
            "max_agents_per_tenant": 100
        }
    )
    registry.register(agent_provision)
    logger.info("✅ AgentProvision product registered")


def get_tenant_product_registry() -> Optional[TenantProductRegistry]:
    """
    Get current tenant's product registry

    Returns:
        TenantProductRegistry for current tenant, or None if no tenant context
    """
    tenant = TenantContext.get_tenant()
    if not tenant or not tenant.products:
        return None

    # Convert tenant.products list to TenantProductAccess instances
    tenant_products = []
    for product_data in tenant.products:
        if isinstance(product_data, dict):
            # Full TenantProductAccess object
            tenant_products.append(TenantProductAccess(**product_data))
        elif isinstance(product_data, TenantProductAccess):
            # Already a TenantProductAccess instance
            tenant_products.append(product_data)
        elif isinstance(product_data, str):
            # Legacy format: just product code string
            # Create default TenantProductAccess with all features enabled
            registry = get_product_registry()
            product = registry.get(product_data)
            if product:
                tenant_products.append(TenantProductAccess(
                    product_code=product_data,
                    enabled=True,
                    features=product.features,  # Grant all product features by default
                    config={},
                    license_type="standard"
                ))

    return TenantProductRegistry(tenant_products)


def check_product_access(product_code: str) -> bool:
    """
    Check if current tenant has access to product

    Args:
        product_code: Product code to check

    Returns:
        True if tenant has access, False otherwise

    Raises:
        ValueError: If no tenant context
    """
    tenant = TenantContext.require_tenant()

    # Get tenant product registry
    tenant_registry = get_tenant_product_registry()
    if not tenant_registry:
        logger.warning(f"Tenant {tenant.tenant_code} has no products configured")
        return False

    has_access = tenant_registry.has_access(product_code)
    if not has_access:
        logger.warning(
            f"Tenant {tenant.tenant_code} does not have access to product: {product_code}"
        )

    return has_access


def check_product_feature(product_code: str, feature: ProductFeature) -> bool:
    """
    Check if current tenant has access to specific product feature

    Args:
        product_code: Product code
        feature: ProductFeature enum

    Returns:
        True if tenant has feature access, False otherwise

    Raises:
        ValueError: If no tenant context
    """
    tenant = TenantContext.require_tenant()

    tenant_registry = get_tenant_product_registry()
    if not tenant_registry:
        return False

    has_feature = tenant_registry.has_feature(product_code, feature)
    if not has_feature:
        logger.warning(
            f"Tenant {tenant.tenant_code} does not have access to "
            f"feature {feature} in product {product_code}"
        )

    return has_feature
