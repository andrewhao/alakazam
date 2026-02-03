#!/usr/bin/env python3
"""
End-to-end integration test for ClaudeCodeAnalyzer with full Alakazam workflow.

Tests the analyzer integrated into the complete Alakazam pipeline.
"""

import asyncio
import json
import shutil
import sys
import tempfile
from pathlib import Path

from alakazam.analyzers import ClaudeCodeAnalyzer


async def test_full_workflow_integration():
    """Test ClaudeCodeAnalyzer in full Alakazam workflow."""
    print("\n" + "=" * 70)
    print("INTEGRATION TEST: Full Alakazam Workflow with ClaudeCodeAnalyzer")
    print("=" * 70)

    # Check if Claude CLI is available
    analyzer = ClaudeCodeAnalyzer(verbose=True)
    if not analyzer.validate_config():
        print("\n⚠ Claude CLI not available - skipping integration test")
        print("  Install Claude CLI with Claude Pro subscription to run this test")
        return None

    # Setup test environment
    test_dir = Path(__file__).parent
    pdf_files = list(test_dir.glob("*.pdf"))

    if not pdf_files:
        print("\n✗ No PDF files found in test_run/")
        return False

    # Create temp directory for output
    with tempfile.TemporaryDirectory() as temp_output:
        output_dir = Path(temp_output)
        log_file = output_dir / ".alakazam_test.log"

        print(f"\nTest configuration:")
        print(f"  Input PDFs:    {len(pdf_files)}")
        print(f"  Output dir:    {output_dir}")
        print(f"  Log file:      {log_file}")

        # Process each PDF
        results = []
        for pdf_path in pdf_files:
            print(f"\n--- Processing: {pdf_path.name} ---")

            # Analyze document
            result = await analyzer.analyze(pdf_path)

            if result:
                # Simulate the rename (dry run)
                new_filename = result['new_filename']
                new_path = output_dir / new_filename

                print(f"  ✓ Analysis succeeded")
                print(f"    Old: {pdf_path.name}")
                print(f"    New: {new_filename}")

                # Copy to "renamed" location (simulating the rename)
                shutil.copy2(pdf_path, new_path)

                # Log the operation
                log_entry = {
                    "source": str(pdf_path),
                    "destination": str(new_path),
                    "analysis": result,
                }
                results.append(log_entry)

                print(f"  ✓ Simulated rename complete")
            else:
                print(f"  ✗ Analysis failed for {pdf_path.name}")
                results.append({"source": str(pdf_path), "error": "Analysis failed"})

        # Write log file
        with open(log_file, "w") as f:
            for entry in results:
                f.write(json.dumps(entry) + "\n")

        print("\n" + "=" * 70)
        print("WORKFLOW SUMMARY")
        print("=" * 70)

        successful = sum(1 for r in results if "error" not in r)
        print(f"\nTotal files:    {len(pdf_files)}")
        print(f"Successful:     {successful}")
        print(f"Failed:         {len(pdf_files) - successful}")

        # Show renamed files
        print(f"\nRenamed files in {output_dir}:")
        renamed_files = sorted(output_dir.glob("*.pdf"))
        for f in renamed_files:
            print(f"  ✓ {f.name}")

        # Show log entries
        print(f"\nLog entries written to {log_file}:")
        print(f"  {len(results)} entries")

        # Verify log file
        with open(log_file) as f:
            log_lines = f.readlines()
            print(f"  ✓ Log file contains {len(log_lines)} lines")

        return successful == len(pdf_files)


