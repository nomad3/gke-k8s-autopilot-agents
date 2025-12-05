# Multi-Tenant Multi-Product Platform Migration Plan

## Executive Summary

This document outlines the migration strategy to transform the current DentalERP MCP Server from a single-product system into a **multi-tenant, multi-product platform** with support for multiple data warehouses (Snowflake + Databricks).

### Goals

1. **Multi-Tenancy**: Support multiple organizations (tenants) with data isolation
2. **Multi-Product**: Support DentalERP + future products (MedicalERP, VetERP, etc.)
3. **Databricks Integration**: Add Databricks as an alternative/complementary data warehouse
4. **Backward Compatibility**: Maintain existing Snowflake functionality
5. **Scalability**: Design for 100+ tenants and 10+ products

### Timeline

- **Phase 1**: Multi-Tenant Foundation (4-6 weeks)
- **Phase 2**: Databricks Connector (2-3 weeks)
- **Phase 3**: Multi-Product Support (3-4 weeks)
- **Phase 4**: Migration & Testing (2-3 weeks)

**Total Estimated Time**: 11-16 weeks

---

## Current Architecture Analysis

### Current State (Single Tenant, Single Product)

```
┌────────────────────────────────────────────────────────────┐
│                      Current MCP Server                     │
│                         (DentalERP)                         │
├────────────────────────────────────────────────────────────┤
│  • Single practice location configuration                  │
│  • Hardcoded DentalERP logic                              │
│  • Direct Snowflake connection (single database)          │
│  • No tenant isolation                                     │
│  • No product abstraction                                  │
└────────────────────────────────────────────────────────────┘
                              │
                              ↓
                    ┌─────────────────┐
                    │   Snowflake     │
                    │  DENTAL_ERP_DW  │
                    └─────────────────┘
```

### Target State (Multi-Tenant, Multi-Product)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Multi-Tenant MCP Platform                         │
├─────────────────────────────────────────────────────────────────────┤
│                       Tenant Management Layer                        │
│  • Tenant identification & isolation                                │
│  • Tenant-specific configurations                                   │
│  • Row-level security enforcement                                   │
├─────────────────────────────────────────────────────────────────────┤
│                        Product Abstraction Layer                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │  DentalERP  │  │ MedicalERP  │  │   VetERP    │  ... more      │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
├─────────────────────────────────────────────────────────────────────┤
│                    Data Warehouse Abstraction                        │
│  ┌──────────────────────┐       ┌──────────────────────┐          │
│  │  Snowflake Connector │       │ Databricks Connector │          │
│  └──────────────────────┘       └──────────────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
                    │                            │
                    ↓                            ↓
         ┌──────────────────┐         ┌──────────────────┐
         │    Snowflake     │         │    Databricks    │
         │  (Multi-tenant)  │         │  (Multi-tenant)  │
         └──────────────────┘         └──────────────────┘
```

---

## Phase 1: Multi-Tenant Foundation

### 1.1 Database Schema Changes

#### New Tables

**`tenants`** - Tenant registry
```sql
CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_code VARCHAR(50) UNIQUE NOT NULL,  -- e.g., 'dental_001', 'medical_002'
  tenant_name VARCHAR(255) NOT NULL,
  industry VARCHAR(50) NOT NULL,             -- 'dental', 'medical', 'veterinary'
  products JSON NOT NULL,                     -- ['dentalerp', 'medicalerp']
  status VARCHAR(20) NOT NULL DEFAULT 'active', -- 'active', 'suspended', 'deleted'
  settings JSON,                              -- Tenant-specific settings
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tenants_code ON tenants(tenant_code);
CREATE INDEX idx_tenants_status ON tenants(status);
```

**`tenant_warehouses`** - Data warehouse configurations per tenant
```sql
CREATE TABLE tenant_warehouses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  warehouse_type VARCHAR(20) NOT NULL,       -- 'snowflake', 'databricks'
  warehouse_config JSON NOT NULL,             -- Connection details (encrypted)
  is_primary BOOLEAN DEFAULT false,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE INDEX idx_tenant_warehouses_tenant ON tenant_warehouses(tenant_id);
CREATE INDEX idx_tenant_warehouses_type ON tenant_warehouses(warehouse_type);
```

**`tenant_users`** - User-tenant mapping
```sql
CREATE TABLE tenant_users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  user_id VARCHAR(255) NOT NULL,              -- Email or user ID
  role VARCHAR(50) NOT NULL,                   -- 'admin', 'user', 'viewer'
  permissions JSON,                            -- Product-specific permissions
  created_at TIMESTAMP DEFAULT NOW(),
  CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE INDEX idx_tenant_users_tenant ON tenant_users(tenant_id);
