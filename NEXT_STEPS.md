# Next Steps for Alakazam

## ✅ Completed

- [x] Create project structure
- [x] Set up pyproject.toml with dependencies
- [x] Define core abstractions (DocumentAnalyzer, NamingStrategy, etc.)
- [x] Implement ISODateNaming strategy
- [x] Create TypeRegistry with adaptive suggestions
- [x] Build main Alakazam orchestrator
- [x] Add basic CLI with Click + Rich
- [x] Write comprehensive README
- [x] Add LICENSE (MIT)
- [x] Initialize git repository
- [x] **Code review and critical bug fixes** (2024-02-02)
  - [x] Fixed class name typo (AlakazamConfig)
  - [x] Fixed async I/O in JSONTracker
  - [x] Fixed truncation length calculation
  - [x] Added edge case validation
  - [x] Created comprehensive test suite (16 tests)

## 🔄 In Progress

### Phase 1: Extract Existing Code (Next!)

1. **Extract Anthropic Analyzer**
   ```bash
   # Copy from: ~/Library/CloudStorage/Dropbox/ScanSnap/auto_rename_documents.py
   # To: src/alakazam/analyzers/anthropic.py
   ```
   - [ ] Copy `analyze_document()` logic
   - [ ] Copy PDF extraction logic
   - [ ] Adapt to DocumentAnalyzer interface
   - [ ] Add error handling
   - [ ] Test with real PDFs

2. **Extract Claude Code Analyzer**
   ```bash
   # Copy from: ~/Library/CloudStorage/Dropbox/ScanSnap/auto_rename_documents_claude_code.py
   # To: src/alakazam/analyzers/claude_code.py
   ```
   - [ ] Copy Claude Code CLI integration
   - [ ] Adapt to DocumentAnalyzer interface
   - [ ] Test with real PDFs

3. **Create Example Script**
   - [ ] `examples/basic_usage.py` - Working example with Anthropic
   - [ ] `examples/claude_code_usage.py` - Free tier example

### Phase 2: Testing

1. **Unit Tests**
   - [x] Test ISODateNaming with various inputs (10 tests added)
   - [x] Test JSONTracker async operations (3 tests added)
   - [x] Test config class (3 tests added)
   - [ ] Test TypeRegistry suggestion tracking
   - [ ] Test LocalStorage operations
   - [ ] Mock analyzer tests

2. **Integration Tests**
   - [ ] Test full pipeline with mock analyzer
   - [ ] Test error handling
   - [ ] Test dry-run mode

3. **End-to-End Tests** (optional)
   - [ ] Test with real API (requires API key in CI)

### Phase 3: CLI Enhancement

1. **Complete CLI Commands**
   - [ ] `alakazam rename` - Full implementation
   - [ ] `alakazam types review` - Show suggestions
   - [ ] `alakazam types add <type>` - Promote type
   - [ ] `alakazam config init` - Create config file
   - [ ] `alakazam config show` - Show current config

2. **Progress Display**
   - [ ] Add progress bar for batch processing
   - [ ] Pretty-print results with Rich tables
   - [ ] Color-coded status messages

### Phase 4: Documentation

1. **API Documentation**
   - [ ] Add docstring examples to all public methods
   - [ ] Create API reference in `docs/`
   - [ ] Add type hints everywhere

2. **User Guides**
   - [ ] Quickstart guide
   - [ ] Configuration guide
   - [ ] Extending guide (custom analyzers)
   - [ ] Troubleshooting guide

3. **Examples**
   - [ ] Basic usage example
   - [ ] Custom analyzer example
   - [ ] Custom naming strategy example
   - [ ] Batch processing example

### Phase 5: Polish & Release

1. **Package Polish**
   - [ ] Add py.typed for type checking
   - [ ] Validate package structure
   - [ ] Test installation from local build
   - [ ] Create wheel and sdist

2. **CI/CD**
   - [ ] GitHub Actions for tests
   - [ ] GitHub Actions for linting (ruff, mypy)
   - [ ] GitHub Actions for publishing to PyPI

3. **Release**
   - [ ] Tag v0.1.0
   - [ ] Publish to PyPI
   - [ ] Create GitHub release with notes

### Phase 6: Community

1. **Launch**
   - [ ] Post to r/Python
   - [ ] Post to Hacker News
   - [ ] Tweet announcement
   - [ ] Submit to Python Weekly

2. **Support**
   - [ ] Set up GitHub Issues templates
   - [ ] Create CONTRIBUTING.md
   - [ ] Set up GitHub Discussions
   - [ ] Respond to feedback

## 📋 Immediate TODO (This Week)

1. Extract Anthropic analyzer from existing code
2. Create basic example that works end-to-end
3. Add unit tests for naming strategy
4. Complete `alakazam rename` CLI command

## 🎯 Goals

**Week 1**: Working prototype with Anthropic analyzer
**Week 2**: Tests + Claude Code analyzer
**Week 3**: Documentation + examples
**Week 4**: Polish + CI/CD
**Week 5**: Release v0.1.0
**Week 6**: Community building

## 🔗 Resources

### Existing Code to Extract From
- `~/Library/CloudStorage/Dropbox/ScanSnap/auto_rename_documents.py`
- `~/Library/CloudStorage/Dropbox/ScanSnap/auto_rename_documents_claude_code.py`

### Reference Documentation
- [Anthropic API Docs](https://docs.anthropic.com/)
- [Click Documentation](https://click.palletsprojects.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [PyPI Publishing Guide](https://packaging.python.org/)

## 💡 Ideas for Future

- OpenAI analyzer
- Local model analyzer (Ollama)
- Image document support (JPG, PNG)
- S3 storage backend
- Dropbox storage backend
- Web UI
- API server for team use
- Plugin system for community analyzers
- Configuration profiles
- Bulk operations dashboard

---

Last updated: 2026-02-02
