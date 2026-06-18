import uuid

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException,
    BackgroundTasks
)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.dependencies import get_db

from app.models.upload_session import UploadSession
from app.services.validation_service import ValidationService
from app.models.chunk import Chunk
from app.services.csv_export_service import CsvExportService
from app.services.s3_service import S3Service
from app.core.config import settings


router = APIRouter(
    prefix="/upload",
    tags=["Upload"]
)


@router.post("")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a CSV file to S3 and start validation process.
    
    Returns:
        Response with session_id and status polling URL
    """
    session_id = str(uuid.uuid4())
    
    # Generate S3 key for uploaded file
    s3_key = f"{settings.S3_UPLOADS_PREFIX}/{session_id}/{file.filename}"
    
    # Read file content
    content = await file.read()
    
    # Upload to S3
    s3_service = S3Service()
    upload_success = s3_service.upload_bytes(
        content=content,
        s3_key=s3_key,
        content_type="text/csv"
    )
    
    if not upload_success:
        raise HTTPException(
            status_code=500,
            detail="Failed to upload file to S3"
        )
    
    # Create upload session record
    session = UploadSession(
        id=session_id,
        original_filename=file.filename,
        file_size_bytes=len(content),
        status="pending"
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    # Schedule validation (pass S3 key instead of local filepath)
    background_tasks.add_task(ValidationService.validate_upload, session_id, s3_key)

    return {
        "session_id": session_id,
        "original_filename": file.filename,
        "file_size_bytes": len(content),
        "status": "pending",
        "message": "Upload received. Validation started.",
        "poll_status_url": f"/api/v1/upload/{session_id}/status"
    }



@router.get("/{session_id}/status")
async def get_status(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get upload session status and chunk information.
    
    Returns:
        Session status with total rows, valid/error counts, and chunk list
    """
    result = await db.execute(select(UploadSession).filter(UploadSession.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    chunks_res = await db.execute(select(Chunk).filter(Chunk.session_id == session_id))
    chunks = chunks_res.scalars().all()

    return {
        "session_id": session.id,
        "original_filename": session.original_filename,
        "status": session.status,
        "total_rows": session.total_rows,
        "valid_rows": session.valid_rows,
        "error_rows": session.error_rows,
        "chunks": [
            {
                "chunk_index": c.chunk_index,
                "row_count": c.row_count,
                "filename": c.filename
            }
            for c in chunks
        ]
    }


@router.get("/{session_id}/download/invalid")
async def download_invalid(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get presigned URL for downloading invalid rows CSV from S3.
    
    Returns:
        Presigned download URL
    """
    # Generate S3 key for invalid CSV
    s3_key = f"{settings.S3_OUTPUTS_PREFIX}/{session_id}_invalid.csv"
    
    # Check if file exists in S3
    s3_service = S3Service()
    if not s3_service.file_exists(s3_key):
        raise HTTPException(
            status_code=404,
            detail="Invalid rows file not found. No invalid rows or file not yet generated."
        )
    
    # Generate presigned URL
    presigned_url = s3_service.get_file_url(
        s3_key,
        expiration=settings.S3_PRESIGNED_URL_EXPIRATION
    )
    
    if not presigned_url:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate download URL"
        )
    
    return {
        "session_id": session_id,
        "file_type": "invalid_rows",
        "download_url": presigned_url,
        "expires_in_seconds": settings.S3_PRESIGNED_URL_EXPIRATION
    }


@router.get("/{session_id}/download/cleaned")
async def download_cleaned(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get presigned URL for downloading cleaned/validated rows CSV from S3.
    
    Returns:
        Presigned download URL
    """
    # Generate S3 key for cleaned CSV
    s3_key = f"{settings.S3_OUTPUTS_PREFIX}/{session_id}_cleaned.csv"
    
    # Check if file exists in S3
    s3_service = S3Service()
    if not s3_service.file_exists(s3_key):
        raise HTTPException(
            status_code=404,
            detail="Cleaned rows file not found. No valid rows or file not yet generated."
        )
    
    # Generate presigned URL
    presigned_url = s3_service.get_file_url(
        s3_key,
        expiration=settings.S3_PRESIGNED_URL_EXPIRATION
    )
    
    if not presigned_url:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate download URL"
        )
    
    return {
        "session_id": session_id,
        "file_type": "cleaned_rows",
        "download_url": presigned_url,
        "expires_in_seconds": settings.S3_PRESIGNED_URL_EXPIRATION
    }