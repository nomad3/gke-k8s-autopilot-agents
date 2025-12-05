"""
PDF Ingestion API Endpoints
Upload and process PDF reports into Snowflake Bronze layer
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional, List
from datetime import datetime
from loguru import logger

from ..services.pdf_ingestion import PDFIngestionService
from ..connectors.snowflake import SnowflakeConnector
from ..core.config import get_settings
from ..core.security import verify_api_key

router = APIRouter(prefix="/api/v1/pdf", tags=["PDF Ingestion"])
settings = get_settings()


def get_pdf_service() -> PDFIngestionService:
    """Dependency to get PDF ingestion service"""
    snowflake_connector = SnowflakeConnector()
    openai_key = settings.openai_api_key if hasattr(settings, 'openai_api_key') else None
    return PDFIngestionService(snowflake_connector, settings, openai_key)


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(..., description="PDF file to upload"),
    report_type: Optional[str] = Form(None, description="Report type: day_sheet, deposit_slip, pay_reconciliation, operations_report"),
    practice_location: Optional[str] = Form(None, description="Practice location name"),
    use_ai: bool = Form(True, description="Use AI extraction (requires OpenAI API key)"),
    batch_id: Optional[str] = Form(None, description="Batch ID for grouping uploads"),
    uploaded_by: Optional[str] = Form(None, description="User who uploaded the file"),
    api_key: str = Depends(verify_api_key),
    service: PDFIngestionService = Depends(get_pdf_service)
):
    """
    Upload and ingest a single PDF file

    - **file**: PDF file (multipart/form-data)
    - **report_type**: Optional type hint (day_sheet, deposit_slip, etc.)
    - **practice_location**: Practice location (e.g., "Eastlake", "Torrey Pines")
    - **use_ai**: Whether to use AI extraction (default: true)
    - **batch_id**: Optional batch identifier
    - **uploaded_by**: User identifier

    Returns extracted data and Bronze layer record ID
    """
    # Validate file
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    logger.info(f"Received PDF upload: {file.filename}")

    try:
        # Read PDF bytes
        pdf_bytes = await file.read()

        # Validate size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50 MB
        if len(pdf_bytes) > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is 50MB, got {len(pdf_bytes) / 1024 / 1024:.1f}MB"
            )

        # Ingest PDF
        result = await service.ingest_pdf(
            pdf_bytes=pdf_bytes,
            file_name=file.filename,
            report_type=report_type,
            practice_location=practice_location,
            uploaded_by=uploaded_by or "api_upload",
            use_ai=use_ai,
            batch_id=batch_id,
        )

        if result.get("success"):
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    **result
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    **result
                }
            )

    except Exception as e:
        logger.error(f"Error processing PDF upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/batch")
async def upload_pdf_batch(
    files: List[UploadFile] = File(..., description="Multiple PDF files"),
    report_type: Optional[str] = Form(None, description="Default report type for all files"),
    practice_location: Optional[str] = Form(None, description="Default practice location for all files"),
    use_ai: bool = Form(True, description="Use AI extraction"),
    uploaded_by: Optional[str] = Form(None, description="User who uploaded the files"),
    api_key: str = Depends(verify_api_key),
    service: PDFIngestionService = Depends(get_pdf_service)
):
    """
    Upload and ingest multiple PDF files in a batch

    - **files**: Multiple PDF files (multipart/form-data)
    - **report_type**: Default type for all files (can be overridden per file)
    - **practice_location**: Default location for all files
    - **use_ai**: Whether to use AI extraction
    - **uploaded_by**: User identifier

    Returns batch ingestion results
    """
    batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"Received batch PDF upload: {len(files)} files, batch_id={batch_id}")

    pdfs = []
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            logger.warning(f"Skipping non-PDF file: {file.filename}")
            continue

        try:
            pdf_bytes = await file.read()

            # Validate size
            max_size = 50 * 1024 * 1024  # 50 MB
            if len(pdf_bytes) > max_size:
                logger.warning(f"Skipping file {file.filename}: too large ({len(pdf_bytes) / 1024 / 1024:.1f}MB)")
                continue

            pdfs.append({
                "pdf_bytes": pdf_bytes,
                "file_name": file.filename,
                "report_type": report_type,
                "practice_location": practice_location,
            })

        except Exception as e:
            logger.error(f"Error reading file {file.filename}: {e}")
            continue

    if not pdfs:
        raise HTTPException(status_code=400, detail="No valid PDF files provided")

    try:
        result = await service.ingest_pdf_batch(
            pdfs=pdfs,
            batch_id=batch_id,
            uploaded_by=uploaded_by or "api_batch_upload",
            use_ai=use_ai,
        )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                **result
            }
        )

    except Exception as e:
        logger.error(f"Error processing batch upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_ingestion_stats(
    practice_location: Optional[str] = None,
    report_type: Optional[str] = None,
    days: int = 30,
    api_key: str = Depends(verify_api_key),
    service: PDFIngestionService = Depends(get_pdf_service)
):
    """
    Get PDF ingestion statistics

    - **practice_location**: Filter by practice (optional)
    - **report_type**: Filter by report type (optional)
    - **days**: Number of days to look back (default: 30)

    Returns ingestion statistics including record counts, upload frequency, etc.
    """
    try:
        stats = await service.get_ingestion_stats(
            practice_location=practice_location,
            report_type=report_type,
            days=days
        )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                **stats
            }
        )

    except Exception as e:
        logger.error(f"Error getting ingestion stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supported-types")
async def get_supported_report_types(
    api_key: str = Depends(verify_api_key)
):
    """
    Get list of supported PDF report types and their schemas

    Returns information about supported report types and what data is extracted
    """
    from ..parsers.pdf_extractor import PDFExtractor

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "supported_types": list(PDFExtractor.REPORT_TYPES.keys()),
            "report_descriptions": {
                report_type: schema.get("description")
                for report_type, schema in PDFExtractor.EXTRACTION_SCHEMAS.items()
            },
            "extraction_fields": PDFExtractor.EXTRACTION_SCHEMAS,
            "ai_extraction_available": hasattr(settings, 'openai_api_key') and settings.openai_api_key is not None,
        }
    )


@router.post("/extract-preview")
async def extract_pdf_preview(
    file: UploadFile = File(..., description="PDF file to preview"),
    report_type: Optional[str] = Form(None, description="Report type hint"),
    use_ai: bool = Form(False, description="Use AI extraction (costs API credits)"),
    api_key: str = Depends(verify_api_key),
    service: PDFIngestionService = Depends(get_pdf_service)
):
    """
    Preview PDF extraction without saving to database

    Useful for testing extraction accuracy before full ingestion

    - **file**: PDF file
    - **report_type**: Optional type hint
    - **use_ai**: Whether to use AI (default: false to save costs)

    Returns extracted data without persisting to Bronze layer
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    try:
        pdf_bytes = await file.read()

        # Just extract, don't persist
        extraction_result = service.pdf_extractor.extract_from_bytes(
            pdf_bytes=pdf_bytes,
            report_type=report_type,
            use_ai=use_ai
        )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "file_name": file.filename,
                "extraction_preview": extraction_result,
                "note": "This is a preview only. Data was not saved to database."
            }
        )

    except Exception as e:
        logger.error(f"Error previewing extraction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
