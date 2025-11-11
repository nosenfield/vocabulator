"""Repository layer for Vocabulator.

This module provides repository pattern implementations for data access.
"""

from src.data.repositories.base_repository import BaseRepository
from src.data.repositories.student_repository import StudentRepository

__all__ = ["BaseRepository", "StudentRepository"]

