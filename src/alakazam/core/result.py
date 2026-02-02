"""Result types for file processing operations."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class ResultStatus(Enum):
    """Status of file processing operation."""

    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"
    DRY_RUN = "dry_run"


@dataclass
class FileResult:
    """Result of processing a single file."""

    status: ResultStatus
    old_name: str
    new_name: Optional[str] = None
    error: Optional[str] = None
    analysis: Optional[Dict] = None

    @classmethod
    def success(cls, old_name: str, new_name: str, analysis: Dict) -> "FileResult":
        """Create success result."""
        return cls(ResultStatus.SUCCESS, old_name, new_name, analysis=analysis)

    @classmethod
    def error(cls, old_name: str, error: str) -> "FileResult":
        """Create error result."""
        return cls(ResultStatus.ERROR, old_name, error=error)

    @classmethod
    def dry_run(cls, old_name: str, new_name: str) -> "FileResult":
        """Create dry-run result."""
        return cls(ResultStatus.DRY_RUN, old_name, new_name)

    @classmethod
    def skipped(cls, old_name: str, reason: str) -> "FileResult":
        """Create skipped result."""
        return cls(ResultStatus.SKIPPED, old_name, error=reason)

    def is_success(self) -> bool:
        """Check if operation was successful."""
        return self.status == ResultStatus.SUCCESS

    def __repr__(self) -> str:
        if self.status == ResultStatus.SUCCESS:
            return f"FileResult(SUCCESS: {self.old_name} → {self.new_name})"
        elif self.status == ResultStatus.ERROR:
            return f"FileResult(ERROR: {self.old_name} - {self.error})"
        elif self.status == ResultStatus.DRY_RUN:
            return f"FileResult(DRY_RUN: {self.old_name} → {self.new_name})"
        else:
            return f"FileResult(SKIPPED: {self.old_name})"


@dataclass
class ProcessingResult:
    """Result of processing a batch of files."""

    files: List[FileResult]
    started: datetime
    completed: datetime

    @property
    def success_count(self) -> int:
        """Count of successful operations."""
        return sum(1 for f in self.files if f.status == ResultStatus.SUCCESS)

    @property
    def error_count(self) -> int:
        """Count of failed operations."""
        return sum(1 for f in self.files if f.status == ResultStatus.ERROR)

    @property
    def skipped_count(self) -> int:
        """Count of skipped operations."""
        return sum(1 for f in self.files if f.status == ResultStatus.SKIPPED)

    @property
    def dry_run_count(self) -> int:
        """Count of dry-run operations."""
        return sum(1 for f in self.files if f.status == ResultStatus.DRY_RUN)

    @property
    def duration(self) -> float:
        """Duration in seconds."""
        return (self.completed - self.started).total_seconds()

    def __repr__(self) -> str:
        return (
            f"ProcessingResult("
            f"total={len(self.files)}, "
            f"success={self.success_count}, "
            f"errors={self.error_count}, "
            f"duration={self.duration:.2f}s)"
        )
