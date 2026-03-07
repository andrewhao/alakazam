# Track support_gemini_model_20260306: Gemini Model Support

## Goal
Extend Alakazam to support Google's Gemini models as a document analyzer. This will allow users to use Gemini 1.5 Flash or Pro for intelligent document renaming.

## Context
Alakazam currently supports:
- `ClaudeCodeAnalyzer`: Uses the Claude Code CLI.
- `CodexAnalyzer`: Uses OpenAI's models via API.

Adding `GeminiAnalyzer` expands the available AI providers, giving users more choice and potential cost/performance benefits.

## Requirements
1. **New Analyzer**: Implement `GeminiAnalyzer` in `src/alakazam/analyzers/gemini.py`.
2. **Library Integration**: Use the `google-generativeai` Python library.
3. **Authentication**: Support `GOOGLE_API_KEY` via environment variables.
4. **Functionality**:
   - `analyze(document_path)`: Extract PDF content and return structured JSON (date, type, filename, description, metadata).
   - `validate_config()`: Check if API key and required library are available.
5. **CLI Support**:
   - Add `gemini` to the `--analyzer` choice in `alakazam rename`.
   - Correctly instantiate `GeminiAnalyzer` based on CLI options.
6. **Async Support**: Ensure the analyzer works correctly within the existing async architecture.

## Technical Constraints
- Follow the existing `DocumentAnalyzer` base class.
- Reuse the standard prompt structure used by other analyzers for consistency.
- Handle PDF content extraction (first 3 pages by default, consistent with `ClaudeCodeAnalyzer`).
- Ensure `google-generativeai` is an optional dependency (extra).
