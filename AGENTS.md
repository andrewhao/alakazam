# AGENTS.md - Developer Guide for AI Assistants

This guide helps AI agents understand and work on the Alakazam codebase.

## Project Overview

**Alakazam** is an AI-powered document renaming system that transforms messy PDF filenames into organized, meaningful names using AI analysis.

**Core Concept:** Analyze PDF content → Extract metadata → Generate intelligent filename

Example:
```
Before: 2022-11-06_JUROR AFFIDAVIT QUESTIONNAIRE.pdf
After:  2022-12-05 San Diego Superior Court Jury Summons Andrew Hao.pdf
```

## Architecture

### Plugin-Based Design

Alakazam uses a **pluggable architecture** with abstract base classes:

```
┌─────────────────────────────────────────────────────────┐
│                    Alakazam Core                        │
│                 (src/alakazam/core/)                    │
└────────────┬────────────────────────────────────────────┘
             │
             ├──► DocumentAnalyzer (analyze PDF → metadata)
             │    └─ ClaudeCodeAnalyzer (CLI-based, no API key)
             │    └─ CodexAnalyzer (OpenAI Codex CLI-based)
             │    └─ AntigravityAnalyzer (Antigravity CLI 'agy', no API key)
             │    └─ AnthropicAnalyzer (API-based, future)
             │    └─ OpenAIAnalyzer (API-based, future)
             │
             ├──► NamingStrategy (metadata → filename)
             │    └─ ISODateNaming (YYYY-MM-DD format)
             │
             ├──► Storage (file operations)
             │    └─ LocalStorage (local filesystem)
             │
             ├──► TypeRegistry (document type management)
             │    └─ Registry with builtin types
             │
             └──► Tracker (prevent duplicate processing)
                  └─ JSONTracker (JSONL log file)
```

### Key Components

#### 1. Document Analyzers (`src/alakazam/analyzers/`)

**Base Class:** `DocumentAnalyzer` (abstract)

**Contract:**
```python
async def analyze(self, document_path: Path) -> Optional[Dict]:
    """
    Returns:
        {
            "document_date": "YYYY-MM-DD",
            "document_type": "invoice",
            "new_filename": "2024-01-15 Acme Corp Invoice.pdf",
            "description": "Human-readable description",
            "metadata": {...}
        }
    """

def validate_config(self) -> bool:
    """Check if analyzer is properly configured"""
```

**Implementations:**
- **ClaudeCodeAnalyzer** - Uses Claude Code CLI (requires Claude Pro, no API key)
  - Location: `src/alakazam/analyzers/claude_code.py`
  - Async subprocess-based
  - Extracts first N pages for optimization
  - Parses JSON from CLI output
- **CodexAnalyzer** - Uses OpenAI Codex CLI (`codex`)
  - Location: `src/alakazam/analyzers/codex.py`
  - Non-interactive CLI execution with sandbox restrictions
- **AntigravityAnalyzer** - Uses Google Antigravity CLI (`agy`)
  - Location: `src/alakazam/analyzers/antigravity.py`
  - Async subprocess-based non-interactive print mode (`agy -p ...`)
  - No API key required; leverages existing local CLI authentication


#### 2. Naming Strategies (`src/alakazam/naming/`)

**Base Class:** `NamingStrategy` (abstract)

**Implementations:**
- **ISODateNaming** - Formats as "YYYY-MM-DD Description.pdf"

#### 3. Storage Backends (`src/alakazam/storage/`)

**Base Class:** `Storage` (abstract)

**Implementations:**
- **LocalStorage** - Local filesystem operations with collision detection

#### 4. Type Registry (`src/alakazam/types/`)

- Manages document type definitions
- Learns new types dynamically
- Builtin types: invoice, medical_statement, tax_document, etc.

#### 5. Tracker (`src/alakazam/core/tracker.py`)

- JSONL log file tracking
- Prevents duplicate processing
- Stores processing history

## Development Setup

### Prerequisites

- Python 3.10+
- `uv` (recommended) or `pip`
- Claude Code CLI (for ClaudeCodeAnalyzer)

### Installation

```bash
# Clone and navigate to repo
cd alakazam

# Install with dependencies
uv pip install -e .

# Or with specific extras
uv pip install -e ".[anthropic]"  # Anthropic API support
uv pip install -e ".[all]"        # All features + dev tools
```

### Project Structure

```
alakazam/
├── src/alakazam/          # Main package
│   ├── analyzers/         # Document analyzers
│   │   ├── base.py        # Abstract base
│   │   └── claude_code.py # Claude CLI implementation
│   ├── naming/            # Naming strategies
│   ├── storage/           # Storage backends
│   ├── types/             # Type registry
│   ├── core/              # Core logic
│   │   ├── renamer.py     # Main Alakazam class
│   │   ├── tracker.py     # Processing tracker
│   │   └── result.py      # Result types
│   └── cli/               # CLI interface
├── test_run/              # Integration tests & samples
│   ├── test_claude_code_e2e.py
│   └── test_alakazam_integration_e2e.py
├── examples/              # Usage examples
│   └── claude_code_usage.py
├── tests/                 # Unit tests
└── pyproject.toml         # Dependencies & config
```

