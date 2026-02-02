"""ISO date naming strategy: YYYY-MM-DD <description>.ext"""

import re
from pathlib import Path
from typing import Dict

from alakazam.naming.base import NamingStrategy


class ISODateNaming(NamingStrategy):
    """
    ISO date naming strategy: YYYY-MM-DD <description>.ext

    Generates filenames in the format:
        2024-01-15 Document Description.pdf

    Features:
        - ISO 8601 date format for sortability
        - Space-separated for readability
        - Extension preserved
        - Length limiting with intelligent truncation
    """

    # Invalid filename characters across platforms
    INVALID_CHARS = '<>:"/\\|?*'

    def __init__(self, max_length: int = 80, title_case: bool = True):
        """
        Initialize ISO date naming strategy.

        Args:
            max_length: Maximum filename length (default 80)
            title_case: Whether to use title case for description (default True)
        """
        self.max_length = max_length
        self.title_case = title_case
        self._pattern = re.compile(r'^\d{4}-\d{2}-\d{2} .+\.\w+$')

    def generate_filename(self, analysis: Dict, original_name: str) -> str:
        """Generate filename in YYYY-MM-DD format."""
        date = analysis['document_date']
        description = analysis.get('description', Path(original_name).stem)
        ext = Path(original_name).suffix

        # Clean description
        description = self._clean_description(description)

        # Apply title case if requested
        if self.title_case:
            description = self._to_title_case(description)

        # Build filename
        filename = f"{date} {description}{ext}"

        # Truncate if needed
        if len(filename) > self.max_length:
            filename = self._truncate(date, description, ext)

        return filename

    def validate(self, filename: str) -> bool:
        """Validate filename matches YYYY-MM-DD pattern."""
        if not self._pattern.match(filename):
            return False

        # Check for invalid characters
        if any(c in filename for c in self.INVALID_CHARS):
            return False

        # Check length
        if len(filename) > 255:  # Max filename length
            return False

        return True

    def _clean_description(self, description: str) -> str:
        """Remove invalid characters from description."""
        for char in self.INVALID_CHARS:
            description = description.replace(char, '')

        # Collapse multiple spaces
        description = ' '.join(description.split())

        return description.strip()

    def _to_title_case(self, text: str) -> str:
        """Convert to title case, preserving acronyms."""
        # Simple title case that preserves all-caps words
        words = []
        for word in text.split():
            if word.isupper() and len(word) > 1:
                # Keep acronyms as-is (e.g., "PDF", "LLC")
                words.append(word)
            else:
                words.append(word.capitalize())
        return ' '.join(words)

    def _truncate(self, date: str, description: str, ext: str) -> str:
        """Intelligently truncate filename to max_length."""
        # Calculate available space for description
        fixed_length = len(date) + len(ext) + 2  # +2 for spaces
        available = self.max_length - fixed_length

        if available < 10:
            # Not enough space for meaningful description
            return f"{date}{ext}"

        # Truncate at word boundary if possible
        truncated_desc = description[:available]

        # Try to truncate at last space
        last_space = truncated_desc.rfind(' ')
        if last_space > available // 2:  # At least halfway through
            truncated_desc = truncated_desc[:last_space]

        return f"{date} {truncated_desc}{ext}"

    def __repr__(self) -> str:
        return f"ISODateNaming(max_length={self.max_length}, title_case={self.title_case})"
