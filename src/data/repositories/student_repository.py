"""Student profile repository for DynamoDB operations.

This module provides a repository for managing student profiles in DynamoDB,
extending the base repository pattern with student-specific operations.
"""

from typing import Dict, List, Optional
from boto3.dynamodb.conditions import Key

from src.data.models.student_profile import StudentProfile, VocabularyEntry
from src.data.repositories.base_repository import BaseRepository
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger("data.repositories.student")


class StudentRepository(BaseRepository[StudentProfile]):
    """Repository for student profile operations.
    
    Provides CRUD operations and vocabulary management for student profiles.
    Uses DynamoDB table with partition key (student_id) and sort key (profile_version).
    """
    
    def __init__(self, table_name: Optional[str] = None):
        """Initialize student repository.
        
        Args:
            table_name: Optional table name override. If not provided, uses
                configured table name from config.
        """
        if table_name is None:
            config = get_config()
            table_name = config.get_dynamodb_table_name("StudentProfiles")
        
        super().__init__(table_name=table_name)
        logger.debug(f"Initialized StudentRepository for table: {table_name}")
    
    def _item_to_model(self, item: Dict) -> StudentProfile:
        """Convert DynamoDB item to StudentProfile model.
        
        Args:
            item: DynamoDB item dictionary
            
        Returns:
            StudentProfile instance
        """
        return StudentProfile.from_dict(item)
    
    def _model_to_item(self, model: StudentProfile) -> Dict:
        """Convert StudentProfile model to DynamoDB item.
        
        Args:
            model: StudentProfile instance
            
        Returns:
            Dictionary suitable for DynamoDB storage
        """
        item = model.to_dict()
        # Ensure DynamoDB-compatible types
        # Convert ISO strings back to numbers/timestamps as needed
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
            Sort key name: "profile_version"
        """
        return "profile_version"
    
    def get(self, student_id: str, profile_version: int = 1) -> Optional[StudentProfile]:
        """Get a student profile by ID.
        
        Args:
            student_id: Student identifier
            profile_version: Profile version (default: 1)
            
        Returns:
            StudentProfile if found, None otherwise
        """
        return super().get(
            partition_value=student_id,
            sort_value=profile_version,
        )
    
    def create(self, profile: StudentProfile) -> StudentProfile:
        """Create a new student profile.
        
        Args:
            profile: StudentProfile instance to create
            
        Returns:
            Created StudentProfile instance
        """
        # Ensure profile_version is set
        if profile.profile_version is None or profile.profile_version < 1:
            profile.profile_version = 1
        
        return super().create(profile)
    
    def update(self, profile: StudentProfile) -> Optional[StudentProfile]:
        """Update an existing student profile.
        
        Updates the profile and recalculates proficiency score.
        
        Args:
            profile: StudentProfile instance with updated data
            
        Returns:
            Updated StudentProfile instance
        """
        # Recalculate proficiency score
        profile.calculate_proficiency_score()
        
        # Update last_updated timestamp
        from datetime import datetime
        profile.last_updated = datetime.now()
        
        # Convert to item and update
        item = self._model_to_item(profile)
        
        # Build update expression
        update_expression_parts = []
        expression_attribute_names = {}
        expression_attribute_values = {}
        
        # Update vocabulary_list
        update_expression_parts.append("vocabulary_list = :vocab_list")
        expression_attribute_values[":vocab_list"] = item["vocabulary_list"]
        
        # Update proficiency_score
        update_expression_parts.append("proficiency_score = :prof_score")
        expression_attribute_values[":prof_score"] = item["proficiency_score"]
        
        # Update last_updated
        update_expression_parts.append("last_updated = :last_upd")
        expression_attribute_values[":last_upd"] = item["last_updated"]
        
        # Update metadata if it exists
        if "metadata" in item and item["metadata"]:
            update_expression_parts.append("metadata = :metadata")
            expression_attribute_values[":metadata"] = item["metadata"]
        
        update_expression = "SET " + ", ".join(update_expression_parts)
        
        updated_item = self.client.update_item(
            partition_key=self._get_partition_key(),
            partition_value=profile.student_id,
            sort_key=self._get_sort_key(),
            sort_value=profile.profile_version,
            update_expression=update_expression,
            expression_attribute_values=expression_attribute_values,
            return_values="ALL_NEW",
        )
        
        if updated_item:
            return self._item_to_model(updated_item)
        return None
    
    def delete(self, student_id: str, profile_version: int = 1) -> None:
        """Delete a student profile.
        
        Args:
            student_id: Student identifier
            profile_version: Profile version (default: 1)
        """
        super().delete(
            partition_value=student_id,
            sort_value=profile_version,
        )
        logger.debug(f"Deleted student profile: {student_id} v{profile_version}")
    
    def add_vocabulary(
        self,
        student_id: str,
        entry: VocabularyEntry,
        profile_version: int = 1,
    ) -> Optional[StudentProfile]:
        """Add vocabulary to a student profile.
        
        Retrieves the profile, adds the vocabulary entry (with deduplication),
        recalculates proficiency score, and saves the updated profile.
        
        Args:
            student_id: Student identifier
            entry: VocabularyEntry to add
            profile_version: Profile version (default: 1)
            
        Returns:
            Updated StudentProfile instance, or None if student not found
        """
        # Get current profile
        profile = self.get(student_id=student_id, profile_version=profile_version)
        if profile is None:
            logger.warning(f"Student profile not found: {student_id}")
            return None
        
        # Add vocabulary (handles deduplication)
        profile.add_vocabulary(entry)
        
        # Recalculate proficiency score
        profile.calculate_proficiency_score()
        
        # Update profile
        return self.update(profile)
    
    def list_by_grade_level(
        self,
        grade_level: int,
        limit: Optional[int] = None,
    ) -> List[StudentProfile]:
        """List students by grade level using GSI.
        
        Args:
            grade_level: Grade level to query (6, 7, or 8)
            limit: Optional limit on number of results
            
        Returns:
            List of StudentProfile instances
        """
        from boto3.dynamodb.conditions import Key
        
        # Query using GSI
        items = self.client.query(
            key_condition_expression=Key("grade_level").eq(grade_level),
            index_name="grade_level-proficiency_score-index",
            limit=limit,
        )
        
        return [self._item_to_model(item) for item in items]

