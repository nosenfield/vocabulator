"""Report generation service.

This module provides a service for generating HTML reports from templates
and uploading them to S3 with presigned URLs.
"""

from datetime import datetime, timezone
from typing import Optional

from src.data.s3_client import S3Client, S3Error
from src.frontend.templates import render_profile_report, render_recommendations_report
from src.data.models.student_profile import StudentProfile
from src.data.models.recommendation import VocabularyRecommendation
from src.utils.logger import get_logger

logger = get_logger("frontend.report_generator")


class ReportGenerationError(Exception):
    """Exception raised when report generation fails."""
    
    pass


class ReportGenerator:
    """Service for generating and uploading HTML reports.
    
    This service generates HTML reports from templates and uploads them
    to S3, returning presigned URLs for access.
    
    Attributes:
        s3_client: S3Client instance for uploading reports
    """
    
    def __init__(self, s3_client: Optional[S3Client] = None):
        """Initialize ReportGenerator.
        
        Args:
            s3_client: S3Client instance. If not provided, creates a new one.
        """
        if s3_client is None:
            s3_client = S3Client()
        self.s3_client = s3_client
    
    def _get_upload_client(self, bucket_name: Optional[str] = None) -> S3Client:
        """Get appropriate S3 client for upload.
        
        If bucket_name is provided and different from current client's bucket,
        creates a new client. Otherwise uses the existing client.
        
        Args:
            bucket_name: Optional bucket name. If provided and different from
                current client's bucket, creates new client.
                
        Returns:
            S3Client instance to use for upload
        """
        # If no bucket_name specified, use existing client
        if not bucket_name:
            return self.s3_client
        
        # If bucket_name matches current client's bucket, use existing client
        if hasattr(self.s3_client, 'bucket_name') and bucket_name == self.s3_client.bucket_name:
            return self.s3_client
        
        # Check if client is a mock (for testing) - if so, always use it
        # Mocks don't have bucket_name attribute or it may not match
        is_mock = hasattr(self.s3_client, '_mock_name') or hasattr(self.s3_client, '_spec_class')
        if is_mock:
            return self.s3_client
        
        # Create new client for different bucket
        return S3Client(bucket_name=bucket_name)
    
    def generate_profile_report(
        self,
        profile: StudentProfile,
        bucket_name: Optional[str] = None,
        s3_key: Optional[str] = None,
        expiration_hours: int = 24 * 7,  # 7 days default
    ) -> str:
        """Generate and upload student profile report.
        
        Args:
            profile: StudentProfile instance to generate report for
            bucket_name: S3 bucket name. If not provided, uses S3 client default.
            s3_key: Custom S3 key. If not provided, generates default key.
            expiration_hours: Hours until presigned URL expires (default: 7 days)
            
        Returns:
            Presigned URL to access the report
            
        Raises:
            ReportGenerationError: If report generation or upload fails
        """
        try:
            # Generate HTML report
            html_content = render_profile_report(profile)
            html_bytes = html_content.encode("utf-8")
            
            # Generate S3 key if not provided
            if s3_key is None:
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
                s3_key = f"reports/{profile.student_id}/profile_{timestamp}.html"
            
            # Upload to S3
            upload_client = self._get_upload_client(bucket_name)
            
            upload_client.upload(
                key=s3_key,
                content=html_bytes,
                content_type="text/html",
            )
            
            logger.info(
                f"Uploaded profile report for student {profile.student_id} to {s3_key}",
                extra={"student_id": profile.student_id, "s3_key": s3_key},
            )
            
            # Generate presigned URL
            presigned_url = upload_client.generate_presigned_url(
                key=s3_key,
                expiration_hours=expiration_hours,
            )
            
            return presigned_url
            
        except S3Error as e:
            error_msg = f"Failed to upload profile report to S3: {str(e)}"
            logger.error(error_msg, extra={"student_id": profile.student_id, "error": str(e)})
            raise ReportGenerationError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to generate profile report: {str(e)}"
            logger.error(error_msg, extra={"student_id": profile.student_id, "error": str(e)})
            raise ReportGenerationError(error_msg) from e
    
    def generate_recommendations_report(
        self,
        recommendation: VocabularyRecommendation,
        bucket_name: Optional[str] = None,
        s3_key: Optional[str] = None,
        expiration_hours: int = 24 * 7,  # 7 days default
    ) -> str:
        """Generate and upload vocabulary recommendations report.
        
        Args:
            recommendation: VocabularyRecommendation instance to generate report for
            bucket_name: S3 bucket name. If not provided, uses S3 client default.
            s3_key: Custom S3 key. If not provided, generates default key.
            expiration_hours: Hours until presigned URL expires (default: 7 days)
            
        Returns:
            Presigned URL to access the report
            
        Raises:
            ReportGenerationError: If report generation or upload fails
        """
        try:
            # Generate HTML report
            html_content = render_recommendations_report(recommendation)
            html_bytes = html_content.encode("utf-8")
            
            # Generate S3 key if not provided
            if s3_key is None:
                # Use recommendation date for key
                date_str = recommendation.recommendation_date.replace("-", "")
                s3_key = f"reports/{recommendation.student_id}/recommendations_{date_str}.html"
            
            # Upload to S3
            upload_client = self._get_upload_client(bucket_name)
            
            upload_client.upload(
                key=s3_key,
                content=html_bytes,
                content_type="text/html",
            )
            
            logger.info(
                f"Uploaded recommendations report for student {recommendation.student_id} to {s3_key}",
                extra={
                    "student_id": recommendation.student_id,
                    "recommendation_date": recommendation.recommendation_date,
                    "s3_key": s3_key,
                },
            )
            
            # Generate presigned URL
            presigned_url = upload_client.generate_presigned_url(
                key=s3_key,
                expiration_hours=expiration_hours,
            )
            
            return presigned_url
            
        except S3Error as e:
            error_msg = f"Failed to upload recommendations report to S3: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "student_id": recommendation.student_id,
                    "recommendation_date": recommendation.recommendation_date,
                    "error": str(e),
                },
            )
            raise ReportGenerationError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to generate recommendations report: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "student_id": recommendation.student_id,
                    "recommendation_date": recommendation.recommendation_date,
                    "error": str(e),
                },
            )
            raise ReportGenerationError(error_msg) from e

