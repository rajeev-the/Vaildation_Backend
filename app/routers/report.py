from sqlalchemy import func, select
from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.dependencies import get_db
from app.models.upload_session import UploadSession

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)


@router.get("/summary")
async def summary(db: AsyncSession = Depends(get_db)):

    total_uploads_res = await db.execute(select(func.count()).select_from(UploadSession))
    total_uploads = total_uploads_res.scalar() or 0

    total_rows_res = await db.execute(select(func.sum(UploadSession.total_rows)))
    total_rows = total_rows_res.scalar() or 0

    valid_rows_res = await db.execute(select(func.sum(UploadSession.valid_rows)))
    valid_rows = valid_rows_res.scalar() or 0

    error_rows_res = await db.execute(select(func.sum(UploadSession.error_rows)))
    error_rows = error_rows_res.scalar() or 0

    return {
        "total_uploads": total_uploads,
        "total_rows_processed": total_rows,
        "total_valid_rows": valid_rows,
        "total_error_rows": error_rows,
    }