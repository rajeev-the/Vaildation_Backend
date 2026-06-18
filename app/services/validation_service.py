import csv
import uuid
import io
import logging
import traceback

from sqlalchemy import select

from app.validators.phone_validator import PhoneValidator
from app.validators.date_validator import DateValidator
from app.validators.integrity_validator import IntegrityValidator

from app.models.validated_row import ValidatedRow
from app.models.upload_session import UploadSession
from app.models.chunk import Chunk
from app.services.csv_export_service import CsvExportService
from app.services.chunk_service import ChunkService
from app.services.s3_service import S3Service

from app.db.database import SessionLocal


class ValidationService:

    @staticmethod
    async def validate_upload(session_id: str, s3_key: str):
        """
        Validate a CSV file uploaded to S3.
        
        Args:
            session_id: Unique session ID
            s3_key: S3 object key (path) of the uploaded file
        """
        logger = logging.getLogger(__name__)
        s3_service = S3Service()

        async with SessionLocal() as db:

            # load session
            try:
                res = await db.execute(select(UploadSession).filter(UploadSession.id == session_id))
                session = res.scalar_one_or_none()

                if not session:
                    logger.error("ValidationService: session not found %s", session_id)
                    return {"error": "session not found"}

            except Exception:
                logger.error("ValidationService: error loading session %s:\n%s", session_id, traceback.format_exc())
                return {"error": "db error"}

            # mark validating
            try:
                session.status = "validating"
                await db.commit()
            except Exception:
                logger.error("ValidationService: error setting validating status %s:\n%s", session_id, traceback.format_exc())

            valid_rows = 0
            error_rows = 0
            total_rows = 0

            try:
                # Download file content from S3
                file_content = s3_service.download_file_bytes(s3_key)
                
                if not file_content:
                    raise Exception(f"Failed to download file from S3: {s3_key}")
                
                # Decode bytes to string and read as CSV
                content_str = file_content.decode("utf-8", errors="replace")
                reader = csv.DictReader(io.StringIO(content_str))

                for row_index, row in enumerate(reader):
                    # normalize keys and strip string values
                    errors = []

                    if row.get("phone"):
                        pres = await PhoneValidator.validate(
                            row["phone"],
                            db
                        )
                        if pres.status == "invalid":
                            errors.append({
                                "field": "phone",
                                "message": pres.message
                            })
                        else:
                            row["phone"] = pres.cleaned

                    if row.get("order_date"):
                        dres = await DateValidator.validate(
                            row["order_date"],
                            db
                        )
                        if dres.is_invalid():
                            errors.append({
                                "field": "order_date",
                                "message": dres.message
                            })
                        else:
                            row["order_date"] = dres.cleaned

                    errors.extend(IntegrityValidator.validate(row))

                    status = "valid" if len(errors) == 0 else "invalid"

                    validated_row = ValidatedRow(
                        session_id=session_id,
                        chunk_index=0,
                        row_index=row_index,
                        raw_data=row,
                        
                        cleaned_data=row if status == "valid" else None,
                        validation_status=status,
                        validation_errors=errors,
                    )

                    db.add(validated_row)
                    total_rows += 1
                    if status == "valid":
                        valid_rows += 1
                    else:
                        error_rows += 1

                await db.commit()

            except Exception:
                logger.error("ValidationService: error processing file %s:\n%s", s3_key, traceback.format_exc())
                # mark failed and re-raise
                try:
                    session.status = "failed"
                    await db.commit()
                except Exception:
                    logger.error("ValidationService: error marking session failed %s:\n%s", session_id, traceback.format_exc())
                return {"error": "processing error"}

            # finalize session
            try:
                session.status = "validated"
                session.valid_rows = valid_rows
                session.error_rows = error_rows
                session.total_rows = total_rows
                await db.commit()
            except Exception:
                logger.error("ValidationService: error finalizing session %s:\n%s", session_id, traceback.format_exc())

            # EXPORT CLEAN CSV to S3
            cleaned_csv_s3_key = await CsvExportService.export_cleaned_csv(session_id=session_id, db=db)

            # EXPORT INVALID CSV to S3
            invalid_csv_s3_key = await CsvExportService.export_invalid_csv(session_id=session_id, db=db)

            # CHUNKING
            chunks = []
            if cleaned_csv_s3_key:
                chunks = await ChunkService.split_csv(session_id=session_id, s3_key=cleaned_csv_s3_key)

            # SAVE CHUNKS
            for chunk in chunks:
                chunk_id = str(uuid.uuid4())
                file_size = chunk.get("file_size") or chunk.get("file_size_bytes") or 0
                db.add(
                    Chunk(
                        id=chunk_id,
                        session_id=session_id,
                        chunk_index=chunk["chunk_index"],
                        filename=chunk["filename"],
                        row_start=chunk["row_start"],
                        row_end=chunk["row_end"],
                        row_count=chunk["row_count"],
                        file_size_bytes=file_size,
                    )
                )

            try:
                await db.commit()
            except Exception:
                logger.error("ValidationService: error saving chunks %s:\n%s", session_id, traceback.format_exc())

            return {"valid_rows": valid_rows, "error_rows": error_rows, "chunks_created": len(chunks)}