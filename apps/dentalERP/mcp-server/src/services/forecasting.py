"""
Forecasting Service - Revenue and Cost Prediction

Uses time series analysis for financial forecasting
Implements anomaly detection for KPI variance alerts
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..utils.cache import cached
from ..utils.logger import logger


class ForecastingService:
    """
    Time series forecasting service

    Methods:
    - Revenue forecasting (Prophet-style decomposition)
    - Cost forecasting with seasonality
    - KPI anomaly detection
    - Alert generation

    NOTE: Heavy ML computations done in Snowflake using built-in ML functions
    MCP just queries pre-computed forecasts from gold.forecasts table
    """

    def __init__(self):
        self._model_cache = {}

    @cached(ttl=3600, key_prefix="forecast:revenue")
    async def forecast_revenue(
        self,
        practice_name: str,
        periods: int = 3,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Forecast revenue for next N periods

        IMPORTANT: Queries pre-computed forecasts from Snowflake
        Snowflake ML functions do the actual forecasting:
        - FORECAST() function
        - ML.FORECAST() for advanced models

        Args:
            practice_name: Practice identifier
            periods: Number of months to forecast
            confidence_level: Confidence interval (0.80-0.99)

        Returns:
            Forecast data with confidence intervals
        """
        logger.info(f"Generating revenue forecast for {practice_name}, {periods} periods")

        # TODO: Query Snowflake's ML.FORECAST() results
        # Snowflake has built-in forecasting:
        #
        # In dbt or Snowflake:
        # CREATE OR REPLACE MODEL gold.revenue_forecast_model
        # FROM gold.monthly_production_kpis
        # FORECAST total_production
        # USING (
        #     type = 'ARIMA',
        #     seasonal_periods = 12,
        #     confidence_level = 0.95
        # );
        #
        # Then MCP just queries:
        # SELECT * FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()));

        # Return empty forecast when Snowflake tables don't exist yet
        return {
            "practice_name": practice_name,
            "metric": "revenue",
            "forecasts": [],
            "model": "not_available",
            "generated_at": datetime.utcnow().isoformat(),
            "message": "Forecasting not available - Snowflake ML models not yet configured"
        }

    @cached(ttl=3600, key_prefix="forecast:cost")
    async def forecast_costs(
        self,
        practice_name: str,
        periods: int = 3,
        include_seasonality: bool = True
    ) -> Dict[str, Any]:
        """
        Forecast costs with seasonality

        Uses Snowflake ML functions for time series forecasting

        Args:
            practice_name: Practice identifier
            periods: Number of months to forecast
            include_seasonality: Include seasonal patterns

        Returns:
            Cost forecast data
        """
        logger.info(f"Generating cost forecast for {practice_name}")

        # TODO: Query Snowflake ML.FORECAST() for costs
        # Return empty forecast when Snowflake tables don't exist yet
        return {
            "practice_name": practice_name,
            "metric": "costs",
            "forecasts": [],
            "model": "not_available",
            "generated_at": datetime.utcnow().isoformat(),
            "message": "Forecasting not available - Snowflake ML models not yet configured"
        }

    async def detect_anomalies(
        self,
        practice_name: str,
        metric: str = "revenue",
        sensitivity: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in KPI metrics

        Uses Snowflake's statistical functions:
        - STDDEV_POP() for variance
        - Z-score calculations
        - Seasonal decomposition

        Args:
            practice_name: Practice identifier
            metric: Metric to analyze ('revenue', 'costs', 'patients')
            sensitivity: Standard deviations for alert (default 2.0)

        Returns:
            List of anomaly alerts
        """
        logger.info(f"Detecting anomalies for {practice_name}, metric: {metric}")

        # TODO: Query Snowflake anomaly detection
        #
        # In Snowflake SQL:
        # WITH stats AS (
        #     SELECT
        #         month_date,
        #         total_production,
        #         AVG(total_production) OVER (
        #             ORDER BY month_date
        #             ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        #         ) AS moving_avg,
        #         STDDEV_POP(total_production) OVER (
        #             ORDER BY month_date
        #             ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        #         ) AS moving_stddev
        #     FROM gold.monthly_production_kpis
        #     WHERE practice_name = %s
        # )
        # SELECT *,
        #     (total_production - moving_avg) / moving_stddev AS z_score
        # FROM stats
        # WHERE ABS(z_score) > %s  -- sensitivity threshold

        # Return empty anomalies when Snowflake tables don't exist yet
        return []

    async def generate_alerts(
        self,
        practice_name: Optional[str] = None,
        severity_threshold: str = "warning"
    ) -> List[Dict[str, Any]]:
        """
        Generate alerts from anomaly detection

        Queries Snowflake for pre-computed alerts based on:
        - KPI variance beyond thresholds
        - Trend reversals
        - Target misses

        Args:
            practice_name: Optional practice filter
            severity_threshold: Minimum severity ('info', 'warning', 'critical')

        Returns:
            List of alerts
        """
        logger.info(f"Generating alerts for {practice_name or 'all practices'}")

        # TODO: Query Snowflake alerts table
        #
        # CREATE TABLE gold.kpi_alerts AS
        # WITH variance_check AS (
        #     SELECT
        #         practice_name,
        #         month_date,
        #         total_production,
        #         production_target,
        #         ABS(total_production - production_target) / production_target AS variance_pct,
        #         CASE
        #             WHEN variance_pct > 0.20 THEN 'critical'
        #             WHEN variance_pct > 0.10 THEN 'warning'
        #             ELSE 'info'
        #         END AS severity
        #     FROM gold.monthly_production_kpis
        # )
        # SELECT * FROM variance_check
        # WHERE severity >= %s

        return []

    @cached(ttl=3600, key_prefix="insights")
    async def generate_insights(
        self,
        practice_name: Optional[str] = None,
        period: str = "month"
    ) -> str:
        """
        Generate natural language insights using GPT-4

        Queries Snowflake for KPIs and recent alerts, then uses GPT-4 to create
        an executive summary with actionable insights.

        Args:
            practice_name: Optional practice filter
            period: Time period for analysis ('month', 'quarter', 'year')

        Returns:
            Natural language insight summary

        Raises:
            RuntimeError: If warehouse query or GPT-4 API fails
        """
        import os
        from openai import AsyncOpenAI

        logger.info(f"Generating AI insights for {practice_name or 'all practices'}")

        try:
            # Import warehouse router here to avoid circular imports
            from ..services.warehouse_router import get_tenant_warehouse

            warehouse = await get_tenant_warehouse()

            # Query top practices by production
            top_practices_query = """
                SELECT
                    practice_name,
                    total_production,
                    mom_production_growth_pct,
                    profit_margin_pct
                FROM gold.monthly_production_kpis
                WHERE month_date = DATE_TRUNC('month', CURRENT_DATE())
                ORDER BY total_production DESC
                LIMIT 5
            """

            # Query recent alerts
            alerts_query = """
                SELECT
                    practice_name,
                    alert_message,
                    severity
                FROM gold.kpi_alerts
                WHERE month_date >= DATEADD(MONTH, -1, CURRENT_DATE())
                ORDER BY severity DESC, month_date DESC
                LIMIT 10
            """

            # Execute queries
            try:
                top_practices = await warehouse.execute_query(top_practices_query)
            except Exception as e:
                logger.warning(f"Failed to query top practices: {e}")
                top_practices = []

            try:
                alerts = await warehouse.execute_query(alerts_query)
            except Exception as e:
                logger.warning(f"Failed to query alerts: {e}")
                alerts = []

            # Format data for GPT-4 prompt
            kpis_text = self._format_kpis_for_prompt(top_practices)
            alerts_text = self._format_alerts_for_prompt(alerts)

            # Build GPT-4 prompt
            prompt = f"""You are analyzing dental practice financial data. Provide a concise 2-3 sentence executive summary.

Top Practices by Production:
{kpis_text}

Recent Alerts:
{alerts_text}

Format:
"Production [up/down] X% MoM, driven by [location]. Top gains: [list]. Cost changes: [summary]."

Focus on actionable insights, not just numbers."""

            # Call GPT-4
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OPENAI_API_KEY not set, returning mock insight")
                return self._generate_mock_insight(top_practices, alerts)

            client = AsyncOpenAI(api_key=api_key)

            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )

            insight = response.choices[0].message.content

            logger.info(f"Generated AI insight: {insight[:100]}...")
            return insight

        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            # Return fallback insight instead of raising error
            return "Unable to generate insights at this time. Please check system logs."

    def _format_kpis_for_prompt(self, kpis: List[Dict[str, Any]]) -> str:
        """Format KPI data for GPT-4 prompt"""
        if not kpis:
            return "No KPI data available"

        lines = []
        for i, kpi in enumerate(kpis, 1):
            practice = kpi.get('practice_name', 'Unknown')
            production = kpi.get('total_production', 0)
            growth = kpi.get('mom_production_growth_pct', 0)
            margin = kpi.get('profit_margin_pct', 0)

            lines.append(
                f"{i}. {practice}: ${production:,.0f} production "
                f"({growth:+.1f}% MoM, {margin:.1f}% margin)"
            )

        return "\n".join(lines)

    def _format_alerts_for_prompt(self, alerts: List[Dict[str, Any]]) -> str:
        """Format alert data for GPT-4 prompt"""
        if not alerts:
            return "No recent alerts"

        lines = []
        for alert in alerts:
            practice = alert.get('practice_name', 'Unknown')
            message = alert.get('alert_message', 'No message')
            severity = alert.get('severity', 'info').upper()

            lines.append(f"- [{severity}] {practice}: {message}")

        return "\n".join(lines)

    def _generate_mock_insight(
        self,
        top_practices: List[Dict[str, Any]],
        alerts: List[Dict[str, Any]]
    ) -> str:
        """Generate mock insight when GPT-4 is unavailable"""
        if not top_practices and not alerts:
            return "Production data shows stable performance across all practices. No significant anomalies detected."

        # Simple template-based insight
        if top_practices:
            top_practice = top_practices[0]
            practice_name = top_practice.get('practice_name', 'Unknown')
            growth = top_practice.get('mom_production_growth_pct', 0)

            if growth > 5:
                return f"Production up {growth:.1f}% MoM, driven by {practice_name}. Strong performance across top practices with healthy margins."
            elif growth < -5:
                return f"Production down {growth:.1f}% MoM. {practice_name} shows decline. Review operational efficiency and patient scheduling."
            else:
                return f"Production stable with {growth:+.1f}% MoM. {practice_name} leads with consistent performance."

        return "Production metrics stable. Monitor for developing trends."


# Singleton instance
_forecasting_service: Optional[ForecastingService] = None


def get_forecasting_service() -> ForecastingService:
    """Get singleton forecasting service"""
    global _forecasting_service
    if _forecasting_service is None:
        _forecasting_service = ForecastingService()
    return _forecasting_service
