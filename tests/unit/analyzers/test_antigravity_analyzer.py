"""Unit tests for AntigravityAnalyzer."""

import asyncio
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from alakazam.analyzers.antigravity import AntigravityAnalyzer


@pytest.mark.asyncio
async def test_antigravity_analyzer_analyze_success(tmp_path: Path, monkeypatch):
    """AntigravityAnalyzer should correctly analyze a document on success."""
    sample_pdf = tmp_path / "test.pdf"
    sample_pdf.write_bytes(b"%PDF-1.4\n%mock\n")

    response_payload = {
        "document_date": "2024-03-06",
        "document_type": "invoice",
        "new_filename": "2024-03-06 Antigravity Services Invoice.pdf",
        "description": "Invoice for Antigravity compute services",
        "alternative_filenames": [
            "2024-03-06 Antigravity Services.pdf",
            "2024-03-06 Cloud Compute Invoice.pdf",
        ],
        "metadata": {"amount": "100.00"},
    }

    async def fake_exec(*args, **kwargs):
        class FakeProcess:
            returncode = 0

            async def communicate(self):
                return json.dumps(response_payload).encode("utf-8"), b""

        return FakeProcess()

    monkeypatch.setattr("asyncio.create_subprocess_exec", fake_exec)

    analyzer = AntigravityAnalyzer(verbose=True)

    with patch.object(analyzer, "_extract_first_pages", return_value=sample_pdf):
        result = await analyzer.analyze(sample_pdf)

    assert result is not None
    assert result["document_date"] == "2024-03-06"
    assert result["document_type"] == "invoice"
    assert result["new_filename"] == "2024-03-06 Antigravity Services Invoice.pdf"
    assert result["metadata"]["amount"] == "100.00"
    assert len(result["alternative_filenames"]) == 2


@pytest.mark.asyncio
async def test_antigravity_analyzer_handles_markdown_json(tmp_path: Path, monkeypatch):
    """AntigravityAnalyzer should handle JSON wrapped in markdown code blocks."""
    sample_pdf = tmp_path / "test.pdf"
    sample_pdf.write_bytes(b"%PDF-1.4\n%mock\n")

    raw_output = (
        "```json\n"
        + json.dumps(
            {
                "document_date": "2024-01-01",
                "document_type": "receipt",
                "new_filename": "2024-01-01 Receipt.pdf",
                "description": "A store receipt",
            }
        )
        + "\n```"
    )

    async def fake_exec(*args, **kwargs):
        class FakeProcess:
            returncode = 0

            async def communicate(self):
                return raw_output.encode("utf-8"), b""

        return FakeProcess()

    monkeypatch.setattr("asyncio.create_subprocess_exec", fake_exec)

    analyzer = AntigravityAnalyzer()

    with patch.object(analyzer, "_extract_first_pages", return_value=sample_pdf):
        result = await analyzer.analyze(sample_pdf)

    assert result is not None
    assert result["document_date"] == "2024-01-01"
    assert result["new_filename"] == "2024-01-01 Receipt.pdf"


@pytest.mark.asyncio
async def test_antigravity_analyzer_timeout_returns_none(tmp_path: Path, monkeypatch):
    """AntigravityAnalyzer should return None on subprocess timeout."""
    sample_pdf = tmp_path / "test.pdf"
    sample_pdf.write_bytes(b"%PDF-1.4\n%mock\n")

    async def fake_exec(*args, **kwargs):
        class FakeProcess:
            returncode = 0

            async def communicate(self):
                await asyncio.sleep(10)
                return b"", b""

            def kill(self):
                pass

        return FakeProcess()

    monkeypatch.setattr("asyncio.create_subprocess_exec", fake_exec)

    analyzer = AntigravityAnalyzer(timeout=0.01, verbose=True)

    with patch.object(analyzer, "_extract_first_pages", return_value=sample_pdf):
        result = await analyzer.analyze(sample_pdf)

    assert result is None


@pytest.mark.asyncio
async def test_antigravity_analyzer_process_error_returns_none(tmp_path: Path, monkeypatch):
    """AntigravityAnalyzer should return None on non-zero exit code."""
    sample_pdf = tmp_path / "test.pdf"
    sample_pdf.write_bytes(b"%PDF-1.4\n%mock\n")

    async def fake_exec(*args, **kwargs):
        class FakeProcess:
            returncode = 1

            async def communicate(self):
                return b"", b"Authentication failed"

        return FakeProcess()

    monkeypatch.setattr("asyncio.create_subprocess_exec", fake_exec)

    analyzer = AntigravityAnalyzer(verbose=True)

    with patch.object(analyzer, "_extract_first_pages", return_value=sample_pdf):
        result = await analyzer.analyze(sample_pdf)

    assert result is None


