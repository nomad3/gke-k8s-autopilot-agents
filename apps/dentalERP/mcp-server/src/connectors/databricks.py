"""Databricks SQL warehouse connector"""

from typing import Any, Dict, List, Optional

from databricks import sql

from .warehouse_base import BaseWarehouseConnector
from ..utils.logger import logger


class DatabricksConnector(BaseWarehouseConnector):
    """
    Databricks SQL Warehouse Connector

    Supports Databricks SQL with:
    - Unity Catalog (catalog.schema.table)
    - SQL Warehouses (formerly SQL Endpoints)
    - Parameterized queries (SQL injection protection)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Databricks connector

        Config structure:
        {
            "server_hostname": "your-workspace.cloud.databricks.com",
            "http_path": "/sql/1.0/warehouses/...",
            "access_token": "dapi...",
            "catalog": "your_catalog",  # Unity Catalog
            "schema": "default"
        }

        Args:
            config: Databricks connection configuration
        """
        super().__init__(config)
        self.server_hostname = config["server_hostname"]
        self.http_path = config["http_path"]
        self.access_token = config["access_token"]
        self.catalog = config.get("catalog", "hive_metastore")
        self.schema = config.get("schema", "default")
        self._connection = None

    @property
    def warehouse_type(self) -> str:
        """Return warehouse type identifier"""
        return "databricks"

    async def connect(self) -> bool:
        """
        Establish connection to Databricks SQL warehouse

        Returns:
            bool: True if connection successful

        Raises:
            ConnectionError: If connection fails
        """
        try:
            self._connection = sql.connect(
                server_hostname=self.server_hostname,
                http_path=self.http_path,
                access_token=self.access_token,
                catalog=self.catalog,
                schema=self.schema
            )
            logger.info(
                f"Connected to Databricks: {self.server_hostname} "
                f"(catalog={self.catalog}, schema={self.schema})"
            )
            return True
        except Exception as e:
            error_msg = f"Failed to connect to Databricks: {str(e)}"
            logger.error(error_msg)
            raise ConnectionError(error_msg)

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute SQL query with parameterization

        Databricks SQL Connector 3.0.0+ supports native parameterized queries
        for SQL injection protection.

        Args:
            query: SQL query string (use :param_name for parameters)
            parameters: Query parameters dictionary

        Returns:
            List of dictionaries representing rows

        Raises:
            RuntimeError: If query execution fails

        Example:
            >>> results = await connector.execute_query(
            ...     "SELECT * FROM gold.production WHERE date = :date",
            ...     {"date": "2025-01-01"}
            ... )
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
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()

            # Convert to list of dicts
            results = [
                dict(zip(columns, row))
                for row in rows
            ]

            logger.debug(f"Databricks query returned {len(results)} rows")
            return results

        except Exception as e:
            error_msg = f"Databricks query execution failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        finally:
            cursor.close()

    async def check_connection(self) -> bool:
        """
        Check if connection is alive

        Returns:
            bool: True if connection is healthy
        """
        try:
            await self.execute_query("SELECT 1")
            return True
        except Exception as e:
            logger.warning(f"Databricks connection check failed: {e}")
            return False

    async def get_tables(self, schema: Optional[str] = None) -> List[str]:
        """
        Get list of tables in schema

        Args:
            schema: Schema name (uses default if None)

        Returns:
            List of table names
        """
        target_schema = schema or self.schema
        query = f"SHOW TABLES IN {self.catalog}.{target_schema}"

        try:
            results = await self.execute_query(query)
            # SHOW TABLES returns rows with 'tableName' column
            return [row.get("tableName") or row.get("table") for row in results]
        except Exception as e:
            logger.error(f"Failed to get Databricks tables: {e}")
            return []

    async def get_table_stats(self, table: str) -> Dict[str, Any]:
        """
        Get table statistics

        Args:
            table: Table name (can be catalog.schema.table or just table)

        Returns:
            Dictionary with table statistics

        Example:
            {
                "num_rows": 1000000,
                "size_bytes": 50000000,
                "location": "s3://bucket/path"
            }
        """
        # Ensure fully qualified table name
        if "." not in table:
            full_table = f"{self.catalog}.{self.schema}.{table}"
        else:
            full_table = table

        query = f"DESCRIBE EXTENDED {full_table}"

        try:
            results = await self.execute_query(query)

            # Parse DESCRIBE EXTENDED output
            stats = {}
            for row in results:
                col_name = row.get("col_name", "")
                data_type = row.get("data_type", "")

                # Extract relevant statistics
                if col_name in ["Table Size", "Num Rows", "Location", "Provider"]:
                    stats[col_name.lower().replace(" ", "_")] = data_type

            logger.debug(f"Databricks table stats for {full_table}: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Failed to get Databricks table stats: {e}")
            return {}

    async def close(self) -> None:
        """Close Databricks connection"""
        if self._connection:
            try:
                self._connection.close()
                logger.info("Databricks connection closed")
            except Exception as e:
                logger.warning(f"Error closing Databricks connection: {e}")
            finally:
                self._connection = None
