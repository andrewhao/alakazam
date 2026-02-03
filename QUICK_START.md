# Quick Start Guide

## 🎯 Your Questions Answered

### Q: Where do I specify the target directory?

**Answer**: You have two options:

#### Option 1: CLI (when fully implemented)
```bash
alakazam rename /path/to/your/documents
                 ↑
                 Target directory here
```

#### Option 2: Python API (works now)
```python
from alakazam.storage import LocalStorage

storage = LocalStorage("/path/to/your/documents")
                       ↑
                       Target directory here
```

### Q: Where is the rename log stored?

**Answer**: In your target directory as `.alakazam.log`

```
/path/to/your/documents/
├── .alakazam.log          ← Rename log HERE (auto-created)
├── document1.pdf
├── document2.pdf
└── document3.pdf
```

You specify the log location when creating the tracker:

```python
from pathlib import Path
from alakazam.core import JSONTracker

target_dir = Path("/path/to/your/documents")
tracker = JSONTracker(target_dir / ".alakazam.log")
                      ↑
                      Log file location
```

---

## 🚀 Try It Now

### Step 1: Run the Example

```bash
cd examples
python basic_usage.py
```

**Output:**
```
============================================================
Alakazam - AI-Powered Document Renaming
============================================================

Target Directory: /Users/you/Documents/TestDocs
Log File: /Users/you/Documents/TestDocs/.alakazam.log

No files found to process.
```

### Step 2: Add Test Files

```bash
# Create test directory
mkdir -p ~/Documents/TestDocs

# Add some PDF files
cp your-pdfs/*.pdf ~/Documents/TestDocs/
```

### Step 3: Run Again

```bash
python basic_usage.py
```

**Output:**
```
Processing documents...
[1/3] Processing: scan_001.pdf
  Analyzing: scan_001.pdf
    Suggested: 2024-01-15 Mock Document scan_001.pdf
  [DRY RUN] Would rename to: 2024-01-15 Mock Document scan_001.pdf

✓ Success!
```

---

## 📁 File Locations at a Glance

| What | Where | How to Specify |
|------|-------|----------------|
| **PDF Files** | Your directory | You provide |
| **Target Directory** | Anywhere you want | `LocalStorage(path)` or CLI arg |
| **Rename Log** | `.alakazam.log` in target dir | `JSONTracker(path)` |
| **Renamed Files** | Same directory (in-place) | Automatic |

### Example Directory Structure

**Before:**
```
~/Documents/Scans/
├── scan_001.pdf
├── IMG_2341.pdf
└── random_file.pdf
```

**After Running Alakazam:**
```
~/Documents/Scans/
├── .alakazam.log                              ← NEW: Rename log
├── 2024-01-15 Invoice Acme Corp.pdf          ← RENAMED
├── 2024-01-20 Medical Statement.pdf          ← RENAMED
└── 2024-01-22 Bank Statement.pdf             ← RENAMED
```

**Log File Contents (`.alakazam.log`):**
```json
{
  "metadata": {"version": "1.0"},
  "renames": [
    {
      "old_name": "scan_001.pdf",
      "new_name": "2024-01-15 Invoice Acme Corp.pdf",
      "document_date": "2024-01-15",
      "document_type": "invoice"
    }
  ]
}
```

---

## 🎨 Complete Example Code

```python
import asyncio
from pathlib import Path
from alakazam import Alakazam
from alakazam.core import AlakazamConfig, JSONTracker
from alakazam.naming import ISODateNaming
from alakazam.storage import LocalStorage
from alakazam.types import TypeRegistry
from your_analyzer import YourAnalyzer  # Implement this

async def main():
    # ============================================
    # SPECIFY DIRECTORY AND LOG LOCATION HERE
    # ============================================
    target_dir = Path("~/Documents/Scans").expanduser()
    log_file = target_dir / ".alakazam.log"

    # Create Alakazam
    alakazam = Alakazam(
        analyzer=YourAnalyzer(),
        naming_strategy=ISODateNaming(),
        storage=LocalStorage(target_dir),      # ← Target directory
        tracker=JSONTracker(log_file),         # ← Log location
        type_registry=TypeRegistry(),
        config=AlakazamConfig(
            batch_size=5,
            dry_run=True,  # Safe mode - preview only
            verbose=True
        )
    )

    # Process files
    result = await alakazam.process_batch()

    # Show results
    print(f"Processed {result.success_count} files")

asyncio.run(main())
```

---

## 💡 Key Points

1. **Target Directory** = Where your PDFs are
   - Set via: `LocalStorage(path)`
   - Or: CLI first argument

2. **Rename Log** = `.alakazam.log` in target directory
   - Set via: `JSONTracker(path)`
   - Tracks all renames
   - Prevents duplicates

3. **Files Renamed In-Place** = Same directory
   - Before: `scan_001.pdf`
   - After: `2024-01-15 Description.pdf`
   - Location: Same folder

4. **Always Use Dry Run First**
   ```python
   config=AlakazamConfig(dry_run=True)  # Preview
   config=AlakazamConfig(dry_run=False) # Actually rename
   ```

---

## 📖 More Information

- **Detailed Guide**: See [USAGE_GUIDE.md](USAGE_GUIDE.md)
- **Working Examples**: See [examples/](examples/)
- **Code Review**: See [CODE_REVIEW_SUMMARY.md](CODE_REVIEW_SUMMARY.md)
- **Next Steps**: See [NEXT_STEPS.md](NEXT_STEPS.md)

---

## 🆘 Quick Troubleshooting

### No files found?
```bash
# Check for PDFs
ls ~/Documents/TestDocs/*.pdf
```

### Where's my log?
```bash
# Find it
ls -la ~/Documents/TestDocs/.alakazam.log

# View it
cat ~/Documents/TestDocs/.alakazam.log | jq .
```

### Files already processed?
```bash
# Delete log to reprocess (careful!)
rm ~/Documents/TestDocs/.alakazam.log
```

---

**Ready to use Alakazam!** 🎉
