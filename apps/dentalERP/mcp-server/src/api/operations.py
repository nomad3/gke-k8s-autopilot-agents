"""
Operations KPI API - Monthly Practice Operations Tracking
REUSES: analytics.py pattern for consistency

All data operations happen in Snowflake warehouse (Dynamic Tables)
Each tenant uses their configured warehouse automatically via tenant context
"""

import os
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel

from ..core.security import get_api_key_header
from ..core.tenant import TenantContext
from ..services.warehouse_router import get_tenant_warehouse
from ..services.operations_excel_parser import OperationsReportParser
from ..core.config import get_settings
from ..utils.logger import logger

router = APIRouter(prefix="/api/v1/operations", tags=["operations"])


class OperationsKPIResponse(BaseModel):
    """Monthly operations KPIs from Gold layer"""
    practice_location: str
    report_month: str
    total_production: float
    collection_rate_pct: float
    visits_total: int
    production_per_visit_overall: float
    case_acceptance_rate_pct: float
    hygiene_productivity_ratio: float


@router.post("/upload")
async def upload_operations_report(
    file: UploadFile = File(...),
    practice_code: str = Form(...),
    practice_name: str = Form(...),
    report_month: str = Form(..., description="Report month in YYYY-MM-DD format"),
    api_key: str = Depends(get_api_key_header)
):
    """
    Upload monthly operations report (Excel or CSV)

    REUSES: pdf_ingestion.py upload pattern

    Example:
        curl -X POST http://localhost:8085/api/v1/operations/upload \
          -H "Authorization: Bearer $MCP_API_KEY" \
          -H "X-Tenant-ID: silvercreek" \
          -F "file=@operations_report.xlsx" \
          -F "practice_code=LHD" \
          -F "practice_name=Laguna Hills Dental" \
          -F "report_month=2022-09-01"
    """
    tenant = TenantContext.get_tenant()
    logger.info(f"Tenant '{tenant.tenant_code}' uploading operations report: {file.filename}")

    # Get warehouse connector
    try:
        warehouse = await get_tenant_warehouse()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Determine file type
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext in ['.xlsx', '.xls']:
        file_type = 'excel'
    elif file_ext == '.csv':
        file_type = 'csv'
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_ext}. Use .xlsx, .xls, or .csv"
        )

    # Save uploaded file to temp location
    temp_dir = "/tmp"
    temp_file = os.path.join(temp_dir, f"operations_{uuid.uuid4().hex}{file_ext}")

    try:
        # Save upload
        contents = await file.read()
        with open(temp_file, 'wb') as f:
            f.write(contents)

        logger.info(f"Saved upload to: {temp_file}")

        # Parse and insert
        settings = get_settings()
        parser = OperationsReportParser(warehouse, settings)

        result = await parser.process_and_insert(
            file_path=temp_file,
            file_type=file_type,
            practice_code=practice_code,
            practice_name=practice_name,
            report_month=report_month
        )

        return {
            "status": "success",
            "message": "Operations report uploaded successfully",
            "data": result
        }

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process operations report: {str(e)}"
        )

    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.unlink(temp_file)