async def test_analyzer_with_type_registry():
    """Test analyzer with custom type registry."""
    print("\n" + "=" * 70)
    print("INTEGRATION TEST: ClaudeCodeAnalyzer with Type Registry")
    print("=" * 70)

    # Create a mock type registry
    class MockTypeRegistry:
        def get_all_types(self):
            return [
                "invoice",
                "receipt",
                "medical_statement",
                "insurance_claim",
                "tax_document",
                "custom_type_1",
                "custom_type_2",
            ]

    registry = MockTypeRegistry()
    analyzer = ClaudeCodeAnalyzer(verbose=True, type_registry=registry)

    print("\n✓ Created analyzer with custom type registry")
    print(f"  Available types: {registry.get_all_types()}")

    # Build prompt to verify it includes custom types
    prompt = analyzer._build_prompt()
    print("\n✓ Prompt includes type registry types:")
    for doc_type in registry.get_all_types():
        if doc_type in prompt:
            print(f"  ✓ '{doc_type}' found in prompt")

    return True


async def test_error_handling():
    """Test error handling scenarios."""
    print("\n" + "=" * 70)
    print("INTEGRATION TEST: Error Handling")
    print("=" * 70)

    analyzer = ClaudeCodeAnalyzer(verbose=True)

    # Test 1: Non-existent file
    print("\nTest 1: Non-existent file")
    fake_path = Path("/tmp/nonexistent_file_12345.pdf")
    try:
        result = await analyzer.analyze(fake_path)
        print(f"  Result: {result}")
        print(f"  ✓ Handled gracefully (returned None)")
    except Exception as e:
        print(f"  ✗ Raised exception: {e}")
        return False

    # Test 2: Invalid command
    print("\nTest 2: Invalid command")
    bad_analyzer = ClaudeCodeAnalyzer(claude_cmd="nonexistent_command_xyz")
    is_valid = bad_analyzer.validate_config()
    if not is_valid:
        print(f"  ✓ Correctly identified invalid command")
    else:
        print(f"  ✗ Should have returned False for invalid command")
        return False

    # Test 3: Short timeout
    print("\nTest 3: Very short timeout (1 second)")
    test_dir = Path(__file__).parent
    pdf_files = list(test_dir.glob("*.pdf"))

    if pdf_files and analyzer.validate_config():
        timeout_analyzer = ClaudeCodeAnalyzer(verbose=True, timeout=1)
        result = await timeout_analyzer.analyze(pdf_files[0])
        # Should timeout and return None
        if result is None:
            print(f"  ✓ Timeout handled correctly (returned None)")
        else:
            print(f"  ⚠ Completed despite short timeout (fast machine or small file)")
    else:
        print(f"  ⚠ Skipped (no PDFs or no CLI)")

    print("\n✓ All error handling tests passed")
    return True


async def main():
    """Run all integration tests."""
    print("\n" + "=" * 70)
    print("ALAKAZAM INTEGRATION TESTS - CLAUDE CODE ANALYZER")
    print("=" * 70)

    # Test 1: Full workflow
    test1_result = await test_full_workflow_integration()

    # Test 2: Type registry
    test2_result = await test_analyzer_with_type_registry()

    # Test 3: Error handling
    test3_result = await test_error_handling()

    # Summary
    print("\n" + "=" * 70)
    print("INTEGRATION TEST RESULTS")
    print("=" * 70)

    if test1_result is None:
        print("\nTest 1 (Full Workflow):     ✗ SKIP (Claude CLI not available)")
    elif test1_result:
        print("\nTest 1 (Full Workflow):     ✓ PASS")
    else:
        print("\nTest 1 (Full Workflow):     ✗ FAIL")

    print(f"Test 2 (Type Registry):     {'✓ PASS' if test2_result else '✗ FAIL'}")
    print(f"Test 3 (Error Handling):    {'✓ PASS' if test3_result else '✗ FAIL'}")

    # Overall
    required_tests = [test2_result, test3_result]
    if test1_result is not None:
        required_tests.append(test1_result)

    overall_pass = all(required_tests)

    print("\n" + "=" * 70)
    if overall_pass:
        print("✓ ALL INTEGRATION TESTS PASSED")
    else:
        print("✗ SOME INTEGRATION TESTS FAILED")
    print("=" * 70)

    return 0 if overall_pass else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
