"""Tests for CodexAnalyzer."""

import json
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_codex_analyzer_parses_output_file(tmp_path: Path, monkeypatch):
    """CodexAnalyzer should read the output file and parse JSON."""
    from alakazam.analyzers.codex import CodexAnalyzer

    output_path = tmp_path / "codex_output.json"
    output_path.write_text(
        json.dumps(
            {
                "document_date": "2024-01-15",
                "document_type": "invoice",
                "new_filename": "2024-01-15 Test Invoice.pdf",
                "description": "Test Invoice",
                "metadata": {"key": "value"},
            }
        )
    )
    sample_pdf = tmp_path / "sample.pdf"
    sample_pdf.write_bytes(b"%PDF-1.4\n%mock\n")

    async def fake_exec(*args, **kwargs):
        class Result:
            returncode = 0

            async def communicate(self, *args, **kwargs):
                return b"", b""

        return Result()

    monkeypatch.setattr("alakazam.analyzers.codex.asyncio.create_subprocess_exec", fake_exec)

    analyzer = CodexAnalyzer(
        codex_cmd="codex",
        timeout=10,
        verbose=False,
        _test_output_path=output_path,
    )

    result = await analyzer.analyze(sample_pdf)

    assert result is not None
    assert result["document_date"] == "2024-01-15"
    assert result["document_type"] == "invoice"
    assert result["new_filename"] == "2024-01-15 Test Invoice.pdf"


@pytest.mark.asyncio
async def test_codex_analyzer_invokes_exec_without_ask_for_approval(
    tmp_path: Path, monkeypatch
):
    """CodexAnalyzer should not pass unsupported ask-for-approval flag."""
    from alakazam.analyzers.codex import CodexAnalyzer

    output_path = tmp_path / "codex_output.json"
    output_path.write_text(
        json.dumps(
            {
                "document_date": "2024-01-15",
                "document_type": "invoice",
                "new_filename": "2024-01-15 Test Invoice.pdf",
                "description": "Test Invoice",
            }
        )
    )

    sample_pdf = tmp_path / "sample.pdf"
    sample_pdf.write_bytes(b"%PDF-1.4\n%mock\n")

    calls = {}

    async def fake_exec(*args, **kwargs):
        calls["args"] = args
        calls["kwargs"] = kwargs

        class Result:
            returncode = 0

            async def communicate(self, *args, **kwargs):
                return b"", b""

        return Result()

    monkeypatch.setattr("alakazam.analyzers.codex.asyncio.create_subprocess_exec", fake_exec)

    analyzer = CodexAnalyzer(
        codex_cmd="codex",
        timeout=10,
        verbose=False,
        _test_output_path=output_path,
    )

    await analyzer.analyze(sample_pdf)

    cmd_args = [str(arg) for arg in calls.get("args", [])]
    assert "--ask-for-approval" not in cmd_args


@pytest.mark.asyncio
async def test_codex_analyzer_skips_git_repo_check(tmp_path: Path, monkeypatch):
    """CodexAnalyzer should allow running outside a git repo."""
    from alakazam.analyzers.codex import CodexAnalyzer

    output_path = tmp_path / "codex_output.json"
    output_path.write_text(
        json.dumps(
            {
                "document_date": "2024-01-15",
                "document_type": "invoice",
                "new_filename": "2024-01-15 Test Invoice.pdf",
                "description": "Test Invoice",
            }
        )
    )

    sample_pdf = tmp_path / "sample.pdf"
    sample_pdf.write_bytes(b"%PDF-1.4\n%mock\n")

    calls = {}

    async def fake_exec(*args, **kwargs):
        calls["args"] = args
        calls["kwargs"] = kwargs

        class Result:
            returncode = 0

            async def communicate(self, *args, **kwargs):
                return b"", b""

        return Result()

    monkeypatch.setattr("alakazam.analyzers.codex.asyncio.create_subprocess_exec", fake_exec)

    analyzer = CodexAnalyzer(
        codex_cmd="codex",
        timeout=10,
        verbose=False,
        _test_output_path=output_path,
    )

    await analyzer.analyze(sample_pdf)

    cmd_args = [str(arg) for arg in calls.get("args", [])]
    assert "--skip-git-repo-check" in cmd_args


@pytest.mark.asyncio
async def test_codex_analyzer_parses_alternative_filenames(tmp_path: Path, monkeypatch):
    """CodexAnalyzer should parse alternative filename suggestions."""
    from alakazam.analyzers.codex import CodexAnalyzer

    output_path = tmp_path / "codex_output.json"
    output_path.write_text(
        json.dumps(
            {
                "document_date": "2024-01-15",
                "document_type": "invoice",
                "new_filename": "2024-01-15 Test Invoice.pdf",
                "description": "Test Invoice",
                "alternative_filenames": [
                    "2024-01-15 Test Invoice Acme.pdf",
                    "2024-01-15 Acme Invoice.pdf",
                ],
            }
        )
    )

    sample_pdf = tmp_path / "sample.pdf"
    sample_pdf.write_bytes(b"%PDF-1.4\n%mock\n")

    async def fake_exec(*args, **kwargs):
        class Result:
            returncode = 0

            async def communicate(self, *args, **kwargs):
                return b"", b""

        return Result()

    monkeypatch.setattr("alakazam.analyzers.codex.asyncio.create_subprocess_exec", fake_exec)

    analyzer = CodexAnalyzer(
        codex_cmd="codex",
        timeout=10,
        verbose=False,
        _test_output_path=output_path,
    )
    result = await analyzer.analyze(sample_pdf)

    assert result["alternative_filenames"][0].startswith("2024-01-15")


def test_codex_prompt_includes_alternatives_and_preferences():
    """Prompt should request alternatives and include preferences when set."""
    from alakazam.analyzers.codex import CodexAnalyzer

    analyzer = CodexAnalyzer()
    analyzer.set_naming_preferences("- Suggested -> Chosen example")
    prompt = analyzer._build_prompt()

    assert "alternative_filenames" in prompt
    assert "Recent user overrides" in prompt
