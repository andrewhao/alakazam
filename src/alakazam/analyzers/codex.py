"""OpenAI Codex CLI-based document analyzer."""

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


class CodexAnalyzer(DocumentAnalyzer):
    """
    Document analyzer using OpenAI Codex CLI.

    Shells out to the `codex` command for analysis.
    Uses `codex exec` in non-interactive mode and reads the final message
    from a temporary output file.
    """

    DEFAULT_CMD = "codex"
    MAX_PDF_PAGES = 3
    TIMEOUT = 120  # seconds

    def __init__(
        self,
        codex_cmd: str = DEFAULT_CMD,
        max_pages: int = MAX_PDF_PAGES,
        timeout: int = TIMEOUT,
        verbose: bool = False,
        type_registry: Optional[object] = None,
        _test_output_path: Optional[Path] = None,
    ):
        """
        Initialize Codex analyzer.

        Args:
            codex_cmd: CLI command to invoke (default: "codex")
            max_pages: Maximum PDF pages to extract for analysis (default: 3)
            timeout: Subprocess timeout in seconds (default: 120)
            verbose: Enable verbose logging (default: False)
            type_registry: Optional TypeRegistry for document types
            _test_output_path: Optional path override for tests
        """
        self.codex_cmd = codex_cmd
        self.max_pages = max_pages
        self.timeout = timeout
        self.verbose = verbose
        self.type_registry = type_registry
        self._test_output_path = _test_output_path

    async def analyze(self, document_path: Path) -> Optional[Dict]:
        """
        Analyze PDF using Codex CLI.

        Args:
            document_path: Path to PDF file

        Returns:
            Dictionary with document metadata, or None if analysis fails
        """
        if self.verbose:
            print(f"  Analyzing: {document_path.name}")

        temp_pdf = None
        try:
            temp_pdf = await self._extract_first_pages(document_path)
            prompt = self._build_prompt()
            response_text = await self._call_codex_cli(temp_pdf, prompt)
            result = self._parse_response(response_text)

            if self.verbose and result:
                print(f"    Suggested: {result['new_filename']}")

            return result

        except asyncio.TimeoutError:
            if self.verbose:
                print(f"    ❌ Error: Codex CLI timed out after {self.timeout}s")
            return None
        except Exception as e:
            if self.verbose:
                print(f"    ❌ Error analyzing document: {e}")
            return None
        finally:
            if temp_pdf and temp_pdf != document_path and temp_pdf.exists():
                try:
                    temp_pdf.unlink()
                except Exception:
                    pass

    def validate_config(self) -> bool:
        """Validate Codex CLI is available."""
        try:
            result = subprocess.run(
                [self.codex_cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    async def _extract_first_pages(self, pdf_path: Path) -> Path:
        """Extract first N pages to temp file for CLI processing."""
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

            temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf", prefix="codex_")
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

    async def _call_codex_cli(self, pdf_path: Path, prompt: str) -> str:
        """
        Call Codex CLI with PDF file.

        Uses:
          codex exec --sandbox read-only --output-last-message <file> -
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            temp_work_pdf = temp_dir_path / "document.pdf"
            shutil.copy2(pdf_path, temp_work_pdf)

            full_prompt = (
                f"Read the PDF file at {temp_work_pdf.absolute()} and analyze it.\n\n{prompt}"
            )

            output_path = self._test_output_path or (temp_dir_path / "codex_output.json")

            cmd = [
                self.codex_cmd,
                "exec",
                "--cd",
                str(temp_dir_path),
                "--skip-git-repo-check",
                "--sandbox",
                "read-only",
                "--output-last-message",
                str(output_path),
                "-",
            ]

            if self.verbose:
                print("   Running: codex exec --sandbox read-only")
                print(f"   Working directory: {temp_dir_path}")
                print(f"   PDF file: {temp_work_pdf}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(temp_dir_path),
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(full_prompt.encode("utf-8")), timeout=self.timeout
                )

                if process.returncode != 0:
                    if self.verbose:
                        print(
                            f"    ❌ Error: Codex CLI returned exit code {process.returncode}"
                        )
                        print(f"    stderr: {stderr.decode('utf-8')}")
                    raise Exception(f"Codex CLI exited with code {process.returncode}")

                if not output_path.exists():
                    raise Exception("Codex CLI did not produce output file")

                response_text = output_path.read_text(encoding="utf-8").strip()

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
        """
        try:
            json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            else:
                json_match = re.search(r"\{[\s\S]*\}", response_text)
                if json_match:
                    response_text = json_match.group(0)

            result = json.loads(response_text)

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
        """Build analysis prompt."""
        if self.type_registry and hasattr(self.type_registry, "get_all_types"):
            doc_types = ", ".join(sorted(self.type_registry.get_all_types()))
        else:
            doc_types = (
                "invoice, receipt, medical_statement, tax_document, "
                "insurance_claim, bank_statement, contract, letter"
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

Return your response in this exact JSON format (no other text):
{{
  "document_date": "YYYY-MM-DD",
  "document_type": "category",
  "new_filename": "YYYY-MM-DD Descriptive Name.pdf",
  "description": "Brief human-readable description",
  "metadata": {{
    "key": "value"
  }}
}}

Only return the JSON, no other text."""

    def __repr__(self) -> str:
        return (
            f"CodexAnalyzer(cmd={self.codex_cmd}, "
            f"max_pages={self.max_pages}, timeout={self.timeout})"
        )
