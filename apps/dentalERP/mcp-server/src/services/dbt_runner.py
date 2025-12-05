"""
dbt Runner Service
Executes dbt transformations in Snowflake after data ingestion
"""

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger

from ..core.config import Settings


class DBTRunner:
    """Service for running dbt transformations"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.dbt_project_dir = Path(__file__).parent.parent.parent.parent / "dbt" / "dentalerp"
        self.dbt_profiles_dir = self.dbt_project_dir

    def _validate_dbt_setup(self) -> bool:
        """Validate dbt project exists and is configured"""
        if not self.dbt_project_dir.exists():
            logger.error(f"dbt project directory not found: {self.dbt_project_dir}")
            return False

        dbt_project_file = self.dbt_project_dir / "dbt_project.yml"
        if not dbt_project_file.exists():
            logger.error(f"dbt_project.yml not found: {dbt_project_file}")
            return False

        logger.info(f"dbt project found: {self.dbt_project_dir}")
        return True

    async def run_dbt_models(
        self,
        models: Optional[List[str]] = None,
        select: Optional[str] = None,
        full_refresh: bool = False,
        vars: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run dbt models

        Args:
            models: List of specific models to run (e.g., ['stg_pms_day_sheets'])
            select: dbt select syntax (e.g., 'tag:daily', 'silver+')
            full_refresh: Force full refresh of incremental models
            vars: Variables to pass to dbt

        Returns:
            Dict with run results
        """
        if not self._validate_dbt_setup():
            return {
                "success": False,
                "error": "dbt project not properly configured",
                "output": ""
            }

        # Build dbt command
        cmd = ["dbt", "run"]

        # Add model selection
        if models:
            cmd.extend(["--models"] + models)
        elif select:
            cmd.extend(["--select", select])

        # Add flags
        if full_refresh:
            cmd.append("--full-refresh")

        # Add vars
        if vars:
            import json
            cmd.extend(["--vars", json.dumps(vars)])

        # Set working directory and profiles dir
        cmd.extend([
            "--project-dir", str(self.dbt_project_dir),
            "--profiles-dir", str(self.dbt_profiles_dir)
        ])

        logger.info(f"Running dbt command: {' '.join(cmd)}")

        try:
            # Build environment with Snowflake credentials
            env = os.environ.copy()
            env['SNOWFLAKE_ACCOUNT'] = self.settings.snowflake_account
            env['SNOWFLAKE_USER'] = self.settings.snowflake_user
            env['SNOWFLAKE_PASSWORD'] = self.settings.snowflake_password
            env['SNOWFLAKE_WAREHOUSE'] = self.settings.snowflake_warehouse
            env['SNOWFLAKE_DATABASE'] = self.settings.snowflake_database
            env['SNOWFLAKE_SCHEMA'] = self.settings.snowflake_schema or 'PUBLIC'
            env['SNOWFLAKE_ROLE'] = self.settings.snowflake_role or 'ACCOUNTADMIN'

            # Run dbt asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.dbt_project_dir),
                env=env
            )

            stdout, stderr = await process.communicate()

            output = stdout.decode() if stdout else ""
            error_output = stderr.decode() if stderr else ""

            success = process.returncode == 0

            if success:
                logger.info(f"✅ dbt run successful")
                logger.debug(f"dbt output:\n{output}")
            else:
                logger.error(f"❌ dbt run failed with return code {process.returncode}")
                logger.error(f"dbt error:\n{error_output}")

            return {
                "success": success,
                "return_code": process.returncode,
                "output": output,
                "error": error_output,
                "command": " ".join(cmd)
            }

        except Exception as e:
            logger.error(f"Failed to run dbt: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "command": " ".join(cmd)
            }

    async def run_pdf_ingestion_pipeline(
        self,
        practice_location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the complete PDF ingestion dbt pipeline:
        Bronze → Silver (stg_pms_day_sheets) → Gold (daily_production_metrics)

        Args:
            practice_location: Optional practice location to filter

        Returns:
            Dict with pipeline results
        """
        logger.info("Running PDF ingestion dbt pipeline")

        results = []

        # Step 1: Run Silver layer
        logger.info("Step 1: Running Silver layer transformations")
        silver_result = await self.run_dbt_models(
            models=["silver.pms.stg_pms_day_sheets"],
            vars={"practice_location": practice_location} if practice_location else None
        )
        results.append({"step": "silver", "result": silver_result})

        if not silver_result["success"]:
            logger.error("Silver layer failed, stopping pipeline")
            return {
                "success": False,
                "pipeline": "pdf_ingestion",
                "steps_completed": 1,
                "results": results,
                "error": "Silver layer transformation failed"
            }

        # Step 2: Run Gold layer
        logger.info("Step 2: Running Gold layer aggregations")
        gold_result = await self.run_dbt_models(
            models=["gold.metrics.daily_production_metrics"],
            vars={"practice_location": practice_location} if practice_location else None
        )
        results.append({"step": "gold", "result": gold_result})

        success = all(r["result"]["success"] for r in results)

        logger.info(f"✅ PDF ingestion pipeline completed: {'SUCCESS' if success else 'FAILED'}")

        return {
            "success": success,
            "pipeline": "pdf_ingestion",
            "steps_completed": len(results),
            "results": results,
            "practice_location": practice_location
        }

    async def test_dbt_connection(self) -> Dict[str, Any]:
        """
        Test dbt connection to Snowflake

        Returns:
            Dict with test results
        """
        if not self._validate_dbt_setup():
            return {
                "success": False,
                "error": "dbt project not properly configured"
            }

        cmd = [
            "dbt", "debug",
            "--project-dir", str(self.dbt_project_dir),
            "--profiles-dir", str(self.dbt_profiles_dir)
        ]

        logger.info("Testing dbt connection")

        try:
            # Build environment with Snowflake credentials
            env = os.environ.copy()
            env['SNOWFLAKE_ACCOUNT'] = self.settings.snowflake_account
            env['SNOWFLAKE_USER'] = self.settings.snowflake_user
            env['SNOWFLAKE_PASSWORD'] = self.settings.snowflake_password
            env['SNOWFLAKE_WAREHOUSE'] = self.settings.snowflake_warehouse
            env['SNOWFLAKE_DATABASE'] = self.settings.snowflake_database
            env['SNOWFLAKE_SCHEMA'] = self.settings.snowflake_schema or 'PUBLIC'
            env['SNOWFLAKE_ROLE'] = self.settings.snowflake_role or 'ACCOUNTADMIN'

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.dbt_project_dir),
                env=env
            )

            stdout, stderr = await process.communicate()

            output = stdout.decode() if stdout else ""
            success = "All checks passed!" in output

            return {
                "success": success,
                "output": output,
                "error": stderr.decode() if stderr else ""
            }

        except Exception as e:
            logger.error(f"Failed to test dbt connection: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
_dbt_runner: Optional[DBTRunner] = None


def get_dbt_runner(settings: Settings) -> DBTRunner:
    """Get singleton dbt runner instance"""
    global _dbt_runner
    if _dbt_runner is None:
        _dbt_runner = DBTRunner(settings)
    return _dbt_runner