CREATE INDEX idx_tenant_users_user ON tenant_users(user_id);
CREATE UNIQUE INDEX idx_tenant_user_unique ON tenant_users(tenant_id, user_id);
```

**`tenant_api_keys`** - Tenant-specific API keys
```sql
CREATE TABLE tenant_api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  key_hash VARCHAR(255) NOT NULL,             -- Hashed API key
  key_prefix VARCHAR(20) NOT NULL,            -- First 8 chars for identification
  name VARCHAR(100),                          -- Key description
  permissions JSON,                           -- Scoped permissions
  expires_at TIMESTAMP,
  last_used_at TIMESTAMP,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
);

CREATE INDEX idx_tenant_api_keys_tenant ON tenant_api_keys(tenant_id);
CREATE INDEX idx_tenant_api_keys_prefix ON tenant_api_keys(key_prefix);
```

### 1.2 Code Structure Changes

#### New Directory Structure
```
mcp-server/
├── src/
│   ├── core/
│   │   ├── config.py              # Existing
│   │   ├── database.py            # Existing
│   │   ├── security.py            # Existing
│   │   ├── tenant.py              # NEW: Tenant context management
│   │   └── multitenancy.py        # NEW: Multi-tenant utilities
│   ├── models/
│   │   ├── tenant.py              # NEW: Tenant models
│   │   ├── tenant_warehouse.py   # NEW: Warehouse config models
│   │   └── ...
│   ├── connectors/
│   │   ├── base.py                # NEW: Abstract warehouse connector
│   │   ├── snowflake.py           # Existing (refactor to extend base)
│   │   └── databricks.py          # NEW: Databricks connector
│   ├── middleware/
│   │   ├── tenant_identifier.py  # NEW: Extract tenant from request
│   │   └── tenant_isolation.py   # NEW: Enforce tenant isolation
│   ├── api/
│   │   ├── v1/
│   │   │   ├── tenants.py         # NEW: Tenant management API
│   │   │   ├── products.py        # NEW: Product-specific routes
│   │   │   └── ...
│   │   └── ...
│   └── services/
│       ├── tenant_service.py      # NEW: Tenant business logic
│       ├── warehouse_router.py    # NEW: Route queries to correct warehouse
│       └── ...
```

### 1.3 Tenant Identification Strategy

#### Option 1: Subdomain-Based (Recommended)
```
https://dental001.mcp.agentprovision.com/api/v1/analytics/...
https://medical002.mcp.agentprovision.com/api/v1/analytics/...
```

**Pros**: Clear tenant separation, DNS-based routing, works with CORS
**Cons**: Requires wildcard SSL certificate

#### Option 2: Header-Based
```http
X-Tenant-ID: dental_001
Authorization: Bearer <tenant-specific-api-key>
```

**Pros**: Simple, no DNS changes
**Cons**: Requires clients to set header correctly

#### Option 3: API Key Embedded
```
API Key Format: dental_001_<random_hash>
```

**Pros**: Single authentication mechanism
**Cons**: Key format leaks tenant info

**Recommendation**: Use **Option 1 (Subdomain)** for web apps + **Option 2 (Header)** as fallback for API-only clients.

### 1.4 Tenant Context Management

**`src/core/tenant.py`**
```python
from contextvars import ContextVar
from typing import Optional
from .models.tenant import Tenant

# Context variable to store current tenant
_tenant_context: ContextVar[Optional[Tenant]] = ContextVar('tenant', default=None)

class TenantContext:
    """Manage tenant context for the current request"""

    @staticmethod
    def set_tenant(tenant: Tenant) -> None:
        """Set the current tenant for this request context"""
        _tenant_context.set(tenant)

    @staticmethod
    def get_tenant() -> Optional[Tenant]:
        """Get the current tenant from request context"""
        return _tenant_context.get()

    @staticmethod
    def require_tenant() -> Tenant:
        """Get tenant or raise error if not set"""
        tenant = _tenant_context.get()
        if not tenant:
            raise ValueError("No tenant context set")
        return tenant

    @staticmethod
    def clear() -> None:
        """Clear tenant context"""
        _tenant_context.set(None)
