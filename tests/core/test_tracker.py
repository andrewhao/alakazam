"""Tests for file tracker (async I/O fix verification)."""

import json
import pytest
from pathlib import Path
from alakazam.core.tracker import JSONTracker


class TestJSONTrackerAsyncIO:
    """Test JSONTracker async I/O operations (verifies async fix)."""

    @pytest.mark.asyncio
    async def test_async_save_creates_file(self, tmp_path):
        """Test that _save() correctly uses async I/O."""
        log_file = tmp_path / "test_log.json"
        tracker = JSONTracker(log_file)

        # Record a rename to trigger save
        await tracker.record_rename(
            "old_file.pdf",
            "new_file.pdf",
            {
                "document_date": "2024-01-15",
                "document_type": "invoice",
                "description": "Test document"
            }
        )

        # Verify file was created
        assert log_file.exists()

        # Verify content is valid JSON
        with open(log_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert "metadata" in data
        assert "renames" in data
        assert len(data["renames"]) == 1
        assert data["renames"][0]["old_name"] == "old_file.pdf"
        assert data["renames"][0]["new_name"] == "new_file.pdf"

    @pytest.mark.asyncio
    async def test_multiple_async_saves(self, tmp_path):
        """Test multiple async save operations."""
        log_file = tmp_path / "test_log.json"
        tracker = JSONTracker(log_file)

        # Record multiple renames
        for i in range(3):
            await tracker.record_rename(
                f"old_{i}.pdf",
                f"new_{i}.pdf",
                {
                    "document_date": f"2024-01-{i+1:02d}",
                    "document_type": "invoice",
                    "description": f"Document {i}"
                }
            )

        # Verify all were saved
        with open(log_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert len(data["renames"]) == 3

    @pytest.mark.asyncio
    async def test_async_save_preserves_unicode(self, tmp_path):
        """Test that async save correctly handles unicode (ensure_ascii=False)."""
        log_file = tmp_path / "test_log.json"
        tracker = JSONTracker(log_file)

        await tracker.record_rename(
            "café.pdf",
            "naïve_résumé.pdf",
            {
                "document_date": "2024-01-15",
                "document_type": "document",
                "description": "Unicode test: café, naïve, 日本語"
            }
        )

        # Verify unicode is preserved
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "café" in content
        assert "naïve" in content
        assert "résumé" in content
        assert "日本語" in content
