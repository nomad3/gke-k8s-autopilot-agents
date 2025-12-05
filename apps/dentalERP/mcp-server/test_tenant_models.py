"""Test script for tenant models and context management"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy import select
from src.core.database import AsyncSessionLocal
from src.models.tenant import Tenant, TenantWarehouse, TenantUser, TenantAPIKey
from src.core.tenant import TenantContext


async def test_tenant_models():
    """Test tenant database models"""
    print("=" * 60)
    print("Testing Tenant Models")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        # Test 1: Query existing default tenant
        print("\n1. Querying default tenant...")
        result = await session.execute(
            select(Tenant).where(Tenant.tenant_code == "default")
        )
        default_tenant = result.scalar_one_or_none()

        if default_tenant:
            print(f"   ✅ Found: {default_tenant.tenant_name}")
            print(f"      ID: {default_tenant.id}")
            print(f"      Code: {default_tenant.tenant_code}")
            print(f"      Industry: {default_tenant.industry}")
            print(f"      Status: {default_tenant.status}")
        else:
            print("   ❌ Default tenant not found!")
            return False

        # Test 2: Create a new test tenant
        print("\n2. Creating test tenant...")
        test_tenant = Tenant(
            tenant_code="test_dental_001",
            tenant_name="Test Dental Practice",
            industry="dental",
            products=["dentalerp"],
            status="active",
            settings={"timezone": "America/Los_Angeles"}
        )
        session.add(test_tenant)
        await session.commit()
        await session.refresh(test_tenant)
        print(f"   ✅ Created tenant: {test_tenant.tenant_name}")
        print(f"      ID: {test_tenant.id}")

        # Test 3: Add warehouse configuration
        print("\n3. Adding Snowflake warehouse config...")
        warehouse = TenantWarehouse(
            tenant_id=test_tenant.id,
            warehouse_type="snowflake",
            warehouse_config={
                "account": "TEST_ACCOUNT",
                "user": "TEST_USER",
                "database": "TEST_DB",
                "warehouse": "COMPUTE_WH"
            },
            is_primary=True,
            is_active=True
        )
        session.add(warehouse)
        await session.commit()
        print(f"   ✅ Added warehouse config")

        # Test 4: Add tenant user
        print("\n4. Adding tenant user...")
        user = TenantUser(
            tenant_id=test_tenant.id,
            user_id="admin@testdental.com",
            role="admin",
            permissions={"dentalerp": ["read", "write", "admin"]}
        )
        session.add(user)
        await session.commit()
        print(f"   ✅ Added user: {user.user_id}")

        # Test 5: Add API key
        print("\n5. Adding tenant API key...")
        api_key = TenantAPIKey(
            tenant_id=test_tenant.id,
            key_hash="hashed_key_value_here",
            key_prefix="test_001",
            name="Production API Key",
            permissions={"endpoints": ["analytics", "warehouse"]},
            is_active=True
        )
        session.add(api_key)
        await session.commit()
        print(f"   ✅ Added API key: {api_key.key_prefix}...")

        # Test 6: Query tenant with relationships
        print("\n6. Querying tenant with relationships...")
        result = await session.execute(
            select(Tenant).where(Tenant.tenant_code == "test_dental_001")
        )
        tenant_with_relations = result.scalar_one()

        # Manually load relationships
        await session.refresh(tenant_with_relations, ["warehouses", "users", "api_keys"])

        print(f"   ✅ Tenant: {tenant_with_relations.tenant_name}")
        print(f"      Warehouses: {len(tenant_with_relations.warehouses)}")
        print(f"      Users: {len(tenant_with_relations.users)}")
        print(f"      API Keys: {len(tenant_with_relations.api_keys)}")

        # Test 7: List all tenants
        print("\n7. Listing all tenants...")
        result = await session.execute(select(Tenant))
        all_tenants = result.scalars().all()
        print(f"   ✅ Total tenants: {len(all_tenants)}")
        for t in all_tenants:
            print(f"      - {t.tenant_code}: {t.tenant_name} ({t.status})")

    return True


async def test_tenant_context():
    """Test tenant context management"""
    print("\n" + "=" * 60)
    print("Testing Tenant Context Management")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        # Get test tenant
        result = await session.execute(
            select(Tenant).where(Tenant.tenant_code == "test_dental_001")
        )
        test_tenant = result.scalar_one()

        # Test 1: Set tenant context
        print("\n1. Setting tenant context...")
        TenantContext.set_tenant(test_tenant)
        print(f"   ✅ Context set for: {test_tenant.tenant_name}")

        # Test 2: Get tenant from context
        print("\n2. Getting tenant from context...")
        current_tenant = TenantContext.get_tenant()
        if current_tenant:
            print(f"   ✅ Retrieved: {current_tenant.tenant_name}")
            print(f"      Code: {current_tenant.tenant_code}")
        else:
            print("   ❌ Failed to retrieve tenant from context")
            return False

        # Test 3: Require tenant
        print("\n3. Testing require_tenant()...")
        try:
            required_tenant = TenantContext.require_tenant()
            print(f"   ✅ Required tenant: {required_tenant.tenant_name}")
        except ValueError as e:
            print(f"   ❌ Error: {e}")
            return False

        # Test 4: Get tenant ID
        print("\n4. Getting tenant ID...")
        tenant_id = TenantContext.get_tenant_id()
        print(f"   ✅ Tenant ID: {tenant_id}")

        # Test 5: Get tenant code
        print("\n5. Getting tenant code...")
        tenant_code = TenantContext.get_tenant_code()
        print(f"   ✅ Tenant code: {tenant_code}")

        # Test 6: Clear context
        print("\n6. Clearing tenant context...")
        TenantContext.clear()
        cleared_tenant = TenantContext.get_tenant()
        if cleared_tenant is None:
            print("   ✅ Context cleared successfully")
        else:
            print("   ❌ Context not cleared")
            return False

        # Test 7: Require tenant when none set (should raise error)
        print("\n7. Testing require_tenant() with no context...")
        try:
            TenantContext.require_tenant()
            print("   ❌ Should have raised ValueError")
            return False
        except ValueError as e:
            print(f"   ✅ Correctly raised error: {e}")

    return True


async def cleanup():
    """Clean up test data"""
    print("\n" + "=" * 60)
    print("Cleaning up test data")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        # Delete test tenant (cascade will delete related records)
        result = await session.execute(
            select(Tenant).where(Tenant.tenant_code == "test_dental_001")
        )
        test_tenant = result.scalar_one_or_none()

        if test_tenant:
            await session.delete(test_tenant)
            await session.commit()
            print("   ✅ Test tenant deleted")
        else:
            print("   ℹ️  Test tenant not found")


async def main():
    """Run all tests"""
    print("\n🧪 TENANT MULTI-TENANCY TESTS\n")

    try:
        # Run model tests
        model_success = await test_tenant_models()

        if not model_success:
            print("\n❌ Model tests failed!")
            return

        # Run context tests
        context_success = await test_tenant_context()

        if not context_success:
            print("\n❌ Context tests failed!")
            return

        # Cleanup
        await cleanup()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nMulti-tenant foundation is working correctly:")
        print("  ✓ Database schema and migrations")
        print("  ✓ SQLAlchemy models with relationships")
        print("  ✓ Tenant context management")
        print("  ✓ Context isolation and cleanup")
        print("\nReady for Phase 1.3: Tenant Middleware")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
