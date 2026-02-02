"""Document type registry with adaptive suggestions."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

from alakazam.types.builtin import BUILTIN_TYPES


@dataclass
class DocumentType:
    """Document type definition."""

    name: str
    description: str
    is_standard: bool = True
    count: int = 0
    first_seen: datetime = field(default_factory=datetime.now)
    examples: List[str] = field(default_factory=list)


class TypeRegistry:
    """
    Registry for document types with adaptive suggestions.

    Tracks both standard types and AI-suggested new types.
    """

    def __init__(self, standard_types: List[str] = None):
        """
        Initialize type registry.

        Args:
            standard_types: List of standard type names (uses BUILTIN_TYPES if None)
        """
        self.standard_types = standard_types or BUILTIN_TYPES.copy()
        self.suggested_types: Dict[str, DocumentType] = {}

    def is_standard(self, type_name: str) -> bool:
        """Check if type is in standard list."""
        return type_name in self.standard_types

    def register_suggestion(self, type_name: str, example: str) -> None:
        """
        Register a new type suggestion.

        Args:
            type_name: Name of the suggested type
            example: Example filename using this type
        """
        if type_name in self.standard_types:
            # Already standard, no need to track
            return

        if type_name not in self.suggested_types:
            self.suggested_types[type_name] = DocumentType(
                name=type_name,
                description=f"AI-suggested type",
                is_standard=False,
                count=0,
                first_seen=datetime.now(),
                examples=[],
            )

        # Increment count
        self.suggested_types[type_name].count += 1

        # Keep up to 3 examples
        if len(self.suggested_types[type_name].examples) < 3:
            self.suggested_types[type_name].examples.append(example)

    def get_recommendations(self, threshold: int = 3) -> Dict[str, DocumentType]:
        """
        Get types recommended for promotion to standard.

        Args:
            threshold: Minimum usage count to recommend (default 3)

        Returns:
            Dictionary of type_name -> DocumentType for recommended types
        """
        return {
            name: dtype
            for name, dtype in self.suggested_types.items()
            if dtype.count >= threshold
        }

    def get_all_suggested(self) -> Dict[str, DocumentType]:
        """Get all suggested types."""
        return self.suggested_types.copy()

    def promote_to_standard(self, type_name: str) -> bool:
        """
        Promote a suggested type to standard.

        Args:
            type_name: Name of type to promote

        Returns:
            True if promoted, False if already standard or not found
        """
        if type_name in self.standard_types:
            return False

        if type_name not in self.suggested_types:
            return False

        self.standard_types.append(type_name)
        # Keep in suggested_types for historical tracking
        self.suggested_types[type_name].is_standard = True

        return True

    def __repr__(self) -> str:
        return (
            f"TypeRegistry(standard={len(self.standard_types)}, "
            f"suggested={len(self.suggested_types)})"
        )
