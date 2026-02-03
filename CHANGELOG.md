# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Fixed class name typo: `AlazazamConfig` → `AlakazamConfig` to match project name
- Fixed async/sync I/O mismatch in `JSONTracker._save()` - now properly uses `aiofiles`
- Fixed off-by-one error in `ISODateNaming._truncate()` length calculation (+2 → +1)
- Added edge case validation in `_truncate()` to raise `ValueError` when `max_length` is too small

### Added
- Comprehensive test suite with 16 unit tests (100% pass rate)
  - 3 tests for config class verification
  - 3 tests for async I/O operations
  - 10 tests for naming strategy and truncation logic
- `FIXES_SUMMARY.md` documenting critical error fixes
- `CHANGELOG.md` for tracking changes

### Changed
- Moved `aiofiles` import to module level in `tracker.py` (style improvement)
- Updated README.md with current status and testing instructions

## [0.1.0] - 2024-02-01

### Added
- Initial core architecture and design
- Abstract base classes for pluggable components:
  - `DocumentAnalyzer` for AI content extraction
  - `NamingStrategy` for filename generation
  - `StorageBackend` for file operations
  - `FileTracker` for duplicate prevention
- Concrete implementations:
  - `ISODateNaming` strategy (YYYY-MM-DD format)
  - `LocalStorage` backend
  - `JSONTracker` for operation logging
- Type registry system with adaptive learning
  - 19 built-in document types
  - AI suggestion tracking and promotion system
- Result types for operation tracking
- CLI interface with Click and Rich
  - `alakazam rename` command
  - `alakazam types list/review` commands
- Development roadmap and next steps documentation

### Technical Details
- Python 3.10+ support
- Async/await architecture throughout
- Pydantic for validation
- Type hints for static analysis
- Modular, extensible design

[unreleased]: https://github.com/andrewhao/alakazam/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/andrewhao/alakazam/releases/tag/v0.1.0