```

### 1.5 Middleware Implementation

**`src/middleware/tenant_identifier.py`**
```python
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.tenant import TenantContext
from ..services.tenant_service import TenantService

class TenantIdentifierMiddleware(BaseHTTPMiddleware):
    """Identify and set tenant context from request"""

    async def dispatch(self, request: Request, call_next):
        # Skip tenant identification for public endpoints
        if request.url.path in ['/health', '/docs', '/openapi.json']:
            return await call_next(request)

        tenant_code = None

        # Method 1: Extract from subdomain
        host = request.headers.get('host', '')
        if '.' in host:
            subdomain = host.split('.')[0]
            if subdomain not in ['www', 'api', 'mcp']:
                tenant_code = subdomain

        # Method 2: Extract from X-Tenant-ID header
        if not tenant_code:
            tenant_code = request.headers.get('X-Tenant-ID')

        # Method 3: Extract from API key prefix
        if not tenant_code:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                api_key = auth_header[7:]
                if '_' in api_key:
                    tenant_code = api_key.split('_')[0]

        if not tenant_code:
            raise HTTPException(
                status_code=400,
                detail="Tenant identification required. Provide via subdomain, X-Tenant-ID header, or tenant-prefixed API key"
            )

        # Load tenant from database
        tenant_service = TenantService()
        tenant = await tenant_service.get_by_code(tenant_code)

        if not tenant:
            raise HTTPException(
                status_code=404,
                detail=f"Tenant '{tenant_code}' not found"
            )

        if tenant.status != 'active':
            raise HTTPException(
                status_code=403,
                detail=f"Tenant '{tenant_code}' is not active"
            )

        # Set tenant context
        TenantContext.set_tenant(tenant)

        try:
            response = await call_next(request)
            return response
        finally:
            TenantContext.clear()
```

---

## Phase 2: Databricks Connector

### 2.1 Databricks Connector Implementation

**`src/connectors/databricks.py`**
```python
from databricks import sql
from databricks.sdk import WorkspaceClient
from typing import List, Dict, Any, Optional
from .base import BaseWarehouseConnector

class DatabricksConnector(BaseWarehouseConnector):
    """Databricks data warehouse connector"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Databricks connector

        Config structure:
        {
            "server_hostname": "your-workspace.cloud.databricks.com",
            "http_path": "/sql/1.0/warehouses/...",
            "access_token": "dapi...",
            "catalog": "your_catalog",
            "schema": "default"
        }
        """
        self.config = config
        self.server_hostname = config['server_hostname']
        self.http_path = config['http_path']
        self.access_token = config['access_token']
        self.catalog = config.get('catalog', 'hive_metastore')
        self.schema = config.get('schema', 'default')
        self._connection = None

    async def connect(self) -> None:
        """Establish connection to Databricks SQL warehouse"""
        try:
            self._connection = sql.connect(
                server_hostname=self.server_hostname,
                http_path=self.http_path,
                access_token=self.access_token,
                catalog=self.catalog,
                schema=self.schema
            )
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Databricks: {str(e)}")

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute SQL query with parameterization

        Databricks SQL Connector 3.0.0+ supports native parameterized queries
        """
        if not self._connection:
            await self.connect()

        cursor = self._connection.cursor()

        try:
            # Use parameterized query execution (prevents SQL injection)
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)

            # Fetch results
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            # Convert to list of dicts
            results = [
                dict(zip(columns, row))
                for row in rows
            ]

            return results

        except Exception as e:
            raise RuntimeError(f"Query execution failed: {str(e)}")
        finally:
            cursor.close()

    async def check_connection(self) -> bool:
        """Check if connection is alive"""
        try:
            await self.execute_query("SELECT 1")
            return True
        except:
            return False

    async def get_tables(self, schema: Optional[str] = None) -> List[str]:
        """Get list of tables in schema"""
        schema = schema or self.schema
        query = f"SHOW TABLES IN {self.catalog}.{schema}"
        results = await self.execute_query(query)
        return [row['tableName'] for row in results]

    async def get_table_stats(self, table: str) -> Dict[str, Any]:
        """Get table statistics"""
        query = f"""
        DESCRIBE EXTENDED {self.catalog}.{self.schema}.{table}
        """
        results = await self.execute_query(query)

        # Parse results into stats dict
        stats = {}
        for row in results:
            if row['col_name'] in ['Table Size', 'Num Rows', 'Location']:
                stats[row['col_name']] = row['data_type']

        return stats

    async def close(self) -> None:
        """Close connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
