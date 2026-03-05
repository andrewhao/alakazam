"""Base class for storage backends."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List


class StorageBackend(ABC):
    """
    Abstract base class for storage backends.

    Handles file listing, renaming, and existence checks.
    """

    @abstractmethod
    async def list_files(self, pattern: str = "*") -> List[Path]:
        """
        List files matching pattern.

        Args:
            pattern: Glob pattern (e.g., "*.pdf", "**/*.jpg")

        Returns:
            List of Path objects sorted by creation time (newest first)
        """
        pass

    @abstractmethod
    async def rename(self, old_path: Path, new_name: str) -> Path:
        """
        Rename file and return new path.

        Args:
            old_path: Current file path
            new_name: New filename (not full path, just name)

        Returns:
            New Path object

        Raises:
            FileNotFoundError: If old_path doesn't exist
            FileExistsError: If new path already exists
        """
        pass

    @abstractmethod
    async def exists(self, path: Path) -> bool:
        """
        Check if file exists.

        Args:
            path: File path to check

        Returns:
            True if exists, False otherwise
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
