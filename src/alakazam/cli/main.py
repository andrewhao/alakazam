"""Main CLI entry point."""

import asyncio
from pathlib import Path

import click
from rich.console import Console

from alakazam import Alakazam
from alakazam.analyzers import ClaudeCodeAnalyzer, CodexAnalyzer
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
    type=click.Choice(["claude_code", "codex"], case_sensitive=False),
    default="claude_code",
    show_default=True,
    help="Analyzer to use",
)
def rename(path, batch_size, dry_run, verbose, continuous, interactive, analyzer):
    """Rename documents in PATH using AI analysis."""
    console.print("\n[bold cyan]✨ Alakazam - AI Document Renamer[/bold cyan]\n")

    target_path = Path(path).expanduser().absolute()
    log_file = target_path / ".alakazam.log"

    console.print(f"Path: {target_path}")
    console.print(f"Log file: {log_file}")
    console.print(f"Batch size: {batch_size}")
    console.print(f"Dry run: {dry_run}")
    console.print(f"Verbose: {verbose}")
    console.print(f"Continuous: {continuous}\n")

    type_registry = TypeRegistry()
    if analyzer == "codex":
        analyzer_instance = CodexAnalyzer(verbose=verbose, type_registry=type_registry)
    else:
        analyzer_instance = ClaudeCodeAnalyzer(verbose=verbose, type_registry=type_registry)

    if not analyzer_instance.validate_config():
        console.print(f"[red]✗ {analyzer_instance.__class__.__name__} CLI not found.[/red]")
        console.print("Install the CLI and log in to use this analyzer.")
        raise SystemExit(1)

    storage = LocalStorage(target_path)
    tracker = JSONTracker(log_file)

    config = AlakazamConfig(
        batch_size=batch_size,
        dry_run=dry_run,
        verbose=verbose,
        interactive=interactive,
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
        options = [suggested_name] + [
            name for name in alternative_names if name != suggested_name
        ]

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
                edited = click.prompt(
                    "Enter filename", default=suggested_name, show_default=False
                )
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
        metadata_bits = ", ".join(
            f"{key}: {value}" for key, value in metadata.items() if value
        )
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


if __name__ == "__main__":
    cli()
