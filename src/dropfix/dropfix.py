#!/usr/bin/env python3
import argparse
import os
import platform
import shlex
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.prompt import Confirm
from rich.table import Table

from dropfix._formatter import RichHelpFormatter, show_version
from dropfix._logger import logger, set_verbosity

console = Console()


def main():
    class DropfixHelpFormatter(RichHelpFormatter):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, title="Dropfix Help", **kwargs)

    parser = argparse.ArgumentParser(
        description="Dropfix: Ignore development directories in Dropbox",
        formatter_class=DropfixHelpFormatter,
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="store_true", help="Show help")
    parser.add_argument("--version", action="store_true", help="Show version")

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Default command (ignore) - no subcommand needed
    parser.add_argument("--path", help="Dropbox path (auto-detects if not specified)")
    parser.add_argument(
        "--dirs",
        nargs="+",
        default=[".venv", ".conda", "node_modules"],
        help="Directories to process (default: .venv .conda node_modules)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increase verbosity (use -v, -vv for more)"
    )

    # Check subcommand
    check_parser = subparsers.add_parser(
        "check",
        help="Verify directories ignored by Dropbox",
        formatter_class=DropfixHelpFormatter,
        add_help=False,
    )
    check_parser.add_argument("-h", "--help", action="store_true", help="Show help")
    check_parser.add_argument("--path", help="Dropbox path (auto-detects if not specified)")
    check_parser.add_argument(
        "--dirs",
        nargs="+",
        default=[".venv", ".conda", "node_modules"],
        help="Directories to check (default: .venv .conda node_modules)",
    )
    check_parser.add_argument(
        "--show",
        choices=["all", "ignored", "not-ignored"],
        default="all",
        help="Filter results (default: all)",
    )
    check_parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increase verbosity (use -v, -vv for more)"
    )

    args = parser.parse_args()

    # Set logging verbosity
    set_verbosity(args.verbose)

    # Handle help and version
    if args.help:
        parser.print_help()
        return 0
    if args.version:
        show_version()

    # Route to check command if specified
    if args.command == "check":
        from dropfix._checker import check_directories

        logger.info("Starting dropfix check")
        dropbox_path = args.path or find_dropbox_path()
        if not dropbox_path:
            logger.error("Could not find Dropbox directory")
            console.print(Panel(
                "[red]Error: Could not find Dropbox directory.[/red]\n"
                "[dim]Please specify your Dropbox path with --path[/dim]",
                title="[bold red]Error[/bold red]",
                border_style="red"
            ))
            return 1

        # Show configuration
        table = Table(show_header=True, header_style="white", box=None)
        table.add_column("Setting", style="dim")
        table.add_column("Value", style="white")
        table.add_row("Dropbox Path", str(dropbox_path))
        table.add_row("Directories", ", ".join(args.dirs))
        table.add_row("Filter", args.show)
        console.print(Panel(table, title="[bold cyan]Check Configuration[/bold cyan]", border_style="cyan"))

        # Check directories
        check_directories(dropbox_path, args.dirs, args.show)
        return 0

    # Default: ignore directories
    logger.info("Starting dropfix")
    dropbox_path = args.path or find_dropbox_path()
    if not dropbox_path:
        logger.error("Could not find Dropbox directory")
        console.print(Panel(
            "[red]Error: Could not find Dropbox directory.[/red]\n"
            "[dim]Please specify your Dropbox path with --path[/dim]",
            title="[bold red]Error[/bold red]",
            border_style="red"
        ))
        return 1

    # Show configuration
    if args.dry_run:
        console.print(Panel(
            "[white]DRY RUN MODE - No changes will be made[/white]",
            border_style="cyan"
        ))

    table = Table(show_header=True, header_style="white", box=None)
    table.add_column("Setting", style="dim")
    table.add_column("Value", style="white")
    table.add_row("Dropbox Path", str(dropbox_path))
    table.add_row("Mode", "Dry Run" if args.dry_run else "Active")
    table.add_row("Directories", ", ".join(args.dirs))
    console.print(Panel(table, title="[bold cyan]Configuration[/bold cyan]", border_style="cyan"))

    if not args.dry_run and not args.yes:
        if not Confirm.ask("\nProceed?"):
            return 0

    # Find and ignore directories
    process_directories(dropbox_path, args.dirs, dry_run=args.dry_run)
    return 0


