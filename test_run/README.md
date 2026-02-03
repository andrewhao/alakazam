# End-to-End Test Directory

This directory contains a complete end-to-end test of the Alakazam document renaming system.

## 📁 What's Here

| File | Purpose |
|------|---------|
| `create_test_pdfs.py` | Creates 4 sample PDF files for testing |
| `run_end_to_end_test.py` | Runs the complete end-to-end test |
| `*.pdf` | Sample PDF documents (created by script) |
| `.alakazam.log` | Rename log (created after actual rename) |

## 🚀 Quick Start

### Step 1: Create Test PDFs

```bash
python create_test_pdfs.py
```

This creates 4 realistic PDF files:
- `test_invoice.pdf` - Sample invoice
- `medical_record.pdf` - Sample medical statement
- `property_tax_statement.pdf` - Sample property tax bill
- `IMG_2341_scan.pdf` - Sample jury summons

### Step 2: Run End-to-End Test (Dry Run)

```bash
python run_end_to_end_test.py
```

**Expected Output:**
```
🎉 ALL TESTS PASSED! Alakazam is working correctly.
```

This will:
- ✅ Find and process all 4 PDF files
- ✅ Analyze them with MockAnalyzer
- ✅ Generate ISO-formatted filenames
- ✅ Preview renames (dry-run mode)
- ✅ Verify all functionality works

### Step 3: Actually Rename Files (Optional)

To actually rename the files, edit `run_end_to_end_test.py` and change:

```python
config = AlakazamConfig(
    dry_run=False,  # ← Change to False
    verbose=True
)
```

Then run again:

```bash
python run_end_to_end_test.py
```

Files will be renamed and a `.alakazam.log` will be created.

## 📊 Test Results

The test verifies:

1. ✅ Files are processed
2. ✅ Log file handling (dry-run vs actual)
3. ✅ All files get new names
4. ✅ No errors occur
5. ✅ Filenames follow ISO date format (YYYY-MM-DD)

## 📝 Sample Output

```
PROCESSING DOCUMENTS
----------------------------------------------------------------------

[1/4] Processing: test_invoice.pdf
  Analyzing: test_invoice.pdf
    Suggested: 2024-01-15 Mock Invoice Test_invoice.pdf
  [DRY RUN] Would rename to: 2024-01-15 Mock Invoice Test_invoice.pdf

[2/4] Processing: medical_record.pdf
  Analyzing: medical_record.pdf
    Suggested: 2024-01-15 Mock Medical Document Medical_record.pdf
  [DRY RUN] Would rename to: 2024-01-15 Mock Medical Document Medical_record.pdf

...
```

## 🔧 What This Tests

### Components Tested

- ✅ **MockAnalyzer**: Document analysis without AI API
- ✅ **ISODateNaming**: Filename generation strategy
- ✅ **LocalStorage**: File operations and listing
- ✅ **JSONTracker**: Rename logging and tracking
- ✅ **TypeRegistry**: Document type system
- ✅ **Alakazam**: Main orchestrator
- ✅ **AlakazamConfig**: Configuration system

### Functionality Tested

- ✅ PDF file discovery
- ✅ Batch processing
- ✅ Filename generation
- ✅ Dry-run mode
- ✅ Verbose output
- ✅ Error handling
- ✅ Result reporting
- ✅ Log file creation

## 📂 Directory Structure

**Before running:**
```
test_run/
├── create_test_pdfs.py
├── run_end_to_end_test.py
└── README.md
```

**After creating PDFs:**
```
test_run/
├── create_test_pdfs.py
├── run_end_to_end_test.py
├── README.md
├── IMG_2341_scan.pdf
├── medical_record.pdf
├── property_tax_statement.pdf
└── test_invoice.pdf
```

**After actual rename:**
```
test_run/
├── create_test_pdfs.py
├── run_end_to_end_test.py
├── README.md
├── .alakazam.log                                        ← NEW
├── 2024-01-15 Mock Document Img_2341_scan.pdf          ← RENAMED
├── 2024-01-15 Mock Invoice Test_invoice.pdf            ← RENAMED
├── 2024-01-15 Mock Medical Document Medical_record.pdf ← RENAMED
└── 2024-01-15 Mock Tax Document Property_tax_statement.pdf ← RENAMED
```

## 🔍 Inspecting Results

### View the rename log:

```bash
cat .alakazam.log | jq .
```

### Check what files exist:

```bash
ls -l *.pdf
```

### Reset for testing again:

```bash
# Delete renamed files and log
rm -f "2024-01-15"*.pdf .alakazam.log

# Recreate test PDFs
python create_test_pdfs.py
```

## 🎯 Understanding the Test Flow

```
┌─────────────────────────────────────────┐
│  1. Create Test PDFs                    │
│     create_test_pdfs.py                 │
└────────────────┬────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────┐
│  2. Run End-to-End Test                 │
│     run_end_to_end_test.py              │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │ a. Scan for PDFs                   │ │
│  │ b. Analyze with MockAnalyzer       │ │
│  │ c. Generate new filenames          │ │
│  │ d. Validate format                 │ │
│  │ e. Preview/Rename                  │ │
│  │ f. Log operations                  │ │
│  └────────────────────────────────────┘ │
└────────────────┬────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────┐
│  3. Verify Results                      │
│     - All files processed?              │
│     - Filenames correct format?         │
│     - No errors?                        │
│     - Log created?                      │
└─────────────────────────────────────────┘
```

## 💡 Tips

1. **Always run in dry-run first** to preview renames
2. **Check the log** to see what was processed
3. **Reset between tests** by deleting renamed files
4. **Use with real AI** by replacing MockAnalyzer with AnthropicAnalyzer

## 🆘 Troubleshooting

### No PDFs found?

```bash
python create_test_pdfs.py
```

### Test fails?

Check the error output in the TEST RESULTS section.

### Want to start fresh?

```bash
# Remove everything except scripts
rm -f *.pdf .alakazam.log *.txt

# Recreate test PDFs
python create_test_pdfs.py
```

## 📖 Next Steps

After verifying the test works:

1. ✅ Implement a real AI analyzer (see `NEXT_STEPS.md`)
2. ✅ Test with your own PDF documents
3. ✅ Customize the naming strategy
4. ✅ Deploy to your documents folder

---

**This test proves Alakazam's core functionality works end-to-end!** 🎊
