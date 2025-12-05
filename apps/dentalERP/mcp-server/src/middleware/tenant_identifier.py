"""Tenant identification middleware for multi-tenant support"""

from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ..core.database import AsyncSessionLocal
from ..core.tenant import TenantContext
from ..services.tenant_service import TenantService
from ..utils.logger import logger


class TenantIdentifierMiddleware(BaseHTTPMiddleware):
    """
    Middleware to identify and set tenant context from incoming requests.

    Supports three identification methods (in priority order):
    1. Subdomain extraction (e.g., acme.dentalerp.com -> 'acme')
    2. X-Tenant-ID header
    3. API key prefix (e.g., acme_abc123... -> 'acme')
    """

    # Public endpoints that don't require tenant identification
    PUBLIC_PATHS = {
        "/health",
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/tenants",  # Tenant management endpoints are public for now
        "/api/v1/products",  # Product catalog is public (not product-specific endpoints)
    }

    async def dispatch(self, request: Request, call_next):
        """
        Process request to identify tenant and set context

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response from downstream handlers
        """
        # Skip tenant identification for public endpoints
        if self._is_public_path(request.url.path):
            response = await call_next(request)
            return response

        # Extract tenant code using multiple methods
        tenant_code = await self._extract_tenant_code(request)

        if not tenant_code:
            logger.warning(f"No tenant identifier found in request: {request.url.path}")
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "Tenant identification required",
                    "message": "Please provide tenant via subdomain, X-Tenant-ID header, or API key"
                }
            )

        # Load tenant from database
        async with AsyncSessionLocal() as db:
            tenant = await TenantService.get_by_code(db, tenant_code)

            if not tenant:
                logger.warning(f"Tenant not found: {tenant_code}")
                return JSONResponse(
                    status_code=404,
                    content={
                        "detail": "Tenant not found",
                        "message": f"No tenant found with code '{tenant_code}'"
                    }
                )

            # Validate tenant status
            if tenant.status != "active":
                logger.warning(f"Inactive tenant attempted access: {tenant_code} (status: {tenant.status})")
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "Tenant inactive",
                        "message": f"Tenant '{tenant_code}' is {tenant.status}"
                    }
                )

            # Set tenant context for this request
            TenantContext.set_tenant(tenant)
            logger.debug(f"Tenant context set: {tenant_code} ({tenant.tenant_name})")

            try:
                # Process request with tenant context
                response = await call_next(request)
                return response
            finally:
                # Clear tenant context after request
                TenantContext.clear()
                logger.debug(f"Tenant context cleared: {tenant_code}")

    def _is_public_path(self, path: str) -> bool:
        """
        Check if path is public (doesn't require tenant)

        Args:
            path: Request URL path

        Returns:
            True if path is public, False otherwise
        """
        # Exact match for public paths
        if path in self.PUBLIC_PATHS:
            return True

        # Allow all tenant management endpoints
        if path.startswith("/api/v1/tenants"):
            return True

        # Allow ONLY the main product catalog endpoint and individual product lookups
        # But NOT tenant-specific product endpoints like /accessible, /*/access, /*/features
        if path == "/api/v1/products" or path == "/api/v1/products/":
            return True

        # Tenant-specific product endpoints (require tenant context)
        tenant_specific_product_paths = [
            "/api/v1/products/accessible",
            "/api/v1/products/access",
            "/api/v1/products/features",
        ]

        # Check if it's a tenant-specific endpoint
        for tenant_path in tenant_specific_product_paths:
            if path.startswith(tenant_path):
                return False

        # Allow individual product lookups: /api/v1/products/{product_code}
        # But must be exactly one path segment after /api/v1/products (no further slashes)
        if path.startswith("/api/v1/products/"):
            remaining = path[len("/api/v1/products/"):]
            # If there are no more slashes, it's a direct product lookup (public)
            # This handles /api/v1/products/dentalerp or /api/v1/products/agentprovision
            if "/" not in remaining:
                return True

        return False

    async def _extract_tenant_code(self, request: Request) -> Optional[str]:
        """
        Extract tenant code from request using multiple methods

        Priority order:
        1. Subdomain (most common in production)
        2. X-Tenant-ID header (for development/testing)
        3. API key prefix (for service-to-service calls)

        Args:
            request: Incoming HTTP request

        Returns:
            Tenant code or None if not found
        """
        # Method 1: Extract from subdomain
        tenant_code = self._extract_from_subdomain(request)
        if tenant_code:
            logger.debug(f"Tenant identified via subdomain: {tenant_code}")
            return tenant_code

        # Method 2: Extract from header
        tenant_code = self._extract_from_header(request)
        if tenant_code:
            logger.debug(f"Tenant identified via header: {tenant_code}")
            return tenant_code

        # Method 3: Extract from API key
        tenant_code = self._extract_from_api_key(request)
        if tenant_code:
            logger.debug(f"Tenant identified via API key: {tenant_code}")
            return tenant_code

        return None

    def _extract_from_subdomain(self, request: Request) -> Optional[str]:
        """
        Extract tenant code from subdomain

        Examples:
            - acme.dentalerp.com -> 'acme'
            - test-practice.api.dentalerp.com -> 'test-practice'
            - localhost -> None (no subdomain)

        Args:
            request: Incoming HTTP request

        Returns:
            Tenant code or None
        """
        host = request.headers.get("host", "")

        # Remove port if present
        if ":" in host:
            host = host.split(":")[0]

        # Split by dots
        parts = host.split(".")

        # Need at least 3 parts for subdomain (subdomain.domain.tld)
        if len(parts) < 3:
            return None

        # First part is the subdomain/tenant code
        subdomain = parts[0]

        # Filter out common non-tenant subdomains
        if subdomain in {"www", "api", "app", "localhost", "mcp"}:
            return None

        return subdomain

    def _extract_from_header(self, request: Request) -> Optional[str]:
        """
        Extract tenant code from X-Tenant-ID header

        Args:
            request: Incoming HTTP request

        Returns:
            Tenant code or None
        """
        return request.headers.get("x-tenant-id") or request.headers.get("X-Tenant-ID")

    def _extract_from_api_key(self, request: Request) -> Optional[str]:
        """
        Extract tenant code from API key prefix

        API keys are formatted as: {tenant_code}_{random_key}
        Example: acme_sk_abc123xyz -> 'acme'

        Args:
            request: Incoming HTTP request

        Returns:
            Tenant code or None
        """
        # Get API key from Authorization header
        auth_header = request.headers.get("authorization", "")

        # Support "Bearer {token}" format
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:]  # Remove "Bearer " prefix
        else:
            api_key = auth_header

        # Extract tenant code from key prefix
        if "_" in api_key:
            tenant_code = api_key.split("_")[0]
            return tenant_code

        return None
