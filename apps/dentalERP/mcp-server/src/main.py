"""
MCP Server - Mapping & Control Plane
Central integration and orchestration service for DentalERP
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .api import data, health, integrations, mappings, warehouse, pdf_ingestion, dbt_runner, analytics, tenants, products, netsuite_sync, financial, bulk_load, operations, analytics_unified, netsuite_upload
from .core.config import settings
from .core.database import close_db, init_db
from .middleware.tenant_identifier import TenantIdentifierMiddleware
from .services.product_registry import get_product_registry
from .scheduler import jobs
from .utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting MCP Server...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Continue anyway for development

    # Initialize product registry
    try:
        get_product_registry()
        logger.info("Product registry initialized successfully")
    except Exception as e:
        logger.error(f"Product registry initialization failed: {e}")

    # Initialize scheduler
    scheduler = AsyncIOScheduler()

    # Job 1: Daily NetSuite full sync at 2am
    scheduler.add_job(
        jobs.sync_netsuite_full,
        CronTrigger(hour=2, minute=0),
        id='netsuite_daily_full_sync',
        name='NetSuite Daily Full Sync',
        replace_existing=True
    )

    # Job 2: Incremental NetSuite sync every 4 hours
    scheduler.add_job(
        jobs.sync_netsuite_incremental,
        'interval',
        hours=4,
        id='netsuite_incremental_sync',
        name='NetSuite Incremental Sync',
        replace_existing=True
    )

    # Job 3: Hourly alert check
    scheduler.add_job(
        jobs.check_and_send_alerts,
        'interval',
        hours=1,
        id='hourly_alert_check',
        name='Hourly Alert Check',
        replace_existing=True
    )

    # Job 4: Weekly insights email (Monday 9am)
    scheduler.add_job(
        jobs.send_weekly_insights,
        CronTrigger(day_of_week='mon', hour=9, minute=0),
        id='weekly_insights_email',
        name='Weekly Insights Email',
        replace_existing=True
    )

    scheduler.start()
    logger.info("✅ Scheduler started: 4 jobs registered")
    logger.info("  - Daily NetSuite full sync: 2am")
    logger.info("  - Incremental NetSuite sync: Every 4 hours")
    logger.info("  - Hourly alert check")
    logger.info("  - Weekly insights: Monday 9am")

    yield

    # Shutdown
    logger.info("Shutting down scheduler...")
    scheduler.shutdown(wait=True)
    logger.info("Scheduler stopped")
    logger.info("Shutting down MCP Server...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title="MCP Server",
    description="Mapping & Control Plane for DentalERP Integrations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tenant identification middleware
# NOTE: Add this AFTER CORS but BEFORE route handlers
app.add_middleware(TenantIdentifierMiddleware)

# Include routers
app.include_router(health.router)
app.include_router(tenants.router)  # Tenant management
app.include_router(products.router)  # Product management
app.include_router(products.dental_router)  # DentalERP product routes
app.include_router(products.agent_router)  # AgentProvision product routes
app.include_router(mappings.router)
app.include_router(integrations.router)
app.include_router(data.router)
app.include_router(warehouse.router)
app.include_router(pdf_ingestion.router)
app.include_router(dbt_runner.router)
app.include_router(analytics.router)
app.include_router(financial.router)
app.include_router(netsuite_sync.router)
app.include_router(bulk_load.router)
app.include_router(operations.router)  # Operations KPI tracking
app.include_router(analytics_unified.router)  # Unified analytics
app.include_router(netsuite_upload.router)  # NetSuite CSV upload


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "MCP Server",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.debug else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
