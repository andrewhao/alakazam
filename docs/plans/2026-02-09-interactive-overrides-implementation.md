# Interactive Overrides Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an interactive rename mode with override choices and model-provided alternative names, while logging decisions to improve future suggestions.

**Architecture:** Introduce a decision layer in the core renamer driven by a CLI-provided callback. Extend tracker logging with decision records and expose recent override examples for prompt feedback. Update analyzer prompts to request alternatives and accept feedback snippets.

**Tech Stack:** Python 3.10+, click, rich, pytest/pytest-asyncio.

### Task 1: Add Decision Logging To Tracker

**Files:**
- Modify: `src/alakazam/core/tracker.py`
- Test: `tests/core/test_tracker.py`

**Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_record_decision_and_get_override_examples(tmp_path):
    log_file = tmp_path / "log.json"
    tracker = JSONTracker(log_file)

    await tracker.record_decision(
        old_name="old.pdf",
        suggested_name="2024-01-01 Acme Invoice.pdf",
        alternative_names=["2024-01-01 Acme Statement.pdf"],
        chosen_name="2024-01-01 Acme Statement.pdf",
        decision="alternate",
        analysis={
            "document_date": "2024-01-01",
            "document_type": "invoice",
            "description": "Acme invoice",
            "metadata": {"provider": "Acme"},
        },
        dry_run=True,
    )

    overrides = tracker.get_override_examples(limit=5)
    assert overrides == [
        {
            "suggested_name": "2024-01-01 Acme Invoice.pdf",
            "chosen_name": "2024-01-01 Acme Statement.pdf",
            "document_type": "invoice",
            "metadata": {"provider": "Acme"},
        }
    ]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/core/test_tracker.py::test_record_decision_and_get_override_examples -q`
Expected: FAIL (missing `record_decision` / `get_override_examples`).

**Step 3: Write minimal implementation**

- Add `decisions` list to tracker data (default `[]` if missing).
- Add async `record_decision(...)` to JSONTracker.
- Add `get_override_examples(limit=5)` to JSONTracker:
  - Filter decisions where `chosen_name` != `suggested_name`.
  - Return list of dicts with keys `suggested_name`, `chosen_name`, `document_type`, `metadata`.
- Do **not** change `get_processed_files` behavior.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/core/test_tracker.py::test_record_decision_and_get_override_examples -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/alakazam/core/tracker.py tests/core/test_tracker.py
git commit -m "feat: log rename decisions and overrides"
```

### Task 2: Update Analyzer Prompts For Alternatives + Preferences

**Files:**
- Modify: `src/alakazam/analyzers/base.py`
- Modify: `src/alakazam/analyzers/claude_code.py`
- Modify: `src/alakazam/analyzers/codex.py`
- Test: `tests/unit/analyzers/test_codex_analyzer.py`

**Step 1: Write the failing tests**

```python
@pytest.mark.asyncio
async def test_codex_analyzer_parses_alternative_filenames(tmp_path: Path, monkeypatch):
    from alakazam.analyzers.codex import CodexAnalyzer

    output_path = tmp_path / "codex_output.json"
    output_path.write_text(json.dumps({
        "document_date": "2024-01-15",
        "document_type": "invoice",
        "new_filename": "2024-01-15 Test Invoice.pdf",
        "description": "Test Invoice",
        "alternative_filenames": [
            "2024-01-15 Test Invoice Acme.pdf",
            "2024-01-15 Acme Invoice.pdf",
        ],
    }))

    sample_pdf = tmp_path / "sample.pdf"
    sample_pdf.write_bytes(b"%PDF-1.4\n%mock\n")

    async def fake_exec(*args, **kwargs):
        class Result:
            returncode = 0
            async def communicate(self, *args, **kwargs):
                return b"", b""
        return Result()

    monkeypatch.setattr("alakazam.analyzers.codex.asyncio.create_subprocess_exec", fake_exec)

    analyzer = CodexAnalyzer(_test_output_path=output_path)
    result = await analyzer.analyze(sample_pdf)

    assert result["alternative_filenames"][0].startswith("2024-01-15")
```

```python
def test_codex_prompt_includes_alternatives_and_preferences():
    from alakazam.analyzers.codex import CodexAnalyzer

    analyzer = CodexAnalyzer()
    analyzer.set_naming_preferences("- Suggested -> Chosen example")
    prompt = analyzer._build_prompt()

    assert "alternative_filenames" in prompt
    assert "Recent user overrides" in prompt
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/analyzers/test_codex_analyzer.py::test_codex_analyzer_parses_alternative_filenames -q`
Expected: FAIL (missing prompt instructions or missing setter).

**Step 3: Write minimal implementation**

