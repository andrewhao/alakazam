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
