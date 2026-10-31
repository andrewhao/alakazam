"""Unit tests for LocalStorage cloud materialization."""

from pathlib import Path
from unittest.mock import patch

import pytest

from alakazam.storage.local import LocalStorage


def test_is_cloud_path_detection(tmp_path: Path):
    """LocalStorage.is_cloud_path correctly identifies CloudStorage and Mobile Documents."""
    storage = LocalStorage(tmp_path)
    cloud_google = Path(
        "/Users/user/Library/CloudStorage/GoogleDrive-test@gmail.com/My Drive/ScanSnap/doc.pdf"
    )
    cloud_icloud = Path("/Users/user/Library/Mobile Documents/com~apple~CloudDocs/doc.pdf")
    local_path = Path("/Users/user/Documents/doc.pdf")

    assert storage.is_cloud_path(cloud_google) is True
    assert storage.is_cloud_path(cloud_icloud) is True
    assert storage.is_cloud_path(local_path) is False


@pytest.mark.asyncio
async def test_materialize_non_cloud_returns_true(tmp_path: Path):
    """Local files not under cloud storage return True immediately without running osascript."""
    storage = LocalStorage(tmp_path, auto_download=True)
    sample = tmp_path / "file.pdf"
    sample.write_bytes(b"%PDF-1.4\n")

    with patch("asyncio.create_subprocess_exec") as mock_exec:
        result = await storage.materialize(sample)
        assert result is True
        mock_exec.assert_not_called()


@pytest.mark.asyncio
async def test_materialize_non_existent_returns_false(tmp_path: Path):
    """Non-existent files return False."""
    storage = LocalStorage(tmp_path)
    result = await storage.materialize(tmp_path / "does_not_exist.pdf")
    assert result is False


@pytest.mark.asyncio
async def test_materialize_cloud_path_executes_osascript(tmp_path: Path, monkeypatch):
    """Under a cloud storage path, materialize triggers osascript."""
    # Simulate a path under Library/CloudStorage
    storage = LocalStorage(tmp_path, auto_download=True)
    sample = tmp_path / "sample.pdf"
    sample.write_bytes(b"%PDF-1.4\n")

    # Force is_cloud_path to True for test
    monkeypatch.setattr(storage, "is_cloud_path", lambda p: True)

    script_called = []

    async def fake_exec(*args, **kwargs):
        script_called.extend(args)

        class FakeProcess:
            returncode = 0

            async def wait(self):
                return 0

        return FakeProcess()

    monkeypatch.setattr("asyncio.create_subprocess_exec", fake_exec)

    result = await storage.materialize(sample, timeout=5.0)
    assert result is True
    assert "osascript" in script_called
    assert "-l" in script_called
    assert "JavaScript" in script_called
