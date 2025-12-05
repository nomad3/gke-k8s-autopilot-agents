"""
Unified Analytics API - Single source for all practice metrics
Queries gold.practice_analytics_unified (Operations + Financial + PMS + ADP)
"""

from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..core.security import get_api_key_header
from ..core.tenant import TenantContext
from ..services.warehouse_router import get_tenant_warehouse
from ..utils.logger import logger

router = APIRouter(prefix="/api/v1/analytics/unified", tags=["analytics-unified"])


@router.get("/monthly")
async def get_unified_monthly_analytics(
    practice_id: Optional[str] = Query(None, description="Filter by practice ID"),
    start_month: Optional[str] = Query(None, description="Start month (YYYY-MM-DD)"),
    end_month: Optional[str] = Query(None, description="End month (YYYY-MM-DD)"),
    category: Optional[str] = Query('all', description="all|operations|financial|production"),
    limit: int = Query(100, ge=1, le=1000),
    api_key: str = Depends(get_api_key_header)
):
    """
    Get unified monthly analytics from all data sources

    Returns all metrics from Operations Report + NetSuite + PMS
    """
    warehouse = await get_tenant_warehouse()
    tenant = TenantContext.get_tenant()

    # Build WHERE clause
    where_clauses = [f"tenant_id = '{tenant.tenant_code}'"]
    if practice_id:
        where_clauses.append(f"practice_id = '{practice_id}'")
    if start_month:
        where_clauses.append(f"report_month >= '{start_month}'")
    if end_month:
        where_clauses.append(f"report_month <= '{end_month}'")

    where_sql = f"WHERE {' AND '.join(where_clauses)}"

    # Select columns based on category
    if category == 'operations':
        select_cols = """
            practice_id, practice_display_name, report_month,
            total_production, collections, collection_rate_pct,
            visits_total, ppv_overall, case_acceptance_rate_pct,
            hygiene_productivity_ratio, new_patients_total,
            ltm_production, ltm_collections
        """
    elif category == 'financial':
        select_cols = """
            practice_id, practice_display_name, report_month,
            netsuite_revenue, netsuite_expenses, netsuite_net_income,
            netsuite_profit_margin, netsuite_revenue_growth
        """
    elif category == 'production':
        select_cols = """
            practice_id, practice_display_name, report_month,
            pms_production, pms_collections, pms_visits, pms_ppv, pms_quality
        """
    else:  # 'all'
        select_cols = "*"

    query = f"""
        SELECT {select_cols}
        FROM gold.practice_analytics_unified
        {where_sql}
        ORDER BY report_month DESC, practice_id
        LIMIT {limit}
    """

    logger.info(f"Unified analytics query: {category}, practice: {practice_id}")

    try:
        results = await warehouse.execute_query(query)
        return results
    except Exception as e:
        logger.error(f"Unified analytics query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query unified analytics: {str(e)}"
        )


@router.get("/summary")
async def get_unified_summary(
    practice_id: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    api_key: str = Depends(get_api_key_header)
):
    """Get aggregated summary from unified view"""

    warehouse = await get_tenant_warehouse()
    tenant = TenantContext.get_tenant()

    where_clauses = [f"tenant_id = '{tenant.tenant_code}'"]
    if practice_id:
        where_clauses.append(f"practice_id = '{practice_id}'")
    if month:
        where_clauses.append(f"report_month = '{month}'")
    else:
        where_clauses.append(f"report_month = (SELECT MAX(report_month) FROM gold.practice_analytics_unified WHERE tenant_id = '{tenant.tenant_code}')")

    where_sql = f"WHERE {' AND '.join(where_clauses)}"

    query = f"""
        SELECT
            COUNT(DISTINCT practice_id) AS practice_count,
            MAX(report_month) AS latest_month,
            SUM(total_production) AS total_production,
            SUM(collections) AS total_collections,
            AVG(collection_rate_pct) AS avg_collection_rate,
            SUM(visits_total) AS total_visits,
            AVG(ppv_overall) AS avg_ppv,
            AVG(case_acceptance_rate_pct) AS avg_case_acceptance,
            AVG(hygiene_productivity_ratio) AS avg_hygiene_ratio,
            SUM(netsuite_revenue) AS total_revenue,
            SUM(netsuite_expenses) AS total_expenses,
            SUM(netsuite_net_income) AS total_net_income,
            SUM(ltm_production) AS ltm_production
        FROM gold.practice_analytics_unified
        {where_sql}
    """

    try:
        results = await warehouse.execute_query(query)
        return results[0] if results else {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-practice")
async def get_unified_by_practice(
    start_month: Optional[str] = Query(None),
    end_month: Optional[str] = Query(None),
    api_key: str = Depends(get_api_key_header)
):
    """Get metrics aggregated by practice"""

    warehouse = await get_tenant_warehouse()
    tenant = TenantContext.get_tenant()

    where_clauses = [f"tenant_id = '{tenant.tenant_code}'"]
    if start_month:
        where_clauses.append(f"report_month >= '{start_month}'")
    if end_month:
        where_clauses.append(f"report_month <= '{end_month}'")

    where_sql = f"WHERE {' AND '.join(where_clauses)}"

    query = f"""
        SELECT
            practice_id,
            practice_display_name,
            COUNT(DISTINCT report_month) AS months_tracked,
            SUM(total_production) AS total_production,
            SUM(collections) AS total_collections,
            AVG(collection_rate_pct) AS avg_collection_rate,
            SUM(visits_total) AS total_visits,
            AVG(ppv_overall) AS avg_ppv,
            AVG(case_acceptance_rate_pct) AS avg_case_acceptance,
            AVG(hygiene_productivity_ratio) AS avg_hygiene_ratio,
            SUM(netsuite_revenue) AS total_revenue,
            SUM(netsuite_net_income) AS total_net_income,
            MIN(report_month) AS first_month,
            MAX(report_month) AS last_month
        FROM gold.practice_analytics_unified
        {where_sql}
        GROUP BY practice_id, practice_display_name
        ORDER BY total_production DESC
    """

    try:
        results = await warehouse.execute_query(query)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
