"""Main CLI entry point."""

import asyncio
from pathlib import Path

import click
from rich.console import Console

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
def rename(path, batch_size, dry_run, verbose, continuous):
    """Rename documents in PATH using AI analysis."""
    console.print("\n[bold cyan]✨ Alakazam - AI Document Renamer[/bold cyan]\n")

    console.print(
        "[yellow]⚠️  Note: This is v0.1.0 - AI analyzer not yet implemented[/yellow]"
    )
    console.print("[yellow]    Will be added in next release![/yellow]\n")

    console.print(f"Path: {path}")
    console.print(f"Batch size: {batch_size}")
    console.print(f"Dry run: {dry_run}")
    console.print(f"Verbose: {verbose}")
    console.print(f"Continuous: {continuous}\n")

    console.print(
        "[green]✓[/green] CLI working! Next: Extract Anthropic analyzer from existing code"
    )


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
