"""Tests for Alakazam core renamer."""

import time
from pathlib import Path
from typing import Dict, Optional

import pytest

from alakazam.core.renamer import Alakazam, AlakazamConfig
from alakazam.core.tracker import JSONTracker
from alakazam.naming import ISODateNaming
from alakazam.storage import LocalStorage
from alakazam.types import TypeRegistry


class TestAlakazamConfig:
    """Test AlakazamConfig dataclass (verifies typo fix)."""

    def test_config_instantiation(self):
        """Test that AlakazamConfig can be instantiated with correct name."""
        config = AlakazamConfig()
        assert config.batch_size == 5
        assert config.dry_run is False
        assert config.safe_mode is False
        assert config.max_batches == 1000
        assert config.verbose is False

    def test_config_with_custom_values(self):
        """Test AlakazamConfig with custom values."""
        config = AlakazamConfig(
            batch_size=10,
            dry_run=True,
            safe_mode=True,
            max_batches=100,
            verbose=True
        )
        assert config.batch_size == 10
        assert config.dry_run is True
        assert config.safe_mode is True
        assert config.max_batches == 100
        assert config.verbose is True

    def test_config_class_name_spelling(self):
        """Verify the class name is spelled correctly (Alakazam not Alazazam)."""
        # This test verifies the typo fix
        assert AlakazamConfig.__name__ == "AlakazamConfig"
        assert "Alakazam" in AlakazamConfig.__name__
        assert "Alazazam" not in AlakazamConfig.__name__


class MissingDateAnalyzer:
    """Analyzer that omits document_date to test error handling."""

    async def analyze(self, document_path: Path) -> Optional[Dict]:
        return {
            "document_type": "invoice",
            "description": "Missing date",
        }

    def validate_config(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_process_batch_missing_document_date_returns_error(tmp_path: Path):
    """Return a clear error when analysis lacks document_date."""
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_text("fake pdf content")

    log_file = tmp_path / ".alakazam.log"

    alakazam = Alakazam(
        analyzer=MissingDateAnalyzer(),
        naming_strategy=ISODateNaming(),
        storage=LocalStorage(tmp_path),
        tracker=JSONTracker(log_file),
        type_registry=TypeRegistry(),
        config=AlakazamConfig(batch_size=5, dry_run=True, verbose=False),
    )

    result = await alakazam.process_batch()

    assert result.error_count == 1
    assert result.files[0].error == "Analysis missing required fields: document_date"


@pytest.mark.asyncio
async def test_interactive_decision_skips_file(tmp_path: Path):
    """Interactive decision provider should be able to skip a file."""

    class FakeAnalyzer:
        async def analyze(self, document_path: Path) -> Optional[Dict]:
            return {
                "document_date": "2024-01-01",
                "document_type": "invoice",
                "description": "Test",
                "alternative_filenames": ["2024-01-01 Test Alt.pdf"],
            }

        def validate_config(self) -> bool:
            return True

    class Decision:
        action = "skip"
        chosen_name = None
        suggested_name = "2024-01-01 Test.pdf"
        alternative_names = ["2024-01-01 Test Alt.pdf"]

    async def decide(*args, **kwargs):
        return Decision()

    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_text("fake pdf content")

    log_file = tmp_path / ".alakazam.log"

    alakazam = Alakazam(
        analyzer=FakeAnalyzer(),
        naming_strategy=ISODateNaming(),
        storage=LocalStorage(tmp_path),
        tracker=JSONTracker(log_file),
        type_registry=TypeRegistry(),
        config=AlakazamConfig(batch_size=1, dry_run=True, verbose=False, interactive=True),
        decision_provider=decide,
    )

    result = await alakazam.process_batch()

    assert result.skipped_count == 1


def test_interactive_mode_without_decision_provider_raises_error(tmp_path: Path):
    """Interactive mode without decision provider should raise ValueError at init."""

    class FakeAnalyzer:
        def validate_config(self) -> bool:
            return True

    log_file = tmp_path / ".alakazam.log"

    with pytest.raises(ValueError, match="decision_provider is required"):
        Alakazam(
            analyzer=FakeAnalyzer(),
            naming_strategy=ISODateNaming(),
            storage=LocalStorage(tmp_path),
            tracker=JSONTracker(log_file),
            type_registry=TypeRegistry(),
            config=AlakazamConfig(interactive=True),
            decision_provider=None,
        )


@pytest.mark.asyncio
async def test_process_batch_starts_with_most_recently_created_file(tmp_path: Path):
    """Batch processing should start with the newest-created file."""

    class FakeAnalyzer:
        async def analyze(self, document_path: Path) -> Optional[Dict]:
            return {
                "document_date": "2024-01-01",
                "document_type": "invoice",
                "description": "Test document",
            }

        def validate_config(self) -> bool:
            return True

    (tmp_path / "older.pdf").write_text("old")
    time.sleep(0.01)
    (tmp_path / "newer.pdf").write_text("new")

    log_file = tmp_path / ".alakazam.log"
    alakazam = Alakazam(
        analyzer=FakeAnalyzer(),
        naming_strategy=ISODateNaming(),
        storage=LocalStorage(tmp_path),
        tracker=JSONTracker(log_file),
        type_registry=TypeRegistry(),
        config=AlakazamConfig(batch_size=1, dry_run=True),
    )

    result = await alakazam.process_batch()

    assert len(result.files) == 1
    assert result.files[0].old_name == "newer.pdf"
