"""Unit tests for GeminiAnalyzer."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from alakazam.analyzers.gemini import GeminiAnalyzer


@pytest.fixture
def mock_genai():
    """Mock the google.generativeai SDK."""
    with patch("alakazam.analyzers.gemini.genai") as mock:
        with patch("alakazam.analyzers.gemini.HAS_GEMINI", True):
            yield mock


@pytest.mark.asyncio
async def test_gemini_analyzer_analyze_success(tmp_path: Path, mock_genai):
    """GeminiAnalyzer should correctly analyze a document on success."""
    # Setup mock response
    mock_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "document_date": "2024-03-06",
        "document_type": "invoice",
        "new_filename": "2024-03-06 Google Gemini Invoice.pdf",
        "description": "Invoice for Gemini API services",
        "alternative_filenames": [
            "2024-03-06 Gemini Services.pdf",
            "2024-03-06 Google Cloud Invoice.pdf"
        ],
        "metadata": {"amount": "100.00"}
    })
    mock_model.generate_content.return_value = mock_response

    # Create a mock PDF
    sample_pdf = tmp_path / "test.pdf"
    sample_pdf.write_bytes(b"%PDF-1.4\n%mock\n")

    analyzer = GeminiAnalyzer(api_key="mock_key", verbose=True)
    
    # Mock PDF extraction to just return original
    with patch.object(analyzer, "_extract_first_pages", return_value=sample_pdf):
        result = await analyzer.analyze(sample_pdf)

    assert result is not None
    assert result["document_date"] == "2024-03-06"
    assert result["document_type"] == "invoice"
    assert result["new_filename"] == "2024-03-06 Google Gemini Invoice.pdf"
    assert result["metadata"]["amount"] == "100.00"
    
    # Verify mock calls
    mock_genai.configure.assert_called_once_with(api_key="mock_key")
    mock_genai.GenerativeModel.assert_called_once_with("gemini-1.5-flash")


@pytest.mark.asyncio
async def test_gemini_analyzer_handles_markdown_json(tmp_path: Path, mock_genai):
    """GeminiAnalyzer should handle JSON wrapped in markdown code blocks."""
    mock_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    
    mock_response = MagicMock()
    mock_response.text = "```json\n" + json.dumps({
        "document_date": "2024-01-01",
        "document_type": "receipt",
        "new_filename": "2024-01-01 Receipt.pdf",
        "description": "A receipt"
    }) + "\n```"
    mock_model.generate_content.return_value = mock_response

    sample_pdf = tmp_path / "test.pdf"
    sample_pdf.write_bytes(b"%PDF-1.4\n%mock\n")

    analyzer = GeminiAnalyzer(api_key="mock_key")
    
    with patch.object(analyzer, "_extract_first_pages", return_value=sample_pdf):
        result = await analyzer.analyze(sample_pdf)

    assert result["document_date"] == "2024-01-01"


@pytest.mark.asyncio
async def test_gemini_analyzer_missing_library(tmp_path: Path):
    """GeminiAnalyzer should fail gracefully if library is missing."""
    with patch("alakazam.analyzers.gemini.HAS_GEMINI", False):
        analyzer = GeminiAnalyzer(api_key="mock_key")
        result = await analyzer.analyze(Path("any.pdf"))
        assert result is None


@pytest.mark.asyncio
async def test_gemini_analyzer_missing_api_key(tmp_path: Path, mock_genai):
    """GeminiAnalyzer should fail gracefully if API key is missing."""
    with patch.dict("os.environ", {}, clear=True):
        analyzer = GeminiAnalyzer(api_key=None)
        result = await analyzer.analyze(Path("any.pdf"))
        assert result is None


def test_gemini_analyzer_validate_config(mock_genai):
    """GeminiAnalyzer.validate_config should check for library and key."""
    analyzer = GeminiAnalyzer(api_key="mock_key")
    assert analyzer.validate_config() is True

    analyzer_no_key = GeminiAnalyzer(api_key=None)
    with patch.dict("os.environ", {}, clear=True):
        assert analyzer_no_key.validate_config() is False


def test_gemini_prompt_includes_preferences():
    """Gemini prompt should include user naming preferences."""
    analyzer = GeminiAnalyzer(api_key="mock_key")
    analyzer.set_naming_preferences("Use specific date format")
    prompt = analyzer._build_prompt()
    assert "Recent user overrides" in prompt
    assert "Use specific date format" in prompt
