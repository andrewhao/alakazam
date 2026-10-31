"""Main CLI entry point."""

import asyncio
from pathlib import Path

import click
from rich.console import Console

from alakazam import Alakazam
from alakazam.analyzers import (
    AntigravityAnalyzer,
    ClaudeCodeAnalyzer,
    CodexAnalyzer,
)
from alakazam.core import AlakazamConfig, JSONTracker
from alakazam.naming import ISODateNaming
from alakazam.storage import LocalStorage
from alakazam.types import TypeRegistry

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """✨ Alakazam - AI-powered intelligent document renaming."""
    pass


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--batch-size", "-n", default=5, help="Number of files to process")
@click.option("--dry-run", is_flag=True, help="Preview without renaming")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--continuous", is_flag=True, help="Process all files")
@click.option("--interactive", is_flag=True, help="Prompt to confirm or edit names")
@click.option(
    "--analyzer",
    type=click.Choice(
        ["claude_code", "codex", "antigravity", "agy", "gemini"],
        case_sensitive=False,
    ),
    default="claude_code",
    show_default=True,
    help="Analyzer to use",
)
@click.option(
    "--auto-download",
    is_flag=True,
    help="Automatically download cloud-stored files (e.g. Google Drive, iCloud, Dropbox) before processing",
)
def rename(path, batch_size, dry_run, verbose, continuous, interactive, analyzer, auto_download):
    """Rename documents in PATH using AI analysis."""
    console.print("\n[bold cyan]✨ Alakazam - AI Document Renamer[/bold cyan]\n")

    target_path = Path(path).expanduser().absolute()
    log_file = target_path / ".alakazam.log"

    console.print(f"Path: {target_path}")
    console.print(f"Log file: {log_file}")
    console.print(f"Batch size: {batch_size}")
    console.print(f"Dry run: {dry_run}")
    console.print(f"Verbose: {verbose}")
    console.print(f"Continuous: {continuous}")
    console.print(f"Auto download: {auto_download}\n")

    type_registry = TypeRegistry()
    if analyzer == "codex":
        analyzer_instance = CodexAnalyzer(verbose=verbose, type_registry=type_registry)
    elif analyzer in ("antigravity", "agy", "gemini"):
        if analyzer == "gemini":
            console.print(
                "[yellow]Note: 'gemini' is deprecated; using 'antigravity' (agy CLI) analyzer.[/yellow]"
            )
        analyzer_instance = AntigravityAnalyzer(verbose=verbose, type_registry=type_registry)
    else:
        analyzer_instance = ClaudeCodeAnalyzer(verbose=verbose, type_registry=type_registry)

    if not analyzer_instance.validate_config():
        console.print(f"[red]✗ {analyzer_instance.__class__.__name__} CLI not found.[/red]")
        console.print("Install the CLI and log in to use this analyzer.")
        raise SystemExit(1)

    storage = LocalStorage(target_path, auto_download=auto_download)
    if auto_download and log_file.exists():
        is_dataless = bool(getattr(log_file.stat(), "st_flags", 0) & 0x40000000)
        if is_dataless:
            asyncio.run(storage.materialize(log_file))

    tracker = JSONTracker(log_file)

    config = AlakazamConfig(
        batch_size=batch_size,
        dry_run=dry_run,
        verbose=verbose,
        interactive=interactive,
        auto_download=auto_download,
    )
    naming_strategy = ISODateNaming(max_length=80, title_case=True)
    decision_provider = None
    if interactive:
        decision_provider = _build_decision_provider(
            naming_strategy=naming_strategy,
            storage=storage,
            dry_run=dry_run,
        )

    overrides = tracker.get_override_examples(limit=5)
    if overrides and hasattr(analyzer_instance, "set_naming_preferences"):
        preferences_text = _format_override_preferences(overrides)
        analyzer_instance.set_naming_preferences(preferences_text)

    alakazam = Alakazam(
        analyzer=analyzer_instance,
        naming_strategy=naming_strategy,
        storage=storage,
        tracker=tracker,
        type_registry=type_registry,
        config=config,
        decision_provider=decision_provider,
    )

    if continuous:
        results = asyncio.run(alakazam.process_continuous())
        success = sum(r.success_count for r in results)
        errors = sum(r.error_count for r in results)
        dry_runs = sum(r.dry_run_count for r in results)
        total = sum(len(r.files) for r in results)
    else:
        result = asyncio.run(alakazam.process_batch())
        success = result.success_count
        errors = result.error_count
        dry_runs = result.dry_run_count
        total = len(result.files)

    console.print("\nResults:")
    console.print(f"Total: {total}")
    console.print(f"Success: {success}")
    console.print(f"Errors: {errors}")
    console.print(f"Dry run: {dry_runs}")


