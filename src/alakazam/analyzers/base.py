"""Base class for document analyzers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional


class DocumentAnalyzer(ABC):
    """
    Abstract base class for document analyzers.

    An analyzer reads a document and extracts metadata using AI or other methods.
    """

    @abstractmethod
    async def analyze(self, document_path: Path) -> Optional[Dict]:
        """
        Analyze a document and return metadata.

        Args:
            document_path: Path to the document to analyze

        Returns:
            Dictionary containing:
                - document_date: str (YYYY-MM-DD format)
                - document_type: str (category like "invoice", "medical_statement")
                - new_filename: str (suggested filename)
                - description: str (human-readable description)
                - metadata: dict (optional additional metadata)

            Returns None if analysis fails.

        Example:
            {
                "document_date": "2024-01-15",
                "document_type": "invoice",
                "new_filename": "2024-01-15 Acme Corp Invoice 12345.pdf",
                "description": "Invoice from Acme Corp",
                "metadata": {
                    "company": "Acme Corp",
                    "invoice_number": "12345",
                    "amount": "$150.00"
                }
            }
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate analyzer configuration.

        Returns:
            True if configuration is valid, False otherwise

        Raises:
            ConfigurationError: If configuration is invalid
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