def find_dropbox_path():
    """Auto-detect Dropbox path based on common locations"""
    home = Path.home()
    common_paths = [home / "Dropbox", home / "Documents" / "Dropbox"]

    # Windows-specific paths
    if platform.system() == "Windows":
        common_paths.extend([
            Path(os.environ.get("USERPROFILE", "")) / "Dropbox",
            Path(os.environ.get("HOMEDRIVE", "") + os.environ.get("HOMEPATH", "")) / "Dropbox",
        ])

    logger.debug(f"Searching for Dropbox in: {common_paths}")
    for path in common_paths:
        if path.exists() and path.is_dir():
            logger.info(f"Found Dropbox at: {path}")
            return path

    logger.warning("Dropbox path not found in common locations")
    return None


def process_directories(dropbox_path, dir_names, dry_run=False):
    """Find and process directories to ignore"""
    system = platform.system()
    ignored_count = 0
    error_count = 0

    logger.info(f"Processing directories: {dir_names}")
    logger.debug(f"System: {system}, Dry run: {dry_run}")

    # Find all matching directories
    for dir_name in dir_names:
        console.print(f"\n[cyan]Searching for '{dir_name}' directories...[/cyan]")
        logger.debug(f"Searching for '{dir_name}' in {dropbox_path}")
        matches = []

        try:
            # Use os.walk to avoid recursive glob limitations in some Python versions
            for root, dirs, _ in os.walk(dropbox_path):
                for d in dirs:
                    if d == dir_name:
                        matches.append(Path(root) / d)
        except (PermissionError, OSError) as e:
            logger.error(f"Error accessing directory during search: {e}")
            console.print(f"[red]Error accessing directory: {e}[/red]")
            continue

        if not matches:
            console.print(f"[dim]No '{dir_name}' directories found[/dim]")
            continue

        console.print(f"[green]Found {len(matches)} '{dir_name}' directories[/green]")
        logger.info(f"Found {len(matches)} '{dir_name}' directories")

        # Process each directory
        with Progress(
            TextColumn("[cyan]{task.description}[/cyan]"),
            BarColumn(complete_style="green", finished_style="green"),
            TextColumn("[white]{task.completed}/{task.total}[/white]"),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"Processing {dir_name}", total=len(matches))
            for dir_path in matches:
                try:
                    logger.debug(f"Processing: {dir_path}")
                    if dry_run:
                        ignored_count += 1
                    elif ignore_directory(dir_path, system):
                        logger.debug(f"Successfully ignored: {dir_path}")
                        ignored_count += 1
                    else:
                        logger.warning(f"Failed to ignore: {dir_path}")
                        error_count += 1
                except (PermissionError, OSError, subprocess.CalledProcessError) as e:
                    logger.error(f"Error processing {dir_path}: {e}")
                    console.print(f"[red]Error {'simulating' if dry_run else 'ignoring'} {dir_path}: {e}[/red]")
                    error_count += 1
                progress.advance(task)

    # Summary
    summary_table = Table(show_header=True, header_style="white", box=None)
    summary_table.add_column("Metric", style="dim")
    summary_table.add_column("Count", style="white")
    summary_table.add_row(
        "Directories " + ("that would be processed" if dry_run else "processed"),
        str(ignored_count)
    )
    if error_count > 0:
        summary_table.add_row("Errors encountered", f"[red]{error_count}[/red]")

    title = "[bold cyan]Summary[/bold cyan]" if not dry_run else "[bold cyan]Dry Run Summary[/bold cyan]"
    console.print(Panel(summary_table, title=title, border_style="cyan"))

    if not dry_run:
        console.print("\n[dim]Note: You may need to restart Dropbox for changes to take effect.[/dim]")


def ignore_directory(path, system):
    """Set the appropriate attribute based on OS"""
    try:
        if system == "Windows":
            # Windows: NTFS alternate data streams
            # Use list arguments to avoid shell injection
            subprocess.run(
                [
                    "powershell",
                    "-Command",
                    f"Set-Content -Path {shlex.quote(str(path))} -Stream com.dropbox.ignored -Value 1"
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        elif system == "Darwin":  # macOS
            # macOS: extended attributes
            subprocess.run(
                ["xattr", "-w", "com.dropbox.ignored", "1", str(path)],
                check=True,
                capture_output=True,
                text=True,
            )
        else:  # Linux and others
            # Linux: attributes
            subprocess.run(
                ["attr", "-s", "com.dropbox.ignored", "-V", "1", str(path)],
                check=True,
                capture_output=True,
                text=True,
            )
        return True
    except subprocess.CalledProcessError:
        return False


if __name__ == "__main__":
    sys.exit(main())
