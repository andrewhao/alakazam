#!/usr/bin/env python3
"""
End-to-end tests for ClaudeCodeAnalyzer.

Tests the analyzer with real PDFs and (optionally) real Claude CLI.
"""

import asyncio
import shutil
import sys
from pathlib import Path

from alakazam.analyzers import ClaudeCodeAnalyzer


async def test_analyzer_validation():
    """Test that analyzer validates configuration."""
    print("\n" + "=" * 70)
    print("TEST 1: Validate Configuration")
    print("=" * 70)

    analyzer = ClaudeCodeAnalyzer(verbose=True)

    # Check if Claude CLI is available
    is_valid = analyzer.validate_config()
    print(f"\n✓ Configuration validation: {is_valid}")

    if is_valid:
        print("  ✓ Claude CLI is available")
    else:
        print("  ✗ Claude CLI not found (install with Claude Pro subscription)")
        print("  → Skipping CLI-dependent tests")

    return is_valid


async def test_analyzer_basic(pdf_path: Path):
    """Test basic analyzer functionality."""
    print("\n" + "=" * 70)
    print(f"TEST 2: Analyze Single PDF - {pdf_path.name}")
    print("=" * 70)

    analyzer = ClaudeCodeAnalyzer(verbose=True)

    print(f"\nAnalyzing: {pdf_path}")
    result = await analyzer.analyze(pdf_path)

    if result:
        print("\n✓ Analysis succeeded!")
        print(f"  Document Date: {result.get('document_date')}")
        print(f"  Document Type: {result.get('document_type')}")
        print(f"  New Filename:  {result.get('new_filename')}")
        print(f"  Description:   {result.get('description')}")
        if result.get('metadata'):
            print(f"  Metadata:      {result['metadata']}")
        return True
    else:
        print("\n✗ Analysis failed")
        return False


async def test_analyzer_all_pdfs():
    """Test analyzer with all available PDFs."""
    print("\n" + "=" * 70)
    print("TEST 3: Analyze All Test PDFs")
    print("=" * 70)

    test_dir = Path(__file__).parent
    pdf_files = sorted(test_dir.glob("*.pdf"))

    if not pdf_files:
        print("\n✗ No PDF files found in test_run/")
        return False

    print(f"\nFound {len(pdf_files)} PDF files")

    analyzer = ClaudeCodeAnalyzer(verbose=True, max_pages=3, timeout=120)

    results = []
    for pdf_path in pdf_files:
        print(f"\n--- Analyzing: {pdf_path.name} ---")
        result = await analyzer.analyze(pdf_path)
        results.append((pdf_path.name, result))

        if result:
            print(f"  ✓ Success: {result['new_filename']}")
        else:
            print(f"  ✗ Failed")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    successful = sum(1 for _, r in results if r is not None)
    print(f"\nTotal PDFs:     {len(results)}")
    print(f"Successful:     {successful}")
    print(f"Failed:         {len(results) - successful}")
    print(f"Success rate:   {successful / len(results) * 100:.1f}%")

    print("\nResults:")
    for filename, result in results:
        if result:
            print(f"  ✓ {filename}")
            print(f"    → {result['new_filename']}")
        else:
            print(f"  ✗ {filename} (failed)")

    return successful == len(results)


async def test_pdf_extraction():
    """Test PDF page extraction."""
    print("\n" + "=" * 70)
    print("TEST 4: PDF Page Extraction")
    print("=" * 70)

    test_dir = Path(__file__).parent
    pdf_files = list(test_dir.glob("*.pdf"))

    if not pdf_files:
        print("\n✗ No PDF files found")
        return False

    pdf_path = pdf_files[0]
    print(f"\nTesting with: {pdf_path.name}")

    analyzer = ClaudeCodeAnalyzer(verbose=True, max_pages=2)

    # Extract pages
    temp_pdf = await analyzer._extract_first_pages(pdf_path)

    if temp_pdf.exists():
        original_size = pdf_path.stat().st_size
        temp_size = temp_pdf.stat().st_size
        print(f"\n✓ Extraction succeeded")
        print(f"  Original size: {original_size:,} bytes")
        print(f"  Extracted size: {temp_size:,} bytes")

        # Clean up
        if temp_pdf != pdf_path:
            temp_pdf.unlink()
            print(f"  ✓ Cleaned up temp file")

        return True
    else:
        print("\n✗ Extraction failed")
        return False


async def test_timeout_handling():
    """Test timeout configuration."""
    print("\n" + "=" * 70)
    print("TEST 5: Timeout Configuration")
    print("=" * 70)

    # Test different timeout values
    timeouts = [60, 120, 180]

    for timeout in timeouts:
        analyzer = ClaudeCodeAnalyzer(timeout=timeout, verbose=False)
        print(f"\n✓ Created analyzer with {timeout}s timeout")
        assert analyzer.timeout == timeout

    print("\n✓ All timeout configurations valid")
    return True


async def main():
    """Run all end-to-end tests."""
    print("\n" + "=" * 70)
    print("CLAUDE CODE ANALYZER - END-TO-END TESTS")
    print("=" * 70)

    # Test 1: Validate configuration
    cli_available = await test_analyzer_validation()

    # Test 4: PDF extraction (doesn't need CLI)
    test4_passed = await test_pdf_extraction()

    # Test 5: Timeout handling (doesn't need CLI)
    test5_passed = await test_timeout_handling()

    # Tests that require CLI
    if cli_available:
        test_dir = Path(__file__).parent
        pdf_files = list(test_dir.glob("*.pdf"))

        if pdf_files:
            # Test 2: Single PDF analysis
            test2_passed = await test_analyzer_basic(pdf_files[0])

            # Test 3: All PDFs
            test3_passed = await test_analyzer_all_pdfs()
        else:
            print("\n✗ No PDF files found for CLI tests")
            test2_passed = False
            test3_passed = False
    else:
        print("\n⚠ Skipping CLI-dependent tests (Claude CLI not available)")
        test2_passed = None
        test3_passed = None

    # Final summary
    print("\n" + "=" * 70)
    print("FINAL TEST RESULTS")
    print("=" * 70)
    print(f"\nTest 1 (Configuration):     {'✓ PASS' if cli_available else '✗ SKIP (no CLI)'}")
    print(f"Test 2 (Single PDF):        {'✓ PASS' if test2_passed else '✗ SKIP (no CLI)' if test2_passed is None else '✗ FAIL'}")
    print(f"Test 3 (All PDFs):          {'✓ PASS' if test3_passed else '✗ SKIP (no CLI)' if test3_passed is None else '✗ FAIL'}")
    print(f"Test 4 (PDF Extraction):    {'✓ PASS' if test4_passed else '✗ FAIL'}")
    print(f"Test 5 (Timeout Config):    {'✓ PASS' if test5_passed else '✗ FAIL'}")

    # Overall status
    all_tests = [test2_passed, test3_passed, test4_passed, test5_passed]
    required_tests = [test4_passed, test5_passed]  # Tests that don't need CLI

    if cli_available:
        overall_pass = all(t for t in all_tests if t is not None)
    else:
        overall_pass = all(required_tests)

    print("\n" + "=" * 70)
    if overall_pass:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 70)

    return 0 if overall_pass else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
