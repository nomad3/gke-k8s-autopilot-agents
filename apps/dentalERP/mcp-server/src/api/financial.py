"""
Financial Analytics API
Real NetSuite financial data endpoints
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional

from ..core.security import get_api_key_header
from ..services.warehouse_router import get_tenant_warehouse
from ..core.tenant import TenantContext
from ..utils.logger import logger

router = APIRouter(prefix="/api/v1/analytics/financial", tags=["financial"])


@router.get("/summary")
async def get_financial_summary(
    practice_name: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    api_key: str = Depends(get_api_key_header)
):
    """
    Get financial summary by practice

    Operations Report Metrics:
    - Total Revenue
    - Total Expenses
    - Net Income
    - Gross Margin %
    - MoM Growth %

    Args:
        practice_name: Optional practice filter
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        Financial metrics per practice per month
    """
    try:
        warehouse = await get_tenant_warehouse()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    tenant = TenantContext.get_tenant()
    logger.info(f"Tenant '{tenant.tenant_code}' querying financial summary")

    # Build query
    query = """
        SELECT
            practice_name,
            subsidiary_id,
            month_date,
            total_revenue,
            total_expenses,
            net_income,
            profit_margin_pct,
            mom_growth_pct,
            prev_month_revenue,
            calculated_at
        FROM gold.monthly_production_kpis
        WHERE 1=1
    """

    params = {}

    if practice_name:
        query += " AND practice_name = %(practice_name)s"
        params['practice_name'] = practice_name

    if start_date:
        query += " AND month_date >= %(start_date)s"
        params['start_date'] = start_date
    else:
        # Default to last 3 months
        query += " AND month_date >= DATEADD(MONTH, -3, CURRENT_DATE())"

    if end_date:
        query += " AND month_date <= %(end_date)s"
        params['end_date'] = end_date

    query += " ORDER BY month_date DESC, practice_name"

    logger.info(f"Querying {warehouse.warehouse_type} financial summary: {query[:200]}...")

    try:
        # Execute query
        result = await warehouse.execute_query(query, parameters=params)

        return {
            "data": result,
            "count": len(result),
            "filters": {
                "practice_name": practice_name,
                "start_date": start_date,
                "end_date": end_date
            }
        }

    except Exception as e:
        logger.error(f"Financial summary failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-practice")
async def get_by_practice_comparison(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    api_key: str = Depends(get_api_key_header)
):
    """
    Compare all practices side-by-side

    Returns:
        Latest month financial metrics for all practices
    """
    try:
        warehouse = await get_tenant_warehouse()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    tenant = TenantContext.get_tenant()
    logger.info(f"Tenant '{tenant.tenant_code}' querying practice comparison")

    query = """
        WITH latest_month AS (
            SELECT MAX(month_date) as max_month
            FROM gold.monthly_production_kpis
        )
        SELECT
            k.practice_name,
            k.total_revenue,
            k.total_expenses,
            k.net_income,
            k.profit_margin_pct,
            k.mom_growth_pct
        FROM gold.monthly_production_kpis k
        CROSS JOIN latest_month l
        WHERE k.month_date = l.max_month
        ORDER BY k.total_revenue DESC
    """

    logger.info(f"Querying {warehouse.warehouse_type} practice comparison: {query[:200]}...")

    try:
        result = await warehouse.execute_query(query)

        return {
            "practices": result,
            "count": len(result),
            "period": "latest_month"
        }

    except Exception as e:
        logger.error(f"Practice comparison failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
