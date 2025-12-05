"""
Scheduled background jobs for data synchronization and alerting
"""

from ..utils.logger import logger
from ..services.netsuite_sync_orchestrator import NetSuiteSyncOrchestrator
from ..services.alerts import get_alert_service, AlertChannel
from ..services.forecasting import get_forecasting_service


async def sync_netsuite_full():
    """
    Daily full NetSuite sync (scheduled 2am)

    AUTO-FETCHES ALL RECORDS from NetSuite without manual limits.
    System automatically:
    - Batches at 3,000 records per request (NetSuite max)
    - Continues until NetSuite returns no more data
    - Handles 75K+ records across all subsidiaries
    - Prevents duplicates with MERGE
    """
    logger.info("🚀 Starting scheduled NetSuite FULL sync (auto-fetch ALL records)")
    try:
        orchestrator = NetSuiteSyncOrchestrator()
        # full_sync=True means ignore last_sync_time, fetch everything
        result = await orchestrator.sync_all_tenants(full_sync=True)
        logger.info(f"✅ Scheduled full sync completed: {result}")
    except Exception as e:
        logger.error(f"❌ Scheduled full sync failed: {e}", exc_info=True)


async def sync_netsuite_incremental():
    """
    Incremental NetSuite sync (every 4 hours)

    Fetches only NEW/MODIFIED records since last sync.
    Uses last_sync_time from database to determine from_date.
    Still auto-batches if needed.
    """
    logger.info("🔄 Starting scheduled NetSuite incremental sync (new/modified records only)")
    try:
        orchestrator = NetSuiteSyncOrchestrator()
        # full_sync=False means use last_sync_time for incremental
        result = await orchestrator.sync_all_tenants(full_sync=False)
        logger.info(f"✅ Scheduled incremental sync completed: {result}")
    except Exception as e:
        logger.error(f"❌ Scheduled incremental sync failed: {e}", exc_info=True)


async def check_and_send_alerts():
    """Check for KPI alerts and send notifications (hourly)"""
    logger.info("Starting scheduled alert check")
    try:
        alert_service = get_alert_service()
        alerts = await alert_service.check_kpi_alerts()

        for alert in alerts:
            # Check deduplication
            if not alert_service.should_deduplicate(alert, window_hours=24):
                # Send to Slack and Email
                await alert_service.send_alert(
                    alert,
                    channels=[AlertChannel.SLACK, AlertChannel.EMAIL]
                )

        logger.info(f"Alert check completed: {len(alerts)} alerts processed")

    except Exception as e:
        logger.error(f"Alert check failed: {e}", exc_info=True)


async def send_weekly_insights():
    """Generate and email weekly AI insights (Monday 9am)"""
    logger.info("Starting weekly insights generation")
    try:
        # TODO: Implement generate_insights() in ForecastingService
        # For now, use generate_alerts() to demonstrate functionality
        forecasting = get_forecasting_service()
        insights = await forecasting.generate_alerts(practice_name="All Practices")

        # Format insights for email
        insight_text = "\n".join([
            f"- {alert.get('alert_message', 'N/A')}"
            for alert in insights
        ])

        # Send via email
        alert_service = get_alert_service()
        await alert_service.send_alert(
            alert={
                "severity": "info",
                "alert_message": f"Weekly Insights:\n\n{insight_text}",
                "practice_name": "All Practices"
            },
            channels=[AlertChannel.EMAIL]
        )

        logger.info("Weekly insights sent successfully")

    except Exception as e:
        logger.error(f"Weekly insights failed: {e}", exc_info=True)
