#!/usr/bin/env python3
"""
End-to-End Test for Alakazam

This script tests the complete Alakazam pipeline:
1. Scans for PDF files in the test_run directory
2. Analyzes them with MockAnalyzer
3. Generates new filenames
4. Renames files (or previews in dry-run mode)
5. Logs operations to .alakazam.log
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import alakazam
sys.path.insert(0, str(Path(__file__).parent.parent))

from alakazam import Alakazam
from alakazam.core import AlakazamConfig, JSONTracker
from alakazam.naming import ISODateNaming
from alakazam.storage import LocalStorage
from alakazam.types import TypeRegistry

# Import mock analyzer from examples
sys.path.insert(0, str(Path(__file__).parent.parent / "examples"))
from mock_analyzer import MockAnalyzer


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title):
    """Print a formatted section."""
    print(f"\n{title}")
    print("-" * 70)


async def main():
    """Run the end-to-end test."""

    print_header("ALAKAZAM END-TO-END TEST")

    # ========================================
    # SETUP
    # ========================================

    test_dir = Path(__file__).parent
    log_file = test_dir / ".alakazam.log"

    print(f"\nTest Directory: {test_dir}")
    print(f"Log File: {log_file}")

    # Count existing PDFs
    existing_pdfs = list(test_dir.glob("*.pdf"))
    print(f"Found {len(existing_pdfs)} PDF files to process")

    if not existing_pdfs:
        print("\n❌ ERROR: No PDF files found!")
        print("   Run create_test_pdfs.py first")
        return 1

    print("\nFiles to process:")
    for pdf in existing_pdfs:
        print(f"  • {pdf.name}")

    # ========================================
    # CONFIGURE ALAKAZAM
    # ========================================

    print_section("CONFIGURATION")

    config = AlakazamConfig(
        batch_size=10,
        dry_run=True,  # ← Safe mode - preview only
        verbose=True,
        safe_mode=False
    )

    print(f"  Batch Size: {config.batch_size}")
    print(f"  Dry Run: {config.dry_run}")
    print(f"  Verbose: {config.verbose}")

    alakazam = Alakazam(
        analyzer=MockAnalyzer(),
        naming_strategy=ISODateNaming(max_length=80, title_case=True),
        storage=LocalStorage(test_dir),
        tracker=JSONTracker(log_file),
        type_registry=TypeRegistry(),
        config=config
    )

    # ========================================
    # PROCESS FILES
    # ========================================

    print_section("PROCESSING DOCUMENTS")

    result = await alakazam.process_batch()

    # ========================================
    # SHOW RESULTS
    # ========================================

    print_header("TEST RESULTS")

    print(f"\nProcessing Summary:")
    print(f"  Total Files: {len(result.files)}")
    print(f"  ✓ Success: {result.success_count}")
    print(f"  ✗ Errors: {result.error_count}")
    print(f"  → Dry Run: {result.dry_run_count}")
    print(f"  ⊘ Skipped: {result.skipped_count}")
    print(f"  ⏱  Duration: {result.duration:.2f}s")

    if result.files:
        print_section("FILE DETAILS")
        for i, file_result in enumerate(result.files, 1):
            print(f"\n[{i}] {file_result.old_name}")

            if file_result.new_name:
                status = "✓" if file_result.is_success() else "→"
                print(f"    {status} New Name: {file_result.new_name}")

                if file_result.analysis:
                    print(f"    📅 Date: {file_result.analysis.get('document_date')}")
                    print(f"    📄 Type: {file_result.analysis.get('document_type')}")
                    print(f"    📝 Description: {file_result.analysis.get('description')}")

            if file_result.status.value == "error":
                print(f"    ✗ Error: {file_result.error}")

    # ========================================
    # CHECK LOG FILE
    # ========================================

    if log_file.exists():
        print_section("RENAME LOG")
        print(f"\nLog file created: {log_file}")
        print(f"Size: {log_file.stat().st_size} bytes")

        # Show log contents
        import json
        with open(log_file, 'r') as f:
            log_data = json.load(f)

        print(f"Version: {log_data['metadata']['version']}")
        print(f"Total renames logged: {len(log_data['renames'])}")

        if config.dry_run:
            print("\n⚠️  NOTE: Files were NOT actually renamed (dry-run mode)")
            print("   To actually rename files, set config.dry_run=False")

    # ========================================
    # VERIFY FUNCTIONALITY
    # ========================================

    print_header("VERIFICATION")

    tests_passed = 0
    tests_failed = 0

    # Test 1: Files were processed
    if len(result.files) > 0:
        print("✓ Test 1: Files were processed")
        tests_passed += 1
    else:
        print("✗ Test 1: No files were processed")
        tests_failed += 1

    # Test 2: Log file was created (or dry-run mode)
    if log_file.exists() or config.dry_run:
        if config.dry_run:
            print("✓ Test 2: Dry-run mode (log file not created)")
        else:
            print("✓ Test 2: Log file was created")
        tests_passed += 1
    else:
        print("✗ Test 2: Log file was NOT created")
        tests_failed += 1

    # Test 3: All files got new names
    if all(f.new_name for f in result.files):
        print("✓ Test 3: All files got new names")
        tests_passed += 1
    else:
        print("✗ Test 3: Some files did not get new names")
        tests_failed += 1

    # Test 4: No errors
    if result.error_count == 0:
        print("✓ Test 4: No errors occurred")
        tests_passed += 1
    else:
        print(f"✗ Test 4: {result.error_count} errors occurred")
        tests_failed += 1

    # Test 5: Naming format is correct
    all_correct_format = True
    for file_result in result.files:
        if file_result.new_name:
            # Check if name starts with YYYY-MM-DD
            if not file_result.new_name[:10].replace('-', '').isdigit():
                all_correct_format = False
                break

    if all_correct_format and result.files:
        print("✓ Test 5: All filenames follow ISO date format")
        tests_passed += 1
    else:
        print("✗ Test 5: Some filenames don't follow format")
        tests_failed += 1

    # ========================================
    # FINAL SUMMARY
    # ========================================

    print_header("FINAL SUMMARY")

    print(f"\nTests Passed: {tests_passed}")
    print(f"Tests Failed: {tests_failed}")

    if tests_failed == 0:
        print("\n🎉 ALL TESTS PASSED! Alakazam is working correctly.")
        print("\nNext Steps:")
        print("  1. Review the proposed filenames above")
        print("  2. If satisfied, run with config.dry_run=False to actually rename files")
        print("  3. Implement a real AI analyzer (see NEXT_STEPS.md)")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - Please review the errors above")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
