"""
Operations Report Excel/CSV Parser Service
Parses SCDP Monthly Operations Report and loads into Snowflake Bronze layer

REUSES: PDFIngestionService pattern for consistency
Flow: Upload Excel/CSV → Parse metrics → Bronze Layer → Dynamic tables auto-refresh
"""

import csv
import json
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from loguru import logger

from ..connectors.snowflake import SnowflakeConnector
from ..core.config import Settings
from ..core.tenant import TenantContext


class OperationsReportParser:
    """
    Parse SCDP Monthly Operations Report (Excel or CSV)
    Follows PDFIngestionService pattern for consistency
    """

    def __init__(self, snowflake_connector: SnowflakeConnector, settings: Settings):
        """
        Initialize operations report parser

        Args:
            snowflake_connector: Snowflake connector instance
            settings: Application settings
        """
        self.snowflake = snowflake_connector
        self.settings = settings

    def parse_excel(
        self,
        file_path: str,
        practice_code: str,
        practice_name: str,
        report_month: str
    ) -> Dict[str, Any]:
        """
        Parse Operations Report Excel file

        Args:
            file_path: Path to Excel file
            practice_code: Practice identifier (e.g., 'LHD', 'eastlake')
            practice_name: Practice display name
            report_month: Report month in YYYY-MM-DD format

        Returns:
            Dictionary with parsed metrics in Bronze-compatible format
        """
        logger.info(f"Parsing Operations Report for {practice_name} ({practice_code}), month: {report_month}")

        try:
            # Read Excel file
            df = pd.read_excel(file_path, sheet_name='Operating Metrics')

            # Extract metrics from the structured Excel layout
            metrics = self._extract_metrics_from_dataframe(df, practice_code, report_month)

            # Build result in same format as PDF ingestion
            result = {
                'practice_code': practice_code,
                'practice_name': practice_name,
                'report_month': report_month,
                'tenant_id': TenantContext.get_tenant().tenant_code if TenantContext.get_tenant() else 'silvercreek',
                'raw_data': metrics,
                'source_file': Path(file_path).name,
                'extraction_method': 'excel_parser',
                'data_quality_score': 1.0  # Excel data = perfect quality
            }

            logger.info(f"Successfully parsed {len(metrics)} metrics from {Path(file_path).name}")
            return result

        except Exception as e:
            logger.error(f"Failed to parse Excel file: {e}")
            raise

    def parse_csv(
        self,
        file_path: str,
        practice_code: str,
        practice_name: str,
        report_month: str
    ) -> Dict[str, Any]:
        """
        Parse Operations Report CSV file (converted from Excel)

        Args:
            file_path: Path to CSV file
            practice_code: Practice identifier
            practice_name: Practice display name
            report_month: Report month in YYYY-MM-DD format

        Returns:
            Dictionary with parsed metrics
        """
        logger.info(f"Parsing Operations Report CSV for {practice_name}")

        try:
            # Read CSV (same structure as Excel export)
            df = pd.read_csv(file_path)

            # Extract metrics
            metrics = self._extract_metrics_from_dataframe(df, practice_code, report_month)

            return {
                'practice_code': practice_code,
                'practice_name': practice_name,
                'report_month': report_month,
                'tenant_id': TenantContext.get_tenant().tenant_code if TenantContext.get_tenant() else 'silvercreek',
                'raw_data': metrics,
                'source_file': Path(file_path).name,
                'extraction_method': 'csv_parser',
                'data_quality_score': 1.0
            }

        except Exception as e:
            logger.error(f"Failed to parse CSV file: {e}")
            raise

    def _extract_metrics_from_dataframe(
        self,
        df: pd.DataFrame,
        practice_code: str,
        report_month: str
    ) -> Dict[str, Any]:
        """
        Extract metrics from Operations Report DataFrame

        The Excel has a complex layout:
        - Row 1-4: Headers and title
        - Row 5: Date columns (one per month)
        - Row 6+: Metric names in column 1, values in subsequent columns

        Args:
            df: Pandas DataFrame
            practice_code: Practice identifier
            report_month: Target month to extract

        Returns:
            Dictionary of metric_name: value pairs
        """
        metrics = {}

        # Find the column index for the target month
        # Row 4 (index 4) contains dates
        date_row = df.iloc[4]

        # Find which column has our target month
        target_col_idx = None
        for col_idx, cell_value in enumerate(date_row):
            if pd.notna(cell_value):
                try:
                    cell_date = pd.to_datetime(cell_value)
                    cell_month = cell_date.strftime('%Y-%m-01')
                    if cell_month == report_month:
                        target_col_idx = col_idx
                        break
                except:
                    continue

        if target_col_idx is None:
            logger.warning(f"Could not find data column for month {report_month}, using latest month")
            # Use the last non-null date column
            for col_idx in range(len(date_row) - 1, -1, -1):
                if pd.notna(date_row[col_idx]):
                    target_col_idx = col_idx
                    break

        logger.info(f"Extracting metrics from column index {target_col_idx}")

        # Extract metrics from rows 6+ (after headers)
        # Column 1 has metric names, target_col_idx has values
        metric_mappings = {
            # Production & Collections
            'Gross Production - Doctor': 'gross_production_doctor',
            'Gross Production - Specialty': 'gross_production_specialty',
            'Gross Production - Hygiene': 'gross_production_hygiene',
            'Gross Production - Total': 'total_production',
            'Net Production (Revenue)': 'net_production',
            'Collections': 'collections',

            # Patient Visits
            'Doctor #1': 'visits_doctor_1',
            'Doctor #2': 'visits_doctor_2',
            'Total Doctor Visits': 'visits_doctor_total',
            'Specialists': 'visits_specialist',
            'Hygienists': 'visits_hygiene',
            'Total Visits': 'visits_total',

            # Case Acceptance - Doctor #1
            'Doctor #1 - Treatment Presented': 'doc1_treatment_presented',
            'Doctor #1 - Treatment Accepted': 'doc1_treatment_accepted',

            # Case Acceptance - Doctor #2
            'Doctor #2 - Treatment Presented': 'doc2_treatment_presented',
            'Doctor #2 - Treatment Accepted': 'doc2_treatment_accepted',

            # New Patients
            'New Patients - Total': 'new_patients_total',
            'Reappointment Rate': 'new_patients_reappt_rate',

            # Hygiene Efficiency
            'Hygiene Capacity': 'hygiene_capacity_slots',
            'Hygiene Net Production': 'hygiene_net_production',
            'Hygiene Compensation': 'hygiene_compensation',
            'Hygiene Reappointment Rate': 'hygiene_reappt_rate',

            # Individual Provider Production
            'Doctor #1 Production': 'doctor_1_production',
            'Doctor #2 Production': 'doctor_2_production',
            'Specialist Production': 'specialist_production',
        }

        # Scan through rows to find and extract metrics
        for idx in range(6, len(df)):
            row = df.iloc[idx]
            metric_label = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ''

            if metric_label in metric_mappings:
                metric_key = metric_mappings[metric_label]
                metric_value = row.iloc[target_col_idx]

                if pd.notna(metric_value):
                    # Convert to appropriate type
                    try:
                        if isinstance(metric_value, (int, float)):
                            metrics[metric_key] = float(metric_value)
                        else:
                            metrics[metric_key] = float(str(metric_value).replace(',', ''))
                    except:
                        metrics[metric_key] = 0.0

        # Calculate derived metrics
        if 'gross_production_doctor' in metrics and 'net_production' not in metrics:
            total_gross = metrics.get('total_production', 0)
            net = metrics.get('net_production', 0)
            if total_gross > 0 and net > 0:
                metrics['adjustments'] = total_gross - net
            else:
                metrics['adjustments'] = 0.0

        logger.info(f"Extracted {len(metrics)} metrics")
        return metrics

    async def insert_to_bronze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert parsed operations data to bronze.operations_metrics_raw

        Dynamic tables (Silver and Gold) will auto-refresh within 1 hour!

        Args:
            data: Parsed operations data

        Returns:
            Result dictionary with success status
        """
        try:
            # Generate unique ID
            record_id = f"{data['practice_code']}_{data['report_month']}"

            # Convert raw_data dict to JSON string for PARSE_JSON()
            raw_data_json = json.dumps(data['raw_data'])

            # Use MERGE to handle duplicates (upsert pattern)
            # If same practice_code + report_month exists, update it
            logger.info(f"Upserting operations data to Bronze: {record_id}")

            merge_query = f"""
                MERGE INTO bronze.operations_metrics_raw AS target
                USING (
                    SELECT
                        '{record_id}' AS id,
                        '{data['practice_code']}' AS practice_code,
                        '{data['practice_name']}' AS practice_name,
                        '{data['report_month']}'::DATE AS report_month,
                        '{data['tenant_id']}' AS tenant_id,
                        PARSE_JSON('{raw_data_json.replace("'", "''")}') AS raw_data,
                        '{data['source_file']}' AS source_file,
                        CURRENT_TIMESTAMP() AS uploaded_at
                ) AS source
                ON target.id = source.id
                WHEN MATCHED THEN
                    UPDATE SET
                        practice_name = source.practice_name,
                        raw_data = source.raw_data,
                        source_file = source.source_file,
                        uploaded_at = source.uploaded_at,
                        loaded_at = CURRENT_TIMESTAMP()
                WHEN NOT MATCHED THEN
                    INSERT (id, practice_code, practice_name, report_month, tenant_id, raw_data, source_file, uploaded_at)
                    VALUES (source.id, source.practice_code, source.practice_name, source.report_month,
                           source.tenant_id, source.raw_data, source.source_file, source.uploaded_at)
            """

            self.snowflake.execute(merge_query)

            logger.info(f"✅ Successfully inserted to Bronze layer")
            logger.info(f"   Dynamic tables will auto-refresh within 1 hour")
            logger.info(f"   To force immediate refresh: ALTER DYNAMIC TABLE ... REFRESH")

            return {
                "status": "success",
                "record_id": record_id,
                "practice_code": data['practice_code'],
                "report_month": data['report_month'],
                "metrics_count": len(data['raw_data']),
                "bronze_table": "bronze.operations_metrics_raw",
                "message": "Data inserted to Bronze. Dynamic tables will auto-refresh."
            }

        except Exception as e:
            logger.error(f"Failed to insert to Bronze: {e}")
            raise

    async def process_and_insert(
        self,
        file_path: str,
        file_type: str,  # 'excel' or 'csv'
        practice_code: str,
        practice_name: str,
        report_month: str
    ) -> Dict[str, Any]:
        """
        Parse file and insert to Bronze in one operation

        Args:
            file_path: Path to Excel or CSV file
            file_type: 'excel' or 'csv'
            practice_code: Practice identifier
            practice_name: Practice display name
            report_month: Report month (YYYY-MM-DD)

        Returns:
            Insertion result
        """
        # Parse based on file type
        if file_type.lower() in ['excel', 'xlsx', 'xls']:
            parsed_data = self.parse_excel(file_path, practice_code, practice_name, report_month)
        elif file_type.lower() == 'csv':
            parsed_data = self.parse_csv(file_path, practice_code, practice_name, report_month)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        # Insert to Bronze
        result = await self.insert_to_bronze(parsed_data)

        return result


# Standalone function for direct script usage (like load_csv_to_snowflake.py)
def load_operations_csv_to_snowflake(csv_file: str, practice_code: str, practice_name: str, report_month: str):
    """
    Direct CSV load function for use in standalone scripts

    Example:
        load_operations_csv_to_snowflake(
            'operations_report.csv',
            'LHD',
            'Laguna Hills Dental',
            '2022-09-01'
        )
    """
    from ..connectors.snowflake import SnowflakeConnector
    from ..core.config import get_settings

    settings = get_settings()
    snowflake = SnowflakeConnector(settings)

    parser = OperationsReportParser(snowflake, settings)

    # Parse CSV
    data = parser.parse_csv(csv_file, practice_code, practice_name, report_month)

    # Insert to Bronze (async wrapper)
    import asyncio
    result = asyncio.run(parser.insert_to_bronze(data))

    print(f"✅ Loaded {practice_name} ({report_month}) to Bronze")
    print(f"   Record ID: {result['record_id']}")
    print(f"   Metrics: {result['metrics_count']}")

    return result
