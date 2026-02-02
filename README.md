# ✨ Alakazam

**AI-powered intelligent document renaming with adaptive type system**

Transform chaotic document filenames into organized, meaningful names using AI magic!

```bash
# Before
2022-11-06_JUROR AFFIDAVIT QUESTIONNAIRE.pdf
2022-11-26_$1.9.00.pdf
2022-11-11_GẸICo.pdf

# After (with alakazam)
2022-12-05 San Diego Superior Court Jury Summons Andrew Hao.pdf
2022-11-16 T-Mobile Final Bill Andrew.pdf
2022-11-11 GEICO Annual Mileage Certification Request Andrew Hao.pdf
```

## Features

- 🧠 **AI-Powered** - Uses Claude, GPT, or local models to understand document content
- 🔌 **Pluggable** - Swap AI providers, naming strategies, and storage backends
- 📊 **Adaptive Types** - Learns new document types as it encounters them
- 💰 **Cost-Effective** - Optimizes API usage (analyzes first 3 pages only)
- 🎯 **Smart Tracking** - Log-based tracking prevents duplicate processing
- 🚀 **Fast** - Async processing for batch operations
- 🛡️ **Safe** - Dry-run mode, backups, collision detection

## Quick Start

### Installation

```bash
pip install alakazam

# With Anthropic support
pip install alakazam[anthropic]

# With OpenAI support
pip install alakazam[openai]

# All features
pip install alakazam[all]
```

### Basic Usage

```bash
# Analyze and rename PDFs in a directory
alakazam rename /path/to/documents

# Dry run (preview only)
alakazam rename /path/to/documents --dry-run

# Use specific AI provider
alakazam rename /path/to/documents --analyzer anthropic

# Process in batches
alakazam rename /path/to/documents --batch-size 10 --continuous
```

### As a Library

```python
from alakazam import Alakazam
from alakazam.analyzers import AnthropicAnalyzer
from alakazam.naming import ISODateNaming

# Configure
alakazam = Alakazam(
    analyzer=AnthropicAnalyzer(api_key="your-key"),
    naming_strategy=ISODateNaming(),
    directory="/path/to/documents"
)

# Process files
result = await alakazam.process_batch(batch_size=10, dry_run=True)

# Review results
for file in result.files:
    print(f"{file.old_name} → {file.new_name}")
```

## How It Works

1. **Scan** - Finds unprocessed documents (checks rename log, not filename patterns)
2. **Analyze** - AI reads document content and extracts key information
3. **Generate** - Creates filename following configured naming strategy
4. **Validate** - Ensures filename is valid and collision-free
5. **Rename** - Renames file and logs the operation
6. **Learn** - Tracks new document types for future review

## Configuration

Create `~/.alakazam/config.yaml`:

```yaml
analyzer:
  type: anthropic  # or: claude_code, openai, local
  model: claude-sonnet-4-20250514
  api_key_env: ANTHROPIC_API_KEY

naming:
  strategy: iso_date  # YYYY-MM-DD format
  max_length: 80

types:
  use_builtin: true
  allow_suggestions: true  # Let AI suggest new types

storage:
  backend: local
  path: /path/to/documents

processing:
  batch_size: 5
  safe_mode: false
```

## Document Types

Built-in types include:
- `invoice`, `receipt`, `medical_statement`, `tax_form`
- `insurance_notice`, `bank_statement`, `legal_document`
- And more...

**Adaptive Learning**: When AI encounters documents that don't fit standard types, it suggests new ones. Review and promote frequently-used types:

```bash
alakazam types review          # See suggestions
alakazam types add jury_summons  # Add to standard list
```

## Extensibility

### Custom AI Analyzer

```python
from alakazam.analyzers import DocumentAnalyzer

class MyAnalyzer(DocumentAnalyzer):
    async def analyze(self, document_path):
        # Your custom AI logic
        return {
            "document_date": "2024-01-15",
            "document_type": "invoice",
            "new_filename": "2024-01-15 Custom Analysis.pdf",
            "description": "Analyzed by my model"
        }
```

### Custom Naming Strategy

```python
from alakazam.naming import NamingStrategy

class SemanticNaming(NamingStrategy):
    def generate_filename(self, analysis, original):
        # Your custom naming logic
        return f"{analysis['document_type']}/{analysis['document_date']}.pdf"
```

## CLI Commands

```bash
# Rename documents
alakazam rename <path> [options]

# Review document types
alakazam types list           # Show all types
alakazam types review         # Review suggestions
alakazam types add <type>     # Add to standard list

# Configuration
alakazam config init          # Create config file
alakazam config show          # Show current config
alakazam config set <key> <value>

# Version
alakazam --version
```

## Why Alakazam?

Existing tools either:
- Require manual rules (Hazel, Bulk Rename Utility)
- Are expensive (Adobe Acrobat)
- Don't understand content (traditional rename scripts)

**Alakazam** uses AI to actually read and understand your documents, then organizes them intelligently.

## Development

```bash
# Clone repo
git clone https://github.com/andrewhao/alakazam.git
cd alakazam

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/alakazam

# Linting
ruff check src/alakazam

# Format
black src/alakazam
```

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT License - see [LICENSE](LICENSE)

## Credits

Born from a personal need to organize hundreds of scanned documents. Built with:
- [Claude](https://www.anthropic.com/) for AI analysis
- [Click](https://click.palletsprojects.com/) for CLI
- [Rich](https://rich.readthedocs.io/) for beautiful output
- [Pydantic](https://docs.pydantic.dev/) for validation

---

Made with ✨ by [Andrew Hao](https://github.com/andrewhao)
