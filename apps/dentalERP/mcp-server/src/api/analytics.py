"""
Analytics API - Multi-Tenant Data Warehouse Queries
All data operations happen in warehouse (Snowflake/Databricks), backend just passes queries through
Each tenant uses their configured warehouse automatically via tenant context
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from ..core.security import get_api_key_header
from ..core.tenant import TenantContext
from ..services.warehouse_router import get_tenant_warehouse
from ..services.forecasting import get_forecasting_service
from ..utils.logger import logger

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


class ProductionMetricsResponse(BaseModel):
    """Production metrics from Gold layer"""
    practice_location: str
    report_date: str
    total_production: float
    net_production: float
    patient_visits: int
    production_per_visit: float
    collection_rate_pct: float
    extraction_method: str
    duplicate_count: int


@router.get("/production/daily", response_model=List[Dict[str, Any]])
async def get_daily_production(
    practice_location: Optional[str] = Query(None, description="Filter by practice location"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    api_key: str = Depends(get_api_key_header)
):
    """
    Get daily production metrics from tenant's data warehouse (Snowflake/Databricks).
    All filtering and aggregation happens in the warehouse.

    Automatically uses the current tenant's configured warehouse.
    """
    # Get current tenant's warehouse connector
    try:
        warehouse = await get_tenant_warehouse()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Get tenant info for logging and filtering
    tenant = TenantContext.get_tenant()
    logger.info(f"Tenant '{tenant.tenant_code}' querying daily production metrics")

    # Build WHERE clause dynamically (warehouse handles the logic)
    # IMPORTANT: Always filter by tenant_id for data isolation
    where_clauses = [f"tenant_id = '{tenant.tenant_code}'"]

    if practice_location:
        where_clauses.append(f"practice_location = '{practice_location}'")
    if start_date:
        where_clauses.append(f"report_date >= '{start_date}'")
    if end_date:
        where_clauses.append(f"report_date <= '{end_date}'")

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    # Simple query - let warehouse do all the work
    query = f"""
        SELECT
            practice_location,
            report_date,
            day_name,
            total_production,
            net_production,
            adjustments,
            collections,
            patient_visits,
            production_per_visit,
            collection_rate_pct,
            extraction_method,
            data_quality_score,
            duplicate_count,
            uploaded_at,
            calculated_at
        FROM bronze_gold.daily_production_metrics
        {where_sql}
        ORDER BY report_date DESC, practice_location
        LIMIT {limit}
    """

    logger.info(f"Querying {warehouse.warehouse_type}: {query[:200]}...")

    try:
        results = await warehouse.execute_query(query)
        return results
    except Exception as e:
        logger.error(f"Failed to query production metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query metrics: {str(e)}"
        )


@router.get("/production/summary", response_model=Dict[str, Any])
async def get_production_summary(
    practice_location: Optional[str] = Query(None, description="Filter by practice location"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    api_key: str = Depends(get_api_key_header)
):
    """
    Get production summary with aggregations.
    All calculations done in tenant's warehouse, backend just returns results.
    """
    # Get current tenant's warehouse connector
    try:
        warehouse = await get_tenant_warehouse()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    tenant = TenantContext.get_tenant()
    logger.info(f"Tenant '{tenant.tenant_code}' querying production summary")

    # Always filter by tenant_id for data isolation
    where_clauses = [f"tenant_id = '{tenant.tenant_code}'"]

    if practice_location:
        where_clauses.append(f"practice_location = '{practice_location}'")
    if start_date:
        where_clauses.append(f"report_date >= '{start_date}'")
    if end_date:
        where_clauses.append(f"report_date <= '{end_date}'")

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    # Warehouse does all aggregations
    query = f"""
        SELECT
            COUNT(DISTINCT practice_location) as practice_count,
            COUNT(DISTINCT report_date) as date_count,
            SUM(total_production) as total_production,
            SUM(net_production) as total_net_production,
            SUM(patient_visits) as total_visits,
            AVG(production_per_visit) as avg_production_per_visit,
            AVG(collection_rate_pct) as avg_collection_rate,
            MIN(report_date) as earliest_date,
            MAX(report_date) as latest_date
        FROM bronze_gold.daily_production_metrics
        {where_sql}
    """

    logger.info(f"Querying {warehouse.warehouse_type} summary: {query[:200]}...")

    try:
        results = await warehouse.execute_query(query)
        return results[0] if results else {}
    except Exception as e:
        logger.error(f"Failed to query production summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query summary: {str(e)}"
        )


@router.get("/production/by-practice", response_model=List[Dict[str, Any]])
async def get_production_by_practice(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    api_key: str = Depends(get_api_key_header)
):
    """
    Get production metrics grouped by practice.
    Tenant's warehouse handles all GROUP BY logic.
    """
    # Get current tenant's warehouse connector
    try:
        warehouse = await get_tenant_warehouse()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    tenant = TenantContext.get_tenant()
    logger.info(f"Tenant '{tenant.tenant_code}' querying production by practice")

    # Always filter by tenant_id for data isolation
    where_clauses = [f"tenant_id = '{tenant.tenant_code}'"]

    if start_date:
        where_clauses.append(f"report_date >= '{start_date}'")
    if end_date:
        where_clauses.append(f"report_date <= '{end_date}'")

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    # Let warehouse do the grouping and aggregation
    query = f"""
        SELECT
            practice_location,
            COUNT(DISTINCT report_date) as days_reported,
            SUM(total_production) as total_production,
            SUM(net_production) as total_net_production,
            SUM(patient_visits) as total_visits,
            AVG(production_per_visit) as avg_production_per_visit,
            AVG(collection_rate_pct) as avg_collection_rate,
            MIN(report_date) as earliest_date,
            MAX(report_date) as latest_date
        FROM bronze_gold.daily_production_metrics
        {where_sql}
        GROUP BY practice_location
        ORDER BY total_production DESC
    """

    logger.info(f"Querying {warehouse.warehouse_type} by practice: {query[:200]}...")

    try:
        results = await warehouse.execute_query(query)
        return results
    except Exception as e:
        logger.error(f"Failed to query by practice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query by practice: {str(e)}"
        )


@router.get("/insights", response_model=Dict[str, Any])
async def get_ai_insights(
    practice_name: Optional[str] = Query(None, description="Filter by practice name"),
    period: str = Query("month", description="Time period for analysis"),
    api_key: str = Depends(get_api_key_header)
):
    """
    Generate AI-powered natural language insights using GPT-4.

    Queries Snowflake for top practices and recent alerts, then uses GPT-4
    to generate a concise executive summary with actionable insights.

    Results are cached for 1 hour.
    """
    tenant = TenantContext.get_tenant()
    logger.info(f"Tenant '{tenant.tenant_code}' requesting AI insights")

    try:
        forecasting_service = get_forecasting_service()
        insight_text = await forecasting_service.generate_insights(
            practice_name=practice_name,
            period=period
        )

        return {
            "insight": insight_text,
            "practice_name": practice_name,
            "period": period,
            "generated_at": datetime.utcnow().isoformat(),
            "tenant_code": tenant.tenant_code
        }
    except Exception as e:
        logger.error(f"Failed to generate insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insights: {str(e)}"
        )
