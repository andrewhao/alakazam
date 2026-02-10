"""Claude Code CLI-based document analyzer.

This analyzer shells out to the 'claude' CLI command to analyze documents.
Requires Claude Pro subscription but no API key.
"""

import asyncio
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional

from pypdf import PdfReader, PdfWriter

from alakazam.analyzers.base import DocumentAnalyzer


class ClaudeCodeAnalyzer(DocumentAnalyzer):
    """
    Document analyzer using Claude Code CLI.

    Shells out to 'claude' command (from Claude Pro subscription).
    No API key required - uses existing Claude Pro authentication.

    The analyzer:
    1. Extracts first N pages of PDF to reduce processing time
    2. Shells out to 'claude' CLI with the PDF
    3. Parses the JSON response from Claude
    4. Returns structured metadata

    Example:
        >>> analyzer = ClaudeCodeAnalyzer(verbose=True)
        >>> result = await analyzer.analyze(Path("invoice.pdf"))
        >>> print(result['new_filename'])
        "2024-01-15 Acme Corp Invoice 12345.pdf"
    """

    DEFAULT_CMD = "claude"
    MAX_PDF_PAGES = 3
    TIMEOUT = 120  # seconds

    def __init__(
        self,
        claude_cmd: str = DEFAULT_CMD,
        max_pages: int = MAX_PDF_PAGES,
        timeout: int = TIMEOUT,
        verbose: bool = False,
        type_registry: Optional[object] = None,
    ):
        """
        Initialize Claude Code analyzer.

        Args:
            claude_cmd: CLI command to invoke (default: "claude")
            max_pages: Maximum PDF pages to extract for analysis (default: 3)
            timeout: Subprocess timeout in seconds (default: 120)
            verbose: Enable verbose logging (default: False)
            type_registry: Optional TypeRegistry for document types
        """
        self.claude_cmd = claude_cmd
        self.max_pages = max_pages
        self.timeout = timeout
        self.verbose = verbose
        self.type_registry = type_registry
        self.naming_preferences: Optional[str] = None

    async def analyze(self, document_path: Path) -> Optional[Dict]:
        """
        Analyze PDF using Claude Code CLI.

        Args:
            document_path: Path to PDF file

        Returns:
            Dictionary with document metadata, or None if analysis fails

        The returned dictionary contains:
            - document_date: str (YYYY-MM-DD)
            - document_type: str (category)
            - new_filename: str (suggested filename)
            - description: str (human-readable)
            - metadata: dict (additional fields)
        """
        if self.verbose:
            print(f"  Analyzing: {document_path.name}")

        temp_pdf = None
        try:
            # Extract first pages to temp file (run in executor - CPU bound)
            temp_pdf = await self._extract_first_pages(document_path)

            # Build prompt with type registry info if available
            prompt = self._build_prompt()

            # Call Claude CLI
            response_text = await self._call_claude_cli(temp_pdf, prompt)

            # Parse JSON response
            result = self._parse_response(response_text)

            if self.verbose and result:
                print(f"    Suggested: {result['new_filename']}")

            return result

        except asyncio.TimeoutError:
            if self.verbose:
                print(f"    ❌ Error: Claude CLI timed out after {self.timeout}s")
            return None
        except Exception as e:
            if self.verbose:
                print(f"    ❌ Error analyzing document: {e}")
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
        Validate Claude Code CLI is available.

        Returns:
            True if 'claude' command is available, False otherwise
        """
        try:
            result = subprocess.run(
                [self.claude_cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    async def _extract_first_pages(self, pdf_path: Path) -> Path:
        """
        Extract first N pages to temp file for CLI processing.

        Runs in executor since pypdf operations are CPU-bound.

        Args:
            pdf_path: Path to source PDF

        Returns:
            Path to temp PDF file (caller must clean up)
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_pages_sync, pdf_path)

    def _extract_pages_sync(self, pdf_path: Path) -> Path:
        """
        Synchronous PDF extraction (runs in executor).

        Args:
            pdf_path: Path to source PDF

        Returns:
            Path to extracted PDF, or original path if extraction fails
        """
        try:
            reader = PdfReader(pdf_path)
            writer = PdfWriter()

            num_pages = min(len(reader.pages), self.max_pages)

            for i in range(num_pages):
                writer.add_page(reader.pages[i])

            # Create temp file
            temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf", prefix="claude_")
            os.close(temp_fd)
            temp_file = Path(temp_path)

            with open(temp_file, "wb") as f:
                writer.write(f)

            if self.verbose:
                original_size = pdf_path.stat().st_size
                new_size = temp_file.stat().st_size
                print(
                    f"   PDF optimization: {original_size:,} → {new_size:,} bytes "
                    f"({num_pages} page{'s' if num_pages != 1 else ''})"
                )

            return temp_file

        except Exception as e:
            if self.verbose:
                print(f"   Warning: Could not extract pages ({e}), using full PDF")
            return pdf_path

    async def _call_claude_cli(self, pdf_path: Path, prompt: str) -> str:
        """
        Call Claude Code CLI with PDF file.

        Args:
            pdf_path: Path to PDF file
            prompt: Analysis prompt

        Returns:
            CLI stdout response

        Raises:
            asyncio.TimeoutError: If subprocess times out
            Exception: If subprocess fails
        """
        # Create temp directory for Claude to work in
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy PDF to temp dir so Claude Code can read it
            temp_work_pdf = Path(temp_dir) / "document.pdf"
            shutil.copy2(pdf_path, temp_work_pdf)

            # Build full prompt with file reading instruction
            full_prompt = (
                f"Read the PDF file at {temp_work_pdf.absolute()} and analyze it.\n\n{prompt}"
            )

            # Build command
            cmd = [
                self.claude_cmd,
                "-p",  # Print mode (non-interactive)
                "--dangerously-skip-permissions",  # Auto-approve tool use
                "--output-format",
                "text",  # Text output
                full_prompt,
            ]

            if self.verbose:
                print(f"   Running: claude -p --dangerously-skip-permissions [prompt]")
                print(f"   Working directory: {temp_dir}")
                print(f"   PDF file: {temp_work_pdf}")

            # Run async subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=temp_dir,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=self.timeout
                )

                if process.returncode != 0:
                    if self.verbose:
                        print(f"    ❌ Error: Claude Code returned exit code {process.returncode}")
                        print(f"    stderr: {stderr.decode('utf-8')}")
                    raise Exception(f"Claude CLI exited with code {process.returncode}")

                response_text = stdout.decode("utf-8").strip()

                if self.verbose:
                    print(f"   Response length: {len(response_text)} chars")
                    print(f"   First 200 chars: {response_text[:200]}...")

                return response_text

            except asyncio.TimeoutError:
                process.kill()
                raise

    def _parse_response(self, response_text: str) -> Optional[Dict]:
        """
        Parse CLI output to extract JSON.

        Handles:
        - Markdown code blocks (```json...```)
        - Plain JSON objects
        - Extra text around JSON

        Args:
            response_text: Raw CLI output

        Returns:
            Parsed dictionary, or None if parsing fails
        """
        try:
            # Try to extract JSON from markdown code block
            json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r"\{[\s\S]*\}", response_text)
                if json_match:
                    response_text = json_match.group(0)

            # Parse JSON
            result = json.loads(response_text)

            # Validate required fields
            required = ["document_date", "document_type", "new_filename", "description"]
            missing = [f for f in required if f not in result]
            if missing:
                if self.verbose:
                    print(f"    ❌ Missing required fields: {', '.join(missing)}")
                return None

            return result

        except json.JSONDecodeError as e:
            if self.verbose:
                print(f"    ❌ Error: Response was not valid JSON: {e}")
                print(f"    Response preview: {response_text[:500]}...")
            return None

    def _build_prompt(self) -> str:
        """
        Build analysis prompt.

        Uses type registry if available to provide document type suggestions.

        Returns:
            Formatted prompt string
        """
        # Get document types from registry if available
        if self.type_registry and hasattr(self.type_registry, "get_all_types"):
            doc_types = ", ".join(sorted(self.type_registry.get_all_types()))
        else:
            # Default fallback types
            doc_types = (
                "invoice, receipt, medical_statement, tax_document, "
                "insurance_claim, bank_statement, contract, letter"
            )

        preferences_section = ""
        if self.naming_preferences:
            preferences_section = (
                "\nRecent user overrides (follow these preferences when reasonable):\n"
                f"{self.naming_preferences}\n"
            )

        return f"""Analyze this PDF document and extract the following information:

1. **Document Date**: The actual date ON the document (not the scan date). Look for dates in headers, "Date:" fields, etc. Format: YYYY-MM-DD
2. **Document Type**: Choose the best match from this list, OR suggest a new type if none fit well:

   Standard types: {doc_types}

   If none of these accurately describe this document, suggest a new type using snake_case
   (e.g., "medical_prescription", "employment_contract", "warranty_document").
   Choose existing types when possible to maintain consistency.

3. **Suggested Filename**: Following the format "YYYY-MM-DD <descriptive name>.pdf"
   - Use the document date, not the scan date
   - Include document type, company/provider name, and key identifiers
   - Keep under 80 characters
   - Use title case
   - Examples:
     * "2022-08-16 Homesite Insurance Claim Denial Andrew Hao.pdf"
     * "2022-09-02 Delta Dental Welcome Letter Andrew Hao.pdf"
     * "2022-08-30 Future Automotive Service Order Andrew Hao.pdf"

4. **Metadata**: Extract relevant fields like:
   - provider/company name
   - patient/customer/recipient name
   - amounts, invoice numbers, claim numbers, etc.
   - any other relevant identifying information

5. **Alternative Filenames**: Provide 2-3 alternative filename suggestions
   - Must be valid filenames and follow the same format
   - Keep under 80 characters
   - Make them meaningfully different (e.g., include/exclude a person name or ID)

{preferences_section}
Return your response in this exact JSON format (no other text):
{{
  "document_date": "YYYY-MM-DD",
  "document_type": "category",
  "new_filename": "YYYY-MM-DD Descriptive Name.pdf",
  "description": "Brief human-readable description",
  "alternative_filenames": [
    "YYYY-MM-DD Alternate Name.pdf",
    "YYYY-MM-DD Another Variant.pdf"
  ],
  "metadata": {{
    "key": "value"
  }}
}}

Only return the JSON, no other text."""

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ClaudeCodeAnalyzer(cmd={self.claude_cmd}, "
            f"max_pages={self.max_pages}, timeout={self.timeout})"
        )
