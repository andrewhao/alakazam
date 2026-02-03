# Alakazam Examples

This directory contains example scripts showing how to use Alakazam.

## Available Examples

### 1. `mock_analyzer.py`

A mock document analyzer that returns fake analysis data. Use this to test Alakazam without needing an AI API key.

**Features:**
- No API key required
- Returns realistic-looking data
- Simple heuristics based on filename

### 2. `basic_usage.py`

Complete working example showing how to use Alakazam to process documents.

**Features:**
- Creates target directory if needed
- Uses mock analyzer (no API required)
- Shows verbose output
- Runs in dry-run mode by default (safe)

## How to Run

### Step 1: Install Alakazam

```bash
# From the project root
cd /path/to/alakazam
uv pip install -e .
```

### Step 2: Create Test Documents

```bash
# Create a test directory with sample PDFs
mkdir -p ~/Documents/TestDocs
cd ~/Documents/TestDocs

# Create some test PDFs (you can use any PDFs you have)
cp /path/to/your/pdfs/*.pdf .

# Or create empty PDFs for testing (on macOS)
echo "Test" | textutil -stdin -output test_invoice.pdf -format txt -convert pdf
echo "Test" | textutil -stdin -output medical_record.pdf -format txt -convert pdf
echo "Test" | textutil -stdin -output tax_document.pdf -format txt -convert pdf
```

### Step 3: Run Basic Example

```bash
cd examples
python basic_usage.py
```

**Expected Output:**

```
============================================================
Alakazam - AI-Powered Document Renaming
============================================================

Target Directory: /Users/you/Documents/TestDocs
Log File: /Users/you/Documents/TestDocs/.alakazam.log

Processing documents...
------------------------------------------------------------
[1/3] Processing: test_invoice.pdf
  Analyzing: test_invoice.pdf
    Suggested: 2024-01-15 Mock Invoice test_invoice.pdf
  [DRY RUN] Would rename to: 2024-01-15 Mock Invoice test_invoice.pdf

[2/3] Processing: medical_record.pdf
  Analyzing: medical_record.pdf
    Suggested: 2024-01-15 Mock Medical Document medical_record.pdf
  [DRY RUN] Would rename to: 2024-01-15 Mock Medical Document medical_record.pdf

============================================================
RESULTS
============================================================
Total Files: 3
Success: 0
Errors: 0
Dry Run: 3
Skipped: 0
Duration: 0.02s

File Details:
------------------------------------------------------------
→ test_invoice.pdf
  → 2024-01-15 Mock Invoice test_invoice.pdf

→ medical_record.pdf
  → 2024-01-15 Mock Medical Document medical_record.pdf

============================================================
```

### Step 4: Actually Rename Files

Edit `basic_usage.py` and change:

```python
config=AlakazamConfig(
    dry_run=False,  # ← Change this to False
    verbose=True
)
```

Run again:

```bash
python basic_usage.py
```

Now files will actually be renamed!

## Understanding the Output

### Target Directory

Where your PDF files are located. This is specified when creating `LocalStorage`:

```python
storage=LocalStorage(target_dir)
```

### Log File

The rename log is stored at:

```
/path/to/target/directory/.alakazam.log
```

This file tracks all rename operations and prevents duplicate processing.

**View the log:**

```bash
cat ~/Documents/TestDocs/.alakazam.log | jq .
```

### Dry Run vs. Actual Rename

- `dry_run=True`: Preview only, no files changed
- `dry_run=False`: Actually rename files

## Next Steps

1. **Test with Mock Analyzer** (no API needed)
   - Run `basic_usage.py`
   - Verify everything works

2. **Implement Real Analyzer**
   - See `NEXT_STEPS.md` for Phase 1
   - Extract Anthropic or OpenAI analyzer

3. **Customize Naming Strategy**
   - Modify `ISODateNaming` parameters
   - Or create your own custom strategy

## File Locations Summary

| What | Where | Set By |
|------|-------|--------|
| **Target Directory** | Specified by you | `LocalStorage(path)` |
| **Rename Log** | `.alakazam.log` in target dir | `JSONTracker(path)` |
| **PDF Files** | Target directory | You provide them |
| **Renamed Files** | Same directory (in-place rename) | Alakazam |

## Troubleshooting

### "No module named alakazam"

Install the package first:

```bash
cd /path/to/alakazam
uv pip install -e .
```

### "No files found to process"

Make sure you have PDF files in the target directory:

```bash
ls ~/Documents/TestDocs/*.pdf
```

### "File already processed"

The file is already in `.alakazam.log`. To reprocess:

```bash
# Delete the log (careful!)
rm ~/Documents/TestDocs/.alakazam.log
```

### Files are being renamed but shouldn't be

Check that `dry_run=True` in the config.

## Advanced Usage

See the main `USAGE_GUIDE.md` in the project root for more advanced examples and configuration options.
