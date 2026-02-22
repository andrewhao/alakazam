"""Sanitize analyzer outputs for leaked internal instructions."""

from __future__ import annotations

import re
from typing import Dict

_SKILL_PREFIX_PATTERNS = [
    re.compile(
        r"^using\s+superpowers[:\w-]*\s+to\s+follow\s+skill\s+workflow\.?\s*",
        re.IGNORECASE,
    ),
    re.compile(r"^using\s+superpowers[:\w-]*\.?\s*", re.IGNORECASE),
    re.compile(r"^superpowers[:\w-]*\.?\s*", re.IGNORECASE),
]


def _strip_skill_leaks(text: str) -> str:
    if not text:
        return text

    cleaned = text.strip()
    sentences = re.split(r"(?<=\.)\s+", cleaned)
    if sentences and "superpowers" in sentences[0].lower():
        cleaned = " ".join(sentences[1:]).strip()

    for pattern in _SKILL_PREFIX_PATTERNS:
        cleaned = pattern.sub("", cleaned).strip()

    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    cleaned = re.sub(r"\.{2,}", ".", cleaned)
    return cleaned


def _sanitize_filename(name: str) -> str:
    if not name:
        return name

    if "." in name:
        stem, ext = name.rsplit(".", 1)
        cleaned = _strip_skill_leaks(stem)
        return f"{cleaned}.{ext}"

    return _strip_skill_leaks(name)


def sanitize_analysis(result: Dict) -> Dict:
    """Remove leaked internal instruction phrases from analysis output."""
    if not result:
        return result

    sanitized = dict(result)
    description = sanitized.get("description")
    if isinstance(description, str):
        sanitized["description"] = _strip_skill_leaks(description)

    new_filename = sanitized.get("new_filename")
    if isinstance(new_filename, str):
        sanitized["new_filename"] = _sanitize_filename(new_filename)

    alternatives = sanitized.get("alternative_filenames")
    if isinstance(alternatives, list):
        sanitized["alternative_filenames"] = [
            _sanitize_filename(name) if isinstance(name, str) else name
            for name in alternatives
        ]

    return sanitized
