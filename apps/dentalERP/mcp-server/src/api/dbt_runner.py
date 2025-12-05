"""
dbt Runner API Endpoints
Trigger dbt transformations in Snowflake
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
from loguru import logger

from ..services.dbt_runner import get_dbt_runner, DBTRunner
from ..core.config import get_settings
from ..core.security import verify_api_key

router = APIRouter(prefix="/api/v1/dbt", tags=["dbt Transformations"])
settings = get_settings()


def get_dbt_service() -> DBTRunner:
    """Dependency to get dbt runner service"""
    return get_dbt_runner(settings)


@router.post("/run")
async def run_dbt_transformations(
    models: Optional[str] = None,
    select: Optional[str] = None,
    full_refresh: bool = False,
    api_key: str = Depends(verify_api_key),
    dbt_service: DBTRunner = Depends(get_dbt_service)
):
    """
    Run dbt transformations

    - **models**: Comma-separated list of models to run (e.g., "stg_pms_day_sheets,daily_production_metrics")
    - **select**: dbt select syntax (e.g., "tag:daily", "silver+", "stg_pms_day_sheets+")
    - **full_refresh**: Force full refresh of incremental models

    Examples:
    - Run all models: POST /api/v1/dbt/run
    - Run specific model: POST /api/v1/dbt/run?models=stg_pms_day_sheets
    - Run with selector: POST /api/v1/dbt/run?select=tag:daily
    - Full refresh: POST /api/v1/dbt/run?full_refresh=true
    """
    logger.info(f"Received dbt run request: models={models}, select={select}, full_refresh={full_refresh}")

    try:
        model_list = models.split(",") if models else None

        result = await dbt_service.run_dbt_models(
            models=model_list,
            select=select,
            full_refresh=full_refresh
        )

        status_code = 200 if result["success"] else 500

        return JSONResponse(
            status_code=status_code,
            content={
                "status": "success" if result["success"] else "error",
                **result
            }
        )

    except Exception as e:
        logger.error(f"Error running dbt: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run/pdf-pipeline")
async def run_pdf_ingestion_pipeline(
    practice_location: Optional[str] = None,
    background: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    api_key: str = Depends(verify_api_key),
    dbt_service: DBTRunner = Depends(get_dbt_service)
):
    """
    Run the complete PDF ingestion dbt pipeline
    Bronze → Silver → Gold

    - **practice_location**: Optional practice location filter
    - **background**: Run in background (return immediately)

    This endpoint runs:
    1. Silver: stg_pms_day_sheets (parse VARIANT JSON)
    2. Gold: daily_production_metrics (aggregate KPIs)
    """
    logger.info(f"Received PDF pipeline run request: practice_location={practice_location}, background={background}")

    try:
        if background:
            # Run in background
            background_tasks.add_task(
                dbt_service.run_pdf_ingestion_pipeline,
                practice_location=practice_location
            )

            return JSONResponse(
                status_code=202,
                content={
                    "status": "accepted",
                    "message": "dbt pipeline started in background",
                    "practice_location": practice_location
                }
            )
        else:
            # Run synchronously
            result = await dbt_service.run_pdf_ingestion_pipeline(
                practice_location=practice_location
            )

            status_code = 200 if result["success"] else 500

            return JSONResponse(
                status_code=status_code,
                content={
                    "status": "success" if result["success"] else "error",
                    **result
                }
            )

    except Exception as e:
        logger.error(f"Error running PDF pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_dbt_status(
    api_key: str = Depends(verify_api_key),
    dbt_service: DBTRunner = Depends(get_dbt_service)
):
    """
    Get dbt connection status and configuration

    Tests connection to Snowflake via dbt
    """
    try:
        result = await dbt_service.test_dbt_connection()

        status_code = 200 if result["success"] else 500

        return JSONResponse(
            status_code=status_code,
            content={
                "status": "success" if result["success"] else "error",
                "dbt_connected": result["success"],
                **result
            }
        )

    except Exception as e:
        logger.error(f"Error checking dbt status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