def _build_decision_provider(naming_strategy, storage, dry_run: bool):
    """
    Build an interactive decision provider callback for rename operations.

    Creates a callback that prompts the user to choose from suggested names,
    edit filenames, or skip files. Validates choices and checks for collisions.

    Args:
        naming_strategy: Strategy to validate filename formats
        storage: Storage backend to check for existing files
        dry_run: If True, indicates collision checks are simulated

    Returns:
        Async callback function that takes (file_path, analysis, suggested_name,
        alternative_names) and returns a decision dict with action and chosen_name.
    """

    async def decision_provider(file_path, analysis, suggested_name, alternative_names):
        options = [suggested_name] + [name for name in alternative_names if name != suggested_name]

        max_attempts = 10
        attempt = 0

        while attempt < max_attempts:
            attempt += 1

            click.echo(f"\nFile: {file_path.name}")
            click.echo("Choose a filename:")
            for idx, name in enumerate(options, 1):
                click.echo(f"  {idx}. {name}")
            click.echo("  e. Edit")
            click.echo("  s. Skip")

            choice = click.prompt("Select option", default="1", show_default=False)
            choice = str(choice).strip().lower()

            if choice == "s":
                return {
                    "action": "skip",
                    "chosen_name": None,
                    "suggested_name": suggested_name,
                    "alternative_names": options[1:],
                }

            if choice == "e":
                edited = click.prompt("Enter filename", default=suggested_name, show_default=False)
                edited = str(edited).strip()
                if not naming_strategy.validate(edited):
                    click.echo("Invalid filename format. Please try again.")
                    continue
                if await storage.exists(file_path.parent / edited):
                    suffix = " (simulated)" if dry_run else ""
                    click.echo(f"Filename already exists{suffix}. Please choose another.")
                    continue
                return {
                    "action": "edit",
                    "chosen_name": edited,
                    "suggested_name": suggested_name,
                    "alternative_names": options[1:],
                }

            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(options):
                    selected = options[index]
                    if not naming_strategy.validate(selected):
                        click.echo("Invalid filename format. Please try again.")
                        continue
                    if await storage.exists(file_path.parent / selected):
                        suffix = " (simulated)" if dry_run else ""
                        click.echo(f"Filename already exists{suffix}. Please choose another.")
                        continue
                    action = "accept" if index == 0 else "alternate"
                    return {
                        "action": action,
                        "chosen_name": selected,
                        "suggested_name": suggested_name,
                        "alternative_names": options[1:],
                    }

            click.echo("Invalid selection. Please try again.")

        # Max attempts exceeded - auto-skip
        click.echo(f"Maximum attempts ({max_attempts}) exceeded. Skipping file.")
        return {
            "action": "skip",
            "chosen_name": None,
            "suggested_name": suggested_name,
            "alternative_names": options[1:],
        }

    return decision_provider


def _format_override_preferences(overrides):
    """
    Format user override examples into a text summary for AI feedback.

    Args:
        overrides: List of override dicts with suggested_name, chosen_name,
                   document_type, and metadata fields

    Returns:
        Formatted string showing suggested -> chosen name patterns with metadata
    """
    lines = []
    for entry in overrides:
        suggested = entry.get("suggested_name")
        chosen = entry.get("chosen_name")
        metadata = entry.get("metadata") or {}
        metadata_bits = ", ".join(f"{key}: {value}" for key, value in metadata.items() if value)
        meta_suffix = f" ({metadata_bits})" if metadata_bits else ""
        lines.append(f"- Suggested: {suggested} -> Chosen: {chosen}{meta_suffix}")
    return "\n".join(lines)


@cli.group()
def types():
    """Manage document types."""
    pass


@types.command("list")
def types_list():
    """List all document types."""
    from alakazam.types import BUILTIN_TYPES

    console.print("\n[bold]Built-in Document Types:[/bold]\n")
    for doc_type in sorted(BUILTIN_TYPES):
        console.print(f"  • {doc_type}")


@types.command("review")
def types_review():
    """Review suggested document types."""
    console.print("\n[yellow]Feature coming soon![/yellow]\n")


