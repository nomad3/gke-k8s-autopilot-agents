"""
Snowflake data warehouse connector

Handles connection and operations with Snowflake:
- Bulk loading raw data to Bronze layer
- Executing queries on Gold layer for analytics
- Managing connection pools for performance

IMPORTANT: This connector does NOT do transformations.
All transformations are handled by dbt models running in Snowflake.
"""

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .warehouse_base import BaseWarehouseConnector
from ..core.config import settings
from ..utils.logger import logger
from ..utils.retry import retry_with_backoff


class SnowflakeConnector(BaseWarehouseConnector):
    """
    Snowflake data warehouse connector

    Responsibilities:
    - LOAD raw data to Bronze layer (no transformation)
    - QUERY pre-computed Gold layer tables (no calculation)
    - Connection pooling and resource management

    NOT responsible for:
    - Data transformations (dbt's job)
    - Aggregations (Snowflake SQL's job)
    - Complex calculations (dbt models)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Snowflake connector

        Args:
            config: Optional configuration dict. If None, uses settings from environment.
                   Format: {
                       'account': 'account-locator',
                       'user': 'username',
                       'password': 'password',  # Or 'private_key': bytes
                       'warehouse': 'warehouse_name',
                       'database': 'database_name',
                       'schema': 'schema_name',
                       'role': 'role_name'
                   }
        """
        # Use config if provided, otherwise use global settings
        if config:
            super().__init__(config)
        else:
            # Build config from settings
            super().__init__({
                'account': settings.snowflake_account,
                'user': settings.snowflake_user,
                'password': settings.snowflake_password,
                'warehouse': settings.snowflake_warehouse,
                'database': settings.snowflake_database,
                'schema': settings.snowflake_schema or 'PUBLIC',
                'role': settings.snowflake_role,
                'private_key_path': getattr(settings, 'snowflake_private_key_path', None),
                'private_key_passphrase': getattr(settings, 'snowflake_private_key_passphrase', None),
            })

        self._is_enabled = self._check_enabled()

    @property
    def warehouse_type(self) -> str:
        """Warehouse type identifier"""
        return "snowflake"

    def _check_enabled(self) -> bool:
        """Check if Snowflake credentials are configured"""
        required_fields = ['account', 'user', 'warehouse', 'database']
        enabled = all(self.config.get(field) for field in required_fields)

        # Check authentication method
        has_password = bool(self.config.get('password'))
        has_private_key = bool(self.config.get('private_key_path'))

        if not (has_password or has_private_key):
            logger.warning("Snowflake: No authentication method configured (password or private_key)")
            enabled = False

        if not enabled:
            logger.warning("Snowflake is not fully configured. Set SNOWFLAKE_* environment variables.")

        return enabled

    @property
    def is_enabled(self) -> bool:
        """Check if Snowflake integration is available"""
        return self._is_enabled

    async def connect(self) -> bool:
        """
        Establish connection to Snowflake

        Supports multiple authentication methods:
        - Username/Password (for development)
        - Key-Pair Authentication (recommended for production)

        Returns:
            bool: True if connection successful, False otherwise

        Raises:
            ConnectionError: If connection fails
        """
        if not self.is_enabled:
            raise ConnectionError("Snowflake is not configured")

        if self._connection is not None:
            # Already connected
            return True

        try:
            # Import snowflake connector (only if configured)
            import snowflake.connector

            logger.info("Initializing Snowflake connection...")

            # Build base connection parameters
            conn_params = {
                'account': self.config['account'],
                'user': self.config['user'],
                'warehouse': self.config['warehouse'],
                'database': self.config['database'],
                'schema': self.config.get('schema', 'PUBLIC'),
                'role': self.config.get('role'),
                # Connection parameters
                'client_session_keep_alive': True,
                'network_timeout': 30,
                # Performance settings
                'autocommit': True,
            }

            # Choose authentication method
            if self.config.get('private_key_path'):
                # Key-Pair Authentication (recommended for production)
                logger.info("Using key-pair authentication")

                try:
                    from cryptography.hazmat.backends import default_backend
                    from cryptography.hazmat.primitives import serialization

                    with open(self.config['private_key_path'], 'rb') as key_file:
                        # Read private key with optional passphrase
                        password = None
                        if self.config.get('private_key_passphrase'):
                            password = self.config['private_key_passphrase'].encode()

                        private_key = serialization.load_pem_private_key(
                            key_file.read(),
                            password=password,
                            backend=default_backend()
                        )

                        # Serialize private key to DER format for Snowflake
                        pkb = private_key.private_bytes(
                            encoding=serialization.Encoding.DER,
                            format=serialization.PrivateFormat.PKCS8,
                            encryption_algorithm=serialization.NoEncryption()
                        )

                        conn_params['private_key'] = pkb

                except ImportError:
                    raise ConnectionError("cryptography package required for key-pair auth. Run: pip install cryptography")
                except FileNotFoundError:
                    raise ConnectionError(f"Private key file not found: {self.config['private_key_path']}")
                except Exception as e:
                    raise ConnectionError(f"Failed to load private key: {e}")

            elif self.config.get('password'):
                # Username/Password Authentication (for development)
                logger.info("Using username/password authentication")
                conn_params['password'] = self.config['password']

            elif self.config.get('private_key'):
                # Direct private key bytes (for tenant-specific configs)
                logger.info("Using direct private key authentication")
                conn_params['private_key'] = self.config['private_key']

            else:
                raise ConnectionError("No authentication method configured. Set password or private_key_path")

            # Create connection
            self._connection = snowflake.connector.connect(**conn_params)

            logger.info(f"✅ Snowflake connected: {self.config['database']}.{self.config['schema']}")
            return True

        except ImportError:
            raise ConnectionError("snowflake-connector-python not installed. Run: pip install snowflake-connector-python")
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {e}")
            raise ConnectionError(f"Failed to connect to Snowflake: {e}")

    async def check_connection(self) -> bool:
        """
        Check if connection is alive

        Returns:
            bool: True if connection is healthy, False otherwise
        """
        if not self.is_enabled:
            return False

        try:
            if not self._connection:
                await self.connect()

            # Run simple query to test connection
            cursor = self._connection.cursor()
            cursor.execute("SELECT CURRENT_VERSION()")
            version = cursor.fetchone()
            cursor.close()

            logger.debug(f"✅ Snowflake connection healthy. Version: {version[0] if version else 'unknown'}")
            return True

        except Exception as e:
            logger.error(f"Snowflake connection check failed: {e}")
            return False

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results

        Typically used to query pre-computed Gold layer tables.
        Should NOT perform heavy calculations - query pre-computed results.

        Args:
            query: SQL SELECT statement
            parameters: Optional query parameters (for parameterized queries)

        Returns:
            List of dictionaries representing query results

        Raises:
            RuntimeError: If query execution fails
        """
        if not self.is_enabled:
            return []

        try:
            if not self._connection:
                await self.connect()

            # Snowflake connector is synchronous, so run in thread pool
            import asyncio
            loop = asyncio.get_event_loop()

            def _execute_sync():
                """Synchronous execution wrapper"""
                from snowflake.connector import DictCursor

                cursor = self._connection.cursor(DictCursor)

                # Execute with parameters if provided
                if parameters:
                    # Convert dict to list for positional parameters
                    cursor.execute(query, list(parameters.values()) if isinstance(parameters, dict) else parameters)
                else:
                    cursor.execute(query)

                results = cursor.fetchall()
                cursor.close()

                logger.debug(f"Query returned {len(results)} rows")
                return results

            # Run blocking Snowflake operations in thread pool
            results = await loop.run_in_executor(None, _execute_sync)
            return results

        except Exception as e:
            logger.error(f"Query execution failed: {e}", exc_info=True)
            raise RuntimeError(f"Query execution failed: {e}")

    async def get_tables(self, schema: Optional[str] = None) -> List[str]:
        """
        Get list of tables in schema

        Args:
            schema: Schema name (uses default from config if None)

        Returns:
            List of table names
        """
        schema = schema or self.config.get('schema', 'PUBLIC')

        try:
            query = f"SHOW TABLES IN SCHEMA {self.config['database']}.{schema}"
            results = await self.execute_query(query)

            # SHOW TABLES returns columns: created_on, name, database_name, schema_name, kind, etc.
            return [row.get('name', row.get('NAME', '')) for row in results]

        except Exception as e:
            logger.error(f"Failed to get tables: {e}")
            return []

    async def get_table_stats(self, table: str) -> Dict[str, Any]:
        """
        Get table statistics (row count, size, etc.)

        Args:
            table: Fully qualified table name (e.g., 'bronze.pms_day_sheets')

        Returns:
            Dictionary with table statistics
        """
        try:
            # Get row count
            count_query = f"SELECT COUNT(*) as row_count FROM {table}"
            count_result = await self.execute_query(count_query)
            row_count = count_result[0].get('ROW_COUNT', 0) if count_result else 0

            # Get table info
            info_query = f"SHOW TABLES LIKE '{table.split('.')[-1]}' IN SCHEMA {self.config['database']}.{table.split('.')[0]}"
            info_result = await self.execute_query(info_query)

            stats = {
                'row_count': row_count,
                'table_name': table,
            }

            if info_result:
                stats.update({
                    'created_on': info_result[0].get('created_on'),
                    'size_bytes': info_result[0].get('bytes'),
                })

            return stats

        except Exception as e:
            logger.error(f"Failed to get table stats: {e}")
            return {'error': str(e)}

    async def close(self) -> None:
        """Close Snowflake connection and cleanup resources"""
        if self._connection:
            try:
                self._connection.close()
                logger.info("Snowflake connection closed")
            except Exception as e:
                logger.error(f"Error closing Snowflake connection: {e}")
            finally:
                self._connection = None

    # ====================================================================
    # Legacy/convenience methods (preserved for backward compatibility)
    # ====================================================================

    @retry_with_backoff(max_attempts=3)
    async def test_connection(self) -> bool:
        """
        Test Snowflake connection (legacy method)

        Returns:
            True if connection successful, False otherwise
        """
        return await self.check_connection()

    async def get_connection(self):
        """
        Get or create Snowflake connection (legacy method)

        Returns:
            Snowflake connection object or None if not configured
        """
        if not self.is_enabled:
            return None

        if not self._connection:
            await self.connect()

        return self._connection

    async def bulk_insert_bronze(
        self,
        table_name: str,
        records: List[Dict[str, Any]],
        batch_size: int = 10000
    ) -> int:
        """
        Bulk insert raw records into Snowflake Bronze layer

        This is an EXTRACT and LOAD operation only - NO transformation!
        Stores entire records as JSON in VARIANT columns for flexibility.

        MULTI-TENANT: Automatically injects tenant_id from TenantContext into all records.

        Args:
            table_name: Bronze layer table (e.g., 'bronze.netsuite_journalentry')
            records: List of raw records with minimal metadata
            batch_size: Number of records per batch

        Returns:
            Number of records inserted

        Example record structure:
            {
                "id": "uuid",
                "source_system": "netsuite",
                "entity_type": "journalentry",
                "raw_data": {...},  # Entire API response as JSON
                "extracted_at": "2025-01-01T00:00:00Z",
                "tenant_id": "default"  # Automatically injected
            }
        """
        if not self.is_enabled or not records:
            return 0

        try:
            # Import TenantContext for tenant_id injection
            from ..core.tenant import TenantContext

            if not self._connection:
                await self.connect()

            # Get current tenant from context
            tenant = TenantContext.get_tenant()
            tenant_id = tenant.tenant_code if tenant else "default"

            logger.info(f"🔍 bulk_insert_bronze called with {len(records)} records (tenant: {tenant_id})")
            if records:
                logger.info(f"🔍 First record keys: {list(records[0].keys())}")
                logger.info(f"🔍 First record type: {type(records[0])}")

            # Inject tenant_id into all records if not already present
            for record in records:
                if 'tenant_id' not in record:
                    record['tenant_id'] = tenant_id

            total_inserted = 0
            cursor = self._connection.cursor()

            # Process in batches for better performance
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]

                if not batch:
                    continue

                # Get all columns from first record
                first_record = batch[0]
                logger.info(f"🔍 First record in batch: {type(first_record)}, keys sample: {str(list(first_record.keys())[:5])}")
                columns = list(first_record.keys())

                logger.info(f"Inserting {len(batch)} records with columns: {columns}")

                # Debug: Check each column name for issues
                for idx, col in enumerate(columns):
                    logger.info(f"🔍 Column {idx}: repr={repr(col)}, type={type(col)}, len={len(col)}")

                # Build INSERT query
                columns_str = ", ".join(columns)

                # Prepare values for each record
                for record in batch:
                    # Build SELECT clause with mix of bind params and literal JSON
                    select_parts = []
                    bind_values = []

                    for col in columns:
                        value = record[col]

                        if isinstance(value, (dict, list)):
                            # VARIANT column - use PARSE_JSON with bind parameter containing JSON string
                            json_str = json.dumps(value)
                            select_parts.append("PARSE_JSON(%s)")
                            bind_values.append(json_str)
                        else:
                            # Regular column - use bind parameter
                            select_parts.append("%s")
                            bind_values.append(value)

                    select_str = ", ".join(select_parts)

                    # Use INSERT INTO ... SELECT instead of VALUES
                    insert_query = f"""
                    INSERT INTO {table_name}
                    ({columns_str})
                    SELECT {select_str}
                    """

                    # Execute with bind parameters
                    try:
                        cursor.execute(insert_query, bind_values)
                    except Exception as e:
                        logger.error(f"❌ cursor.execute() failed: {type(e).__name__}: {e}")
                        logger.error(f"❌ Query was: {insert_query[:500]}...")
                        logger.error(f"❌ Bind values: {bind_values[:3]}")
                        raise

                total_inserted += len(batch)
                logger.info(f"Inserted batch {i // batch_size + 1}: {len(batch)} records → {table_name}")

            cursor.close()

            logger.info(f"✅ Bronze layer insert complete: {total_inserted} records → {table_name}")
            logger.info(f"   Next step: Run dbt to transform Bronze → Silver → Gold")

            return total_inserted

        except Exception as e:
            logger.error(f"Failed to insert to Bronze layer: {e}", exc_info=True)
            return 0

    async def execute_many(
        self,
        statement: str,
        records: List[Any]  # Can be list of tuples or list of dicts
    ) -> int:
        """
        Execute bulk INSERT with multiple records

        Args:
            statement: SQL INSERT statement with %s placeholders
            records: List of tuples (values in column order)

        Returns:
            Number of rows inserted
        """
        if not self.is_enabled:
            return 0

        if not records:
            return 0

        try:
            if not self._connection:
                await self.connect()

            cursor = self._connection.cursor()

            # Use executemany for bulk insert
            cursor.executemany(statement, records)

            rows_affected = cursor.rowcount
            cursor.close()

            logger.info(f"✅ Bulk inserted {rows_affected} rows to Snowflake")
            return rows_affected

        except Exception as e:
            logger.error(f"Snowflake bulk insert failed: {e}")
            logger.error(f"Statement: {statement}")
            logger.error(f"Sample record: {records[0] if records else 'none'}")
            raise

    async def execute_dml(
        self,
        statement: str,
        params: Optional[List[Any]] = None
    ) -> int:
        """
        Execute DML statement (INSERT, UPDATE, DELETE)

        Args:
            statement: SQL DML statement
            params: Optional parameters

        Returns:
            Number of rows affected
        """
        if not self.is_enabled:
            return 0

        try:
            if not self._connection:
                await self.connect()

            cursor = self._connection.cursor()

            if params:
                cursor.execute(statement, params)
            else:
                cursor.execute(statement)

            rows_affected = cursor.rowcount
            cursor.close()

            logger.info(f"DML affected {rows_affected} rows")

            return rows_affected

        except Exception as e:
            logger.error(f"DML execution failed: {e}", exc_info=True)
            return 0

    async def query_gold_layer(
        self,
        table_name: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Query Gold layer table (pre-computed analytics)

        Args:
            table_name: Gold table (e.g., 'gold.monthly_production_kpis')
            filters: Optional WHERE clause filters
            limit: Max rows to return

        Returns:
            Pre-computed analytics results
        """
        where_clause = ""
        params = []

        if filters:
            where_conditions = []
            for key, value in filters.items():
                where_conditions.append(f"{key} = %s")
                params.append(value)
            where_clause = "WHERE " + " AND ".join(where_conditions)

        query = f"""
        SELECT *
        FROM {table_name}
        {where_clause}
        ORDER BY 1 DESC
        LIMIT {limit}
        """

        return await self.execute_query(query, params if params else None)


# Singleton instance (for backward compatibility)
_snowflake_connector: Optional[SnowflakeConnector] = None


def get_snowflake_connector() -> SnowflakeConnector:
    """Get singleton Snowflake connector instance (legacy)"""
    global _snowflake_connector
    if _snowflake_connector is None:
        _snowflake_connector = SnowflakeConnector()
    return _snowflake_connector
