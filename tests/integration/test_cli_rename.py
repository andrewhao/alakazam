"""CLI integration tests for the rename command."""

from pathlib import Path
from typing import Dict, Optional

from click.testing import CliRunner

from alakazam.cli.main import cli


class FakeAnalyzer:
    """Analyzer stub for CLI tests (no external dependencies)."""

    def __init__(self, *args, **kwargs):
        self.calls = []

    async def analyze(self, document_path: Path) -> Optional[Dict]:
        self.calls.append(document_path)
        return {
            "document_date": "2024-01-15",
            "document_type": "invoice",
            "new_filename": f"2024-01-15 Test {document_path.stem}.pdf",
            "description": f"Test {document_path.stem}",
            "metadata": {},
        }

    def validate_config(self) -> bool:
        return True


def test_cli_rename_dry_run_processes_files(monkeypatch, tmp_path: Path):
    """Rename command should run the pipeline and report dry-run count."""
    (tmp_path / "one.pdf").write_text("fake")
    (tmp_path / "two.pdf").write_text("fake")

    instances = []

    class FakeAnalyzerFactory(FakeAnalyzer):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            instances.append(self)

    monkeypatch.setattr("alakazam.cli.main.ClaudeCodeAnalyzer", FakeAnalyzerFactory)

    runner = CliRunner()
    result = runner.invoke(cli, ["rename", str(tmp_path), "--dry-run"])

    assert result.exit_code == 0
    assert "Dry run: 2" in result.output
    assert len(instances) == 1
    assert len(instances[0].calls) == 2


def test_cli_rename_uses_codex_analyzer(monkeypatch, tmp_path: Path):
    """--analyzer codex should select CodexAnalyzer."""
    (tmp_path / "one.pdf").write_text("fake")

    instances = []

    class FakeCodexAnalyzer(FakeAnalyzer):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            instances.append(self)

    monkeypatch.setattr("alakazam.cli.main.CodexAnalyzer", FakeCodexAnalyzer)

    runner = CliRunner()
    result = runner.invoke(cli, ["rename", str(tmp_path), "--dry-run", "--analyzer", "codex"])

    assert result.exit_code == 0
    assert "Dry run: 1" in result.output
    assert len(instances) == 1
