# Alakazam Usage Guide

## Current Status

**⚠️ Important**: The CLI is currently a placeholder. The AI analyzer needs to be implemented before the tool is fully functional. However, the **core architecture is complete and tested**.

This guide shows you how everything works once the analyzer is implemented.

---

## How to Specify the Target Directory

### Option 1: CLI (when fully implemented)

```bash
# Basic usage - specify directory as argument
alakazam rename /path/to/your/documents

# Examples
alakazam rename ~/Documents/Scans
alakazam rename /Users/you/Downloads/PDFs
alakazam rename ./invoices
```

### Option 2: Python API (works now)

```python
from pathlib import Path
from alakazam import Alakazam
from alakazam.core import AlakazamConfig, JSONTracker  # Config and tracking
from alakazam.analyzers import DocumentAnalyzer  # Your custom analyzer
from alakazam.naming import ISODateNaming
from alakazam.storage import LocalStorage
from alakazam.types import TypeRegistry

# Specify directory when creating LocalStorage
target_directory = Path("~/Documents/Scans").expanduser()

alakazam = Alakazam(
    analyzer=YourAnalyzer(),  # Implement this
    naming_strategy=ISODateNaming(),
    storage=LocalStorage(target_directory),  # ← Target directory here
    tracker=JSONTracker(target_directory / ".alakazam.log"),  # ← Log location
    type_registry=TypeRegistry(),
    config=AlakazamConfig(
        batch_size=5,
        dry_run=False,
        verbose=True
    )
)

# Process files in that directory
result = await alakazam.process_batch()
```

---

## Where the Rename Log is Stored

### Default Location

The rename log (tracking file) is stored **in the same directory as your documents** by default:

```
/path/to/your/documents/
├── .alakazam.log          ← Rename log stored here
├── document1.pdf
├── document2.pdf
└── document3.pdf
```

### Log File Format

The `.alakazam.log` file is a JSON file that tracks all rename operations:

```json
{
  "metadata": {
    "version": "1.0"
  },
  "renames": [
    {
      "old_name": "scan_001.pdf",
      "new_name": "2024-01-15 Acme Corp Invoice 12345.pdf",
      "document_date": "2024-01-15",
      "document_type": "invoice",
      "description": "Invoice from Acme Corp",
      "metadata": {
        "company": "Acme Corp",
        "invoice_number": "12345",
        "amount": "$150.00"
      }
    },
    {
      "old_name": "IMG_2341.pdf",
      "new_name": "2024-01-20 Medical Statement Kaiser Permanente.pdf",
      "document_date": "2024-01-20",
      "document_type": "medical_statement",
      "description": "Medical statement from Kaiser"
    }
  ]
}
```

### Custom Log Location

You can specify a custom log location:

```python
# Store log in a different location
tracker = JSONTracker(Path("~/.config/alakazam/rename_log.json"))

# Or use a project-specific log
tracker = JSONTracker(Path("/var/log/alakazam/documents.json"))
```

### Why Track Renames?

The log serves several purposes:

1. **Prevent Duplicate Processing**: Files are only processed once
2. **Audit Trail**: See what was renamed and when
3. **Recovery**: Understand original filenames if needed
4. **Analytics**: Track document types discovered over time
5. **Type Learning**: Feed the adaptive type system

---

## Complete Working Example

Here's a full example showing how to use Alakazam (once you implement an analyzer):

### 1. Create a Mock Analyzer (for testing)

```python
# examples/mock_analyzer.py
from pathlib import Path
from typing import Dict, Optional
from alakazam.analyzers import DocumentAnalyzer

class MockAnalyzer(DocumentAnalyzer):
    """Mock analyzer for testing without AI API."""

    async def analyze(self, document_path: Path) -> Optional[Dict]:
        """Return mock analysis data."""
        return {
            "document_date": "2024-01-15",
            "document_type": "invoice",
            "new_filename": f"2024-01-15 Mock Analysis {document_path.stem}.pdf",
            "description": f"Mock analysis of {document_path.name}",
            "metadata": {
                "analyzer": "mock",
                "confidence": 1.0
            }
        }

    def validate_config(self) -> bool:
        """Mock analyzer is always valid."""
        return True
```

### 2. Use It to Process Documents

