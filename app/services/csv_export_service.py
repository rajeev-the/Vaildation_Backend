import csv
import io
import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.validated_row import ValidatedRow
from app.services.s3_service import S3Service
from app.core.config import settings

logger = logging.getLogger(__name__)


class CsvExportService:

    @staticmethod
    async def export_cleaned_csv(session_id: str, db: AsyncSession) -> str:
        """
        Export cleaned (valid) rows to S3 as CSV.
        
        Args:
            session_id: Unique session ID
            db: Database session
            
        Returns:
            S3 key (path) of the exported file, or None if no valid rows
        """
        result = await db.execute(
            select(ValidatedRow).filter(
                ValidatedRow.session_id == session_id,
                ValidatedRow.validation_status == "valid"
            )
        )

        rows = result.scalars().all()

        if not rows:
            logger.info(f"No cleaned rows found for session {session_id}")
            return None

        headers = rows[0].cleaned_data.keys()

        # Generate CSV content in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()

        for row in rows:
            writer.writerow(row.cleaned_data)

        # Get CSV content as bytes
        csv_content = output.getvalue().encode("utf-8")

        # Generate S3 key
        s3_key = f"{settings.S3_OUTPUTS_PREFIX}/{session_id}_cleaned.csv"

        # Upload to S3
        s3_service = S3Service()
        success = s3_service.upload_bytes(
            content=csv_content,
            s3_key=s3_key,
            content_type="text/csv"
        )

        if not success:
            logger.error(f"Failed to upload cleaned CSV to S3: {s3_key}")
            return None

        logger.info(f"Exported cleaned CSV to S3: {s3_key}")
        return s3_key

    @staticmethod
    async def export_invalid_csv(session_id: str, db: AsyncSession) -> str:
        """
        Export invalid rows to S3 as CSV.
        
        Args:
            session_id: Unique session ID
            db: Database session
            
        Returns:
            S3 key (path) of the exported file, or None if no invalid rows
        """
        result = await db.execute(
            select(ValidatedRow).filter(
                ValidatedRow.session_id == session_id,
                ValidatedRow.validation_status == "invalid"
            )
        )

        rows = result.scalars().all()

        if not rows:
            logger.info(f"No invalid rows found for session {session_id}")
            return None

        # Build headers from raw_data keys plus a `validation_errors` column
        raw_keys = set()
        for r in rows:
            if r.raw_data:
                raw_keys.update(r.raw_data.keys())

        headers = list(raw_keys)
        headers.append("validation_errors")

        # Generate CSV content in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()

        for row in rows:
            record = {}

            if row.raw_data:
                for k in raw_keys:
                    record[k] = row.raw_data.get(k, "")

            # Include validation errors as JSON string
            record["validation_errors"] = json.dumps(row.validation_errors or [])

            writer.writerow(record)

        # Get CSV content as bytes
        csv_content = output.getvalue().encode("utf-8")

        # Generate S3 key
        s3_key = f"{settings.S3_OUTPUTS_PREFIX}/{session_id}_invalid.csv"

        # Upload to S3
        s3_service = S3Service()
        success = s3_service.upload_bytes(
            content=csv_content,
            s3_key=s3_key,
            content_type="text/csv"
        )

        if not success:
            logger.error(f"Failed to upload invalid CSV to S3: {s3_key}")
            return None

        logger.info(f"Exported invalid CSV to S3: {s3_key}")
        return s3_key