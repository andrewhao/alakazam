"""Local filesystem storage backend."""

import aiofiles.os
from pathlib import Path
from typing import List

from alakazam.storage.base import StorageBackend


class LocalStorage(StorageBackend):
    """
    Local filesystem storage backend.

    Handles file operations on the local filesystem.
    """

    def __init__(self, root_path: Path):
        """
        Initialize local storage.

        Args:
            root_path: Root directory path
        """
        self.root = Path(root_path).expanduser().absolute()

        if not self.root.exists():
            raise FileNotFoundError(f"Root path does not exist: {self.root}")

        if not self.root.is_dir():
            raise NotADirectoryError(f"Root path is not a directory: {self.root}")

    async def list_files(self, pattern: str = "*") -> List[Path]:
        """List files matching pattern, sorted by creation time (newest first)."""
        files = list(self.root.glob(pattern))

        # Filter out directories
        files = [f for f in files if f.is_file()]

        # Prefer true creation time when available (e.g. macOS), otherwise fall back
        # to modification time on platforms without st_birthtime.
        files.sort(key=self._created_timestamp, reverse=True)

        return files

    @staticmethod
    def _created_timestamp(path: Path) -> float:
        """Get best-available creation timestamp for sorting."""
        stat = path.stat()
        return getattr(stat, "st_birthtime", stat.st_mtime)

    async def rename(self, old_path: Path, new_name: str) -> Path:
        """Rename file on local filesystem."""
        if not old_path.exists():
            raise FileNotFoundError(f"File not found: {old_path}")

        new_path = old_path.parent / new_name

        if new_path.exists():
            raise FileExistsError(f"File already exists: {new_path}")

        # Use aiofiles for async operation
        await aiofiles.os.rename(old_path, new_path)

        return new_path

    async def exists(self, path: Path) -> bool:
        """Check if file exists on local filesystem."""
        return path.exists()

    def __repr__(self) -> str:
        return f"LocalStorage(root={self.root})"
