"""Alakazam - AI-powered intelligent document renaming."""

__version__ = "0.1.0"

from alakazam.core.renamer import Alakazam
from alakazam.core.result import FileResult, ProcessingResult, ResultStatus

__all__ = [
    "Alakazam",
    "FileResult",
    "ProcessingResult",
    "ResultStatus",
    "__version__",
]
