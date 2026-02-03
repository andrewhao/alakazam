"""Mock analyzer for testing Alakazam without AI API."""

from pathlib import Path
from typing import Dict, Optional
from alakazam.analyzers import DocumentAnalyzer


class MockAnalyzer(DocumentAnalyzer):
    """
    Mock analyzer that returns fake analysis data.

    Use this to test Alakazam without needing an AI API key.
    """

    async def analyze(self, document_path: Path) -> Optional[Dict]:
        """
        Return mock analysis data for any document.

        Args:
            document_path: Path to the PDF document

        Returns:
            Mock analysis dictionary with standard fields
        """
        # Extract some info from the filename for more realistic output
        filename = document_path.stem

        # Simple heuristics based on filename
        if "invoice" in filename.lower():
            doc_type = "invoice"
            description = f"Mock Invoice {filename}"
        elif "medical" in filename.lower() or "health" in filename.lower():
            doc_type = "medical_statement"
            description = f"Mock Medical Document {filename}"
        elif "tax" in filename.lower():
            doc_type = "tax_form"
            description = f"Mock Tax Document {filename}"
        else:
            doc_type = "receipt"
            description = f"Mock Document {filename}"

        return {
            "document_date": "2024-01-15",  # Mock date
            "document_type": doc_type,
            "new_filename": f"2024-01-15 {description}.pdf",
            "description": description,
            "metadata": {
                "analyzer": "mock",
                "confidence": 1.0,
                "original_filename": document_path.name
            }
        }

    def validate_config(self) -> bool:
        """Mock analyzer is always valid."""
        return True
