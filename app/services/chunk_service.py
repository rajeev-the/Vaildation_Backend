import csv
import io
import math
import logging
import os

from app.core.config import settings
from app.services.s3_service import S3Service

logger = logging.getLogger(__name__)


class ChunkService:

    CHUNK_THRESHOLD = 10000

    @staticmethod
    async def split_csv(
        session_id: str,
        s3_key: str
    ):
        """
        Split a CSV file stored in S3 into chunks.
        
        Args:
            session_id: Unique session ID
            s3_key: S3 object key (path) of the CSV file
            
        Returns:
            List of chunk metadata dictionaries
        """
        s3_service = S3Service()
        
        # Download file content from S3
        content = s3_service.download_file_bytes(s3_key)
        
        if not content:
            logger.error(f"Failed to download file from S3: {s3_key}")
            return []
        
        # Count rows in the file
        total_rows = ChunkService.count_rows_from_bytes(content)

        if total_rows == 0:
            logger.info(f"No rows found in file: {s3_key}")
            return []

        if total_rows <= ChunkService.CHUNK_THRESHOLD:
            return await ChunkService.create_single_chunk(
                session_id,
                content,
                total_rows
            )

        return await ChunkService.create_multiple_chunks(
            session_id,
            content,
            total_rows
        )

    @staticmethod
    def count_rows_from_bytes(content: bytes) -> int:
        """
        Count rows in CSV content from bytes.
        
        Args:
            content: CSV file content as bytes
            
        Returns:
            Number of data rows (excluding header)
        """
        try:
            content_str = content.decode("utf-8", errors="replace")
            return max(sum(1 for _ in content_str.splitlines()) - 1, 0)
        except Exception:
            return 0

    @staticmethod
    async def create_single_chunk(
        session_id: str,
        content: bytes,
        total_rows: int
    ) -> list:
        """
        Create a single chunk from CSV content and upload to S3.
        
        Args:
            session_id: Unique session ID
            content: CSV file content as bytes
            total_rows: Total number of data rows
            
        Returns:
            List with single chunk metadata dictionary
        """
        s3_service = S3Service()
        
        chunk_name = f"{session_id[:8]}_chunk_0.csv"
        s3_chunk_key = f"{settings.S3_CHUNKS_PREFIX}/{session_id}/{chunk_name}"
        
        # Upload chunk to S3
        success = s3_service.upload_bytes(
            content=content,
            s3_key=s3_chunk_key,
            content_type="text/csv"
        )
        
        if not success:
            logger.error(f"Failed to upload chunk to S3: {s3_chunk_key}")
            return []
        
        # Get file size from S3
        file_size = s3_service.get_file_size(s3_chunk_key) or len(content)
        
        logger.info(f"Created single chunk: {s3_chunk_key}")
        
        return [{
            "chunk_index": 0,
            "filename": chunk_name,
            "row_start": 0,
            "row_end": total_rows - 1,
            "row_count": total_rows,
            "file_size": file_size,
            "s3_key": s3_chunk_key
        }]

    @staticmethod
    async def create_multiple_chunks(
        session_id: str,
        content: bytes,
        total_rows: int,
        threshold: int = 10000
    ) -> list:
        """
        Split CSV content into multiple chunks and upload to S3.
        
        Args:
            session_id: Unique session ID
            content: CSV file content as bytes
            total_rows: Total number of data rows
            threshold: Maximum rows per chunk (default: 10000)
            
        Returns:
            List of chunk metadata dictionaries
        """
        s3_service = S3Service()
        chunks = []
        
        num_chunks = math.ceil(total_rows / threshold)
        rows_per_chunk = math.ceil(total_rows / num_chunks)
        
        content_str = content.decode("utf-8", errors="replace")
        reader = csv.reader(io.StringIO(content_str))
        
        # Read header
        header = next(reader)
        
        for chunk_index in range(num_chunks):
            chunk_name = f"{session_id[:8]}_chunk_{chunk_index}.csv"
            s3_chunk_key = f"{settings.S3_CHUNKS_PREFIX}/{session_id}/{chunk_name}"
            
            start_row = chunk_index * rows_per_chunk
            rows_written = 0
            
            # Build chunk content in memory
            chunk_output = io.StringIO()
            writer = csv.writer(chunk_output)
            writer.writerow(header)
            
            while rows_written < rows_per_chunk:
                try:
                    row = next(reader)
                    writer.writerow(row)
                    rows_written += 1
                except StopIteration:
                    break
            
            # Convert chunk to bytes
            chunk_content = chunk_output.getvalue().encode("utf-8")
            
            # Upload chunk to S3
            success = s3_service.upload_bytes(
                content=chunk_content,
                s3_key=s3_chunk_key,
                content_type="text/csv"
            )
            
            if not success:
                logger.error(f"Failed to upload chunk to S3: {s3_chunk_key}")
                continue
            
            # Get file size from S3
            file_size = s3_service.get_file_size(s3_chunk_key) or len(chunk_content)
            
            chunks.append({
                "chunk_index": chunk_index,
                "filename": chunk_name,
                "row_start": start_row,
                "row_end": start_row + rows_written - 1,
                "row_count": rows_written,
                "file_size": file_size,
                "s3_key": s3_chunk_key
            })
            
            logger.info(f"Created chunk {chunk_index}: {s3_chunk_key}")
        
        return chunks


