"""Repository layer for Vocabulator.

This module provides repository pattern implementations for data access.
"""

from src.data.repositories.base_repository import BaseRepository
from src.data.repositories.student_repository import StudentRepository
from src.data.repositories.recommendation_repository import RecommendationRepository

__all__ = [
    "BaseRepository",
    "StudentRepository",
    "RecommendationRepository",
]

