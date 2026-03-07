# Implementation Plan: Gemini Model Support

This plan outlines the steps to add Google Gemini support to Alakazam.

## Phase 1: Environment and Dependencies [checkpoint: de3d170]
- [x] Task: Add `google-generativeai` to `project.optional-dependencies` in `pyproject.toml` as part of a new `gemini` extra. 83ccc6d
- [x] Task: Update `uv.lock` by running `uv lock`. f81d8f2
- [x] Task: Conductor - User Manual Verification 'Phase 1: Environment and Dependencies' (Protocol in workflow.md) de3d170

## Phase 2: Core Analyzer Implementation
- [x] Task: Create `src/alakazam/analyzers/gemini.py` with the `GeminiAnalyzer` class inheriting from `DocumentAnalyzer`. 8c434d9
- [x] Task: Write Tests: Create `tests/unit/analyzers/test_gemini_analyzer.py` and implement unit tests that mock the `google-generativeai` SDK. ac42337
- [~] Task: Implement Feature: Implement `GeminiAnalyzer.analyze()` to extract PDF content and call the Gemini API, returning the required JSON structure.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Core Analyzer Implementation' (Protocol in workflow.md)

## Phase 3: CLI Integration and Registration
- [ ] Task: Export `GeminiAnalyzer` in `src/alakazam/analyzers/__init__.py`.
- [ ] Task: Update `src/alakazam/cli/main.py` to add `gemini` to the `--analyzer` click options and handle its instantiation in the `rename` command.
- [ ] Task: Write Tests: Add an integration test in `tests/integration/test_cli_rename.py` (or a new file) to verify `alakazam rename --analyzer gemini` works with mocked API responses.
- [ ] Task: Implement Feature: Finalize the CLI integration, ensuring proper error handling for missing API keys or dependencies.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: CLI Integration and Registration' (Protocol in workflow.md)
