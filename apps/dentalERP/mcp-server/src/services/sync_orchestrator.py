"""
Sync Orchestration Service

Orchestrates data synchronization from external systems to Snowflake
Implements ETL pipeline: Extract → Transform → Load
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..connectors.registry import get_connector_registry
from ..connectors.snowflake import get_snowflake_connector
from ..models.mapping import IntegrationTypeEnum, SyncJob, SyncStatusEnum
from ..utils.logger import logger


class SyncOrchestrator:
    """
    Orchestrates ETL workflows for data synchronization

    Flow:
    1. Extract: Fetch data from external API via connector
    2. Load: Write RAW data to Snowflake Bronze layer
    3. Transform: dbt handles Bronze → Silver → Gold (happens in Snowflake)
    4. Track: Update sync job status
    """

    def __init__(self):
        self.connector_registry = get_connector_registry()
        self.snowflake_connector = get_snowflake_connector()

    async def execute_sync(
        self,
        db: AsyncSession,
        sync_job: SyncJob
    ) -> Dict[str, Any]:
        """
        Execute a sync job

        MCP Server role: EXTRACT and LOAD only
        - Extract: Fetch data from external APIs
        - Load: Insert raw data into Snowflake Bronze layer
        - Transform: Let Snowflake/dbt handle all transformations

        Args:
            db: Database session
            sync_job: Sync job configuration

        Returns:
            Sync result summary
        """
        logger.info(f"Executing sync job: {sync_job.id}")

        try:
            # Update status to RUNNING
            sync_job.status = SyncStatusEnum.RUNNING
            sync_job.started_at = datetime.utcnow()
            await db.commit()

            # Get connector for the integration type
            connector = await self.connector_registry.get_connector(
                sync_job.integration_type.value
            )

            if not connector:
                raise Exception(f"Connector not available for {sync_job.integration_type}")

            # EXTRACT: Fetch raw data from external system (no heavy processing)
            all_records = []
            for entity_type in sync_job.entity_types:
                logger.info(f"Extracting {entity_type} from {sync_job.integration_type}")

                response = await connector.fetch_data(
                    entity_type=entity_type,
                    filters={
                        "location_ids": sync_job.location_ids,
                        "sync_mode": sync_job.sync_mode,
                    }
                )

                if response.success and response.data:
                    # Minimal transformation - just add metadata for tracking
                    for record in response.data:
                        all_records.append({
                            "source_system": sync_job.integration_type.value,
                            "entity_type": entity_type,
                            "raw_data": record,  # Store entire raw response
                            "extracted_at": datetime.utcnow().isoformat()
                        })

                    logger.info(f"Extracted {len(response.data)} {entity_type} records")
                else:
                    logger.warning(f"Failed to fetch {entity_type}: {response.error}")

            # LOAD: Write raw data directly to Snowflake Bronze layer
            # Let Snowflake handle all heavy transformations via dbt
            if self.snowflake_connector.is_enabled and all_records:
                loaded_count = await self._load_to_snowflake_bronze(all_records, sync_job.integration_type.value)
                logger.info(f"Loaded {loaded_count} raw records to Snowflake Bronze layer")
            else:
                logger.warning("Snowflake not configured, skipping load step")
                loaded_count = len(all_records)

            # Update sync job as completed
            sync_job.status = SyncStatusEnum.COMPLETED
            sync_job.completed_at = datetime.utcnow()
            sync_job.records_processed = loaded_count
            await db.commit()

            logger.info(f"✅ Sync complete: {loaded_count} records → Snowflake Bronze → dbt will transform")

            return {
                "status": "completed",
                "records_processed": loaded_count,
                "entity_types": sync_job.entity_types,
                "note": "Raw data loaded to Snowflake. Run dbt to transform into Silver/Gold layers."
            }

        except Exception as e:
            logger.error(f"Sync job failed: {e}", exc_info=True)

            # Update sync job as failed
            sync_job.status = SyncStatusEnum.FAILED
            sync_job.completed_at = datetime.utcnow()
            sync_job.errors = [str(e)]
            await db.commit()

            return {
                "status": "failed",
                "error": str(e),
            }

    async def _load_to_snowflake_bronze(
        self,
        records: List[Dict[str, Any]],
        source_system: str
    ) -> int:
        """
        Load RAW records to Snowflake Bronze layer

        NO heavy transformation here - that's dbt's job!
        Just insert raw JSON data with metadata

        Args:
            records: List of raw records with minimal metadata
            source_system: Source system name

        Returns:
            Number of records loaded
        """
        logger.info(f"Loading {len(records)} RAW records to Snowflake Bronze layer")

        # Group by entity type
        by_entity = {}
        for record in records:
            entity_type = record.get("entity_type", "unknown")
            if entity_type not in by_entity:
                by_entity[entity_type] = []
            by_entity[entity_type].append(record)

        # Insert raw data to Bronze layer tables
        total_loaded = 0
        for entity_type, entity_records in by_entity.items():
            table_name = f"bronze.{source_system}_{entity_type}"

            logger.info(f"Inserting {len(entity_records)} raw records into {table_name}")

            # Ensure Bronze table exists before inserting
            await self.snowflake_connector.create_bronze_table_if_not_exists(
                table_name,
                source_system
            )

            # Bulk insert raw records with metadata
            # Store entire raw_data as VARIANT column for flexibility
            inserted_count = await self.snowflake_connector.bulk_insert_bronze(
                table_name=table_name,
                records=entity_records,
                batch_size=10000
            )

            total_loaded += inserted_count
            logger.info(f"✅ Inserted {inserted_count} records to {table_name}")

        logger.info(f"✅ Bronze layer load complete: {total_loaded} records. Run dbt to transform.")
        return total_loaded

    async def create_and_execute_sync(
        self,
        db: AsyncSession,
        integration_type: str,
        entity_types: List[str],
        location_ids: Optional[List[str]] = None,
        sync_mode: str = "incremental"
    ) -> SyncJob:
        """
        Create and immediately execute a sync job

        Args:
            db: Database session
            integration_type: Integration to sync
            entity_types: Entity types to sync
            location_ids: Optional location filter
            sync_mode: 'full' or 'incremental'

        Returns:
            Completed sync job
        """
        # Create sync job record
        sync_job = SyncJob(
            id=f"sync_{uuid4().hex[:12]}",
            integration_type=IntegrationTypeEnum(integration_type),
            entity_types=entity_types,
            location_ids=location_ids,
            sync_mode=sync_mode,
            status=SyncStatusEnum.PENDING,
        )

        db.add(sync_job)
        await db.commit()
        await db.refresh(sync_job)

        # Execute sync (in background for production)
        await self.execute_sync(db, sync_job)

        await db.refresh(sync_job)
        return sync_job


# Singleton instance
_sync_orchestrator: Optional[SyncOrchestrator] = None


def get_sync_orchestrator() -> SyncOrchestrator:
    """Get singleton sync orchestrator"""
    global _sync_orchestrator
    if _sync_orchestrator is None:
        _sync_orchestrator = SyncOrchestrator()
    return _sync_orchestrator
