#!/usr/bin/env python3
import argparse
import os
import platform
import shlex
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.table import Table

from dropfix._formatter import RichHelpFormatter, show_version
from dropfix._logger import logger, set_verbosity

console = Console()


def main():
    class DropfixCheckHelpFormatter(RichHelpFormatter):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, title="Dropfix-Check Help", **kwargs)

    parser = argparse.ArgumentParser(
        description="Dropfix-Check: Verify directories ignored by Dropbox",
        formatter_class=DropfixCheckHelpFormatter,
        add_help=False,
    )
    parser.add_argument("-h", "--help", action="store_true", help="Show help")
    parser.add_argument("--version", action="store_true", help="Show version")
    parser.add_argument("--path", help="Dropbox path (auto-detects if not specified)")
    parser.add_argument(
        "--dirs",
        nargs="+",
        default=[".venv", ".conda", "node_modules"],
        help="Directories to check (default: .venv .conda node_modules)",
    )
    parser.add_argument(
        "--show",
        choices=["all", "ignored", "not-ignored"],
        default="all",
        help="Filter results (default: all)",
    )
    parser.add_argument(
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

    # Auto-detect or use provided Dropbox path
    logger.info("Starting dropfix-check")
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

    for path in common_paths:
        if path.exists() and path.is_dir():
            return path

    return None


def check_directories(dropbox_path, dir_names, show_filter="all"):
    """Find directories and check if they're ignored by Dropbox"""
    system = platform.system()
    ignored_count = 0
    not_ignored_count = 0
    error_count = 0

    logger.info(f"Checking directories: {dir_names}")
    logger.debug(f"System: {system}, Filter: {show_filter}")

    # Track directories by name for grouping
    dir_groups = {name: [] for name in dir_names}

    # Find all matching directories
    for dir_name in dir_names:
        console.print(f"[cyan]Searching for '{dir_name}' directories...[/cyan]")
        logger.debug(f"Searching for '{dir_name}' in {dropbox_path}")
        matches = []

        try:
            # Use os.walk to find all matching directories
            for root, dirs, _ in os.walk(dropbox_path):
                for d in dirs:
                    if d == dir_name:
                        matches.append(Path(root) / d)
        except (PermissionError, OSError) as e:
            console.print(f"[red]Error accessing directory: {e}[/red]")
            continue

        if not matches:
            console.print(f"[dim]No '{dir_name}' directories found.[/dim]")
            continue

        console.print(f"[green]Found {len(matches)} '{dir_name}' directories.[/green]")
        logger.info(f"Found {len(matches)} '{dir_name}' directories")
        dir_groups[dir_name].extend(matches)

    # Combine all directories for processing
    all_matches = []
    for matches in dir_groups.values():
        all_matches.extend(matches)

    if not all_matches:
        console.print("[dim]No matching directories found.[/dim]")
        return

    console.print(f"[cyan]Checking Dropbox ignore status for {len(all_matches)} directories...[/cyan]")

    # Check each directory
    ignored_dirs = []
    not_ignored_dirs = []
    error_dirs = []

    with Progress(
        TextColumn("[cyan]{task.description}[/cyan]"),
        BarColumn(complete_style="green", finished_style="green"),
        TextColumn("[white]{task.completed}/{task.total}[/white]"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Checking directories", total=len(all_matches))
        for dir_path in all_matches:
            try:
                logger.debug(f"Checking: {dir_path}")
                is_ignored = check_if_ignored(dir_path, system)
                if is_ignored is True:
                    logger.debug(f"Ignored: {dir_path}")
                    ignored_dirs.append(dir_path)
                    ignored_count += 1
                elif is_ignored is False:
                    logger.debug(f"Not ignored: {dir_path}")
                    not_ignored_dirs.append(dir_path)
                    not_ignored_count += 1
                else:  # None = error
                    logger.warning(f"Error checking: {dir_path}")
                    error_dirs.append(dir_path)
                    error_count += 1
            except (PermissionError, OSError, subprocess.CalledProcessError) as e:
                logger.error(f"Error checking {dir_path}: {e}")
                console.print(f"[red]Error checking {dir_path}: {e}[/red]")
                error_dirs.append(dir_path)
                error_count += 1
            progress.advance(task)

    # Group ignored directories by name and parent-child relationships
    ignored_by_name = defaultdict(list)
    for d in ignored_dirs:
        ignored_by_name[d.name].append(d)

    # Print results
    console.print()

    # Ignored directories - grouped and filtered
    if show_filter in ["all", "ignored"] and ignored_dirs:
        console.print(Panel(
            f"[green]Directories ignored by Dropbox ({len(ignored_dirs)})[/green]",
            border_style="green"
        ))

        for dir_name, paths in ignored_by_name.items():
            # Get organized hierarchy of directories
            top_level_dirs, nested_counts = organize_directories(paths, dropbox_path)

            # Show only top-level directories with nested counts
            for top_dir in top_level_dirs:
                nested_count = nested_counts.get(top_dir, 0)
                if nested_count > 0:
                    console.print(f"[green]✓ {top_dir}[/green] [cyan](+{nested_count} nested ignored directories)[/cyan]")
                else:
                    console.print(f"[green]✓ {top_dir}[/green]")

    # Not ignored directories
    if show_filter in ["all", "not-ignored"] and not_ignored_dirs:
        console.print(Panel(
            f"[white]Directories NOT ignored by Dropbox ({len(not_ignored_dirs)})[/white]",
            border_style="cyan"
        ))

        # Group not-ignored directories by name
        not_ignored_by_name = defaultdict(list)
        for d in not_ignored_dirs:
            not_ignored_by_name[d.name].append(d)

        for dir_name, paths in not_ignored_by_name.items():
            # Get organized hierarchy
            top_level_dirs, nested_counts = organize_directories(paths, dropbox_path)

            # Show only top-level directories with nested counts
            for top_dir in top_level_dirs:
                nested_count = nested_counts.get(top_dir, 0)
                if nested_count > 0:
                    console.print(f"[white]✗ {top_dir}[/white] [dim](+{nested_count} nested non-ignored directories)[/dim]")
                else:
                    console.print(f"[white]✗ {top_dir}[/white]")

    # Errors
    if error_dirs:
        console.print(Panel(
            f"[red]Directories with check errors ({len(error_dirs)})[/red]",
            border_style="red"
        ))

        # Group error directories by name
        error_by_name = defaultdict(list)
        for d in error_dirs:
            error_by_name[d.name].append(d)

        for dir_name, paths in error_by_name.items():
            # Get organized hierarchy
            top_level_dirs, nested_counts = organize_directories(paths, dropbox_path)

            # Show only top-level directories with nested counts
            for top_dir in top_level_dirs:
                nested_count = nested_counts.get(top_dir, 0)
                if nested_count > 0:
                    console.print(f"[red]! {top_dir}[/red] [cyan](+{nested_count} nested error directories)[/cyan]")
                else:
                    console.print(f"[red]! {top_dir}[/red]")

    # Summary
    summary_table = Table(show_header=True, header_style="white", box=None)
    summary_table.add_column("Status", style="dim")
    summary_table.add_column("Count", style="white")
    summary_table.add_row("Total directories checked", str(ignored_count + not_ignored_count + error_count))
    summary_table.add_row("Ignored by Dropbox", f"[green]{ignored_count}[/green]")
    summary_table.add_row("Not ignored", str(not_ignored_count))
    if error_count > 0:
        summary_table.add_row("Check errors", f"[red]{error_count}[/red]")
    console.print(Panel(summary_table, title="[bold cyan]Summary[/bold cyan]", border_style="cyan"))


def organize_directories(paths, base_path):
    """Organize directories into a hierarchy of parent-child relationships

    Args:
        paths: List of Path objects to organize
        base_path: Base path to consider as root for relative paths

    Returns:
        tuple: (top_level_dirs, nested_counts)
            - top_level_dirs: List of top-level directories
            - nested_counts: Dict mapping top-level dirs to count of nested dirs
    """
    # Sort paths by depth (shortest paths first)
    sorted_paths = sorted(paths, key=lambda p: len(str(p).split(os.sep)))

    # Find top-level directories and count nested directories
    top_level_dirs = []
    nested_counts = {}

    for path in sorted_paths:
        # Check if this path is under any already processed path
        is_nested = False
        path_str = str(path)

        for existing_path in top_level_dirs:
            existing_str = str(existing_path)
            # If this path starts with an existing path plus a separator, it's nested
            if path_str.startswith(existing_str + os.sep):
                is_nested = True
                # Increment the nested count for the parent path
                nested_counts[existing_path] += 1
                break

        if not is_nested:
            # This is a top-level directory
            top_level_dirs.append(path)
            nested_counts[path] = 0

    return top_level_dirs, nested_counts


def check_if_ignored(path, system):
    """Check if a directory is ignored by Dropbox

    Returns:
        True: Directory is ignored
        False: Directory is not ignored
        None: Could not determine (error)
    """
    try:
        if system == "Windows":
            # Windows: Check NTFS alternate data streams
            result = subprocess.run(
                [
                    "powershell",
                    "-Command",
                    f"Get-Content -Path {shlex.quote(str(path))} -Stream com.dropbox.ignored -ErrorAction SilentlyContinue",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            # If command succeeds and value is "1", directory is ignored
            return result.returncode == 0 and result.stdout.strip() == "1"

        elif system == "Darwin":  # macOS
            # macOS: Check extended attributes
            result = subprocess.run(
                ["xattr", "-p", "com.dropbox.ignored", str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
            # If command succeeds and value is "1", directory is ignored
            return result.returncode == 0 and result.stdout.strip() == "1"

        else:  # Linux and others
            # Linux: Check attributes
            result = subprocess.run(
                ["attr", "-q", "-g", "com.dropbox.ignored", str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
            # If command succeeds and value contains "1", directory is ignored
            return result.returncode == 0 and "1" in result.stdout.strip()

    except (PermissionError, OSError, subprocess.SubprocessError):
        return None  # Error occurred

    return False  # Default: not ignored


if __name__ == "__main__":
    sys.exit(main())