@pytest.mark.asyncio
async def test_antigravity_analyzer_sanitizes_skill_leaks(tmp_path: Path, monkeypatch):
    """AntigravityAnalyzer should sanitize skill instructions from output."""
    sample_pdf = tmp_path / "test.pdf"
    sample_pdf.write_bytes(b"%PDF-1.4\n%mock\n")

    response_payload = {
        "document_date": "2024-02-02",
        "document_type": "invoice",
        "new_filename": "2024-02-02 Using superpowers to follow skill workflow Acme.pdf",
        "description": "using superpowers:file-reader to follow skill workflow. Acme Invoice",
        "alternative_filenames": ["2024-02-02 Superpowers Acme.pdf"],
    }

    async def fake_exec(*args, **kwargs):
        class FakeProcess:
            returncode = 0

            async def communicate(self):
                return json.dumps(response_payload).encode("utf-8"), b""

        return FakeProcess()

    monkeypatch.setattr("asyncio.create_subprocess_exec", fake_exec)

    analyzer = AntigravityAnalyzer()

    with patch.object(analyzer, "_extract_first_pages", return_value=sample_pdf):
        result = await analyzer.analyze(sample_pdf)

    assert result is not None
    assert "superpowers" not in result["description"].lower()
    assert "superpowers" not in result["new_filename"].lower()
    assert "superpowers" not in result["alternative_filenames"][0].lower()


@pytest.mark.asyncio
async def test_antigravity_analyzer_passes_model_and_effort_flags(tmp_path: Path, monkeypatch):
    """AntigravityAnalyzer should pass --model and --effort to agy when provided."""
    sample_pdf = tmp_path / "test.pdf"
    sample_pdf.write_bytes(b"%PDF-1.4\n%mock\n")

    captured_cmd = []

    async def fake_exec(*args, **kwargs):
        captured_cmd.extend(args)

        class FakeProcess:
            returncode = 0

            async def communicate(self):
                valid_resp = {
                    "document_date": "2024-01-01",
                    "document_type": "letter",
                    "new_filename": "2024-01-01 Letter.pdf",
                    "description": "A letter",
                }
                return json.dumps(valid_resp).encode("utf-8"), b""

        return FakeProcess()

    monkeypatch.setattr("asyncio.create_subprocess_exec", fake_exec)

    analyzer = AntigravityAnalyzer(
        agy_cmd="agy",
        model="gemini-2.5-flash",
        effort="high",
    )

    with patch.object(analyzer, "_extract_first_pages", return_value=sample_pdf):
        await analyzer.analyze(sample_pdf)

    assert "--model" in captured_cmd
    model_idx = captured_cmd.index("--model")
    assert captured_cmd[model_idx + 1] == "gemini-2.5-flash"

    assert "--effort" in captured_cmd
    effort_idx = captured_cmd.index("--effort")
    assert captured_cmd[effort_idx + 1] == "high"

    assert "--dangerously-skip-permissions" in captured_cmd
    assert "--output-format" in captured_cmd
    assert "-p" in captured_cmd
    p_idx = captured_cmd.index("-p")
    assert captured_cmd[p_idx + 1].startswith("Read the PDF file")


def test_antigravity_analyzer_validate_config(monkeypatch):
    """AntigravityAnalyzer.validate_config checks if agy command runs."""
    analyzer = AntigravityAnalyzer(agy_cmd="agy")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        assert analyzer.validate_config() is True

        mock_run.return_value = MagicMock(returncode=1)
        assert analyzer.validate_config() is False

        mock_run.side_effect = FileNotFoundError()
        assert analyzer.validate_config() is False

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="agy", timeout=5)
        assert analyzer.validate_config() is False


def test_antigravity_prompt_includes_preferences_and_registry():
    """Antigravity prompt should include naming preferences and registry types."""
    mock_registry = MagicMock()
    mock_registry.get_all_types.return_value = ["custom_doc_a", "custom_doc_b"]

    analyzer = AntigravityAnalyzer(type_registry=mock_registry)
    analyzer.set_naming_preferences("Prefer prefix ProjectX")
    prompt = analyzer._build_prompt()

    assert "custom_doc_a" in prompt
    assert "custom_doc_b" in prompt
    assert "Recent user overrides" in prompt
    assert "Prefer prefix ProjectX" in prompt


def test_gemini_analyzer_backwards_compatibility_alias():
    """GeminiAnalyzer should be an alias to AntigravityAnalyzer."""
    from alakazam.analyzers import GeminiAnalyzer as RootGemini
    from alakazam.analyzers.gemini import GeminiAnalyzer as ModuleGemini

    assert RootGemini is AntigravityAnalyzer
    assert ModuleGemini is AntigravityAnalyzer
