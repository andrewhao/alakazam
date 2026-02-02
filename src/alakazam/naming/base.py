"""Base class for naming strategies."""

from abc import ABC, abstractmethod
from typing import Dict


class NamingStrategy(ABC):
    """
    Abstract base class for filename generation strategies.

    A naming strategy takes analysis results and generates a new filename.
    """

    @abstractmethod
    def generate_filename(self, analysis: Dict, original_name: str) -> str:
        """
        Generate new filename from analysis results.

        Args:
            analysis: Analysis dictionary from DocumentAnalyzer
            original_name: Original filename (for extension, fallback)

        Returns:
            New filename string

        Example:
            Input:
                analysis = {
                    "document_date": "2024-01-15",
                    "description": "Acme Corp Invoice"
                }
                original_name = "scan_001.pdf"

            Output:
                "2024-01-15 Acme Corp Invoice.pdf"
        """
        pass

    @abstractmethod
    def validate(self, filename: str) -> bool:
        """
        Validate generated filename.

        Args:
            filename: Filename to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
