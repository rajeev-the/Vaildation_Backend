import io
import csv
from app.services.s3_service import S3Service


class FileService:

    @staticmethod
    def count_rows(filepath):
        """Count rows in a local file (legacy support)."""
        with open(
            filepath,
            "r",
            encoding="utf-8",
            errors="replace"
        ) as file:

            return max(
                sum(1 for _ in file) - 1,
                0
            )

    @staticmethod
    def count_rows_from_s3(s3_key: str) -> int:
        """
        Count rows in a CSV file stored in S3.

        Args:
            s3_key: S3 object key (path)

        Returns:
            Number of data rows (excluding header)
        """
        s3_service = S3Service()
        content = s3_service.download_file_bytes(s3_key)

        if not content:
            return 0

        try:
            # Decode bytes to string
            content_str = content.decode("utf-8", errors="replace")
            # Count lines, subtract 1 for header
            return max(sum(1 for _ in content_str.splitlines()) - 1, 0)
        except Exception:
            return 0

    @staticmethod
    def read_csv_from_s3(s3_key: str) -> list:
        """
        Read CSV file from S3 and return as list of dictionaries.

        Args:
            s3_key: S3 object key (path)

        Returns:
            List of row dictionaries
        """
        s3_service = S3Service()
        content = s3_service.download_file_bytes(s3_key)

        if not content:
            return []

        try:
            content_str = content.decode("utf-8", errors="replace")
            reader = csv.DictReader(io.StringIO(content_str))
            return list(reader)
        except Exception:
            return []
