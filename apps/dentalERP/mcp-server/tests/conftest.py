"""
Pytest configuration and fixtures for MCP Server tests
Provides reusable test fixtures and utilities
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure the ``src`` package is importable when tests are run from the
# repository root (e.g. ``pytest`` without changing directories). Using an
# absolute path avoids relying on the current working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Provide required configuration defaults for settings initialised during
# module import. These values match the dedicated test credentials used
# elsewhere in the suite and prevent ``ValidationError`` when environment
# variables are absent.
os.environ.setdefault(
    "MCP_API_KEY", "test-api-key-for-integration-testing-min-32-chars"
)
os.environ.setdefault(
    "SECRET_KEY", "test-secret-key-for-integration-testing-min-32-chars"
)

from src.core.config import Settings
from src.core.database import Base, get_db
from src.main import app


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register custom command line options."""

    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require external services",
    )


# Test settings
@pytest.fixture(scope="session")
def test_settings():
    """Test environment settings"""
    return Settings(
        environment="test",
        debug=True,
        mcp_api_key="test-api-key-for-integration-testing-min-32-chars",
        secret_key="test-secret-key-for-integration-testing-min-32-chars",
        postgres_host="localhost",
        postgres_db="mcp_test",
        postgres_user="postgres",
        postgres_password="postgres",
        redis_host="localhost",
        log_level="DEBUG"
    )


# Async test database
@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session
    Each test gets a fresh database
    """
    # Create test engine
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/mcp_test",
        echo=False,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    # Cleanup - drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


# Test client
@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Synchronous test client for FastAPI"""
    with TestClient(app) as c:
        yield c


# Async test client
@pytest_asyncio.fixture()
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Asynchronous test client for FastAPI"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# Auth headers
@pytest.fixture
def auth_headers(test_settings):
    """Headers with valid API key for authenticated requests"""
    return {
        "Authorization": f"Bearer {test_settings.mcp_api_key}",
        "Content-Type": "application/json"
    }


# Mock connector
@pytest.fixture
def mock_connector_response():
    """Mock connector response data"""
    return {
        "success": True,
        "data": [
            {
                "id": "123",
                "transaction_id": "TXN-001",
                "amount": 1500.00,
                "date": "2025-01-15"
            },
            {
                "id": "124",
                "transaction_id": "TXN-002",
                "amount": 2500.00,
                "date": "2025-01-16"
            }
        ],
        "metadata": {
            "total_results": 2,
            "source": "netsuite"
        }
    }


# Event loop for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

