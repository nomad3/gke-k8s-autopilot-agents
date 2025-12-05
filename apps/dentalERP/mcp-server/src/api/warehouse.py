"""
Data warehouse management endpoints

Provides administrative and operational endpoints for Snowflake data warehouse:
- Bronze layer data loading status
- dbt transformation triggers
- Data lineage and freshness checks
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from ..connectors.snowflake import get_snowflake_connector
from ..core.security import get_api_key_header
from ..utils.logger import logger

router = APIRouter(prefix="/api/v1/warehouse", tags=["warehouse"])

# Get Snowflake connector
snowflake_connector = get_snowflake_connector()


class BronzeLayerStatus(BaseModel):
    """Bronze layer status response"""
    table_name: str
    source_system: str
    entity_type: str
    record_count: int
    latest_extracted_at: Optional[str] = None
    oldest_extracted_at: Optional[str] = None


class DataFreshnessCheck(BaseModel):
    """Data freshness check response"""
    layer: str  # bronze, silver, gold
    table_name: str
    latest_record_timestamp: Optional[str] = None
    hours_since_update: Optional[float] = None
    is_stale: bool
    threshold_hours: int


class DbtRunRequest(BaseModel):
    """Request to trigger dbt run"""
    models: Optional[List[str]] = None  # Specific models to run, or None for all
    full_refresh: bool = False


class DbtRunResponse(BaseModel):
    """dbt run response"""
    status: str
    message: str
    models_run: List[str]
    execution_time_seconds: Optional[float] = None


@router.get("/status", response_model=Dict[str, Any])
async def get_warehouse_status(api_key: str = Depends(get_api_key_header)):
    """
    Get overall warehouse status

    Returns:
    - Connection status
    - Warehouse name and size
    - Database and schema info
    - Layer record counts (bronze, silver, gold)

    Args:
        api_key: Verified API key
    """
    if not snowflake_connector.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Snowflake is not configured. Set SNOWFLAKE_* environment variables."
        )

    logger.info("Getting warehouse status")

    try:
        # Test connection
        is_connected = await snowflake_connector.test_connection()

        if not is_connected:
            return {
                "connected": False,
                "message": "Failed to connect to Snowflake. Check credentials."
            }

        # Get warehouse info
        warehouse_info = await snowflake_connector.execute_query("""
            SELECT CURRENT_WAREHOUSE() as warehouse,
                   CURRENT_DATABASE() as database,
                   CURRENT_SCHEMA() as schema,
                   CURRENT_VERSION() as version
        """)

        # Get layer counts (example - adjust to your schema)
        bronze_count_query = """
        SELECT 'bronze' as layer, COUNT(*) as record_count
        FROM information_schema.tables
        WHERE table_schema = 'BRONZE'
        """

        silver_count_query = """
        SELECT 'silver' as layer, COUNT(*) as record_count
        FROM information_schema.tables
        WHERE table_schema = 'SILVER'
        """

        gold_count_query = """
        SELECT 'gold' as layer, COUNT(*) as record_count
        FROM information_schema.tables
        WHERE table_schema = 'GOLD'
        """

        bronze_tables = await snowflake_connector.execute_query(bronze_count_query)
        silver_tables = await snowflake_connector.execute_query(silver_count_query)
        gold_tables = await snowflake_connector.execute_query(gold_count_query)

        return {
            "connected": True,
            "warehouse": warehouse_info[0] if warehouse_info else {},
            "layers": {
                "bronze": {"table_count": bronze_tables[0].get('RECORD_COUNT', 0) if bronze_tables else 0},
                "silver": {"table_count": silver_tables[0].get('RECORD_COUNT', 0) if silver_tables else 0},
                "gold": {"table_count": gold_tables[0].get('RECORD_COUNT', 0) if gold_tables else 0}
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get warehouse status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get warehouse status: {str(e)}"
        )


@router.get("/bronze/status", response_model=List[BronzeLayerStatus])
async def get_bronze_layer_status(
    source_system: Optional[str] = Query(None, description="Filter by source system"),
    api_key: str = Depends(get_api_key_header)
):
    """
    Get Bronze layer data status

    Shows record counts and data freshness for Bronze layer tables
    (raw data from external APIs)

    Args:
        source_system: Optional filter by source system (netsuite, adp, etc.)
        api_key: Verified API key

    Returns:
        List of Bronze table statuses with record counts and freshness
    """
    if not snowflake_connector.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Snowflake is not configured"
        )

    logger.info(f"Getting Bronze layer status for source_system: {source_system}")

    try:
        # Query Bronze layer metadata
        query = """
        SELECT
            table_schema || '.' || table_name AS table_name,
            source_system,
            entity_type,
            COUNT(*) AS record_count,
            MAX(extracted_at) AS latest_extracted_at,
            MIN(extracted_at) AS oldest_extracted_at
        FROM bronze.*
        """

        if source_system:
            query += f" WHERE source_system = '{source_system}'"

        query += " GROUP BY 1, 2, 3 ORDER BY 1"

        results = await snowflake_connector.execute_query(query)

        return [
            BronzeLayerStatus(
                table_name=row.get('TABLE_NAME', ''),
                source_system=row.get('SOURCE_SYSTEM', ''),
                entity_type=row.get('ENTITY_TYPE', ''),
                record_count=int(row.get('RECORD_COUNT', 0)),
                latest_extracted_at=str(row.get('LATEST_EXTRACTED_AT')) if row.get('LATEST_EXTRACTED_AT') else None,
                oldest_extracted_at=str(row.get('OLDEST_EXTRACTED_AT')) if row.get('OLDEST_EXTRACTED_AT') else None
            )
            for row in results
        ]

    except Exception as e:
        logger.error(f"Failed to get Bronze layer status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Bronze layer status: {str(e)}"
        )


@router.get("/freshness", response_model=List[DataFreshnessCheck])
async def check_data_freshness(
    threshold_hours: int = Query(24, description="Freshness threshold in hours"),
    api_key: str = Depends(get_api_key_header)
):
    """
    Check data freshness across all layers

    Identifies stale data that hasn't been updated within threshold

    Args:
        threshold_hours: Consider data stale if not updated in X hours
        api_key: Verified API key

    Returns:
        List of freshness checks for each layer
    """
    if not snowflake_connector.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Snowflake is not configured"
        )

    logger.info(f"Checking data freshness (threshold: {threshold_hours}h)")

    try:
        # Check Bronze layer freshness
        bronze_freshness = await snowflake_connector.execute_query("""
        SELECT
            'bronze' AS layer,
            source_system || '_' || entity_type AS table_name,
            MAX(extracted_at) AS latest_record_timestamp,
            DATEDIFF('hour', MAX(extracted_at), CURRENT_TIMESTAMP()) AS hours_since_update
        FROM bronze.*
        GROUP BY 1, 2
        """)

        # Check Gold layer freshness (example)
        gold_freshness = await snowflake_connector.execute_query("""
        SELECT
            'gold' AS layer,
            'monthly_production_kpis' AS table_name,
            MAX(month_date) AS latest_record_timestamp,
            DATEDIFF('hour', MAX(month_date), CURRENT_TIMESTAMP()) AS hours_since_update
        FROM gold.monthly_production_kpis
        """)

        all_freshness = bronze_freshness + gold_freshness

        return [
            DataFreshnessCheck(
                layer=row.get('LAYER', ''),
                table_name=row.get('TABLE_NAME', ''),
                latest_record_timestamp=str(row.get('LATEST_RECORD_TIMESTAMP')) if row.get('LATEST_RECORD_TIMESTAMP') else None,
                hours_since_update=float(row.get('HOURS_SINCE_UPDATE', 0)),
                is_stale=float(row.get('HOURS_SINCE_UPDATE', 0)) > threshold_hours,
                threshold_hours=threshold_hours
            )
            for row in all_freshness
        ]

    except Exception as e:
        logger.error(f"Failed to check data freshness: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check data freshness: {str(e)}"
        )


@router.post("/dbt/run", response_model=DbtRunResponse)
async def trigger_dbt_run(
    request: DbtRunRequest,
    api_key: str = Depends(get_api_key_header)
):
    """
    Trigger dbt transformation run

    Runs dbt models to transform Bronze → Silver → Gold

    NOTE: This endpoint assumes dbt Cloud API or a dbt job orchestrator.
    For local dbt, run manually: `dbt run --select <models>`

    Args:
        request: dbt run configuration
        api_key: Verified API key

    Returns:
        dbt run status and results
    """
    if not snowflake_connector.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Snowflake is not configured"
        )

    logger.info(f"Triggering dbt run: models={request.models}, full_refresh={request.full_refresh}")

    # TODO: Integrate with dbt Cloud API or Airflow/Prefect
    # For now, return a placeholder response

    return DbtRunResponse(
        status="pending",
        message="dbt run trigger not yet implemented. Run manually: dbt run",
        models_run=request.models or ["all"],
        execution_time_seconds=None
    )


@router.get("/query", response_model=List[Dict[str, Any]])
async def execute_custom_query(
    sql: str = Query(..., description="SQL SELECT query"),
    limit: int = Query(1000, description="Max rows to return"),
    api_key: str = Depends(get_api_key_header)
):
    """
    Execute custom SQL query on Snowflake

    USE WITH CAUTION: Allows arbitrary SQL execution.
    Intended for admin/debugging only.

    Only SELECT queries are allowed (no DML/DDL).

    Args:
        sql: SQL SELECT statement
        limit: Maximum rows to return
        api_key: Verified API key

    Returns:
        Query results
    """
    if not snowflake_connector.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Snowflake is not configured"
        )

    # Security: Only allow SELECT queries
    if not sql.strip().upper().startswith("SELECT"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only SELECT queries are allowed"
        )

    logger.info(f"Executing custom query: {sql[:100]}...")

    try:
        # Add LIMIT if not present
        if "LIMIT" not in sql.upper():
            sql = f"{sql.rstrip(';')} LIMIT {limit}"

        results = await snowflake_connector.execute_query(sql)

        return results

    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(e)}"
        )
