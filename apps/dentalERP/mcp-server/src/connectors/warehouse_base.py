"""Base connector class for data warehouse integrations"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..utils.logger import logger


class BaseWarehouseConnector(ABC):
    """
    Abstract base class for data warehouse connectors

    Supports:
    - Snowflake
    - Databricks
    - Future: BigQuery, Redshift, etc.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize warehouse connector

        Args:
            config: Warehouse-specific configuration dictionary
        """
        self.config = config
        self._connection = None

    @property
    @abstractmethod
    def warehouse_type(self) -> str:
        """Warehouse type identifier (e.g., 'snowflake', 'databricks')"""
        pass

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to data warehouse

        Returns:
            bool: True if connection successful, False otherwise

        Raises:
            ConnectionError: If connection fails
        """
        pass

    @abstractmethod
    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results

        Args:
            query: SQL query string (use parameters for injection protection)
            parameters: Query parameters for parameterized queries

        Returns:
            List of dictionaries representing query results

        Raises:
            RuntimeError: If query execution fails
        """
        pass

    @abstractmethod
    async def check_connection(self) -> bool:
        """
        Check if connection is alive

        Returns:
            bool: True if connection is healthy, False otherwise
        """
        pass

    @abstractmethod
    async def get_tables(self, schema: Optional[str] = None) -> List[str]:
        """
        Get list of tables in schema

        Args:
            schema: Schema/database name (uses default if None)

        Returns:
            List of table names
        """
        pass

    @abstractmethod
    async def get_table_stats(self, table: str) -> Dict[str, Any]:
        """
        Get table statistics (row count, size, etc.)

        Args:
            table: Fully qualified table name

        Returns:
            Dictionary with table statistics
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Close warehouse connection and cleanup resources
        """
        pass

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