```

### 2.2 Base Warehouse Connector

**`src/connectors/base.py`**
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseWarehouseConnector(ABC):
    """Abstract base class for data warehouse connectors"""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to warehouse"""
        pass

    @abstractmethod
    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute SQL query and return results"""
        pass

    @abstractmethod
    async def check_connection(self) -> bool:
        """Check if connection is alive"""
        pass

    @abstractmethod
    async def get_tables(self, schema: Optional[str] = None) -> List[str]:
        """Get list of tables in schema"""
        pass

    @abstractmethod
    async def get_table_stats(self, table: str) -> Dict[str, Any]:
        """Get table statistics"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close connection"""
        pass
```

### 2.3 Warehouse Router

**`src/services/warehouse_router.py`**
```python
from typing import Dict, Any, Optional
from ..connectors.base import BaseWarehouseConnector
from ..connectors.snowflake import SnowflakeConnector
from ..connectors.databricks import DatabricksConnector
from ..core.tenant import TenantContext

class WarehouseRouter:
    """Route queries to the appropriate data warehouse for current tenant"""

    def __init__(self):
        self._connectors: Dict[str, BaseWarehouseConnector] = {}

    async def get_connector(
        self,
        warehouse_type: Optional[str] = None
    ) -> BaseWarehouseConnector:
        """
        Get warehouse connector for current tenant

        Args:
            warehouse_type: Specific warehouse type ('snowflake', 'databricks')
                           If None, uses tenant's primary warehouse
        """
        tenant = TenantContext.require_tenant()

        # Get tenant's warehouse configuration
        if warehouse_type:
            warehouse_config = await self._get_warehouse_config(
                tenant.id, warehouse_type
            )
        else:
            warehouse_config = await self._get_primary_warehouse_config(tenant.id)

        if not warehouse_config:
            raise ValueError(
                f"No warehouse configuration found for tenant {tenant.tenant_code}"
            )

        # Create or get cached connector
        cache_key = f"{tenant.id}_{warehouse_config['type']}"

        if cache_key not in self._connectors:
            connector = self._create_connector(
                warehouse_config['type'],
                warehouse_config['config']
            )
            await connector.connect()
            self._connectors[cache_key] = connector

        return self._connectors[cache_key]

    def _create_connector(
        self,
        warehouse_type: str,
        config: Dict[str, Any]
    ) -> BaseWarehouseConnector:
        """Factory method to create warehouse connector"""
        if warehouse_type == 'snowflake':
            return SnowflakeConnector(config)
        elif warehouse_type == 'databricks':
            return DatabricksConnector(config)
        else:
            raise ValueError(f"Unsupported warehouse type: {warehouse_type}")

    async def _get_warehouse_config(
        self,
        tenant_id: str,
        warehouse_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get warehouse configuration for tenant"""
        # Query tenant_warehouses table
        # Implementation depends on your database service
        pass

    async def _get_primary_warehouse_config(
        self,
        tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get primary warehouse configuration for tenant"""
        # Query tenant_warehouses table where is_primary=true
        pass

    async def close_all(self) -> None:
        """Close all cached connections"""
        for connector in self._connectors.values():
            await connector.close()
        self._connectors.clear()
```

### 2.4 Databricks Configuration

**Environment Variables**
```bash
# Databricks Configuration
DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/abc123def456
DATABRICKS_ACCESS_TOKEN=dapi...
DATABRICKS_CATALOG=dental_erp
DATABRICKS_SCHEMA=gold

# Unity Catalog (for multi-tenant isolation)
DATABRICKS_USE_UNITY_CATALOG=true
```

**Tenant-Specific Configuration** (stored in `tenant_warehouses` table)
```json
{
  "server_hostname": "your-workspace.cloud.databricks.com",
  "http_path": "/sql/1.0/warehouses/abc123def456",
  "access_token": "dapi...",
  "catalog": "tenant_dental_001",
  "schema": "gold",
  "use_unity_catalog": true,
  "row_level_security": {
    "enabled": true,
    "filter_column": "tenant_id"
  }
}
```

---

## Phase 3: Multi-Product Support

### 3.1 Product Abstraction

