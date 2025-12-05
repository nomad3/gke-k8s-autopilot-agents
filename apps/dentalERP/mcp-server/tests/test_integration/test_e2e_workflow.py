"""
End-to-End Integration Tests
Tests complete workflow from API call through to response
"""

import pytest
from httpx import AsyncClient


class TestCompleteWorkflow:
    """Test complete data flow through MCP Server"""
    
    @pytest.mark.asyncio
    async def test_health_check_workflow(self, async_client: AsyncClient):
        """
        Test 1: Health Check
        Verifies MCP Server is accessible
        """
        response = await async_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "mcp-server"
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_integration_status_workflow(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """
        Test 2: Integration Status
        Frontend → ERP → MCP → Database → Response
        """
        response = await async_client.get(
            "/api/v1/integrations/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should have default integrations
        integration_types = [item["integration_type"] for item in data]
        assert "adp" in integration_types
        assert "netsuite" in integration_types
    
    @pytest.mark.asyncio
    async def test_sync_workflow(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_db: any
    ):
        """
        Test 3: Complete Sync Workflow
        Trigger Sync → Create Job → Execute → Track Status → Complete
        """
        # Step 1: Trigger sync
        sync_request = {
            "integration_type": "netsuite",
            "entity_types": ["journalEntry"],
            "sync_mode": "incremental"
        }
        
        response = await async_client.post(
            "/api/v1/sync/run",
            json=sync_request,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "sync_id" in data
        assert data["status"] in ["pending", "running", "completed"]
        
        sync_id = data["sync_id"]
        
        # Step 2: Check sync status
        status_response = await async_client.get(
            f"/api/v1/sync/{sync_id}",
            headers=auth_headers
        )
        
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["sync_id"] == sync_id
        assert "status" in status_data
    
    @pytest.mark.asyncio
    async def test_data_query_workflow(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """
        Test 4: Financial Data Query
        Request → MCP → Snowflake Gold Table → Cache → Response
        """
        response = await async_client.get(
            "/api/v1/finance/summary?location=downtown&from=2025-01-01&to=2025-01-31",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "location_id" in data
        assert "revenue" in data
        assert "expenses" in data
        assert "net_income" in data
        assert "date_range" in data
        assert isinstance(data["breakdown"], list)
    
    @pytest.mark.asyncio
    async def test_forecast_workflow(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """
        Test 5: Forecasting Workflow
        Request → MCP → Snowflake ML → Cache → Response
        """
        response = await async_client.get(
            "/api/v1/forecast/downtown?metric=revenue&periods=3",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "location_id" in data
        assert "metric" in data
        assert "predicted" in data
        assert "confidence" in data
        assert 0 <= data["confidence"] <= 1
    
    @pytest.mark.asyncio
    async def test_alerts_workflow(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """
        Test 6: Alerts Workflow
        Request → MCP → Snowflake KPI Alerts → Response
        """
        response = await async_client.get(
            "/api/v1/alerts?severity=warning",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Verify alert structure
        if data:
            alert = data[0]
            assert "id" in alert
            assert "severity" in alert
            assert "message" in alert
            assert "source" in alert
    
    @pytest.mark.asyncio
    async def test_mapping_workflow(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_db: any
    ):
        """
        Test 7: Mapping Registration & Retrieval
        Create Mapping → Store in DB → Retrieve
        """
        # Step 1: Register mapping
        mapping_data = {
            "source_system": "netsuite",
            "source_id": "12345",
            "target_system": "erp",
            "target_id": "emp_67890",
            "entity_type": "employee",
            "extra_data": {"practice": "downtown"}
        }
        
        create_response = await async_client.post(
            "/api/v1/mappings/register",
            json=mapping_data,
            headers=auth_headers
        )
        
        assert create_response.status_code == 200
        created = create_response.json()
        assert created["source_id"] == "12345"
        assert created["target_id"] == "emp_67890"
        
        # Step 2: Retrieve mappings
        get_response = await async_client.get(
            "/api/v1/mappings/employee",
            headers=auth_headers
        )
        
        assert get_response.status_code == 200
        mappings = get_response.json()
        assert isinstance(mappings, list)
        assert any(m["source_id"] == "12345" for m in mappings)
    
    @pytest.mark.asyncio
    async def test_authentication_workflow(self, async_client: AsyncClient):
        """
        Test 8: Authentication
        Request without auth → 401
        Request with valid auth → 200
        """
        # Without auth
        response = await async_client.get("/api/v1/integrations/status")
        assert response.status_code == 403  # No credentials provided
        
        # With invalid auth
        response = await async_client.get(
            "/api/v1/integrations/status",
            headers={"Authorization": "Bearer invalid-key"}
        )
        assert response.status_code == 401  # Invalid credentials
        
        # With valid auth
        response = await async_client.get(
            "/api/v1/integrations/status",
            headers={"Authorization": "Bearer test-api-key-for-integration-testing-min-32-chars"}
        )
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling across the system"""
    
    @pytest.mark.asyncio
    async def test_invalid_entity_type(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """Test handling of invalid entity types"""
        response = await async_client.get(
            "/api/v1/mappings/invalid_entity_type_12345",
            headers=auth_headers
        )
        
        # Should still return 200 with empty list (valid query, no results)
        assert response.status_code == 200
        assert response.json() == []
    
    @pytest.mark.asyncio
    async def test_missing_required_params(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """Test handling of missing required parameters"""
        response = await async_client.get(
            "/api/v1/finance/summary",  # Missing required 'location' param
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error


class TestCaching:
    """Test caching behavior"""
    
    @pytest.mark.asyncio
    async def test_response_caching(
        self,
        async_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that responses are cached properly"""
        # First request - cache miss
        response1 = await async_client.get(
            "/api/v1/finance/summary?location=downtown",
            headers=auth_headers
        )
        assert response1.status_code == 200
        
        # Second request - should hit cache
        response2 = await async_client.get(
            "/api/v1/finance/summary?location=downtown",
            headers=auth_headers
        )
        assert response2.status_code == 200
        
        # Responses should be identical (from cache)
        assert response1.json() == response2.json()

