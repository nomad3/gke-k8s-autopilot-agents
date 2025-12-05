"""
Product models for multi-product support

Defines the products available in the system (DentalERP, MedicalERP, VetERP)
and manages product-specific configurations and access.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ProductType(str, Enum):
    """Available product types in the system"""
    DENTAL_ERP = "dentalerp"
    MEDICAL_ERP = "medicalerp"
    VET_ERP = "veterp"
    # Future products can be added here


class ProductFeature(str, Enum):
    """Product feature flags"""
    ANALYTICS = "analytics"
    PRODUCTION_TRACKING = "production_tracking"
    FINANCIAL_REPORTING = "financial_reporting"
    INVENTORY_MANAGEMENT = "inventory_management"
    APPOINTMENT_SCHEDULING = "appointment_scheduling"
    PATIENT_PORTAL = "patient_portal"
    BILLING = "billing"
    INSURANCE_CLAIMS = "insurance_claims"
    DOCUMENT_MANAGEMENT = "document_management"
    COMPLIANCE_REPORTING = "compliance_reporting"


class ProductStatus(str, Enum):
    """Product lifecycle status"""
    ACTIVE = "active"
    BETA = "beta"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"


class Product(BaseModel):
    """
    Product definition model

    Represents a product offering in the platform (e.g., DentalERP)
    """
    id: UUID = Field(default_factory=uuid4, description="Unique product ID")
    code: str = Field(..., description="Product code (e.g., 'dentalerp')")
    name: str = Field(..., description="Display name (e.g., 'Dental ERP')")
    description: Optional[str] = Field(None, description="Product description")
    version: str = Field(default="1.0.0", description="Current product version")
    status: ProductStatus = Field(default=ProductStatus.ACTIVE, description="Product status")

    # API Configuration
    api_prefix: str = Field(..., description="API route prefix (e.g., '/dental')")
    api_routes: List[str] = Field(
        default_factory=list,
        description="Available API endpoints for this product"
    )

    # Data Warehouse Configuration
    warehouse_schemas: Dict[str, str] = Field(
        default_factory=dict,
        description="Warehouse schema mappings (e.g., {'bronze': 'dental_bronze', 'gold': 'dental_gold'})"
    )

    # Feature Flags
    features: List[ProductFeature] = Field(
        default_factory=list,
        description="Enabled features for this product"
    )

    # Integration Requirements
    required_integrations: List[str] = Field(
        default_factory=list,
        description="Required integrations (e.g., ['dentrix', 'opendental'])"
    )
    optional_integrations: List[str] = Field(
        default_factory=list,
        description="Optional integrations (e.g., ['netsuite', 'adp'])"
    )

    # Configuration
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Product-specific configuration"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration"""
        json_schema_extra = {
            "example": {
                "code": "dentalerp",
                "name": "Dental ERP",
                "description": "Complete ERP solution for dental practices",
                "version": "1.0.0",
                "api_prefix": "/dental",
                "api_routes": [
                    "/dental/analytics/production",
                    "/dental/analytics/collections",
                    "/dental/practices",
                    "/dental/providers"
                ],
                "warehouse_schemas": {
                    "bronze": "dental_bronze",
                    "silver": "dental_silver",
                    "gold": "dental_gold"
                },
                "features": [
                    "analytics",
                    "production_tracking",
                    "financial_reporting"
                ],
                "required_integrations": ["dentrix"],
                "optional_integrations": ["netsuite", "adp"]
            }
        }


class ProductCreate(BaseModel):
    """Product creation request model"""
    code: str = Field(..., min_length=3, max_length=50, description="Product code")
    name: str = Field(..., min_length=3, max_length=100, description="Product name")
    description: Optional[str] = Field(None, max_length=500)
    version: str = Field(default="1.0.0")
    status: ProductStatus = Field(default=ProductStatus.BETA)
    api_prefix: str = Field(..., pattern=r"^/[a-z][a-z0-9-]*$")
    api_routes: List[str] = Field(default_factory=list)
    warehouse_schemas: Dict[str, str] = Field(default_factory=dict)
    features: List[ProductFeature] = Field(default_factory=list)
    required_integrations: List[str] = Field(default_factory=list)
    optional_integrations: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)


class ProductUpdate(BaseModel):
    """Product update request model"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    version: Optional[str] = None
    status: Optional[ProductStatus] = None
    api_routes: Optional[List[str]] = None
    warehouse_schemas: Optional[Dict[str, str]] = None
    features: Optional[List[ProductFeature]] = None
    required_integrations: Optional[List[str]] = None
    optional_integrations: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None


class ProductResponse(BaseModel):
    """Product response model (public API)"""
    id: UUID
    code: str
    name: str
    description: Optional[str]
    version: str
    status: ProductStatus
    api_prefix: str
    features: List[ProductFeature]
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration"""
        from_attributes = True


class TenantProductAccess(BaseModel):
    """
    Tenant product access model

    Defines which products a tenant has access to and their configuration
    """
    product_code: str = Field(..., description="Product code")
    enabled: bool = Field(default=True, description="Whether product is enabled for tenant")
    features: List[ProductFeature] = Field(
        default_factory=list,
        description="Enabled features (subset of product features)"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tenant-specific product configuration"
    )
    license_type: Optional[str] = Field(None, description="License type (e.g., 'standard', 'professional', 'enterprise')")
    max_users: Optional[int] = Field(None, description="Maximum users allowed")
    expires_at: Optional[datetime] = Field(None, description="License expiration date")

    class Config:
        """Pydantic configuration"""
        json_schema_extra = {
            "example": {
                "product_code": "dentalerp",
                "enabled": True,
                "features": ["analytics", "production_tracking"],
                "config": {
                    "max_locations": 10,
                    "data_retention_days": 730
                },
                "license_type": "professional",
                "max_users": 50,
                "expires_at": "2026-12-31T23:59:59Z"
            }
        }