**`src/models/product.py`**
```python
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel

class ProductType(str, Enum):
    DENTAL_ERP = "dentalerp"
    MEDICAL_ERP = "medicalerp"
    VET_ERP = "veterp"
    # Add more products as needed

class Product(BaseModel):
    id: str
    code: ProductType
    name: str
    description: str
    version: str
    api_routes: List[str]  # Product-specific API routes
    warehouse_schemas: dict  # Schema names per warehouse type

    class Config:
        use_enum_values = True
```

### 3.2 Product-Specific Routing

**`src/api/v1/products.py`**
```python
from fastapi import APIRouter, Depends
from ...core.tenant import TenantContext
from ...models.product import ProductType

# Create product-specific routers
dental_router = APIRouter(prefix="/dental", tags=["DentalERP"])
medical_router = APIRouter(prefix="/medical", tags=["MedicalERP"])
vet_router = APIRouter(prefix="/vet", tags=["VetERP"])

@dental_router.get("/analytics/production/summary")
async def get_dental_production_summary():
    """DentalERP-specific production analytics"""
    tenant = TenantContext.require_tenant()

    # Verify tenant has access to dentalerp product
    if ProductType.DENTAL_ERP not in tenant.products:
        raise HTTPException(403, "Tenant does not have access to DentalERP")

    # Query from dental-specific schema
    # ...

@medical_router.get("/analytics/patient/summary")
async def get_medical_patient_summary():
    """MedicalERP-specific patient analytics"""
    tenant = TenantContext.require_tenant()

    # Verify tenant has access to medicalerp product
    if ProductType.MEDICAL_ERP not in tenant.products:
        raise HTTPException(403, "Tenant does not have access to MedicalERP")

    # Query from medical-specific schema
    # ...
```

### 3.3 Product Registry

**`src/services/product_registry.py`**
```python
from typing import Dict, List
from ..models.product import Product, ProductType

class ProductRegistry:
    """Registry of available products and their configurations"""

    _products: Dict[ProductType, Product] = {}

    @classmethod
    def register(cls, product: Product) -> None:
        """Register a product"""
        cls._products[product.code] = product

    @classmethod
    def get(cls, code: ProductType) -> Product:
        """Get product by code"""
        if code not in cls._products:
            raise ValueError(f"Product '{code}' not registered")
        return cls._products[code]

    @classmethod
    def list_all(cls) -> List[Product]:
        """List all registered products"""
        return list(cls._products.values())

# Register products on startup
ProductRegistry.register(Product(
    id="dental-erp-v1",
    code=ProductType.DENTAL_ERP,
    name="DentalERP",
    description="Dental practice management and analytics",
    version="1.0.0",
    api_routes=["/dental/*"],
    warehouse_schemas={
        "snowflake": {
            "bronze": "dental_bronze",
            "silver": "dental_silver",
            "gold": "dental_gold"
        },
        "databricks": {
            "bronze": "dental_bronze",
            "silver": "dental_silver",
            "gold": "dental_gold"
        }
    }
))
```

---

## Phase 4: Migration Strategy

### 4.1 Data Migration

#### Step 1: Add Tenant Column to Existing Tables

```sql
-- Add tenant_id to existing Snowflake tables
ALTER TABLE bronze.pms_day_sheets ADD COLUMN tenant_id VARCHAR(50);
ALTER TABLE bronze_gold.daily_production_metrics ADD COLUMN tenant_id VARCHAR(50);

-- Backfill with default tenant for existing data
UPDATE bronze.pms_day_sheets SET tenant_id = 'dental_001';
UPDATE bronze_gold.daily_production_metrics SET tenant_id = 'dental_001';

-- Make tenant_id NOT NULL after backfill
ALTER TABLE bronze.pms_day_sheets ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE bronze_gold.daily_production_metrics ALTER COLUMN tenant_id SET NOT NULL;

-- Add indexes
CREATE INDEX idx_pms_day_sheets_tenant ON bronze.pms_day_sheets(tenant_id);
CREATE INDEX idx_daily_production_tenant ON bronze_gold.daily_production_metrics(tenant_id);
```

#### Step 2: Create Row-Level Security

**Snowflake Row Access Policy**
```sql
CREATE OR REPLACE ROW ACCESS POLICY tenant_isolation_policy
AS (tenant_id VARCHAR) RETURNS BOOLEAN ->
  CASE
    WHEN CURRENT_ROLE() = 'ACCOUNTADMIN' THEN TRUE
    WHEN tenant_id = CURRENT_USER() THEN TRUE
    ELSE FALSE
  END;

-- Apply to tables
ALTER TABLE bronze.pms_day_sheets
  ADD ROW ACCESS POLICY tenant_isolation_policy ON (tenant_id);

ALTER TABLE bronze_gold.daily_production_metrics
  ADD ROW ACCESS POLICY tenant_isolation_policy ON (tenant_id);
```

