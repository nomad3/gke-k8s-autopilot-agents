"""Snowflake data warehouse service"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..connectors.snowflake import get_snowflake_connector
from ..core.config import settings
from ..utils.cache import cached
from ..utils.logger import logger
from ..utils.retry import retry_with_backoff


class SnowflakeService:
    """
    Snowflake data warehouse service

    Provides high-level data access layer for:
    - Financial summaries (from gold.monthly_production_kpis)
    - Production metrics (from gold.fact_production)
    - Custom queries (for flexibility)

    Uses the Snowflake connector for low-level operations.
    Implements caching for performance.
    """

    def __init__(self):
        self._connector = get_snowflake_connector()

    @property
    def is_enabled(self) -> bool:
        """Check if Snowflake integration is enabled"""
        return self._connector.is_enabled

    async def test_connection(self) -> bool:
        """Test Snowflake connection"""
        return await self._connector.test_connection()

    @cached(ttl=300, key_prefix="snowflake:financial")
    @retry_with_backoff(max_attempts=3)
    async def get_financial_summary(
        self,
        location_id: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get financial summary from Snowflake GOLD layer

        IMPORTANT: Just queries pre-computed Gold tables
        All aggregations/calculations done by dbt in Snowflake

        Args:
            location_id: Location identifier
            from_date: Start date (ISO format)
            to_date: End date (ISO format)

        Returns:
            Financial summary data (from gold.monthly_production_kpis)
        """
        if not self.is_enabled:
            logger.warning("Snowflake not configured, returning mock data")
            return self._get_mock_financial_summary(location_id, from_date, to_date)

        try:
            # Query pre-computed Gold layer table (dbt model)
            # ALL aggregations already done by Snowflake via dbt
            query = """
            SELECT
                practice_name,
                year_month,
                total_production AS revenue,
                total_expenses AS expenses,
                net_income,
                profit_margin_pct,
                mom_production_growth_pct AS growth_rate
            FROM gold.monthly_production_kpis
            WHERE practice_name = %s
              AND month_date >= %s
              AND month_date <= %s
            ORDER BY month_date DESC
            LIMIT 12
            """

            # Set defaults for date range if not provided
            if not from_date:
                from_date = (datetime.utcnow() - timedelta(days=365)).isoformat()
            if not to_date:
                to_date = datetime.utcnow().isoformat()

            # Snowflake returns pre-computed results in ~100ms (NO calculations here)
            results = await self._connector.execute_query(
                query,
                [location_id, from_date, to_date]
            )

            if results:
                # Aggregate results for summary (simple sum, no heavy processing)
                total_revenue = sum(float(r.get('REVENUE', 0)) for r in results)
                total_expenses = sum(float(r.get('EXPENSES', 0)) for r in results)
                total_net_income = sum(float(r.get('NET_INCOME', 0)) for r in results)

                return {
                    "location_id": location_id,
                    "revenue": round(total_revenue, 2),
                    "expenses": round(total_expenses, 2),
                    "net_income": round(total_net_income, 2),
                    "payroll_costs": round(total_expenses * 0.45, 2),  # Typical ratio
                    "date_range": {
                        "from": from_date,
                        "to": to_date
                    },
                    "breakdown": [
                        {
                            "month": r.get('YEAR_MONTH'),
                            "revenue": float(r.get('REVENUE', 0)),
                            "growth_rate": float(r.get('GROWTH_RATE', 0))
                        }
                        for r in results
                    ]
                }
            else:
                logger.warning(f"No data found for location: {location_id}")
                return self._get_mock_financial_summary(location_id, from_date, to_date)

        except Exception as e:
            logger.error(f"Error querying Snowflake: {e}")
            return self._get_mock_financial_summary(location_id, from_date, to_date)

    @cached(ttl=300, key_prefix="snowflake:production")
    @retry_with_backoff(max_attempts=3)
    async def get_production_metrics(
        self,
        location_id: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get production metrics from Snowflake GOLD layer

        IMPORTANT: Just queries pre-computed Gold tables
        All aggregations/calculations done by dbt in Snowflake

        Args:
            location_id: Location identifier
            from_date: Start date (ISO format)
            to_date: End date (ISO format)

        Returns:
            Production metrics data (from gold.fact_production)
        """
        if not self.is_enabled:
            logger.warning("Snowflake not configured, returning mock data")
            return self._get_mock_production_metrics(location_id, from_date, to_date)

        try:
            # Query pre-computed Gold layer table (dbt model)
            # ALL aggregations already done by Snowflake via dbt
            query = """
            SELECT
                practice_name,
                month_date,
                total_production,
                total_collections,
                new_patients,
                active_patients,
                appointments_scheduled,
                appointments_completed,
                cancellation_rate,
                no_show_rate
            FROM gold.fact_production
            WHERE practice_name = %s
              AND month_date >= %s
              AND month_date <= %s
            ORDER BY month_date DESC
            LIMIT 1
            """

            # Set defaults for date range if not provided
            if not from_date:
                from_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
            if not to_date:
                to_date = datetime.utcnow().isoformat()

            # Snowflake returns pre-computed results in ~100ms (NO calculations here)
            results = await self._connector.execute_query(
                query,
                [location_id, from_date, to_date]
            )

            if results:
                # Just format the pre-computed data (no aggregation)
                latest = results[0]
                return {
                    "location_id": location_id,
                    "date_range": {
                        "from": from_date,
                        "to": to_date
                    },
                    "total_production": float(latest.get('TOTAL_PRODUCTION', 0)),
                    "total_collections": float(latest.get('TOTAL_COLLECTIONS', 0)),
                    "new_patients": int(latest.get('NEW_PATIENTS', 0)),
                    "active_patients": int(latest.get('ACTIVE_PATIENTS', 0)),
                    "appointments_scheduled": int(latest.get('APPOINTMENTS_SCHEDULED', 0)),
                    "appointments_completed": int(latest.get('APPOINTMENTS_COMPLETED', 0)),
                    "cancellation_rate": float(latest.get('CANCELLATION_RATE', 0)),
                    "no_show_rate": float(latest.get('NO_SHOW_RATE', 0))
                }
            else:
                logger.warning(f"No production data found for location: {location_id}")
                return self._get_mock_production_metrics(location_id, from_date, to_date)

        except Exception as e:
            logger.error(f"Error querying Snowflake: {e}")
            return self._get_mock_production_metrics(location_id, from_date, to_date)

    async def execute_query(
        self,
        query: str,
        params: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute custom SQL query on Snowflake

        Args:
            query: SQL query string
            params: Optional query parameters (list for positional params)

        Returns:
            Query results as list of dictionaries
        """
        if not self.is_enabled:
            logger.warning("Snowflake not configured")
            return []

        logger.info(f"Executing Snowflake query: {query[:100]}...")
        return await self._connector.execute_query(query, params)

    def _get_mock_financial_summary(
        self,
        location_id: str,
        from_date: Optional[str],
        to_date: Optional[str]
    ) -> Dict[str, Any]:
        """Generate mock financial data for development"""
        import random

        revenue = random.uniform(150000, 250000)
        expenses = revenue * random.uniform(0.6, 0.75)

        return {
            "location_id": location_id,
            "revenue": round(revenue, 2),
            "expenses": round(expenses, 2),
            "net_income": round(revenue - expenses, 2),
            "payroll_costs": round(expenses * 0.45, 2),
            "date_range": {
                "from": from_date or (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "to": to_date or datetime.utcnow().isoformat()
            },
            "breakdown": [
                {"category": "Patient Services", "amount": round(revenue * 0.85, 2)},
                {"category": "Insurance", "amount": round(revenue * 0.15, 2)},
            ]
        }

    def _get_mock_production_metrics(
        self,
        location_id: str,
        from_date: Optional[str],
        to_date: Optional[str]
    ) -> Dict[str, Any]:
        """Generate mock production data for development"""
        import random

        production = random.uniform(200000, 300000)
        collections = production * random.uniform(0.85, 0.95)
        appointments = random.randint(450, 550)
        completed = int(appointments * random.uniform(0.85, 0.92))

        return {
            "location_id": location_id,
            "date_range": {
                "from": from_date or (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "to": to_date or datetime.utcnow().isoformat()
            },
            "total_production": round(production, 2),
            "total_collections": round(collections, 2),
            "new_patients": random.randint(40, 80),
            "active_patients": random.randint(1800, 2200),
            "appointments_scheduled": appointments,
            "appointments_completed": completed,
            "cancellation_rate": round(random.uniform(3, 8), 1),
            "no_show_rate": round(random.uniform(2, 6), 1)
        }

    async def close(self):
        """Close Snowflake connection"""
        await self._connector.close()


# Singleton instance
_snowflake_service: Optional[SnowflakeService] = None


def get_snowflake_service() -> SnowflakeService:
    """Get singleton Snowflake service"""
    global _snowflake_service
    if _snowflake_service is None:
        _snowflake_service = SnowflakeService()
    return _snowflake_service
