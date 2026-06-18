import logging
import io
from typing import Optional, BinaryIO
from botocore.exceptions import ClientError
import boto3
from app.core.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """
    Reusable S3 service for managing file operations with AWS S3.
    Provides methods for uploading, downloading, listing, and deleting files.
    """

    def __init__(self):
        """Initialize S3 client with AWS credentials from settings."""
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        self.bucket_name = settings.AWS_S3_BUCKET

    def upload_file(self, local_path: str, s3_key: str) -> bool:
        """
        Upload a file from local filesystem to S3.

        Args:
            local_path: Path to local file
            s3_key: S3 object key (path)

        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.upload_file(local_path, self.bucket_name, s3_key)
            logger.info(f"Uploaded {local_path} to s3://{self.bucket_name}/{s3_key}")
            return True
        except ClientError as e:
            logger.error(
                f"Error uploading {local_path} to S3: {e}"
            )
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error uploading file: {e}"
            )
            return False

    def upload_bytes(
        self, content: bytes, s3_key: str, content_type: str = "text/csv"
    ) -> bool:
        """
        Upload bytes content to S3.

        Args:
            content: Bytes to upload
            s3_key: S3 object key (path)
            content_type: MIME type of the file

        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content,
                ContentType=content_type,
            )
            logger.info(f"Uploaded bytes to s3://{self.bucket_name}/{s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Error uploading bytes to S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading bytes: {e}")
            return False

    def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        Download a file from S3 to local filesystem.

        Args:
            s3_key: S3 object key (path)
            local_path: Path to save downloaded file

        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            logger.info(f"Downloaded s3://{self.bucket_name}/{s3_key} to {local_path}")
            return True
        except ClientError as e:
            logger.error(f"Error downloading from S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading file: {e}")
            return False

    def download_file_bytes(self, s3_key: str) -> Optional[bytes]:
        """
        Download a file from S3 as bytes.

        Args:
            s3_key: S3 object key (path)

        Returns:
            File content as bytes, or None if error
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            content = response["Body"].read()
            logger.info(f"Downloaded bytes from s3://{self.bucket_name}/{s3_key}")
            return content
        except ClientError as e:
            logger.error(f"Error downloading bytes from S3: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading bytes: {e}")
            return None

    def get_file_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for downloading a file from S3.

        Args:
            s3_key: S3 object key (path)
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL string, or None if error
        """
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expiration,
            )
            logger.info(f"Generated presigned URL for s3://{self.bucket_name}/{s3_key}")
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL: {e}")
            return None

    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.

        Args:
            s3_key: S3 object key (path)

        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Deleted s3://{self.bucket_name}/{s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting from S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting file: {e}")
            return False

    def file_exists(self, s3_key: str) -> bool:
        """
        Check if a file exists in S3.

        Args:
            s3_key: S3 object key (path)

        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"File exists: s3://{self.bucket_name}/{s3_key}")
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                logger.info(f"File not found: s3://{self.bucket_name}/{s3_key}")
                return False
            logger.error(f"Error checking file existence: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking file existence: {e}")
            return False

    def list_files(self, prefix: str) -> list:
        """
        List files in S3 with a given prefix.

        Args:
            prefix: S3 prefix to search under

        Returns:
            List of file keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix
            )
            files = [obj["Key"] for obj in response.get("Contents", [])]
            logger.info(f"Listed {len(files)} files with prefix: {prefix}")
            return files
        except ClientError as e:
            logger.error(f"Error listing files: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing files: {e}")
            return []

    def get_file_size(self, s3_key: str) -> Optional[int]:
        """
        Get the size of a file in S3.

        Args:
            s3_key: S3 object key (path)

        Returns:
            File size in bytes, or None if error
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            size = response["ContentLength"]
            logger.info(
                f"File size for s3://{self.bucket_name}/{s3_key}: {size} bytes"
            )
            return size
        except ClientError as e:
            logger.error(f"Error getting file size: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting file size: {e}")
            return None
