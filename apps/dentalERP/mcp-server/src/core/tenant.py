"""Tenant context management for multi-tenant support"""

from contextvars import ContextVar
from typing import Optional

# Import will be added after we create the model
# from ..models.tenant import Tenant

# Context variable to store current tenant
# Using Any type initially to avoid circular imports
_tenant_context: ContextVar[Optional[any]] = ContextVar('tenant', default=None)


class TenantContext:
    """
    Manage tenant context for the current request.

    Uses Python's contextvars to maintain tenant isolation
    across async requests without thread-local storage.
    """

    @staticmethod
    def set_tenant(tenant) -> None:
        """
        Set the current tenant for this request context

        Args:
            tenant: Tenant model instance
        """
        _tenant_context.set(tenant)

    @staticmethod
    def get_tenant():
        """
        Get the current tenant from request context

        Returns:
            Optional[Tenant]: Current tenant or None
        """
        return _tenant_context.get()

    @staticmethod
    def require_tenant():
        """
        Get tenant or raise error if not set

        Returns:
            Tenant: Current tenant

        Raises:
            ValueError: If no tenant context is set
        """
        tenant = _tenant_context.get()
        if not tenant:
            raise ValueError("No tenant context set. Tenant identification required.")
        return tenant

    @staticmethod
    def clear() -> None:
        """Clear tenant context"""
        _tenant_context.set(None)

    @staticmethod
    def get_tenant_id() -> Optional[str]:
        """
        Get current tenant ID

        Returns:
            Optional[str]: Tenant ID or None
        """
        tenant = _tenant_context.get()
        return str(tenant.id) if tenant else None

    @staticmethod
    def get_tenant_code() -> Optional[str]:
        """
        Get current tenant code

        Returns:
            Optional[str]: Tenant code or None
        """
        tenant = _tenant_context.get()
        return tenant.tenant_code if tenant else None
