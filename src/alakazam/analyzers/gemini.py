"""Google Gemini-based document analyzer.

This analyzer uses the official Google Generative AI SDK (Gemini) to analyze documents.
Requires GOOGLE_API_KEY environment variable.
"""

import asyncio
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Dict, Optional, List

from pypdf import PdfReader, PdfWriter

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    genai = None  # type: ignore
    HAS_GEMINI = False

from alakazam.analyzers.base import DocumentAnalyzer
from alakazam.analyzers.sanitize import sanitize_analysis


class GeminiAnalyzer(DocumentAnalyzer):
    """
    Document analyzer using Google Gemini API.

    Uses the 'google-generativeai' SDK.
    Requires GOOGLE_API_KEY environment variable.

    The analyzer:
    1. Extracts first N pages of PDF to reduce processing time
    2. Uploads the PDF to Gemini (or sends as bytes/text depending on model)
    3. Parses the JSON response from Gemini
    4. Returns structured metadata
    """

    DEFAULT_MODEL = "gemini-1.5-flash"
    MAX_PDF_PAGES = 3
    TIMEOUT = 60  # seconds

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        api_key: Optional[str] = None,
        max_pages: int = MAX_PDF_PAGES,
        timeout: int = TIMEOUT,
        verbose: bool = False,
        type_registry: Optional[object] = None,
    ):
        """
        Initialize Gemini analyzer.

        Args:
            model_name: Gemini model to use (default: "gemini-1.5-flash")
            api_key: Google API key (default: from GOOGLE_API_KEY env var)
            max_pages: Maximum PDF pages to extract for analysis (default: 3)
            timeout: API timeout in seconds (default: 60)
            verbose: Enable verbose logging (default: False)
            type_registry: Optional TypeRegistry for document types
        """
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.max_pages = max_pages
        self.timeout = timeout
        self.verbose = verbose
        self.type_registry = type_registry
        self.naming_preferences: Optional[str] = None

        if HAS_GEMINI and self.api_key:
            genai.configure(api_key=self.api_key)

    async def analyze(self, document_path: Path) -> Optional[Dict]:
        """
        Analyze PDF using Gemini API.

        Args:
            document_path: Path to PDF file

        Returns:
            Dictionary with document metadata, or None if analysis fails
        """
        if not HAS_GEMINI:
            if self.verbose:
                print("    ❌ Error: google-generativeai library not installed.")
            return None

        if not self.api_key:
            if self.verbose:
                print("    ❌ Error: GOOGLE_API_KEY not found.")
            return None

        if self.verbose:
            print(f"  Analyzing (Gemini): {document_path.name}")

        temp_pdf = None
        try:
            # Extract first pages to temp file (run in executor - CPU bound)
            temp_pdf = await self._extract_first_pages(document_path)

            # Call Gemini API
            response_text = await self._call_gemini_api(temp_pdf)

            # Parse JSON response
            result = self._parse_response(response_text)
            if result:
                result = sanitize_analysis(result)

            if self.verbose and result:
                print(f"    Suggested: {result['new_filename']}")

            return result

        except Exception as e:
            if self.verbose:
                print(f"    ❌ Error analyzing document with Gemini: {e}")
            return None
        finally:
            # Clean up temp file if we created one
            if temp_pdf and temp_pdf != document_path and temp_pdf.exists():
                try:
                    temp_pdf.unlink()
                except Exception:
                    pass

    def validate_config(self) -> bool:
        """
        Validate Gemini configuration.

        Returns:
            True if library is installed and API key is present.
        """
        return HAS_GEMINI and bool(self.api_key)

    def set_naming_preferences(self, preferences: str) -> None:
        """Set user naming preferences for the analyzer."""
        self.naming_preferences = preferences

    async def _extract_first_pages(self, pdf_path: Path) -> Path:
        """Extract first N pages to temp file for processing."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_pages_sync, pdf_path)

    def _extract_pages_sync(self, pdf_path: Path) -> Path:
        """Synchronous PDF extraction (runs in executor)."""
        try:
            reader = PdfReader(pdf_path)
            writer = PdfWriter()
            num_pages = min(len(reader.pages), self.max_pages)

            for i in range(num_pages):
                writer.add_page(reader.pages[i])

            temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf", prefix="gemini_")
            os.close(temp_fd)
            temp_file = Path(temp_path)

            with open(temp_file, "wb") as f:
                writer.write(f)

            return temp_file
        except Exception as e:
            if self.verbose:
                print(f"   Warning: Could not extract pages ({e}), using full PDF")
            return pdf_path

    async def _call_gemini_api(self, pdf_path: Path) -> str:
        """Call Gemini API with PDF content."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._call_gemini_sync, pdf_path)

    def _call_gemini_sync(self, pdf_path: Path) -> str:
        """Synchronous Gemini API call."""
        model = genai.GenerativeModel(self.model_name)
        # Read PDF as bytes
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()

        prompt = self._build_prompt()
        
        # Gemini 1.5 supports document passing directly
        response = model.generate_content(
            [
                prompt,
                {
                    "mime_type": "application/pdf",
                    "data": pdf_data
                }
            ],
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )
        )
        
        return response.text

    def _parse_response(self, response_text: str) -> Optional[Dict]:
        """Parse Gemini output to extract JSON."""
        try:
            # Clean markdown if Gemini wrapped it
            json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            
            result = json.loads(response_text)
            
            required = ["document_date", "document_type", "new_filename", "description"]
            if all(k in result for k in required):
                return result
            
            if self.verbose:
                print(f"    ❌ Missing required fields in Gemini response")
            return None

        except json.JSONDecodeError as e:
            if self.verbose:
                print(f"    ❌ Error: Gemini response was not valid JSON: {e}")
            return None

    def _build_prompt(self) -> str:
        """Build analysis prompt for Gemini."""
        if self.type_registry and hasattr(self.type_registry, "get_all_types"):
            doc_types = ", ".join(sorted(self.type_registry.get_all_types()))
        else:
            doc_types = (
                "invoice, receipt, medical_statement, tax_document, "
                "insurance_claim, bank_statement, contract, letter"
            )

        preferences_section = ""
        if self.naming_preferences:
            preferences_section = f"\nRecent user overrides:\n{self.naming_preferences}\n"

        return f"""Analyze this PDF document and extract:
1. **Document Date**: YYYY-MM-DD
2. **Document Type**: Choose from: {doc_types} or suggest a new snake_case type.
3. **Suggested Filename**: "YYYY-MM-DD Descriptive Name.pdf" (max 80 chars, Title Case).
4. **Metadata**: Key identifying info (company, recipient, IDs, amounts).
5. **Alternative Filenames**: 2-3 meaningful variants.

{preferences_section}
Return ONLY a JSON object with these keys: document_date, document_type, new_filename, description, alternative_filenames, metadata."""

    def __repr__(self) -> str:
        return f"GeminiAnalyzer(model={self.model_name}, max_pages={self.max_pages})"
