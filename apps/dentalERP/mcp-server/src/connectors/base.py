"""Base connector class for all external integrations"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

from ..utils.cache import cached, get_cache
from ..utils.logger import logger
from ..utils.retry import CircuitBreaker, retry_with_backoff


@dataclass
class ConnectorConfig:
    """Configuration for a connector"""
    api_url: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    cache_ttl: int = 300


@dataclass
class ConnectorResponse:
    """Standardized response from connectors"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class BaseConnector(ABC):
    """
    Abstract base class for all integration connectors
    
    Provides common functionality:
    - HTTP client with timeout
    - Retry logic with exponential backoff
    - Circuit breaker for fault tolerance
    - Response caching
    - Logging and error handling
    """
    
    def __init__(self, config: ConnectorConfig):
        self.config = config
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=20,  # Increased from 5 for production tolerance
            recovery_timeout=300   # Increased from 60s to 5 minutes
        )
        self._session: Optional[aiohttp.ClientSession] = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Connector name (e.g., 'ADP', 'NetSuite')"""
        pass
    
    @property
    @abstractmethod
    def integration_type(self) -> str:
        """Integration type identifier (e.g., 'adp', 'netsuite')"""
        pass
    
    async def get_session(self) -> aiohttp.ClientSession:
        """
        Get or create HTTP session
        
        Returns:
            aiohttp.ClientSession: HTTP session with default headers
        """
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            headers = self._get_default_headers()
            
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
        
        return self._session
    
    def _get_default_headers(self) -> Dict[str, str]:
        """
        Get default HTTP headers
        
        Returns:
            Dict of default headers
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"MCP-Server/1.0 ({self.name})"
        }
        
        # Add API key if configured
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        return headers
    
    @retry_with_backoff(max_attempts=3, initial_delay=1.0, exceptions=(aiohttp.ClientError,))
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional request parameters
            
        Returns:
            JSON response data
            
        Raises:
            aiohttp.ClientError: On request failure
        """
        url = f"{self.config.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        logger.info(f"[{self.name}] {method} {url}")
        
        session = await self.get_session()
        
        async with session.request(method, url, **kwargs) as response:
            response.raise_for_status()
            data = await response.json()
            
            logger.debug(f"[{self.name}] Response: {response.status}")
            return data
    
    async def test_connection(self) -> bool:
        """
        Test connection to external API
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            await self._test_connection_impl()
            logger.info(f"[{self.name}] Connection test successful")
            return True
        except Exception as e:
            logger.error(f"[{self.name}] Connection test failed: {e}")
            return False
    
    @abstractmethod
    async def _test_connection_impl(self):
        """
        Implementation-specific connection test
        Override this in subclasses
        """
        pass
    
    @abstractmethod
    async def fetch_data(
        self,
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> ConnectorResponse:
        """
        Fetch data from external system
        
        Args:
            entity_type: Type of entity to fetch (e.g., 'employee', 'patient')
            filters: Optional filters for the query
            
        Returns:
            ConnectorResponse with data or error
        """
        pass
    
    async def transform_data(
        self,
        raw_data: Any,
        entity_type: str
    ) -> List[Dict[str, Any]]:
        """
        Transform external data to standard format
        
        Args:
            raw_data: Raw data from external API
            entity_type: Entity type
            
        Returns:
            List of transformed records
        """
        # Default implementation - override in subclasses for custom transformation
        if isinstance(raw_data, list):
            return raw_data
        elif isinstance(raw_data, dict):
            return [raw_data]
        else:
            return []
    
    async def close(self):
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug(f"[{self.name}] Session closed")
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(type={self.integration_type})>"

