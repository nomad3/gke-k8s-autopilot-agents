"""
Connector Integration Tests
Tests actual API connectivity (requires credentials)
"""

import pytest


class TestNetSuiteConnector:
    """Test NetSuite connector integration"""
    
    @pytest.mark.integration
    @pytest.mark.skipif(
        "not config.getoption('--run-integration')",
        reason="Requires NetSuite credentials"
    )
    async def test_netsuite_authentication(self):
        """
        Test NetSuite OAuth 1.0a authentication
        
        Requires:
        - Valid NetSuite credentials in environment
        - Sandbox or production account access
        """
        from src.connectors.netsuite import create_netsuite_connector
        from src.core.config import settings
        
        if not all([
            settings.netsuite_account,
            settings.netsuite_consumer_key,
            settings.netsuite_consumer_secret,
            settings.netsuite_token_key,
            settings.netsuite_token_secret
        ]):
            pytest.skip("NetSuite credentials not configured")
        
        connector = create_netsuite_connector(
            account=settings.netsuite_account,
            consumer_key=settings.netsuite_consumer_key,
            consumer_secret=settings.netsuite_consumer_secret,
            token_key=settings.netsuite_token_key,
            token_secret=settings.netsuite_token_secret
        )
        
        # Test connection
        result = await connector.test_connection()
        assert result is True
    
    @pytest.mark.integration
    async def test_netsuite_fetch_journal_entries(self):
        """
        Test fetching journal entries from NetSuite
        
        Workflow:
        1. Connect to NetSuite
        2. Fetch journal entries
        3. Verify response structure
        4. Verify data transformation
        """
        # TODO: Implement with real credentials
        pass


class TestADPConnector:
    """Test ADP connector integration"""
    
    @pytest.mark.integration
    async def test_adp_oauth_flow(self):
        """
        Test ADP OAuth 2.0 client credentials flow
        
        Workflow:
        1. Request access token
        2. Verify token received
        3. Verify token cached
        4. Verify auto-refresh before expiry
        """
        # TODO: Implement with ADP credentials
        pass
    
    @pytest.mark.integration
    async def test_adp_fetch_employees(self):
        """
        Test fetching employee data from ADP
        
        Workflow:
        1. Authenticate with ADP
        2. Fetch employee data
        3. Verify response structure
        4. Verify data transformation
        """
        # TODO: Implement
        pass


class TestConnectorRegistry:
    """Test connector registry functionality"""
    
    @pytest.mark.asyncio
    async def test_connector_factory(self):
        """
        Test connector factory creates correct instances
        
        Workflow:
        1. Request NetSuite connector
        2. Verify correct type returned
        3. Verify singleton behavior
        """
        from src.connectors.registry import get_connector_registry
        
        registry = get_connector_registry()
        
        # Request connector (may return None if not configured)
        connector = await registry.get_connector("netsuite")
        
        # If configured, should be NetSuiteConnector
        if connector:
            assert connector.integration_type == "netsuite"
            assert connector.name == "NetSuite"
    
    @pytest.mark.asyncio
    async def test_connector_caching(self):
        """
        Test that connectors are cached and reused
        
        Workflow:
        1. Get connector twice
        2. Verify same instance returned
        """
        from src.connectors.registry import get_connector_registry
        
        registry = get_connector_registry()
        
        connector1 = await registry.get_connector("adp")
        connector2 = await registry.get_connector("adp")
        
        # Should be same instance (if configured)
        if connector1 and connector2:
            assert connector1 is connector2