## Common Development Tasks

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/analyzers/test_claude_code.py

# Run with coverage
uv run pytest --cov=alakazam

# Run end-to-end tests (requires Claude CLI)
uv run python test_run/test_claude_code_e2e.py

# Run integration tests
uv run python test_run/test_alakazam_integration_e2e.py
```

### Running Examples

```bash
# Usage examples
uv run python examples/claude_code_usage.py
```

### Running the CLI

```bash
# Dry run (no actual renaming)
uv run alakazam rename /path/to/pdfs --dry-run

# Actual rename with confirmation
uv run alakazam rename /path/to/pdfs

# Verbose output
uv run alakazam rename /path/to/pdfs --verbose --dry-run
```

### Code Quality

```bash
# Format code
uv run black src/ tests/

# Lint
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

## Adding a New Analyzer

To add a new document analyzer (e.g., for OpenAI, Google, local models):

### 1. Create the Analyzer Class

**File:** `src/alakazam/analyzers/your_analyzer.py`

```python
from pathlib import Path
from typing import Dict, Optional
from alakazam.analyzers.base import DocumentAnalyzer


class YourAnalyzer(DocumentAnalyzer):
    """
    Document analyzer using [Your Service].

    Brief description of what makes this analyzer unique.
    """

    def __init__(self, api_key: str, **options):
        """Initialize with required configuration."""
        self.api_key = api_key
        # ... other config

    async def analyze(self, document_path: Path) -> Optional[Dict]:
        """
        Analyze PDF and return metadata.

        Returns:
            Dict with required fields:
            - document_date: str (YYYY-MM-DD)
            - document_type: str
            - new_filename: str
            - description: str
            - metadata: dict (optional)

            Returns None if analysis fails.
        """
        # 1. Read/extract PDF content
        # 2. Call your AI service
        # 3. Parse response
        # 4. Return structured dict or None
        pass

    def validate_config(self) -> bool:
        """Validate configuration (API key, etc.)"""
        # Check if API key is valid, service is reachable, etc.
        pass
```

### 2. Export the Analyzer

**File:** `src/alakazam/analyzers/__init__.py`

```python
from alakazam.analyzers.base import DocumentAnalyzer
from alakazam.analyzers.claude_code import ClaudeCodeAnalyzer
from alakazam.analyzers.your_analyzer import YourAnalyzer  # Add this

__all__ = ["DocumentAnalyzer", "ClaudeCodeAnalyzer", "YourAnalyzer"]
```

### 3. Create Tests

**File:** `tests/unit/analyzers/test_your_analyzer.py`

```python
import pytest
from pathlib import Path
from alakazam.analyzers import YourAnalyzer


@pytest.mark.asyncio
async def test_analyze_success(mocker, tmp_path):
    """Test successful analysis."""
    # Mock your API calls
    # Test the analyze() method
    # Verify return format
    pass


def test_validate_config():
    """Test configuration validation."""
    # Test valid config
    # Test invalid config
    pass
```

### 4. Create End-to-End Test

**File:** `test_run/test_your_analyzer_e2e.py`

```python
#!/usr/bin/env python3
import asyncio
from pathlib import Path
from alakazam.analyzers import YourAnalyzer


async def main():
    analyzer = YourAnalyzer(api_key="...")

    # Test with real PDF
    result = await analyzer.analyze(Path("test.pdf"))
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
```

### 5. Create Example

**File:** `examples/your_analyzer_usage.py`

Show basic usage patterns, configuration options, and common workflows.

### 6. Update Documentation

Add your analyzer to:
- README.md (list of supported analyzers)
- This AGENTS.md file

## Important Implementation Notes

### Async/Await Pattern

All analyzers use async/await:

```python
# Correct
async def analyze(self, document_path: Path) -> Optional[Dict]:
    result = await self.call_api(document_path)
    return result

# Usage
analyzer = YourAnalyzer()
result = await analyzer.analyze(pdf_path)
```

### Error Handling Strategy

**Return None on failure, don't raise exceptions:**

```python
async def analyze(self, document_path: Path) -> Optional[Dict]:
    try:
        # ... analysis logic
        return result_dict
    except APIError as e:
        if self.verbose:
            print(f"❌ API error: {e}")
        return None  # Don't raise, return None
    except Exception as e:
        if self.verbose:
            print(f"❌ Error: {e}")
        return None
```

### PDF Optimization

For API-based analyzers, extract first N pages to reduce costs:

```python
from pypdf import PdfReader, PdfWriter

def _extract_first_pages(self, pdf_path: Path, max_pages: int = 3) -> Path:
    """Extract first N pages to temp file."""
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for i in range(min(len(reader.pages), max_pages)):
        writer.add_page(reader.pages[i])

    # Write to temp file
    # Return temp path
```

### Response Validation

Always validate the AI response structure:

