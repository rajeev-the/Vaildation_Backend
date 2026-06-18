from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.dependencies import get_db

from app.models.chunk import Chunk
from app.services.s3_service import S3Service
from app.core.config import settings


router = APIRouter(
    prefix="/upload",
    tags=["Chunks"]
)


@router.get("/{session_id}/chunks")
async def get_chunks(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get list of chunks for a session with download URLs.
    
    Returns:
        List of chunks with download URLs
    """
    res = await db.execute(select(Chunk).filter(Chunk.session_id == session_id))
    chunks = res.scalars().all()

    return {
        "session_id": session_id,
        "total_chunks": len(chunks),
        "chunks": [
            {
                "chunk_id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "filename": chunk.filename,
                "row_count": chunk.row_count,
                "file_size_bytes": chunk.file_size_bytes,
                "download_url": f"/api/v1/upload/{session_id}/chunks/{chunk.id}/download",
            }
            for chunk in chunks
        ],
    }


@router.get("/{session_id}/chunks/{chunk_id}/download")
async def download_chunk(
    session_id: str,
    chunk_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get presigned URL for downloading a chunk from S3.
    
    Returns:
        Presigned download URL
    """
    res = await db.execute(
        select(Chunk).filter(
            Chunk.id == chunk_id,
            Chunk.session_id == session_id
        )
    )

    chunk = res.scalar_one_or_none()

    if not chunk:
        raise HTTPException(
            status_code=404,
            detail=f"Chunk {chunk_id} not found for session {session_id}"
        )

    # Generate S3 key for the chunk
    s3_chunk_key = f"{settings.S3_CHUNKS_PREFIX}/{session_id}/{chunk.filename}"

    # Verify chunk exists in S3
    s3_service = S3Service()
    if not s3_service.file_exists(s3_chunk_key):
        raise HTTPException(
            status_code=404,
            detail=f"Chunk file not found in S3: {s3_chunk_key}"
        )

    # Generate presigned URL
    presigned_url = s3_service.get_file_url(
        s3_chunk_key,
        expiration=settings.S3_PRESIGNED_URL_EXPIRATION
    )

    if not presigned_url:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate download URL"
        )

    return {
        "session_id": session_id,
        "chunk_id": chunk.id,
        "chunk_index": chunk.chunk_index,
        "filename": chunk.filename,
        "row_count": chunk.row_count,
        "file_size_bytes": chunk.file_size_bytes,
        "download_url": presigned_url,
        "expires_in_seconds": settings.S3_PRESIGNED_URL_EXPIRATION
    }