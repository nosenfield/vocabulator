"""S3 client wrapper with error handling and path management.

This module provides a high-level interface for S3 operations with
automatic multipart upload for large files, presigned URL generation,
and consistent error handling.
"""

import io
from typing import BinaryIO, Dict, List, Optional
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from botocore.client import BaseClient

from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger("data.s3")


class S3Error(Exception):
    """Base exception for S3 operations."""
    
    pass


class S3Client:
    """S3 client wrapper with error handling and path management.
    
    This client provides a high-level interface for S3 operations with
    automatic multipart upload for large files, presigned URL generation,
    and consistent error handling.
    
    Attributes:
        bucket_name: Name of the S3 bucket
        client: boto3 S3 client instance
    """
    
    def __init__(self, bucket_name: Optional[str] = None):
        """Initialize S3 client.
        
        Args:
            bucket_name: Name of the S3 bucket. If not provided, uses
                configured bucket name from config.
                
        Raises:
            S3Error: If bucket cannot be accessed
        """
        config = get_config()
        
        if bucket_name is None:
            bucket_name = config.s3_bucket_name
        
        self.bucket_name = bucket_name
        
        # Configure boto3 with retry logic
        boto_config = Config(
            region_name=config.aws_region,
            retries={
                "max_attempts": 3,
                "mode": "adaptive",
            },
            max_pool_connections=50,
        )
        
        # Create S3 client
        endpoint_url = config.get_aws_endpoint_url()
        if endpoint_url:
            # LocalStack requires explicit credentials
            # Only pass credentials if they're provided (for local development)
            client_kwargs = {
                "endpoint_url": endpoint_url,
                "config": boto_config,
            }
            if config.aws_access_key_id and config.aws_secret_access_key:
                client_kwargs["aws_access_key_id"] = config.aws_access_key_id
                client_kwargs["aws_secret_access_key"] = config.aws_secret_access_key
            self.client: BaseClient = boto3.client("s3", **client_kwargs)
        else:
            # Production: Use IAM roles (no explicit credentials)
            self.client = boto3.client("s3", config=boto_config)
        
        logger.debug(f"Initialized S3 client for bucket: {bucket_name}")
    
    def upload(
        self,
        key: str,
        content: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        multipart_threshold: int = 5 * 1024 * 1024,  # 5MB default
    ) -> None:
        """Upload content to S3.
        
        Automatically uses multipart upload for large files.
        
        Args:
            key: S3 object key (path)
            content: Content to upload (bytes)
            content_type: Optional content type (e.g., "text/plain")
            metadata: Optional metadata dictionary
            multipart_threshold: Size threshold for multipart upload (default: 5MB)
            
        Raises:
            S3Error: If upload fails
        """
        try:
            extra_args = {}
            
            if content_type:
                extra_args["ContentType"] = content_type
            
            if metadata:
                extra_args["Metadata"] = metadata
            
            # Server-side encryption by default
            extra_args["ServerSideEncryption"] = "AES256"
            
            # Use multipart upload for large files
            if len(content) >= multipart_threshold:
                from boto3.s3.transfer import TransferConfig
                
                transfer_config = TransferConfig(
                    multipart_threshold=multipart_threshold,
                    multipart_chunksize=multipart_threshold,
                )
                
                self.client.upload_fileobj(
                    io.BytesIO(content),
                    self.bucket_name,
                    key,
                    ExtraArgs=extra_args,
                    Config=transfer_config,
                )
            else:
                # Regular upload for small files
                self.client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=content,
                    **extra_args,
                )
            
            logger.debug(f"Uploaded file to s3://{self.bucket_name}/{key}")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            raise S3Error(f"Failed to upload file '{key}': {error_code} - {e}") from e
        except Exception as e:
            logger.error(f"Error uploading file to {self.bucket_name}/{key}: {e}")
            raise S3Error(f"Failed to upload file '{key}': {e}") from e
    
    def download(self, key: str) -> bytes:
        """Download content from S3.
        
        Args:
            key: S3 object key (path)
            
        Returns:
            File content as bytes
            
        Raises:
            S3Error: If download fails or file not found
        """
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            content = response["Body"].read()
            logger.debug(f"Downloaded file from s3://{self.bucket_name}/{key}")
            return content
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                raise S3Error(f"File not found: '{key}'") from e
            raise S3Error(f"Failed to download file '{key}': {error_code} - {e}") from e
        except Exception as e:
            logger.error(f"Error downloading file from {self.bucket_name}/{key}: {e}")
            raise S3Error(f"Failed to download file '{key}': {e}") from e
    
    def list(self, prefix: str = "", limit: Optional[int] = None) -> List[str]:
        """List objects in S3 bucket with given prefix.
        
        Args:
            prefix: Prefix to filter objects (e.g., "transcripts/raw/STU-001/")
            limit: Optional limit on number of results
            
        Returns:
            List of object keys matching the prefix
        """
        try:
            keys = []
            paginator = self.client.get_paginator("list_objects_v2")
            
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=limit,
            )
            
            for page in page_iterator:
                if "Contents" in page:
                    keys.extend([obj["Key"] for obj in page["Contents"]])
                
                if limit and len(keys) >= limit:
                    break
            
            logger.debug(f"Listed {len(keys)} objects with prefix '{prefix}'")
            return keys
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            raise S3Error(f"Failed to list objects with prefix '{prefix}': {error_code} - {e}") from e
        except Exception as e:
            logger.error(f"Error listing objects in {self.bucket_name} with prefix '{prefix}': {e}")
            raise S3Error(f"Failed to list objects: {e}") from e
    
    def delete(self, key: str) -> None:
        """Delete an object from S3.
        
        Args:
            key: S3 object key (path)
            
        Raises:
            S3Error: If deletion fails
        """
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.debug(f"Deleted file s3://{self.bucket_name}/{key}")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                raise S3Error(f"File not found: '{key}'") from e
            raise S3Error(f"Failed to delete file '{key}': {error_code} - {e}") from e
        except Exception as e:
            logger.error(f"Error deleting file from {self.bucket_name}/{key}: {e}")
            raise S3Error(f"Failed to delete file '{key}': {e}") from e
    
    def generate_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
        http_method: str = "GET",
    ) -> str:
        """Generate a presigned URL for secure temporary access.
        
        Args:
            key: S3 object key (path)
            expiration: URL expiration time in seconds (default: 1 hour)
            http_method: HTTP method for the URL (default: "GET")
            
        Returns:
            Presigned URL string
        """
        try:
            url = self.client.generate_presigned_url(
                "get_object" if http_method == "GET" else "put_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expiration,
            )
            logger.debug(f"Generated presigned URL for {key} (expires in {expiration}s)")
            return url
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            raise S3Error(f"Failed to generate presigned URL for '{key}': {error_code} - {e}") from e
        except Exception as e:
            logger.error(f"Error generating presigned URL for {self.bucket_name}/{key}: {e}")
            raise S3Error(f"Failed to generate presigned URL: {e}") from e
    
    def build_path(
        self,
        category: str,
        student_id: Optional[str] = None,
        subcategory: Optional[str] = None,
        filename: str = "",
    ) -> str:
        """Build S3 path according to bucket structure.
        
        Path structure:
        - transcripts/raw/{student_id}/{filename}
        - transcripts/processed/{student_id}/{filename}
        - writing-samples/raw/{student_id}/{filename}
        - writing-samples/processed/{student_id}/{filename}
        - reports/{student_id}/{filename}
        
        Args:
            category: Main category (transcripts, writing-samples, reports)
            student_id: Optional student identifier
            subcategory: Optional subcategory (raw, processed)
            filename: Filename
            
        Returns:
            S3 key (path)
        """
        parts = [category]
        
        if subcategory:
            parts.append(subcategory)
        
        if student_id:
            parts.append(student_id)
        
        if filename:
            parts.append(filename)
        
        return "/".join(parts)

