"""
NetSuite CSV Upload API - Manual ingestion for NetSuite TransactionDetail exports
REUSES: operations.py upload pattern for consistency
"""

import os
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from ..core.security import get_api_key_header
from ..core.tenant import TenantContext
from ..services.warehouse_router import get_tenant_warehouse
from ..services.netsuite_csv_parser import NetSuiteCSVParser
from ..core.config import get_settings
from ..utils.logger import logger

router = APIRouter(prefix="/api/v1/netsuite", tags=["netsuite"])


@router.post("/upload/transactions")
async def upload_netsuite_transactions(
    file: UploadFile = File(...),
    subsidiary_id: Optional[str] = Form(None, description="Optional: Practice ID (will auto-detect from CSV)"),
    subsidiary_name: Optional[str] = Form(None, description="Optional: Practice name (will auto-detect from CSV)"),
    api_key: str = Depends(get_api_key_header)
):
    """
    Upload NetSuite TransactionDetail CSV export

    REUSES: operations.py /upload pattern

    CSV Format Expected:
    - Row 1: "Silver Creek Dental Partners, LLC"
    - Row 2: "Parent Company : ... : SCDP {Practice}, LLC"
    - Row 3: Transaction Detail
    - Row 4: Date range
    - Row 5: Blank
    - Row 6: Blank
    - Row 7: Headers (Type, Date, Document Number, Name, Memo, Account, Clr, Split, Qty, Amount)
    - Row 8+: Transaction data

    Example:
        curl -X POST http://localhost:8085/api/v1/netsuite/upload/transactions \
          -H "Authorization: Bearer $MCP_API_KEY" \
          -H "X-Tenant-ID: silvercreek" \
          -F "file=@TransactionDetail-83.csv"

    Or with explicit subsidiary info:
        curl -X POST http://localhost:8085/api/v1/netsuite/upload/transactions \
          -H "Authorization: Bearer $MCP_API_KEY" \
          -H "X-Tenant-ID: silvercreek" \
          -F "file=@transactions.csv" \
          -F "subsidiary_id=lhd" \
          -F "subsidiary_name=Laguna Hills Dental"
    """
    tenant = TenantContext.get_tenant()
    logger.info(f"Tenant '{tenant.tenant_code}' uploading NetSuite TransactionDetail CSV: {file.filename}")

    # Get warehouse connector
    try:
        warehouse = await get_tenant_warehouse()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Validate file type
    file_ext = os.path.splitext(file.filename or '')[1].lower()
    if file_ext not in ['.csv']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_ext}. NetSuite TransactionDetail must be CSV format."
        )

    # Save uploaded file to temp location
    temp_dir = "/tmp"
    temp_file = os.path.join(temp_dir, f"netsuite_txn_{uuid.uuid4().hex}.csv")

    try:
        # Save upload
        contents = await file.read()
        with open(temp_file, 'wb') as f:
            f.write(contents)

        logger.info(f"Saved NetSuite CSV to: {temp_file}")

        # Parse and insert
        settings = get_settings()
        parser = NetSuiteCSVParser(warehouse, settings)

        result = await parser.process_and_insert(
            file_path=temp_file,
            subsidiary_id=subsidiary_id,
            subsidiary_name=subsidiary_name
        )

        return {
            "status": "success",
            "message": f"NetSuite transactions uploaded successfully for {result['subsidiary_name']}",
            "data": result
        }

    except Exception as e:
        logger.error(f"NetSuite CSV upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process NetSuite CSV: {str(e)}"
        )

    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.unlink(temp_file)


@router.post("/upload/bulk-transactions")
async def bulk_upload_netsuite_transactions(
    api_key: str = Depends(get_api_key_header)
):
    """
    Bulk upload all NetSuite TransactionDetail CSV files from backup directory

    This endpoint processes all TransactionDetail-*.csv files in the /app/backup directory.
    Useful for initial data load or recovery.

    Example:
        curl -X POST http://localhost:8085/api/v1/netsuite/upload/bulk-transactions \
          -H "Authorization: Bearer $MCP_API_KEY" \
          -H "X-Tenant-ID: silvercreek"
    """
    tenant = TenantContext.get_tenant()
    logger.info(f"Tenant '{tenant.tenant_code}' triggering bulk NetSuite CSV upload")

    # Get warehouse connector
    try:
        warehouse = await get_tenant_warehouse()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    backup_dir = "/app/backup"
    if not os.path.exists(backup_dir):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup directory not found: {backup_dir}"
        )

    # Find all TransactionDetail CSV files
    csv_files = sorted([
        f for f in os.listdir(backup_dir)
        if f.startswith('TransactionDetail') and f.endswith('.csv')
    ])

    if not csv_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No TransactionDetail CSV files found in {backup_dir}"
        )

    logger.info(f"Found {len(csv_files)} TransactionDetail CSV files")

    # Process each file
    settings = get_settings()
    parser = NetSuiteCSVParser(warehouse, settings)
    results = []
    total_transactions = 0

    for csv_file in csv_files:
        file_path = os.path.join(backup_dir, csv_file)
        try:
            result = await parser.process_and_insert(file_path)
            results.append({
                'file': csv_file,
                'status': 'success',
                'subsidiary': result['subsidiary_name'],
                'transactions': result['transactions_count']
            })
            total_transactions += result['transactions_count']
            logger.info(f"✅ {csv_file}: {result['transactions_count']} transactions")
        except Exception as e:
            logger.error(f"❌ {csv_file}: {e}")
            results.append({
                'file': csv_file,
                'status': 'failed',
                'error': str(e)
            })

    return {
        "status": "completed",
        "message": f"Processed {len(csv_files)} files, loaded {total_transactions} transactions",
        "files_processed": len(csv_files),
        "total_transactions": total_transactions,
        "results": results
    }
