"""
Bulk CSV Load API - Use existing Snowflake warehouse router to load CSVs
"""
from fastapi import APIRouter
from pydantic import BaseModel
import csv
import os
import json
from datetime import datetime
from typing import List, Dict
from ..services.warehouse_router import WarehouseRouter
from ..core.tenant import TenantContext

router = APIRouter(prefix="/api/v1/bulk-load", tags=["bulk-load"])

class BulkLoadResponse(BaseModel):
    status: str
    records_loaded: int
    tenant_id: str

@router.post("/transactions", response_model=BulkLoadResponse)
async def load_transactions_from_csv():
    """Load all transaction CSV files to Snowflake Bronze layer using warehouse router"""
    tenant = TenantContext.require_tenant()

    # CSV files configuration
    csv_files = [
        ('backup/TransactionDetail_eastlake.csv', 'eastlake'),
        ('backup/TransactionDetail_torrey_pines.csv', 'torrey_pines'),
        ('backup/TransactionDetail_ads.csv', 'ads')
    ]

    # Get warehouse router
    warehouse_router = WarehouseRouter()
    connector = await warehouse_router.get_connector('snowflake')
    total_loaded = 0

    for csv_file, practice_id in csv_files:
        csv_path = os.path.join('/app', csv_file)

        if not os.path.exists(csv_path):
            print(f"Skipping {csv_file} - file not found")
            continue

        print(f"Loading {csv_file} for {practice_id}...")

        # Read CSV
        with open(csv_path, 'r', encoding='utf-8') as f:
            # Skip header rows
            for _ in range(6):
                next(f)

            reader = csv.DictReader(f)
            batch = []

            for row in reader:
                clean_row = {k.strip(): v.strip() for k, v in row.items()}
                batch.append(clean_row)

                # Insert in batches of 500
                if len(batch) >= 500:
                    await _insert_batch(connector, batch, practice_id)
                    total_loaded += len(batch)
                    print(f"  Loaded {total_loaded} total records...")
                    batch = []

            # Insert remaining
            if batch:
                await _insert_batch(connector, batch, practice_id)
                total_loaded += len(batch)

    return BulkLoadResponse(
        status="success",
        records_loaded=total_loaded,
        tenant_id=tenant.tenant_code
    )

async def _insert_batch(connector, batch: List[Dict], practice_id: str):
    """Insert a batch of records using multi-row INSERT"""
    values = []
    for i, row in enumerate(batch):
        record_id = f"{practice_id}_{row.get('Document Number', '')}_{i}"
        sync_id = f"csv_load_{datetime.now().strftime('%Y%m%d')}"
        raw_data_json = json.dumps(row).replace("'", "''")

        values.append(f"""(
            '{record_id}',
            '{sync_id}',
            '{practice_id}',
            PARSE_JSON('{raw_data_json}'),
            CURRENT_TIMESTAMP(),
            CURRENT_TIMESTAMP(),
            FALSE
        )""")

    sql = f"""
        INSERT INTO bronze.netsuite_journal_entries
        (id, sync_id, tenant_id, raw_data, last_modified_date, extracted_at, is_deleted)
        VALUES {', '.join(values)}
    """

    await connector.execute_query(sql)
