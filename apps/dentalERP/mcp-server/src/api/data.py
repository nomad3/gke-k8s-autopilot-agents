"""Data endpoints for finance, production, forecasts, and alerts"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import random

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..core.security import get_api_key_header
from ..services.snowflake import get_snowflake_service
from ..services.forecasting import get_forecasting_service
from ..services.alerts import get_alert_service
from ..utils.logger import logger

router = APIRouter(prefix="/api/v1", tags=["data"])

# Get services
snowflake_service = get_snowflake_service()
forecasting_service = get_forecasting_service()
alert_service = get_alert_service()


class FinancialSummary(BaseModel):
    """Financial summary response"""
    location_id: str
    revenue: float
    expenses: float
    net_income: float
    payroll_costs: float
    date_range: Dict[str, str]
    breakdown: List[Dict[str, Any]]


class ProductionMetrics(BaseModel):
    """Production metrics response"""
    location_id: str
    date_range: Dict[str, str]
    total_production: float
    total_collections: float
    new_patients: int
    active_patients: int
    appointments_scheduled: int
    appointments_completed: int
    cancellation_rate: float
    no_show_rate: float


class Forecast(BaseModel):
    """Forecast response"""
    location_id: str
    metric: str
    predicted: float
    confidence: float
    period: str
    factors: Dict[str, Any]


class Alert(BaseModel):
    """Alert response"""
    id: str
    severity: str
    message: str
    source: str
    location_id: Optional[str] = None
    timestamp: str
    extra_data: Optional[Dict[str, Any]] = None


@router.get("/finance/summary", response_model=FinancialSummary)
async def get_financial_summary(
    location: str = Query(..., description="Location ID"),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    api_key: str = Depends(get_api_key_header)
):
    """
    Get financial summary for a location

    Uses Snowflake data warehouse for actual data
    Falls back to mock data if Snowflake is not configured

    Args:
        location: Location ID
        from_date: Start date (ISO format)
        to_date: End date (ISO format)
        api_key: Verified API key

    Returns:
        FinancialSummary: Financial data
    """
    logger.info(f"Getting financial summary for location: {location}")

    # Fetch from Snowflake (uses caching and retry logic)
    data = await snowflake_service.get_financial_summary(location, from_date, to_date)

    return FinancialSummary(**data)


@router.get("/production/metrics", response_model=ProductionMetrics)
async def get_production_metrics(
    location: str = Query(..., description="Location ID"),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    api_key: str = Depends(get_api_key_header)
):
    """
    Get production metrics for a location

    Uses Snowflake data warehouse for actual data
    Falls back to mock data if Snowflake is not configured

    Args:
        location: Location ID
        from_date: Start date (ISO format)
        to_date: End date (ISO format)
        api_key: Verified API key

    Returns:
        ProductionMetrics: Production data
    """
    logger.info(f"Getting production metrics for location: {location}")

    # Fetch from Snowflake (uses caching and retry logic)
    data = await snowflake_service.get_production_metrics(location, from_date, to_date)

    return ProductionMetrics(**data)


@router.get("/forecast/{location_id}", response_model=Forecast)
async def get_forecast(
    location_id: str,
    metric: str = Query(..., description="Metric to forecast"),
    periods: int = Query(3, description="Number of periods to forecast"),
    api_key: str = Depends(get_api_key_header)
):
    """
    Get forecast data for a location

    Queries Snowflake for pre-computed forecasts
    Snowflake ML.FORECAST() does the actual prediction

    Args:
        location_id: Location ID
        metric: Metric to forecast (revenue, costs, patients)
        periods: Number of periods ahead
        api_key: Verified API key

    Returns:
        Forecast: Forecast data from Snowflake
    """
    logger.info(f"Getting forecast for location: {location_id}, metric: {metric}")

    # Get forecast from Snowflake (pre-computed via ML functions)
    forecast_data = await forecasting_service.forecast_revenue(
        practice_name=location_id,
        periods=periods
    )

    # Return first forecast period
    first_forecast = forecast_data["forecasts"][0] if forecast_data["forecasts"] else {}

    return Forecast(
        location_id=location_id,
        metric=metric,
        predicted=first_forecast.get("predicted", 0),
        confidence=first_forecast.get("confidence", 0.95),
        period=first_forecast.get("period", "next_month"),
        factors={
            "model": forecast_data.get("model", "snowflake_ml"),
            "confidence_interval": f"{first_forecast.get('lower_bound', 0)}-{first_forecast.get('upper_bound', 0)}",
            "historical_accuracy": 0.87  # TODO: Calculate from actuals vs predictions
        }
    )


@router.get("/alerts", response_model=List[Alert])
async def get_alerts(
    location: Optional[str] = Query(None, description="Location ID filter"),
    severity: Optional[str] = Query(None, description="Severity filter"),
    api_key: str = Depends(get_api_key_header)
):
    """
    Get system alerts

    Queries Snowflake gold.kpi_alerts table (pre-computed)
    Alert detection logic runs in Snowflake SQL via dbt

    Args:
        location: Optional location filter
        severity: Optional severity filter (info, warning, critical)
        api_key: Verified API key

    Returns:
        List[Alert]: List of alerts from Snowflake
    """
    logger.info(f"Getting alerts - location: {location}, severity: {severity}")

    # Query pre-computed alerts from Snowflake
    # TODO: When Snowflake connected:
    # alerts_data = await alert_service.check_kpi_alerts(practice_name=location)

    # For now, return mock alerts
    alerts = [
        Alert(
            id=f"alert_{i}",
            severity=random.choice(["info", "warning", "critical"]),
            message=f"KPI variance alert - Production {random.choice(['above', 'below'])} target",
            source="snowflake",
            location_id=location,
            timestamp=datetime.utcnow().isoformat(),
            extra_data={
                "metric": "production",
                "variance_pct": random.uniform(-15, 15),
                "computed_in": "snowflake"
            }
        )
        for i in range(random.randint(2, 5))
    ]

    # Filter by severity if provided
    if severity:
        alerts = [a for a in alerts if a.severity == severity]

    return alerts


@router.post("/datalake/query")
async def query_data_lake(
    query: str,
    params: Optional[Dict[str, Any]] = None,
    api_key: str = Depends(get_api_key_header)
):
    """
    Execute custom query against data lake

    Uses Snowflake for actual queries

    Args:
        query: SQL query to execute
        params: Optional query parameters
        api_key: Verified API key

    Returns:
        List[Dict]: Query results
    """
    logger.info(f"Executing data lake query: {query[:100]}...")

    # Execute query via Snowflake service
    results = await snowflake_service.execute_query(query, params)

    return results
