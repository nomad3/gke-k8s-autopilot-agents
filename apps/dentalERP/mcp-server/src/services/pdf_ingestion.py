"""
PDF Ingestion Service
Extracts data from PDF reports and loads into Snowflake Bronze layer

Flow:
1. Upload PDF → 2. AI Extract → 3. Transform → 4. Bronze Layer → 5. Queue dbt run
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from loguru import logger

from ..parsers.pdf_extractor import PDFExtractor
from ..connectors.snowflake import SnowflakeConnector
from ..core.config import Settings


class PDFIngestionService:
    """Service for ingesting PDF reports into Snowflake data warehouse"""

    # Map report types to Bronze table names
    BRONZE_TABLE_MAP = {
        "day_sheet": "bronze.pms_day_sheets",
        "deposit_slip": "bronze.pms_deposit_slips",
        "pay_reconciliation": "bronze.payroll_reconciliations",
        "operations_report": "bronze.operations_reports",
    }

    # Bronze table schemas
    BRONZE_SCHEMAS = {
        "bronze.pms_day_sheets": """
            id VARCHAR(255) PRIMARY KEY,
            source_system VARCHAR(100) NOT NULL DEFAULT 'manual_pdf',
            practice_location VARCHAR(100),
            report_date DATE,
            report_type VARCHAR(50) NOT NULL DEFAULT 'day_sheet',
            raw_data VARIANT NOT NULL,
            extracted_data VARIANT,
            extraction_method VARCHAR(50),
            file_name VARCHAR(500),
            uploaded_by VARCHAR(255),
            uploaded_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
            extracted_at TIMESTAMP_LTZ,
            batch_id VARCHAR(255),
            correlation_id VARCHAR(255)
        """,
        "bronze.pms_deposit_slips": """
            id VARCHAR(255) PRIMARY KEY,
            source_system VARCHAR(100) NOT NULL DEFAULT 'manual_pdf',
            practice_location VARCHAR(100),
            deposit_date DATE,
            report_type VARCHAR(50) NOT NULL DEFAULT 'deposit_slip',
            raw_data VARIANT NOT NULL,
            extracted_data VARIANT,
            extraction_method VARCHAR(50),
            file_name VARCHAR(500),
            uploaded_by VARCHAR(255),
            uploaded_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
            extracted_at TIMESTAMP_LTZ,
            batch_id VARCHAR(255),
            correlation_id VARCHAR(255)
        """,
        "bronze.payroll_reconciliations": """
            id VARCHAR(255) PRIMARY KEY,
            source_system VARCHAR(100) NOT NULL DEFAULT 'manual_pdf',
            practice_location VARCHAR(100),
            pay_period_start DATE,
            pay_period_end DATE,
            report_type VARCHAR(50) NOT NULL DEFAULT 'pay_reconciliation',
            raw_data VARIANT NOT NULL,
            extracted_data VARIANT,
            extraction_method VARCHAR(50),
            file_name VARCHAR(500),
            uploaded_by VARCHAR(255),
            uploaded_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
            extracted_at TIMESTAMP_LTZ,
            batch_id VARCHAR(255),
            correlation_id VARCHAR(255)
        """,
        "bronze.operations_reports": """
            id VARCHAR(255) PRIMARY KEY,
            source_system VARCHAR(100) NOT NULL DEFAULT 'manual_pdf',
            practice_location VARCHAR(100),
            report_period VARCHAR(20),
            report_type VARCHAR(50) NOT NULL DEFAULT 'operations_report',
            raw_data VARIANT NOT NULL,
            extracted_data VARIANT,
            extraction_method VARCHAR(50),
            file_name VARCHAR(500),
            uploaded_by VARCHAR(255),
            uploaded_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
            extracted_at TIMESTAMP_LTZ,
            batch_id VARCHAR(255),
            correlation_id VARCHAR(255)
        """,
    }

    def __init__(
        self,
        snowflake_connector: SnowflakeConnector,
        settings: Settings,
        openai_api_key: Optional[str] = None
    ):
        """
        Initialize PDF ingestion service

        Args:
            snowflake_connector: Snowflake connector instance
            settings: Application settings
            openai_api_key: Optional OpenAI API key for AI extraction
        """
        self.snowflake = snowflake_connector
        self.settings = settings
        self.pdf_extractor = PDFExtractor(openai_api_key)

    async def ingest_pdf(
        self,
        pdf_bytes: bytes,
        file_name: str,
        report_type: Optional[str] = None,
        practice_location: Optional[str] = None,
        uploaded_by: Optional[str] = None,
        use_ai: bool = True,
        batch_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Ingest a single PDF file into Snowflake Bronze layer

        Args:
            pdf_bytes: PDF file as bytes
            file_name: Original filename
            report_type: Optional report type (day_sheet, deposit_slip, etc.)
            practice_location: Practice location name
            uploaded_by: User who uploaded the file
            use_ai: Whether to use AI extraction
            batch_id: Optional batch identifier for grouping uploads
            correlation_id: Optional correlation ID for tracking

        Returns:
            Dictionary with ingestion results
        """
        logger.info(f"Ingesting PDF: {file_name}")

        try:
            # Step 1: Extract data from PDF
            extraction_result = self.pdf_extractor.extract_from_bytes(
                pdf_bytes=pdf_bytes,
                report_type=report_type,
                use_ai=use_ai
            )

            detected_report_type = extraction_result.get("report_type", "unknown")
            extracted_data = extraction_result.get("data", {})
            extraction_method = extraction_result.get("extraction_method", "rules")

            # Override location if provided in extraction
            if not practice_location and extracted_data.get("practice_location"):
                practice_location = extracted_data.get("practice_location")

            # Step 2: Determine Bronze table
            table_name = self.BRONZE_TABLE_MAP.get(detected_report_type)
            if not table_name:
                logger.warning(f"Unknown report type: {detected_report_type}, using generic table")
                table_name = "bronze.pms_unknown_reports"

            # Step 3: Ensure Bronze table exists
            await self._ensure_bronze_table_exists(table_name)

            # Step 4: Prepare record for insertion
            record_id = self._generate_record_id(file_name, practice_location)

            record = {
                "id": record_id,
                "source_system": "manual_pdf",
                "practice_location": practice_location,
                "report_type": detected_report_type,
                "raw_data": extraction_result,  # Full extraction result as JSON
                "extracted_data": extracted_data,  # Just the data portion
                "extraction_method": extraction_method,
                "file_name": file_name,
                "uploaded_by": uploaded_by,
                "uploaded_at": datetime.utcnow().isoformat(),
                "extracted_at": extraction_result.get("extracted_at"),
                "batch_id": batch_id,
                "correlation_id": correlation_id,
            }

            # Add report-specific date fields
            if detected_report_type == "day_sheet":
                record["report_date"] = extracted_data.get("report_date")
            elif detected_report_type == "deposit_slip":
                record["deposit_date"] = extracted_data.get("deposit_date")
            elif detected_report_type == "pay_reconciliation":
                record["pay_period_start"] = extracted_data.get("pay_period_start")
                record["pay_period_end"] = extracted_data.get("pay_period_end")
            elif detected_report_type == "operations_report":
                record["report_period"] = extracted_data.get("report_period")

            # Step 5: Insert into Bronze layer
            inserted_count = await self.snowflake.bulk_insert_bronze(
                table_name=table_name,
                records=[record],
                batch_size=1
            )

            logger.info(f"Successfully inserted PDF data into {table_name}")

            # Step 6: Return result
            # Safely get extracted_fields
            logger.debug(f"extracted_data type: {type(extracted_data)}, value: {str(extracted_data)[:200]}")
            try:
                extracted_fields = list(extracted_data.keys()) if (extracted_data and isinstance(extracted_data, dict)) else []
            except Exception as e:
                logger.error(f"Could not extract fields from extracted_data: {e}", exc_info=True)
                extracted_fields = []

            return {
                "success": True,
                "record_id": record_id,
                "table_name": table_name,
                "report_type": detected_report_type,
                "practice_location": practice_location,
                "extraction_method": extraction_method,
                "records_inserted": inserted_count,
                "extracted_fields": extracted_fields,
                "message": f"Successfully ingested {file_name} into {table_name}"
            }

        except Exception as e:
            logger.error(f"Error ingesting PDF {file_name}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "file_name": file_name,
                "message": f"Failed to ingest {file_name}: {str(e)}"
            }

    async def ingest_pdf_batch(
        self,
        pdfs: List[Dict[str, Any]],
        batch_id: Optional[str] = None,
        uploaded_by: Optional[str] = None,
        use_ai: bool = True,
    ) -> Dict[str, Any]:
        """
        Ingest multiple PDF files in a batch

        Args:
            pdfs: List of dicts with {pdf_bytes, file_name, report_type, practice_location}
            batch_id: Batch identifier for tracking
            uploaded_by: User who uploaded the files
            use_ai: Whether to use AI extraction

        Returns:
            Dictionary with batch results
        """
        if not batch_id:
            batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"Starting batch ingestion: {batch_id} ({len(pdfs)} files)")

        results = []
        for pdf_info in pdfs:
            result = await self.ingest_pdf(
                pdf_bytes=pdf_info["pdf_bytes"],
                file_name=pdf_info["file_name"],
                report_type=pdf_info.get("report_type"),
                practice_location=pdf_info.get("practice_location"),
                uploaded_by=uploaded_by,
                use_ai=use_ai,
                batch_id=batch_id,
                correlation_id=pdf_info.get("correlation_id"),
            )
            results.append(result)

        # Summary
        successful = sum(1 for r in results if r.get("success"))
        failed = len(results) - successful

        return {
            "batch_id": batch_id,
            "total_files": len(pdfs),
            "successful": successful,
            "failed": failed,
            "results": results,
            "uploaded_by": uploaded_by,
            "use_ai": use_ai,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _ensure_bronze_table_exists(self, table_name: str):
        """Create Bronze table if it doesn't exist"""
        if table_name not in self.BRONZE_SCHEMAS:
            logger.warning(f"No schema defined for {table_name}, skipping table creation")
            return

        schema_sql = self.BRONZE_SCHEMAS[table_name]

        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {schema_sql}
        ) CLUSTER BY (source_system, report_type, uploaded_at)
        """

        try:
            await self.snowflake.execute_query(create_table_sql)
            logger.info(f"Ensured Bronze table exists: {table_name}")
        except Exception as e:
            logger.error(f"Error creating Bronze table {table_name}: {e}")
            raise

    def _generate_record_id(self, file_name: str, location: Optional[str]) -> str:
        """Generate unique record ID for Bronze layer"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
        location_part = location.lower().replace(" ", "_") if location else "unknown"
        file_part = Path(file_name).stem[:50].lower().replace(" ", "_")

        return f"pdf_{location_part}_{file_part}_{timestamp}"

    async def get_ingestion_stats(
        self,
        practice_location: Optional[str] = None,
        report_type: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get ingestion statistics

        Args:
            practice_location: Filter by practice
            report_type: Filter by report type
            days: Number of days to look back

        Returns:
            Statistics dictionary
        """
        # Build WHERE clause
        where_conditions = [
            f"uploaded_at >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())"
        ]

        if practice_location:
            where_conditions.append(f"practice_location = '{practice_location}'")

        if report_type:
            where_conditions.append(f"report_type = '{report_type}'")

        where_clause = " AND ".join(where_conditions)

        # Query all Bronze tables for stats
        stats_queries = []
        for table_name in self.BRONZE_TABLE_MAP.values():
            query = f"""
            SELECT
                '{table_name}' as table_name,
                COUNT(*) as record_count,
                COUNT(DISTINCT practice_location) as location_count,
                MIN(uploaded_at) as earliest_upload,
                MAX(uploaded_at) as latest_upload,
                COUNT(DISTINCT DATE(uploaded_at)) as upload_days
            FROM {table_name}
            WHERE {where_clause}
            """
            stats_queries.append(query)

        combined_query = " UNION ALL ".join(stats_queries)

        try:
            results = await self.snowflake.execute_query(combined_query)

            return {
                "period_days": days,
                "practice_location": practice_location,
                "report_type": report_type,
                "tables": results,
                "total_records": sum(r.get("RECORD_COUNT", 0) for r in results),
                "queried_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting ingestion stats: {e}")
            return {"error": str(e)}
