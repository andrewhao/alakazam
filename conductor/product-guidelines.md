# Product Guidelines: Alakazam

## Product Vision & UX Principles
Alakazam's user experience should be **Informative & Visual**, leveraging its Rich-powered UI to provide clear, engaging progress and status updates. It prioritizes clarity, transparency, and user confidence.

## Tone & Voice
- **Voice**: Professional, intelligent, yet approachable.
- **Tone**: Helpful and transparent.

## Experience Guidelines
- **Informative & Visual**: Use progress bars, tables, and color-coded status messages to make batch operations clear and easy to follow.
- **Show AI Reasoning**: Be transparent about **WHY** a document was named a certain way. This builds trust in the AI's classification and naming logic.
- **Safety-First Overwrites**: Never overwrite an existing file without explicit user confirmation or configuration.

## Error Handling & Resilience
- **Model-Level Error Logging**: Errors from underlying AI models (e.g., Anthropic, OpenAI) must be clearly captured and logged to assist with troubleshooting and parameter tuning.
- **Graceful Failure**: Design batch operations to log individual file errors and continue with the rest of the set whenever possible.

## Technical Standards (UX)
- **ISO 8601 Standard**: Enforce `YYYY-MM-DD` as the primary date format for all renaming operations to ensure consistent sorting and searchability.
- **Path Validation**: Always validate destination paths and filename characters to prevent file system errors.
