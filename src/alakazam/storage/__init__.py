"""Storage backends for file operations."""

from alakazam.storage.base import StorageBackend
from alakazam.storage.local import LocalStorage

__all__ = ["StorageBackend", "LocalStorage"]
