"""File tracking to prevent duplicate processing."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Set

import aiofiles


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

    async def record_decision(
        self,
        old_name: str,
        suggested_name: str,
        alternative_names: list,
        chosen_name: str | None,
        decision: str,
        analysis: Dict,
        dry_run: bool,
    ) -> None:
        """
        Record an interactive naming decision.

        Default implementation does nothing. Subclasses can override to track decisions.
        """
        pass

    def get_override_examples(self, limit: int = 5) -> list:
        """
        Return recent examples of user overrides.

        Default implementation returns empty list. Subclasses can override to provide examples.
        """
        return []


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
            "decisions": [],
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

    async def record_decision(
        self,
        old_name: str,
        suggested_name: str,
        alternative_names: list,
        chosen_name: str | None,
        decision: str,
        analysis: Dict,
        dry_run: bool,
    ) -> None:
        """Record an interactive naming decision in the log."""
        entry = {
            "old_name": old_name,
            "suggested_name": suggested_name,
            "alternative_names": alternative_names or [],
            "chosen_name": chosen_name,
            "decision": decision,
            "dry_run": dry_run,
            "document_date": analysis.get('document_date'),
            "document_type": analysis.get('document_type'),
            "description": analysis.get('description'),
        }

        if 'metadata' in analysis and analysis['metadata']:
            entry['metadata'] = analysis['metadata']

        self.data.setdefault('decisions', []).append(entry)
        await self._save()

    def get_override_examples(self, limit: int = 5) -> list:
        """Return recent examples where chosen name differs from suggestion."""
        examples = []
        for entry in reversed(self.data.get('decisions', [])):
            if entry.get('chosen_name') and entry.get('chosen_name') != entry.get('suggested_name'):
                examples.append(
                    {
                        "suggested_name": entry.get('suggested_name'),
                        "chosen_name": entry.get('chosen_name'),
                        "document_type": entry.get('document_type'),
                        "metadata": entry.get('metadata', {}),
                    }
                )
            if len(examples) >= limit:
                break
        return list(reversed(examples))

    async def _save(self) -> None:
        """Save log file."""
        async with aiofiles.open(self.log_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(self.data, indent=2, ensure_ascii=False))

    def __repr__(self) -> str:
        return f"JSONTracker(log_file={self.log_file}, entries={len(self.data.get('renames', []))})"
