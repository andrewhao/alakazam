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
@click.option(
    "--analyzer",
    type=click.Choice(["claude_code", "codex"], case_sensitive=False),
    default="claude_code",
    show_default=True,
    help="Analyzer to use",
)
def rename(path, batch_size, dry_run, verbose, continuous, analyzer):
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

    config = AlakazamConfig(batch_size=batch_size, dry_run=dry_run, verbose=verbose)
    alakazam = Alakazam(
        analyzer=analyzer_instance,
        naming_strategy=ISODateNaming(max_length=80, title_case=True),
        storage=LocalStorage(target_path),
        tracker=JSONTracker(log_file),
        type_registry=type_registry,
        config=config,
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
