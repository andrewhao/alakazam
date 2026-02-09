# Interactive Overrides With Learning Feedback (Design)

Date: 2026-02-09

## Summary
Add an interactive mode to the rename flow that lets users accept, edit, skip, or choose from model-provided alternative filenames. Record these decisions in the tracker and feed recent overrides back into analyzer prompts to improve future suggestions.

## Goals
- Provide an interactive per-file override prompt with minimal friction.
- Allow choosing from 2–3 model-suggested alternatives.
- Persist override decisions (including dry-run) for learning feedback.
- Keep analyzer contracts backward compatible.

## Non-Goals
- No rules engine or deterministic naming templates yet.
- No GUI or batch review UI.
- No heavy prompt memory; keep feedback short.

## User Experience
New CLI flag: `--interactive`.

Per-file flow (interactive):
- Display primary suggestion and 2–3 alternatives if present.
- Options:
  - `1..N` choose a suggested name
  - `e` edit (freeform filename)
  - `s` skip
- Validate the chosen name with naming strategy and collision checks.
- On invalid input or collision, show error and re-prompt.

Dry run behavior:
- Still prompt and record decisions, but no rename occurs.

## Data Flow (High Level)
1. Analyzer produces analysis with `new_filename` and optional `alternative_filenames`.
2. Naming strategy generates primary filename (for consistency and validation).
3. Interactive prompt (if enabled) selects final name or skip.
4. Storage rename (unless dry run or skipped).
5. Tracker logs decision and feedback data.
6. Recent overrides are injected into analyzer prompt for future runs.

## Analyzer Output Contract (Additive)
Existing fields remain unchanged. Add optional:

```
"alternative_filenames": [
  "YYYY-MM-DD Descriptive Name.pdf",
  "YYYY-MM-DD Other Variant.pdf"
]
```

If missing or invalid, treat as no alternatives.

## Prompt Changes
Update analyzer prompts to request 2–3 alternatives:
- `new_filename` is primary.
- `alternative_filenames` must be valid, < 80 chars, meaningfully different.
- Keep JSON-only output.

## Core/CLI Changes
- `AlakazamConfig`: add `interactive: bool = False`.
- CLI: add `--interactive` flag; pass to config.
- `Alakazam._process_file`: invoke interactive decision layer after suggestion.
- Add a small prompt helper in CLI or core (depends on where Rich usage is desired).

## Tracking & Feedback
Extend tracker entry schema to include:
- `suggested_name`
- `alternative_names`
- `chosen_name`
- `decision` (accept/alternate/edit/skip)
- `dry_run` (bool)

Expose tracker helper:
- `get_override_examples(limit=5)`

Analyzer receives a short, formatted list of recent overrides to append to prompt.

## Validation & Error Handling
- Always validate filename via `NamingStrategy.validate`.
- Reject invalid characters/format or length > 255.
- Collision check before rename.
- On skip, do not rename and record decision.

## Testing
Unit tests:
- Prompt construction includes alternatives and feedback examples.
- Parser handles missing/invalid alternatives.
- Interactive selection validation (invalid input, collision, skip).
- Tracker logs full decision schema.

Integration tests:
- `--interactive --dry-run` with mocked analyzer to verify prompt, logging, and no rename.

## Open Questions
- None for initial implementation.
