"""Basic usage example for Alakazam."""

import asyncio
from pathlib import Path
from alakazam import Alakazam
from alakazam.core import AlakazamConfig, JSONTracker
from alakazam.naming import ISODateNaming
from alakazam.storage import LocalStorage
from alakazam.types import TypeRegistry
from mock_analyzer import MockAnalyzer


async def main():
    """Run basic Alakazam example."""

    # ========================================
    # CONFIGURATION
    # ========================================

    # Target directory - where your PDFs are located
    target_dir = Path("~/Documents/TestDocs").expanduser()

    # Create target directory if it doesn't exist (for demo)
    target_dir.mkdir(parents=True, exist_ok=True)

    # Log file location - tracking rename operations
    log_file = target_dir / ".alakazam.log"

    print("=" * 60)
    print("Alakazam - AI-Powered Document Renaming")
    print("=" * 60)
    print(f"\nTarget Directory: {target_dir}")
    print(f"Log File: {log_file}")
    print()

    # ========================================
    # CREATE ALAKAZAM INSTANCE
    # ========================================

    alakazam = Alakazam(
        analyzer=MockAnalyzer(),  # Replace with real analyzer when available
        naming_strategy=ISODateNaming(max_length=80, title_case=True),
        storage=LocalStorage(target_dir),
        tracker=JSONTracker(log_file),
        type_registry=TypeRegistry(),
        config=AlakazamConfig(
            batch_size=5,
            dry_run=True,  # ← IMPORTANT: Set to False to actually rename
            verbose=True,
            safe_mode=False
        )
    )

    # ========================================
    # PROCESS DOCUMENTS
    # ========================================

    print("Processing documents...")
    print("-" * 60)

    result = await alakazam.process_batch()

    # ========================================
    # SHOW RESULTS
    # ========================================

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total Files: {len(result.files)}")
    print(f"Success: {result.success_count}")
    print(f"Errors: {result.error_count}")
    print(f"Dry Run: {result.dry_run_count}")
    print(f"Skipped: {result.skipped_count}")
    print(f"Duration: {result.duration:.2f}s")
    print()

    if result.files:
        print("File Details:")
        print("-" * 60)
        for file_result in result.files:
            if file_result.new_name:
                status = "✓" if file_result.is_success() else "→"
                print(f"{status} {file_result.old_name}")
                print(f"  → {file_result.new_name}")
            elif file_result.error:
                print(f"✗ {file_result.old_name}")
                print(f"  Error: {file_result.error}")
            print()
    else:
        print("No files found to process.")
        print()
        print("To test this example:")
        print(f"1. Add some PDF files to: {target_dir}")
        print(f"2. Run this script again")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