- Add default `set_naming_preferences(self, preferences: Optional[str]) -> None` to `DocumentAnalyzer` (non-abstract).
- Store `self.naming_preferences` in both analyzers.
- Update `_build_prompt()` in both analyzers to:
  - Request `alternative_filenames` array with 2–3 valid entries.
  - Append a short “Recent user overrides” section if `naming_preferences` is set.

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/analyzers/test_codex_analyzer.py::test_codex_analyzer_parses_alternative_filenames tests/unit/analyzers/test_codex_analyzer.py::test_codex_prompt_includes_alternatives_and_preferences -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/alakazam/analyzers/base.py src/alakazam/analyzers/claude_code.py src/alakazam/analyzers/codex.py tests/unit/analyzers/test_codex_analyzer.py
git commit -m "feat: add alternative name support to analyzer prompts"
```

### Task 3: Core Interactive Decision Flow

**Files:**
- Modify: `src/alakazam/core/renamer.py`
- Modify: `src/alakazam/core/result.py`
- Test: `tests/core/test_renamer.py`

**Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_interactive_decision_skips_file(tmp_path: Path):
    class FakeAnalyzer:
        async def analyze(self, document_path: Path):
            return {
                "document_date": "2024-01-01",
                "document_type": "invoice",
                "description": "Test",
                "alternative_filenames": ["2024-01-01 Test Alt.pdf"],
            }
        def validate_config(self):
            return True

    class Decision:
        action = "skip"
        chosen_name = None
        suggested_name = "2024-01-01 Test.pdf"
        alternative_names = ["2024-01-01 Test Alt.pdf"]

    async def decide(*args, **kwargs):
        return Decision()

    log_file = tmp_path / ".alakazam.log"
    alakazam = Alakazam(
        analyzer=FakeAnalyzer(),
        naming_strategy=ISODateNaming(),
        storage=LocalStorage(tmp_path),
        tracker=JSONTracker(log_file),
        type_registry=TypeRegistry(),
        config=AlakazamConfig(batch_size=1, dry_run=True, verbose=False, interactive=True),
        decision_provider=decide,
    )

    result = await alakazam.process_batch()

    assert result.skipped_count == 1
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/core/test_renamer.py::test_interactive_decision_skips_file -q`
Expected: FAIL (missing `interactive` config and decision provider).

**Step 3: Write minimal implementation**

- Add `interactive: bool = False` to `AlakazamConfig`.
- Add `decision_provider` optional parameter to `Alakazam.__init__`.
- Define a simple decision data structure (small dataclass or expected dict) and normalize in `_process_file`.
- In `_process_file`:
  - Build suggested name as today.
  - Gather valid alternatives from analysis.
  - If interactive, call decision provider with file info and suggestions.
  - If skip, record decision and return `FileResult.skipped`.
  - If edit/alternate/accept, use chosen name.
- Always call `tracker.record_decision(...)` (even dry-run).

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/core/test_renamer.py::test_interactive_decision_skips_file -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/alakazam/core/renamer.py src/alakazam/core/result.py tests/core/test_renamer.py
git commit -m "feat: add interactive decision flow to renamer"
```

### Task 4: CLI Interactive Prompt + Feedback Injection

**Files:**
- Modify: `src/alakazam/cli/main.py`
- Test: `tests/integration/test_cli_rename.py`

**Step 1: Write the failing test**

```python
def test_cli_rename_interactive_dry_run_accepts_default(monkeypatch, tmp_path: Path):
    (tmp_path / "one.pdf").write_text("fake")
    (tmp_path / "two.pdf").write_text("fake")

    class FakeAnalyzer:
        async def analyze(self, document_path: Path):
            return {
                "document_date": "2024-01-15",
                "document_type": "invoice",
                "new_filename": f"2024-01-15 Test {document_path.stem}.pdf",
                "description": f"Test {document_path.stem}",
                "alternative_filenames": ["2024-01-15 Alt Name.pdf"],
                "metadata": {},
            }
        def validate_config(self):
            return True

    monkeypatch.setattr("alakazam.cli.main.ClaudeCodeAnalyzer", FakeAnalyzer)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["rename", str(tmp_path), "--dry-run", "--interactive"],
        input="1\n1\n",
    )

    assert result.exit_code == 0
    assert "Dry run: 2" in result.output
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_cli_rename.py::test_cli_rename_interactive_dry_run_accepts_default -q`
Expected: FAIL (missing `--interactive`).

**Step 3: Write minimal implementation**

- Add `--interactive` option in CLI and pass into `AlakazamConfig`.
- Build an interactive decision provider using `click.echo` + `click.prompt`:
  - Display numbered options for suggested + alternatives.
  - `e` to edit, `s` to skip.
  - Validate with naming strategy and check collisions.
- Inject recent overrides into analyzer:
  - `overrides = tracker.get_override_examples(limit=5)`
  - Format into a short string and call `analyzer.set_naming_preferences(...)`.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/integration/test_cli_rename.py::test_cli_rename_interactive_dry_run_accepts_default -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/alakazam/cli/main.py tests/integration/test_cli_rename.py
git commit -m "feat: add interactive rename prompt"
```

## Notes
- Keep `renames` list in tracker for actual renames; store all choices in new `decisions` list.
- Keep feedback examples short to avoid prompt bloat.

