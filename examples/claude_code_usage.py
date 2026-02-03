#!/usr/bin/env python3
"""
Example: Using ClaudeCodeAnalyzer to analyze documents.

This example shows how to use the ClaudeCodeAnalyzer - an analyzer that
uses the Claude Code CLI instead of the Anthropic API.

Requirements:
- Claude Pro subscription
- Claude Code CLI installed (https://claude.com/cli)
- No API key needed!

Installation:
    pip install alakazam

Usage:
    python examples/claude_code_usage.py
"""

import asyncio
from pathlib import Path

from alakazam.analyzers import ClaudeCodeAnalyzer


async def example_basic_usage():
    """Basic example: Analyze a single PDF."""
    print("=" * 70)
    print("EXAMPLE 1: Basic Usage")
    print("=" * 70)

    # Create analyzer
    analyzer = ClaudeCodeAnalyzer(verbose=True)

    # Validate configuration
    if not analyzer.validate_config():
        print("\n❌ Claude CLI not found!")
        print("   Install from: https://claude.com/cli")
        return

    # Analyze a PDF
    pdf_path = Path("test_run/2024-01-15 Mock Invoice Test_invoice.pdf")

    if pdf_path.exists():
        result = await analyzer.analyze(pdf_path)

        if result:
            print(f"\n✓ Analysis complete!")
            print(f"  Suggested name: {result['new_filename']}")
            print(f"  Document type:  {result['document_type']}")
            print(f"  Document date:  {result['document_date']}")
        else:
            print("\n❌ Analysis failed")
    else:
        print(f"\n⚠ PDF not found: {pdf_path}")


async def example_custom_config():
    """Example: Custom analyzer configuration."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Custom Configuration")
    print("=" * 70)

    # Create analyzer with custom settings
    analyzer = ClaudeCodeAnalyzer(
        claude_cmd="claude",  # CLI command name
        max_pages=5,  # Extract first 5 pages
        timeout=180,  # 3 minute timeout
        verbose=True,  # Enable debug output
    )

    print(f"\nAnalyzer configuration:")
    print(f"  Command:     {analyzer.claude_cmd}")
    print(f"  Max pages:   {analyzer.max_pages}")
    print(f"  Timeout:     {analyzer.timeout}s")
    print(f"  Verbose:     {analyzer.verbose}")


async def example_batch_processing():
    """Example: Process multiple PDFs."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Batch Processing")
    print("=" * 70)

    analyzer = ClaudeCodeAnalyzer(verbose=False)  # Quiet mode for batch

    # Find all PDFs in test_run
    test_dir = Path("test_run")
    if not test_dir.exists():
        print(f"\n⚠ Directory not found: {test_dir}")
        return

    pdf_files = sorted(test_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"\n⚠ No PDFs found in {test_dir}")
        return

    print(f"\nProcessing {len(pdf_files)} PDFs...\n")

    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] {pdf_path.name}")

        result = await analyzer.analyze(pdf_path)

        if result:
            print(f"  ✓ {result['new_filename']}")
        else:
            print(f"  ✗ Failed")


async def example_with_type_registry():
    """Example: Using analyzer with custom type registry."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: With Type Registry")
    print("=" * 70)

    # Mock type registry (in real usage, use TypeRegistry from alakazam.types)
    class SimpleTypeRegistry:
        def get_all_types(self):
            return [
                "invoice",
                "receipt",
                "medical_statement",
                "insurance_claim",
                "tax_document",
                "bank_statement",
                "contract",
            ]

    registry = SimpleTypeRegistry()

    # Create analyzer with registry
    analyzer = ClaudeCodeAnalyzer(
        type_registry=registry,
        verbose=False,
    )

    print(f"\nType registry loaded with {len(registry.get_all_types())} types:")
    for doc_type in registry.get_all_types():
        print(f"  • {doc_type}")

    print("\nThese types will be suggested to Claude during analysis.")


async def example_error_handling():
    """Example: Handling errors gracefully."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Error Handling")
    print("=" * 70)

    analyzer = ClaudeCodeAnalyzer(verbose=True)

    # Test 1: Non-existent file
    print("\n1. Non-existent file:")
    result = await analyzer.analyze(Path("/tmp/does_not_exist.pdf"))
    print(f"   Result: {result}")

    # Test 2: Invalid CLI command
    print("\n2. Invalid CLI command:")
    bad_analyzer = ClaudeCodeAnalyzer(claude_cmd="invalid_command")
    is_valid = bad_analyzer.validate_config()
    print(f"   Valid: {is_valid}")

    # Test 3: Timeout handling
    print("\n3. Short timeout (will likely timeout):")
    timeout_analyzer = ClaudeCodeAnalyzer(timeout=1, verbose=False)

    pdf_path = Path("test_run/2024-01-15 Mock Invoice Test_invoice.pdf")
    if pdf_path.exists():
        result = await timeout_analyzer.analyze(pdf_path)
        print(f"   Result: {result}")
    else:
        print(f"   Skipped (no test PDF)")


async def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("CLAUDE CODE ANALYZER - USAGE EXAMPLES")
    print("=" * 70)

    # Run examples
    await example_basic_usage()
    await example_custom_config()
    await example_batch_processing()
    await example_with_type_registry()
    await example_error_handling()

    print("\n" + "=" * 70)
    print("EXAMPLES COMPLETE")
    print("=" * 70)
    print("\nFor more information:")
    print("  • Documentation: https://github.com/andrewhao/alakazam")
    print("  • Claude CLI: https://claude.com/cli")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