```python
def _validate_response(self, result: Dict) -> bool:
    """Validate AI response has required fields."""
    required = ['document_date', 'document_type', 'new_filename', 'description']

    # Check all required fields exist
    if not all(field in result for field in required):
        return False

    # Validate date format
    try:
        datetime.strptime(result['document_date'], '%Y-%m-%d')
    except ValueError:
        return False

    # Validate filename ends with .pdf
    if not result['new_filename'].endswith('.pdf'):
        return False

    return True
```

## Testing Philosophy

### Test Pyramid

1. **Unit Tests** (`tests/unit/`) - Mock external dependencies
   - Fast, isolated
   - Test individual methods
   - Use pytest-asyncio for async tests

2. **Integration Tests** (`test_run/*_integration_e2e.py`) - Test component interaction
   - Test analyzer + full workflow
   - Use temp directories
   - Verify file operations

3. **End-to-End Tests** (`test_run/*_e2e.py`) - Test with real services
   - Optional (may require API keys, CLI tools)
   - Test actual AI service calls
   - Use real PDFs

### Running Tests Without External Dependencies

Tests should be runnable without API keys or external services:

```python
@pytest.mark.skipif(
    not has_api_key(),
    reason="Requires API key"
)
async def test_with_real_api():
    # Test with real API
    pass
```

## Git Workflow

### Branching Strategy

```bash
# Feature branch
git checkout -b feature/your-feature-name

# Bug fix branch
git checkout -b fix/bug-description
```

### Commit Messages

Follow the existing style:

```
Add [Feature] - Brief description

Longer description with details about:
- What was added/changed
- Why it was needed
- Key implementation details

Test Results:
- Test coverage
- Key validations

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### Pre-commit Checklist

Before committing:
- [ ] All tests pass (`uv run pytest`)
- [ ] Code is formatted (`uv run black src/ tests/`)
- [ ] No linting errors (`uv run ruff check src/`)
- [ ] Type hints are correct (`uv run mypy src/`)
- [ ] Documentation is updated

## Debugging Tips

### Verbose Mode

Enable verbose output to see what's happening:

```python
analyzer = ClaudeCodeAnalyzer(verbose=True)
```

Shows:
- PDF extraction details
- CLI commands being run
- Response lengths and previews
- Error messages

### Logging

Check the Alakazam log file:

```bash
# Default log location
cat .alakazam.log | jq .

# See recent operations
tail -f .alakazam.log
```

### Testing Individual Components

Test components in isolation:

```python
# Test analyzer alone
analyzer = ClaudeCodeAnalyzer(verbose=True)
result = await analyzer.analyze(Path("test.pdf"))
print(result)

# Test naming strategy
strategy = ISODateNaming()
filename = strategy.generate_filename(metadata)
print(filename)
```

## Common Issues & Solutions

### Issue: Import errors

**Solution:** Reinstall package in development mode
```bash
uv pip install -e .
```

### Issue: Tests can't find test PDFs

**Solution:** Tests look in `test_run/` directory. Ensure test PDFs exist:
```bash
ls test_run/*.pdf
```

### Issue: Claude CLI not found

**Solution:** Install Claude Code CLI or use mock for tests:
```python
@pytest.mark.skipif(
    shutil.which("claude") is None,
    reason="Requires Claude CLI"
)
```

### Issue: Async test failures

**Solution:** Use `pytest-asyncio` and mark tests:
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_call()
    assert result is not None
```

## API Reference

### DocumentAnalyzer Base Class

```python
class DocumentAnalyzer(ABC):
    @abstractmethod
    async def analyze(self, document_path: Path) -> Optional[Dict]:
        """Analyze document and return metadata."""

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate configuration."""
```

**Required Return Format:**
```python
{
    "document_date": "2024-01-15",           # YYYY-MM-DD
    "document_type": "invoice",              # snake_case
    "new_filename": "2024-01-15 Acme.pdf",   # Full filename
    "description": "Invoice from Acme",      # Human-readable
    "metadata": {                            # Optional extra data
        "company": "Acme Corp",
        "amount": "$100.00"
    }
}
```

## Resources

- **Repository:** https://github.com/andrewhao/alakazam
- **Issues:** https://github.com/andrewhao/alakazam/issues
- **Claude CLI:** https://claude.com/cli

## Quick Reference Commands

```bash
# Development
uv pip install -e ".[all]"              # Install with dev dependencies
uv run pytest                           # Run tests
uv run black src/ tests/                # Format code
uv run alakazam rename /path --dry-run  # Test CLI

# Testing
uv run pytest tests/unit/              # Unit tests only
uv run pytest --cov=alakazam           # With coverage
uv run python test_run/test_*_e2e.py   # End-to-end tests

# Examples
uv run python examples/claude_code_usage.py
```

## Contributing Guidelines

1. Create a feature branch
2. Write tests first (TDD approach)
3. Implement feature
4. Ensure all tests pass
5. Update documentation
6. Commit with descriptive message
7. Push and create PR

---

**Last Updated:** 2026-02-02
**For Questions:** See GitHub issues or README.md