**Databricks Row-Level Security (Unity Catalog)**
```sql
-- Create UDF for row filtering
CREATE FUNCTION filter_by_tenant(tenant_id STRING)
RETURNS BOOLEAN
RETURN tenant_id = current_user();

-- Create view with filter
CREATE VIEW gold.daily_production_secure AS
SELECT *
FROM gold.daily_production_metrics
WHERE filter_by_tenant(tenant_id);
```

### 4.2 API Migration

#### Backward Compatibility Layer

```python
# src/api/v1/legacy.py
from fastapi import APIRouter, Request
from ...core.tenant import TenantContext

legacy_router = APIRouter(prefix="/api/v1", tags=["Legacy (Deprecated)"])

@legacy_router.get("/analytics/production/summary")
async def legacy_production_summary(request: Request):
    """
    Legacy endpoint - automatically routes to tenant's DentalERP

    DEPRECATED: Use /api/v2/dental/analytics/production/summary instead
    """
    # For backward compatibility, assume default tenant if no context
    tenant = TenantContext.get_tenant()
    if not tenant:
        # Fallback to default tenant (e.g., first dental practice)
        tenant = await get_default_tenant()
        TenantContext.set_tenant(tenant)

    # Route to new product-specific endpoint
    return await new_dental_production_summary()
```

### 4.3 Configuration Migration

#### Before (Single Tenant)
```bash
SNOWFLAKE_ACCOUNT=HKTPGHW-ES87244
SNOWFLAKE_USER=NOMADSIMON
SNOWFLAKE_PASSWORD=@SebaSofi.2k25!!
```

#### After (Multi-Tenant)
```bash
# Default/Admin Warehouse (for tenant management)
ADMIN_SNOWFLAKE_ACCOUNT=HKTPGHW-ES87244
ADMIN_SNOWFLAKE_USER=ADMIN_USER
ADMIN_SNOWFLAKE_PASSWORD=<admin_password>

# Tenant-specific configs stored in database (tenant_warehouses table)
# Each tenant has encrypted connection details
```

### 4.4 Testing Strategy

#### Unit Tests
```python
# tests/test_multitenancy.py
import pytest
from src.core.tenant import TenantContext
from src.models.tenant import Tenant

async def test_tenant_context():
    """Test tenant context management"""
    tenant = Tenant(id="123", tenant_code="dental_001", ...)
    TenantContext.set_tenant(tenant)

    assert TenantContext.get_tenant() == tenant

    TenantContext.clear()
    assert TenantContext.get_tenant() is None

async def test_tenant_isolation():
    """Test that queries are isolated by tenant"""
    tenant_a = Tenant(id="a", tenant_code="dental_001", ...)
    tenant_b = Tenant(id="b", tenant_code="dental_002", ...)

    # Set tenant A
    TenantContext.set_tenant(tenant_a)
    results_a = await analytics_service.get_production_summary()

    # Set tenant B
    TenantContext.set_tenant(tenant_b)
    results_b = await analytics_service.get_production_summary()

    # Results should be different (tenant-specific)
    assert results_a != results_b
```

#### Integration Tests
```bash
# Test tenant A
curl -H "X-Tenant-ID: dental_001" \
     -H "Authorization: Bearer dental_001_<key>" \
     http://localhost:8085/api/v2/dental/analytics/production/summary

# Test tenant B
curl -H "X-Tenant-ID: dental_002" \
     -H "Authorization: Bearer dental_002_<key>" \
     http://localhost:8085/api/v2/dental/analytics/production/summary

# Should return different results
```

---

## Implementation Checklist

