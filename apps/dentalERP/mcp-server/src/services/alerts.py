"""
Alert Service - KPI Monitoring and Notification

Monitors KPIs and sends alerts via multiple channels
Integrates with forecasting for proactive alerting
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ..utils.logger import logger


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertChannel(str, Enum):
    """Alert delivery channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class AlertService:
    """
    Alert monitoring and delivery service

    Features:
    - KPI threshold monitoring (queries Snowflake)
    - Multi-channel delivery (email, Slack, webhook)
    - Alert deduplication
    - Alert history tracking
    """

    def __init__(self):
        self._alert_cache = {}

    async def check_kpi_alerts(
        self,
        practice_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Check for KPI alerts from Snowflake

        Queries gold.kpi_alerts table (pre-computed in Snowflake)

        Args:
            practice_name: Optional practice filter

        Returns:
            List of active alerts
        """
        logger.info(f"Checking KPI alerts for {practice_name or 'all practices'}")

        # Import warehouse router
        from .warehouse_router import get_warehouse_router

        warehouse_router = get_warehouse_router()

        try:
            # Query Snowflake for pre-computed alerts
            query = """
                SELECT
                    practice_name,
                    metric_name,
                    actual_value,
                    expected_value,
                    variance_pct,
                    severity,
                    alert_message,
                    month_date
                FROM gold.kpi_alerts
                WHERE 1=1
            """

            params = []
            if practice_name:
                query += " AND practice_name = %s"
                params.append(practice_name)

            query += " ORDER BY month_date DESC, severity DESC"

            # Execute query
            connector = await warehouse_router.get_connector()
            results = await connector.execute_query(query, tuple(params) if params else None)

            # Convert to list of dicts
            alerts = []
            for row in results:
                alerts.append({
                    'practice_name': row[0],
                    'metric_name': row[1],
                    'actual_value': float(row[2]) if row[2] else 0,
                    'expected_value': float(row[3]) if row[3] else 0,
                    'variance_pct': float(row[4]) if row[4] else 0,
                    'severity': row[5],
                    'alert_message': row[6],
                    'month_date': str(row[7]) if row[7] else None
                })

            logger.info(f"Found {len(alerts)} active alerts")
            return alerts

        except Exception as e:
            logger.error(f"Failed to query KPI alerts: {e}")
            return []

    async def send_alert(
        self,
        alert: Dict[str, Any],
        channels: List[AlertChannel]
    ) -> Dict[str, bool]:
        """
        Send alert to specified channels

        Args:
            alert: Alert data
            channels: List of channels to send to

        Returns:
            Dict of channel -> success status
        """
        results = {}

        for channel in channels:
            try:
                if channel == AlertChannel.EMAIL:
                    success = await self._send_email_alert(alert)
                elif channel == AlertChannel.SLACK:
                    success = await self._send_slack_alert(alert)
                elif channel == AlertChannel.WEBHOOK:
                    success = await self._send_webhook_alert(alert)
                else:
                    success = True  # IN_APP just stores in database

                results[channel.value] = success

            except Exception as e:
                logger.error(f"Failed to send alert via {channel}: {e}")
                results[channel.value] = False

        return results

    async def _send_email_alert(self, alert: Dict[str, Any]) -> bool:
        """Send alert via email (SMTP)"""
        import os
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        smtp_host = os.getenv('SMTP_HOST')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        from_email = os.getenv('SMTP_FROM', smtp_user)
        to_email = os.getenv('ALERT_EMAIL')

        if not all([smtp_host, smtp_user, smtp_password, to_email]):
            logger.warning("SMTP not fully configured, skipping email")
            return False

        try:
            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"DentalERP Alert: {alert.get('severity', 'INFO').upper()} - {alert.get('practice_name', 'Unknown')}"
            msg['From'] = from_email
            msg['To'] = to_email

            # HTML body
            html = f"""
            <html>
              <body>
                <h2>DentalERP Alert</h2>
                <p><strong>Severity:</strong> {alert.get('severity', 'info').upper()}</p>
                <p><strong>Practice:</strong> {alert.get('practice_name', 'Unknown')}</p>
                <p><strong>Date:</strong> {alert.get('month_date', 'N/A')}</p>
                <p><strong>Message:</strong> {alert.get('alert_message', 'No message')}</p>
                <hr>
                <p><strong>Details:</strong></p>
                <ul>
                  <li>Metric: {alert.get('metric_name', 'N/A')}</li>
                  <li>Actual: {alert.get('actual_value', 0)}</li>
                  <li>Expected: {alert.get('expected_value', 0)}</li>
                  <li>Variance: {alert.get('variance_pct', 0)}%</li>
                </ul>
              </body>
            </html>
            """

            msg.attach(MIMEText(html, 'html'))

            # Send via SMTP
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            logger.info(f"Email alert sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False

    async def _send_slack_alert(self, alert: Dict[str, Any]) -> bool:
        """Send alert via Slack webhook"""
        import os
        import httpx

        webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        if not webhook_url:
            logger.warning("SLACK_WEBHOOK_URL not configured, skipping")
            return False

        try:
            # Format Slack message with blocks
            severity_emoji = {
                'info': 'ℹ️',
                'warning': '⚠️',
                'critical': '🚨'
            }

            severity = alert.get('severity', 'info')
            emoji = severity_emoji.get(severity, '📊')

            message = {
                "text": f"{emoji} {alert.get('alert_message', 'No message')}",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{emoji} DentalERP Alert"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Practice:* {alert.get('practice_name', 'Unknown')}"},
                            {"type": "mrkdwn", "text": f"*Severity:* {severity.upper()}"},
                            {"type": "mrkdwn", "text": f"*Metric:* {alert.get('metric_name', 'N/A')}"},
                            {"type": "mrkdwn", "text": f"*Variance:* {alert.get('variance_pct', 0)}%"}
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": alert.get('alert_message', 'No message')
                        }
                    }
                ]
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(webhook_url, json=message)

                if response.status_code == 200:
                    logger.info(f"Slack alert sent successfully")
                    return True
                else:
                    logger.error(f"Slack webhook returned status {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False

    async def _send_webhook_alert(self, alert: Dict[str, Any]) -> bool:
        """Send alert via custom webhook"""
        # TODO: Implement webhook POST
        logger.info(f"Sending webhook alert: {alert.get('message')}")
        return True

    def should_deduplicate(
        self,
        alert: Dict[str, Any],
        window_hours: int = 24
    ) -> bool:
        """
        Check if alert should be deduplicated

        Prevents alert spam by checking if similar alert
        was sent recently

        Args:
            alert: Alert data
            window_hours: Deduplication window

        Returns:
            True if should skip (duplicate), False if should send
        """
        # Generate cache key
        key = f"{alert.get('practice_name')}:{alert.get('metric')}:{alert.get('severity')}"

        if key in self._alert_cache:
            last_sent = self._alert_cache[key]
            time_diff = (datetime.utcnow() - last_sent).total_seconds() / 3600

            if time_diff < window_hours:
                logger.debug(f"Skipping duplicate alert: {key}")
                return True

        # Update cache
        self._alert_cache[key] = datetime.utcnow()
        return False


# Singleton instance
_alert_service: Optional[AlertService] = None


def get_alert_service() -> AlertService:
    """Get singleton alert service"""
    global _alert_service
    if _alert_service is None:
        _alert_service = AlertService()
    return _alert_service