```python
# examples/basic_usage.py
import asyncio
from pathlib import Path
from alakazam import Alakazam
from alakazam.core import AlakazamConfig, JSONTracker
from alakazam.naming import ISODateNaming
from alakazam.storage import LocalStorage
from alakazam.types import TypeRegistry
from mock_analyzer import MockAnalyzer

async def main():
    # Configuration
    target_dir = Path("~/Documents/ToProcess").expanduser()
    log_file = target_dir / ".alakazam.log"

    # Create Alakazam instance
    alakazam = Alakazam(
        analyzer=MockAnalyzer(),
        naming_strategy=ISODateNaming(max_length=80, title_case=True),
        storage=LocalStorage(target_dir),
        tracker=JSONTracker(log_file),
        type_registry=TypeRegistry(),
        config=AlakazamConfig(
            batch_size=5,
            dry_run=True,  # Preview mode - won't actually rename
            verbose=True
        )
    )

    # Process one batch
    print("Processing documents...")
    result = await alakazam.process_batch()

    # Show results
    print(f"\n✓ Processed {len(result.files)} files in {result.duration:.2f}s")
    print(f"  Success: {result.success_count}")
    print(f"  Errors: {result.error_count}")
    print(f"  Dry run: {result.dry_run_count}")

    # Show individual results
    for file_result in result.files:
        if file_result.new_name:
            print(f"  {file_result.old_name} → {file_result.new_name}")
        else:
            print(f"  ✗ {file_result.old_name}: {file_result.error}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Run It

```bash
# Dry run (preview only)
python examples/basic_usage.py

# To actually rename files, edit the script:
# config=AlakazamConfig(dry_run=False, ...)
```

---

## CLI Usage (When Implemented)

### Basic Commands

```bash
# Specify target directory as first argument
alakazam rename /path/to/documents

# Process 10 files at a time
alakazam rename /path/to/documents --batch-size 10

# Dry run (preview only)
alakazam rename /path/to/documents --dry-run

# Verbose output
alakazam rename /path/to/documents --verbose

# Process ALL files (multiple batches)
alakazam rename /path/to/documents --continuous

# Combine options
alakazam rename ~/Documents/Scans --batch-size 10 --continuous --verbose
```

### Document Type Management

```bash
# List all built-in document types
alakazam types list

# Review AI-suggested new types
alakazam types review

# Add a suggested type to standard list
alakazam types add jury_summons
```

---

## Configuration File (Future)

You can create `~/.alakazam/config.yaml` to set defaults:

```yaml
# Default target directory
directory: ~/Documents/Scans

# Log file location
log_file: ~/.alakazam/rename_log.json

# Analyzer settings
analyzer:
  type: anthropic
  model: claude-sonnet-4-20250514
  api_key_env: ANTHROPIC_API_KEY

# Naming strategy
naming:
  strategy: iso_date
  max_length: 80
  title_case: true

# Processing defaults
processing:
  batch_size: 5
  dry_run: false
  verbose: false
```

Then you can just run:

```bash
alakazam rename  # Uses config file defaults
```

---

## Directory Structure

Here's what a typical working directory looks like:

```
~/Documents/Scans/
├── .alakazam.log                    ← Rename log (auto-created)
├── scan_001.pdf                     ← Unprocessed files
├── scan_002.pdf
├── IMG_2341.pdf
└── 2024-01-15 Previously Renamed.pdf  ← Already processed (in log)
```

After running Alakazam:

```
~/Documents/Scans/
├── .alakazam.log                              ← Updated with new renames
├── 2024-01-15 Acme Corp Invoice 12345.pdf    ← Renamed!
├── 2024-01-20 Medical Statement Kaiser.pdf   ← Renamed!
├── 2024-01-22 Bank Statement Chase.pdf       ← Renamed!
└── 2024-01-15 Previously Renamed.pdf          ← Skipped (already in log)
```

---

## Important Notes

### 1. Files Are Renamed In-Place

Alakazam renames files **in the same directory**. It doesn't move them elsewhere.

### 2. Tracking Prevents Duplicates

Once a file is processed (appears in `.alakazam.log`), it won't be processed again - even if you run Alakazam multiple times.

### 3. Log File is Critical

**Don't delete `.alakazam.log`** - it's how Alakazam knows which files it has already processed. Without it, files could be processed multiple times.

### 4. Dry Run First!

Always use `--dry-run` first to preview renames before making changes:

```bash
alakazam rename /path/to/docs --dry-run
```

### 5. Collision Detection

If a renamed file would overwrite an existing file, Alakazam will:
- Skip the rename
- Mark it as an error
- Report the collision

---

## Troubleshooting

### "No files to process"

Check:
1. Are there PDF files in the directory?
2. Is `.alakazam.log` marking them as already processed?
3. Delete `.alakazam.log` to reprocess (careful!)

### "File already exists"

The new filename collides with an existing file. Options:
1. Manually rename the conflicting file
2. Adjust the naming strategy to avoid collisions

### Where's my log file?

```bash
# Find it
ls -la /path/to/your/documents/.alakazam.log

# View it
cat /path/to/your/documents/.alakazam.log | jq .

# Count processed files
cat /path/to/your/documents/.alakazam.log | jq '.renames | length'
```

---

## Next Steps

1. **Implement an Analyzer** - See `NEXT_STEPS.md` Phase 1
2. **Test with Mock Data** - Use the MockAnalyzer example above
3. **Run in Dry Mode** - Always preview first
4. **Check the Log** - Verify tracking works correctly
5. **Process Real Files** - Remove `--dry-run` flag

---

**Questions?** See the main README.md or open an issue on GitHub.