### Phase 1: Multi-Tenant Foundation
- [ ] Create new database tables (tenants, tenant_warehouses, tenant_users, tenant_api_keys)
- [ ] Implement TenantContext for request-scoped tenant management
- [ ] Build TenantIdentifierMiddleware for subdomain/header-based identification
- [ ] Create TenantService for tenant CRUD operations
- [ ] Add tenant isolation to existing queries (add WHERE tenant_id = ?)
- [ ] Implement tenant-specific API key authentication
- [ ] Add tenant management API endpoints (/api/v1/tenants/*)
- [ ] Update existing endpoints to be tenant-aware
- [ ] Add tenant_id column to all data tables
- [ ] Create row-level security policies

### Phase 2: Databricks Connector
- [ ] Install databricks-sql-connector package
- [ ] Implement BaseWarehouseConnector abstract class
- [ ] Refactor SnowflakeConnector to extend BaseWarehouseConnector
- [ ] Implement DatabricksConnector with SQL connector
- [ ] Build WarehouseRouter for dynamic connector selection
- [ ] Add warehouse_type to tenant_warehouses configuration
- [ ] Test Databricks connection with sample queries
- [ ] Implement connection pooling for Databricks
- [ ] Add Databricks-specific health checks
- [ ] Update analytics API to support both warehouses

### Phase 3: Multi-Product Support
- [ ] Create Product model and ProductType enum
- [ ] Build ProductRegistry for product management
- [ ] Create product-specific API routers (dental, medical, vet)
- [ ] Add products field to tenants table
- [ ] Implement product-level permission checks
- [ ] Create product-specific database schemas
- [ ] Add product abstraction to warehouse queries
- [ ] Build product-specific analytics endpoints
- [ ] Create product configuration management
- [ ] Add product versioning support

### Phase 4: Migration & Testing
- [ ] Backfill tenant_id for existing data
- [ ] Create default tenant for existing installation
- [ ] Test backward compatibility with legacy endpoints
- [ ] Migrate existing Snowflake data to tenant-aware schema
- [ ] Test row-level security enforcement
- [ ] Load test with multiple concurrent tenants
- [ ] Security audit (SQL injection, cross-tenant access)
- [ ] Performance testing (query latency with tenant filtering)
- [ ] Documentation updates
- [ ] Deploy to staging environment

---

## Security Considerations

### 1. Tenant Isolation

**Critical**: Must prevent cross-tenant data access at all layers:
- Database row-level security
- Application-level filtering (defense in depth)
- API authentication (tenant-scoped keys)
- Warehouse-level isolation (separate catalogs/databases)

### 2. Credential Management

**Encrypt tenant-specific warehouse credentials**:
```python
from cryptography.fernet import Fernet

class CredentialEncryption:
    def __init__(self, master_key: bytes):
        self.cipher = Fernet(master_key)

    def encrypt(self, credentials: dict) -> str:
        """Encrypt credentials for storage"""
        json_str = json.dumps(credentials)
        encrypted = self.cipher.encrypt(json_str.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt(self, encrypted_credentials: str) -> dict:
        """Decrypt credentials for use"""
        encrypted = base64.b64decode(encrypted_credentials)
        decrypted = self.cipher.decrypt(encrypted)
        return json.loads(decrypted.decode())
```

### 3. API Key Security

- Use tenant-prefixed keys: `dental_001_abc123...`
- Hash keys before storage (never store plaintext)
- Support key rotation without downtime
- Implement rate limiting per tenant
- Log all API key usage

### 4. Audit Logging

```python
class TenantAuditLog(BaseModel):
    tenant_id: str
    user_id: str
    action: str  # 'query', 'upload', 'delete'
    resource: str  # 'analytics', 'pdf'
    timestamp: datetime
    ip_address: str
    success: bool
    error_message: Optional[str]
```

---

## Performance Optimization

### 1. Connection Pooling

```python
# Use connection pool per tenant
from sqlalchemy.pool import QueuePool

class TenantConnectionPool:
    def __init__(self):
        self._pools = {}

    def get_pool(self, tenant_id: str, config: dict):
        if tenant_id not in self._pools:
            self._pools[tenant_id] = QueuePool(
                lambda: create_connection(config),
                max_overflow=10,
                pool_size=5,
                timeout=30
            )
        return self._pools[tenant_id]
```

### 2. Query Optimization

- Add tenant_id to all indexes: `CREATE INDEX idx_table_tenant ON table(tenant_id, date)`
- Use tenant_id as first column in composite indexes
- Partition tables by tenant_id (for large datasets)
- Cache tenant metadata (tenants table queries)

### 3. Caching Strategy

```python
# Cache tenant warehouse config (rarely changes)
@cache(ttl=3600)  # 1 hour
async def get_tenant_warehouse_config(tenant_id: str) -> dict:
    # Query from database
    pass

# Cache analytics results (per tenant)
@cache(ttl=300, key="analytics:{tenant_id}:{metric}")  # 5 min
async def get_analytics(tenant_id: str, metric: str) -> dict:
    # Query from warehouse
    pass
```

---

## Cost Estimation

### Infrastructure Costs (Monthly)

| Component | Current | Multi-Tenant (10 tenants) | Multi-Tenant (100 tenants) |
|-----------|---------|---------------------------|----------------------------|
| Snowflake Compute | $500 | $800 (+60%) | $2,000 (+300%) |
| Databricks Compute | $0 | $400 (new) | $1,500 (new) |
| PostgreSQL (RDS) | $50 | $100 (+100%) | $300 (+500%) |
| Redis (ElastiCache) | $30 | $50 (+67%) | $150 (+400%) |
| **Total** | **$580** | **$1,350** | **$3,950** |

### Development Costs

| Phase | Estimated Hours | Cost @ $100/hr |
|-------|----------------|----------------|
| Phase 1: Multi-Tenant Foundation | 240 hours | $24,000 |
| Phase 2: Databricks Connector | 80 hours | $8,000 |
| Phase 3: Multi-Product Support | 120 hours | $12,000 |
| Phase 4: Migration & Testing | 120 hours | $12,000 |
| **Total** | **560 hours** | **$56,000** |

---

## Success Metrics

### Technical Metrics
- **Query Latency**: <500ms per tenant (P95)
- **API Response Time**: <200ms (P95)
- **Tenant Isolation**: 100% (zero cross-tenant access incidents)
- **Uptime**: 99.9% SLA per tenant
- **Concurrent Tenants**: Support 100+ tenants simultaneously

### Business Metrics
- **Onboarding Time**: New tenant activated in <1 hour
- **Cost Per Tenant**: <$50/month infrastructure cost
- **Scalability**: Add 10 new tenants/week without performance degradation
- **Product Adoption**: 3+ products launched within 6 months

---

## Risk Mitigation

### High Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Cross-tenant data leak** | Critical | Row-level security + application filtering + audit logging + penetration testing |
| **Performance degradation** | High | Connection pooling + query optimization + caching + load testing |
| **Backward compatibility broken** | High | Legacy API layer + gradual migration + feature flags |
| **Databricks integration complexity** | Medium | Proof of concept first + phased rollout + fallback to Snowflake |
| **Credential management vulnerabilities** | Critical | Encryption at rest + key rotation + secret manager (AWS/Vault) |

---

## Next Steps

1. **Review & Approval**: Present plan to stakeholders
2. **POC**: Build proof-of-concept for Phase 1 (2 weeks)
3. **Architecture Review**: Security & scalability review
4. **Resource Allocation**: Assign development team
5. **Kickoff**: Begin Phase 1 implementation

---

## Appendix

### A. Databricks Installation

```bash
# Install Databricks SQL Connector
pip install databricks-sql-connector

# Install Databricks SDK (for advanced features)
pip install databricks-sdk

# Verify installation
python -c "from databricks import sql; print('Databricks connector installed')"
```

### B. Sample Tenant Configuration

```json
{
  "tenant_id": "dental_001",
  "tenant_name": "Smile Dental Group",
  "industry": "dental",
  "products": ["dentalerp"],
  "warehouses": [
    {
      "type": "snowflake",
      "is_primary": true,
      "config": {
        "account": "HKTPGHW-ES87244",
        "user": "tenant_dental_001",
        "database": "DENTAL_ERP_DW",
        "schema": "dental_001_gold",
        "warehouse": "TENANT_DENTAL_001_WH"
      }
    },
    {
      "type": "databricks",
      "is_primary": false,
      "config": {
        "server_hostname": "workspace.cloud.databricks.com",
        "http_path": "/sql/1.0/warehouses/abc123",
        "catalog": "dental_001_catalog",
        "schema": "gold"
      }
    }
  ]
}
```

### C. References

- [Databricks SQL Connector Documentation](https://docs.databricks.com/dev-tools/python-sql-connector.html)
- [Databricks Unity Catalog](https://docs.databricks.com/data-governance/unity-catalog/index.html)
- [Multi-Tenant Architecture Patterns](https://learn.microsoft.com/en-us/azure/architecture/patterns/category/multitenant)
- [Snowflake Row Access Policies](https://docs.snowflake.com/en/user-guide/security-row-intro)

---

**Document Version**: 1.0
**Last Updated**: October 30, 2025
**Status**: Draft - Pending Review
