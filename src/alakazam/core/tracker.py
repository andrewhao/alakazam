"""File tracking to prevent duplicate processing."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Set


class FileTracker(ABC):
    """Abstract base class for file tracking."""

    @abstractmethod
    def get_processed_files(self) -> Set[str]:
        """Get set of all processed filenames."""
        pass

    @abstractmethod
    async def record_rename(self, old_name: str, new_name: str, analysis: Dict) -> None:
        """Record a rename operation."""
        pass


class JSONTracker(FileTracker):
    """
    JSON-based file tracker.

    Tracks processed files in a JSON log file.
    """

    def __init__(self, log_file: Path):
        """
        Initialize JSON tracker.

        Args:
            log_file: Path to JSON log file
        """
        self.log_file = Path(log_file)
        self.data = self._load()

    def _load(self) -> Dict:
        """Load log file or create empty structure."""
        if self.log_file.exists():
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        return {
            "metadata": {"version": "1.0"},
            "renames": [],
        }

    def get_processed_files(self) -> Set[str]:
        """Get set of all processed filenames (both old and new names)."""
        processed = set()
        for entry in self.data.get('renames', []):
            if 'old_name' in entry:
                processed.add(entry['old_name'])
            if 'new_name' in entry:
                processed.add(entry['new_name'])
        return processed

    async def record_rename(self, old_name: str, new_name: str, analysis: Dict) -> None:
        """Record a rename operation in the log."""
        entry = {
            "old_name": old_name,
            "new_name": new_name,
            "document_date": analysis.get('document_date'),
            "document_type": analysis.get('document_type'),
            "description": analysis.get('description'),
        }

        # Add optional metadata if present
        if 'metadata' in analysis and analysis['metadata']:
            entry['metadata'] = analysis['metadata']

        self.data['renames'].append(entry)

        # Save to file
        await self._save()

    async def _save(self) -> None:
        """Save log file."""
        import aiofiles
        async with aiofiles.open(self.log_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(self.data, indent=2, ensure_ascii=False))

    def __repr__(self) -> str:
        return f"JSONTracker(log_file={self.log_file}, entries={len(self.data.get('renames', []))})"
