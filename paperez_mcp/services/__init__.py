"""
Service layer for PaperezMCP - business logic abstraction.
"""

from .paper_processor import process_papers
from .search_service import SearchOrchestrationService

__all__ = ["process_papers", "SearchOrchestrationService"]
