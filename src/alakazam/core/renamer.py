"""Main Alakazam orchestrator for document renaming."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from alakazam.analyzers.base import DocumentAnalyzer
from alakazam.core.result import FileResult, ProcessingResult, ResultStatus
from alakazam.core.tracker import FileTracker
from alakazam.naming.base import NamingStrategy
from alakazam.storage.base import StorageBackend
from alakazam.types.registry import TypeRegistry


@dataclass
class AlazazamConfig:
    """Configuration for Alakazam renamer."""

    batch_size: int = 5
    dry_run: bool = False
    safe_mode: bool = False  # Save after each file
    max_batches: int = 1000
    verbose: bool = False


class Alakazam:
    """
    Main orchestrator for intelligent document renaming.

    Coordinates between analyzer, naming strategy, storage, tracker, and type system.
    """

    def __init__(
        self,
        analyzer: DocumentAnalyzer,
        naming_strategy: NamingStrategy,
        storage: StorageBackend,
        tracker: FileTracker,
        type_registry: TypeRegistry,
        config: Optional[AlazazamConfig] = None,
    ):
        """
        Initialize Alakazam renamer.

        Args:
            analyzer: Document analyzer for AI content extraction
            naming_strategy: Strategy for generating filenames
            storage: Storage backend for file operations
            tracker: File tracker for preventing duplicates
            type_registry: Registry for document types
            config: Configuration options
        """
        self.analyzer = analyzer
        self.naming = naming_strategy
        self.storage = storage
        self.tracker = tracker
        self.types = type_registry
        self.config = config or AlazazamConfig()

    async def process_batch(self, batch_size: Optional[int] = None) -> ProcessingResult:
        """
        Process a batch of files.

        Args:
            batch_size: Number of files to process (uses config if None)

        Returns:
            ProcessingResult with details of all operations
        """
        started = datetime.now()
        batch_size = batch_size or self.config.batch_size

        # Find unprocessed files
        all_files = await self.storage.list_files("*.pdf")
        processed = self.tracker.get_processed_files()
        unprocessed = [f for f in all_files if f.name not in processed][:batch_size]

        if not unprocessed:
            return ProcessingResult([], started, datetime.now())

        if self.config.verbose:
            print(f"\nFound {len(unprocessed)} file(s) to process:\n")

        # Process each file
        results = []
        for idx, file_path in enumerate(unprocessed, 1):
            if self.config.verbose:
                print(f"[{idx}/{len(unprocessed)}] Processing: {file_path.name}")

            result = await self._process_file(file_path)
            results.append(result)

            # Save after each file in safe mode
            if self.config.safe_mode and result.is_success():
                # Tracker already saves internally
                pass

        completed = datetime.now()
        return ProcessingResult(results, started, completed)

    async def _process_file(self, file_path: Path) -> FileResult:
        """Process a single file."""
        try:
            # 1. Analyze document
            if self.config.verbose:
                print(f"  Analyzing: {file_path.name}")

            analysis = await self.analyzer.analyze(file_path)
            if not analysis:
                return FileResult.error(file_path.name, "Analysis failed")

            # 2. Check document type
            doc_type = analysis.get('document_type', 'unknown')
            if not self.types.is_standard(doc_type):
                if self.config.verbose:
                    print(f"   💡 New document type suggested: '{doc_type}'")
                self.types.register_suggestion(doc_type, analysis.get('new_filename', ''))

            # 3. Generate new filename
            new_name = self.naming.generate_filename(analysis, file_path.name)

            if not self.naming.validate(new_name):
                return FileResult.error(file_path.name, f"Invalid filename: {new_name}")

            if self.config.verbose:
                print(f"    Suggested: {new_name}")

            # 4. Dry run check
            if self.config.dry_run:
                if self.config.verbose:
                    print(f"  [DRY RUN] Would rename to: {new_name}\n")
                return FileResult.dry_run(file_path.name, new_name)

            # 5. Check for collisions
            new_path = file_path.parent / new_name
            if await self.storage.exists(new_path):
                return FileResult.error(file_path.name, f"File exists: {new_name}")

            # 6. Rename file
            await self.storage.rename(file_path, new_name)

            # 7. Track rename
            await self.tracker.record_rename(file_path.name, new_name, analysis)

            if self.config.verbose:
                print(f"    Renamed to: {new_name}")
                print(f"  ✓ Successfully processed\n")

            return FileResult.success(file_path.name, new_name, analysis)

        except Exception as e:
            if self.config.verbose:
                print(f"    ❌ Error: {e}\n")
            return FileResult.error(file_path.name, str(e))

    async def process_continuous(self) -> List[ProcessingResult]:
        """
        Process files continuously until none remain.

        Returns:
            List of ProcessingResult for each batch
        """
        results = []
        batch_num = 0

        while batch_num < self.config.max_batches:
            result = await self.process_batch()

            if result.success_count == 0 and result.dry_run_count == 0:
                break  # No more files to process

            results.append(result)
            batch_num += 1

            if self.config.verbose:
                print(
                    f"\nBatch {batch_num} complete: {result.success_count} file(s) processed\n"
                )

        return results

    def __repr__(self) -> str:
        return (
            f"Alakazam("
            f"analyzer={self.analyzer}, "
            f"naming={self.naming}, "
            f"storage={self.storage})"
        )