@router.get("/kpis/monthly", response_model=List[Dict[str, Any]])
async def get_monthly_operations_kpis(
    practice_location: Optional[str] = Query(None, description="Filter by practice location"),
    start_month: Optional[str] = Query(None, description="Start month (YYYY-MM-DD)"),
    end_month: Optional[str] = Query(None, description="End month (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    api_key: str = Depends(get_api_key_header)
):
    """
    Get monthly operations KPIs from tenant's data warehouse

    COPIED from analytics.py /production/daily pattern
    Changed: Table name and date field only

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
    logger.info(f"Tenant '{tenant.tenant_code}' querying monthly operations KPIs")

    # Build WHERE clause dynamically (SAME PATTERN as analytics.py)
    where_clauses = [f"tenant_id = '{tenant.tenant_code}'"]

    if practice_location:
        where_clauses.append(f"practice_location = '{practice_location}'")
    if start_month:
        where_clauses.append(f"report_month >= '{start_month}'")
    if end_month:
        where_clauses.append(f"report_month <= '{end_month}'")

    where_sql = f"WHERE {' AND '.join(where_clauses)}"

    # Query Gold layer (use actual column names from Gold table)
    query = f"""
        SELECT
            practice_location,
            practice_name,
            report_month,
            total_production,
            net_production,
            collections,
            collection_rate_pct,
            visits_doctor_total,
            visits_hygiene,
            visits_total,
            ppv_doctor_avg,
            ppv_hygiene,
            ppv_overall,
            case_acceptance_rate_pct,
            new_patients_total,
            hygiene_capacity_utilization_pct,
            hygiene_productivity_ratio,
            ltm_production,
            ltm_collections,
            ltm_visits,
            data_quality_score,
            uploaded_at,
            calculated_at
        FROM bronze_gold.operations_kpis_monthly
        {where_sql}
        ORDER BY report_month DESC, practice_location
        LIMIT {limit}
    """

    logger.info(f"Querying {warehouse.warehouse_type}: operations_kpis_monthly")

    try:
        results = await warehouse.execute_query(query)
        logger.info(f"Retrieved {len(results)} operations KPI records")
        return results

    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query operations KPIs: {str(e)}"
        )


@router.get("/kpis/summary")
async def get_operations_summary(
    practice_location: Optional[str] = Query(None, description="Filter by practice"),
    month: Optional[str] = Query(None, description="Specific month (YYYY-MM-DD)"),
    api_key: str = Depends(get_api_key_header)
):
    """
    Get aggregated operations summary (latest month or all practices)

    COPIED from analytics.py /production/summary pattern
    """
    try:
        warehouse = await get_tenant_warehouse()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    tenant = TenantContext.get_tenant()
    logger.info(f"Tenant '{tenant.tenant_code}' querying operations summary")

    # Build WHERE clause
    where_clauses = [f"tenant_id = '{tenant.tenant_code}'"]

    if practice_location:
        where_clauses.append(f"practice_location = '{practice_location}'")
    if month:
        where_clauses.append(f"report_month = '{month}'")
    else:
        # Default to latest month if not specified
        where_clauses.append(f"report_month = (SELECT MAX(report_month) FROM bronze_gold.operations_kpis_monthly WHERE tenant_id = '{tenant.tenant_code}')")

    where_sql = f"WHERE {' AND '.join(where_clauses)}"

    # Aggregate query
    query = f"""
        SELECT
            '{tenant.tenant_code}' AS tenant_id,
            COUNT(DISTINCT practice_location) AS practice_count,
            MAX(report_month) AS latest_month,
            SUM(total_production) AS total_production,
            SUM(collections) AS total_collections,
            AVG(collection_rate_pct) AS avg_collection_rate_pct,
            SUM(visits_total) AS total_visits,
            AVG(ppv_overall) AS avg_production_per_visit,
            AVG(case_acceptance_rate_pct) AS avg_case_acceptance_rate,
            AVG(hygiene_productivity_ratio) AS avg_hygiene_productivity,
            SUM(ltm_production) AS ltm_production,
            SUM(ltm_collections) AS ltm_collections
        FROM bronze_gold.operations_kpis_monthly
        {where_sql}
    """

    logger.info(f"Querying operations summary")

    try:
        results = await warehouse.execute_query(query)
        if results and len(results) > 0:
            return results[0]
        else:
            return {
                "message": "No operations data found",
                "tenant_id": tenant.tenant_code
            }

    except Exception as e:
        logger.error(f"Summary query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query operations summary: {str(e)}"
        )


@router.get("/kpis/by-practice")
async def get_operations_by_practice(
    start_month: Optional[str] = Query(None, description="Start month (YYYY-MM-DD)"),
    end_month: Optional[str] = Query(None, description="End month (YYYY-MM-DD)"),
    api_key: str = Depends(get_api_key_header)
):
    """
    Get operations KPIs aggregated by practice (for comparison)

    COPIED from analytics.py /production/by-practice pattern
    """
    try:
        warehouse = await get_tenant_warehouse()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    tenant = TenantContext.get_tenant()

    # Build WHERE clause
    where_clauses = [f"tenant_id = '{tenant.tenant_code}'"]

    if start_month:
        where_clauses.append(f"report_month >= '{start_month}'")
    if end_month:
        where_clauses.append(f"report_month <= '{end_month}'")

    where_sql = f"WHERE {' AND '.join(where_clauses)}"

    # Aggregate by practice
    query = f"""
        SELECT
            practice_location,
            practice_name,
            COUNT(DISTINCT report_month) AS months_tracked,
            SUM(total_production) AS total_production,
            SUM(collections) AS total_collections,
            AVG(collection_rate_pct) AS avg_collection_rate,
            SUM(visits_total) AS total_visits,
            AVG(ppv_overall) AS avg_ppv,
            AVG(case_acceptance_rate_pct) AS avg_acceptance_rate,
            AVG(hygiene_productivity_ratio) AS avg_hygiene_ratio,
            MIN(report_month) AS first_month,
            MAX(report_month) AS last_month
        FROM bronze_gold.operations_kpis_monthly
        {where_sql}
        GROUP BY practice_location, practice_name
        ORDER BY total_production DESC
    """

    try:
        results = await warehouse.execute_query(query)
        logger.info(f"Retrieved {len(results)} practice summaries")
        return results

    except Exception as e:
        logger.error(f"By-practice query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query operations by practice: {str(e)}"
        )