@cli.command("eval")
@click.option(
    "--log-file",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Evaluate recent rename entries from a .alakazam.log file",
)
@click.option(
    "--live-dir",
    type=click.Path(exists=True, file_okay=False),
    default=None,
    help="Run live analyzer on PDFs in a directory and evaluate the generated filenames",
)
@click.option(
    "--limit",
    "-n",
    default=10,
    show_default=True,
    help="Maximum number of log entries or live PDFs to evaluate",
)
@click.option(
    "--analyzer",
    type=click.Choice(
        ["claude_code", "codex", "antigravity", "agy", "gemini"],
        case_sensitive=False,
    ),
    default="antigravity",
    show_default=True,
    help="Analyzer to use for --live-dir or --llm-judge",
)
@click.option(
    "--llm-judge",
    is_flag=True,
    help="Also grade each filename (1-5 scale) using an LLM-as-a-Judge",
)
@click.option(
    "--use-recorded",
    is_flag=True,
    help="When using --log-file, evaluate the historically recorded new_name instead of regenerating via ISODateNaming",
)
def run_eval(log_file, live_dir, limit, analyzer, llm_judge, use_recorded):
    """Evaluate generated filenames for source/author prominence and naming quality."""
    from rich.table import Table
    from alakazam.evals import (
        EvalSuiteResult,
        FilenameEvaluator,
        GOLDEN_DATASET,
        LLMJudgeEvaluator,
        load_eval_cases_from_log,
    )

    console.print("\n[bold cyan]✨ Alakazam - Filename Quality Evals[/bold cyan]\n")

    evaluator = FilenameEvaluator(max_length=80)
    judge_cmd = "agy" if analyzer in ("antigravity", "agy", "gemini") else (
        "codex" if analyzer == "codex" else "claude"
    )
    judge = LLMJudgeEvaluator(cli_cmd=judge_cmd) if llm_judge else None

    async def _execute_evals():
        cases_to_run = []

        if live_dir:
            target_dir = Path(live_dir).expanduser().absolute()
            pdfs = sorted(target_dir.glob("*.pdf"))[:limit]
            type_registry = TypeRegistry()
            if analyzer == "codex":
                analyzer_inst = CodexAnalyzer(verbose=False, type_registry=type_registry)
            elif analyzer in ("antigravity", "agy", "gemini"):
                analyzer_inst = AntigravityAnalyzer(verbose=False, type_registry=type_registry)
            else:
                analyzer_inst = ClaudeCodeAnalyzer(verbose=False, type_registry=type_registry)

            for idx, pdf_path in enumerate(pdfs, 1):
                console.print(f"  Analyzing [{idx}/{len(pdfs)}]: {pdf_path.name}...")
                analysis = await analyzer_inst.analyze(pdf_path)
                if not analysis:
                    continue
                cases_to_run.append(
                    {
                        "id": pdf_path.stem[:28],
                        "original_filename": pdf_path.name,
                        "expected_sources": [],
                        "analysis": analysis,
                        "generated_filename": None,
                    }
                )
        elif log_file:
            loaded = load_eval_cases_from_log(Path(log_file), limit=limit)
            for item in loaded:
                cases_to_run.append(
                    {
                        "id": item["id"],
                        "original_filename": item["original_filename"],
                        "expected_sources": item["expected_sources"],
                        "analysis": item["analysis"],
                        "generated_filename": item["recorded_filename"] if use_recorded else None,
                    }
                )
        else:
            for item in GOLDEN_DATASET:
                cases_to_run.append(
                    {
                        "id": item["id"],
                        "original_filename": item["original_filename"],
                        "expected_sources": item["expected_sources"],
                        "analysis": item["analysis"],
                        "generated_filename": None,
                    }
                )

        results = []
        for item in cases_to_run:
            case_res = evaluator.evaluate_case(
                case_id=item["id"],
                analysis=item["analysis"],
                original_filename=item["original_filename"],
                generated_filename=item["generated_filename"],
                expected_sources=item["expected_sources"],
            )
            if judge:
                judge_res = await judge.score_filename(
                    item["analysis"], case_res.generated_filename
                )
                case_res.judge_score = judge_res.get("score")
                case_res.judge_reasoning = judge_res.get("reasoning")
            results.append(case_res)

        return EvalSuiteResult(cases=results)

    suite = asyncio.run(_execute_evals())

    table = Table(title="Filename Evaluation Results", show_lines=True)
    table.add_column("Case", style="cyan", no_wrap=True)
    table.add_column("Generated Filename", style="white")
    table.add_column("Source", justify="center")
    table.add_column("Prominent", justify="center")
    table.add_column("Clean End", justify="center")
    table.add_column("Score", justify="right")
    if llm_judge:
        table.add_column("LLM Judge", justify="right")

    for case in suite.cases:
        check_map = {c.name: c for c in case.checks}
        src_ok = "✓" if check_map["source_present"].passed else "[red]✗[/red]"
        prom_ok = "✓" if check_map["source_prominent"].passed else "[red]✗[/red]"
        trunc_ok = (
            "✓"
            if (check_map["no_dangling_truncation"].passed and check_map["concise_title"].passed)
            else "[red]✗[/red]"
        )
        score_str = (
            f"[green]{case.score * 100:.0f}%[/green]"
            if case.passed
            else f"[red]{case.score * 100:.0f}%[/red]"
        )
        row = [
            case.case_id,
            case.generated_filename,
            src_ok,
            prom_ok,
            trunc_ok,
            score_str,
        ]
        if llm_judge:
            j_str = f"{case.judge_score:.1f}/5" if case.judge_score is not None else "N/A"
            row.append(j_str)
        table.add_row(*row)

    console.print(table)
    console.print(
        f"\n[bold]Summary:[/bold] {suite.passed_count}/{suite.total} passed "
        f"({suite.pass_rate * 100:.1f}%) | Avg Rubric Score: {suite.average_score * 100:.1f}%"
    )
    if suite.average_judge_score is not None:
        console.print(f"[bold]Avg LLM Judge Score:[/bold] {suite.average_judge_score:.2f} / 5.00")

    if suite.failed_count > 0:
        console.print("\n[yellow]Failed Checks Detail:[/yellow]")
        for case in suite.cases:
            if not case.passed:
                failed_reasons = [f"{c.name}: {c.reason}" for c in case.checks if not c.passed]
                console.print(f"  • [bold]{case.case_id}[/bold] ({case.generated_filename}):")
                for r in failed_reasons:
                    console.print(f"      - {r}")
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
