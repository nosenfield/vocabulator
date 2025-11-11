"""Vocabulary recommendation repository for DynamoDB operations.

This module provides a repository for managing vocabulary recommendations in DynamoDB,
extending the base repository pattern with recommendation-specific operations.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from boto3.dynamodb.conditions import Key

from src.data.models.recommendation import (
    VocabularyRecommendation,
    RecommendationStatus,
)
from src.data.repositories.base_repository import BaseRepository
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger("data.repositories.recommendation")


class RecommendationRepository(BaseRepository[VocabularyRecommendation]):
    """Repository for vocabulary recommendation operations.
    
    Provides CRUD operations and query methods for vocabulary recommendations.
    Uses DynamoDB table with partition key (student_id) and sort key (recommendation_date).
    Supports TTL for automatic expiration of old recommendations.
    """
    
    def __init__(self, table_name: Optional[str] = None):
        """Initialize recommendation repository.
        
        Args:
            table_name: Optional table name override. If not provided, uses
                configured table name from config.
        """
        if table_name is None:
            config = get_config()
            table_name = config.get_dynamodb_table_name("VocabularyRecommendations")
        
        super().__init__(table_name=table_name)
        logger.debug(f"Initialized RecommendationRepository for table: {table_name}")
    
    def _item_to_model(self, item: Dict) -> VocabularyRecommendation:
        """Convert DynamoDB item to VocabularyRecommendation model.
        
        Args:
            item: DynamoDB item dictionary
            
        Returns:
            VocabularyRecommendation instance
        """
        return VocabularyRecommendation.from_dict(item)
    
    def _model_to_item(self, model: VocabularyRecommendation) -> Dict:
        """Convert VocabularyRecommendation model to DynamoDB item.
        
        Args:
            model: VocabularyRecommendation instance
            
        Returns:
            Dictionary suitable for DynamoDB storage
        """
        item = model.to_dict()
        return item
    
    def _get_partition_key(self) -> str:
        """Get partition key attribute name.
        
        Returns:
            Partition key name: "student_id"
        """
        return "student_id"
    
    def _get_sort_key(self) -> Optional[str]:
        """Get sort key attribute name.
        
        Returns:
            Sort key name: "recommendation_date"
        """
        return "recommendation_date"
    
    def get(
        self,
        student_id: str,
        recommendation_date: str,
    ) -> Optional[VocabularyRecommendation]:
        """Get a recommendation by student ID and date.
        
        Args:
            student_id: Student identifier
            recommendation_date: Recommendation date (ISO 8601 date string)
            
        Returns:
            VocabularyRecommendation if found, None otherwise
        """
        return super().get(
            partition_value=student_id,
            sort_value=recommendation_date,
        )
    
    def create(self, recommendation: VocabularyRecommendation) -> VocabularyRecommendation:
        """Create a new vocabulary recommendation.
        
        Args:
            recommendation: VocabularyRecommendation instance to create
            
        Returns:
            Created VocabularyRecommendation instance
        """
        return super().create(recommendation)
    
    def delete(
        self,
        student_id: str,
        recommendation_date: str,
    ) -> None:
        """Delete a vocabulary recommendation.
        
        Args:
            student_id: Student identifier
            recommendation_date: Recommendation date (ISO 8601 date string)
        """
        super().delete(
            partition_value=student_id,
            sort_value=recommendation_date,
        )
        logger.debug(
            f"Deleted recommendation: {student_id} on {recommendation_date}"
        )
    
    def get_by_student(
        self,
        student_id: str,
        limit: Optional[int] = None,
    ) -> List[VocabularyRecommendation]:
        """Get all recommendations for a student.
        
        Args:
            student_id: Student identifier
            limit: Optional limit on number of results
            
        Returns:
            List of VocabularyRecommendation instances, ordered by date (newest first)
        """
        # Query by partition key (student_id)
        items = self.client.query(
            partition_key=self._get_partition_key(),
            partition_value=student_id,
            limit=limit,
        )
        
        # Sort by date (newest first)
        items.sort(key=lambda x: x.get("recommendation_date", ""), reverse=True)
        
        return [self._item_to_model(item) for item in items]
    
    def get_by_date_range(
        self,
        student_id: str,
        start_date: str,
        end_date: str,
        limit: Optional[int] = None,
    ) -> List[VocabularyRecommendation]:
        """Get recommendations for a student within a date range.
        
        Args:
            student_id: Student identifier
            start_date: Start date (ISO 8601 date string, inclusive)
            end_date: End date (ISO 8601 date string, inclusive)
            limit: Optional limit on number of results
            
        Returns:
            List of VocabularyRecommendation instances within date range
        """
        # Query by partition key with sort key range using key_condition_expression
        key_condition = Key(self._get_partition_key()).eq(student_id) & Key(
            self._get_sort_key()
        ).between(start_date, end_date)
        
        items = self.client.query(
            key_condition_expression=key_condition,
            limit=limit,
        )
        
        return [self._item_to_model(item) for item in items]
    
    def update_status(
        self,
        student_id: str,
        recommendation_date: str,
        status: RecommendationStatus,
    ) -> Optional[VocabularyRecommendation]:
        """Update the status of a recommendation.
        
        Args:
            student_id: Student identifier
            recommendation_date: Recommendation date (ISO 8601 date string)
            status: New status
            
        Returns:
            Updated VocabularyRecommendation instance, or None if not found
        """
        updated_item = self.client.update_item(
            partition_key=self._get_partition_key(),
            partition_value=student_id,
            sort_key=self._get_sort_key(),
            sort_value=recommendation_date,
            update_expression="SET #status = :status",
            expression_attribute_names={"#status": "status"},
            expression_attribute_values={":status": status.value},
            return_values="ALL_NEW",
        )
        
        if updated_item:
            return self._item_to_model(updated_item)
        return None
    
    def get_by_status(
        self,
        status: RecommendationStatus,
        limit: Optional[int] = None,
    ) -> List[VocabularyRecommendation]:
        """Get recommendations by status using GSI.
        
        Args:
            status: Status to query
            limit: Optional limit on number of results
            
        Returns:
            List of VocabularyRecommendation instances with the specified status
        """
        # Query using GSI
        items = self.client.query(
            key_condition_expression=Key("status").eq(status.value),
            index_name="status-recommendation_date-index",
            limit=limit,
        )
        
        return [self._item_to_model(item) for item in items]

